# Frontend Specification — DO NOT MODIFY

This document is the source of truth for the visual layer. The agent must preserve every value below exactly. Any deviation in colour, font, layout, or section order is a bug.

---

## Design Tokens (CSS Variables)

These live in `static/css/styles.css` and must not be changed.

```css
:root {
    --bg-color: #0a0a0a;          /* page background — near-black */
    --text-color: #ffffff;         /* primary text */
    --accent-color: #00ff88;       /* neon green — ALL highlights, borders, active states */
    --gray-text: #888888;          /* secondary / muted text */
    --dark-gray: #1a1a1a;          /* sidebar background, card surfaces */
    --font-main: 'Space Grotesk', sans-serif;
}
```

---

## Fonts

- **Primary**: `Space Grotesk` — loaded from Google Fonts
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  ```
- **Icons**: Font Awesome 6.0.0
  ```html
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  ```

---

## Page Layout

```
+--------+------------------------------------------+
|        |                                          |
|  SIDE  |            MAIN CONTENT                  |
|  BAR   |                                          |
| 100px  |     margin-left: 100px                   |
|        |     padding: 2rem 4rem                   |
+--------+------------------------------------------+
```

- Sidebar: `position: fixed`, `width: 100px`, `background: var(--dark-gray)` (`#1a1a1a`)
- Main content: `margin-left: 100px`
- On mobile (≤ 480px): sidebar slides in from left as overlay, hamburger toggle shown

---

## Sidebar

```html
<nav class="sidebar">
    <div class="logo">
        <span class="logo-text">M</span>  <!-- accent colour, 2.5rem, font-weight 900 -->
    </div>
    <ul class="nav-links">
        <li><a href="#about">ABOUT</a></li>
        <li><a href="#experience">EXPERIENCE</a></li>
        <li><a href="#skills">SKILLS</a></li>
        <li><a href="#projects">WORK</a></li>
        <li><a href="#certifications">CERTIFICATIONS</a></li>
        <li><a href="#contact">CONTACT</a></li>
    </ul>
</nav>
```

Nav links: rotated 90° on desktop sidebar, `writing-mode: vertical-rl`, `font-size: 12px`, `letter-spacing: 2px`, `color: var(--gray-text)`, hover → `color: var(--accent-color)`.

---

## Sections — Order and Structure

Sections appear in this exact order inside `<main class="main-content">`:

1. **Hero** (`section.hero`)
2. **About** (`section#about`)
3. **Skills** (`section#skills`)
4. **Experience** (`section#experience`)
5. **Work/Projects** (`section#projects`)
6. **Certifications** (`section#certifications`)
7. **Education** (`section#education`) — nested inside certifications section
8. **Contact** (`section#contact`) — nested inside certifications section

---

## Section Title Styling

All `<h2 class="section-title">` elements:
- `font-size: 14px`
- `letter-spacing: 4px`
- `color: var(--accent-color)`
- `text-transform: uppercase`
- Bottom border: `2px solid var(--accent-color)`, `width: 40px`

---

## Hero Section

```
Hi,
I'm Moinak,
AI Engineer
[subtitle paragraph — from DB or fallback text]
[CONTACT ME! button]
```

- `h1.greeting` / `h1.name` / `h1.title`: `font-size: 80px`, `font-weight: 700`
- `.title` colour: `var(--accent-color)`
- `.subtitle`: `font-size: 20px`, `color: var(--gray-text)`
- `.contact-btn`: transparent bg, `border: 2px solid var(--accent-color)`, hover fills with accent colour

---

## Project Cards

### Major Projects (`.project-card` in `.projects-grid`)

```
[image placeholder]
[h3 — project title]
[p — ai_summary]
[tech tags — key_features as spans]
[GitHub Repo link]
```

Card style:
- `background: linear-gradient(145deg, rgba(0,255,136,0.03), rgba(0,255,136,0.01))`
- `border: 1px solid rgba(0,255,136,0.08)`
- `border-radius: 20px`
- Hover: border becomes `rgba(0,255,136,0.3)`

### Other Projects — shown in modal (`#projects-modal`)
- Same card style, shown in a 2-col grid inside modal
- Modal background: `rgba(0,0,0,0.8)`, content: `var(--dark-gray)`, border: `1px solid rgba(0,255,136,0.2)`

---

## Certificate Cards (`.cert-card`)

```
[fa-certificate icon — accent colour]
[h3 — cert name]
[p.cert-issuer]
[p.cert-date — Month Year format]
[a.cert-link — "View Certificate"]
```

Grid: `display: grid`, `grid-template-columns: repeat(auto-fill, minmax(250px, 1fr))`

Card:
- `background: var(--dark-gray)`
- `border: 1px solid rgba(0,255,136,0.1)`
- `border-radius: 15px`
- Hover: `border-color: var(--accent-color)`

---

## Skills Section

Skills are rendered as **hardcoded HTML** — they are NOT pulled from the database. The skills section lists:

**Languages**: Python, JavaScript, Java  
**Frameworks**: Django, FastAPI, React, Node.js  
**AI/LLM Systems**: LangChain, LangGraph, RAG, ReAct Agents, Tool Calling, OpenAI, Gemini, Ollama  
**Databases**: PostgreSQL, MySQL, MongoDB, Supabase, pgvector  
**DevOps & Cloud**: Docker, GKE, Cloud Run, AWS, GCP, Nginx  
**Automation**: n8n, REST APIs, Webhooks  
**Data Science**: NumPy, Pandas, Matplotlib, Scikit-learn  
**Testing**: Pytest  

Each skill renders as a `.skill-card`:
```html
<div class="skill-card">
    <div class="skill-card-icon"><i class="fas fa-python"></i></div>
    <span>Python</span>
</div>
```

**Core Competencies** (hardcoded below skills): Problem Solving, Team Leadership, Public Speaking, Project Management, Networking, Innovation.

---

## Experience Section

Rendered from `WorkExperience` DB model. Each entry:
```html
<div class="experience-item">
    <h3>{{ job_title }}</h3>
    <p class="company">{{ company }}</p>
    <p class="duration">{{ start_date }} - {{ end_date or "Present" }}</p>
    <p class="description">{{ description }}</p>
</div>
```

---

## Contact Section

Contains:
- Left: contact info + social links (GitHub, LinkedIn, Twitter/X)
- Right: contact form (name, email, subject, message, submit button)
- Form submits via `POST /api/contact/`
- EmailJS is used: `emailjs.init("qo5LuKIhLWQt8R-lj")`
- Social links: `https://github.com/m0inak057`, `https://www.linkedin.com/in/moinakm/`, `https://x.com/Moinak_05`

---

## Modals

Two existing modals (keep both):
1. `#projects-modal` — shows OTHER category projects
2. `#certificate-modal` — PDF viewer using PDF.js

PDF.js version: `3.11.174` from cdnjs.

---

## What IS Allowed to Change in the Frontend

Only two additions are permitted:

1. **Add a "Sync Now" button** — see `08_SYNC_BUTTON_UI.md` for exact placement and style
2. **Add `static/js/sync.js`** — new file only, do not modify `script.js`

Everything else in `index.html`, `styles.css`, and `script.js` is frozen.
