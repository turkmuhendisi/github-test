"""
Temel URL Utilities ve Patterns
"""

from django.urls import path
from django.http import HttpResponse

# =============================================================================
# UTILITY VIEWS
# =============================================================================

def robots_txt(request):
    """robots.txt dosyası."""
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Allow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def favicon(request):
    """Favicon redirect veya 204 response."""
    return HttpResponse(status=204)

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    path('robots.txt', robots_txt, name='robots'),
    path('favicon.ico', favicon, name='favicon'),
]