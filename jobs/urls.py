from django.urls import path

from .views import JobDetailView, JobListView

app_name = "jobs"

urlpatterns = [
	path("", JobListView.as_view(), name="job_list"),
	path("jobs/<int:pk>/", JobDetailView.as_view(), name="job_detail"),
]