from django.db import models
from django.contrib.auth.models import User
from jobs.models import JobPosting

class Interaction(models.Model):
    """
    Log of every user action that should influence future recommendations.
    This single table doubles as the implicit-preference store;
    preferences are derived at scoring time by weighting rows here.
    """

    ACTION_CHOICES = [
        ("view", "View"),
        ("click", "Click"),
        ("save", "Save"),
        ("apply", "Apply"),
        ("dismiss", "Dismiss"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["job", "action"]),
        ]

    def __str__(self):
        return f"{self.user.username} {self.action} '{self.job}'"
