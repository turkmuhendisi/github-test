"""
Webapp Core Module
==================

Merkezi web uygulaması bileşenleri.

İçerik:
------
- context_processors: Template context processors
- templatetags: Custom template tags ve filters

Kullanım:
--------
# settings.py - Context Processors
'webapp.core.context_processors.site_settings',

# Template - Custom Tags
{% load core_tags %}
{% site_name %}
"""

