"""
Form Template Tags
==================

Form rendering için template tag ve filter'lar.

Kullanım:
--------
{% load form_tags %}

{{ form|add_class:'form-control' }}
{% render_field form.email class='form-control' placeholder='E-posta' %}
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


# =============================================================================
# FILTERS
# =============================================================================

@register.filter
def add_class(field, css_class):
    """
    Form field'a CSS class ekler.
    
    Kullanım:
        {{ form.email|add_class:'form-control' }}
    """
    if hasattr(field, 'field'):
        existing_class = field.field.widget.attrs.get('class', '')
        new_class = f"{existing_class} {css_class}".strip()
        return field.as_widget(attrs={'class': new_class})
    return field


@register.filter
def add_attr(field, attr_string):
    """
    Form field'a attribute ekler.
    
    Kullanım:
        {{ form.email|add_attr:'placeholder:E-posta adresiniz' }}
        {{ form.password|add_attr:'autocomplete:new-password' }}
    """
    if hasattr(field, 'field'):
        if ':' in attr_string:
            attr_name, attr_value = attr_string.split(':', 1)
            return field.as_widget(attrs={attr_name: attr_value})
    return field


@register.filter
def add_error_class(field, error_class='is-invalid'):
    """
    Hatalı field'a CSS class ekler.
    
    Kullanım:
        {{ form.email|add_error_class }}
        {{ form.email|add_error_class:'error' }}
    """
    if hasattr(field, 'errors') and field.errors:
        existing_class = field.field.widget.attrs.get('class', '')
        new_class = f"{existing_class} {error_class}".strip()
        return field.as_widget(attrs={'class': new_class})
    return field


# =============================================================================
# SIMPLE TAGS
# =============================================================================

@register.simple_tag
def render_field(field, **kwargs):
    """
    Form field'ı custom attribute'larla render eder.
    
    Kullanım:
        {% render_field form.email class='form-control' placeholder='E-posta' %}
        {% render_field form.message rows='5' class='form-control' %}
    """
    if hasattr(field, 'field'):
        return field.as_widget(attrs=kwargs)
    return field


@register.simple_tag
def form_errors(form):
    """
    Form hatalarını HTML olarak döndürür.
    
    Kullanım:
        {% form_errors form %}
    """
    if not form.errors:
        return ''
    
    html = '<div class="alert alert-danger"><ul class="mb-0">'
    for field, errors in form.errors.items():
        for error in errors:
            if field == '__all__':
                html += f'<li>{error}</li>'
            else:
                html += f'<li><strong>{field}:</strong> {error}</li>'
    html += '</ul></div>'
    
    return mark_safe(html)


@register.inclusion_tag('components/form_field.html')
def form_field(field, label=None, help_text=None, show_errors=True):
    """
    Form field'ı wrapper ile render eder.
    
    Kullanım:
        {% form_field form.email %}
        {% form_field form.email label='E-posta Adresi' %}
        {% form_field form.password help_text='En az 8 karakter' %}
    """
    return {
        'field': field,
        'label': label or field.label,
        'help_text': help_text or field.help_text,
        'show_errors': show_errors,
        'errors': field.errors if hasattr(field, 'errors') else [],
    }

