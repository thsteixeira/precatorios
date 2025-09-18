from django import template
from django.http import QueryDict

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """
    Replace or add a parameter in the current URL's query string.
    
    Usage: {% url_replace request 'page' 2 %}
    This will maintain all existing GET parameters and replace/add the specified one.
    """
    query_dict = request.GET.copy()
    query_dict[field] = value
    return query_dict.urlencode()

@register.simple_tag
def add_url_params(request, field, value):
    """
    Add or replace a parameter in the current URL's query string and return the query string.
    
    Usage: {% url 'view_name' %}{% add_url_params request 'page' 2 %}
    This will maintain all existing GET parameters and replace/add the specified one.
    """
    query_dict = request.GET.copy()
    query_dict[field] = value
    query_string = query_dict.urlencode()
    return f"?{query_string}" if query_string else ""