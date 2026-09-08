# SkillUp 🚀

SkillUp is an AI-powered job-fit assistant designed to improve the connection between job seekers and job opportunities. It analyzes resumes and job descriptions, normalizes skills using AI, matches candidates with relevant jobs, identifies skill gaps, and provides personalized learning recommendations.

## ✨ Features

- 📄 Upload resumes in PDF, DOCX, or TXT format
- 💼 Upload or paste job descriptions
- 🤖 AI-powered resume and job description analysis using Google Gemini
- 🧠 Automatic skill extraction and normalization
- 🎯 Intelligent job matching based on candidate skills
- 🟢 Green Skills — skills explicitly matched between the resume and job
- 🟡 Yellow Skills — skills inferred from resume context using AI
- 🔴 Red Skills — skills required by the job but missing from the resume
- 📊 Job match percentage calculation
- 🏆 Displays the Top 5 most relevant job matches
- 📚 Personalized skill recommendations
- 💾 SQLite database for storing jobs and resume information
- 🔄 Gemini model fallback mechanism for improved reliability

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** HTML, Jinja2, Tailwind CSS
- **AI / LLM:** Google Gemini API
- **Database:** SQLite
- **Server:** Uvicorn
- **File Processing:** PyMuPDF, python-docx
- **API Communication:** HTTPX
- **Environment Management:** python-dotenv

## 📁 Project Structure

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

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Code-With-Salman/SkillUp.git
cd SkillUp
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API

Create a `.env` file in the root directory and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Important:** Never upload your `.env` file or API keys to GitHub.

### 4. Run the application

```bash
python main.py
```

Then open:

```text
http://localhost:8000
```

## 🧠 How Skill Matching Works

SkillUp compares the normalized skills extracted from a candidate's resume with the skills required by job descriptions.

- 🟢 **Green Skills:** Skills explicitly present in both the resume and job requirements.
- 🟡 **Yellow Skills:** Skills inferred from the candidate's resume context using AI.
- 🔴 **Red Skills:** Skills required by the job but missing from the candidate's resume.

Based on these results, SkillUp calculates a match percentage and ranks the most relevant job opportunities.

## 📚 Skill Recommendations

SkillUp analyzes missing skills across relevant job opportunities and recommends skills that the user should consider learning.

This helps users understand:

- What skills they already have
- What skills can be inferred from their experience
- What skills they are missing
- What they should learn next

## 🔐 Security

Sensitive information such as API keys is stored using environment variables and excluded from version control using `.gitignore`.

```text
.env
skillup.db
__pycache__/
*.pyc
*.pyo
.DS_Store
venv/
.venv/
```

## 🎯 Project Goal

The goal of SkillUp is to make job matching more intelligent and useful than traditional keyword-based systems by combining structured skill comparison with AI-assisted contextual understanding.

## 👨‍💻 Author

**Mohammad Salman**

GitHub: **Code-With-Salman**

## 📄 License

This project was developed for educational and portfolio purposes.
