from django import template

register = template.Library()


@register.filter
def ugx(value):
    """Format a numeric salary with thousands separators, e.g. 1000000 -> "1,000,000"."""
    if value in (None, ""):
        return ""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value
