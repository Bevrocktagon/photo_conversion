from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def authenticate_drive_service(service_account_file):
    """
    Authenticate to the Google Drive API using a service account.
    """
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def list_files_owned_by_service_account(drive_service):
    """
    List all files owned by the service account.
    """
    results = drive_service.files().list(
        fields="files(id, name, owners, permissions)"
    ).execute()
    return results.get('files', [])

def file_is_shared_with_user(file, user_email):
    """
    Check if the file is already shared with the given user email.
    """
    for permission in file.get('permissions', []):
        if permission.get('emailAddress') == user_email:
            return True
    return False

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
    print(f"Shared file {file_id} with {user_email}")

def main():
    # Path to your service account key file
    service_account_file = 'italyphotos-e561bf9f5f24.json'
    # Replace with your personal email
    user_email = 'bevans18@gmail.com'

    # Authenticate the Drive API
    drive_service = authenticate_drive_service(service_account_file)

    # List all files owned by the service account
    files = list_files_owned_by_service_account(drive_service)
    if not files:
        print("No files found.")
        return

    print("Found the following files owned by the service account:")
    for file in files:
        print(f"Name: {file['name']}, ID: {file['id']}")

    # Share each file only if it's not owned or shared with the user
    for file in files:
        if file_is_shared_with_user(file, user_email):
            print(f"File {file['name']} ({file['id']}) is already shared with {user_email}. Skipping.")
        else:
            try:
                share_file_with_user(drive_service, file['id'], user_email)
            except Exception as e:
                print(f"Failed to share file {file['id']}: {e}")

if __name__ == '__main__':
    main()

