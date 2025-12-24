"""
Secure Module
=============

Merkezi Kimlik ve Güvenlik Yönetim Sistemi.

İçerik:
------
- encryption.py     : Field-level encryption
- tokens.py         : Secure token generation
- validators.py     : Input validation
- sanitizers.py     : XSS/SQL injection prevention
- permissions.py    : Custom permission classes
- passwords.py      : Password utilities

Kullanım:
--------
from secure import generate_secure_token, hash_value
from secure.validators import validate_email, validate_phone
from secure.encryption import encrypt_value, decrypt_value

Örnek:
------
>>> from secure import generate_secure_token
>>> token = generate_secure_token(32)
>>> print(token)  # 'a1b2c3d4...'

>>> from secure import hash_value
>>> hashed = hash_value('my_password')
>>> print(hashed)  # 'sha256:...'
"""

from .tokens import (
    generate_secure_token,
    generate_uuid,
    generate_short_uuid,
)

from .passwords import (
    hash_value,
    verify_hash,
)

__version__ = '1.0.0'

__all__ = [
    # Tokens
    'generate_secure_token',
    'generate_uuid',
    'generate_short_uuid',
    # Passwords
    'hash_value',
    'verify_hash',
]
