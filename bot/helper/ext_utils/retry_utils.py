# Retry Decorator with Exponential Backoff
"""
Provides automatic retry logic with exponential backoff for failed operations.

This module helps handle transient failures by automatically retrying
operations with increasing wait times between attempts.

Usage:
    from bot.helper.ext_utils.retry_utils import async_retry
    
    @async_retry(max_attempts=5, exceptions=(HTTPError,))
    async def fetch_data():
        # This will retry up to 5 times on HTTPError
        return await http_client.get(url)
"""

import asyncio
from functools import wraps
from typing import Callable, Type, Tuple
from bot import LOGGER

__all__ = ["async_retry", "sync_retry"]


def async_retry(
    max_attempts: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    log_errors: bool = True,
):
    """
    Decorator for async functions with exponential backoff retry
    
    Args:
        max_attempts: Maximum number of retry attempts
        exceptions: Tuple of exception types to catch
        backoff_factor: Multiplier for wait time between retries
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        log_errors: Whether to log retry attempts
    
    Usage:
        @async_retry(max_attempts=5, exceptions=(HTTPError, TimeoutError))
        async def fetch_data():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            wait_time = min_wait
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        if log_errors:
                            LOGGER.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                        raise
                    
                    if log_errors:
                        LOGGER.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                    
                    await asyncio.sleep(wait_time)
                    wait_time = min(wait_time * backoff_factor, max_wait)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def sync_retry(
    max_attempts: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    log_errors: bool = True,
):
    """
    Decorator for sync functions with exponential backoff retry
    
    Same args as async_retry but for synchronous functions
    """
    import time
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            wait_time = min_wait
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        if log_errors:
                            LOGGER.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                        raise
                    
                    if log_errors:
                        LOGGER.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                    
                    time.sleep(wait_time)
                    wait_time = min(wait_time * backoff_factor, max_wait)
            
            raise last_exception
        
        return wrapper
    return decorator
