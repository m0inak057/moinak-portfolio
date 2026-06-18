import io
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def get_drive_service():
    """Build authenticated Google Drive service from service account credentials."""
    credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_JSON')
    if not credentials_path:
        raise ValueError("GOOGLE_DRIVE_CREDENTIALS_JSON not set in environment")
    
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)


def list_pdf_files_in_folder(folder_id: str) -> list[dict]:
    """
    Lists all PDF files in the given Drive folder.
    Returns list of dicts: [{id, name, createdTime}]
    """
    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    
    results = service.files().list(
        q=query,
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc"
    ).execute()
    
    return results.get('files', [])


def download_pdf_as_bytes(file_id: str) -> bytes:
    """
    Downloads a Drive file and returns its raw bytes.
    """
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    return buffer.getvalue()
