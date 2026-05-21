# 🛰️ StackSage v2.0

**AI-Powered GitHub Trend Intelligence Platform**

Search any technology domain → get real GitHub data + AI insights + interactive charts + personalized learning roadmap. Instantly.

---

## ✨ What's New in v2.0

### 🎨 Design
- **Glassmorphism UI** with animated gradient mesh background and floating particles
- **Dark / Light mode** toggle (saved in localStorage)
- **Fully responsive** mobile-first design with slide-out drawer
- **Smooth animations** throughout (hover effects, fade-up, scroll-reveal, pulse, twinkle)
- **Animated SVG hero** with wavy lines and floating dots
- New brand palette: blue → purple → cyan gradients

### 🤖 AI Features
- **AI Chat widget** — floating chatbot that answers questions about your results in context
- **AI Recommendations** — picks 3 best repos (beginner / production / hidden gem)
- **Side-by-side domain comparison** with AI verdict (e.g. React vs Vue)

### 📊 Data Features
- **PDF Export** — clean printable report (powered by reportlab)
- **Share Link** — generate a public URL anyone can view
- 5 visual charts (stars, languages, scatter, word cloud, timeline)

### 🔧 Extra
- **3 languages**: English, 中文, বাংলা
- **404 page** with personality
- **Health endpoint** `/health` for monitoring
- **User accounts** schema ready (login routes can be enabled in `app.py`)
- **SQLite-backed**: history, bookmarks, share links, users

---

## 🚀 Quick Start

### 1. Install
```bash
cd stacksage
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
export GEMINI_API_KEY="your_gemini_key"     # FREE — get at aistudio.google.com
export GITHUB_TOKEN="your_github_token"     # optional, avoids rate limit
```

### 3. Run
```bash
python app.py
# → http://127.0.0.1:5000
```

---

## 🌍 Deployment (Render, Railway, Fly.io, etc.)

The included `render.yaml` + `Procfile` work out of the box.

```bash
# Render: just connect the repo, set env vars GEMINI_API_KEY and GITHUB_TOKEN
# Fly.io: `flyctl launch`
# Heroku-style: `gunicorn app:app`
```

---

## 🗂️ File Structure

```
stacksage/
├── app.py                  # Flask app with all routes
├── ai_analyzer.py          # Gemini AI: analysis, chat, recommendations, compare
├── github_api.py           # GitHub REST API client
├── visualizer.py           # Matplotlib + WordCloud charts
├── database.py             # SQLite layer (searches, bookmarks, shares, users)
├── config.py               # Env var configuration
├── requirements.txt
├── Procfile                # gunicorn entrypoint
├── render.yaml
├── static/
│   ├── css/style.css       # Premium glassmorphism theme
│   └── js/
│       ├── main.js         # Theme, chat, share, mobile, animations
│       └── lang.js         # i18n: en / zh / bn
└── templates/
    ├── base.html
    ├── index.html
    ├── results.html        # Main analysis view + chat widget
    ├── compare.html        # NEW: 2-domain comparison input
    ├── compare_results.html # NEW: side-by-side + AI verdict
    ├── shared.html         # NEW: public share link view
    ├── history.html
    ├── bookmarks.html
    └── 404.html            # NEW
```

---

## 🔗 New Routes

| Route | Method | Purpose |
|---|---|---|
| `/compare` | GET | 2-domain compare input page |
| `/compare/run` | POST | Run side-by-side compare with AI verdict |
| `/api/chat` | POST | Contextual AI chat |
| `/api/share/<id>` | POST | Create share link |
| `/shared/<token>` | GET | View shared analysis |
| `/export/pdf/<id>` | GET | Download PDF report |
| `/api/bookmark/<id>` | DELETE | Remove a bookmark |
| `/health` | GET | Health check JSON |

---

## 🎨 Design Tokens

The UI uses CSS variables for both themes — easy to customize in `static/css/style.css`:

```css
--accent:    #7c9eff;  /* primary blue */
--accent-2:  #b794f4;  /* purple */
--accent-3:  #4fd1c5;  /* cyan */
```

Switch theme: click the sun/moon icon in the navbar.

---

## 📝 License

MIT — Built with ❤️ by NK
