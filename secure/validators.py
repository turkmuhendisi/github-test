"""
Input Validators
================

Giriş doğrulama fonksiyonları.

Kullanım:
--------
from secure.validators import (
    validate_email,
    validate_phone,
    validate_url,
    is_valid_email,
)

# Boolean döndürür
if is_valid_email('user@example.com'):
    print('Geçerli')

# Exception fırlatır
try:
    validate_email('invalid-email')
except ValidationError as e:
    print(e)
"""

import re
from typing import Optional
from urllib.parse import urlparse


class ValidationError(Exception):
    """Doğrulama hatası."""
    pass


# =============================================================================
# EMAIL VALIDATION
# =============================================================================

EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def is_valid_email(email: str) -> bool:
    """Email geçerli mi kontrol eder."""
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email))


def validate_email(email: str) -> str:
    """
    Email doğrular ve normalize eder.
    
    Raises:
        ValidationError: Geçersiz email
    """
    if not email:
        raise ValidationError("Email boş olamaz")
    
    email = email.strip().lower()
    
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Geçersiz email formatı")
    
    return email


# =============================================================================
# PHONE VALIDATION
# =============================================================================

PHONE_PATTERN = re.compile(r'^[0-9]{10,11}$')
TURKISH_PHONE_PATTERN = re.compile(r'^(0)?5[0-9]{9}$')


def is_valid_phone(phone: str, country: str = 'TR') -> bool:
    """Telefon numarası geçerli mi kontrol eder."""
    if not phone:
        return False
    
    # Sadece rakamları al
    digits = ''.join(filter(str.isdigit, phone))
    
    if country == 'TR':
        return bool(TURKISH_PHONE_PATTERN.match(digits))
    
    return bool(PHONE_PATTERN.match(digits))


def validate_phone(phone: str, country: str = 'TR') -> str:
    """
    Telefon numarasını doğrular ve normalize eder.
    
    Raises:
        ValidationError: Geçersiz telefon
    """
    if not phone:
        raise ValidationError("Telefon numarası boş olamaz")
    
    # Sadece rakamları al
    digits = ''.join(filter(str.isdigit, phone))
    
    if country == 'TR':
        if not TURKISH_PHONE_PATTERN.match(digits):
            raise ValidationError("Geçersiz Türkiye telefon numarası")
        
        # Normalize: 0 ile başlamasını sağla
        if not digits.startswith('0'):
            digits = '0' + digits
    else:
        if not PHONE_PATTERN.match(digits):
            raise ValidationError("Geçersiz telefon numarası")
    
    return digits


# =============================================================================
# URL VALIDATION
# =============================================================================

def is_valid_url(url: str, require_https: bool = False) -> bool:
    """URL geçerli mi kontrol eder."""
    if not url:
        return False
    
    try:
        result = urlparse(url)
        
        if require_https and result.scheme != 'https':
            return False
        
        return all([
            result.scheme in ('http', 'https'),
            result.netloc
        ])
    except Exception:
        return False


def validate_url(url: str, require_https: bool = False) -> str:
    """
    URL doğrular.
    
    Raises:
        ValidationError: Geçersiz URL
    """
    if not url:
        raise ValidationError("URL boş olamaz")
    
    url = url.strip()
    
    if not is_valid_url(url, require_https):
        if require_https:
            raise ValidationError("Geçersiz URL (HTTPS gerekli)")
        raise ValidationError("Geçersiz URL formatı")
    
    return url


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

def validate_password(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_symbol: bool = False,
) -> str:
    """
    Şifre kurallarını doğrular.
    
    Raises:
        ValidationError: Kurallara uymayan şifre
    """
    if not password:
        raise ValidationError("Şifre boş olamaz")
    
    errors = []
    
    if len(password) < min_length:
        errors.append(f"Şifre en az {min_length} karakter olmalı")
    
    if require_uppercase and not any(c.isupper() for c in password):
        errors.append("Şifre en az bir büyük harf içermeli")
    
    if require_lowercase and not any(c.islower() for c in password):
        errors.append("Şifre en az bir küçük harf içermeli")
    
    if require_digit and not any(c.isdigit() for c in password):
        errors.append("Şifre en az bir rakam içermeli")
    
    if require_symbol:
        symbols = set('!@#$%^&*()-_=+[]{}|;:,.<>?')
        if not any(c in symbols for c in password):
            errors.append("Şifre en az bir sembol içermeli")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return password


# =============================================================================
# COMMON VALIDATORS
# =============================================================================

def validate_not_empty(value: str, field_name: str = 'Değer') -> str:
    """Boş olmadığını doğrular."""
    if not value or not value.strip():
        raise ValidationError(f"{field_name} boş olamaz")
    return value.strip()


def validate_length(
    value: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = 'Değer'
) -> str:
    """Uzunluk sınırlarını doğrular."""
    if min_length and len(value) < min_length:
        raise ValidationError(f"{field_name} en az {min_length} karakter olmalı")
    
    if max_length and len(value) > max_length:
        raise ValidationError(f"{field_name} en fazla {max_length} karakter olmalı")
    
    return value


def validate_alphanumeric(value: str, field_name: str = 'Değer') -> str:
    """Sadece harf ve rakam içerdiğini doğrular."""
    if not value.isalnum():
        raise ValidationError(f"{field_name} sadece harf ve rakam içerebilir")
    return value

