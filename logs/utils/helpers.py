"""
Logging Helper Functions
========================

Kolay kullanım için yardımcı fonksiyonlar.
"""

import logging
from typing import Optional, Any


_loggers = {}


def get_logger(name: str = 'django') -> logging.Logger:
    """
    Named logger döndürür (cached).
    
    Args:
        name: Logger adı
    
    Returns:
        logging.Logger
    
    Kullanım:
    --------
    logger = get_logger('myapp.module')
    logger.info("Message")
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


def log_info(
    message: str,
    logger_name: str = 'django',
    **extra
):
    """
    INFO log helper.
    
    Kullanım:
    --------
    log_info("User logged in", user_id=123)
    """
    logger = get_logger(logger_name)
    logger.info(message, extra=extra)


def log_warning(
    message: str,
    logger_name: str = 'django',
    **extra
):
    """
    WARNING log helper.
    
    Kullanım:
    --------
    log_warning("Rate limit approaching", current=90, max=100)
    """
    logger = get_logger(logger_name)
    logger.warning(message, extra=extra)


def log_error(
    message: str,
    logger_name: str = 'django',
    exc_info: bool = False,
    **extra
):
    """
    ERROR log helper.
    
    Kullanım:
    --------
    log_error("Payment failed", order_id=456, exc_info=True)
    """
    logger = get_logger(logger_name)
    logger.error(message, exc_info=exc_info, extra=extra)


def log_debug(
    message: str,
    logger_name: str = 'django',
    **extra
):
    """
    DEBUG log helper.
    
    Kullanım:
    --------
    log_debug("Processing item", item_id=789, status='pending')
    """
    logger = get_logger(logger_name)
    logger.debug(message, extra=extra)


def log_exception(
    message: str,
    logger_name: str = 'django',
    **extra
):
    """
    Exception log helper (traceback ile).
    
    Kullanım:
    --------
    try:
        risky_operation()
    except Exception:
        log_exception("Operation failed", operation='risky')
    """
    logger = get_logger(logger_name)
    logger.exception(message, extra=extra)


def log_with_request(
    message: str,
    request,
    level: int = logging.INFO,
    logger_name: str = 'django.request',
    **extra
):
    """
    Request bilgisi ile log.
    
    Kullanım:
    --------
    log_with_request("API call received", request, endpoint='/users')
    """
    logger = get_logger(logger_name)
    
    # Request bilgilerini ekle
    extra.update({
        'path': request.path,
        'method': request.method,
        'user': str(request.user) if hasattr(request, 'user') else 'anonymous',
    })
    
    # IP adresi
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        extra['ip'] = x_forwarded_for.split(',')[0].strip()
    else:
        extra['ip'] = request.META.get('REMOTE_ADDR', '')
    
    logger.log(level, message, extra=extra)


def structured_log(
    event: str,
    logger_name: str = 'django',
    level: int = logging.INFO,
    **data
):
    """
    Structured logging.
    
    Kullanım:
    --------
    structured_log(
        'user.created',
        user_id=123,
        email='user@example.com',
        source='registration'
    )
    """
    logger = get_logger(logger_name)
    
    # Event adını mesaja ekle
    message = f"[{event}] {' '.join(f'{k}={v}' for k, v in data.items())}"
    
    logger.log(level, message, extra={'event': event, **data})

