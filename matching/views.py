from django.shortcuts import render


def recommendations(request):
    # Hard-coded sample context, shaped like matching.models.RecommendationScore
    # joined with jobs.models.JobPosting, until the real scoring algorithm (REQ-05)
    # and its view exist. `score` is treated here as a 0-100 match percentage for
    # display; how the real algorithm normalises its raw score is a backend concern.
    sample_recommendations = [
        {
            'job': {
                'id': 1,
                'title': 'Junior Backend Developer',
                'company': 'Acme Ltd',
                'location': 'Kampala',
                'job_type': 'full-time',
            },
            'score': 92,
        },
        {
            'job': {
                'id': 2,
                'title': 'Data Analyst Intern',
                'company': 'Beta Corp',
                'location': 'Remote',
                'job_type': 'remote',
            },
            'score': 78,
        },
        {
            'job': {
                'id': 3,
                'title': 'Software Engineer',
                'company': 'Gamma Inc',
                'location': 'Kampala',
                'job_type': 'contract',
            },
            'score': 65,
        },
    ]
    return render(request, 'matching/recommendations.html', {'recommendations': sample_recommendations})
