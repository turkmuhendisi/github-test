"""
Log Utils App
=============

Gelişmiş logging utilities.

Özellikler:
----------
- @log_execution_time decorator
- @log_errors decorator
- log_context context manager
- Structured logging helpers
- Performance tracking
"""

from .decorators import (
    log_execution_time,
    log_errors,
    log_function_call,
)

from .context import (
    log_context,
    LogContext,
)

from .helpers import (
    get_logger,
    log_info,
    log_warning,
    log_error,
    log_debug,
    log_exception,
)

from .performance import (
    PerformanceTracker,
    track_performance,
)

__all__ = [
    # Decorators
    'log_execution_time',
    'log_errors',
    'log_function_call',
    # Context
    'log_context',
    'LogContext',
    # Helpers
    'get_logger',
    'log_info',
    'log_warning',
    'log_error',
    'log_debug',
    'log_exception',
    # Performance
    'PerformanceTracker',
    'track_performance',
]

default_app_config = 'logs.utils.apps.UtilsConfig'

