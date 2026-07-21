import django_filters
from django import forms

from .models import JobPosting


class JobPostingFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(
        field_name="location",
        lookup_expr="icontains",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Kampala, Remote"}),
    )
    salary_min = django_filters.NumberFilter(
        field_name="salary_min",
        lookup_expr="gte",
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 500000"}),
    )

    class Meta:
        model = JobPosting
        fields = ["category", "experience_level", "job_type", "location", "salary_min"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()