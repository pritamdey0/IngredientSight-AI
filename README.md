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
[![License: MIT](https://img.shields.io/badge/License-MIT-F7DC6F?style=for-the-badge)](./LICENSE)

<br/>

> **Upload a product label → AI & Regulatory Engine analyzes it → Get a full cosmetic safety report.**  
> A full-stack AI application combining a cinematic editorial landing page with an automated ingredient analysis dashboard.

<br/>

---

</div>

## 🧬 What is IngredientSight AI?

**IngredientSight AI** is a full-stack intelligent system that decodes the ingredient labels of cosmetic and skincare products using **RapidOCR**, **EU CosIng regulatory annexes**, **ECHA CLP hazard classifications**, and **Tavily web context**. Photograph your product label, drop it into the dashboard, and receive an authentic, source-backed safety report — with per-ingredient regulatory status, CMR categories, fragrance allergens, and verified scientific references.

The project opens with a cinematic landing page featuring a full-screen atmospheric hero, glassmorphic navigation, scroll-reveal feature panels, and an intuitive transition into the live analysis dashboard.

<br/>

---

## ✨ Feature Highlights

| 🧠 Intelligent Analysis Pipeline | 🎨 Premium Frontend |
|---|---|
| **RapidOCR Engine** — Local ONNX text extraction: zero API quota, instant label recognition | **Cinematic Landing Page** with full-screen atmospheric hero and glassmorphic nav |
| **INCI Ingredient Parser** — Normalizes, cleanses, and tokenizes complex ingredient labels | **Drop Image Dashboard** with fully transparent backdrop & subtle glow |
| **CosIng & CLP Regulatory Lookup** — Deterministic EU Annex matching (prohibited, restricted, positive list) | **Framer Motion Micro-interactions** with smooth transitions and status states |
| **Research Context** — Verbatim scientific excerpts from SCCS, CIR & PubChem via Tavily | **Editorial Typography** with crisp monochrome aesthetics & clean hierarchy |
| **LLM Synthesis** — Plain-language summary powered by Google Gemini or Groq | **Live Re-checking** with per-ingredient manual corrections in the report sheet |

<br/>

---

## 🏗️ Architecture

```
                ┌─────────────────────────────────────┐
                │         React 19 Frontend           │
                │   Vite 6 · TypeScript · Tailwind v4 │
                │        Framer Motion · Lucide       │
                └────────────────┬────────────────────┘
                                 │  REST API (HTTP)
                ┌────────────────▼────────────────────┐
                │       FastAPI Backend (Python)      │
                │  POST /api/analyze-image · /health  │
                └────────────────┬────────────────────┘
                                 │
                ┌────────────────▼────────────────────┐
                │          Analysis Pipeline          │
                │                                     │
                │  ┌──────────────────────────────┐   │
                │  │  🔍  RapidOCR (Local ONNX)   │   │
                │  │      Extracts text from pic  │   │
                │  └──────────────┬───────────────┘   │
                │            ocr_text                 │
                │  ┌──────────────▼───────────────┐   │
                │  │  🧪  INCI Parser & Matcher   │   │
                │  │      RapidFuzz + CosIng DB   │   │
                │  └──────────────┬───────────────┘   │
                │            ingredients[ ]           │
                │  ┌──────────────▼───────────────┐   │
                │  │  🔬  Tavily Research Context │   │
                │  │      Scientific sources      │   │
                │  └──────────────┬───────────────┘   │
                │            evidence & clips         │
                │  ┌──────────────▼───────────────┐   │
                │  │  🛡️  Regulatory Rules Engine │   │
                │  │      Annex II/III + CLP H-cds│   │
                │  └──────────────┬───────────────┘   │
                │            status & hazard flags    │
                │  ┌──────────────▼───────────────┐   │
                │  │  📋  LLM Summary (Gemini/Groq│   │
                │  │      Markdown + JSON Output  │   │
                │  └──────────────────────────────┘   │
                └─────────────────────────────────────┘
```

<br/>

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend Framework** | React 19 + TypeScript | Component-based reactive UI |
| **Build Tool** | Vite 6 | Fast local development server & HMR |
| **Styling** | Tailwind CSS v4 | Clean utility-first design system |
| **Animation** | Framer Motion | Smooth interaction animations & drag-and-drop feedback |
| **Icons** | Lucide React | Crisp, consistent SVG icons |
| **Backend Framework** | FastAPI | High-performance Python async REST API |
| **OCR Engine** | RapidOCR (`rapidocr-onnxruntime`) | Local ONNX engine — zero external API quota, runs entirely on device |
| **Regulatory Dataset** | EU CosIng + ECHA CLP | 4,700+ curated records covering cosmetics prohibitions, limits, and hazards |
| **LLM Reasoning** | Google Gemini / Groq | Rephrases structured findings into plain-language summaries |
| **Web Research** | Tavily Search API | Real-time scientific evidence gathering for cosmetic ingredients |
| **Python Runtime** | Python 3.11+ | Tested on Python 3.11 and 3.12 |

<br/>

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Minimum Version | Download |
|-------------|----------------|----------|
| **Node.js** | v18+ | [nodejs.org](https://nodejs.org/) |
| **Python** | v3.11+ | [python.org](https://www.python.org/) |

<br/>

### Step 1 — Clone the Repository

```bash
git clone https://github.com/pritamdey0/IngredientSight-AI.git
cd IngredientSight-AI
```

<br/>

### Step 2 — Configure Environment Variables

Create your `.env` file in the project root:

```env
# ── Recommended: Tavily Search API (Web research) ───────────────────────
TAVILY_API_KEY=tvly-dev-your_tavily_key_here

# ── Optional: LLM Providers (for friendly summary generation) ───────────
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
```

> ⚠️ **Never commit your `.env` file.** It is included in `.gitignore`.

<br/>

### Step 3 — Install Dependencies

**Backend (Python):**
```bash
pip install -r requirements.txt
```

> **Note on OCR:** `rapidocr-onnxruntime` runs completely locally with no need for external binaries like Tesseract. It works immediately out of the box.

**Frontend (Node.js):**
```bash
npm install
```

<br/>

### Step 4 — Run the Project

Open **two terminal windows**:

**Terminal 1 — Backend (FastAPI)**
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
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
| 🌐 Web Application | `http://localhost:5173` |

<br/>

---

## 🔬 How the Pipeline Works

Once you upload or drag a product label image:

```
Step 1 — 🔍  RapidOCR Engine
              Processes the image locally with ONNX Runtime models
              → Extracts full INCI text in top-down reading order

Step 2 — 🧪  INCI Parser & Normalizer
              Tokenizes ingredient commas/delimiters, resolves synonyms and handles edge cases
              → Outputs normalized list of discrete chemical and botanical names

Step 3 — 🛡️  CosIng & CLP Regulatory Analysis
              Deterministically compares against 4,700+ Annex II, III, IV, V, VI entries
              → Classifies status (Prohibited, Restricted, Positive List, Unidentified)
              → Maps CLP Hazard codes and CMR Categories

Step 4 — 🔬  Tavily Web Research
              Pulls reputable data from Europa SCCS, CIR, and scientific databases
              → Gathers clinical alerts and safety context

Step 5 — 📋  Summary & Interactive Report
              Gemini / Groq produces a structured summary of the verified facts
              → Live report card displays with candidate verifications and export options
```

<br/>

---

## 📁 Project Structure

```
IngredientSight-AI/
│
├── 📂 backend/                  # FastAPI Backend & Intelligence Services
│   ├── app.py                   # Main FastAPI server and routing
│   ├── config.py                # Environment configuration and provider logic
│   ├── data_layer.py            # Local dataset loader and normalization
│   ├── hazard_codes.py          # ECHA CLP hazard code descriptions
│   ├── llm_summary.py           # Gemini & Groq plain-language summary builders
│   ├── matcher.py               # Fuzzy matching & synonym lookup
│   ├── models.py                # Pydantic request/response schemas
│   ├── ocr.py                   # RapidOCR ONNX integration
│   ├── parser.py                # INCI list parser
│   ├── report.py                # Markdown report generator
│   ├── rules.py                 # CosIng regulatory classification rules
│   └── web_context.py           # Tavily search and source verification
│
├── 📂 data/                     # Reference Datasets
│   ├── reference.csv            # Consolidated EU CosIng Annexes & CLP data
│   └── aliases.json             # Chemical synonym map
│
├── 📂 src/                      # React 19 + TypeScript Frontend
│   ├── components/
│   │   ├── Analyzer.tsx         # Dashboard with drag-and-drop OCR
│   │   ├── NovaLandingPage.tsx  # Cinematic hero & landing experience
│   │   ├── Reveal.tsx           # Framer motion entrance animations
│   │   ├── ScrollVideoBackground.tsx # Scroll-driven video background
│   │   └── report/              # Interactive report and ingredient cards
│   ├── App.tsx                  # Root application router
│   └── main.tsx                 # Entry point
│
├── .env.example                 # Environment variable template
├── .gitignore                   # Ignore rules
├── vite.config.ts               # Vite configuration with local API proxy
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Node dependencies
└── requirements.txt             # Python dependencies
```

<br/>

---

## 🌐 API Reference

### `POST /api/analyze-image`

Upload a photo of a cosmetic ingredient label for OCR and full regulatory assessment.

**Request (`multipart/form-data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | `UploadFile` | ✅ Yes | Image file (PNG, JPG, WebP, GIF, BMP) up to 8MB |
| `product_name` | `string` | No | Optional product name |

---

### `POST /api/web-context`

Fetch real-time scientific citations for a specific cosmetic ingredient.

**Request (`application/json`):**
```json
{
  "ingredient": "Phenoxyethanol",
  "include_other": false,
  "topics": ["skin irritation", "use limits"]
}
```

---

### `GET /api/health`

Returns the current system health and status of OCR and AI engines.

```json
{
  "status": "ok",
  "dataset_loaded": true,
  "dataset_rows": 4722,
  "ocr_available": true,
  "llm_enabled": true,
  "web_context_enabled": true
}
```

<br/>

---

## 📜 License

This project is licensed underr the **MIT License**.

<br/>

---

<div align="center">

**Built with ❤️ for safer cosmetics ingredient analysis.**

*IngredientSight AI — Sourced. Cited. Not Scored.*

</div>
