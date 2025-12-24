# -*- coding: utf-8 -*-
"""
Monitor Management Command
===========================

Terminalde canlı sistem izleme aracını başlatır.

Kullanım:
    python manage.py monitor            # Unified Monitor (önerilen)
    python manage.py monitor --unified  # Unified Monitor
    python manage.py monitor --live     # Live request flow monitor
    python manage.py monitor --simple   # Basit ANSI modu
    python manage.py monitor --demo     # Demo modu (sahte trafik)
"""

from django.core.management.base import BaseCommand
import time
import random
import threading


class Command(BaseCommand):
    help = 'Canlı sistem izleme aracını başlatır'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--unified',
            action='store_true',
            help='Unified Monitor - tüm özellikler tek ekranda (varsayılan)',
        )
        parser.add_argument(
            '--live',
            action='store_true',
            help='Live Monitor - request akış izleme',
        )
        parser.add_argument(
            '--simple',
            action='store_true',
            help='Rich olmadan basit ANSI modunda çalıştır',
        )
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Demo modu - sahte trafik oluştur (sadece --live ile)',
        )
        parser.add_argument(
            '--refresh',
            type=float,
            default=1.0,
            help='Yenileme hızı (saniye)',
        )
    
    def handle(self, *args, **options):
        # Live monitor modu
        if options['live']:
            self._run_live_monitor(options)
            return
        
        # Unified monitor (varsayılan)
        self._run_unified_monitor(options)
    
    def _run_unified_monitor(self, options):
        """Unified Monitor'u çalıştır."""
        try:
            from tools.monitor.unified_monitor import UnifiedMonitor, SimpleMonitor, RICH_AVAILABLE
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Import hatası: {e}'))
            return
        
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('╔══════════════════════════════════════════════════════════════╗'))
        self.stdout.write(self.style.NOTICE('║           🔴 GLOBALMAIN UNIFIED MONITOR                      ║'))
        self.stdout.write(self.style.NOTICE('╠══════════════════════════════════════════════════════════════╣'))
        self.stdout.write(self.style.NOTICE('║  📊 Docker Containers + Services + Metrics                   ║'))
        self.stdout.write(self.style.NOTICE('║  📐 Animasyonlu Sistem Mimarisi                              ║'))
        self.stdout.write(self.style.NOTICE('║  🔄 Real-time Güncellemeler                                  ║'))
        self.stdout.write(self.style.NOTICE('╚══════════════════════════════════════════════════════════════╝'))
        self.stdout.write('')
        
        # Monitor seç
        if options['simple'] or not RICH_AVAILABLE:
            if not RICH_AVAILABLE:
                self.stdout.write(self.style.WARNING(
                    '⚠️  Rich kütüphanesi bulunamadı, basit mod kullanılıyor.'
                ))
                self.stdout.write(self.style.WARNING(
                    '   Kurulum: pip install rich'
                ))
            monitor = SimpleMonitor()
        else:
            monitor = UnifiedMonitor()
        
        self.stdout.write(self.style.SUCCESS('   Ctrl+C veya q ile çıkın.'))
        self.stdout.write('')
        
        time.sleep(1)
        
        try:
            monitor.run(refresh_rate=options['refresh'])
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Monitor durduruldu.'))
    
    def _run_live_monitor(self, options):
        """Live Monitor'u çalıştır (request tracking)."""
        try:
            from tools.monitor.live_monitor import (
                LiveMonitor, 
                SimpleMonitor, 
                RequestTracker,
                ComponentState,
                RICH_AVAILABLE
            )
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Import hatası: {e}'))
            return
        
        self.stdout.write(self.style.NOTICE('🔴 Live Request Monitor'))
        self.stdout.write('')
        
        # Monitor seç
        if options['simple'] or not RICH_AVAILABLE:
            if not RICH_AVAILABLE:
                self.stdout.write(self.style.WARNING(
                    '   Rich kütüphanesi bulunamadı, basit mod kullanılıyor.'
                ))
            monitor = SimpleMonitor()
        else:
            monitor = LiveMonitor()
        
        # Demo modu
        if options['demo']:
            self.stdout.write(self.style.SUCCESS('   Demo modu aktif - sahte trafik oluşturuluyor'))
            demo_thread = threading.Thread(
                target=self._generate_demo_traffic,
                args=(monitor.tracker,),
                daemon=True
            )
            demo_thread.start()
        else:
            self.stdout.write(self.style.SUCCESS(
                '   Middleware\'i MIDDLEWARE listesine ekleyin:'
            ))
            self.stdout.write(self.style.SUCCESS(
                '   "tools.monitor.middleware.MonitorMiddleware"'
            ))
        
        self.stdout.write('')
        self.stdout.write('   Ctrl+C ile durdurun.')
        self.stdout.write('')
        
        time.sleep(1)
        
        try:
            monitor.start(refresh_rate=options['refresh'])
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Monitor durduruldu.'))
    
    def _generate_demo_traffic(self, tracker: 'RequestTracker'):
        """Demo trafik oluştur."""
        from tools.monitor.live_monitor import ComponentState
        
        paths = [
            '/',
            '/api/v1/users/',
            '/api/v1/products/',
            '/admin/',
            '/health/',
            '/static/css/style.css',
            '/api/v1/orders/',
            '/login/',
            '/dashboard/',
        ]
        
        methods = ['GET', 'GET', 'GET', 'POST', 'PUT', 'DELETE']
        
        request_id = 0
        
        while True:
            request_id += 1
            path = random.choice(paths)
            method = random.choice(methods)
            
            # Request başlat
            tracker.track_request_start(
                request_id=f"demo-{request_id}",
                method=method,
                path=path,
                user=random.choice([None, 'admin', 'user1', 'guest'])
            )
            
            # Bileşenlerden geç
            time.sleep(random.uniform(0.05, 0.15))
            tracker.track_component('middleware', ComponentState.ACTIVE)
            
            time.sleep(random.uniform(0.05, 0.1))
            tracker.track_component('urls', ComponentState.ACTIVE)
            
            time.sleep(random.uniform(0.05, 0.1))
            tracker.track_component('views', ComponentState.ACTIVE)
            
            # Bazen DB sorgusu
            if random.random() > 0.3:
                time.sleep(random.uniform(0.02, 0.08))
                tracker.track_component('models', ComponentState.ACTIVE)
                
                for _ in range(random.randint(1, 5)):
                    time.sleep(random.uniform(0.01, 0.03))
                    tracker.track_db_query(random.uniform(1, 50))
            
            # Template
            if not path.startswith('/api/') and not path.startswith('/static/'):
                time.sleep(random.uniform(0.02, 0.05))
                tracker.track_component('templates', ComponentState.ACTIVE)
            
            # Response
            time.sleep(random.uniform(0.02, 0.05))
            
            # Status code
            status = random.choices(
                [200, 201, 301, 400, 404, 500],
                weights=[70, 10, 5, 5, 8, 2]
            )[0]
            
            duration = random.uniform(50, 500)
            
            tracker.track_request_end(
                request_id=f"demo-{request_id}",
                status_code=status,
                duration_ms=duration
            )
            
            # Sonraki request için bekle
            time.sleep(random.uniform(0.3, 2.0))
