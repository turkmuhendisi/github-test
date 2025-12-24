"""
Django Admin URL'leri
"""

from django.contrib import admin
from django.urls import path
from django.conf.urls.i18n import i18n_patterns

# =============================================================================
# ADMIN CUSTOMIZATION
# =============================================================================

admin.site.site_header = "Asrın Global Yönetim Paneli"
admin.site.site_title = "Asrın Global Admin"
admin.site.index_title = "Yönetim Paneli"

# =============================================================================
# URL PATTERNS (i18n destekli)
# =============================================================================

# i18n_patterns ile dil prefix'li admin URL'leri
urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    prefix_default_language=False,
)