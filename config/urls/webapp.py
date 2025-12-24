"""
Webapp Frontend URL'leri
========================

Ana web uygulaması URL'leri.
"""

from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

# =============================================================================
# URL PATTERNS
# =============================================================================

# Webapp home modülü URL'leri (i18n destekli)
urlpatterns = i18n_patterns(
    # Home app
    path('', include('webapp.home.urls', namespace='home')),
    
    # Diğer webapp modülleri (oluşturulduğunda)
    # path('dashboard/', include('webapp.dashboard.urls')),
    # path('profile/', include('webapp.profile.urls')),
    
    prefix_default_language=False,
)