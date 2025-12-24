"""
Proje kurulum komutu
====================

Kullanım:
    python manage.py setup_project

Bu komut:
1. Tüm veritabanlarında migration çalıştırır
2. Superuser oluşturur (yoksa)
3. Initial data yükler (varsa)
4. Static files toplar
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Projeyi baştan kurar: migrations, superuser, static files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-static',
            action='store_true',
            help='Static files toplama işlemini atla',
        )
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Superuser oluşturmayı atla',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🚀 Proje kurulumu başlıyor...'))
        
        # 1. Migrations
        self.run_migrations()
        
        # 2. Superuser
        if not options['skip_superuser']:
            self.create_superuser()
        
        # 3. Static files
        if not options['skip_static']:
            self.collect_static()
        
        self.stdout.write(self.style.SUCCESS('✅ Proje kurulumu tamamlandı!'))

    def run_migrations(self):
        """Tüm veritabanlarında migration çalıştır."""
        self.stdout.write(self.style.NOTICE('📦 Migrations çalıştırılıyor...'))
        
        databases = ['default']
        
        # Analytics aktifse
        if getattr(settings, 'DB_ANALYTICS_ENABLED', False) or 'analytics' in settings.DATABASES:
            databases.append('analytics')
        
        # Logs aktifse
        if getattr(settings, 'DB_LOGS_ENABLED', False) or 'logs' in settings.DATABASES:
            databases.append('logs')
        
        for db in databases:
            try:
                self.stdout.write(f'  → {db} database...')
                call_command('migrate', database=db, verbosity=0)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {db} migration tamamlandı'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ {db} migration hatası: {e}'))

    def create_superuser(self):
        """Superuser oluştur (yoksa)."""
        self.stdout.write(self.style.NOTICE('👤 Superuser kontrol ediliyor...'))
        
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'  → Superuser "{username}" zaten mevcut')
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Superuser "{username}" oluşturuldu'))

    def collect_static(self):
        """Static files topla."""
        self.stdout.write(self.style.NOTICE('📁 Static files toplanıyor...'))
        try:
            call_command('collectstatic', verbosity=0, interactive=False)
            self.stdout.write(self.style.SUCCESS('  ✓ Static files toplandı'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠ Static files hatası: {e}'))