"""
Management command: seed_data

Populates the Job Recommendation Engine with realistic demo data:
  - ~28 Skills
  - 9 Categories
  - 16 users + Profiles (varied experience levels, locations, prefs)
  - 40 JobPostings (varied categories, skills, salary, location, type)
  - A batch of Interaction rows so the feedback loop / recompute_scores
    command has something real to chew on during a demo.

WHERE THIS GOES
    Built against the schema documented in the SDD (accounts / jobs /
    interactions / matching apps). Drop this file at:
        accounts/management/commands/seed_data.py
    (create the two empty __init__.py files in
     accounts/management/ and accounts/management/commands/ if they
     don't exist yet). Adjust the import paths below if Person 1's
     actual app/model names differ from the SDD.

USAGE
    python manage.py seed_data            # create data (safe to re-run)
    python manage.py seed_data --flush    # wipe seeded data first, then recreate

WHY get_or_create() EVERYWHERE
    Re-running the command shouldn't duplicate rows. This makes it safe
    to run after every migration during development.
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# --- Adjust these imports if your actual app layout differs ---------------
from accounts.models import Profile, Skill
from jobs.models import Category, JobPosting
from interactions.models import Interaction

User = get_user_model()

EXPERIENCE_LEVELS = ["entry", "mid", "senior"]
JOB_TYPES = ["full-time", "part-time", "contract", "remote"]

SKILLS = [
    "Python", "Django", "JavaScript", "React", "SQL", "PostgreSQL",
    "HTML", "CSS", "Git", "Docker", "AWS", "REST APIs",
    "Machine Learning", "Data Analysis", "Excel", "Node.js", "Java",
    "C++", "Linux", "Kubernetes", "Figma", "Photoshop", "Sales",
    "Customer Service", "Accounting", "Marketing", "Project Management",
    "Communication",
]

CATEGORIES = [
    "Software Engineering", "Data & Analytics", "Design",
    "Marketing", "Sales", "Customer Support",
    "Finance & Accounting", "Product Management", "DevOps & Infrastructure",
]

LOCATIONS = [
    "Kampala", "Nairobi", "Lagos", "Remote", "London",
    "New York", "Berlin", "Cape Town",
]

# ---------------------------------------------------------------------------
# 16 user profiles. Deliberately overlapping skills/locations/categories
# with the job postings below so match-scoring has real signal to work with.
# ---------------------------------------------------------------------------
USERS = [
    dict(username="amina_k", first="Amina", last="Kato", email="amina.kato@example.com",
         experience_level="entry", preferred_location="Kampala",
         preferred_salary_min=2_400_000, preferred_job_type="full-time",
         skills=["Python", "Django", "SQL", "Git"],
         categories=["Software Engineering"]),
    dict(username="brian_o", first="Brian", last="Okello", email="brian.okello@example.com",
         experience_level="mid", preferred_location="Nairobi",
         preferred_salary_min=4_500_000, preferred_job_type="full-time",
         skills=["JavaScript", "React", "HTML", "CSS", "Node.js"],
         categories=["Software Engineering", "Design"]),
    dict(username="carol_n", first="Carol", last="Nabirye", email="carol.nabirye@example.com",
         experience_level="senior", preferred_location="Remote",
         preferred_salary_min=9_000_000, preferred_job_type="remote",
         skills=["Python", "Machine Learning", "Data Analysis", "SQL"],
         categories=["Data & Analytics"]),
    dict(username="david_m", first="David", last="Mwangi", email="david.mwangi@example.com",
         experience_level="entry", preferred_location="Nairobi",
         preferred_salary_min=2_100_000, preferred_job_type="full-time",
         skills=["Excel", "Accounting", "Communication"],
         categories=["Finance & Accounting"]),
    dict(username="esther_a", first="Esther", last="Auma", email="esther.auma@example.com",
         experience_level="mid", preferred_location="Kampala",
         preferred_salary_min=3_600_000, preferred_job_type="full-time",
         skills=["Figma", "Photoshop", "Communication"],
         categories=["Design"]),
    dict(username="felix_t", first="Felix", last="Tumusiime", email="felix.tumusiime@example.com",
         experience_level="senior", preferred_location="Remote",
         preferred_salary_min=10_500_000, preferred_job_type="remote",
         skills=["AWS", "Docker", "Kubernetes", "Linux", "Python"],
         categories=["DevOps & Infrastructure"]),
    dict(username="grace_w", first="Grace", last="Wanjiru", email="grace.wanjiru@example.com",
         experience_level="entry", preferred_location="Lagos",
         preferred_salary_min=1_800_000, preferred_job_type="part-time",
         skills=["Sales", "Communication", "Customer Service"],
         categories=["Sales"]),
    dict(username="henry_s", first="Henry", last="Ssekandi", email="henry.ssekandi@example.com",
         experience_level="mid", preferred_location="Kampala",
         preferred_salary_min=4_200_000, preferred_job_type="full-time",
         skills=["Java", "SQL", "Git", "Project Management"],
         categories=["Software Engineering", "Product Management"]),
    dict(username="irene_b", first="Irene", last="Birungi", email="irene.birungi@example.com",
         experience_level="senior", preferred_location="Berlin",
         preferred_salary_min=12_000_000, preferred_job_type="full-time",
         skills=["Project Management", "Data Analysis", "Communication"],
         categories=["Product Management"]),
    dict(username="james_k", first="James", last="Kironde", email="james.kironde@example.com",
         experience_level="entry", preferred_location="Cape Town",
         preferred_salary_min=1_950_000, preferred_job_type="contract",
         skills=["Customer Service", "Communication", "Excel"],
         categories=["Customer Support"]),
    dict(username="lydia_n", first="Lydia", last="Nakato", email="lydia.nakato@example.com",
         experience_level="mid", preferred_location="Remote",
         preferred_salary_min=5_400_000, preferred_job_type="remote",
         skills=["Python", "Django", "REST APIs", "PostgreSQL"],
         categories=["Software Engineering"]),
    dict(username="michael_o", first="Michael", last="Otieno", email="michael.otieno@example.com",
         experience_level="senior", preferred_location="Nairobi",
         preferred_salary_min=9_600_000, preferred_job_type="full-time",
         skills=["Marketing", "Communication", "Data Analysis"],
         categories=["Marketing"]),
    dict(username="nancy_a", first="Nancy", last="Achieng", email="nancy.achieng@example.com",
         experience_level="entry", preferred_location="Kampala",
         preferred_salary_min=2_250_000, preferred_job_type="full-time",
         skills=["HTML", "CSS", "JavaScript"],
         categories=["Software Engineering", "Design"]),
    dict(username="oscar_l", first="Oscar", last="Lubega", email="oscar.lubega@example.com",
         experience_level="mid", preferred_location="London",
         preferred_salary_min=7_500_000, preferred_job_type="full-time",
         skills=["Accounting", "Excel", "Communication"],
         categories=["Finance & Accounting"]),
    dict(username="patricia_m", first="Patricia", last="Mbabazi", email="patricia.mbabazi@example.com",
         experience_level="senior", preferred_location="Remote",
         preferred_salary_min=11_400_000, preferred_job_type="remote",
         skills=["AWS", "Python", "Docker", "Linux"],
         categories=["DevOps & Infrastructure", "Software Engineering"]),
    dict(username="ronald_k", first="Ronald", last="Kavuma", email="ronald.kavuma@example.com",
         experience_level="entry", preferred_location="Kampala",
         preferred_salary_min=2_100_000, preferred_job_type="full-time",
         skills=["Sales", "Marketing", "Communication"],
         categories=["Sales", "Marketing"]),
]

# ---------------------------------------------------------------------------
# 40 job postings. Salaries are UGX gross monthly (nothing below 1,000,000).
# ---------------------------------------------------------------------------
JOBS = [
    dict(title="Junior Django Developer", company="Kampala Softworks",
         category="Software Engineering", experience_level="entry",
         job_type="full-time", location="Kampala",
         salary_min=2_100_000, salary_max=3_000_000,
         skills=["Python", "Django", "SQL", "Git"],
         description="Build and maintain internal Django apps alongside a small backend team."),
    dict(title="Frontend Engineer (React)", company="Nairobi Digital",
         category="Software Engineering", experience_level="mid",
         job_type="full-time", location="Nairobi",
         salary_min=3_900_000, salary_max=5_700_000,
         skills=["JavaScript", "React", "HTML", "CSS"],
         description="Own the customer-facing dashboard, working closely with design and product."),
    dict(title="Senior Data Scientist", company="Insight Analytics",
         category="Data & Analytics", experience_level="senior",
         job_type="remote", location="Remote",
         salary_min=9_600_000, salary_max=13_500_000,
         skills=["Python", "Machine Learning", "Data Analysis", "SQL"],
         description="Lead predictive modelling projects for enterprise clients."),
    dict(title="Accounts Assistant", company="Mwangi & Partners",
         category="Finance & Accounting", experience_level="entry",
         job_type="full-time", location="Nairobi",
         salary_min=1_800_000, salary_max=2_550_000,
         skills=["Excel", "Accounting", "Communication"],
         description="Support the finance team with reconciliations and reporting."),
    dict(title="UI/UX Designer", company="Studio Kampala",
         category="Design", experience_level="mid",
         job_type="full-time", location="Kampala",
         salary_min=3_300_000, salary_max=4_800_000,
         skills=["Figma", "Photoshop", "Communication"],
         description="Design user flows and interfaces for a fintech mobile app."),
    dict(title="Cloud/DevOps Engineer", company="Scale Infra",
         category="DevOps & Infrastructure", experience_level="senior",
         job_type="remote", location="Remote",
         salary_min=10_200_000, salary_max=14_400_000,
         skills=["AWS", "Docker", "Kubernetes", "Linux"],
         description="Own CI/CD pipelines and cloud infrastructure across three environments."),
    dict(title="Retail Sales Associate", company="Lagos Retail Group",
         category="Sales", experience_level="entry",
         job_type="part-time", location="Lagos",
         salary_min=1_500_000, salary_max=2_100_000,
         skills=["Sales", "Communication", "Customer Service"],
         description="Front-of-store sales and customer support in a busy retail outlet."),
    dict(title="Backend Engineer (Java)", company="Ssese Systems",
         category="Software Engineering", experience_level="mid",
         job_type="full-time", location="Kampala",
         salary_min=3_900_000, salary_max=5_400_000,
         skills=["Java", "SQL", "Git"],
         description="Build backend services for a logistics platform."),
    dict(title="Product Manager", company="Berlin Product Co",
         category="Product Management", experience_level="senior",
         job_type="full-time", location="Berlin",
         salary_min=11_400_000, salary_max=15_600_000,
         skills=["Project Management", "Data Analysis", "Communication"],
         description="Own the roadmap for a B2B SaaS product used across Europe."),
    dict(title="Customer Support Representative", company="Cape Town Care",
         category="Customer Support", experience_level="entry",
         job_type="contract", location="Cape Town",
         salary_min=1_650_000, salary_max=2_250_000,
         skills=["Customer Service", "Communication"],
         description="Handle first-line customer queries via chat and email."),
    dict(title="Django Backend Engineer (Remote)", company="Distal Labs",
         category="Software Engineering", experience_level="mid",
         job_type="remote", location="Remote",
         salary_min=5_100_000, salary_max=6_900_000,
         skills=["Python", "Django", "REST APIs", "PostgreSQL"],
         description="Fully remote team building an API-first Django platform."),
    dict(title="Marketing Analyst", company="Nairobi Growth Co",
         category="Marketing", experience_level="senior",
         job_type="full-time", location="Nairobi",
         salary_min=8_700_000, salary_max=10_800_000,
         skills=["Marketing", "Communication", "Data Analysis"],
         description="Analyse campaign performance and advise on budget allocation."),
    dict(title="Junior Frontend Developer", company="Kampala Softworks",
         category="Software Engineering", experience_level="entry",
         job_type="full-time", location="Kampala",
         salary_min=1_950_000, salary_max=2_850_000,
         skills=["HTML", "CSS", "JavaScript"],
         description="Work on internal tools' frontend, mentored by senior engineers."),
    dict(title="Finance Officer", company="London Capital Partners",
         category="Finance & Accounting", experience_level="mid",
         job_type="full-time", location="London",
         salary_min=6_900_000, salary_max=8_700_000,
         skills=["Accounting", "Excel", "Communication"],
         description="Manage monthly close and financial reporting for a mid-size fund."),
    dict(title="Site Reliability Engineer", company="Uptime Collective",
         category="DevOps & Infrastructure", experience_level="senior",
         job_type="remote", location="Remote",
         salary_min=10_800_000, salary_max=14_100_000,
         skills=["AWS", "Python", "Docker", "Linux"],
         description="Keep production systems reliable across a distributed team."),
    dict(title="Sales & Marketing Coordinator", company="Kampala Growth Hub",
         category="Sales", experience_level="entry",
         job_type="full-time", location="Kampala",
         salary_min=1_950_000, salary_max=2_700_000,
         skills=["Sales", "Marketing", "Communication"],
         description="Support outbound sales campaigns and coordinate marketing events."),
    dict(title="Data Analyst", company="Insight Analytics",
         category="Data & Analytics", experience_level="mid",
         job_type="full-time", location="Remote",
         salary_min=4_800_000, salary_max=6_600_000,
         skills=["SQL", "Data Analysis", "Excel"],
         description="Build dashboards and reports for internal stakeholders."),
    dict(title="Product Designer", company="Studio Kampala",
         category="Design", experience_level="entry",
         job_type="full-time", location="Kampala",
         salary_min=2_100_000, salary_max=3_000_000,
         skills=["Figma", "Communication"],
         description="Support senior designers on wireframes and prototypes."),
    dict(title="DevOps Intern", company="Scale Infra",
         category="DevOps & Infrastructure", experience_level="entry",
         job_type="contract", location="Remote",
         salary_min=1_200_000, salary_max=1_800_000,
         skills=["Linux", "Docker", "Git"],
         description="3-month internship supporting the platform team's tooling."),
    dict(title="Senior Django Engineer", company="Distal Labs",
         category="Software Engineering", experience_level="senior",
         job_type="remote", location="Remote",
         salary_min=9_000_000, salary_max=12_600_000,
         skills=["Python", "Django", "PostgreSQL", "AWS"],
         description="Lead backend architecture decisions for a growing Django platform."),
    dict(title="QA Engineer", company="Nakato Tech",
         category="Software Engineering", experience_level="entry",
         job_type="full-time", location="Kampala",
         salary_min=1_300_000, salary_max=1_900_000,
         skills=["Python", "Git", "SQL"],
         description="Write and maintain automated test suites for a growing product team."),
    dict(title="Mobile App Developer (Android)", company="Kampala Softworks",
         category="Software Engineering", experience_level="mid",
         job_type="full-time", location="Kampala",
         salary_min=3_600_000, salary_max=5_200_000,
         skills=["Java", "Git", "REST APIs"],
         description="Build and ship features for a consumer Android app used across East Africa."),
    dict(title="DevOps Engineer", company="CloudNest Africa",
         category="DevOps & Infrastructure", experience_level="mid",
         job_type="remote", location="Remote",
         salary_min=5_500_000, salary_max=7_500_000,
         skills=["AWS", "Docker", "Linux", "Git"],
         description="Automate deployments and manage cloud infrastructure for client platforms."),
    dict(title="Platform Reliability Engineer", company="Uptime Collective",
         category="DevOps & Infrastructure", experience_level="senior",
         job_type="remote", location="Remote",
         salary_min=9_500_000, salary_max=13_000_000,
         skills=["AWS", "Kubernetes", "Linux", "Python"],
         description="Own uptime and incident response for a fleet of production clusters."),
    dict(title="BI Analyst", company="Kampala Insights",
         category="Data & Analytics", experience_level="mid",
         job_type="full-time", location="Kampala",
         salary_min=3_000_000, salary_max=4_200_000,
         skills=["SQL", "Data Analysis", "Excel"],
         description="Build reporting dashboards that inform weekly leadership decisions."),
    dict(title="Junior Data Analyst", company="Insight Analytics",
         category="Data & Analytics", experience_level="entry",
         job_type="full-time", location="Nairobi",
         salary_min=1_500_000, salary_max=2_100_000,
         skills=["Excel", "Data Analysis", "SQL"],
         description="Support senior analysts with data cleaning and ad-hoc reporting."),
    dict(title="Machine Learning Engineer", company="Insight Analytics",
         category="Data & Analytics", experience_level="senior",
         job_type="remote", location="Remote",
         salary_min=10_000_000, salary_max=14_000_000,
         skills=["Python", "Machine Learning", "Data Analysis"],
         description="Design and deploy ML models for client-facing recommendation products."),
    dict(title="Graphic Designer", company="Creative Hub Kampala",
         category="Design", experience_level="entry",
         job_type="part-time", location="Kampala",
         salary_min=1_000_000, salary_max=1_500_000,
         skills=["Photoshop", "Figma", "Communication"],
         description="Produce social and print assets for a roster of local brand clients."),
    dict(title="Senior Product Designer", company="Berlin Product Co",
         category="Design", experience_level="senior",
         job_type="full-time", location="Berlin",
         salary_min=8_000_000, salary_max=11_000_000,
         skills=["Figma", "Photoshop", "Communication"],
         description="Lead end-to-end design for a B2B SaaS product used across Europe."),
    dict(title="Digital Marketing Specialist", company="GrowthWorks Uganda",
         category="Marketing", experience_level="mid",
         job_type="full-time", location="Kampala",
         salary_min=2_800_000, salary_max=3_800_000,
         skills=["Marketing", "Communication", "Data Analysis"],
         description="Plan and run paid and organic campaigns across social channels."),
    dict(title="Social Media Manager", company="Lagos Retail Group",
         category="Marketing", experience_level="entry",
         job_type="full-time", location="Lagos",
         salary_min=1_400_000, salary_max=2_000_000,
         skills=["Marketing", "Communication"],
         description="Grow and manage brand presence across Instagram, TikTok, and X."),
    dict(title="Head of Marketing", company="Nairobi Growth Co",
         category="Marketing", experience_level="senior",
         job_type="full-time", location="Nairobi",
         salary_min=9_000_000, salary_max=12_500_000,
         skills=["Marketing", "Data Analysis", "Communication"],
         description="Set marketing strategy and lead a small in-house team."),
    dict(title="Business Development Executive", company="Pearl Traders",
         category="Sales", experience_level="mid",
         job_type="full-time", location="Kampala",
         salary_min=2_500_000, salary_max=3_500_000,
         skills=["Sales", "Communication", "Marketing"],
         description="Identify and close new B2B accounts across the region."),
    dict(title="Sales Representative", company="Cape Town Care",
         category="Sales", experience_level="entry",
         job_type="full-time", location="Cape Town",
         salary_min=1_200_000, salary_max=1_800_000,
         skills=["Sales", "Communication", "Customer Service"],
         description="Handle inbound leads and walk-in customers for a growing retailer."),
    dict(title="Regional Sales Manager", company="Lagos Retail Group",
         category="Sales", experience_level="senior",
         job_type="full-time", location="Lagos",
         salary_min=8_500_000, salary_max=11_500_000,
         skills=["Sales", "Marketing", "Project Management"],
         description="Own sales targets and manage a team of reps across multiple outlets."),
    dict(title="Support Team Lead", company="HelpDesk Africa",
         category="Customer Support", experience_level="senior",
         job_type="full-time", location="Nairobi",
         salary_min=6_000_000, salary_max=8_000_000,
         skills=["Customer Service", "Communication", "Project Management"],
         description="Lead a support team and own escalation handling and SLAs."),
    dict(title="Customer Success Associate", company="HelpDesk Africa",
         category="Customer Support", experience_level="entry",
         job_type="contract", location="Remote",
         salary_min=1_100_000, salary_max=1_700_000,
         skills=["Customer Service", "Communication"],
         description="Respond to customer queries via chat and email for SaaS clients."),
    dict(title="Financial Analyst", company="Kampala Capital Partners",
         category="Finance & Accounting", experience_level="mid",
         job_type="full-time", location="Kampala",
         salary_min=4_000_000, salary_max=5_500_000,
         skills=["Accounting", "Excel", "Data Analysis"],
         description="Build financial models and support investment decision-making."),
    dict(title="Junior Accountant", company="Mwangi & Partners",
         category="Finance & Accounting", experience_level="entry",
         job_type="full-time", location="Nairobi",
         salary_min=1_600_000, salary_max=2_200_000,
         skills=["Accounting", "Excel", "Communication"],
         description="Assist with bookkeeping, invoicing, and monthly reconciliations."),
    dict(title="Head of Finance", company="London Capital Partners",
         category="Finance & Accounting", experience_level="senior",
         job_type="full-time", location="London",
         salary_min=10_000_000, salary_max=14_000_000,
         skills=["Accounting", "Data Analysis", "Project Management"],
         description="Own financial strategy, reporting, and audits for a mid-size fund."),
]

ACTIONS = ["view", "click", "save", "apply", "dismiss"]
ACTION_WEIGHTS = [0.40, 0.25, 0.15, 0.10, 0.10]  # view most common, apply/dismiss rarer


class Command(BaseCommand):
    help = "Seed the database with realistic demo users, profiles, jobs, and interactions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete previously seeded demo data before recreating it.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        with transaction.atomic():
            skills = self._create_skills()
            categories = self._create_categories()
            users = self._create_users(skills, categories)
            jobs = self._create_jobs(skills, categories)
            self._create_interactions(users, jobs)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(SKILLS)} skills, {len(CATEGORIES)} categories, "
            f"{len(USERS)} users/profiles, {len(JOBS)} job postings."
        ))

    # -- teardown ------------------------------------------------------
    def _flush(self):
        usernames = [u["username"] for u in USERS]
        Interaction.objects.filter(user__username__in=usernames).delete()
        JobPosting.objects.filter(company__in={j["company"] for j in JOBS}).delete()
        User.objects.filter(username__in=usernames).delete()
        self.stdout.write("Flushed previously seeded demo data.")

    # -- lookups ---------------------------------------------------------
    def _create_skills(self):
        return {name: Skill.objects.get_or_create(name=name)[0] for name in SKILLS}

    def _create_categories(self):
        return {name: Category.objects.get_or_create(name=name)[0] for name in CATEGORIES}

    # -- users / profiles --------------------------------------------------
    def _create_users(self, skills, categories):
        created = []
        for u in USERS:
            user, _ = User.objects.get_or_create(
                username=u["username"],
                defaults=dict(
                    email=u["email"], first_name=u["first"], last_name=u["last"]
                ),
            )
            if not user.has_usable_password():
                user.set_password("demo1234")
                user.save()

            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults=dict(
                    experience_level=u["experience_level"],
                    preferred_location=u["preferred_location"],
                    preferred_salary_min=u["preferred_salary_min"],
                    preferred_job_type=u["preferred_job_type"],
                ),
            )
            profile.skills.set([skills[s] for s in u["skills"]])
            profile.preferred_categories.set([categories[c] for c in u["categories"]])
            created.append(user)
        return created

    # -- job postings --------------------------------------------------
    def _create_jobs(self, skills, categories):
        # posted_at is auto_now_add=True, so Django ignores any value we
        # pass in at creation time — it always gets set to "now" on save().
        # To stagger dates (so the listing page has real variety to sort
        # by), we create normally, then use a queryset .update(), which
        # goes straight to SQL and bypasses auto_now_add entirely.
        created = []
        now = timezone.now()
        for i, j in enumerate(JOBS):
            job, _ = JobPosting.objects.get_or_create(
                title=j["title"],
                company=j["company"],
                defaults=dict(
                    description=j["description"],
                    category=categories[j["category"]],
                    experience_level=j["experience_level"],
                    job_type=j["job_type"],
                    location=j["location"],
                    salary_min=j["salary_min"],
                    salary_max=j["salary_max"],
                    is_active=True,
                ),
            )
            job.required_skills.set([skills[s] for s in j["skills"]])
            created.append(job)

        # Stagger posted_at across the seeded jobs (bypasses auto_now_add).
        for i, job in enumerate(created):
            JobPosting.objects.filter(pk=job.pk).update(
                posted_at=now - timedelta(days=i)
            )
        return created

    # -- interactions ----------------------------------------------------
    def _create_interactions(self, users, jobs):
        """
        Deterministic pseudo-random interactions so the feedback loop /
        recompute_scores command has data to demonstrate, but re-running
        the seed script produces the same result each time (easier to
        reason about during QA).
        """
        # Interaction.timestamp is also auto_now_add=True, so — same as
        # posted_at above — any value passed at creation is ignored. We
        # create normally, then backdate via .update() afterward.
        rng = random.Random(42)
        now = timezone.now()

        for user in users:
            # Each user interacts with 4-8 jobs
            sample_jobs = rng.sample(jobs, k=rng.randint(4, 8))
            for job in sample_jobs:
                action = rng.choices(ACTIONS, weights=ACTION_WEIGHTS, k=1)[0]
                interaction, _ = Interaction.objects.get_or_create(
                    user=user, job=job, action=action,
                )
                Interaction.objects.filter(pk=interaction.pk).update(
                    timestamp=now - timedelta(days=rng.randint(0, 20))
                )
