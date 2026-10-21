"""
SQLite Database Layer for AI-Based Resume Screening System
Handles Jobs, Candidates, Screening Results, and Recruiter Audit Logs.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resume_screener.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database tables and seeds demo job postings if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        experience_level TEXT NOT NULL,
        min_experience_years INTEGER DEFAULT 0,
        required_skills TEXT NOT NULL,
        preferred_skills TEXT,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Resumes & Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        candidate_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        raw_text TEXT NOT NULL,
        extracted_skills TEXT,
        experience_years REAL DEFAULT 0,
        education TEXT,
        status TEXT DEFAULT 'Under Review', -- 'Shortlisted', 'Under Review', 'Interview Scheduled', 'Rejected'
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    )
    """)

    # AI Screening Evaluations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screenings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL UNIQUE,
        job_id INTEGER NOT NULL,
        overall_score REAL NOT NULL,
        skills_score REAL NOT NULL,
        experience_score REAL NOT NULL,
        education_score REAL NOT NULL,
        relevance_score REAL NOT NULL,
        recommendation TEXT NOT NULL, -- 'Strong Match', 'Potential Match', 'Weak Match'
        ai_summary TEXT NOT NULL,
        strengths_json TEXT,
        weaknesses_json TEXT,
        matched_skills_json TEXT,
        missing_skills_json TEXT,
        interview_questions_json TEXT,
        screened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    )
    """)

    # Audit / Activity Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Seed demo jobs if empty
    cursor.execute("SELECT COUNT(*) as count FROM jobs")
    if cursor.fetchone()["count"] == 0:
        seed_demo_jobs(cursor)
        conn.commit()

    conn.close()


def seed_demo_jobs(cursor):
    """Inserts initial realistic job descriptions for instant testing."""
    sample_jobs = [
        (
            "Senior AI / Machine Learning Engineer",
            "Engineering & AI",
            "Senior (5+ yrs)",
            5,
            json.dumps(["Python", "PyTorch", "TensorFlow", "NLP", "LLMs", "FastAPI", "Docker", "SQL"]),
            json.dumps(["Kubernetes", "LangChain", "Vector DBs", "RAG", "AWS"]),
            "We are seeking an experienced AI/ML Engineer to architect, build, and deploy generative AI agents, LLM pipelines, and computer vision systems. Must have solid Python, PyTorch/TensorFlow, and production deployment experience."
        ),
        (
            "Full Stack Python Developer",
            "Product Development",
            "Mid-Senior (3-5 yrs)",
            3,
            json.dumps(["Python", "FastAPI", "Django", "JavaScript", "React", "PostgreSQL", "Git", "REST APIs"]),
            json.dumps(["TypeScript", "Docker", "Redis", "TailwindCSS", "GraphQL"]),
            "Looking for a Full Stack Developer skilled in modern web applications. You will be building scalable APIs using FastAPI/Django and responsive frontends in React/Modern JS with relational databases."
        ),
        (
            "Data Scientist & Analytics Lead",
            "Data Science",
            "Mid-Level (3+ yrs)",
            3,
            json.dumps(["Python", "SQL", "Pandas", "Scikit-Learn", "Machine Learning", "Data Visualization", "Statistics"]),
            json.dumps(["PowerBI", "Tableau", "BigQuery", "A/B Testing", "Spark"]),
            "Join our Data Science team to discover insights, build predictive models, and optimize business decisions. Proficiency in SQL, Python data stack (Pandas, Scikit-Learn), and clear communication is required."
        )
    ]

    cursor.executemany("""
    INSERT INTO jobs (title, department, experience_level, min_experience_years, required_skills, preferred_skills, description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_jobs)


# Helper Database Queries
def list_jobs() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT j.*, COUNT(c.id) as applicant_count,
           AVG(s.overall_score) as avg_score
    FROM jobs j
    LEFT JOIN candidates c ON j.id = c.job_id
    LEFT JOIN screenings s ON c.id = s.candidate_id
    GROUP BY j.id
    ORDER BY j.id DESC
    """)
    rows = cursor.fetchall()
    jobs = []
    for r in rows:
        job = dict(r)
        job["required_skills"] = json.loads(job["required_skills"]) if job["required_skills"] else []
        job["preferred_skills"] = json.loads(job["preferred_skills"]) if job["preferred_skills"] else []
        job["avg_score"] = round(job["avg_score"], 1) if job["avg_score"] is not None else 0.0
        jobs.append(job)
    conn.close()
    return jobs


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    job = dict(row)
    job["required_skills"] = json.loads(job["required_skills"]) if job["required_skills"] else []
    job["preferred_skills"] = json.loads(job["preferred_skills"]) if job["preferred_skills"] else []
    return job


def create_job(title: str, department: str, experience_level: str, min_experience_years: int,
               required_skills: List[str], preferred_skills: List[str], description: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO jobs (title, department, experience_level, min_experience_years, required_skills, preferred_skills, description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        department,
        experience_level,
        min_experience_years,
        json.dumps(required_skills),
        json.dumps(preferred_skills),
        description
    ))
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id


def delete_job(job_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    cursor.execute("DELETE FROM candidates WHERE job_id = ?", (job_id,))
    cursor.execute("DELETE FROM screenings WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()


def save_candidate_and_screening(
    job_id: int,
    candidate_name: str,
    email: str,
    phone: str,
    raw_text: str,
    extracted_skills: List[str],
    experience_years: float,
    education: str,
    screening_result: Dict[str, Any]
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine initial status from match score
    initial_status = "Under Review"
    if screening_result["overall_score"] >= 80:
        initial_status = "Shortlisted"
    elif screening_result["overall_score"] < 50:
        initial_status = "Rejected"

    # Insert candidate
    cursor.execute("""
    INSERT INTO candidates (job_id, candidate_name, email, phone, raw_text, extracted_skills, experience_years, education, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        candidate_name,
        email,
        phone,
        raw_text,
        json.dumps(extracted_skills),
        experience_years,
        education,
        initial_status
    ))
    candidate_id = cursor.lastrowid

    # Insert screening evaluation
    cursor.execute("""
    INSERT INTO screenings (
        candidate_id, job_id, overall_score, skills_score, experience_score, education_score, relevance_score,
        recommendation, ai_summary, strengths_json, weaknesses_json, matched_skills_json,
        missing_skills_json, interview_questions_json
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        job_id,
        screening_result["overall_score"],
        screening_result["skills_score"],
        screening_result["experience_score"],
        screening_result["education_score"],
        screening_result["relevance_score"],
        screening_result["recommendation"],
        screening_result["ai_summary"],
        json.dumps(screening_result["strengths"]),
        json.dumps(screening_result["weaknesses"]),
        json.dumps(screening_result["matched_skills"]),
        json.dumps(screening_result["missing_skills"]),
        json.dumps(screening_result["interview_questions"])
    ))

    # Log activity
    cursor.execute("""
    INSERT INTO activity_logs (candidate_id, action, details)
    VALUES (?, ?, ?)
    """, (
        candidate_id,
        "Screened Candidate",
        f"Evaluated with score {screening_result['overall_score']}% ({screening_result['recommendation']})"
    ))

    conn.commit()
    conn.close()
    return candidate_id


def list_candidates(job_id: Optional[int] = None, status: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT c.*, j.title as job_title, j.department as job_department,
           s.overall_score, s.skills_score, s.experience_score, s.recommendation,
           s.ai_summary, s.matched_skills_json, s.missing_skills_json
    FROM candidates c
    JOIN jobs j ON c.job_id = j.id
    LEFT JOIN screenings s ON c.id = s.candidate_id
    WHERE 1=1
    """
    params = []

    if job_id:
        query += " AND c.job_id = ?"
        params.append(job_id)

    if status and status != "All":
        query += " AND c.status = ?"
        params.append(status)

    if search:
        query += " AND (c.candidate_name LIKE ? OR c.email LIKE ? OR c.extracted_skills LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY s.overall_score DESC, c.id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    candidates = []
    for r in rows:
        item = dict(r)
        item["extracted_skills"] = json.loads(item["extracted_skills"]) if item["extracted_skills"] else []
        item["matched_skills"] = json.loads(item["matched_skills_json"]) if item.get("matched_skills_json") else []
        item["missing_skills"] = json.loads(item["missing_skills_json"]) if item.get("missing_skills_json") else []
        candidates.append(item)

    conn.close()
    return candidates


def get_candidate_details(candidate_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.*, j.title as job_title, j.department as job_department, j.required_skills as job_required_skills,
           s.overall_score, s.skills_score, s.experience_score, s.education_score, s.relevance_score,
           s.recommendation, s.ai_summary, s.strengths_json, s.weaknesses_json,
           s.matched_skills_json, s.missing_skills_json, s.interview_questions_json, s.screened_at
    FROM candidates c
    JOIN jobs j ON c.job_id = j.id
    LEFT JOIN screenings s ON c.id = s.candidate_id
    WHERE c.id = ?
    """, (candidate_id,))

    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    item = dict(row)
    item["extracted_skills"] = json.loads(item["extracted_skills"]) if item["extracted_skills"] else []
    item["job_required_skills"] = json.loads(item["job_required_skills"]) if item["job_required_skills"] else []
    item["strengths"] = json.loads(item["strengths_json"]) if item.get("strengths_json") else []
    item["weaknesses"] = json.loads(item["weaknesses_json"]) if item.get("weaknesses_json") else []
    item["matched_skills"] = json.loads(item["matched_skills_json"]) if item.get("matched_skills_json") else []
    item["missing_skills"] = json.loads(item["missing_skills_json"]) if item.get("missing_skills_json") else []
    item["interview_questions"] = json.loads(item["interview_questions_json"]) if item.get("interview_questions_json") else []
    return item


def update_candidate_status(candidate_id: int, status: str, notes: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET status = ?, notes = COALESCE(?, notes) WHERE id = ?", (status, notes, candidate_id))
    cursor.execute("INSERT INTO activity_logs (candidate_id, action, details) VALUES (?, ?, ?)",
                   (candidate_id, "Status Updated", f"Changed status to '{status}'"))
    conn.commit()
    conn.close()


def get_analytics_summary() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM candidates")
    total_screened = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM candidates WHERE status = 'Shortlisted'")
    shortlisted_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM candidates WHERE status = 'Interview Scheduled'")
    interview_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM candidates WHERE status = 'Rejected'")
    rejected_count = cursor.fetchone()["count"]

    cursor.execute("SELECT AVG(overall_score) as avg_score FROM screenings")
    avg_score_row = cursor.fetchone()
    avg_score = round(avg_score_row["avg_score"], 1) if avg_score_row and avg_score_row["avg_score"] is not None else 0.0

    # Skill match frequency
    cursor.execute("SELECT matched_skills_json, missing_skills_json FROM screenings")
    rows = cursor.fetchall()

    top_matched = {}
    top_missing = {}
    for r in rows:
        if r["matched_skills_json"]:
            for skill in json.loads(r["matched_skills_json"]):
                top_matched[skill] = top_matched.get(skill, 0) + 1
        if r["missing_skills_json"]:
            for skill in json.loads(r["missing_skills_json"]):
                top_missing[skill] = top_missing.get(skill, 0) + 1

    conn.close()

    sorted_matched = sorted(top_matched.items(), key=lambda x: x[1], reverse=True)[:6]
    sorted_missing = sorted(top_missing.items(), key=lambda x: x[1], reverse=True)[:6]

    return {
        "total_screened": total_screened,
        "shortlisted": shortlisted_count,
        "interview_scheduled": interview_count,
        "rejected": rejected_count,
        "avg_match_score": avg_score,
        "top_matched_skills": [{"skill": k, "count": v} for k, v in sorted_matched],
        "top_missing_skills": [{"skill": k, "count": v} for k, v in sorted_missing],
    }
