from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q
from django_filters.views import FilterView
from django.views.generic import DetailView

from interactions.models import Interaction
from matching.forms import CVUploadForm
from matching.services import extract_text_from_cv, get_matches_for_cv_text

from .filters import JobPostingFilter
from .models import JobPosting


class JobListView(FilterView):
	model = JobPosting
	filterset_class = JobPostingFilter
	template_name = "jobs/job_list.html"
	paginate_by = 6

	def get_queryset(self):
		queryset = (
			JobPosting.objects.select_related("category")
			.prefetch_related("required_skills")
			.filter(is_active=True)
		)
		query = self.request.GET.get("q", "").strip()
		if query:
			queryset = queryset.filter(
				Q(title__icontains=query)
				| Q(company__icontains=query)
				| Q(description__icontains=query)
				| Q(location__icontains=query)
			)
		return queryset

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		page_query = self.request.GET.copy()
		page_query.pop("page", None)
		context["query_string"] = page_query.urlencode()
		context["search_query"] = self.request.GET.get("q", "")
		context["cv_form"] = getattr(self, "cv_form", None) or CVUploadForm()
		context["cv_matches"] = getattr(self, "cv_matches", None)
		return context

	def post(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect_to_login(request.get_full_path())

		self.cv_form = CVUploadForm(request.POST, request.FILES)
		self.cv_matches = None
		if self.cv_form.is_valid():
			cv_text = extract_text_from_cv(self.cv_form.cleaned_data["cv_file"])
			self.cv_matches = get_matches_for_cv_text(cv_text, limit=2)
			if not self.cv_matches:
				messages.info(request, "We couldn't find a strong job match for your CV yet.")

		return self.get(request, *args, **kwargs)


class JobDetailView(DetailView):
	model = JobPosting
	template_name = "job_detail.html"

	def get_queryset(self):
		return JobPosting.objects.select_related("category").prefetch_related("required_skills")

	def get(self, request, *args, **kwargs):
		response = super().get(request, *args, **kwargs)
		if request.user.is_authenticated:
			Interaction.objects.create(user=request.user, job=self.object, action="view")
		return response
