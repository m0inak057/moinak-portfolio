# Quick Start Guide - Portfolio CMS

**Status**: Phase 1 MVP Complete ✅  
**Date**: March 29, 2026  
**Next Step**: Configure GitHub & Gemini keys and test!

---

##  1️⃣ Configure Your API Keys

### Get GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (read access only)
4. Copy the token

### Get Gemini API Key
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create a new API key for your project
4. Copy the key

### Update .env
Edit `portfolio-cms/.env`:
```
GITHUB_TOKEN=your_token_here
GEMINI_API_KEY=your_key_here
```

---

## 2️⃣ Test GitHub Sync

```bash
cd portfolio-cms
source venv/Scripts/activate  # Windows: venv\Scripts\activate.bat

python manage.py sync_github_repos
```

**Expected output:**
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

---

## 3️⃣ Test AI Content Generation

### Option A: Via Admin Panel (Easy)
```bash
python manage.py runserver
```

1. Visit http://localhost:8000/admin/
2. Login (admin / admin123)
3. Click "Projects"
4. Select 1-2 projects
5. Under "Admin actions" dropdown, select "Generate/Refresh AI content..."
6. Click "Go"

Wait 10-15 seconds... ✨

### Option B: Via API (Programmatic)
```bash
curl -X POST http://localhost:8000/api/projects/1/generate-content/
```

Response:
```json
{
  "status": "success",
  "message": "AI content generated successfully for wikipedia-summarizer",
  "data": {
    "id": 1,
    "ai_title": "Wikipedia Article Summarizer",
    "ai_summary": "A full-stack NLP application...",
    "key_features": ["Smart search...", "..."],
    "tech_stack": ["Flask", "Python", "NLP"]
  }
}
```

---

## 4️⃣ Verify API Endpoints

### List Visible Projects
```bash
curl http://localhost:8000/api/projects/?is_visible=true
```

### Get MAJOR Projects Only
```bash
curl http://localhost:8000/api/projects/major/
```

### Get OTHER Projects Only
```bash
curl http://localhost:8000/api/projects/other/
```

### Update Project (toggle visibility)
```bash
curl -X PATCH http://localhost:8000/api/projects/1/ \
  -H "Content-Type: application/json" \
  -d '{"is_visible": true, "category": "MAJOR"}'
```

---

## 5️⃣ Admin Controls Checklist

Go to http://localhost:8000/admin/ and verify:

- [ ] Projects list displays all synced repos
- [ ] Each project shows: name, category, visibility, AI status
- [ ] Click on a project → can toggle `is_visible`
- [ ] Click on a project → can change `category` (MAJOR/OTHER)
- [ ] Click on a project → verify AI content populated (after generation)
- [ ]  Select projects → use "Generate AI content" action
- [ ] After generation, verify:
  - `ai_title` field filled
  - `ai_summary` field filled
  - `key_features` list populated
  - `tech_stack` list populated

---

## 6️⃣ Current State

### Database
- ✅ SQLite database created
- ✅ 5 migration files applied
- ✅ Project table ready
- Total projects in DB: (will show after `sync_github_repos`)

### API
- ✅ DRF browsable API at http://localhost:8000/api/projects/
- ✅ Filtering, searching, ordering supported
- ✅ Pagination enabled (20 per page)

### Admin
- ✅ Admin site at http://localhost:8000/admin/
- ✅ Credentials: admin / admin123
- ✅ Custom actions for AI content

---

## 7️⃣ Make Your Portfolio Visible

**To show projects on your public portfolio:**

1. Generate AI content (Step 3)
2. Toggle `is_visible = True` for projects you want to show
3. Select `category`:
   - `MAJOR` = Full details (summary, 3-5 features, tech stack)
   - `OTHER` = Compact (1-liner, 2-3 features, tech stack)

---

## ⚡ Common Issues

### "Invalid API key" error
- Check GITHUB_TOKEN is in `.env`
- Verify token has repo read access
- Test: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

### "Gemini API quota exceeded"
- Check usage at https://console.cloud.google.com/
- Free tier is ~$15/month worth of credits (thousands of calls)

### "No repositories synced"
- Ensure GITHUB_USERNAME is correct in `.env`
- Verify GitHub token has `repo` scope
- Check GitHub has public repos

### JSON parsing error from Gemini
- Check logs: `cat db.sqlite3` (just kidding, check console output)
- System automatically falls back to regex parsing

---

## 📊 Next Steps After Testing

✅ **If everything works:**
1. Commit code to GitHub
2. Move to Phase 2: Build public portfolio frontend with Django templates

❌ **If something fails:**
1. Check the IMPLEMENTATION_PLAN.md for detailed architecture
2. Check README.md troubleshooting section
3. Verify all keys are correct in .env
4. Run `python manage.py check` to validate setup

---

## 📝 Performance Expectations

| Operation | Time |
|-----------|------|
| GitHub Sync (20 repos) | 2-3 seconds |
| Generate AI content (1 project) | 10-15 seconds |
| API list response | <100ms |
| Admin page load | <500ms |

---

## 🎯 Success Criteria

You'll know it's working when:
1. ✅ `sync_github_repos` creates 15+ project records
2. ✅ Admin panel shows all projects with filtering/search
3. ✅ "Generate AI content" creates meaningful titles & summaries
4. ✅ API returns JSON with visible projects only
5. ✅ MAJOR projects show full details, OTHER projects are concise

---

## 🚀 That's It!

Your **AI-Powered Portfolio CMS** is now ready for Phase 2 (frontend).

Questions? Check:
- `IMPLEMENTATION_PLAN.md` - full technical spec
- `README.md` - setup and troubleshooting
- Django docs: https://docs.djangoproject.com/
- Gemini docs: https://ai.google.dev/docs

**Happy automating!** 🎉
