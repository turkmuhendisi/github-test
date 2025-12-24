"""
Logging Decorators
==================

Fonksiyon ve method'lar için logging decorator'ları.
"""

import functools
import time
import logging
import traceback
from typing import Callable, Optional, Any


def log_execution_time(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    message: str = None,
    threshold_ms: float = 0,
):
    """
    Fonksiyon çalışma süresini loglar.
    
    Args:
        logger: Kullanılacak logger (default: fonksiyon adından)
        level: Log seviyesi (default: INFO)
        message: Özel mesaj template'i
        threshold_ms: Sadece bu sürenin üzerindeyse logla
    
    Kullanım:
    --------
    @log_execution_time()
    def slow_function():
        ...
    
    @log_execution_time(threshold_ms=100, level=logging.WARNING)
    def should_be_fast():
        ...
    
    @log_execution_time(message="API call to {func_name} took {duration:.2f}ms")
    def api_call():
        ...
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = (time.perf_counter() - start) * 1000
                
                if duration >= threshold_ms:
                    msg = message or "{func_name} executed in {duration:.2f}ms"
                    logger.log(
                        level,
                        msg.format(
                            func_name=func.__name__,
                            duration=duration,
                            module=func.__module__,
                        ),
                        extra={'duration_ms': duration}
                    )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = (time.perf_counter() - start) * 1000
                
                if duration >= threshold_ms:
                    msg = message or "{func_name} executed in {duration:.2f}ms"
                    logger.log(
                        level,
                        msg.format(
                            func_name=func.__name__,
                            duration=duration,
                            module=func.__module__,
                        ),
                        extra={'duration_ms': duration}
                    )
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


def log_errors(
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    reraise: bool = True,
    message: str = None,
    exc_info: bool = True,
):
    """
    Fonksiyon hatalarını loglar.
    
    Args:
        logger: Kullanılacak logger
        level: Log seviyesi (default: ERROR)
        reraise: Hatayı tekrar fırlat (default: True)
        message: Özel mesaj template'i
        exc_info: Traceback ekle (default: True)
    
    Kullanım:
    --------
    @log_errors()
    def risky_function():
        ...
    
    @log_errors(reraise=False)
    def safe_function():
        # Hata olsa bile devam et
        ...
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                msg = message or "Error in {func_name}: {error}"
                logger.log(
                    level,
                    msg.format(
                        func_name=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                    ),
                    exc_info=exc_info,
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'error_type': type(e).__name__,
                    }
                )
                
                if reraise:
                    raise
                return None
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                msg = message or "Error in {func_name}: {error}"
                logger.log(
                    level,
                    msg.format(
                        func_name=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                    ),
                    exc_info=exc_info,
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'error_type': type(e).__name__,
                    }
                )
                
                if reraise:
                    raise
                return None
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


def log_function_call(
    logger: Optional[logging.Logger] = None,
    level: int = logging.DEBUG,
    log_args: bool = True,
    log_result: bool = False,
    max_arg_length: int = 100,
):
    """
    Fonksiyon çağrılarını detaylı loglar.
    
    Args:
        logger: Kullanılacak logger
        level: Log seviyesi (default: DEBUG)
        log_args: Argümanları logla
        log_result: Sonucu logla
        max_arg_length: Maksimum argüman uzunluğu
    
    Kullanım:
    --------
    @log_function_call()
    def process_data(user_id, data):
        ...
    
    @log_function_call(log_result=True)
    def calculate_something():
        return 42
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Giriş logu
            call_info = f"{func.__name__}("
            
            if log_args:
                arg_strs = []
                for i, arg in enumerate(args):
                    arg_str = repr(arg)
                    if len(arg_str) > max_arg_length:
                        arg_str = arg_str[:max_arg_length] + '...'
                    arg_strs.append(arg_str)
                
                for key, value in kwargs.items():
                    val_str = repr(value)
                    if len(val_str) > max_arg_length:
                        val_str = val_str[:max_arg_length] + '...'
                    arg_strs.append(f"{key}={val_str}")
                
                call_info += ", ".join(arg_strs)
            
            call_info += ")"
            
            logger.log(level, f"Calling {call_info}")
            
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            
            # Çıkış logu
            if log_result:
                result_str = repr(result)
                if len(result_str) > max_arg_length:
                    result_str = result_str[:max_arg_length] + '...'
                logger.log(level, f"{func.__name__} returned {result_str} in {duration:.2f}ms")
            else:
                logger.log(level, f"{func.__name__} completed in {duration:.2f}ms")
            
            return result
        
        return wrapper
    
    return decorator

