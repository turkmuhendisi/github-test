"""
Core Template Tags
==================

Genel amaçlı template tag ve filter'lar.

Kullanım:
--------
{% load core_tags %}

{% site_name %}
{% active_url 'home' %}
{{ price|currency }}
{{ phone|phone_format }}
"""

from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

# =============================================================================
# SIMPLE TAGS
# =============================================================================

@register.simple_tag
def site_name():
    """Site adını döndürür."""
    return "GlobalMain"


@register.simple_tag(takes_context=True)
def active_url(context, url_name, css_class='active'):
    """
    Aktif sayfa için CSS class döndürür.
    
    Kullanım:
        <a class="{% active_url 'home' %}">Ana Sayfa</a>
    """
    request = context.get('request')
    if request and hasattr(request, 'resolver_match') and request.resolver_match:
        if request.resolver_match.url_name == url_name:
            return css_class
    return ''


@register.simple_tag
def json_script(data, element_id):
    """
    JavaScript için JSON data.
    
    Kullanım:
        {% json_script my_data 'my-data' %}
        <script>
            const data = JSON.parse(document.getElementById('my-data').textContent);
        </script>
    """
    json_data = json.dumps(data)
    return mark_safe(f'<script id="{element_id}" type="application/json">{json_data}</script>')


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """
    URL query string oluşturur veya günceller.
    
    Kullanım:
        <a href="?{% query_string page=2 %}">Sayfa 2</a>
        <a href="?{% query_string page=page_obj.next_page_number %}">Sonraki</a>
    """
    request = context.get('request')
    if not request:
        return ''
    
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    
    return params.urlencode()


# =============================================================================
# FILTERS
# =============================================================================

@register.filter
def currency(value, symbol='₺'):
    """
    Para birimi formatı.
    
    Kullanım:
        {{ price|currency }}      → ₺1,234.56
        {{ price|currency:'$' }}  → $1,234.56
    """
    try:
        return f"{symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter
def phone_format(value):
    """
    Telefon numarası formatı.
    
    Kullanım:
        {{ phone|phone_format }}  → (532) 123 4567
    """
    if not value:
        return ''
    digits = ''.join(filter(str.isdigit, str(value)))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]} {digits[6:]}"
    elif len(digits) == 11 and digits[0] == '0':
        return f"({digits[1:4]}) {digits[4:7]} {digits[7:]}"
    return value


@register.filter
def truncate_chars(value, max_length):
    """
    Karakter sayısına göre kısalt.
    
    Kullanım:
        {{ text|truncate_chars:50 }}
    """
    if not value:
        return ''
    value = str(value)
    if len(value) <= max_length:
        return value
    return value[:max_length-3] + '...'


@register.filter
def percentage(value, decimals=1):
    """
    Yüzde formatı.
    
    Kullanım:
        {{ ratio|percentage }}    → 75.5%
        {{ ratio|percentage:0 }}  → 76%
    """
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return value


@register.filter
def file_size(value):
    """
    Dosya boyutu formatı.
    
    Kullanım:
        {{ size|file_size }}  → 1.5 MB
    """
    try:
        value = float(value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"
    except (ValueError, TypeError):
        return value


# =============================================================================
# INCLUSION TAGS
# =============================================================================

@register.inclusion_tag('components/pagination.html', takes_context=True)
def pagination(context, page_obj, adjacent_pages=2):
    """
    Sayfalama bileşeni.
    
    Kullanım:
        {% pagination page_obj %}
        {% pagination page_obj adjacent_pages=3 %}
    """
    return {
        'page_obj': page_obj,
        'adjacent_pages': adjacent_pages,
        'request': context.get('request'),
    }


@register.inclusion_tag('components/breadcrumb.html')
def breadcrumb(items):
    """
    Breadcrumb bileşeni.
    
    Kullanım:
        {% breadcrumb items %}
        
    items = [
        {'title': 'Ana Sayfa', 'url': '/'},
        {'title': 'Ürünler', 'url': '/products/'},
        {'title': 'Detay'},  # Son öğe, URL yok
    ]
    """
    return {'items': items}

