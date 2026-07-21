from django.db.models import Q
from django_filters.views import FilterView
from django.views.generic import DetailView

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
		return context


class JobDetailView(DetailView):
	model = JobPosting
	template_name = "jobs/job_detail.html"

	def get_queryset(self):
		return JobPosting.objects.select_related("category").prefetch_related("required_skills")
