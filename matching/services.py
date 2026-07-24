import re
from collections import defaultdict

from accounts.models import Profile, Skill
from interactions.models import Interaction
from interactions.services import get_latest_save_dismiss_states
from jobs.models import JobPosting

INTERACTION_WEIGHTS = {
    "apply": 5,
    "save": 3,
    "view": 1,
    "dismiss": -3,
}


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


def _category_interaction_points(user):
    """
    Points per job category from the user's own interaction history,
    weighted per SDD §5 (apply/save/view positive, dismiss negative).
    """
    points = defaultdict(int)
    rows = Interaction.objects.filter(user=user).values_list("job__category_id", "action")
    for category_id, action in rows:
        points[category_id] += INTERACTION_WEIGHTS.get(action, 0)
    return points


def get_recommendations_for_user(user, limit=20):
    """
    Rank active job postings for a user: the profile-based match score from
    recommend_job_score(), nudged by a bounded bonus from the user's past
    interactions with jobs in the same category. Jobs the user has dismissed
    (and not re-saved since) are excluded outright.
    """
    profile = getattr(user, "profile", None)
    if profile is None:
        return []

    dismissed_job_ids = {
        job_id
        for job_id, action in get_latest_save_dismiss_states(user).items()
        if action == "dismiss"
    }
    category_points = _category_interaction_points(user)

    jobs = (
        JobPosting.objects.filter(is_active=True)
        .exclude(id__in=dismissed_job_ids)
        .select_related("category")
        .prefetch_related("required_skills")
    )

    scored = []
    for job in jobs:
        bonus = max(-0.3, min(0.3, category_points.get(job.category_id, 0) / 50))
        total = max(0.0, min(1.0, recommend_job_score(profile, job) + bonus))
        scored.append({"job": job, "score": round(total * 100)})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]


def extract_text_from_cv(uploaded_file) -> str:
    """
    Pull raw text out of an uploaded CV file (.pdf or .txt).
    """
    if uploaded_file.name.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    return uploaded_file.read().decode("utf-8", errors="ignore")


def extract_skills_from_text(text: str):
    """
    Match known Skill names that appear as whole words in the given text.
    """
    text_lower = text.lower()
    return [
        skill
        for skill in Skill.objects.all()
        if re.search(r"\b" + re.escape(skill.name.lower()) + r"\b", text_lower)
    ]


def recommend_job_score_from_skills(cv_skills, job_posting: JobPosting) -> float:
    """
    Mirrors the skill-match component of recommend_job_score(), but scored
    against skills extracted from a CV instead of a stored profile — a CV's
    raw text carries no reliable signal for experience level, location, or
    salary preference, so those components of recommend_job_score() are left
    out here rather than guessed at.

    Returns:
        float: A score between 0 and 1, where 1 indicates every required
        skill for the job was found in the CV.
    """
    job_skills = set(job_posting.required_skills.all())
    if not job_skills:
        return 0.0
    return len(set(cv_skills) & job_skills) / len(job_skills)


def get_matches_for_cv_text(text: str, limit=2):
    """
    Rank active job postings against skills extracted from CV text, the same
    way get_recommendations_for_user() ranks jobs against a stored profile.
    """
    cv_skills = set(extract_skills_from_text(text))

    jobs = (
        JobPosting.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("required_skills")
    )

    scored = []
    for job in jobs:
        score = recommend_job_score_from_skills(cv_skills, job)
        if score <= 0:
            continue
        matched_skills = cv_skills & set(job.required_skills.all())
        scored.append({
            "job": job,
            "score": round(score * 100),
            "matched_skills": sorted(skill.name for skill in matched_skills),
        })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]