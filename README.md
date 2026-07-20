# Job Recommendation Engine

- A Django-based job recommendation engine that provides personalized job recommendations to users based on their skills, preferences and past applications. The engine also tracks clicks or applications to improve the suggestions of job openings.

## Steps to set up the project

1. `git clone https://github.com/jwamani/job-recommendation-engine.git`
2. `cd job-recommendation-engine`
3. `python -m venv .venv`
4. `source .venv/Scripts/activate`  # On Windows use `.venv\Scripts\activate`
5. if no uv is installed, use `pip install -r requirements.txt` or else `uv sync`
6. `python manage.py migrate`
