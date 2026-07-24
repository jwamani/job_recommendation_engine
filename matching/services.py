from collections import defaultdict
from dataclasses import dataclass

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

# Attribute weights for recommend_job_score, keyed by label. Must sum to 1.0.
SCORE_WEIGHTS = {
    "Skills match": 0.4,
    "Experience level": 0.2,
    "Location": 0.2,
    "Salary": 0.1,
    "Job type": 0.1,
}


@dataclass
class ScoreComponent:
    """One attribute's contribution to a job's match percentage."""

    label: str
    points: float
    # Best-case points this attribute could contribute (out of 100), or None
    # for adjustments (e.g. activity bonus) that aren't rendered as a bar.
    max_points: float | None = None


@dataclass
class ScoreBreakdown:
    """Result of recommend_job_score: the combined 0-1 total plus the
    per-attribute contributions (in percentage points) that produced it."""

    total: float
    components: list[ScoreComponent]


def recommend_job_score(profile: Profile, job_posting: JobPosting) -> ScoreBreakdown:
    """
    Calculate a recommendation score for a job posting based on the user's profile.

    The score is calculated based on the following criteria:
    - Skill Match: The number of matching skills between the user's profile and the job posting.
    - Experience Level Match: A score based on how well the user's experience level matches the job's required experience level.
    - Location Preference: A score based on whether the user's preferred location matches the job's location.
    - Salary Preference: A score based on whether the user's preferred salary range matches the job's salary range.
    - Job Type Preference: A score based on whether the user's preferred job type matches the job's type.

    Returns:
        ScoreBreakdown: the combined score (0-1, where 1 is a perfect match)
        alongside a ScoreComponent per attribute showing how many of the
        final 0-100 points it contributed.
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

    raw_matches = {
        "Skills match": skill_match_score,
        "Experience level": experience_level_score,
        "Location": location_score,
        "Salary": salary_score,
        "Job type": job_type_score,
    }

    components = [
        ScoreComponent(
            label=label,
            points=raw_matches[label] * weight * 100,
            max_points=weight * 100,
        )
        for label, weight in SCORE_WEIGHTS.items()
    ]

    # Weighted average of all scores
    total_score = sum(raw_matches[label] * weight for label, weight in SCORE_WEIGHTS.items())

    return ScoreBreakdown(total=total_score, components=components)


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
        breakdown = recommend_job_score(profile, job)
        bonus = max(-0.3, min(0.3, category_points.get(job.category_id, 0) / 50))
        uncapped_total = breakdown.total + bonus
        total = max(0.0, min(1.0, uncapped_total))

        components = list(breakdown.components)
        if bonus:
            components.append(ScoreComponent(label="Your activity in this category", points=bonus * 100))

        # Surface how much the 0-100% clamp took off (or added back), so the
        # displayed line items always sum to the displayed score.
        clamp_adjustment = (total - uncapped_total) * 100
        if round(clamp_adjustment):
            components.append(ScoreComponent(label="Adjustment (capped at 0-100%)", points=clamp_adjustment))

        scored.append({"job": job, "score": round(total * 100), "breakdown": components})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]