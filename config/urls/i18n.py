"""
Internationalization URL'leri
"""

from django.urls import path, include

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Dil değiştirme endpoint'i
    path('i18n/', include('django.conf.urls.i18n')),
]