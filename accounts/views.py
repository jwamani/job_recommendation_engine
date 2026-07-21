from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpRequest

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import Profile, Skill


def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get('next')
            return redirect(next_url or 'accounts:profile')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request: HttpRequest):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request: HttpRequest):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def profile_edit_view(request: HttpRequest):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.save()

            skill_names = [
                name.strip()
                for name in form.cleaned_data.get('skills', '').split(',')
                if name.strip()
            ]
            skills = [Skill.objects.get_or_create(name=name)[0] for name in skill_names]
            profile.skills.set(skills)

            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'profile': profile, 'form': form})


@login_required
def logout_view(request: HttpRequest):
    logout(request)
    return redirect('jobs:job_list')
