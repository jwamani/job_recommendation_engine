from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from jobs.models import JobPosting

from .models import Interaction


def _safe_next(request, fallback):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return fallback


@login_required
@require_POST
def log_interaction(request):
    job = get_object_or_404(JobPosting, pk=request.POST.get("job_id"))
    action = request.POST.get("action")

    valid_actions = dict(Interaction.ACTION_CHOICES)
    if action in valid_actions:
        Interaction.objects.create(user=request.user, job=job, action=action)

    fallback = reverse("jobs:job_detail", kwargs={"pk": job.pk})
    return redirect(_safe_next(request, fallback))


@login_required
def saved_jobs(request):
    saved_job_ids = Interaction.objects.filter(
        user=request.user, action="save"
    ).values_list("job_id", flat=True)
    applied_job_ids = Interaction.objects.filter(
        user=request.user, action="apply"
    ).values_list("job_id", flat=True)

    context = {
        "saved_jobs": JobPosting.objects.filter(id__in=saved_job_ids).select_related("category"),
        "applied_jobs": JobPosting.objects.filter(id__in=applied_job_ids).select_related("category"),
    }
    return render(request, "interactions/saved_jobs.html", context)
