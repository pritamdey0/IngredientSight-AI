<div align="center">

<br/>

```
 ██╗███╗  ██╗ ██████╗ ██████╗ ███████╗██████╗ ██╗███████╗███╗  ██╗████████╗    ███████╗██╗ ██████╗ ██╗  ██╗████████╗
 ██║████╗ ██║██╔════╝ ██╔══██╗██╔════╝██╔══██╗██║██╔════╝████╗ ██║╚══██╔══╝    ██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝
 ██║██╔██╗██║██║  ███╗██████╔╝█████╗  ██║  ██║██║█████╗  ██╔██╗██║   ██║       ███████╗██║██║  ███╗███████║   ██║   
 ██║██║╚████║██║   ██║██╔══██╗██╔══╝  ██║  ██║██║██╔══╝  ██║╚████║   ██║       ╚════██║██║██║   ██║██╔══██║   ██║   
 ██║██║ ╚███║╚██████╔╝██║  ██║███████╗██████╔╝██║███████╗██║ ╚███║   ██║       ███████║██║╚██████╔╝██║  ██║   ██║   
 ╚═╝╚═╝  ╚══╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚══════╝╚═╝  ╚══╝   ╚═╝       ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝
```

### ✦ AI-Powered Cosmetic & Skincare Ingredient Intelligence ✦

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Pipeline-FF6B35?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F7DC6F?style=for-the-badge)](./LICENSE)

<br/>

> **Upload a product label → 5 AI Agents analyze it → Get a full dermatological safety report.**  
> A full-stack AI application combining a cinematic editorial landing page with a live multi-agent analysis dashboard.

<br/>

---

</div>

## 🧬 What is IngredientSight AI?

**IngredientSight AI** is a full-stack intelligent system that decodes the ingredient labels of cosmetic and skincare products using a **5-stage autonomous AI pipeline** built with [LangGraph](https://langchain-ai.github.io/langgraph/). Simply photograph your product label, upload it to the dashboard, and receive a comprehensive, research-backed safety report — complete with a dermatological risk score, per-ingredient profiles, health warnings, and downloadable reports.

The project opens with a cinematic landing page featuring a full-screen atmospheric hero, glassmorphic navigation, scroll-reveal feature panels, and a `Get Started` CTA that transitions into the live AI analysis dashboard.

<br/>

---

## ✨ Feature Highlights

| 🧠 5-Agent AI Pipeline | 🎨 Premium Frontend |
|---|---|
| **OCR Agent** — Local-first extraction: RapidOCR (ONNX) → pytesseract → Gemini Vision fallback | **Cinematic Landing Page** with full-screen atmospheric hero and glassmorphic nav |
| **Ingredient Agent** — Parses and normalizes INCI ingredient lists | **Scroll-Reveal Feature Cards** with staggered Framer Motion entrance animations |
| **Research Agent** — Pulls clinical evidence via Tavily web search | **GSAP 3 + Framer Motion** scroll physics & micro-interactions |
| **Safety Agent** — Scores ingredients, flags allergens & irritants | **`mix-blend-mode: exclusion`** typography overlays for editorial feel |
| **Report Agent** — Generates `.md` + `.json` safety reports | **Realtime Pipeline Visualizer** showing each agent's live execution state |

<br/>

---

## 🏗️ Architecture

```
                ┌─────────────────────────────────────┐
                │         React 19  Frontend           │
                │   Vite 6 · TypeScript · Tailwind v4  │
                │    GSAP 3 · Framer Motion · Lucide    │
                └────────────────┬────────────────────-┘
                                 │  REST API (HTTP)
                ┌────────────────▼────────────────────-┐
                │       FastAPI Backend  (Python)        │
                │    POST /api/analyze · GET /api/health │
                └────────────────┬────────────────────-┘
                                 │
                ┌────────────────▼────────────────────-┐
                │      LangGraph  StateGraph Pipeline    │
                │                                       │
                │  ┌──────────────────────────────┐    │
                │  │           START              │    │
                │  └──────────────┬───────────────┘    │
                │                 │                     │
                │  ┌──────────────▼───────────────┐    │
                │  │  🔍  OCR Agent               │    │
                │  │  RapidOCR → pytesseract      │    │
                │  │  → Gemini Vision (fallback)   │    │
                │  └──────────────┬───────────────┘    │
                │            ocr_text                   │
                │  ┌──────────────▼───────────────┐    │
                │  │  🧪  Ingredient Agent         │    │
                │  │      INCI List Parser         │    │
                │  └──────────────┬───────────────┘    │
                │            ingredients[ ]             │
                │  ┌──────────────▼───────────────┐    │
                │  │  🔬  Research Agent           │    │
                │  │      Tavily Web Search        │    │
                │  └──────────────┬───────────────┘    │
                │            research_results{}         │
                │  ┌──────────────▼───────────────┐    │
                │  │  🛡️  Safety Agent             │    │
                │  │      Risk Scoring Engine      │    │
                │  └──────────────┬───────────────┘    │
                │         safety_score · risk_label     │
                │  ┌──────────────▼───────────────┐    │
                │  │  📋  Report Agent             │    │
                │  │      .md + .json Generator    │    │
                │  └──────────────┬───────────────┘    │
                │                 │                     │
                │  ┌──────────────▼───────────────┐    │
                │  │            END               │    │
                │  └──────────────────────────────┘    │
                └───────────────────────────────────────┘
```

<br/>

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend Framework** | React 19 + TypeScript | Component-based reactive UI |
| **Build Tool** | Vite 6 | Lightning-fast dev server & HMR |
| **Styling** | Tailwind CSS v4 | Utility-first design system |
| **Animation** | GSAP 3 + Framer Motion | Scroll physics & micro-interactions |
| **Icons** | Lucide React | Crisp, consistent SVG icon library |
| **Backend Framework** | FastAPI | High-performance async REST API |
| **AI Orchestration** | LangGraph (StateGraph) | Multi-agent pipeline with typed state |
| **OCR — Primary** | RapidOCR (`rapidocr-onnxruntime`) | Local ONNX engine — zero API quota, no system binary |
| **OCR — Secondary** | pytesseract | Tesseract wrapper — gracefully skipped if binary absent |
| **Vision AI — Fallback** | Google Gemini Vision | API-based OCR — only invoked when local engines fail |
| **Vision AI — Last Resort** | Groq Vision API | Final API fallback using `GROQ_API_KEY` |
| **LLM (Agents)** | Google Gemini 2.5 Flash | Powers Ingredient, Research & Safety agent reasoning |
| **Web Research** | Tavily Search API | Real-time ingredient evidence gathering |
| **Python Runtime** | Python 3.11+ | Tested on CPython 3.11 and 3.12 |

<br/>

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Minimum Version | Download |
|-------------|----------------|----------|
| **Node.js** | v18 or v24+ | [nodejs.org](https://nodejs.org/) |
| **Python** | v3.11+ | [python.org](https://www.python.org/) |

<br/>

### Step 1 — Clone the Repository

```bash
git clone https://github.com/pritamdey0/IngredientSight-AI.git
cd IngredientSight-AI
```

<br/>

### Step 2 — Configure Environment Variables

Copy the example env file and fill in your API keys:

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

Open `.env` and set your keys:

```env
# ── Required ──────────────────────────────────────────────────────────
# Google Gemini API key — powers Ingredient, Safety & OCR fallback agents
# Get yours free at: https://aistudio.google.com/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# ── Recommended ───────────────────────────────────────────────────────
# Tavily Search API — enables real-time web research per ingredient
# Get yours at: https://app.tavily.com
TAVILY_API_KEY=your_tavily_api_key_here

# ── Optional ──────────────────────────────────────────────────────────
# Groq API — used as OCR Vision fallback (Stage 4) if Gemini also fails
GROQ_API_KEY=

# Path to tesseract.exe on Windows (only needed if you install Tesseract)
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

<br/>

### Step 3 — Install Dependencies

**Backend (Python):**
```bash
# Recommended — install from the requirements file
pip install -r requirements.txt
```

> **OCR Note:** `rapidocr-onnxruntime` (the primary OCR engine) runs entirely locally with no extra system dependencies — it just works out of the box.  
> If you also want `pytesseract` as a second local fallback, install the [Tesseract binary](https://github.com/UB-Mannheim/tesseract/wiki) and set `TESSERACT_CMD` in your `.env`.

**Frontend (Node.js):**
```bash
npm install
```

<br/>

### Step 4 — Launch the Application

Open **two terminal windows** and run each command simultaneously:

**Terminal 1 — Backend (FastAPI + LangGraph)**
```bash
python server.py
```

| Service | URL |
|---------|-----|
| 🚀 API Server | `http://localhost:8000` |
| 📖 Interactive API Docs (Swagger) | `http://localhost:8000/docs` |
| ❤️ Health Check | `http://localhost:8000/api/health` |

<br/>

**Terminal 2 — Frontend (Vite Dev Server)**
```bash
npm run dev
```

| Service | URL |
|---------|-----|
| 🌐 Frontend App | `http://localhost:5173` |

<br/>

---

## 🔬 How the Pipeline Works

Once you upload a product label image, the following 5-step sequence executes automatically:

```
Step 1 — 🔍  OCR Agent  (local-first — zero API quota on primary path)
              1a. RapidOCR (ONNX, local)  — extracts text, no API calls, no system binary
              1b. pytesseract (local)      — fallback if RapidOCR yields empty result
              1c. Gemini Vision API        — API fallback if both local engines fail
              1d. Groq Vision API          — last-resort API fallback
              → Returns raw extracted text from the ingredient panel

Step 2 — 🧪  Ingredient Agent
              Parses the OCR output
              → Normalizes and identifies each INCI ingredient name

Step 3 — 🔬  Research Agent
              Queries Tavily Search for each key ingredient
              → Gathers clinical studies, safety data & usage guidelines

Step 4 — 🛡️  Safety Agent
              Evaluates each ingredient against safety references
              → Computes a dermatological safety score (0–100)
              → Flags allergens, irritants & comedogenic compounds

Step 5 — 📋  Report Agent
              Synthesizes all findings into a structured report
              → Saves as .md (human-readable) and .json (machine-readable)
              → Returns safety_score and risk_label to the dashboard
```

<br/>

---

## 📁 Project Structure

```
IngredientSight-AI/
│
├── 📂 langgraphagentic/          # Core 5-agent AI pipeline (Python)
│   ├── graph.py                  # LangGraph StateGraph definition & wiring
│   ├── ocr_agent.py              # Agent 1: RapidOCR → pytesseract → Gemini/Groq Vision
│   ├── ingredient_agent.py       # Agent 2: INCI ingredient parser
│   ├── research_agent.py         # Agent 3: Tavily web research
│   ├── safety_agent.py           # Agent 4: Safety scoring engine
│   └── report_agent.py           # Agent 5: Markdown + JSON report generator
│
├── 📂 src/                       # React + TypeScript frontend
│   ├── components/
│   │   ├── NovaLandingPage.tsx   # Cinematic landing page (hero + feature panels)
│   │   ├── LandingHero.tsx       # Full-screen hero with glassmorphic nav
│   │   ├── Reveal.tsx            # Scroll-reveal animation wrapper
│   │   ├── ScrollVideoBackground.tsx  # Scroll-driven video component
│   │   ├── Dashboard.tsx         # Main AI analysis dashboard
│   │   └── CustomCursor.tsx      # Custom cursor component
│   ├── App.tsx                   # Root component — routes landing ↔ dashboard
│   ├── main.tsx                  # Vite entry point
│   └── index.css                 # Global styles, CSS variables & liquid-glass utilities
│
├── 📂 uploads/                   # Uploaded label images (runtime, gitignored)
├── 📂 reports/                   # Generated AI reports (runtime, gitignored)
├── 📂 public/                    # Static frontend assets (images, video)
│
├── server.py                     # FastAPI app — REST endpoints, image validation
├── main.py                       # CLI entry point
├── .env.example                  # Environment variable template (safe to commit)
├── .gitignore                    # Comprehensive ignore rules
├── vercel.json                   # Vercel config with long-lived asset cache headers
├── render.yaml                   # Render.com deployment config
├── vite.config.ts                # Vite build configuration
├── tsconfig.json                 # TypeScript compiler config
├── package.json                  # Node.js dependencies & scripts
├── pyproject.toml                # Python project metadata
└── requirements.txt              # Python dependencies list
```

<br/>

---

## 🌐 API Reference

### `POST /api/analyze`

Runs the full 5-agent LangGraph pipeline on an uploaded product label image.

**Request (multipart/form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `UploadFile` | ✅ Yes | Product label image (PNG, JPG, WebP, GIF, BMP) |
| `product_name` | `string` | No | Optional display name for the product |

**Example Response:**
```json
{
  "success": true,
  "product_name": "CeraVe Moisturizing Cream",
  "safety_score": 87,
  "risk_label": "Low Risk",
  "ocr_text": "INGREDIENTS: Aqua, Glycerin, Cetearyl Alcohol ...",
  "ingredients": ["Aqua", "Glycerin", "Cetearyl Alcohol", "..."],
  "research_results": {
    "Glycerin": { "safety": "well-tolerated humectant", "sources": ["..."] }
  },
  "safety_analysis": {
    "overall_score": 87,
    "warnings": [],
    "recommendations": ["Suitable for sensitive skin"]
  },
  "markdown_report": "# IngredientSight Safety Report\n...",
  "json_report": { "product": "...", "score": 87 },
  "report_md_path": "/reports/report_abc123.md",
  "report_json_path": "/reports/report_abc123.json"
}
```

<br/>

### `GET /api/health`

Returns the current health and configuration status of the backend pipeline.

```json
{
  "status": "ok",
  "service": "IngredientSight AI LangGraph Pipeline",
  "gemini_configured": true,
  "tavily_configured": true,
  "upload_dir": "/path/to/uploads",
  "reports_dir": "/path/to/reports",
  "port": 8000,
  "host": "0.0.0.0"
}
```

<br/>

---

## 🔑 API Keys Reference

| Variable | Required | Provider | Used By |
|----------|----------|----------|---------|
| `GEMINI_API_KEY` | ✅ Required | [Google AI Studio](https://aistudio.google.com/apikey) | Ingredient, Safety agents + OCR Stage 3 fallback |
| `TAVILY_API_KEY` | ⚡ Recommended | [Tavily](https://app.tavily.com) | Research agent (real-time web search) |
| `GROQ_API_KEY` | ⚡ Optional | [Groq Console](https://console.groq.com) | OCR Vision fallback — Stage 4 last resort |
| `TESSERACT_CMD` | ⚡ Optional | [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) | Points pytesseract to the binary on Windows |

> Without `TAVILY_API_KEY`, the Research Agent gracefully falls back to LLM-only knowledge. All core features remain fully operational.  
> Without `GROQ_API_KEY`, the Groq Vision fallback is simply skipped — no errors thrown.

<br/>

---

## 🚢 Production Deployment (Vercel + Render)

This project is deployed **free** with a split architecture: the React frontend lives on **Vercel**, and the FastAPI + LangGraph backend lives on **Render** (Vercel's free tier cannot host Python services).

```
 Vercel (frontend, auto-deploys on every git push)        Render (backend, free Web Service)
 ingredient-sight-ai.vercel.app      ── REST (HTTPS) ──▶  ingredientsight-ai.onrender.com
```

### Backend — Render (free tier)

1. Create a **New Web Service** from the GitHub repo (`pritamdey0/IngredientSight-AI`)
2. Configure:
   | Setting | Value |
   |---------|-------|
   | Environment | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python server.py` |
   | Instance Type | `Free` |
3. Add environment variables: `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `TAVILY_API_KEY`, `GROQ_API_KEY` (all **Secret**), plus `PYTHON_VERSION=3.11.9`
4. In **Settings**, set **Health Check Path** to `/api/health`
5. Do **not** set `PORT` — Render injects it automatically and `server.py` reads it

> ℹ️ The free tier sleeps after ~15 minutes of inactivity. The dashboard handles this gracefully: it retries the health check for up to ~2 minutes showing *"Waking up backend (free tier cold start)…"* while Render boots (60–90 s). Analyses take 2–4 minutes on the free 0.1 CPU instance.

### Frontend — Vercel

1. Import the same GitHub repo in Vercel — deploys **auto-trigger on every push to `main`**
2. Add the environment variable **`VITE_API_URL = https://ingredientsight-ai.onrender.com`** (this is baked into the build by `vite.config.ts` via `__BACKEND_URL__`)
3. Framework preset: **Vite** · Build: `npm run build` · Output: `dist`
4. ⚠️ If you change `VITE_API_URL`, you must **redeploy** for it to take effect — it is read at build time, not runtime

### Local ↔ Cloud development

`vite.config.ts` proxies `/api/*` to the local backend during development, following `SERVER_PORT`/`PORT` from your `.env` (default `8000`). With `VITE_API_URL` unset locally, the app talks to your own `python server.py`.

<br/>

---

## 🛡️ Security Notes

- Uploaded files are validated against **image magic bytes** (not just file extensions) — spoofed file types are rejected before OCR ever runs
- The `.env` file is **gitignored** — your API keys are never committed to version control
- **If any key was ever accidentally committed**, rotate it immediately at the provider's console and generate a fresh one. You should also purge it from git history using `git filter-branch` or `git-filter-repo`
- CORS is restricted to explicit origins: local dev (`localhost:3000` / `localhost:5173`) plus any `*.vercel.app` deployment — with credentials disabled per the CORS spec
- All uploaded files are stored with a random UUID prefix — filenames cannot be predicted or enumerated

<br/>

---

## 📝 Changelog

### v1.2.0 — Production Deployment + Reliability Hardening

**☁️ Deployment (Vercel + Render, free tier)**
- 🚀 Backend deployed to Render as a free Web Service; frontend to Vercel with GitHub auto-deploy on every push
- 📄 `render.yaml` fixed — removed invalid `PORT` env-var declaration (`generateValue` is not a valid blueprint key; Render injects `PORT` automatically)
- 🔧 `vite.config.ts` dev proxy now follows `SERVER_PORT`/`PORT` from `.env` instead of hard-coding `8000`

**🐛 Bug Fixes**
- 🆙 All Gemini calls migrated from retired `gemini-1.5-flash` → `gemini-2.5-flash` (the old model ID had been fully retired, breaking every agent)
- 🆙 Groq vision fallback updated to the current `qwen/qwen3.8-27b` model (`llama-3.2-11b-vision-preview` deprecated)
- 🐛 Fixed `ocr_agent.py` crash when RapidOCR returns a scalar elapsed time instead of a list
- ⚡ `/api/analyze` converted to a sync route so multi-minute pipeline runs execute in Starlette's threadpool instead of blocking the event loop (dashboard health checks no longer freeze during analysis)
- 🧴 Removed the dead `SAMPLE_IMAGE` fallback — requests without a real label image now fail fast with a clear HTTP 400 instead of silently analyzing a bundled sample
- 🛡️ CORS hardened: explicit origins + `*.vercel.app` regex, `allow_credentials` disabled (wildcard + credentials is invalid per spec and was silently rejecting browser requests)
- 🧪 Research Agent now matches OCR'd ingredients with normalized exact-first lookup (no more `Aqua` fetching research for `Aquaphthalmica` via loose substring collisions)
- 🩺 Safety Agent negation regex tightened (`no parabens …` no longer flags parabens); `\b(?!un)safe\b` prevents "unsafe"/"unsafe" misclassification
- 📁 Report filenames include a short UUID suffix — concurrent same-second analyses can no longer overwrite each other's files
- 🧹 Deleted dead `extract_safety_score()` (never called, crashed on `None` responses)
- 🧩 `pytesseract` and `rapidocr-onnxruntime` added to `pyproject.toml` (previously only in `requirements.txt`)
- 📝 `.env.example` invalid box-drawing separator lines replaced with proper `#` comments (they were parsed as bogus key/value pairs by `python-dotenv`)

**💚 Cold-start resilience (Render free tier)**
- 🔄 Dashboard health check is now a patient retry loop (up to ~2 min) showing *"Waking up backend (free tier cold start)…"* instead of a false "Backend not connected" after 6 s
- 🧪 Frontend now fails fast with a clear message if no file is attached, instead of sending a doomed `FormData`

### v1.1.0 — Local-First OCR + Cinematic Landing Page

**🔍 OCR Engine — Replaced API-only with local-first multi-stage pipeline**
- 🆕 **RapidOCR** (`rapidocr-onnxruntime`) is now the **primary OCR engine** — runs entirely locally using ONNX models, no system binary required, zero API quota consumption, no rate-limit risk
- 🆕 **pytesseract** added as **secondary local fallback** — gracefully skipped if the Tesseract binary is not installed; configurable via `TESSERACT_CMD` env var
- ✅ **Gemini Vision API** demoted to Stage 3 — only called when both local engines fail
- ✅ **Groq Vision API** added as **Stage 4 last-resort fallback** (uses `GROQ_API_KEY`)
- 🗑️ Removed EasyOCR dependency (failed to install in target environment; replaced by lighter alternatives)
- This change eliminates rate-limit errors entirely when running multiple analyses in quick succession

**🎨 Frontend — Cinematic Landing Page Overhaul**
- 🆕 `NovaLandingPage.tsx` — new cinematic landing page with full-screen atmospheric hero, glassmorphic navbar, scroll-reveal frosted capability panel, and `Get Started` CTA
- 🆕 `LandingHero.tsx` — standalone hero section component with `Instrument Serif` display typography
- 🆕 `Reveal.tsx` — reusable scroll-reveal animation wrapper using Framer Motion
- 🆕 `ScrollVideoBackground.tsx` — scroll-driven video background component
- 🎨 `index.css` — updated with `Instrument Serif` + `Inter` font stack, `--liquid-glass` CSS utility class, refined design tokens and CSS variables
- 🚀 `vercel.json` — added long-lived `Cache-Control: public, max-age=31536000, immutable` headers for `/assets/*` — dramatically improves repeat-visit load times on deployed site
- 🎨 Dashboard background updated to match the landing page's deep teal/midnight palette

**🔒 Backend & Security**
- ✅ `server.py` — image magic-byte validation (PNG/JPEG/WebP/GIF/BMP headers checked, not just file extensions)
- ✅ `server.py` — explicit `400` errors instead of silently falling back to the bundled sample image
- ✅ `server.py` — static file mounts for `/uploads` and `/reports` endpoints so saved reports are reachable via direct URLs
- ✅ `.gitignore` — hardened to cover all `.env` variants (`*.env`, `.env.*`), Python cache dirs, test artifacts, and the `.freebuff` scratch folder

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. **Fork** the repository
2. Create your feature branch: `git checkout -b feat/your-feature-name`
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: add amazing new feature"
   ```
4. Push to your branch: `git push origin feat/your-feature-name`
5. Open a **Pull Request** and describe your changes

<br/>

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for full details.

<br/>

---

<div align="center">

**Built with ❤️ using LangGraph · FastAPI · React 19 · Google Gemini**

*IngredientSight AI — Know exactly what's in your product.*

<br/>

[![GitHub Stars](https://img.shields.io/github/stars/pritamdey0/IngredientSight-AI?style=social)](https://github.com/pritamdey0/IngredientSight-AI)
[![GitHub Forks](https://img.shields.io/github/forks/pritamdey0/IngredientSight-AI?style=social)](https://github.com/pritamdey0/IngredientSight-AI/fork)

</div>
