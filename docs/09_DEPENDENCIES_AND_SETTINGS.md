# Dependencies & Settings Reference

## Complete `requirements.txt`

Replace the existing `requirements.txt` with this:

```
# Django core
Django==4.2.10
djangorestframework==3.14.0
django-filter==24.1
python-dotenv==1.0.0
gunicorn==21.2.0
whitenoise==6.6.0

# Database
psycopg2-binary==2.9.9

# HTTP
requests==2.31.0

# AI
google-generativeai==0.7.2

# LangGraph agent orchestration
langgraph==0.2.28
langchain-core==0.3.15

# Google Drive
google-api-python-client==2.111.0
google-auth==2.26.1
google-auth-httplib2==0.2.0

# Image handling
Pillow==10.1.0
```

---

## Complete `.env` Template

Create `.env` from this template (never commit to git):

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=m0inak057

# Gemini
GEMINI_API_KEY=AIzaSy_xxxxxxxxxxxxxxxxxxxx

# Google Drive (service account)
GOOGLE_DRIVE_CREDENTIALS_JSON=/path/to/service-account-credentials.json
GOOGLE_DRIVE_FOLDER_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ

# Email (keep existing values)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=moinak.mondal057@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=moinak.mondal057@gmail.com
CONTACT_EMAIL=moinak.mondal057@gmail.com
```

---

## `settings.py` Additions

Add these lines to `portfolio_cms/settings.py` (the rest of the file stays the same):

```python
# Google Drive
GOOGLE_DRIVE_CREDENTIALS_JSON = os.getenv('GOOGLE_DRIVE_CREDENTIALS_JSON', '')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
```

Add `'agents'` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'projects',
    'agents',    # ← add this line
]
```

---

## `.gitignore` — Ensure These Are Listed

```
.env
*.json           # service account credentials
db.sqlite3
media/
staticfiles/
venv/
__pycache__/
*.pyc
```

---

## Setup Commands (in order)

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy .env and fill in all values
cp .env.example .env

# 4. Run migrations (includes new SyncLog model and Certificate/Project field additions)
python manage.py makemigrations projects
python manage.py migrate

# 5. Create admin user
python manage.py createsuperuser

# 6. Collect static files
python manage.py collectstatic

# 7. Start server
python manage.py runserver

# 8. Test the sync
curl -X POST http://localhost:8000/api/sync/ \
  -H "X-CSRFToken: $(python -c 'import django; django.setup(); from django.middleware.csrf import get_token; from django.test import RequestFactory; print(get_token(RequestFactory().get("/")))')"
# (or just click the sync button in the browser)
```
