"""
Django settings doğrulama scripti.
python manage.py shell < check_settings.py
"""

from django.conf import settings

print("=" * 60)
print("DJANGO SETTINGS KONTROLÜ")
print("=" * 60)

# Environment
print(f"\n📌 ENVIRONMENT")
print(f"  DJANGO_ENV: {getattr(settings, 'DJANGO_ENV', 'N/A')}")
print(f"  DEBUG: {settings.DEBUG}")
print(f"  SECRET_KEY: {'✓ Set' if settings.SECRET_KEY else '✗ Missing'}")

# Databases
print(f"\n📌 DATABASES")
for db_name, db_config in settings.DATABASES.items():
    host = db_config.get('HOST', 'N/A')
    port = db_config.get('PORT', 'N/A')
    name = db_config.get('NAME', 'N/A')
    print(f"  {db_name}: {host}:{port}/{name}")

# Installed Apps
print(f"\n📌 INSTALLED_APPS")
print(f"  Total: {len(settings.INSTALLED_APPS)}")

# Middleware
print(f"\n📌 MIDDLEWARE")
print(f"  Total: {len(settings.MIDDLEWARE)}")

# URLs
print(f"\n📌 URLs")
print(f"  ROOT_URLCONF: {settings.ROOT_URLCONF}")

# Static
print(f"\n📌 STATIC FILES")
print(f"  STATIC_URL: {settings.STATIC_URL}")
print(f"  STATIC_ROOT: {getattr(settings, 'STATIC_ROOT', 'N/A')}")

# Logging
print(f"\n📌 LOGGING")
print(f"  Configured: {'✓' if hasattr(settings, 'LOGGING') else '✗'}")

print("\n" + "=" * 60)
print("KONTROL TAMAMLANDI")
print("=" * 60)