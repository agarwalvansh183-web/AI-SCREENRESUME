"""
ScreenAI — AI-Based Resume Screening System Runner
Starts the FastAPI application with Uvicorn.
"""

import sys
import os
import uvicorn

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    print("=" * 65)
    print("  🚀 Starting ScreenAI — AI-Based Resume Screening System")
    print("  📡 Server URL: http://127.0.0.1:8000")
    print("  🗄️ Database: SQLite (resume_screener.db)")
    print("  🤖 AI Engine: Dual-Mode (Local NLP + Gemini 2.5 Flash)")
    print("=" * 65)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
