# ---------------------------
# FILE: storage.py
# ---------------------------

import sqlite3
import json


# ---------------------------
# DB SETUP
# ---------------------------

DB_FILE = "skillup.db"

def init_db():
    """
    Initializes the SQLite database, creating 'jobs' and 'resumes' tables
    if they do not already exist. Includes 'job_field' and 'raw_text' in the resumes table.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        responsibilities TEXT,
        required_skills TEXT,
        normalized_skills TEXT,
        job_field TEXT,
        gig TEXT,
        UNIQUE(title, description) ON CONFLICT IGNORE
    )
    """)
    # Added UNIQUE constraint on (title, description) for basic duplicate prevention at DB level.
    # ON CONFLICT IGNORE means if a duplicate (title, description) is inserted, it will be ignored.

    # Resumes Table (only 1 resume stored at a time for demo)
    # Added 'raw_text' column for LLM inference later
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        experience TEXT,
        projects TEXT,
        skills TEXT,
        normalized_skills TEXT,
        job_field TEXT,
        raw_text TEXT -- ADDED: Store the raw text for later LLM inference
    )
    """)

    conn.commit()
    conn.close()

# ---------------------------
# Check for Duplicate Job
# ---------------------------

def job_exists(job_title: str, job_description: str) -> bool:
    """
    Checks if a job with the given title and description already exists in the database.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE title = ? AND description = ?", (job_title, job_description))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# ---------------------------
# Save Job
# ---------------------------

def save_job(job: dict) -> bool:
    """
    Saves a structured job dictionary into the 'jobs' table.
    Returns True if the job was saved, False if it was a duplicate.
    """
    job_title = job.get("job_title", "")
    job_description = job.get("description", "")

    if job_exists(job_title, job_description):
        print(f"INFO: Duplicate job detected for title: '{job_title}' and description.")
        return False # Indicate that it's a duplicate

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO jobs (title, description, responsibilities, required_skills, normalized_skills, job_field, gig)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_title,
            job_description,
            json.dumps(job.get("responsibilities", [])),
            json.dumps(job.get("required_skills", [])),
            json.dumps(job.get("normalized_skills", [])),
            job.get("job_field", ""),
            job.get("gig", "")
        ))
        conn.commit()
        return True # Indicate successful save
    except sqlite3.IntegrityError:
        print(f"INFO: Database IntegrityError - Possible duplicate job not caught by initial check: '{job_title}'")
        return False
    except Exception as e:
        print(f"ERROR: Failed to save job: {e}")
        return False
    finally:
        conn.close()


# ---------------------------
# Save Resume
# ---------------------------

def save_resume(resume: dict):
    """
    Saves a structured resume dictionary into the 'resumes' table.
    For this demo, it first clears previous resumes to keep only the latest.
    'raw_text' is now stored for later LLM inference.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # For demo: clear previous resume (keep latest only)
    cursor.execute("DELETE FROM resumes")

    cursor.execute("""
    INSERT INTO resumes (name, experience, projects, skills, normalized_skills, job_field, raw_text)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        resume.get("name", ""),
        resume.get("experience", ""),
        json.dumps(resume.get("projects", [])),
        json.dumps(resume.get("skills", [])),
        json.dumps(resume.get("normalized_skills", [])),
        resume.get("job_field", ""),
        resume.get("raw_text", "") # ADDED: Store raw text
    ))
    conn.commit()
    conn.close()


# ---------------------------
# Fetch All Jobs
# ---------------------------

def get_all_jobs():
    """
    Retrieves all jobs from the database, parsing JSON string fields back into lists.
    Ensures all skills are lowercased for consistent matching.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, responsibilities, required_skills, normalized_skills, job_field, gig FROM jobs")
    rows = cursor.fetchall()
    conn.close()

    jobs = []
    for row in rows:
        # Load JSON strings and ensure all skills within are lowercased
        required_skills_list = [s.lower() for s in json.loads(row[4])]
        normalized_skills_list = [s.lower() for s in json.loads(row[5])]
        
        jobs.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "responsibilities": json.loads(row[3]),
            "required_skills": required_skills_list, # Now a list of lowercase strings
            "normalized_skills": normalized_skills_list, # Now a list of lowercase strings
            "job_field": row[6],
            "gig": row[7],
        })
    return jobs

def get_latest_resume_for_matching():
    """
    Fetches the full latest resume data, including raw_text, for matching purposes.
    Ensures normalized_skills are converted to a set of lowercased strings.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, experience, projects, skills, normalized_skills, job_field, raw_text FROM resumes ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Ensure normalized_skills are lowercased when loaded and converted to a set
    normalized_skills_from_db = json.loads(row[4])
    normalized_skills_set = set(s.lower() for s in normalized_skills_from_db)

    return {
        "name": row[0],
        "experience": row[1],
        "projects": json.loads(row[2]),
        "skills": json.loads(row[3]),
        "normalized_skills": normalized_skills_set, # Now a set of lowercase strings
        "job_field": row[5],
        "raw_text": row[6] # Return raw_text
    }

