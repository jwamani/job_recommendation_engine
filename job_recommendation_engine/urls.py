from django.contrib import admin
from django.urls import include, path
from .views import home_view

handler404 = 'job_recommendation_engine.views.custom_404'
handler500 = 'job_recommendation_engine.views.custom_500'

urlpatterns = [
    path("", home_view, name="home"),
    path("jobs/", include("jobs.urls")),
    path("accounts/", include("accounts.urls")),
    path("interactions/", include("interactions.urls")),
    path("matching/", include("matching.urls")),
    path("admin/", admin.site.urls),
]
