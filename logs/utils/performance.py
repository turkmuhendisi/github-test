"""
Performance Tracking
====================

Performans izleme ve raporlama.
"""

import time
import logging
import functools
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from contextlib import contextmanager


logger = logging.getLogger('django')


@dataclass
class TimingRecord:
    """Zamanlama kaydı."""
    name: str
    duration_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceTracker:
    """
    Performans izleme sınıfı.
    
    Kullanım:
    --------
    tracker = PerformanceTracker('api_request')
    
    with tracker.track('database_query'):
        result = db.query()
    
    with tracker.track('serialization'):
        data = serialize(result)
    
    tracker.log_summary()  # Toplam süre ve breakdown
    """
    
    def __init__(self, name: str = 'operation'):
        self.name = name
        self.start_time = time.perf_counter()
        self.timings: List[TimingRecord] = []
        self._current_section: Optional[str] = None
        self._section_start: Optional[float] = None
    
    @contextmanager
    def track(self, section: str, **metadata):
        """
        Belirli bir bölümü izle.
        
        Args:
            section: Bölüm adı
            **metadata: Ek metadata
        """
        start = time.perf_counter()
        self._current_section = section
        self._section_start = start
        
        try:
            yield
        finally:
            duration = (time.perf_counter() - start) * 1000
            self.timings.append(TimingRecord(
                name=section,
                duration_ms=duration,
                timestamp=start,
                metadata=metadata,
            ))
            self._current_section = None
            self._section_start = None
    
    def mark(self, name: str, **metadata):
        """
        Anlık zaman damgası ekle.
        
        Args:
            name: İşaret adı
            **metadata: Ek metadata
        """
        now = time.perf_counter()
        duration = (now - self.start_time) * 1000
        self.timings.append(TimingRecord(
            name=name,
            duration_ms=duration,
            timestamp=now,
            metadata=metadata,
        ))
    
    @property
    def total_duration(self) -> float:
        """Toplam süre (ms)."""
        return (time.perf_counter() - self.start_time) * 1000
    
    @property
    def breakdown(self) -> Dict[str, float]:
        """Bölüm bazlı süre dağılımı."""
        result = defaultdict(float)
        for timing in self.timings:
            result[timing.name] += timing.duration_ms
        return dict(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """Özet bilgi döndür."""
        total = self.total_duration
        breakdown = self.breakdown
        
        return {
            'name': self.name,
            'total_ms': round(total, 2),
            'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
            'tracked_ms': round(sum(breakdown.values()), 2),
            'untracked_ms': round(total - sum(breakdown.values()), 2),
            'section_count': len(self.timings),
        }
    
    def log_summary(self, level: int = logging.INFO):
        """Özeti logla."""
        summary = self.get_summary()
        
        parts = [f"{self.name}: {summary['total_ms']:.2f}ms"]
        
        for section, duration in summary['breakdown'].items():
            pct = (duration / summary['total_ms'] * 100) if summary['total_ms'] > 0 else 0
            parts.append(f"  - {section}: {duration:.2f}ms ({pct:.1f}%)")
        
        if summary['untracked_ms'] > 1:
            pct = (summary['untracked_ms'] / summary['total_ms'] * 100) if summary['total_ms'] > 0 else 0
            parts.append(f"  - (untracked): {summary['untracked_ms']:.2f}ms ({pct:.1f}%)")
        
        logger.log(level, "\n".join(parts), extra=summary)


def track_performance(
    name: str = None,
    log_level: int = logging.INFO,
    threshold_ms: float = 0,
):
    """
    Fonksiyon performansını izle ve logla.
    
    Args:
        name: İzleme adı (default: fonksiyon adı)
        log_level: Log seviyesi
        threshold_ms: Sadece bu sürenin üzerindeyse logla
    
    Kullanım:
    --------
    @track_performance(threshold_ms=100)
    def slow_function():
        with PerformanceTracker.current().track('step1'):
            ...
        with PerformanceTracker.current().track('step2'):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracker = PerformanceTracker(name or func.__name__)
            
            # Tracker'ı thread-local'e koy
            _tracker_stack.append(tracker)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                _tracker_stack.pop()
                
                if tracker.total_duration >= threshold_ms:
                    tracker.log_summary(log_level)
        
        return wrapper
    return decorator


# Thread-local tracker stack
import threading
_tracker_local = threading.local()


def _get_tracker_stack() -> List[PerformanceTracker]:
    if not hasattr(_tracker_local, 'stack'):
        _tracker_local.stack = []
    return _tracker_local.stack


_tracker_stack = property(lambda self: _get_tracker_stack())


def get_current_tracker() -> Optional[PerformanceTracker]:
    """Mevcut tracker'ı döndür (varsa)."""
    stack = _get_tracker_stack()
    return stack[-1] if stack else None


@contextmanager
def track_section(name: str, **metadata):
    """
    Mevcut tracker'da bölüm izle.
    
    Kullanım:
    --------
    @track_performance()
    def my_function():
        with track_section('database'):
            db.query()
    """
    tracker = get_current_tracker()
    
    if tracker:
        with tracker.track(name, **metadata):
            yield
    else:
        # Tracker yoksa sadece çalıştır
        yield

