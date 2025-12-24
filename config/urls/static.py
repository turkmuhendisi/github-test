"""
Static ve Media URL'leri (Development Only)
===========================================

Bu dosya sadece DEBUG=True olduğunda kullanılır.
Production'da nginx veya CDN ile serve edilmeli.

Not: Django dev server static dosyaları STATICFILES_DIRS'den serve eder,
     STATIC_ROOT sadece collectstatic için kullanılır.
"""

from django.conf import settings
from django.conf.urls.static import static

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = []

if settings.DEBUG:
    # Media files - user uploads
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        urlpatterns += static(
            settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT
        )
    
    # Static files - Django runserver otomatik serve eder
    # STATICFILES_DIRS'den. Ama açıkça eklemek istiyorsak:
    # Not: Django'nun runserver'ı staticfiles app yüklüyse
    # otomatik olarak STATICFILES_DIRS'den serve eder.
    # Bu nedenle genelde ek bir şey yapmaya gerek yok.