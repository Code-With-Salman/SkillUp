# ---------------------------
# FILE: recommender.py
# ---------------------------

import sqlite3
import json
from collections import Counter
# from llm import call_gemini # No longer needed if not using LLM for links


# ---------------------------
# Get Skill Gaps for Resume
# ---------------------------

def get_resume_skills_and_field():
    """
    Fetches the normalized skills and job field from the latest resume in the DB.
    """
    conn = sqlite3.connect("skillup.db")
    cursor = conn.cursor()
    # Fetch job_field too to potentially narrow down recommendations
    cursor.execute("SELECT normalized_skills, job_field FROM resumes ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return set(), None
    return set(json.loads(row[0])), row[1]


# ---------------------------
# Top Missing Skills
# ---------------------------

def get_top_missing_skills(limit=5):
    """
    Identifies the top missing skills (skills required by jobs but not on resume).
    Considers the resume's job field to focus recommendations.
    """
    resume_skills, resume_field = get_resume_skills_and_field()
    if not resume_skills:
        return [] # No resume, no missing skills

    conn = sqlite3.connect("skillup.db")
    cursor = conn.cursor()

    # Get all job skills
    cursor.execute("SELECT normalized_skills, job_field FROM jobs")
    all_job_skills_data = cursor.fetchall()
    conn.close()

    missing_skills_counter = Counter()

    for job_normalized_skills_json, job_field in all_job_skills_data:
        job_normalized_skills = set(json.loads(job_normalized_skills_json))

        # Only consider jobs that match the resume's field, if a resume field is defined
        if resume_field and job_field and resume_field != job_field:
            continue

        # Skills required by the job but not explicitly in the resume
        skills_missing_from_resume = job_normalized_skills.difference(resume_skills)
        missing_skills_counter.update(skills_missing_from_resume)

    # Return top N most frequently missing skills
    return [skill for skill, count in missing_skills_counter.most_common(limit)]


# ---------------------------
# Recommendation Link Generation
# ---------------------------

def recommend_learning_links(skills: list[str]) -> list[dict]:
    """
    Generates static learning links for a given list of skills,
    grouped by skill and including multiple platforms.
    """
    recommendations_by_skill = []
    base_urls = {
        "Udemy": "https://www.udemy.com/courses/search/?q=",
        "Coursera": "https://www.coursera.org/search?query=",
        "YouTube": "https://www.youtube.com/results?search_query=" # Standard Youtube URL
    }

    for skill in skills:
        skill_entry = {
            "name": skill.title(), # Capitalize for display
            "resources": []
        }
        for platform, base_url in base_urls.items():
            encoded_skill = skill.replace(" ", "+")
            link = f"{base_url}{encoded_skill}"
            skill_entry["resources"].append({
                "platform": platform,
                "link": link
            })
        recommendations_by_skill.append(skill_entry)
    return recommendations_by_skill

# The LLM-based function is no longer called by default, but kept for reference if needed
# You would need to re-import call_gemini if you decide to re-enable it.
"""
async def recommend_links_with_llm(skills: list[str]) -> list[dict]:
    from llm import call_gemini # Re-import here if truly needed for this specific function

    prompt = f\"\"\"
You are an AI assistant specialized in providing online learning resource recommendations.
For each skill in the provided list, suggest 1 to 3 highly relevant online learning resources.
Prioritize popular platforms like Udemy, Coursera, and YouTube.

For each resource, you MUST provide:
- The `name` of the skill (capitalized for display).
- The `platform` name (e.g., "Udemy", "Coursera", "YouTube").
- The `link` to the search results page on that platform for the specific skill.

Use the following URL formats strictly:
- Udemy: `https://www.udemy.com/courses/search/?q=YOUR_SKILL_HERE`
- Coursera: `https://www.coursera.org/search?query=YOUR_SKILL_HERE`
- YouTube: `https://www.youtube.com/results?search_query=YOUR_SKILL_HERE`

Replace 'YOUR_SKILL_HERE' with the URL-encoded skill name (replace spaces with '+').

Return ONLY a JSON list of objects. Each object must have 'name', 'platform', and 'link' keys.
Example for two skills:
[
  {{ "name": "Project Management", "platform": "Udemy", "link": "https://www.udemy.com/courses/search/?q=project+management" }},
  {{ "name": "Project Management", "platform": "Coursera", "link": "https://www.coursera.org/search?query=project%20management" }},
  {{ "name": "Data Analysis", "platform": "Udemy", "link": "https://www.udemy.com/courses/search/?q=data+analysis" }},
  {{ "name": "Data Analysis", "platform": "YouTube", "link": "https://www.youtube.com/results?search_query=data+analysis" }}
]

Skills to recommend resources for:
{json.dumps(skills)}
\"\"\"
    try:
        result_text = await call_gemini(prompt)
        llm_recommendations = json.loads(result_text)

        if isinstance(llm_recommendations, list) and \
           all(isinstance(item, dict) and "name" in item and "platform" in item and "link" in item for item in llm_recommendations):
            # This LLM function currently returns a flat list.
            # If we want it to return a grouped list like recommend_learning_links,
            # its prompt and parsing would need significant adjustment.
            # For now, if we use LLM, it implies the recommendations.html
            # should revert to expecting a flat list for LLM output,
            # or we convert this flat list to the grouped format here.
            # Given the current request, this function is effectively disabled.
            print("LLM recommendations function called but its output structure might not match the new HTML expectation.")
            return llm_recommendations
        else:
            print(f"⚠️ LLM returned unexpected JSON structure for recommendations: {result_text}")
            return recommend_learning_links(skills)
    except (json.JSONDecodeError, ConnectionError, ValueError) as e:
        print(f"⚠️ Error generating LLM recommendations: {e}. Falling back to static links.")
        return recommend_learning_links(skills)
    except Exception as e:
        print(f"⚠️ An unexpected error occurred in recommend_links_with_llm: {e}. Falling back.")
        return recommend_learning_links(skills)
"""

# ---------------------------\
# Exported Function
# ---------------------------\

async def get_skill_recommendations(): # Removed use_llm parameter, now always manual
    """
    Main function to get skill recommendations.
    Now always uses static/manual link generation.
    """
    skills_to_recommend = get_top_missing_skills()
    # Always use manual/static links as per user request
    return recommend_learning_links(skills_to_recommend)