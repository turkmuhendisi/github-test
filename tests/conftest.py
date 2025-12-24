"""
Pytest Configuration & Fixtures
===============================

Tüm testler tarafından kullanılan ortak fixtures.
"""

import pytest
from django.conf import settings


# =============================================================================
# DJANGO CONFIGURATION
# =============================================================================

def pytest_configure():
    """pytest başlatılırken Django ayarlarını yapılandır."""
    settings.DEBUG = False
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture
def db_access(db):
    """Veritabanı erişimi sağlar."""
    pass


# =============================================================================
# USER FIXTURES
# =============================================================================

@pytest.fixture
def user(django_user_model):
    """Normal kullanıcı oluşturur."""
    return django_user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(django_user_model):
    """Admin kullanıcı oluşturur."""
    return django_user_model.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def authenticated_client(client, user):
    """Giriş yapmış client döndürür."""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Admin olarak giriş yapmış client döndürür."""
    client.force_login(admin_user)
    return client


# =============================================================================
# API FIXTURES (DRF için)
# =============================================================================

@pytest.fixture
def api_client():
    """DRF API client döndürür."""
    try:
        from rest_framework.test import APIClient
        return APIClient()
    except ImportError:
        pytest.skip("Django REST Framework not installed")


@pytest.fixture
def authenticated_api_client(api_client, user):
    """Authenticated API client döndürür."""
    api_client.force_authenticate(user=user)
    return api_client


# =============================================================================
# REQUEST FIXTURES
# =============================================================================

@pytest.fixture
def rf():
    """Django RequestFactory döndürür."""
    from django.test import RequestFactory
    return RequestFactory()


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_request(rf, user):
    """Mock request objesi döndürür."""
    request = rf.get('/')
    request.user = user
    return request

