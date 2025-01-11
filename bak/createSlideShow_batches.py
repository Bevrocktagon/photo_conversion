import io
import requests
from PIL import Image
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
from concurrent.futures import ThreadPoolExecutor

# Authenticate Google Drive and Slides API clients
def authenticate_apis(credentials_path):
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/presentations",
    ])
    drive_service = build('drive', 'v3', credentials=creds)
    slides_service = build('slides', 'v1', credentials=creds)
    return drive_service, slides_service

import os
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import requests
from PIL import Image
import io

def get_image_metadata(file):
    try:
        image_url = f"https://drive.google.com/uc?id={file['id']}"
        print(image_url)
        response = requests.get(image_url, timeout=5)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            file['width'], file['height'] = img.size
            return file
        else:
            raise Exception(f"Failed to fetch image from {image_url}")
    except Exception as e:
        print(f"Error fetching dimensions for {file['name']} (ID: {file['id']}): {e}")
        return None

def fetch_image_files_with_size_check(drive_service, directories, size_limit=10 * 1024 * 1024):
    """
    Fetch image files, filter by size, and extract dimensions in parallel.
    """
    valid_images = []
    skipped_images = []

    for folder_id in directories:
        print(f"Accessing folder: {folder_id}")
        page_token = None
        while True:
            response = drive_service.files().list(
                q=f"'{folder_id}' in parents and mimeType='image/jpeg'",
                fields="nextPageToken, files(id, name, size)",
                pageSize=100,
                pageToken=page_token
            ).execute()

            files = response.get('files', [])
            small_files = [file for file in files if int(file.get('size', 0)) <= size_limit]

            with ProcessPoolExecutor() as executor:
                processed_files = list(executor.map(get_image_metadata, small_files))

            for file in processed_files:
                if file:
                    valid_images.append(file)
                else:
                    skipped_images.append({
                        "name": file['name'] if file else "Unknown",
                        "id": file['id'] if file else "Unknown",
                        "reason": "Failed to fetch metadata"
                    })

            for file in files:
                if int(file.get('size', 0)) > size_limit:
                    skipped_images.append({
                        "name": file['name'],
                        "id": file['id'],
                        "size_mb": int(file['size']) / (1024 * 1024)
                    })

            page_token = response.get('nextPageToken')
            if not page_token:
                break

    # Save valid images metadata to a CSV
    df_valid = pd.DataFrame(valid_images)
    df_valid.to_csv("image_metadata.csv", index=False)
    print(f"Saved metadata for {len(valid_images)} valid images to 'image_metadata.csv'.")

    # Save skipped images to a CSV
    if skipped_images:
        df_skipped = pd.DataFrame(skipped_images)
        df_skipped.to_csv("skipped_images.csv", index=False)
        print(f"Skipped {len(skipped_images)} images. Details saved to 'skipped_images.csv'.")

    return valid_images

def load_metadata_from_csv():
    """
    Load image metadata from the saved CSV file.
    """
    try:
        df = pd.read_csv("image_metadata.csv")
        required_columns = {'id', 'name', 'width', 'height'}
        if required_columns.issubset(df.columns):
            return df.to_dict(orient='records')  # Convert back to list of dicts
        else:
            raise ValueError("Metadata file is missing required columns.")
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return None

def add_slides_with_images(slides_service, presentation_id, image_files):
    """
    Create slides in a single batch and add images in batches of up to 50.
    """

    image_files = image_files[:200]
    # Step 1: Create all slides in one batch
    slide_requests = [{"createSlide": {}} for _ in image_files]
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": slide_requests}
    ).execute()
    print(f"Created {len(image_files)} slides.")

    # Step 2: Retrieve slide IDs
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation.get('slides', [])
    slide_ids = [slide['objectId'] for slide in slides]

    if len(slide_ids) < len(image_files):
        raise ValueError("Mismatch between number of slides created and images provided.")

    # Step 3: Batch-insert images into slides
    image_requests = []
    batch_count = 0

    for idx, (image, slide_id) in enumerate(zip(image_files, slide_ids)):
        image_url = f"https://drive.google.com/uc?id={image['id']}"
        print(f"Processing image: {image['name']} ({image_url})")

        # Use pre-fetched dimensions
        width = image.get('width')
        height = image.get('height')

        if width is None or height is None:
            print(f"Skipping {image['name']} due to missing dimensions.")
            continue

        image_requests.append({
            "createImage": {
                "url": image_url,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "height": {"magnitude": height * 10000, "unit": "EMU"},
                        "width": {"magnitude": width * 10000, "unit": "EMU"}
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 0,
                        "translateY": 0,
                        "unit": "EMU"
                    }
                }
            }
        })

        # Execute batch every 50 requests or on the last image
        if len(image_requests) == 50 or idx == len(image_files) - 1:
            slides_service.presentations().batchUpdate(
                presentationId=presentation_id, body={"requests": image_requests}
            ).execute()
            batch_count += 1
            print(f"Processed batch {batch_count} of {len(image_requests)} images.")
            image_requests = []  # Clear the batch

    print("All images processed in batches.")
    
def create_presentation(slides_service, title="Photo Album"):
    presentation = slides_service.presentations().create(body={"title": title}).execute()
    return presentation['presentationId']

def share_file_with_user(drive_service, file_id, user_email):
    permission = {'type': 'user', 'role': 'writer', 'emailAddress': user_email}
    drive_service.permissions().create(fileId=file_id, body=permission).execute()
    print(f"Shared file with {user_email}")

def main():
    credentials_path = "italyphotos-e561bf9f5f24.json"
    directories = ["1-8b-xaA4AYc6E7rH7shkdFt3qxFoWx0t",]
                   #"1ahT_GEC3PfqyIIuv_bigdJRJdyRl1DgJ",
                   #"1XycLyYNEU3FS1a801Fv-p4InqDRLCuIh"]

    # Authenticate APIs
    drive_service, slides_service = authenticate_apis(credentials_path)

    # Check for existing metadata
    if os.path.exists("image_metadata.csv"):
        print("Metadata file found. Attempting to load...")
        image_files = load_metadata_from_csv()
        if image_files:
            print(f"Loaded metadata for {len(image_files)} images from 'image_metadata.csv'.")
        else:
            print("Metadata file is invalid or corrupted. Re-fetching image metadata...")
            image_files = fetch_image_files_with_size_check(drive_service, directories)
    else:
        print("No metadata file found. Fetching image metadata...")
        image_files = fetch_image_files_with_size_check(drive_service, directories)

    # Create a presentation
    presentation_id = create_presentation(slides_service)

    # Add slides and images
    add_slides_with_images(slides_service, presentation_id, image_files)

    # Share the presentation
    print(f"Presentation created: https://docs.google.com/presentation/d/{presentation_id}")
    share_file_with_user(drive_service, presentation_id, "bevans18@gmail.com")

if __name__ == "__main__":
    main()


    
