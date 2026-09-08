import sqlite3
import json
from llm import infer_yellow_skills_from_resume
from storage import get_all_jobs, get_latest_resume_for_matching


async def match_jobs_to_resume():
    """
    Matches the latest resume against all stored jobs.
    Performs a two-phase matching:
    1. Initial strict matching (Green/Red skills) based on normalized skills from both sides.
    2. Post-matching LLM inference for Yellow skills (from the resume's raw text)
       for the initially identified missing (red) skills.
    Returns a list of top 5 matched jobs, with all skill lists lowercased for display.
    """
    resume_data = get_latest_resume_for_matching()
    if not resume_data:
        return [] # No resume found

    # These are already sets of lowercase strings from storage.py
    resume_normalized_skills_explicit = resume_data["normalized_skills"]
    resume_raw_text = resume_data["raw_text"]
    resume_field = resume_data["job_field"]

    all_jobs = get_all_jobs() # required_skills and normalized_skills are lists of lowercase strings here
    matched_jobs = []

    for job in all_jobs:
        job_title = job.get("title", "Unknown Job")
        job_gig = job.get("gig", "No gig description available.")
        # Ensure job skills are a set for efficient operations
        job_normalized_skills_set = set(job.get("normalized_skills", []))
        job_field = job.get("job_field", None)

        # Skip job if its field doesn't match resume's field, unless resume_field is None
        if resume_field and job_field and resume_field != job_field:
            continue

        # Green Skills: Skills explicitly present in both job requirements and resume
        green_skills = resume_normalized_skills_explicit.intersection(job_normalized_skills_set)

        # Initial Red Skills: Skills required by job but NOT explicitly in resume
        initial_red_skills = job_normalized_skills_set.difference(resume_normalized_skills_explicit)

        # Yellow Skills: Skills initially red but inferred from resume's raw text by LLM
        yellow_skills = set()

        # START - Commented out Yellow Skills Logic
        
        if initial_red_skills: # Only infer if there are actually missing skills
            # Use the LLM to infer if any of the initial_red_skills can be covered by the resume's raw text
            inferred_from_llm = await infer_yellow_skills_from_resume(
                resume_raw_text, list(initial_red_skills) # Pass list for LLM prompt
            )
            yellow_skills.update(set(inferred_from_llm).intersection(initial_red_skills))
        # END - Commented out Yellow Skills Logic

        # Final Red Skills: Skills that remain red even after LLM inference.
        # Since yellow skills are commented out, final_red_skills are simply initial_red_skills
        final_red_skills = initial_red_skills.difference(yellow_skills)

        # Calculate Match Percentage: (Green Skills) / Total REQUIRED Skills from Job (normalized)
        # As per user's request, yellow skills are not included in this calculation for now.
        total_required_for_calc = len(job_normalized_skills_set)
        if total_required_for_calc == 0:
            match_percentage = 0
        else:
            # Corrected formula: (matched skills / total required skills) * 100
            match_percentage = round(((len(green_skills) + len(yellow_skills)) / total_required_for_calc) * 100)


        matched_jobs.append({
            "title": job_title,
            "gig": job_gig,
            "percentage": match_percentage,
            "green": ", ".join(sorted(list(green_skills))),
            "yellow": ", ".join(sorted(list(yellow_skills))), # Yellow skills are now included
            "red": ", ".join(sorted(list(final_red_skills)))
        })

    # Sort matches by percentage in descending order and take top 5
    matched_jobs.sort(key=lambda x: x["percentage"], reverse=True)
    return matched_jobs[:5]