"""
AI Screening Agent Engine
Provides Dual-Mode Intelligence:
1. Built-in High Precision Semantic/NLP Screener (Deterministic, Offline, Zero API key required).
2. Live Google Gemini LLM Integration (Optionally enabled when API key is provided).
"""

import os
import re
import json
import math
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple, Optional

# Extended skills catalog for intelligent matching
SKILL_TAXONOMY = {
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "golang", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "sql", "bash", "shell",
    # AI & ML
    "machine learning", "deep learning", "nlp", "natural language processing", "llm",
    "llms", "large language models", "generative ai", "genai", "pytorch", "tensorflow",
    "keras", "scikit-learn", "pandas", "numpy", "transformers", "huggingface", "langchain",
    "llamaindex", "rag", "vector dbs", "pinecone", "chromadb", "weaviate", "milvus",
    "computer vision", "opencv", "spacy", "nltk",
    # Web & Frameworks
    "fastapi", "flask", "django", "react", "react.js", "next.js", "vue", "vue.js",
    "angular", "node.js", "express", "express.js", "spring boot", "asp.net", "graphql",
    "rest apis", "rest api", "html", "html5", "css", "css3", "tailwind", "tailwindcss",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "k8s", "ci/cd", "git", "github", "gitlab", "terraform", "ansible", "linux", "helm",
    # Databases & Big Data
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "cassandra", "kafka", "spark", "hadoop", "bigquery", "snowflake", "dynamodb",
    # Practices & Soft Skills
    "agile", "scrum", "system design", "microservices", "unit testing", "ci/cd pipeline",
    "leadership", "project management", "problem solving", "data visualization", "tableau", "powerbi"
}


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extracts clean plain text from PDF or TXT bytes."""
    lower_name = filename.lower()
    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore")

    elif lower_name.endswith(".pdf"):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            return "\n".join(text_parts)
        except Exception as e:
            # Fallback to string extraction
            clean_str = re.sub(r"[^\x20-\x7E\n]", " ", file_bytes.decode("latin-1", errors="ignore"))
            return clean_str

    # Fallback
    try:
        return file_bytes.decode("utf-8")
    except Exception:
        return file_bytes.decode("latin-1", errors="ignore")


def extract_candidate_info(text: str) -> Dict[str, Any]:
    """Extracts basic candidate profile entities: Name, Email, Phone, Years of Exp, Education, Skills."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Candidate Name detection
    candidate_name = "Candidate"
    if lines:
        for line in lines[:5]:
            clean_line = re.sub(r"[^\w\s]", "", line).strip()
            # If line is 2-4 capitalized words and doesn't look like a title or email
            if (1 < len(clean_line.split()) <= 4 and 
                not any(term in clean_line.lower() for term in ["resume", "curriculum", "cv", "profile", "engineer", "developer", "phone", "email"])):
                candidate_name = clean_line
                break

    # Email detection
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    email = email_match.group(0) if email_match else "Not provided"

    # If candidate name wasn't found, try getting it from email username
    if candidate_name == "Candidate" and email != "Not provided":
        local_part = email.split("@")[0]
        cleaned_parts = re.split(r"[._]", local_part)
        candidate_name = " ".join(part.capitalize() for part in cleaned_parts if len(part) > 1)

    # Phone detection
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    phone = phone_match.group(0) if phone_match else "Not provided"

    # Experience Years calculation
    experience_years = 0.0
    # Explicit mention check: "X+ years of experience" or "X years"
    exp_pattern = re.search(r"(\d+(\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?", text, re.IGNORECASE)
    if exp_pattern:
        try:
            experience_years = float(exp_pattern.group(1))
        except ValueError:
            pass

    # Year ranges check: "2018 - 2024", "2020 - Present"
    if experience_years == 0.0:
        year_ranges = re.findall(r"(20\d\d|19\d\d)\s*(?:-|to|–)\s*(20\d\d|present|current)", text, re.IGNORECASE)
        total_span = 0
        current_year = 2026
        for start_str, end_str in year_ranges:
            try:
                start_yr = int(start_str)
                end_yr = current_year if end_str.lower() in ["present", "current"] else int(end_str)
                if end_yr >= start_yr:
                    total_span += (end_yr - start_yr)
            except ValueError:
                continue
        if total_span > 0:
            experience_years = min(float(total_span), 25.0)

    # Education detection
    edu_keywords = ["ph.d", "phd", "master", "m.s.", "m.tech", "msc", "bachelor", "b.tech", "b.s.", "bsc", "b.e.", "degree", "computer science"]
    found_edu = []
    lower_text = text.lower()
    for kw in edu_keywords:
        if kw in lower_text:
            found_edu.append(kw.upper() if len(kw) <= 5 else kw.title())
    education = ", ".join(list(dict.fromkeys(found_edu))[:3]) if found_edu else "Undergraduate / Technical Degree"

    # Extracted skills
    extracted_skills = []
    for skill in SKILL_TAXONOMY:
        # Check boundary match
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, lower_text):
            extracted_skills.append(skill.title() if len(skill) > 3 else skill.upper())

    return {
        "candidate_name": candidate_name,
        "email": email,
        "phone": phone,
        "experience_years": experience_years,
        "education": education,
        "extracted_skills": sorted(list(set(extracted_skills)))
    }


def normalize_skill(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\.js$", "", s)
    if s in ["reactjs", "react.js"]:
        return "react"
    if s in ["vuejs", "vue.js"]:
        return "vue"
    if s in ["nodejs", "node.js"]:
        return "node"
    if s in ["amazon web services", "aws"]:
        return "aws"
    if s in ["google cloud", "gcp"]:
        return "gcp"
    if s in ["large language models", "llm", "llms"]:
        return "llm"
    if s in ["generative ai", "genai"]:
        return "genai"
    return s


def evaluate_resume_local(candidate_data: Dict[str, Any], job_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    """
    High-Precision deterministic AI evaluation engine.
    Calculates Skills Score, Experience Score, Education Score, and Semantic Relevance.
    Generates Strengths, Weaknesses, and Tailored Interview Questions.
    """
    job_required = [normalize_skill(s) for s in job_data.get("required_skills", [])]
    job_preferred = [normalize_skill(s) for s in job_data.get("preferred_skills", [])]
    cand_skills_norm = {normalize_skill(s): s for s in candidate_data.get("extracted_skills", [])}

    matched_skills = []
    missing_skills = []

    for req in job_required:
        if req in cand_skills_norm:
            matched_skills.append(cand_skills_norm[req])
        else:
            # Check if mentioned in raw text directly
            pattern = r"\b" + re.escape(req) + r"\b"
            if re.search(pattern, raw_text.lower()):
                matched_skills.append(req.title() if len(req) > 3 else req.upper())
            else:
                matched_skills_names = [s.lower() for s in matched_skills]
                if req not in matched_skills_names:
                    missing_skills.append(req.title() if len(req) > 3 else req.upper())

    # Skills Score (40% weight)
    if job_required:
        skills_ratio = len(matched_skills) / len(job_required)
        # Bonus for preferred skills
        pref_matches = sum(1 for p in job_preferred if p in cand_skills_norm or re.search(r"\b" + re.escape(p) + r"\b", raw_text.lower()))
        pref_bonus = (pref_matches * 3.0)
        skills_score = min(100.0, round((skills_ratio * 90.0) + pref_bonus, 1))
    else:
        skills_score = 80.0

    # Experience Score (30% weight)
    req_exp = float(job_data.get("min_experience_years", 0))
    cand_exp = float(candidate_data.get("experience_years", 0))
    if req_exp == 0:
        exp_score = 90.0
    elif cand_exp >= req_exp:
        exp_score = min(100.0, round(85.0 + ((cand_exp - req_exp) * 3.0), 1))
    else:
        # Partial credit
        exp_score = max(20.0, round((cand_exp / req_exp) * 80.0, 1))

    # Education Score (15% weight)
    edu_text = candidate_data.get("education", "").lower()
    if any(deg in edu_text for deg in ["ph.d", "phd", "master", "m.tech", "m.s."]):
        edu_score = 95.0
    elif any(deg in edu_text for deg in ["bachelor", "b.tech", "b.s.", "b.e.", "computer science"]):
        edu_score = 88.0
    elif edu_text:
        edu_score = 75.0
    else:
        edu_score = 65.0

    # Semantic Relevance Score (15% weight)
    job_desc = job_data.get("description", "").lower()
    desc_words = set(re.findall(r"\b\w{4,}\b", job_desc))
    cand_words = set(re.findall(r"\b\w{4,}\b", raw_text.lower()))
    common_terms = desc_words.intersection(cand_words)
    relevance_ratio = len(common_terms) / max(len(desc_words), 1)
    relevance_score = min(100.0, round(50.0 + (relevance_ratio * 50.0), 1))

    # Overall Composite Score
    overall_score = round(
        (skills_score * 0.40) +
        (exp_score * 0.30) +
        (edu_score * 0.15) +
        (relevance_score * 0.15),
        1
    )

    # Recommendation Verdict
    if overall_score >= 80.0:
        recommendation = "Strong Match"
    elif overall_score >= 60.0:
        recommendation = "Potential Match"
    else:
        recommendation = "Weak Match"

    # Strengths Identification
    strengths = []
    if len(matched_skills) >= max(1, len(job_required) * 0.7):
        strengths.append(f"Demonstrates strong coverage of core technical stack: {', '.join(matched_skills[:4])}.")
    if cand_exp >= req_exp and req_exp > 0:
        strengths.append(f"Exceeds minimum experience criteria with {cand_exp} years in software/domain.")
    elif cand_exp > 0:
        strengths.append(f"Hands-on background with approximately {cand_exp} years of relevant experience.")
    if any(p in cand_skills_norm for p in job_preferred):
        bonus_found = [cand_skills_norm[p] for p in job_preferred if p in cand_skills_norm]
        strengths.append(f"Possesses desired secondary competencies: {', '.join(bonus_found[:3])}.")
    if not strengths:
        strengths.append("Foundational technical literacy aligned with general job profile.")

    # Weaknesses / Skill Gaps Identification
    weaknesses = []
    if missing_skills:
        weaknesses.append(f"Missing documented hands-on evidence for: {', '.join(missing_skills[:4])}.")
    if cand_exp < req_exp:
        weaknesses.append(f"Identified experience of {cand_exp} yrs falls below required {req_exp} yrs threshold.")
    if relevance_score < 65:
        weaknesses.append("Resume wording shows moderate divergence from the specific domain vocabulary of the job.")
    if not weaknesses:
        weaknesses.append("No critical dealbreakers found; candidate profile exhibits high compatibility.")

    # AI Summary
    ai_summary = (
        f"Candidate {candidate_data['candidate_name']} is evaluated as a {recommendation} for the {job_data['title']} position "
        f"with an overall match score of {overall_score}%. Matched {len(matched_skills)} of {len(job_required)} required skills. "
        f"{'Profile strongly aligns with requirements.' if overall_score >= 80 else 'Follow up on missing technical areas during technical screen.'}"
    )

    # Tailored Interview Questions
    interview_questions = []
    if matched_skills:
        top_skill = matched_skills[0]
        interview_questions.append({
            "category": "Technical Depth",
            "question": f"Can you elaborate on your most complex project using {top_skill}? What architectural trade-offs did you make?",
            "eval_guide": f"Assess depth in {top_skill}, concurrency/scalability handling, and design rationale."
        })
    if len(matched_skills) > 1:
        skill_b = matched_skills[1]
        interview_questions.append({
            "category": "Practical Implementation",
            "question": f"How have you integrated {skill_b} into a CI/CD or production pipeline? Walk us through a bug or bottleneck you solved.",
            "eval_guide": "Look for real debugging experience, logging practices, and performance profiling."
        })
    if missing_skills:
        miss_skill = missing_skills[0]
        interview_questions.append({
            "category": "Skill Gap & Adaptability",
            "question": f"Our team relies heavily on {miss_skill}. While your resume doesn't detail it, how familiar are you with its paradigms, and how quickly could you ramp up?",
            "eval_guide": "Measure learning agility, conceptual understanding of similar tools, and enthusiasm."
        })
    interview_questions.append({
        "category": "Behavioral & Delivery",
        "question": "Describe a scenario where requirements changed midway through a sprint. How did you prioritize tasks and communicate with stakeholders?",
        "eval_guide": "Evaluates adaptability, agile communication, and delivery focus under pressure."
    })

    return {
        "overall_score": overall_score,
        "skills_score": skills_score,
        "experience_score": exp_score,
        "education_score": edu_score,
        "relevance_score": relevance_score,
        "recommendation": recommendation,
        "ai_summary": ai_summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "interview_questions": interview_questions,
        "agent_mode": "Local NLP Screener"
    }


def evaluate_with_gemini_api(api_key: str, candidate_data: Dict[str, Any], job_data: Dict[str, Any], raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Calls Google Gemini API for deep generative candidate screening.
    Falls back gracefully to local NLP engine if API error occurs.
    """
    if not api_key:
        return None

    prompt = f"""
You are an expert HR AI Agent and Technical Recruiter evaluating a candidate's resume for a specific job opening.

JOB DETAILS:
Title: {job_data.get('title')}
Department: {job_data.get('department')}
Experience Level: {job_data.get('experience_level')} (Min {job_data.get('min_experience_years')} years)
Required Skills: {json.dumps(job_data.get('required_skills', []))}
Preferred Skills: {json.dumps(job_data.get('preferred_skills', []))}
Job Description: {job_data.get('description')}

CANDIDATE PROFILE:
Name: {candidate_data.get('candidate_name')}
Email: {candidate_data.get('email')}
Phone: {candidate_data.get('phone')}
Extracted Experience Years: {candidate_data.get('experience_years')}
Extracted Education: {candidate_data.get('education')}
Resume Text:
---
{raw_text[:3000]}
---

Please produce a rigorous JSON evaluation with the following keys exactly:
{{
  "overall_score": float (0 to 100),
  "skills_score": float (0 to 100),
  "experience_score": float (0 to 100),
  "education_score": float (0 to 100),
  "relevance_score": float (0 to 100),
  "recommendation": string ("Strong Match" | "Potential Match" | "Weak Match"),
  "ai_summary": string (concise summary of candidate profile and fit),
  "strengths": list of strings (3 bullet points),
  "weaknesses": list of strings (2-3 bullet points identifying skill gaps),
  "matched_skills": list of strings,
  "missing_skills": list of strings,
  "interview_questions": [
     {{"category": string, "question": string, "eval_guide": string}},
     {{"category": string, "question": string, "eval_guide": string}},
     {{"category": string, "question": string, "eval_guide": string}},
     {{"category": string, "question": string, "eval_guide": string}}
  ]
}}

Return ONLY valid JSON. No markdown backticks, no explanations.
"""
    # Gemini REST API call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
    }
    headers = {"Content-Type": "application/json"}

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)
            parsed["agent_mode"] = "Gemini 2.5 Flash LLM"
            return parsed
    except Exception as e:
        print(f"Gemini API request failed ({e}), using local screening agent instead.")
        return None


def run_screening_agent(raw_text: str, filename: str, job_data: Dict[str, Any], api_key: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Main entry point for screening an applicant.
    Returns (candidate_data, screening_result).
    """
    # 1. Extract metadata and entities
    candidate_data = extract_candidate_info(raw_text)

    # 2. Run Evaluation (Gemini LLM if key available, else deterministic NLP)
    screening_result = None
    if api_key:
        screening_result = evaluate_with_gemini_api(api_key, candidate_data, job_data, raw_text)

    if not screening_result:
        screening_result = evaluate_resume_local(candidate_data, job_data, raw_text)

    return candidate_data, screening_result
