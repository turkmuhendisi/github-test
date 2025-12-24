"""
Authentication URL'leri
"""

from django.urls import path, include

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Django built-in auth views
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Custom auth views (oluşturulduğunda)
    # path('accounts/', include('services.auth.urls')),
]