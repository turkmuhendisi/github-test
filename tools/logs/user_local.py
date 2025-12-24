"""
Thread-Local Storage
====================

Her thread için ayrı kullanıcı ve istek bilgisi saklar.
Middleware tarafından set edilir, logger tarafından okunur.

Kullanım:
--------
from tools.logs.user_local import user_local

# Middleware'de set et
user_local.user = request.user
user_local.ip_address = get_client_ip(request)
user_local.request_id = generate_request_id()

# Logger'da oku
username = getattr(user_local, 'user', None)
"""

from threading import local
from typing import Optional, Any

# Thread-local storage instance
user_local = local()


def set_user_context(
    user: Any = None,
    ip_address: str = None,
    request_id: str = None,
    path: str = None,
    method: str = None,
) -> None:
    """
    Thread-local context'e kullanıcı bilgilerini set eder.
    
    Args:
        user: Django User instance veya None
        ip_address: Client IP adresi
        request_id: Unique request ID (tracking için)
        path: Request path
        method: HTTP method
    """
    user_local.user = user
    user_local.ip_address = ip_address or 'Unknown'
    user_local.request_id = request_id or '-'
    user_local.path = path or '-'
    user_local.method = method or '-'


def clear_user_context() -> None:
    """Thread-local context'i temizler."""
    user_local.user = None
    user_local.ip_address = 'Unknown'
    user_local.request_id = '-'
    user_local.path = '-'
    user_local.method = '-'


def get_username() -> str:
    """Mevcut kullanıcı adını döndürür."""
    from django.contrib.auth.models import AnonymousUser
    
    user = getattr(user_local, 'user', None)
    if user is None or isinstance(user, AnonymousUser):
        return 'Anonymous'
    return getattr(user, 'username', str(user))


def get_ip_address() -> str:
    """Mevcut IP adresini döndürür."""
    return getattr(user_local, 'ip_address', 'Unknown')


def get_request_id() -> str:
    """Mevcut request ID'sini döndürür."""
    return getattr(user_local, 'request_id', '-')