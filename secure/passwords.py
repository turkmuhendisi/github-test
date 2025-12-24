"""
Password Utilities
==================

Şifre hashleme ve doğrulama fonksiyonları.

Kullanım:
--------
from secure.passwords import hash_value, verify_hash

hashed = hash_value('my_password')
is_valid = verify_hash('my_password', hashed)

NOT:
----
Django'nun password hasher'larını kullanmanız önerilir:
from django.contrib.auth.hashers import make_password, check_password

Bu modül Django dışı kullanımlar içindir.
"""

import hashlib
import hmac
import secrets
from typing import Optional


def hash_value(value: str, salt: Optional[str] = None, algorithm: str = 'sha256') -> str:
    """
    Değeri hashler.
    
    Args:
        value: Hashlenecek değer
        salt: Opsiyonel salt (yoksa üretilir)
        algorithm: Hash algoritması ('sha256', 'sha512', 'blake2b')
        
    Returns:
        str: 'algorithm:salt:hash' formatında hash
        
    Example:
        >>> hashed = hash_value('my_password')
        >>> print(hashed)  # 'sha256:abc123...:def456...'
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Değeri encode et
    value_bytes = (salt + value).encode('utf-8')
    
    # Hash hesapla
    if algorithm == 'sha256':
        hash_obj = hashlib.sha256(value_bytes)
    elif algorithm == 'sha512':
        hash_obj = hashlib.sha512(value_bytes)
    elif algorithm == 'blake2b':
        hash_obj = hashlib.blake2b(value_bytes)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    hash_hex = hash_obj.hexdigest()
    
    return f"{algorithm}:{salt}:{hash_hex}"


def verify_hash(value: str, hashed: str) -> bool:
    """
    Değeri hash ile doğrular.
    
    Args:
        value: Doğrulanacak değer
        hashed: 'algorithm:salt:hash' formatında hash
        
    Returns:
        bool: Doğrulama sonucu
        
    Example:
        >>> hashed = hash_value('my_password')
        >>> verify_hash('my_password', hashed)
        True
        >>> verify_hash('wrong_password', hashed)
        False
    """
    try:
        parts = hashed.split(':')
        if len(parts) != 3:
            return False
        
        algorithm, salt, _ = parts
        
        # Aynı salt ile tekrar hashle
        new_hash = hash_value(value, salt=salt, algorithm=algorithm)
        
        # Timing-safe karşılaştırma
        return hmac.compare_digest(hashed, new_hash)
    except Exception:
        return False


def generate_password(length: int = 16, include_symbols: bool = True) -> str:
    """
    Güvenli rastgele şifre üretir.
    
    Args:
        length: Şifre uzunluğu
        include_symbols: Sembol içersin mi
        
    Returns:
        str: Rastgele şifre
        
    Example:
        >>> password = generate_password(16)
        >>> print(password)  # 'Abc123!@def456$%'
    """
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    if include_symbols:
        alphabet += '!@#$%^&*()-_=+[]{}|;:,.<>?'
    
    # En az bir büyük harf, bir küçük harf ve bir rakam
    password_chars = [
        secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        secrets.choice('abcdefghijklmnopqrstuvwxyz'),
        secrets.choice('0123456789'),
    ]
    
    if include_symbols:
        password_chars.append(secrets.choice('!@#$%^&*()-_=+'))
    
    # Kalan karakterleri rastgele seç
    remaining = length - len(password_chars)
    password_chars.extend(secrets.choice(alphabet) for _ in range(remaining))
    
    # Karıştır
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)

