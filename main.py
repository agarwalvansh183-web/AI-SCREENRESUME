"""
FastAPI Server & REST API for AI-Based Resume Screening System
Integrates SQLite Database, AI Screening Agent, and Web Dashboard.
"""

import os
import io
import csv
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import database
import ai_agent
from models import JobCreate, ScreenTextRequest, StatusUpdateRequest, TestApiKeyRequest

# Initialize database tables & seed data on startup
database.init_db()

app = FastAPI(
    title="AI-Based Resume Screening System",
    description="Intelligent AI Agent for automated resume screening, ranking, skill gap analysis & interview prep",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# In-memory settings cache for Gemini API Key if user sets it via UI
APP_CONFIG = {
    "gemini_api_key": os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")),
    "forced_mode": None  # None = auto, 'local' = force NLP, 'gemini' = force Gemini
}


@app.get("/")
def serve_home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ---------------- JOB ENDPOINTS ----------------

@app.get("/api/jobs")
def get_jobs():
    return database.list_jobs()


@app.post("/api/jobs")
def create_job(job: JobCreate):
    job_id = database.create_job(
        title=job.title,
        department=job.department,
        experience_level=job.experience_level,
        min_experience_years=job.min_experience_years,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        description=job.description
    )
    return {"success": True, "job_id": job_id, "message": "Job posting created successfully"}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: int):
    job = database.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int):
    database.delete_job(job_id)
    return {"success": True, "message": f"Job {job_id} deleted"}


# ---------------- SCREENING ENDPOINTS ----------------

@app.post("/api/screen/text")
def screen_resume_text(req: ScreenTextRequest):
    job = database.get_job_by_id(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Target job not found")

    api_key = req.gemini_api_key or APP_CONFIG["gemini_api_key"]
    # Respect forced mode: if user forced local, pass empty key so agent uses NLP
    if APP_CONFIG["forced_mode"] == "local":
        api_key = ""
    candidate_data, screening_result = ai_agent.run_screening_agent(
        raw_text=req.resume_text,
        filename="pasted_resume.txt",
        job_data=job,
        api_key=api_key
    )

    if req.candidate_name:
        candidate_data["candidate_name"] = req.candidate_name
    if req.email:
        candidate_data["email"] = req.email

    candidate_id = database.save_candidate_and_screening(
        job_id=req.job_id,
        candidate_name=candidate_data["candidate_name"],
        email=candidate_data["email"],
        phone=candidate_data["phone"],
        raw_text=req.resume_text,
        extracted_skills=candidate_data["extracted_skills"],
        experience_years=candidate_data["experience_years"],
        education=candidate_data["education"],
        screening_result=screening_result
    )

    return {
        "success": True,
        "candidate_id": candidate_id,
        "candidate": candidate_data,
        "evaluation": screening_result
    }


@app.post("/api/screen/upload")
async def screen_resume_upload(
    job_id: int = Form(...),
    file: UploadFile = File(...),
    candidate_name: Optional[str] = Form(None),
    gemini_api_key: Optional[str] = Form(None)
):
    job = database.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Target job not found")

    file_bytes = await file.read()
    raw_text = ai_agent.extract_text_from_file(file_bytes, file.filename)

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from uploaded resume")

    api_key = gemini_api_key or APP_CONFIG["gemini_api_key"]
    # Respect forced mode
    if APP_CONFIG["forced_mode"] == "local":
        api_key = ""
    candidate_data, screening_result = ai_agent.run_screening_agent(
        raw_text=raw_text,
        filename=file.filename,
        job_data=job,
        api_key=api_key
    )

    if candidate_name and candidate_name.strip():
        candidate_data["candidate_name"] = candidate_name.strip()

    candidate_id = database.save_candidate_and_screening(
        job_id=job_id,
        candidate_name=candidate_data["candidate_name"],
        email=candidate_data["email"],
        phone=candidate_data["phone"],
        raw_text=raw_text,
        extracted_skills=candidate_data["extracted_skills"],
        experience_years=candidate_data["experience_years"],
        education=candidate_data["education"],
        screening_result=screening_result
    )

    return {
        "success": True,
        "candidate_id": candidate_id,
        "candidate": candidate_data,
        "evaluation": screening_result
    }


@app.post("/api/screen/batch")
async def screen_resume_batch(
    job_id: int = Form(...),
    files: List[UploadFile] = File(...),
    gemini_api_key: Optional[str] = Form(None)
):
    job = database.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Target job not found")

    results = []
    api_key = gemini_api_key or APP_CONFIG["gemini_api_key"]

    for file in files:
        try:
            file_bytes = await file.read()
            raw_text = ai_agent.extract_text_from_file(file_bytes, file.filename)
            if not raw_text.strip():
                continue

            cand_data, eval_result = ai_agent.run_screening_agent(
                raw_text=raw_text,
                filename=file.filename,
                job_data=job,
                api_key=api_key
            )

            cand_id = database.save_candidate_and_screening(
                job_id=job_id,
                candidate_name=cand_data["candidate_name"],
                email=cand_data["email"],
                phone=cand_data["phone"],
                raw_text=raw_text,
                extracted_skills=cand_data["extracted_skills"],
                experience_years=cand_data["experience_years"],
                education=cand_data["education"],
                screening_result=eval_result
            )

            results.append({
                "candidate_id": cand_id,
                "candidate_name": cand_data["candidate_name"],
                "score": eval_result["overall_score"],
                "recommendation": eval_result["recommendation"]
            })
        except Exception as e:
            print(f"Error screening {file.filename}: {e}")

    return {"success": True, "processed_count": len(results), "screenings": results}


# ---------------- CANDIDATE ENDPOINTS ----------------

@app.get("/api/candidates")
def list_candidates(
    job_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    return database.list_candidates(job_id=job_id, status=status, search=search)


@app.get("/api/candidates/{candidate_id}")
def get_candidate(candidate_id: int):
    candidate = database.get_candidate_details(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@app.patch("/api/candidates/{candidate_id}/status")
def update_status(candidate_id: int, req: StatusUpdateRequest):
    database.update_candidate_status(candidate_id, req.status, req.notes)
    return {"success": True, "message": f"Candidate status updated to '{req.status}'"}


# ---------------- ANALYTICS & EXPORT ----------------

@app.get("/api/analytics")
def get_analytics():
    return database.get_analytics_summary()


@app.get("/api/export/csv")
def export_csv(job_id: Optional[int] = Query(None)):
    candidates = database.list_candidates(job_id=job_id)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Candidate ID", "Name", "Email", "Phone", "Job Title",
        "Overall Score (%)", "Skills Score (%)", "Experience Score (%)",
        "Recommendation", "Status", "Experience Years", "Matched Skills", "Missing Skills"
    ])

    for c in candidates:
        writer.writerow([
            c["id"],
            c["candidate_name"],
            c["email"],
            c["phone"],
            c.get("job_title", ""),
            c.get("overall_score", 0),
            c.get("skills_score", 0),
            c.get("experience_score", 0),
            c.get("recommendation", ""),
            c.get("status", ""),
            c.get("experience_years", 0),
            ", ".join(c.get("matched_skills", [])),
            ", ".join(c.get("missing_skills", []))
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidate_screening_report.csv"}
    )


# ---------------- SETTINGS ----------------

@app.post("/api/settings/save-key")
def save_api_key(req: TestApiKeyRequest):
    APP_CONFIG["gemini_api_key"] = req.api_key.strip()
    # If key is cleared, reset forced mode to local
    if not APP_CONFIG["gemini_api_key"]:
        APP_CONFIG["forced_mode"] = "local"
    return {"success": True, "message": "Gemini API key updated in session"}


@app.post("/api/settings/set-mode")
def set_engine_mode(payload: dict):
    mode = payload.get("mode", "local")
    if mode not in ("local", "gemini"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'local' or 'gemini'.")
    if mode == "gemini" and not APP_CONFIG["gemini_api_key"]:
        raise HTTPException(status_code=400, detail="Cannot set Gemini mode without an API key.")
    APP_CONFIG["forced_mode"] = mode
    return {"success": True, "active_mode": mode}


@app.get("/api/settings")
def get_settings():
    has_key = bool(APP_CONFIG["gemini_api_key"])
    masked = f"...{APP_CONFIG['gemini_api_key'][-4:]}" if has_key and len(APP_CONFIG['gemini_api_key']) > 4 else ("Configured" if has_key else "None")
    forced = APP_CONFIG["forced_mode"]
    if forced == "local":
        active_mode = "local"
    elif forced == "gemini" and has_key:
        active_mode = "gemini"
    else:
        active_mode = "gemini" if has_key else "local"
    return {
        "has_gemini_key": has_key,
        "masked_key": masked,
        "forced_mode": forced,
        "active_mode": active_mode,
        "default_mode": "Gemini 2.5 Flash" if active_mode == "gemini" else "Local High-Precision NLP Screener"
    }


# Mount static assets
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
