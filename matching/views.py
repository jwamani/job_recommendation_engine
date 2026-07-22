from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_recommendations_for_user


@login_required
def recommendations(request):
    recommendations = get_recommendations_for_user(request.user)
    return render(request, 'matching/recommendations.html', {'recommendations': recommendations})
