# ScreenAI — AI-Based Resume Screening System 🎯

A production-ready **AI-Based Resume Screening & Talent Intelligence System** built with **Python**, **FastAPI**, **SQLite Database**, and an intelligent **AI Screening Agent** (Dual-mode: High-Precision Local NLP + Google Gemini LLM integration).

Designed as the full-stack evolution of the Google Opal AI prototype into a real, local, production-grade application.

---

## ✨ Key Features

1. **🤖 Dual-Mode AI Screening Agent**:
   - **Local NLP Agent**: Fast, deterministic, and works 100% offline without needing any API key. Extracts entities (name, email, phone, tenure, education) and computes multi-dimensional match scores.
   - **Google Gemini 2.5 Flash Mode**: Connect your Google Gemini API key in Settings to unlock deep qualitative persona reasoning, nuanced evaluation, and generative insights.

2. **📊 Multi-Dimensional Candidate Scoring**:
   - **Overall Match Fit (%)** (Radial animated gauge)
   - **Core Skills Score (40%)**: Matches candidate tech stack against required & preferred role skills.
   - **Experience Fit (30%)**: Compares years of industry experience vs job seniority requirement.
   - **Education & Credentials (15%)**: Evaluates degree level (Ph.D., M.S., B.Tech, etc.).
   - **Semantic Relevance (15%)**: Keyword density and domain context alignment.

3. **🔍 Instant Gap Analysis & Strengths**:
   - **Matched Competencies** (Green badges) vs **Unverified / Missing Skills** (Red/Amber badges).
   - Candidate specific strengths and potential skill risks.

4. **❓ Tailored AI Interview Rubrics**:
   - Automatically generates targeted technical and behavioral interview questions tailored to the candidate's exact strengths and detected missing competencies.

5. **🗄️ Full SQL Database Architecture (SQLite)**:
   - Stores job openings, candidate profiles, extracted skills, multi-stage screening evaluations, and recruiter audit logs.
   - Pipeline stages: `Shortlisted`, `Interview Scheduled`, `Under Review`, `Rejected`.

6. **📁 Multiple Resume Input Formats**:
   - Drag & drop PDF files (extracted using `pypdf`).
   - Plain text resume upload (.txt / .md).
   - Direct text paste with **1-Click Preloaded Sample Resumes** (AI Lead, Fullstack, Junior).

7. **📈 Talent Pool & Recruiter Intelligence**:
   - Searchable, filterable candidate table.
   - Full AI Dossier modal with recruiter note-taking and status updates.
   - Analytics dashboard with Macro Match Rate and Top Skill Bottlenecks.
   - One-click CSV Export.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (Tested and verified on Python 3.15)
- Dependencies: `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `pypdf`

### 2. Run the Application
In your terminal, navigate to the project directory and run:

```bash
python run.py
```

Or run directly with uvicorn:
```bash
python -m uvicorn main:app --reload --port 8000
```

### 3. Open Web Dashboard
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 🗂️ Project Structure

```
ai_resume_screening_system/
├── main.py              # FastAPI server & REST API routes
├── database.py          # SQLite database schema, queries & demo seeders
├── ai_agent.py          # AI Screening Agent (NLP + Gemini API integration)
├── models.py            # Pydantic data schemas
├── run.py               # One-click startup runner
├── requirements.txt     # Python package requirements
├── resume_screener.db   # SQLite database (auto-created on startup)
└── static/
    ├── index.html       # Modern Glassmorphic Dashboard UI
    ├── style.css        # Rich dark-mode design system & animations
    └── app.js           # Client-side interactive logic & state manager
```

---

## 💡 How to Test in 10 Seconds

1. Open `http://127.0.0.1:8000` in your browser.
2. Under **Step 1**, the dropdown will have default jobs loaded (e.g. *Senior AI / Machine Learning Engineer*).
3. Click on the **Paste Text** tab.
4. Click **"Load Demo: AI Lead"** (or FullStack or Junior).
5. Click **"Run AI Screening Evaluation"**!
6. Watch the AI agent analyze the resume in real-time, generate the match score, identify skill gaps, and provide custom interview questions!
