"""
Bot Constants Module
Centralized constants to avoid magic numbers throughout the codebase.

Usage:
    from bot.helper.ext_utils.constants import MAX_FILE_SIZE, QUALITY_OPTIONS
"""

__all__ = [
    # File Size Limits
    "MAX_FILE_SIZE",
    "MAX_SPLIT_SIZE",
    # Time Intervals
    "DEFAULT_TIMEOUT",
    "METADATA_FETCH_TIMEOUT",
    "UPLOAD_RETRY_DELAY",
    "STATUS_UPDATE_INTERVAL",
    # Download Limits
    "MAX_CONCURRENT_DOWNLOADS",
    "MAX_CONCURRENT_UPLOADS",
    "CHUNK_SIZE_SMALL",
    "CHUNK_SIZE_LARGE",
    # FFmpeg Settings
    "FFMPEG_THREADS_AUTO",
    "DEFAULT_VIDEO_CODEC",
    "DEFAULT_AUDIO_CODEC",
    "DEFAULT_SUBTITLE_CODEC",
    # Quality Presets
    "QUALITY_ORIGINAL",
    "QUALITY_1080P",
    "QUALITY_720P",
    "QUALITY_480P",
    "QUALITY_360P",
    "QUALITY_240P",
    "QUALITY_144P",
    "QUALITY_OPTIONS",
    # Video Scale Settings
    "SCALE_1080P",
    "SCALE_720P",
    "SCALE_480P",
    "SCALE_360P",
    "SCALE_240P",
    "SCALE_144P",
    # Retry Settings
    "MAX_RETRY_ATTEMPTS",
    "RETRY_MIN_WAIT",
    "RETRY_MAX_WAIT",
    "RETRY_MULTIPLIER",
    # File Operations
    "MAX_FILENAME_LENGTH",
    "TEMP_DIR_PREFIX",
    # Media Group Settings
    "MEDIA_GROUP_SIZE",
    # Logging
    "LOG_MAX_PATH_LENGTH",
    # Default Values
    "DEFAULT_QUALITY",
    "DEFAULT_REMOVE_AUDIO",
    "DEFAULT_REMOVE_SUBS",
]

# ==================== File Size Limits ====================
# All sizes in bytes

MAX_FILE_SIZE = 2097152000  # 2GB - Telegram file size limit
MAX_SPLIT_SIZE = 2097152000  # 2GB - Maximum size for file splitting

# ==================== Time Intervals ====================
# All intervals in seconds

DEFAULT_TIMEOUT = 300  # 5 minutes - Default timeout for operations
METADATA_FETCH_TIMEOUT = 60  # 1 minute - Timeout for metadata extraction
UPLOAD_RETRY_DELAY = 2  # Delay between upload retry attempts
STATUS_UPDATE_INTERVAL = 3  # Interval for status message updates

# Download Limits
MAX_CONCURRENT_DOWNLOADS = 10
MAX_CONCURRENT_UPLOADS = 5
CHUNK_SIZE_SMALL = 5  # 5 chunks for metadata
CHUNK_SIZE_LARGE = 100  # 100 chunks for full download

# FFmpeg Settings
FFMPEG_THREADS_AUTO = -1  # Auto-detect
DEFAULT_VIDEO_CODEC = "libx264"
DEFAULT_AUDIO_CODEC = "copy"
DEFAULT_SUBTITLE_CODEC = "copy"

# Quality Presets
QUALITY_ORIGINAL = "Original"
QUALITY_1080P = "1080p"
QUALITY_720P = "720p"  
QUALITY_480P = "480p"
QUALITY_360P = "360p"
QUALITY_240P = "240p"
QUALITY_144P = "144p"

QUALITY_OPTIONS = [
    QUALITY_ORIGINAL,
    QUALITY_1080P,
    QUALITY_720P,
    QUALITY_480P,
    QUALITY_360P,
    QUALITY_240P,
    QUALITY_144P,
]

# Video Scale Settings
SCALE_1080P = "scale=-2:1080"
SCALE_720P = "scale=-2:720"
SCALE_480P = "scale=-2:480"
SCALE_360P = "scale=-2:360"
SCALE_240P = "scale=-2:240"
SCALE_144P = "scale=-2:144"

# Retry Settings
MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 4  # seconds
RETRY_MAX_WAIT = 8  # seconds
RETRY_MULTIPLIER = 2

# File Operations
MAX_FILENAME_LENGTH = 200
TEMP_DIR_PREFIX = "Metadata/"

# Media Group Settings
MEDIA_GROUP_SIZE = 10  # Max messages in group

# Logging
LOG_MAX_PATH_LENGTH = 100  # Truncate long paths in logs

# Default Values
DEFAULT_QUALITY = QUALITY_ORIGINAL
DEFAULT_REMOVE_AUDIO = False
DEFAULT_REMOVE_SUBS = False
