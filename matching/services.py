from collections import defaultdict

from accounts.models import Profile
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