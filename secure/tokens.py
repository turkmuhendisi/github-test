"""
Secure Token Generation
=======================

Güvenli token ve UUID üretimi.

Kullanım:
--------
from secure.tokens import generate_secure_token, generate_uuid

token = generate_secure_token(32)
uuid_str = generate_uuid()
"""

import secrets
import uuid as _uuid
from typing import Optional


def generate_secure_token(length: int = 32) -> str:
    """
    Kriptografik olarak güvenli rastgele token üretir.
    
    Args:
        length: Token uzunluğu (byte cinsinden)
        
    Returns:
        str: Hex formatında token
        
    Example:
        >>> token = generate_secure_token(32)
        >>> len(token)
        64
    """
    return secrets.token_hex(length)


def generate_url_safe_token(length: int = 32) -> str:
    """
    URL-safe base64 encoded token üretir.
    
    Args:
        length: Token uzunluğu (byte cinsinden)
        
    Returns:
        str: URL-safe token
    """
    return secrets.token_urlsafe(length)


def generate_uuid() -> str:
    """
    UUID4 (random) üretir.
    
    Returns:
        str: UUID string
        
    Example:
        >>> uuid_str = generate_uuid()
        >>> print(uuid_str)  # '123e4567-e89b-12d3-a456-426614174000'
    """
    return str(_uuid.uuid4())


def generate_short_uuid(length: int = 8) -> str:
    """
    Kısa UUID üretir (ilk N karakter).
    
    Args:
        length: Karakter sayısı (max 32)
        
    Returns:
        str: Kısa UUID
        
    Example:
        >>> short = generate_short_uuid(8)
        >>> print(short)  # 'a1b2c3d4'
    """
    return str(_uuid.uuid4()).replace('-', '')[:length]


def generate_api_key(prefix: Optional[str] = None) -> str:
    """
    API anahtarı üretir.
    
    Args:
        prefix: Opsiyonel prefix (örn: 'sk_', 'pk_')
        
    Returns:
        str: API anahtarı
        
    Example:
        >>> key = generate_api_key('sk_')
        >>> print(key)  # 'sk_a1b2c3d4e5f6...'
    """
    token = secrets.token_hex(24)  # 48 karakter
    if prefix:
        return f"{prefix}{token}"
    return token


def generate_otp(length: int = 6) -> str:
    """
    One-Time Password üretir.
    
    Args:
        length: OTP uzunluğu (varsayılan 6)
        
    Returns:
        str: Numerik OTP
        
    Example:
        >>> otp = generate_otp()
        >>> print(otp)  # '123456'
    """
    # Sayısal karakter seti
    digits = '0123456789'
    return ''.join(secrets.choice(digits) for _ in range(length))

