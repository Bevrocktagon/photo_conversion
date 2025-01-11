from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
from createSlideShow import authenticate_apis as authenticate_apis

def check_file_permissions(drive_service, file_id):
    try:
        file = drive_service.files().get(fileId=file_id, fields="id, name").execute()
        print(f"Service account can access file: {file['name']} (ID: {file['id']})")
    except Exception as e:
        print(f"Error accessing file: {e}")

credentials_path = "italyphotos-e561bf9f5f24.json"
drive_service, slides_service = authenticate_apis(credentials_path)
check_file_permissions(drive_service,'16jbneTXRjQj25RTH0GwSG0g8zHWwLbcT')


results = drive_service.files().list(pageSize=10, fields="files(id, name)").execute()
items = results.get('files', [])
if not items:
    print("No files found.")
else:
    for item in items:
        print(f"{item['name']} ({item['id']})")
