# ---------------------------
# FILE: llm.py
# ---------------------------

import json
# Keep json for json.loads and other json operations

from model import call_gemini_with_fallback # Import the new fallback function


# ---------------------------
# Job/Resume Parsing & Structuring
# ---------------------------

async def normalize_skills(data: dict | str, mode="job") -> dict:
    """
    Parses raw text (job description or resume) using Gemini, extracts structured data,
    and normalizes skills. Returns a dictionary with parsed data or an error.
    IMPORTANT: For both job and resume, normalized_skills will now be STRICTLY
    based on explicit mentions, without inference of new skills beyond standardization.
    """
    raw_text = data if isinstance(data, str) else data.get("raw_text", "")

    if not raw_text.strip():
        return {"error": "No content provided for AI parsing. Please provide valid text or file.", "raw_text": raw_text}

    prompt = ""
    if mode == "job":
        prompt = f"""
You are an intelligent job parser. Given the raw job description below, extract the following fields as JSON:

- job_title (string)
- description (string)
- responsibilities (list of strings)
- required_skills (list of strings, ONLY explicitly mentioned skills, ALL IN LOWERCASE)
- job_field (string, e.g., "graphic design", "software engineering", "data science", "marketing", ALL IN LOWERCASE)
- normalized_skills (list of strings, cleaned and standardized versions of EXPLICITLY mentioned skills, ALL IN LOWERCASE)

For 'required_skills', list ONLY the skills that are explicitly stated as requirements in the job description. Do NOT infer any skills for this list. All skills in this list MUST be in LOWERCASE.

For 'normalized_skills', apply a comprehensive and global standardization. This means:
- **Expansion**: Expand common abbreviations (e.g., "JS" → "javascript", "ML" → "machine learning", "AR/VR" -> "augmented reality", "virtual reality").
- **Splitting**: Separate combined skills into individual components (e.g., "HTML/CSS" → "html", "css").
- **Standardization**: Convert variants to a single, common lowercase form (e.g., "UI/UX" → "ui", "ux", "Adobe Photoshop" → "photoshop", "Adobe Illustrator" → "illustrator", "Adobe XD" → "xd", "3ds Max" -> "3d studio max", "CorelDRAW" -> "coreldraw").
- **Consistency**: Ensure uniform spelling and phrasing.
- **CRITICAL: Strict Adherence to Explicit Mentions**: Do NOT infer or add any skills that are not directly and explicitly stated or a direct standardized variant of a stated skill from the job description. The 'normalized_skills' list must strictly represent the explicit skill requirements of the job, just in a cleaner, standardized format. ALL skills in this list MUST be in LOWERCASE.

ONLY return clean JSON. No comments or extra explanations.

Job Description:
{raw_text}
"""

    elif mode == "resume":
        prompt = f"""
You are an expert resume parser. Given this resume content, extract the following fields in JSON:

- name (string)
- experience (string, short summary of total experience)
- projects (list of strings, bullet points/summaries of key projects)
- skills (list of strings, raw skills as found)
- normalized_skills (list of strings, cleaned, expanded, and standardized skills from the resume, ALL IN LOWERCASE)
- job_field (string, infer the primary professional field/area, e.g., "software development", "ui/ux design", "project management", ALL IN LOWERCASE)

For 'normalized_skills', apply a comprehensive and global standardization. This means:
- **Expansion**: Expand common abbreviations (e.g., "JS" → "javascript", "ML" → "machine learning", "AR/VR" -> "augmented reality", "virtual reality").
- **Splitting**: Separate combined skills into individual components (e.g., "HTML/CSS" → "html", "css").
- **Standardization**: Convert variants to a single, common lowercase form (e.g., "UI/UX" → "ui", "ux", "Adobe Photoshop" → "photoshop", "Adobe Illustrator" → "illustrator", "Adobe XD" → "xd", "3ds Max" -> "3d studio max", "CorelDRAW" -> "coreldraw").
- **Consistency**: Ensure uniform spelling and phrasing.
- **CRITICAL: Strict Adherence to Explicit Mentions**: Do NOT infer or add any skills that are not directly and explicitly stated or a direct standardized variant of a stated skill from the job description. The 'normalized_skills' list must strictly represent the explicit skill requirements of the job, just in a cleaner, standardized format. ALL skills in this list MUST be in LOWERCASE.

Ensure all skills and the 'job_field' are in LOWERCASE.

ONLY return clean JSON. No comments or extra explanations.

Resume Content:
{raw_text}
"""
    else:
        return {"error": "Invalid mode specified for skill normalization.", "raw_text": raw_text}

    try:
        response_text = await call_gemini_with_fallback(prompt) # <--- UPDATED CALL

        # Remove Markdown code block delimiters if present
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-len("```")].strip()

        parsed_json = json.loads(response_text)
        return parsed_json
    except json.JSONDecodeError:
        print(f"⚠️ JSON parsing failed. Gemini returned: {response_text}")
        return {"error": "Failed to parse LLM response as JSON.", "llm_raw_response": response_text, "raw_text": raw_text}
    except ConnectionError as e:
        # ConnectionError is now raised by call_gemini_with_fallback if all models fail
        return {"error": f"Network error during AI processing: {e}", "raw_text": raw_text}
    except ValueError as e:
        # ValueError can be raised by call_gemini_with_fallback for API errors
        return {"error": f"AI processing error: {e}", "raw_text": raw_text}
    except Exception as e:
        print(f"⚠️ An unexpected error occurred during LLM processing: {e}")
        return {"error": f"An unexpected error occurred during AI processing: {e}", "raw_text": raw_text}


# ---------------------------
# Job Gig Generation
# ---------------------------

async def generate_job_gig(job_structured: dict) -> str:
    """
    Generates a professional job gig using Gemini based on structured job data.
    """
    def safe(key):
        return job_structured.get(key, "Not specified")

    responsibilities_list = job_structured.get("responsibilities", [])
    required_skills_list = job_structured.get("required_skills", [])

    prompt = f"""
You are a creative and professional job gig writer. Create an engaging job post based on the following structured data:

Title: {safe("job_title")}
Description: {safe("description")}
Responsibilities: {", ".join(responsibilities_list) if responsibilities_list else "Not specified"}
Required Skills: {", ".join(required_skills_list) if required_skills_list else "Not specified"}
Job Field: {safe("job_field")}

Make it clean, modern, friendly, and concise. Highlight key aspects to attract top talent.
"""
    try:
        # Also apply the stripping logic for gig generation, as LLMs might also wrap this.
        generated_gig_raw = await call_gemini_with_fallback(prompt) # <--- UPDATED CALL
        if generated_gig_raw.startswith("```"): # Check for generic markdown code block
            # This is a simpler strip, assuming it's just code block markers without language specifier
            generated_gig_raw = generated_gig_raw[generated_gig_raw.find('\n')+1:].strip()
            if generated_gig_raw.endswith("```"):
                generated_gig_raw = generated_gig_raw[:-len("```")].strip()
        return generated_gig_raw
    except Exception as e:
        print(f"⚠️ Error generating job gig with LLM: {e}")
        return "Failed to generate job gig. Please try again or provide manual content."

# ---------------------------
# Resume-based Skill Inference (for Yellow Skills)
# ---------------------------

async def infer_yellow_skills_from_resume(resume_content: str, explicitly_missing_job_skills: list[str]) -> list[str]:
    """
    Uses the LLM to infer 'yellow skills' from the resume's raw content.
    Yellow skills are those not explicitly listed but can be confidently inferred
    from other descriptions in the resume (e.g., experience, projects).
    These are broader, often "ethical" or soft skills, or higher-level concepts
    inferred from more granular descriptions.

    Crucially, yellow skills MUST NOT be:
    - Specific programming languages (e.g., Python, Java, C++, JavaScript)
    - Specific AI/ML frameworks/libraries (e.g., TensorFlow, PyTorch, Scikit-learn)
    - Specific software tools (e.g., Blender, AutoCAD, Microsoft Word, Photoshop)

    Instead, they should be:
    - Ethical skills (e.g., communication, teamwork, leadership, problem-solving, adaptability)
    - Broader conceptual skills inferred from related experience (e.g., "Video Editing" if "motion graphics," "color grading," "storyboarding" are mentioned; "Data Analysis" if "statistical modeling," "report generation" are mentioned).
    - Design-related principles (e.g., "Layout Design", "User Experience").

    Returns a JSON list of inferred yellow skills (all lowercased).
    """
    prompt = f"""
You are an expert in resume analysis. Your task is to identify "yellow skills" from a resume.
"Yellow skills" are those that are NOT explicitly mentioned but can be confidently inferred
from the resume's content (experience, projects, etc.) based on the 'Explicitly Missing Job Skills' list.

CRITICAL RULES for Yellow Skills:
1.  **MUST NOT** be specific programming languages (e.g., python, java, c++, javascript).
2.  **MUST NOT** be specific AI/ML frameworks/libraries (e.g., tensorflow, pytorch, scikit-learn).
3.  **MUST NOT** be specific software tools (e.g., blender, autocad, microsoft word, photoshop, excel).
4.  **MUST** be broader conceptual skills, "ethical skills" (soft skills), or design-related principles.
    * **Examples of acceptable yellow skills:** "communication", "teamwork", "leadership", "problem-solving", "adaptability", "critical thinking", "negotiation", "client management", "strategic planning", "data analysis" (if inferred from data-related tasks), "layout design", "user experience", "video editing" (if inferred from motion graphics, color grading, etc.), "content creation".
    * **Inference Example:** If the resume mentions "managed a team of 10" or "presented research findings," you could infer "leadership" or "communication". If "motion graphics" and "color correction" are mentioned, you could infer "video editing".

Resume Content:
{resume_content}

Explicitly Missing Job Skills (these are the 'red skills' from the initial match):
{json.dumps(explicitly_missing_job_skills)}

Infer relevant "yellow skills" from the 'Explicitly Missing Job Skills' list that you can confidently determine
the resume owner possesses based on the 'Resume Content' and STRICTLY following the CRITICAL RULES above.

Return ONLY a JSON list of the inferred yellow skills. All inferred skills MUST be in LOWERCASE.
If no skills can be inferred under these strict rules, return an empty list `[]`.

Example JSON response:
["communication", "leadership", "data analysis"]
"""
    try:
        response_text = await call_gemini_with_fallback(prompt) # <--- UPDATED CALL

        # Remove Markdown code block delimiters if present
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-len("```")].strip()

        inferred_skills = json.loads(response_text)
        if isinstance(inferred_skills, list) and all(isinstance(s, str) for s in inferred_skills):
            # Ensure all returned skills are lowercased and unique
            return sorted(list(set([s.lower() for s in inferred_skills])))
        else:
            print(f"⚠️ LLM returned invalid format for inferred skills: {response_text}")
            return [] # Return empty list if format is incorrect
    except (json.JSONDecodeError, ConnectionError, ValueError) as e:
        print(f"⚠️ Error inferring yellow skills with LLM: {e}")
        return [] # Return empty list on error
    except Exception as e:
        print(f"⚠️ An unexpected error occurred during yellow skill inference: {e}")
        return []