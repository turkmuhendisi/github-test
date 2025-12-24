"""
GlobalMain Test Suite
=====================

Test dizin yapısı:

tests/
├── __init__.py          # Bu dosya
├── conftest.py          # Shared pytest fixtures
├── unit/                # Unit tests
│   ├── test_models.py
│   ├── test_views.py
│   └── test_utils.py
├── integration/         # Integration tests
│   └── test_api.py
└── e2e/                 # End-to-end tests
    └── test_flows.py

Kullanım:
--------
# Tüm testleri çalıştır
pytest

# Belirli bir modülü test et
pytest tests/unit/

# Coverage ile
pytest --cov=.

# Verbose
pytest -v
"""

