from accounts.models import Profile
from jobs.models import JobPosting


def recommend_job_score(profile: Profile, job_posting: JobPosting) -> float:
    """
    Calculate a recommendation score for a job posting based on the user's profile.

    The score is calculated based on the following criteria:
    - Skill Match: The number of matching skills between the user's profile and the job posting.
    - Experience Level Match: A score based on how well the user's experience level matches the job's required experience level.
    - Location Preference: A score based on whether the user's preferred location matches the job's location.
    - Salary Preference: A score based on whether the user's preferred salary range matches the job's salary range.
    - Job Type Preference: A score based on whether the user's preferred job type matches the job's type.

    Returns:
        float: A recommendation score between 0 and 1, where 1 indicates a perfect match.
    """
    # Skill Match
    user_skills = set(profile.skills.all())
    job_skills = set(job_posting.required_skills.all())
    skill_match_score = len(user_skills & job_skills) / max(len(job_skills), 1)

    # Experience Level Match
    experience_level_score = 1.0 if profile.experience_level == job_posting.experience_level else 0.0

    # Location Preference
    location_score = 1.0 if profile.preferred_location.lower() == job_posting.location.lower() else 0.0

    # Salary Preference
    salary_score = 0.0
    if profile.preferred_salary_min is not None and (job_posting.salary_min is not None and job_posting.salary_max is not None):
        if profile.preferred_salary_min <= job_posting.salary_max:
            salary_score = 1.0

    # Job Type Preference
    job_type_score = 1.0 if profile.preferred_job_type == job_posting.job_type else 0.0

    # Weighted average of all scores
    total_score = (
        skill_match_score * 0.4 +
        experience_level_score * 0.2 +
        location_score * 0.2 +
        salary_score * 0.1 +
        job_type_score * 0.1
    )

    return total_score