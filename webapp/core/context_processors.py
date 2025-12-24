"""
Context Processors
==================

Template'lerde global olarak erişilebilen değişkenler.

Kullanım:
--------
TEMPLATES ayarında context_processors listesine ekleyin:
'webapp.core.context_processors.site_settings',
"""

from datetime import datetime

from django.conf import settings


def site_settings(request):
    """Site geneli değişkenler."""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'GlobalMain'),
        'SITE_URL': getattr(settings, 'SITE_URL', 'https://example.com'),
        'SUPPORT_EMAIL': getattr(settings, 'SUPPORT_EMAIL', 'support@example.com'),
        'CURRENT_YEAR': datetime.now().year,
        'DEBUG': settings.DEBUG,
    }


def navigation(request):
    """
    Navigasyon menüsü.
    
    NOT: Bu fonksiyon MenuItem modeli oluşturulduğunda aktifleştirilmeli.
    Şimdilik boş dict döndürür.
    """
    # TODO: core.models.MenuItem oluşturulduğunda bu kısmı aktifleştir
    # try:
    #     from core.models import MenuItem
    #     return {
    #         'nav_items': MenuItem.objects.filter(is_active=True),
    #     }
    # except ImportError:
    #     pass
    return {'nav_items': []}


def user_preferences(request):
    """
    Kullanıcı tercihleri.
    
    NOT: Profile modeli oluşturulduğunda tam işlevsellik sağlanır.
    Şimdilik varsayılan değerler döndürür.
    """
    if request.user.is_authenticated:
        # Profile modeli varsa kullan, yoksa varsayılan değerler
        profile = getattr(request.user, 'profile', None)
        if profile:
            return {
                'theme': getattr(profile, 'theme', 'light'),
                'language': getattr(profile, 'language', 'tr'),
            }
        return {
            'theme': 'light',
            'language': 'tr',
        }
    return {
        'theme': 'light',
        'language': 'tr',
    }

