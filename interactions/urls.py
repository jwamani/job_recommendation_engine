from django.urls import path

from . import views

app_name = "interactions"

urlpatterns = [
    path("log/", views.log_interaction, name="log"),
    path("saved/", views.saved_jobs, name="saved_jobs"),
]