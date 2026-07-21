from django.db import migrations


def seed_job_postings(apps, schema_editor):
    Category = apps.get_model("jobs", "Category")
    JobPosting = apps.get_model("jobs", "JobPosting")
    Skill = apps.get_model("accounts", "Skill")

    categories = {}
    for name in ["Engineering", "Data", "Design", "Marketing"]:
        category, _ = Category.objects.get_or_create(name=name)
        categories[name] = category

    skills = {}
    for name in ["Python", "Django", "SQL", "JavaScript", "Communication", "Figma", "Analytics", "Git"]:
        skill, _ = Skill.objects.get_or_create(name=name)
        skills[name] = skill

    sample_jobs = [
        {
            "title": "Junior Django Developer",
            "company": "Northstar Labs",
            "description": "Build and maintain server-rendered Django features for a growing recruitment platform.",
            "category": categories["Engineering"],
            "skills": [skills["Python"], skills["Django"], skills["Git"]],
            "experience_level": "entry",
            "job_type": "full-time",
            "location": "Accra",
            "salary_min": 2500000,
            "salary_max": 4000000,
        },
        {
            "title": "Data Analyst",
            "company": "Insight Loop",
            "description": "Turn hiring and product usage data into clear dashboards and actionable reporting.",
            "category": categories["Data"],
            "skills": [skills["SQL"], skills["Analytics"], skills["Communication"]],
            "experience_level": "mid",
            "job_type": "full-time",
            "location": "Remote",
            "salary_min": 2200000,
            "salary_max": 5200000,
        },
        {
            "title": "Product Designer",
            "company": "Skyward Studio",
            "description": "Shape polished user flows and interface systems for internal tools and client products.",
            "category": categories["Design"],
            "skills": [skills["Figma"], skills["Communication"], skills["JavaScript"]],
            "experience_level": "mid",
            "job_type": "contract",
            "location": "Kumasi",
            "salary_min": 1700000,
            "salary_max": 3500000,
        },
        {
            "title": "Growth Marketing Associate",
            "company": "BrightSeed",
            "description": "Support campaigns, content, and analytics for a job platform focused on early-career talent.",
            "category": categories["Marketing"],
            "skills": [skills["Communication"], skills["Analytics"], skills["Git"]],
            "experience_level": "entry",
            "job_type": "part-time",
            "location": "Accra",
            "salary_min": 1800000,
            "salary_max": 2600000,
        },
        {
            "title": "Senior Backend Engineer",
            "company": "CloudHarbor",
            "description": "Lead architecture, review code, and mentor junior engineers across multiple Django services.",
            "category": categories["Engineering"],
            "skills": [skills["Python"], skills["Django"], skills["SQL"], skills["Git"]],
            "experience_level": "senior",
            "job_type": "remote",
            "location": "Remote",
            "salary_min": 6000000,
            "salary_max": 9000000,
        },
    ]

    for job_data in sample_jobs:
        skills_for_job = job_data.pop("skills")
        job, created = JobPosting.objects.get_or_create(
            title=job_data["title"],
            company=job_data["company"],
            defaults=job_data,
        )
        if created:
            job.required_skills.set(skills_for_job)


def unseed_job_postings(apps, schema_editor):
    JobPosting = apps.get_model("jobs", "JobPosting")
    Category = apps.get_model("jobs", "Category")
    Skill = apps.get_model("accounts", "Skill")

    JobPosting.objects.filter(title__in=[
        "Junior Django Developer",
        "Data Analyst",
        "Product Designer",
        "Growth Marketing Associate",
        "Senior Backend Engineer",
    ]).delete()

    Category.objects.filter(name__in=["Engineering", "Data", "Design", "Marketing"]).delete()
    Skill.objects.filter(name__in=["Python", "Django", "SQL", "JavaScript", "Communication", "Figma", "Analytics", "Git"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_initial"),
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_job_postings, unseed_job_postings),
    ]