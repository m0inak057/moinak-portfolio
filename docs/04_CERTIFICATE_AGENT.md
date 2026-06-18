# Certificate Agent

## Responsibility

Watches a designated Google Drive folder. For every PDF file found in that folder, if it has not already been processed (checked via `drive_file_id`), it downloads the PDF, uses Gemini Vision to extract the certificate name, issuer, and issued date, and creates a `Certificate` record in the database.

**Zero manual input required.** Moinak drops a PDF into the Drive folder → next sync → certificate appears on portfolio.

---

## File Locations

```
agents/
├── certificate_agent.py        # main agent class
└── tools/
    └── drive_tools.py          # Google Drive API helpers
```

---

## Google Drive Setup (One-Time)

The agent uses a **Service Account** to access Google Drive. This is the recommended approach for server-side automation.

### Steps to set up (document these for Moinak):

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use existing)
3. Enable **Google Drive API**
4. Create a **Service Account** under IAM & Admin → Service Accounts
5. Download the service account JSON credentials file
6. Save the path to this file as `GOOGLE_DRIVE_CREDENTIALS_JSON` in `.env`
7. **Share the certificates Drive folder** with the service account email (find it in the JSON file under `"client_email"`)
8. Copy the folder ID from the Drive URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
9. Save `GOOGLE_DRIVE_FOLDER_ID` in `.env`

---

## Drive Tools (`agents/tools/drive_tools.py`)

```python
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
```

---

## Gemini Vision OCR Tool (`agents/tools/gemini_tools.py`)

Add this function to the existing gemini tools (create file if it doesn't exist):

```python
import base64
import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


def extract_certificate_data(pdf_bytes: bytes) -> dict:
    """
    Uses Gemini Vision to extract structured data from a certificate PDF.
    
    Returns:
    {
        "name": "AWS Certified Developer - Associate",
        "issuer": "Amazon Web Services",
        "issued_date": "2024-03-15",   # YYYY-MM-DD format
        "confidence": "high"            # high / medium / low
    }
    
    On failure returns None.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Convert PDF bytes to base64
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode('utf-8')
    
    prompt = """You are extracting information from a professional certificate or course completion document.
    
Extract and return ONLY a JSON object with these exact fields:
{
  "name": "Full official name of the certificate or course (e.g. 'AWS Certified Solutions Architect - Associate')",
  "issuer": "Organisation that issued it (e.g. 'Amazon Web Services', 'Google', 'IBM', 'Coursera')",
  "issued_date": "Date in YYYY-MM-DD format. If only month/year visible, use first day of that month. If year only, use YYYY-01-01",
  "confidence": "high if all fields clearly visible, medium if some inference needed, low if mostly guessing"
}

Return ONLY valid JSON. No markdown, no explanation, no extra text."""

    try:
        response = model.generate_content([
            {
                "mime_type": "application/pdf",
                "data": pdf_b64
            },
            prompt
        ])
        
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        data = json.loads(text)
        
        # Validate required fields
        required = ["name", "issuer", "issued_date"]
        for field in required:
            if not data.get(field):
                logger.warning(f"Gemini OCR missing field: {field}")
                return None
        
        return data
    
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Certificate OCR failed: {str(e)}")
        return None
```

---

## Certificate Agent (`agents/certificate_agent.py`)

```python
import logging
from datetime import date
from django.conf import settings
from projects.models import Certificate
from .tools.drive_tools import list_pdf_files_in_folder, download_pdf_as_bytes
from .tools.gemini_tools import extract_certificate_data

logger = logging.getLogger(__name__)


class CertificateAgent:
    """
    Scans Google Drive folder for new certificate PDFs and publishes them to portfolio.
    """

    def run(self) -> dict:
        """
        Main entry point.
        Returns:
        {
            "drive_files_found": int,
            "created": int,
            "skipped": int,       # already in DB
            "errors": list[str]
        }
        """
        result = {
            "drive_files_found": 0,
            "created": 0,
            "skipped": 0,
            "errors": []
        }

        folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        if not folder_id:
            result["errors"].append("GOOGLE_DRIVE_FOLDER_ID not configured")
            return result

        try:
            drive_files = list_pdf_files_in_folder(folder_id)
        except Exception as e:
            result["errors"].append(f"Google Drive listing failed: {str(e)}")
            return result

        result["drive_files_found"] = len(drive_files)

        for drive_file in drive_files:
            try:
                self._process_file(drive_file, result)
            except Exception as e:
                result["errors"].append(
                    f"Error processing {drive_file.get('name')}: {str(e)}"
                )

        return result

    def _process_file(self, drive_file: dict, result: dict):
        file_id = drive_file["id"]
        file_name = drive_file["name"]

        # Deduplication check — skip if already processed
        if Certificate.objects.filter(drive_file_id=file_id).exists():
            result["skipped"] += 1
            logger.debug(f"Skipping already-processed certificate: {file_name}")
            return

        logger.info(f"Processing new certificate: {file_name}")

        # Download PDF
        pdf_bytes = download_pdf_as_bytes(file_id)

        # Run Gemini OCR
        extracted = extract_certificate_data(pdf_bytes)

        if not extracted:
            result["errors"].append(
                f"Gemini could not extract data from: {file_name}. "
                f"Skipping — add manually via admin if needed."
            )
            return

        # Parse issued_date
        try:
            from datetime import datetime
            issued_date = datetime.strptime(extracted["issued_date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            issued_date = date.today()
            logger.warning(f"Could not parse date from {file_name}, using today")

        # Save PDF to media storage and create Certificate record
        import io
        from django.core.files.base import ContentFile

        cert = Certificate(
            name=extracted["name"],
            issuer=extracted["issuer"],
            issued_date=issued_date,
            drive_file_id=file_id,
            auto_extracted=True,
            is_visible=True,  # auto-publish — Moinak can hide from admin if needed
        )

        # Save PDF into Django's media storage
        pdf_content = ContentFile(pdf_bytes, name=f"{file_id}.pdf")
        cert.pdf_file.save(f"certificates/pdfs/{file_id}.pdf", pdf_content, save=False)
        cert.save()

        result["created"] += 1
        logger.info(
            f"Created certificate: {extracted['name']} from {extracted['issuer']}"
        )
```

---

## Key Decisions

**Auto-publish (`is_visible=True`)**  
Certificates are auto-published. The assumption is Moinak only puts certificates he wants to show in the Drive folder. If he wants to hide one, he can do so from the admin panel.

**Deduplication via `drive_file_id`**  
Before OCR, the agent checks if `Certificate.objects.filter(drive_file_id=file_id).exists()`. If yes, skip. This is safe across multiple syncs.

**Graceful degradation**  
If Gemini OCR fails for a specific file, the agent logs the error and continues. It adds the file to the error list in the `SyncLog`. The other files still get processed. Moinak can add the failed certificate manually if needed.

**PDF stored in Django media**  
The downloaded PDF bytes are saved to `MEDIA_ROOT/certificates/pdfs/{drive_file_id}.pdf`. This allows the existing PDF viewer modal to work unchanged.

---

## New Settings Required

```python
# portfolio_cms/settings.py — add these
GOOGLE_DRIVE_CREDENTIALS_JSON = os.getenv('GOOGLE_DRIVE_CREDENTIALS_JSON', '')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
```

---

## New Dependencies

Add to `requirements.txt`:

```
google-api-python-client==2.111.0
google-auth==2.26.1
google-auth-httplib2==0.2.0
```
