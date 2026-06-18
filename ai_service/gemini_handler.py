import json
import logging
import re
import requests
from typing import Dict, List, Optional
from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)


class GeminiProjectAnalyzer:
    """
    Analyzes GitHub repository READMEs and generates AI-powered project content.
    Uses Google's Gemini API to create compelling portfolio descriptions.
    """
    
    MAJOR_PROJECT_PROMPT = """You are a Senior Technical Recruiter and Developer. Analyze the following README and code context.
Return a JSON response with EXACTLY these fields (no extra fields):
{{
    "title": "A refined, impactful project title (2-5 words)",
    "summary": "A 2-3 paragraph summary focusing on 'The Problem', 'The Solution', and 'The Impact'. Use action verbs like 'Architected', 'Optimized', 'Implemented'.",
    "features": ["Feature 1 (technical detail)", "Feature 2 (technical detail)", "Feature 3"],
    "tech_stack": ["Technology1", "Technology2", "Framework"]
}}

README content:
{readme_text}

Return ONLY valid JSON, no markdown, no explanations."""

    OTHER_PROJECT_PROMPT = """You are a Senior Technical Recruiter and Developer. Analyze the following README.
Return a JSON response with EXACTLY these fields (no extra fields):
{{
    "title": "A concise project title (2-3 words)",
    "summary": "A 1-sentence summary of what this project does",
    "features": ["Key feature 1", "Key feature 2"],
    "tech_stack": ["Tech1", "Tech2", "Tech3"]
}}

README content:
{readme_text}

Return ONLY valid JSON, no markdown, no explanations."""

    SYSTEM_PROMPT = """You are a Senior Technical Recruiter and Developer. Your job is to transform raw GitHub README data into compelling portfolio entries. 
Use professional, impact-driven language. Always respond with valid JSON only, no markdown or explanations."""

    def __init__(self):
        """Initialize Gemini API client"""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"
        self.github_token = settings.GITHUB_TOKEN
    
    def fetch_readme_from_github(self, repo_url: str) -> Optional[str]:
        """
        Fetch the README.md content from a GitHub repository.
        
        Args:
            repo_url: Full GitHub repository URL
            
        Returns:
            README content as string, or None if not found
        """
        try:
            # Parse repo URL to get owner/repo
            # URL format: https://github.com/owner/repo
            parts = repo_url.rstrip('/').split('/')
            owner = parts[-2]
            repo = parts[-1]
            
            # GitHub API endpoint for README
            api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            # GitHub API returns README as raw content with Accept header
            headers['Accept'] = 'application/vnd.github.v3.raw'
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch README from {repo_url}: Status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching README from {repo_url}: {str(e)}")
            return None
    
    def validate_json_response(self, content: str) -> Optional[Dict]:
        """
        Validate and parse JSON response from Gemini.
        Handles markdown code blocks and JSON extraction.
        
        Args:
            content: Raw response from Gemini API
            
        Returns:
            Parsed JSON dict, or None if invalid
        """
        try:
            # Remove markdown code blocks if present
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            content = content.strip()
            
            # Try to parse JSON
            data = json.loads(content)
            
            # Validate required fields
            required_fields = {'title', 'summary', 'features', 'tech_stack'}
            if not all(field in data for field in required_fields):
                logger.warning(f"JSON missing required fields. Got: {data.keys()}")
                return None
            
            # Ensure fields are correct types
            if not isinstance(data['title'], str):
                data['title'] = str(data['title'])
            if not isinstance(data['summary'], str):
                data['summary'] = str(data['summary'])
            if not isinstance(data['features'], list):
                data['features'] = [str(f) for f in data.get('features', [])]
            if not isinstance(data['tech_stack'], list):
                data['tech_stack'] = [str(t) for t in data.get('tech_stack', [])]
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Gemini: {str(e)}")
            return None
    
    def fallback_parse(self, readme: str) -> Dict:
        """
        Fallback parser if Gemini fails or returns invalid JSON.
        Extracts basic info from README using regex.
        
        Args:
            readme: README content
            
        Returns:
            Dict with title, summary, features, and tech_stack
        """
        logger.info("Using fallback parsing for project content")
        
        # Extract title from first heading
        title_match = re.search(r'^#\s+(.+?)$', readme, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled Project"
        
        # Extract first non-heading paragraph as summary
        paragraphs = re.split(r'\n\n+', readme)
        summary = ""
        for para in paragraphs:
            if para.strip() and not para.strip().startswith('#'):
                summary = para.strip()[:200]  # First 200 chars
                break
        
        # Look for common tech indicators in README
        tech_keywords = [
            'Python', 'JavaScript', 'TypeScript', 'Django', 'Flask', 'React', 'Vue',
            'Java', 'C++', 'C#', '.NET', 'Go', 'Rust', 'Node.js', 'Express',
            'PostgreSQL', 'MongoDB', 'Redis', 'AWS', 'Azure', 'Google Cloud',
            'Docker', 'Kubernetes', 'Git', 'TensorFlow', 'PyTorch', 'Scikit-learn',
            'API', 'REST', 'GraphQL', 'WebSocket', 'HTML5', 'CSS3'
        ]
        tech_stack = [tech for tech in tech_keywords if tech.lower() in readme.lower()][:5]
        
        return {
            'title': title,
            'summary': summary or "A GitHub project",
            'features': ["Built with modern technologies"],
            'tech_stack': tech_stack or ["GitHub"]
        }
    
    def analyze_readme(self, readme_text: str, category: str = 'OTHER') -> Dict:
        """
        Analyze README text using Gemini API.
        
        Args:
            readme_text: Content of the README.md file
            category: Project category ('MAJOR' or 'OTHER')
            
        Returns:
            Dict with keys: title, summary, features, tech_stack
        """
        if not readme_text or not readme_text.strip():
            logger.warning(f"Empty README for {category} project, using fallback")
            return self.fallback_parse("# No README")
        
        try:
            # Select prompt based on category
            if category == 'MAJOR':
                prompt = self.MAJOR_PROJECT_PROMPT.format(readme_text=readme_text)
            else:
                prompt = self.OTHER_PROJECT_PROMPT.format(readme_text=readme_text)
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
            )
            
            # Parse response
            response_text = response.text.strip()
            parsed_data = self.validate_json_response(response_text)
            
            if parsed_data:
                return parsed_data
            else:
                logger.warning("Gemini returned invalid JSON, using fallback")
                return self.fallback_parse(readme_text)
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}, using fallback")
            return self.fallback_parse(readme_text)
    
    def analyze_and_update_project(self, project) -> None:
        """
        Fetch README, analyze it, and update the project model.
        
        Args:
            project: Project model instance
            
        Raises:
            Exception if GitHub fetch or analysis fails
        """
        # Fetch README from GitHub
        readme = self.fetch_readme_from_github(project.repo_url)
        if not readme:
            logger.warning(f"Could not fetch README for {project.repo_name}")
            # Use repo description as fallback
            readme = project.repo_description or "No description available"
        
        # Analyze with Gemini
        analysis = self.analyze_readme(readme, category=project.category)
        
        # Update project with AI-generated content
        project.ai_title = analysis.get('title', '')
        project.ai_summary = analysis.get('summary', '')
        project.key_features = analysis.get('features', [])
        project.tech_stack = analysis.get('tech_stack', [])
        project.mark_ai_generated()
        project.save()
        
        logger.info(f"Successfully generated AI content for {project.repo_name}")
