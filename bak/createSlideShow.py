from googleapiclient.discovery import build
from google.oauth2 import service_account
import re

# Setup Google Drive and Slides API clients
def authenticate_apis(credentials_path):
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/presentations",
    ])
    drive_service = build('drive', 'v3', credentials=creds)
    slides_service = build('slides', 'v1', credentials=creds)
    return drive_service, slides_service

# Fetch image files from Google Drive
def fetch_image_files(drive_service, directories):
    """
    Fetch all image files (JPEGs) from the specified directories.
    Handles pagination to retrieve more than 100 files.
    """
    image_files = []

    for folder_id in directories:
        print('Accessing folder:',folder_id)
        page_token = None
        idx = 0
        while True:
            response = drive_service.files().list(
                q=f"'{folder_id}' in parents and mimeType='image/jpeg'",
                fields="nextPageToken, files(id, name)",
                pageSize=100,
                pageToken=page_token
            ).execute()

            print('Extracting batch:',idx*100)
            # Add files from the current page to the list
            image_files.extend(response.get('files', []))

            # Check if there are more pages
            page_token = response.get('nextPageToken')
            if not page_token:
                break
            idx+=1

    return sorted(image_files, key=lambda x: x['name'])

# Create Google Slides presentation
def create_presentation(slides_service, title="Photo Album"):
    presentation = slides_service.presentations().create(body={"title": title}).execute()
    return presentation['presentationId']

def add_slides_with_images(slides_service, presentation_id, image_files):

    for image in image_files:
        
        # Create a new slide
        create_slide_request = {
            "requests": [{"createSlide": {"objectId": f"slide_{image['id']}"}}]
        }
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id, body=create_slide_request
        ).execute()

        # Construct the image URL
        image_url = f"https://drive.google.com/uc?id={image['id']}"
        print(image_url)  # Debugging output to check the URL

        # Add the image to the slide
        add_image_request = {
            "requests": [
                {
                    "createImage": {
                        "url": image_url,
                        "elementProperties": {
                            "pageObjectId": f"slide_{image['id']}",
                            "size": {
                                "height": {"magnitude": 5400000, "unit": "EMU"},
                                "width": {"magnitude": 7200000, "unit": "EMU"}
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
                }
            ]
        }
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id, body=add_image_request
        ).execute()

def share_file_with_user(drive_service, file_id, user_email):
    """
    Share a file with a specific user by email.
    """
    permission = {
        'type': 'user',
        'role': 'writer',  # Use 'reader' for view-only access
        'emailAddress': user_email
    }
    drive_service.permissions().create(
        fileId=file_id,
        body=permission
    ).execute()
    print(f"Shared file with {user_email}")        

# Main function
def main():
    credentials_path = "italyphotos-e561bf9f5f24.json"
    directories = ["1-8b-xaA4AYc6E7rH7shkdFt3qxFoWx0t",
                   "1ahT_GEC3PfqyIIuv_bigdJRJdyRl1DgJ",
                   "1XycLyYNEU3FS1a801Fv-p4InqDRLCuIh"]
    drive_service, slides_service = authenticate_apis(credentials_path)
    image_files = fetch_image_files(drive_service, directories)
    presentation_id = create_presentation(slides_service)
    add_slides_with_images(slides_service, presentation_id, image_files)
    print(f"Presentation created: https://docs.google.com/presentation/d/{presentation_id}")
    user_email = "bevans18@gmail.com"
    share_file_with_user(drive_service, presentation_id, user_email)

if __name__ == "__main__":
    main()
