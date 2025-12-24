"""
Debug Toolbar URL'leri (Development Only)
=========================================

debug_toolbar sadece:
1. DEBUG=True
2. INSTALLED_APPS'te varsa
3. Paket yüklüyse

aktif olur.
"""

from django.urls import path, include
from django.conf import settings

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = []

# Debug toolbar sadece DEBUG modda ve INSTALLED_APPS'te varsa aktif
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass  # debug_toolbar paketi yüklü değil