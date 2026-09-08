# ---------------------------
# FILE: main.py
# ---------------------------

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import ast
import uvicorn

from parser import parse_job_file, parse_resume_file
from llm import generate_job_gig, normalize_skills # infer_yellow_skills_from_resume is used by matcher
from storage import init_db, save_job, save_resume, get_latest_resume_for_matching # Import new storage func
from matcher import match_jobs_to_resume # This will now be async
from recommender import get_skill_recommendations # This will now be async

from dotenv import load_dotenv
load_dotenv()

# ---------------------------
# App Initialization
# ---------------------------

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()


# ---------------------------
# ROUTES
# ---------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Renders the home page with options to upload job or resume.
    """
    return templates.TemplateResponse("index.html", {"request": request})


# --- JOB FLOW ---

@app.get("/upload-job", response_class=HTMLResponse)
async def upload_job(request: Request):
    """
    Renders the job upload form.
    """
    return templates.TemplateResponse("upload_job.html", {"request": request})


@app.post("/parse-job", response_class=HTMLResponse)
async def parse_job(request: Request, job_file: UploadFile = File(None), job_text: str = Form(None)):
    """
    Parses job description from file or text, normalizes skills with LLM,
    generates a job gig, and shows a preview.
    """
    content = await parse_job_file(job_file, job_text)

    if not content.strip():
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "No job description content provided or extracted from file.",
            "details": "Please upload a valid file (PDF, DOCX, TXT) or paste text directly into the text area."
        })

    structured_job_data = await normalize_skills(content, mode="job")

    if "error" in structured_job_data:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"Failed to process job description with AI: {structured_job_data.get('error', 'Unknown error')}",
            "details": f"Raw text sent to AI: {structured_job_data.get('raw_text', 'N/A')}<br>AI raw response: {structured_job_data.get('llm_raw_response', 'N/A')}"
        })

    generated_gig = await generate_job_gig(structured_job_data)

    return templates.TemplateResponse("job_preview.html", {
        "request": request,
        "gig_text": generated_gig,
        "structured_data": str(structured_job_data)
    })


@app.post("/save-job")
async def save_job_route(gig_text: str = Form(...), structured_data: str = Form(...)):
    """
    Saves the generated job gig and its structured data to the database.
    Checks for duplicates before saving.
    """
    try:
        structured = ast.literal_eval(structured_data)
        structured["gig"] = gig_text

        job_saved_successfully = save_job(structured)

        if job_saved_successfully:
            return RedirectResponse(url="/", status_code=302)
        else:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "message": "This job appears to be a duplicate.",
                "details": "A job with the same title and description already exists in our database. Please upload a unique job."
            }, status_code=409)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid structured data received: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save job: {e}")


# --- RESUME FLOW ---

@app.get("/upload-resume", response_class=HTMLResponse)
async def upload_resume(request: Request):
    """
    Renders the resume upload form.
    """
    return templates.TemplateResponse("upload_resume.html", {"request": request})


@app.post("/parse-resume", response_class=HTMLResponse)
async def parse_resume(request: Request, resume_file: UploadFile = File(...)):
    """
    Parses resume content from PDF, normalizes skills with LLM,
    saves the resume, and shows a preview.
    """
    resume_content_dict = await parse_resume_file(resume_file)
    raw_resume_text = resume_content_dict.get("raw_text", "")

    if not raw_resume_text.strip():
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "No content extracted from your resume file.",
            "details": "Please ensure the PDF/DOCX/TXT file is valid and contains readable text. Only PDF, DOCX, TXT are supported for now."
        })

    # Pass the entire resume_content_dict to normalize_skills, which includes raw_text
    normalized_resume = await normalize_skills(resume_content_dict, mode="resume")

    # Add the raw_text to the normalized_resume dict before saving
    normalized_resume["raw_text"] = raw_resume_text

    if "error" in normalized_resume:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"Failed to process resume with AI: {normalized_resume.get('error', 'Unknown error')}",
            "details": f"Raw text sent to AI: {normalized_resume.get('raw_text', 'N/A')}<br>AI raw response: {normalized_resume.get('llm_raw_response', 'N/A')}"
        })

    save_resume(normalized_resume) # Save the normalized resume data

    return templates.TemplateResponse("resume_preview.html", {
        "request": request,
        "resume": normalized_resume
    })


@app.post("/match-resume", response_class=HTMLResponse)
async def match_resume_route(request: Request):
    """
    Finds and displays the top job matches for the latest uploaded resume.
    This route is now async because match_jobs_to_resume is async.
    """
    matches = await match_jobs_to_resume()
    if not matches:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "No job matches found.",
            "details": "Either no resume has been uploaded yet, or no jobs have been saved, or no matches were found based on skills and fields."
        })
    return templates.TemplateResponse("matches.html", {
        "request": request,
        "matches": matches
    })


@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations(request: Request):
    """
    Provides personalized skill recommendations based on missing skills.
    This route is now async.
    """
    skills = await get_skill_recommendations()
    if not skills:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "No skill recommendations available.",
            "details": "This might happen if no resume or jobs have been processed, or if your resume matches all available jobs perfectly!"
        })
    return templates.TemplateResponse("recommendations.html", {
        "request": request,
        "skills": skills
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)