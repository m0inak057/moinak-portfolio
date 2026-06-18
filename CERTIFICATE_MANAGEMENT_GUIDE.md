# Certificate Management System - Complete Guide

**Status**: Phase 2 MVP Complete ✅  
**Date**: March 31, 2026  
**Feature**: Dynamic certificate management with PDF uploads

---

## 📋 Overview

The Certificate Management System allows you to:
- ✅ Upload certificate PDFs through the Django admin panel
- ✅ Manage certificate visibility (show/hide from portfolio)
- ✅ Display certificates dynamically on your portfolio
- ✅ Access certificates via API endpoints
- ✅ Organize certificates by issuer and date

---

## 🚀 How to Use

### **1️⃣ Add a Certificate via Admin Panel**

#### Step-by-step:
1. Go to http://localhost:8000/admin/
2. Login with your credentials (admin / admin123)
3. In the sidebar, click `"Certificates"`
4. Click the `"+ Add Certificate"` button (top right)
5. Fill in the form:

```
Name:           AWS Certified Solutions Architect
Issuer:         Amazon Web Services
Issued Date:    2024-12-15 (Use the calendar picker)
PDF File:       Click "Choose File" and select your certificate PDF
Is Visible:     Check the checkbox to show on portfolio
```

6. Click `"SAVE"` button

#### Fields Explained:

| Field | Required | Example | Notes |
|-------|----------|---------|-------|
| **Name** | ✅ Yes | "AWS Solutions Architect" | Display name on portfolio |
| **Issuer** | ✅ Yes | "Amazon Web Services" | Organization that issued it |
| **Issued Date** | ✅ Yes | 2024-12-15 | When you earned it |
| **PDF File** | ✅ Yes | certificate.pdf | Upload the actual certificate |
| **Is Visible** | ✅ Yes | Checked/Unchecked | Show/hide from public portfolio |

---

### **2️⃣ Manage Your Certificates**

#### View All Certificates:
1. Go to http://localhost:8000/admin/
2. Click `"Certificates"` in the sidebar
3. You'll see all your certificates in a list view:

```
Certificate List
├── AWS Solutions Architect    │ Amazon...  │  Apr 2024  │ ✓ Visible │ 📄 PDF │
├── Google Cloud Associate     │ Google...  │  Feb 2024  │ ✓ Visible │ 📄 PDF │
└── Azure Administrator        │ Microsoft  │  Jan 2024  │ ✕ Hidden  │ 📄 PDF │
```

#### Quick Actions:

**Toggle Visibility (Show/Hide)**
- Click the ✓ or ✕ in the "Visibility" column
- Red ✕ = Hidden from portfolio
- Green ✓ = Visible on portfolio

**View/Download PDF**
- Look at the "File" column
- Green "📄 PDF" badge = PDF uploaded
- Gray "—" = No PDF

**Edit Certificate**
- Click on the certificate name
- Modify any field
- Click "SAVE"

**Delete Certificate**
- Click on the certificate name
- Click "DELETE" button at bottom

---

### **3️⃣ How Certificates Display on Portfolio**

#### On Your Website:
```
CERTIFICATIONS
┌─────────────────────────────┐
│ 🏆 AWS Solutions Architect  │
│     Amazon Web Services     │
│     Apr 2024                │
│     View Certificate → (PDF)│
└─────────────────────────────┘
```

**Rules:**
- Only certificates with `Is Visible = ✓` show on portfolio
- Certificates are sorted by issue date (newest first)
- Each certificate displays: Name, Issuer, Date, PDF link
- PDF opens in a new tab when clicked

---

## 🔌 API Endpoints

### **Get All Visible Certificates**
```bash
curl http://localhost:8000/api/certificates/
```

**Response Example:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "AWS Solutions Architect",
      "issuer": "Amazon Web Services",
      "issued_date": "2024-12-15",
      "pdf_file": "https://yourdomain.com/media/certificates/pdfs/AWS_cert.pdf",
      "is_visible": true,
      "created_at": "2024-12-16T10:30:00Z",
      "updated_at": "2024-12-16T10:30:00Z"
    }
  ]
}
```

### **Add a Certificate via API**
```bash
curl -X POST http://localhost:8000/api/certificates/ \
  -H "Content-Type: multipart/form-data" \
  -F "name=Google Cloud Associate" \
  -F "issuer=Google Cloud" \
  -F "issued_date=2024-02-10" \
  -F "pdf_file=@/path/to/certificate.pdf" \
  -F "is_visible=true"
```

### **Update a Certificate**
```bash
curl -X PATCH http://localhost:8000/api/certificates/1/ \
  -H "Content-Type: application/json" \
  -d '{"is_visible": false}'
```

### **Delete a Certificate**
```bash
curl -X DELETE http://localhost:8000/api/certificates/1/
```

---

## 📂 File Structure

```
portfolio-cms/
├── media/
│   └── certificates/
│       └── pdfs/              ← Your uploaded PDFs go here
│           ├── cert1.pdf
│           ├── cert2.pdf
│           └── ...
├── projects/
│   ├── models.py              ← Certificate model defined here
│   ├── admin.py               ← Certificate admin panel
│   ├── serializers.py         ← API serialization
│   ├── views.py               ← API & Web views
│   └── urls.py                ← API routes
├── templates/
│   └── portfolio/
│       └── index.html         ← Certificates section template
└── portfolio_cms/
    └── settings.py            ← Media file configuration
```

---

## 🎯 Common Tasks

### **Upload Multiple Certificates**
1. Go to admin panel
2. Add first certificate
3. Repeat for each certificate
4. No batch upload feature yet (can be added in future)

### **Change Certificate Order**
Certificates automatically sort by issue date (newest first). To change order:
1. Edit the certificate
2. Update the "Issued Date" field
3. The page will re-sort automatically

### **Replace a PDF**
1. Go to the certificate in admin
2. Click "Choose File" again
3. Select new PDF
4. Click "SAVE"
5. Old PDF is automatically replaced

### **Search Certificates**
In the admin certificates list:
1. Use the search box at the top
2. Search by name or issuer
3. Results filter in real-time

### **Filter by Visibility**
In the admin certificates list:
1. Click "Filters" on the right
2. Select "Is Visible: True" or "Is Visible: False"

---

## 🛠️ Technical Details

### **Certificate Model Fields**
```python
class Certificate(models.Model):
    name            # CharField - Display name
    issuer          # CharField - Organization
    issued_date     # DateField - When earned
    pdf_file        # FileField - Upload location: media/certificates/pdfs/
    is_visible      # BooleanField - Show on portfolio
    created_at      # DateTimeField - Auto-set on creation
    updated_at      # DateTimeField - Auto-updated on save
```

### **Admin Features**
- ✅ Custom list display with badges
- ✅ Inline editing
- ✅ Search by name/issuer
- ✅ Filter by visibility
- ✅ PDF preview link
- ✅ Readonly timestamps

### **Template Integration**
The portfolio template (`index.html`) displays certificates with:
```django
{% for cert in certificates %}
  Name: {{ cert.name }}
  Issuer: {{ cert.issuer }}
  Date: {{ cert.issued_date|date:"M Y" }}
  PDF: {{ cert.pdf_file.url }}
{% endfor %}
```

---

## ⚙️ Configuration

### **Media File Settings** (in `settings.py`)
```python
MEDIA_URL = 'media/'                    # Public URL for PDFs
MEDIA_ROOT = BASE_DIR / 'media'         # Where files are stored
```

### **URL Routing** (in `urls.py`)
```python
# Media files served from /media/ in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 📱 Portfolio Display

### **Before** (No certificates)
```
CERTIFICATIONS
┌───────────────────────────────────┐
│ No certificates uploaded yet.      │
│ Visit the admin panel to add your  │
│ certifications!                    │
└───────────────────────────────────┘
```

### **After** (With certificates)
```
CERTIFICATIONS
┌──────────────────┐  ┌──────────────────┐
│ 🏆 AWS Certified │  │ 🏆 Google Cloud  │
│ Amazon Web Srvcs │  │ Google           │
│ Dec 2024         │  │ Feb 2024         │
│ View Certificate │  │ View Certificate │
└──────────────────┘  └──────────────────┘
```

---

## 🚀 Testing the Feature

### **Quick Test (5 minutes)**
```bash
# 1. Start Django server
cd portfolio-cms
python manage.py runserver

# 2. Go to admin
http://localhost:8000/admin/

# 3. Add one certificate
# - Fill form
# - Upload PDF
# - Click SAVE

# 4. Check portfolio
http://localhost:8000/

# 5. Check API
http://localhost:8000/api/certificates/
```

### **Expected Result**
- ✅ Certificate appears in admin list
- ✅ Green "✓ Visible" badge
- ✅ Green "📄 PDF" badge
- ✅ Certificate shows on portfolio homepage
- ✅ API returns the certificate
- ✅ PDF link works (opens in new tab)

---

## 🐛 Troubleshooting

### **Problem: PDF upload fails**
**Solution:**
- Ensure `media/` folder exists
- Check file is less than 10MB
- File should be PDF format
- Run `python manage.py collectstatic` (if using production setup)

### **Problem: Certificates not showing on portfolio**
**Solution:**
- Go to admin → Certificates
- Verify "Is Visible" checkbox is checked ✓
- Make sure you saved the certificate
- Refresh browser (Ctrl+Shift+R for hard refresh)

### **Problem: PDF link returns 404**
**Solution:**
- Ensure Django is running with media serving enabled
- Check `MEDIA_URL` and `MEDIA_ROOT` in settings
- Verify the file exists in `media/certificates/pdfs/`

### **Problem: Admin panel shows error "Certificate not found"**
**Solution:**
- Run migrations: `python manage.py migrate`
- Check database is not corrupted
- Delete and restart Django

---

## 📊 Database Schema

```sql
CREATE TABLE projects_certificate (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(255) NOT NULL,
    issued_date DATE NOT NULL,
    pdf_file VARCHAR(100),
    is_visible BOOLEAN DEFAULT TRUE,
    created_at DATETIME AUTO,
    updated_at DATETIME AUTO
);
```

---

## ✨ Future Enhancements

Potential features to add later:
- 📷 Certificate thumbnail preview
- 📦 Batch certificate upload
- 🔐 Certificate verification links
- 📅 Certificate expiration dates
- 🏷️ Certificate categories/tags
- ⚡ Drag-and-drop reordering
- 📧 Email notifications when certificates are viewed

---

## 📞 Need Help?

**For Django admin issues:**
- See QUICK_START.md - Admin setup
- See FRONTEND_SETUP.md - Technical details

**For API integration:**
- Test API endpoints using browser at http://localhost:8000/api/certificates/
- Check migration status: `python manage.py showmigrations`

**For template customization:**
- Edit `templates/portfolio/index.html`
- Modify CSS in `static/css/styles.css`

---

## ✅ Checklist

- [ ] Certificates table created in database
- [ ] Admin panel has Certificates section
- [ ] Can upload PDF files
- [ ] Certificates display on portfolio
- [ ] API endpoint works
- [ ] Toggle visibility working
- [ ] PDF links work correctly

**You're all set!** 🎉

