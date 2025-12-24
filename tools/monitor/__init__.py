# -*- coding: utf-8 -*-
"""
GlobalMain Monitor Package
===========================

Tüm monitoring özelliklerini içeren merkezi paket.

Modüller:
---------
- unified_monitor: Kapsamlı birleşik monitor (TÜM ÖZELLİKLER)
- middleware: Django request tracking middleware
- live_monitor: Request akış izleme (eski, unified'a taşındı)
- system_monitor: Sistem izleme (eski, unified'a taşındı)

Kullanım:
---------
Terminal'de:
    python tools/monitor/unified_monitor.py
    make monitor

Django management command:
    python manage.py monitor          # Full monitor
    python manage.py monitor --simple # Basit mod

Python'dan:
    from tools.monitor import UnifiedMonitor
    monitor = UnifiedMonitor()
    monitor.run()

Middleware (settings.py):
    MIDDLEWARE = [
        ...
        'tools.monitor.middleware.MonitorMiddleware',
        'tools.monitor.middleware.DatabaseQueryMonitorMiddleware',
        ...
    ]
"""

# =============================================================================
# UNIFIED MONITOR (Ana Monitor)
# =============================================================================

def get_unified_monitor():
    """Unified monitor class'ını al."""
    from .unified_monitor import UnifiedMonitor
    return UnifiedMonitor


def get_simple_monitor():
    """Simple monitor class'ını al."""
    from .unified_monitor import SimpleMonitor
    return SimpleMonitor


# =============================================================================
# LEGACY SUPPORT (Eski API'ler - geriye uyumluluk için)
# =============================================================================

def get_live_monitor():
    """Legacy: LiveMonitor class'ını al."""
    from .live_monitor import LiveMonitor
    return LiveMonitor


def get_request_tracker():
    """Request tracker singleton'ını al."""
    from .live_monitor import RequestTracker
    return RequestTracker


def get_system_monitor():
    """Legacy: SystemMonitor class'ını al."""
    from .system_monitor import SystemMonitor
    return SystemMonitor


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_monitor(simple: bool = False, refresh_rate: float = 1.0):
    """Monitor'u hızlıca çalıştır."""
    if simple:
        monitor_cls = get_simple_monitor()
    else:
        monitor_cls = get_unified_monitor()
    
    monitor = monitor_cls()
    monitor.run(refresh_rate=refresh_rate)


def create_monitor(simple: bool = False):
    """Monitor instance oluştur."""
    if simple:
        return get_simple_monitor()()
    return get_unified_monitor()()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Ana API
    'get_unified_monitor',
    'get_simple_monitor',
    'run_monitor',
    'create_monitor',
    
    # Legacy
    'get_live_monitor',
    'get_request_tracker',
    'get_system_monitor',
]

__version__ = '2.0.0'
