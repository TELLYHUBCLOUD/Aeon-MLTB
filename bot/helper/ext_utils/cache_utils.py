# Cache Utility Module
"""
Provides in-memory caching with TTL (Time-To-Live) support.

This module implements a simple but effective caching layer to reduce
database queries and expensive operations like metadata extraction.

Usage:
    from bot.helper.ext_utils.cache_utils import user_settings_cache
    
    # Get cached value
    settings = user_settings_cache.get("user_123")
    
    # Set value with auto-expiration
    user_settings_cache.set("user_123", {"name": "John"})
"""

from time import time
from typing import Any, Optional

__all__ = [
    "SimpleCache",
    "user_settings_cache",
    "metadata_cache",
    "config_cache",
    "get_user_settings_cached",
    "invalidate_user_cache",
    "get_metadata_cached",
]

class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, ttl: int = 300):
        """
        Initialize cache with time-to-live
        
        Args:
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self._cache = {}
        self._timestamps = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        if key not in self._cache:
            return None
        
        # Check if expired
        if time() - self._timestamps[key] > self._ttl:
            self.delete(key)
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value
        self._timestamps[key] = time()
    
    def delete(self, key: str) -> None:
        """
        Delete key from cache
        
        Args:
            key: Cache key
        """
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
        self._timestamps.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return self.get(key) is not None


# Global cache instances
user_settings_cache = SimpleCache(ttl=600)  # 10 minutes
metadata_cache = SimpleCache(ttl=1800)  # 30 minutes
config_cache = SimpleCache(ttl=3600)  # 1 hour


def get_user_settings_cached(user_id: int, db_fetch_func):
    """
    Get user settings with caching
    
    Args:
        user_id: User ID
        db_fetch_func: Function to fetch from database if not cached
        
    Returns:
        User settings dict
    """
    cache_key = f"user_{user_id}"
    cached = user_settings_cache.get(cache_key)
    
    if cached is not None:
        return cached
    
    # Fetch from database
    settings = db_fetch_func(user_id)
    user_settings_cache.set(cache_key, settings)
    return settings


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate user settings cache when updated"""
    cache_key = f"user_{user_id}"
    user_settings_cache.delete(cache_key)


def get_metadata_cached(file_path: str, metadata_func):
    """
    Get file metadata with caching
    
    Args:
        file_path: Path to media file
        metadata_func: Function to extract metadata
        
    Returns:
        Metadata dict
    """
    cache_key = f"meta_{file_path}"
    cached = metadata_cache.get(cache_key)
    
    if cached is not None:
        return cached
    
    # Extract metadata
    metadata = metadata_func(file_path)
    metadata_cache.set(cache_key, metadata)
    return metadata
