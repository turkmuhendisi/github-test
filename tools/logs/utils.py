"""
Logging Utilities
=================

Merkezi log yardımcı fonksiyonları.
Tüm middleware ve servisler bu modülü kullanmalı.

Fonksiyonlar:
------------
- get_client_ip: Client IP adresini döndürür (proxy-aware)
- generate_request_id: Unique request ID üretir
- mask_sensitive_data: Hassas verileri maskeler
"""

import uuid
import re
from typing import Optional, Any

from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """
    Client IP adresini döndürür.
    Proxy arkasındaysa X-Forwarded-For header'ını kontrol eder.
    
    Args:
        request: Django HttpRequest objesi
        
    Returns:
        str: Client IP adresi
        
    Example:
        >>> from tools.logs.utils import get_client_ip
        >>> ip = get_client_ip(request)
        >>> print(ip)  # '192.168.1.1'
    
    Notes:
        - X-Forwarded-For header'ı varsa ilk IP kullanılır
        - Proxy zincirinde: "client, proxy1, proxy2" formatında
        - Header yoksa REMOTE_ADDR kullanılır
        - Hiçbiri yoksa 'Unknown' döner
    """
    # X-Forwarded-For header'ı kontrol et (reverse proxy arkasında)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # İlk IP gerçek client IP'sidir
        # Format: "client, proxy1, proxy2"
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Direkt bağlantı
        ip = request.META.get('REMOTE_ADDR', 'Unknown')
    
    return ip


def generate_request_id() -> str:
    """
    Unique request ID üretir.
    Distributed tracing ve log korelasyonu için kullanılır.
    
    Returns:
        str: 8 karakterlik unique ID
        
    Example:
        >>> from tools.logs.utils import generate_request_id
        >>> request_id = generate_request_id()
        >>> print(request_id)  # 'a1b2c3d4'
    """
    return str(uuid.uuid4())[:8]


def mask_sensitive_data(data: Any, fields: tuple = None) -> Any:
    """
    Hassas verileri maskeler.
    
    Args:
        data: Maskelenecek veri (dict, str veya diğer)
        fields: Maskelenecek alan isimleri (varsayılan: password, token, secret, key)
        
    Returns:
        Maskelenmiş veri
        
    Example:
        >>> data = {'username': 'john', 'password': 'secret123'}
        >>> masked = mask_sensitive_data(data)
        >>> print(masked)  # {'username': 'john', 'password': '***'}
    """
    if fields is None:
        fields = ('password', 'token', 'secret', 'key', 'api_key', 'auth', 'credential')
    
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(f in key.lower() for f in fields):
                masked[key] = '***'
            elif isinstance(value, dict):
                masked[key] = mask_sensitive_data(value, fields)
            else:
                masked[key] = value
        return masked
    
    return data


def sanitize_path(path: str, max_length: int = 500) -> str:
    """
    URL path'ini temizler ve kısaltır.
    
    Args:
        path: URL path
        max_length: Maksimum karakter sayısı
        
    Returns:
        str: Temizlenmiş path
    """
    if not path:
        return '/'
    
    # Tehlikeli karakterleri temizle
    path = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', path)
    
    # Maksimum uzunluk
    if len(path) > max_length:
        path = path[:max_length] + '...'
    
    return path


def get_user_identifier(request: HttpRequest) -> str:
    """
    Request'ten kullanıcı tanımlayıcısını döndürür.
    
    Args:
        request: Django HttpRequest objesi
        
    Returns:
        str: Kullanıcı adı, ID veya 'Anonymous'
    """
    if hasattr(request, 'user'):
        user = request.user
        if user.is_authenticated:
            return getattr(user, 'username', str(user.id))
    return 'Anonymous'

