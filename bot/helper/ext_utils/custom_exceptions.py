# Custom Exception Classes
"""
Provides specific exception types for better error handling and categorization.

Using specific exceptions makes it easier to:
1. Handle different error types appropriately
2. Log errors with correct severity
3. Provide meaningful error messages to users
4. Debug issues more efficiently

Usage:
    from bot.helper.ext_utils.custom_exceptions import DownloadException
    
    if download_failed:
        raise DownloadException("Failed to download file: timeout")
"""

__all__ = [
    "BotException",
    "DownloadException",
    "UploadException",
    "MetadataException",
    "CacheException",
    "DatabaseException",
    "ValidationException",
    "LimitExceededException",
    "TaskCancelledException",
    "ConfigurationException",
]

class BotException(Exception):
    """Base exception for all bot errors"""
    pass


class DownloadException(BotException):
    """Raised when download fails"""
    pass


class UploadException(BotException):
    """Raised when upload fails"""
    pass


class MetadataException(BotException):
    """Raised when metadata extraction fails"""
    pass


class CacheException(BotException):
    """Raised when cache operations fail"""
    pass


class DatabaseException(BotException):
    """Raised when database operations fail"""
    pass


class ValidationException(BotException):
    """Raised when input validation fails"""
    pass


class LimitExceededException(BotException):
    """Raised when size/count limits are exceeded"""
    pass


class TaskCancelledException(BotException):
    """Raised when a task is cancelled"""
    pass


class ConfigurationException(BotException):
    """Raised when configuration is invalid"""
    pass
