from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from jobs.models import JobPosting

from .models import Interaction
from .services import get_latest_save_dismiss_states


def _safe_next(request, fallback):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return fallback


def _record_interaction(user, job, action):
    """
    view always logs a new row. apply happens at most once ever.
    save/dismiss are a toggle - only log when the state actually changes.
    """
    if action == "view":
        Interaction.objects.create(user=user, job=job, action=action)
    elif action == "apply":
        already_applied = Interaction.objects.filter(
            user=user, job=job, action="apply"
        ).exists()
        if not already_applied:
            Interaction.objects.create(user=user, job=job, action=action)
    elif action in ("save", "dismiss"):
        latest = (
            Interaction.objects.filter(user=user, job=job, action__in=["save", "dismiss"])
            .values_list("action", flat=True)
            .first()
        )
        if latest != action:
            Interaction.objects.create(user=user, job=job, action=action)


@login_required
@require_POST
def log_interaction(request):
    job = get_object_or_404(JobPosting, pk=request.POST.get("job_id"))
    action = request.POST.get("action")

    valid_actions = dict(Interaction.ACTION_CHOICES)
    if action in valid_actions:
        _record_interaction(request.user, job, action)

    if action == "apply":
        return redirect(reverse("interactions:application_submitted", kwargs={"pk": job.pk}))

    fallback = reverse("jobs:job_detail", kwargs={"pk": job.pk})
    return redirect(_safe_next(request, fallback))


@login_required
def saved_jobs(request):
    save_dismiss_states = get_latest_save_dismiss_states(request.user)
    saved_job_ids = [job_id for job_id, action in save_dismiss_states.items() if action == "save"]
    applied_job_ids = Interaction.objects.filter(
        user=request.user, action="apply"
    ).values_list("job_id", flat=True)

    context = {
        "saved_jobs": JobPosting.objects.filter(id__in=saved_job_ids).select_related("category"),
        "applied_jobs": JobPosting.objects.filter(id__in=applied_job_ids).select_related("category"),
    }
    return render(request, "interactions/saved_jobs.html", context)


@login_required
def application_submitted(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    return render(request, "interactions/application_submitted.html", {"job": job})
