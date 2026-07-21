from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    path('recommendations/', views.recommendations, name='recommendations'),
]
