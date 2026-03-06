# 🤖 CodeRefine – AI Code Review & Optimization Engine

> Paste your code → get an instant AI-powered review, security audit, and optimized rewrite — powered by **Llama 3.3-70b** on **Groq**.

---

## ✨ Features

- 🔍 **Code Review** — Detects bugs, security holes, performance issues & best-practice violations
- 🎯 **Severity Classification** — Critical / High / Medium / Low with live counters
- 🔄 **Auto Rewrite** — Refactors & rewrites code following clean-code principles
- 🎨 **Syntax Highlighting** — via Highlight.js (Python, JS, TS, Java, C++)
- 📝 **Markdown Rendering** — AI responses rendered as rich Markdown via Marked.js
- 📋 **One-click Copy** — Copy review text or rewritten code
- 💡 **Demo Samples** — Built-in intentionally buggy samples for each language

---

## 🗂️ Project Structure

```
coderefine-ai-code-review-full-repo/
├── backend/
│   ├── main.py           ← FastAPI app (endpoints + Groq AI + parser)
│   ├── requirements.txt
│   └── .env              ← GROQ_API_KEY goes here
├── frontend/
│   ├── index.html        ← Full dark-theme UI
│   ├── script.js         ← All frontend logic
│   └── styles.css        ← Custom styles (glass cards, severity chips…)
├── requirements.txt      ← Root-level deps (same as backend)
└── .env.example
```

---

## 🚀 Quick Start

### 1. Get a Groq API Key

Sign up at [console.groq.com](https://console.groq.com) — it's free.

### 2. Configure the API key

```bash
cp .env.example backend/.env
# Edit backend/.env and paste your GROQ_API_KEY
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
cd backend
uvicorn main:app --reload
```

### 5. Open the browser

```
http://localhost:8000
```

---

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | Serves `frontend/index.html` |
| `POST` | `/api/review` | AI code review with severity breakdown |
| `POST` | `/api/rewrite` | AI code rewrite & optimization |
| `GET`  | `/health` | Health check + config status |

### POST `/api/review`

```json
{
  "code": "string",
  "language": "Python",
  "focus_areas": ["Bugs", "Security", "Performance", "Best Practices"]
}
```

### POST `/api/rewrite`

```json
{
  "code": "string",
  "language": "Python"
}
```

---

## ⚙️ Model Configuration

In `backend/main.py`:

```python
MODEL       = "llama-3.3-70b-versatile"
TEMPERATURE = 0.3
MAX_TOKENS  = 2000
TOP_P       = 0.9
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| AI Model | Llama 3.3-70b via Groq SDK |
| Frontend | HTML5 + Tailwind CSS + Vanilla JS |
| Code Highlighting | Highlight.js |
| Markdown Rendering | Marked.js |

---

## 📄 License

MIT
