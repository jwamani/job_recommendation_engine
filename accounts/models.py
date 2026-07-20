from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    EXPERIENCE_LEVELS = [
        ("entry", "Entry Level"),
        ("mid", "Mid Level"),
        ("senior", "Senior Level"),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    skills = models.ManyToManyField(Skill, related_name="profiles", blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS)
    preferred_location = models.CharField(max_length=100, blank=True)
    preferred_salary_min = models.IntegerField(null=True, blank=True)
    preferred_categories = models.ManyToManyField("jobs.Category", related_name="interested_profiles", blank=True)
    
    def __str__(self):
        return self.user.username