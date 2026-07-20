from django.shortcuts import render


# Create your views here.
def login_view(request):
	return render(request, 'accounts/login.html')


def register_view(request):
	return render(request, 'accounts/register.html')


def profile_view(request):
	# Hard-coded sample context, shaped to match accounts.models.Profile,
	# until real auth and profile data are wired up.
	sample_user = {
		'full_name': 'Jane Doe',
		'email': 'jane@example.com',
		'skills': ['Python', 'SQL', 'Django'],
		'experience_level': 'mid',
		'preferred_location': 'Kampala',
		'preferred_job_type': 'remote',
	}
	return render(request, 'accounts/profile.html', {'user_data': sample_user})