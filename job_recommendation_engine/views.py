from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home_view(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


def custom_404(request: HttpRequest, exception):
    return render(request, '404.html', status=404)


def custom_500(request: HttpRequest):
    return render(request, '500.html', status=500)
