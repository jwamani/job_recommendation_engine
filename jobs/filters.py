import django_filters

from .models import JobPosting


class JobPostingFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    salary_min = django_filters.NumberFilter(field_name="salary_min", lookup_expr="gte")

    class Meta:
        model = JobPosting
        fields = ["category", "experience_level", "job_type", "location", "salary_min"]