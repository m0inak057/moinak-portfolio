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
