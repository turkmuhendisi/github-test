"""
Logging Context Managers
========================

Log context için context manager'lar.
"""

import logging
import time
from typing import Optional, Any, Dict
from contextlib import contextmanager


class LogContext:
    """
    Logging context sınıfı.
    
    Log mesajlarına otomatik context bilgisi ekler.
    
    Kullanım:
    --------
    with LogContext(user_id=123, action='purchase') as ctx:
        ctx.log_info("Processing purchase")
        # İşlemler...
        ctx.add_data('item_id', 456)
        ctx.log_info("Purchase completed")
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        logger_name: str = 'django',
        **context
    ):
        self.logger = logger or logging.getLogger(logger_name)
        self.context = context
        self.start_time = None
        self.extra_data: Dict[str, Any] = {}
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.perf_counter() - self.start_time) * 1000
        
        if exc_type:
            self.log_error(
                f"Context failed after {duration:.2f}ms: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        
        return False
    
    def add_data(self, key: str, value: Any):
        """Context'e veri ekle."""
        self.extra_data[key] = value
    
    def _build_extra(self) -> dict:
        """Extra dict oluştur."""
        return {**self.context, **self.extra_data}
    
    def _format_message(self, message: str) -> str:
        """Mesajı context ile formatla."""
        context_str = " ".join(f"{k}={v}" for k, v in self.context.items())
        if context_str:
            return f"[{context_str}] {message}"
        return message
    
    def log(self, level: int, message: str, **kwargs):
        """Log mesajı."""
        self.logger.log(
            level,
            self._format_message(message),
            extra=self._build_extra(),
            **kwargs
        )
    
    def log_debug(self, message: str, **kwargs):
        """DEBUG log."""
        self.log(logging.DEBUG, message, **kwargs)
    
    def log_info(self, message: str, **kwargs):
        """INFO log."""
        self.log(logging.INFO, message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """WARNING log."""
        self.log(logging.WARNING, message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """ERROR log."""
        self.log(logging.ERROR, message, **kwargs)
    
    def log_exception(self, message: str, **kwargs):
        """Exception log (traceback ile)."""
        self.logger.exception(
            self._format_message(message),
            extra=self._build_extra(),
            **kwargs
        )


@contextmanager
def log_context(
    operation: str = '',
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    log_start: bool = True,
    log_end: bool = True,
    **context
):
    """
    Basit log context manager.
    
    Kullanım:
    --------
    with log_context('user_creation', user_id=123):
        # İşlemler...
        pass
    
    with log_context('api_call', endpoint='/users', log_start=False):
        response = api.get_users()
    """
    _logger = logger or logging.getLogger('django')
    start = time.perf_counter()
    
    context_str = " ".join(f"{k}={v}" for k, v in context.items())
    prefix = f"[{context_str}] " if context_str else ""
    
    if log_start and operation:
        _logger.log(level, f"{prefix}Starting {operation}")
    
    try:
        yield
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        _logger.error(
            f"{prefix}{operation} failed after {duration:.2f}ms: {e}",
            extra=context,
            exc_info=True
        )
        raise
    else:
        if log_end and operation:
            duration = (time.perf_counter() - start) * 1000
            _logger.log(
                level,
                f"{prefix}{operation} completed in {duration:.2f}ms",
                extra={**context, 'duration_ms': duration}
            )

