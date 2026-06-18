import base64
import json
import logging
from google import genai
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_ID = "gemini-2.0-flash"


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
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt,
            ],
        )
        
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


def generate_project_content(readme_text: str, repo_name: str) -> dict | None:
    """
    Given README content and repo name, returns structured project content.
    
    Returns:
    {
        "title": str,
        "summary": str,
        "features": list[str],
        "tech_stack": list[str],
        "category": "MAJOR" | "OTHER",    # agent decides based on complexity
        "should_be_visible": bool          # agent decides if worth showing
    }
    
    Returns None on failure.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Truncate README if too long
    readme_truncated = readme_text[:8000] if len(readme_text) > 8000 else readme_text
    
    prompt = f"""You are a Senior Technical Recruiter reviewing a developer's GitHub portfolio.
Analyze this repository and return a JSON object with EXACTLY these fields:

{{
  "title": "A refined, professional project title (2-5 words). Better than the repo name.",
  "summary": "For complex projects: 2-3 paragraph summary covering The Problem, The Solution, The Impact. Use strong verbs: Architected, Optimised, Implemented. For simple/toy projects: 1 sentence only.",
  "features": ["Feature 1 with technical detail", "Feature 2", "Feature 3"],
  "tech_stack": ["Technology1", "Framework2", "Tool3"],
  "category": "MAJOR if this is a substantial, real-world project with meaningful complexity, clear purpose, and good documentation. OTHER if it is a tutorial, assignment, experiment, or small utility.",
  "should_be_visible": true if the project is worth showing to recruiters (not empty, not a fork-only, not a hello-world), false otherwise
}}

Repository name: {repo_name}

README content:
{readme_truncated if readme_truncated else "No README available."}

Return ONLY valid JSON. No markdown fences, no explanation."""

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
        )
        text = response.text.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        
        data = json.loads(text)
        
        # Validate and sanitise
        data.setdefault("category", "OTHER")
        data.setdefault("should_be_visible", False)
        data["category"] = "MAJOR" if data["category"] == "MAJOR" else "OTHER"
        data["features"] = data.get("features", [])[:6]   # cap at 6
        data["tech_stack"] = data.get("tech_stack", [])[:8]  # cap at 8
        
        return data
    
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Content generation failed for {repo_name}: {str(e)}")
        return None
