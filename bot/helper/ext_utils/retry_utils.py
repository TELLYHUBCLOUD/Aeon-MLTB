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
