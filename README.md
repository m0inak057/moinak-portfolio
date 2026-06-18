# Portfolio CMS - MVP

A Django-based backend with automated GitHub sync and AI-powered project descriptions using Gemini API.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- GitHub Personal Access Token
- Gemini API Key

### Setup

1. **Clone and enter the directory**
   ```bash
   cd portfolio-cms
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows: venv\Scripts\activate.bat
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Edit `.env` and add:
   ```
   GITHUB_TOKEN=your_github_personal_access_token
   GEMINI_API_KEY=your_gemini_api_key
   GITHUB_USERNAME=m0inak057
   SECRET_KEY=generate-a-random-key
   ```

   To generate a SECRET_KEY:
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

5. **Run migrations** (already done, but for reference)
   ```bash
   python manage.py migrate
   ```

6. **Create admin user** (already created as 'admin')
   ```
   Username: admin
   Password: admin123  (CHANGE THIS IN PRODUCTION!)
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

   Visit:
   - Admin: http://localhost:8000/admin/
   - API: http://localhost:8000/api/projects/

---

## 📋 Features Implemented (Phase 1 MVP)

### ✅ Backend
- [x] Django project setup with DRF
- [x] Project model with GitHub sync fields
- [x] AdminProjectAdmin with custom actions
- [x] GitHub sync management command
- [x] Gemini AI service with JSON validation and fallback parsing
- [x] DRF API endpoints (list, filter, generate content)
- [x] SQLite database (zero-ops)

### ✅ API Endpoints
```
GET    /api/projects/          - List visible projects
GET    /api/projects/major/    - List MAJOR projects
GET    /api/projects/other/    - List OTHER projects
PATCH  /api/projects/{id}/     - Update project (is_visible, category)
POST   /api/projects/{id}/generate-content/ - Generate AI content
```

### 🔄 Management Commands
```bash
python manage.py sync_github_repos                # Sync all GitHub repos
python manage.py sync_github_repos --username m0inak057  # Specify user
python manage.py sync_github_repos --force        # Force update all
```

---

## 🧠 How It Works

### 1. **GitHub Sync**
```bash
python manage.py sync_github_repos
```
- Fetches all repos from GitHub API
- Creates/updates `Project` records
- Defaults new repos to `is_visible=False`
- Handles pagination and rate limiting

### 2. **AI Content Generation**
Via Django Admin:
1. Go to http://localhost:8000/admin/projects/project/
2. Click "Admin Actions" dropdown
3. Select projects and choose "Generate/Refresh AI content for selected projects"

Or via API:
```bash
curl -X POST http://localhost:8000/api/projects/1/generate-content/
```

Process:
1. Fetches README.md from GitHub
2. Sends to Gemini with category-specific prompt
3. Saves: `ai_title`, `ai_summary`, `key_features`, `tech_stack`
4. Falls back to regex parsing if Gemini fails

### 3. **Portfolio Display**
```bash
GET /api/projects/?is_visible=true
GET /api/projects/major/?is_visible=true
GET /api/projects/other/?is_visible=true
```

Returns JSON:
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "repo_name": "wikipedia-summarizer",
      "ai_title": "Wikipedia Summarizer",
      "ai_summary": "A full-stack NLP...",
      "key_features": ["Smart search", "..."],
      "tech_stack": ["Flask", "Python", "NLP"],
      "category": "MAJOR",
      "is_visible": true,
      "repo_url": "https://github.com/..."
    }
  ]
}
```

---

## 📁 Project Structure

```
portfolio-cms/
├── manage.py
├── requirements.txt
├── .env                          # Environment variables
├── .gitignore
├── db.sqlite3                    # SQLite database (auto-created)
├── set_password.py              # Helper script
├── venv/                        # Virtual environment
├── portfolio_cms/               # Main project settings
│   ├── settings.py             # Django config + GitHub/Gemini keys
│   ├── urls.py                 # URL routing
│   └── wsgi.py
├── projects/                    # Main app
│   ├── models.py               # Project model
│   ├── admin.py                # Admin interface
│   ├── views.py                # DRF ViewSets
│   ├── serializers.py          # DRF Serializers
│   ├── urls.py                 # API routes
│   ├── migrations/             # Database migrations
│   └── management/
│       └── commands/
│           └── sync_github_repos.py
├── ai_service/                  # AI layer
│   └── gemini_handler.py       # Gemini API integration
├── static/                      # CSS, JS, images
├── templates/                   # Django templates (for future frontend)
└── IMPLEMENTATION_PLAN.md      # Full implementation details

```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEBUG` | Django debug mode | Yes (True/False) |
| `SECRET_KEY` | Django secret key | Yes |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GITHUB_USERNAME` | GitHub username to sync | Yes |
| `DATABASE_URL` | Database URL (SQLite default) | No |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | No |

---

## 🧪 Testing the Setup

### 1. Sync GitHub Repos
```bash
python manage.py sync_github_repos
```
Expected output:
```
Starting GitHub sync for user: m0inak057
Found 20 repositories
  ✓ Created: wikipedia-summarizer
  ✓ Created: news-scraper
  ...
✓ Sync complete!
  Created: 20
  Updated: 0
  Total projects in DB: 20
```

### 2. Generate AI Content
```bash
# Via Django admin
python manage.py runserver
# Visit http://localhost:8000/admin/projects/project/
# Select a project and click "Generate/Refresh AI content for selected projects"
```

### 3. Query API
```bash
# List all visible projects
curl http://localhost:8000/api/projects/?is_visible=true

# Get only MAJOR projects
curl http://localhost:8000/api/projects/major/

# Get only OTHER projects
curl http://localhost:8000/api/projects/other/
```

---

## ⚡ Performance Notes

- **GitHub Sync**: ~2-3 seconds for 20 repos (handles pagination)
- **AI Generation (Gemini)**: ~8-15 seconds per project (synchronous, single request)
- **API Response**: <100ms (SQLite with <100 projects)
- **Cost**: ~$0.010 per project analysis (Gemini Flash model)

---

## 🔒 Security

- Environment variables in `.env` (never commit!)
- SQLite database file (dev only, switch to PostgreSQL for production)
- Admin authentication via Django (username: admin, password: admin123)
- JSON validation + error handling for Gemini API

⚠️ **TODO for Production:**
- Change SECRET_KEY
- Change admin password
- Set DEBUG=False
- Use PostgreSQL instead of SQLite
- Use environment-specific settings
- Add HTTPS enforcement
- Set secure ALLOWED_HOSTS

---

## 📝 Next Steps (Phase 2 - Optional)

- [ ] Add Celery + Redis for async AI generation
- [ ] Build Django templates + HTMX for portfolio display
- [ ] Migrate skills, certifications, education to CMS
- [ ] Add authentication for admin endpoints
- [ ] Deploy to Render.com or Fly.io
- [ ] Set up GitHub webhooks for real-time sync
- [ ] Add analytics tracking

---

## 🆘 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'google.generativeai'"
**Solution:**
```bash
pip install google-generativeai
```

### Issue: "github_token invalid" error during sync
**Solution:**
1. Verify GITHUB_TOKEN in `.env`
2. Ensure token has repo read access in GitHub settings
3. Check GitHub API rate limits: https://api.github.com/rate_limit

### Issue: Gemini returns invalid JSON
- Check logs for error messages
- Verify GEMINI_API_KEY is correct
- Fallback parsing will extract basic info from README

### Issue: "ALLOWED_HOSTS invalid"
**Solution:** Edit `.env`:
```
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

---

## 📚 Resources

- Django Docs: https://docs.djangoproject.com/
- DRF Docs: https://www.django-rest-framework.org/
- GitHub API: https://docs.github.com/en/rest
- Gemini API: https://ai.google.dev/docs

---

## 📄 License

Personal portfolio project.

---

**Built with ❤️ using Django, DRF, and Gemini AI**
