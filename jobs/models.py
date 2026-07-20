from django.db import models
from accounts.models import Skill

class Category(models.Model):
    """Job category (e.g. Engineering, Design, Marketing)."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class JobPosting(models.Model):
    """A single job opening with its requirements and metadata."""

    EXPERIENCE_LEVELS = [
        ("entry", "Entry Level"),
        ("mid", "Mid Level"),
        ("senior", "Senior Level"),
    ]

    JOB_TYPE_CHOICES = [
        ("full-time", "Full-time"),
        ("part-time", "Part-time"),
        ("contract", "Contract"),
        ("remote", "Remote"),
    ]

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    required_skills = models.ManyToManyField(
        Skill,
        related_name="jobs",
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS,
    )
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
    )
    location = models.CharField(
        max_length=100,
        db_index=True,
    )
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-posted_at"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["experience_level", "is_active"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"
