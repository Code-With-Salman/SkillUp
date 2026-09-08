# SkillUp

SkillUp is an AI-powered job matching system that helps users compare their resumes with job descriptions. It extracts skills from resumes and job posts, compares them, shows missing skills, and recommends what the user should learn to improve their chances for relevant jobs.

## Features

- Upload resumes in PDF, DOCX, or TXT format
- Upload or paste job descriptions
- Resume and job description analysis using Google Gemini
- Skill extraction and normalization
- Job matching based on candidate skills
- 🟢 Green Skills - skills that match the job requirements
- 🟡 Yellow Skills - skills that can be inferred from the resume
- 🔴 Red Skills - skills required by the job but missing from the resume
- Job match percentage
- Top job matches for the uploaded resume
- Recommendations for missing skills
- SQLite database for storing data

## Tech Stack

- Python
- FastAPI
- Google Gemini API
- SQLite
- HTML
- Jinja2
- Tailwind CSS
- Uvicorn
- PyMuPDF
- python-docx

## Project Structure

```text
SkillUp/
├── main.py
├── llm.py
├── matcher.py
├── model.py
├── parser.py
├── recommender.py
├── storage.py
├── requirements.txt
├── .gitignore
└── templates/
    ├── index.html
    ├── error.html
    ├── job_preview.html
    ├── matches.html
    ├── recommendations.html
    ├── resume_preview.html
    ├── upload_job.html
    └── upload_resume.html
```

## How It Works

The user first uploads a resume. SkillUp extracts information and skills from the resume and normalizes them for matching.

Job descriptions can also be uploaded or pasted into the system. The required skills are extracted from each job and compared with the candidate's skills.

The matching results are divided into three categories:

- 🟢 **Green Skills:** Skills found in both the resume and job requirements.
- 🟡 **Yellow Skills:** Skills that are not directly mentioned but can be inferred from the resume.
- 🔴 **Red Skills:** Skills required for the job that are missing from the resume.

Based on these skills, the system calculates a match percentage and shows the most relevant jobs.

## Skill Recommendations

SkillUp also looks at the skills a user is missing for relevant jobs. It recommends skills that could be useful to learn and provides learning resources to help the user improve their profile.

## Installation

Clone the repository:

```bash
git clone https://github.com/Code-With-Salman/SkillUp.git
cd SkillUp
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project folder and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Run the project:

```bash
python main.py
```

Then open:

```text
http://localhost:8000
```

## Author

Mohammad Salman
