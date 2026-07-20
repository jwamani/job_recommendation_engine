from django.db import models
from django.contrib.auth.models import User


class RecommendationScore(models.Model):
    """
    Cached match score for a (user, job) pair.
    Recomputed periodically or on demand — never edited by hand —
    so the scoring algorithm can change later without touching the schema.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendation_scores")
    job = models.ForeignKey("jobs.JobPosting", on_delete=models.CASCADE, related_name="recommendation_scores")
    score = models.FloatField()
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "job"]
        ordering = ["-score"]

    def __str__(self):
        return f"{self.user.username} → {self.job.title}: {self.score:.2f}"
