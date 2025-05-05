# REQUIRED CONFIG
BOT_TOKEN = ""  # Get this from @BotFather
OWNER_ID = 0  # Your Telegram User ID (not username) as an integer
TELEGRAM_API = 0  # Get this from my.telegram.org
TELEGRAM_HASH = ""  # Get this from my.telegram.org

# SEMI-REQUIRED, WE SUGGEST TO FILL IT FROM MONGODB
DATABASE_URL = ""  # MongoDB URI for storing user data and preferences

# OPTIONAL CONFIG
TG_PROXY = {}  # Proxy for Telegram connection, format: {'addr': 'ip:port', 'username': 'username', 'password': 'password'}
USER_SESSION_STRING = ""  # Pyrogram user session string for mirror/leech authentication
DOWNLOAD_DIR = "/usr/src/app/downloads/"  # Directory where downloads will be stored
CMD_SUFFIX = ""  # Command suffix to distinguish commands, e.g. "1" would make commands like /mirror1
AUTHORIZED_CHATS = ""  # List of authorized chat IDs where the bot can be used, separated by space
SUDO_USERS = ""  # List of sudo user IDs who can use admin commands, separated by space
DEFAULT_UPLOAD = "rc"  # Default upload destination: 'rc' for rclone or 'gd' for Google Drive
FILELION_API = ""  # FileLion API key for direct links
STREAMWISH_API = ""  # StreamWish API key for direct links
EXCLUDED_EXTENSIONS = ""  # File extensions to exclude from processing, separated by space
INCOMPLETE_TASK_NOTIFIER = False  # Notify about incomplete tasks on bot restart
YT_DLP_OPTIONS = ""  # Additional yt-dlp options as a JSON string
USE_SERVICE_ACCOUNTS = False  # Whether to use service accounts for Google Drive
NAME_SUBSTITUTE = ""  # Regex pattern to substitute in filenames
FFMPEG_CMDS = {}  # Custom FFmpeg commands for different file types
UPLOAD_PATHS = {}  # Custom upload paths for different file types
USER_COOKIES = ""  # Path to cookies file for yt-dlp and other downloaders
IMDB_TEMPLATE = """<b>🎬 Title:</b> <code>{title}</code> [{year}]
 <b>⭐ Rating:</b> <i>{rating}</i>
 <b>🎭 Genre:</b> {genres}
 <b>📅 Released:</b> <a href=\"{url_releaseinfo}\">{release_date}</a>
 <b>🎙️ Languages:</b> {languages}
 <b>🌍 Country:</b> {countries}
 <b>🎬 Type:</b> {kind}

 <b>📖 Story Line:</b>
 <blockquote>{plot}</blockquote>

 <b>🔗 IMDb URL:</b> <a href=\"{url}\">{url}</a>
 <b>👥 Cast:</b> <a href=\"{url_cast}\">{cast}</a>

 <b>👨‍💼 Director:</b> {director}
 <b>✍️ Writer:</b> {writer}
 <b>🎵 Music:</b> {composer}
 <b>🎥 Cinematography:</b> {cinematographer}

 <b>⏱️ Runtime:</b> {runtime} minutes
 <b>🏆 Awards:</b> {certificates}

 <i>Powered by IMDb</i>"""  # Custom template for IMDB results formatting. If empty, the default template below will be used:
EQUAL_SPLITS = False  # Create equal-sized parts when splitting files
LEECH_SUFFIX = ""  # Suffix to add to leeched files
LEECH_FONT = ""  # Font to use for leech captions
LEECH_FILENAME = ""  # Custom filename template for leeched files
MEDIA_STORE = False  # Enable media store for faster thumbnail generation
LOGIN_PASS = ""  # Password for web login
MUSIC_SEARCH_CHATS = []  # List of chat IDs where music search is enabled

# INKYPINKY
DELETE_LINKS = False  # Delete links after download
FSUB_IDS = ""  # Force subscribe channel IDs, separated by space
TOKEN_TIMEOUT = 0  # Token timeout in seconds (0 = no timeout)
PAID_CHANNEL_ID = 0  # Paid channel ID for premium features
PAID_CHANNEL_LINK = ""  # Invite link for paid channel
SET_COMMANDS = True  # Set bot commands in Telegram UI
METADATA_KEY = ""  # Default metadata key for files
WATERMARK_KEY = ""  # Default watermark text
LOG_CHAT_ID = 0  # Chat ID where logs will be sent
LEECH_FILENAME_CAPTION = ""  # Caption template for leeched files
HYDRA_IP = ""  # Hydra IP address for direct links
HYDRA_API_KEY = ""  # Hydra API key for direct links
INSTADL_API = ""  # InstaDL API key for Instagram downloads

# GDrive Tools
GDRIVE_ID = ""  # Google Drive folder/TeamDrive ID where files will be uploaded
IS_TEAM_DRIVE = False  # Whether the GDRIVE_ID is a TeamDrive
STOP_DUPLICATE = False  # Skip uploading files that are already in the drive
INDEX_URL = ""  # Index URL for Google Drive

# Rclone
RCLONE_PATH = ""  # Path to rclone.conf file
RCLONE_FLAGS = ""  # Additional rclone flags
RCLONE_SERVE_URL = ""  # URL for rclone serve
RCLONE_SERVE_PORT = 0  # Port for rclone serve (0 to disable)
RCLONE_SERVE_USER = ""  # Username for rclone serve
RCLONE_SERVE_PASS = ""  # Password for rclone serve
RCLONE_CONFIG = ""  # Rclone config as a string (alternative to RCLONE_PATH)

# JDownloader
JD_EMAIL = ""  # JDownloader email/username
JD_PASS = ""  # JDownloader password

# Mega credentials
MEGA_EMAIL = ""  # Mega.nz account email
MEGA_PASSWORD = ""  # Mega.nz account password

# Sabnzbd
USENET_SERVERS = [  # List of Usenet servers for NZB downloads
    {
        "name": "main",  # Server name
        "host": "",  # Server hostname or IP
        "port": 563,  # Server port
        "timeout": 60,  # Connection timeout in seconds
        "username": "",  # Server username
        "password": "",  # Server password
        "connections": 8,  # Number of connections to use
        "ssl": 1,  # Use SSL: 0=no, 1=yes
        "ssl_verify": 2,  # SSL verification: 0=no, 1=verify host, 2=verify host and peer
        "ssl_ciphers": "",  # SSL ciphers to use
        "enable": 1,  # Enable server: 0=no, 1=yes
        "required": 0,  # Server is required: 0=no, 1=yes
        "optional": 0,  # Server is optional: 0=no, 1=yes
        "retention": 0,  # Server retention in days (0=unlimited)
        "send_group": 0,  # Send group command: 0=no, 1=yes
        "priority": 0,  # Server priority (0=highest)
    },
]

# Update
UPSTREAM_REPO = "https://github.com/AeonOrg/Aeon-MLTB"  # Repository URL for updates
UPSTREAM_BRANCH = "main"  # Branch to use for updates

# Leech
LEECH_SPLIT_SIZE = 0  # Size of split files in bytes, 0 means no split
AS_DOCUMENT = False  # Send files as documents instead of media
MEDIA_GROUP = False  # Group media files together when sending
USER_TRANSMISSION = False  # Use transmission for torrents
HYBRID_LEECH = False  # Enable hybrid leech (both document and media)
LEECH_FILENAME_PREFIX = ""  # Prefix to add to leeched filenames
LEECH_DUMP_CHAT = ""  # Chat ID where leeched files will be sent
THUMBNAIL_LAYOUT = ""  # Layout for thumbnails: empty, top, bottom, or custom

# qBittorrent/Aria2c
TORRENT_TIMEOUT = 0  # Timeout for torrent downloads in seconds (0 = no timeout)
BASE_URL = ""  # Base URL for web server
BASE_URL_PORT = 80  # Port for web server (0 to disable)
WEB_PINCODE = False  # Enable pincode protection for web server

# Queueing system
QUEUE_ALL = 0  # Maximum number of concurrent tasks (0 = unlimited)
QUEUE_DOWNLOAD = 0  # Maximum number of concurrent downloads (0 = unlimited)
QUEUE_UPLOAD = 0  # Maximum number of concurrent uploads (0 = unlimited)

# RSS
RSS_DELAY = 600  # Delay between RSS feed checks in seconds
RSS_CHAT = ""  # Chat ID where RSS feed updates will be sent
RSS_SIZE_LIMIT = 0  # Maximum size for RSS downloads in bytes (0 = unlimited)

# Resource Management Settings
PIL_MEMORY_LIMIT = 2048  # Memory limit for PIL image processing in MB

# Auto Restart Settings
AUTO_RESTART_ENABLED = False  # Enable automatic bot restart
AUTO_RESTART_INTERVAL = 24  # Restart interval in hours

# Limits Settings
STORAGE_THRESHOLD = 0  # Storage threshold in GB, bot will stop if free space falls below this
TORRENT_LIMIT = 0  # Maximum size for torrent downloads in GB (0 = unlimited)
DIRECT_LIMIT = 0  # Maximum size for direct link downloads in GB (0 = unlimited)
YTDLP_LIMIT = 0  # Maximum size for YouTube/video downloads in GB (0 = unlimited)
GDRIVE_LIMIT = 0  # Maximum size for Google Drive downloads in GB (0 = unlimited)
CLONE_LIMIT = 0  # Maximum size for clone operations in GB (0 = unlimited)
MEGA_LIMIT = 0  # Maximum size for Mega downloads in GB (0 = unlimited)
LEECH_LIMIT = 0  # Maximum size for leech operations in GB (0 = unlimited)
JD_LIMIT = 0  # Maximum size for JDownloader downloads in GB (0 = unlimited)
NZB_LIMIT = 0  # Maximum size for NZB downloads in GB (0 = unlimited)
PLAYLIST_LIMIT = 0  # Maximum number of videos in a playlist (0 = unlimited)
DAILY_TASK_LIMIT = 0  # Maximum number of tasks per day per user (0 = unlimited)
DAILY_MIRROR_LIMIT = 0  # Maximum mirror size in GB per day per user (0 = unlimited)
DAILY_LEECH_LIMIT = 0  # Maximum leech size in GB per day per user (0 = unlimited)
USER_MAX_TASKS = 0  # Maximum concurrent tasks per user (0 = unlimited)
USER_TIME_INTERVAL = 0  # Minimum time between user tasks in seconds (0 = no delay)

# Extra Modules Settings
ENABLE_EXTRA_MODULES = True  # Enable additional modules and features

# Truecaller API Settings
TRUECALLER_API_URL = ""  # Truecaller API URL for phone number lookup

# AI Settings
DEFAULT_AI_PROVIDER = "mistral"  # Default AI provider for /ask command: mistral, deepseek, chatgpt, gemini

# Mistral AI Settings
MISTRAL_API_KEY = ""  # Mistral AI API key
MISTRAL_API_URL = ""  # Custom Mistral AI API URL (optional)

# DeepSeek AI Settings
DEEPSEEK_API_KEY = ""  # DeepSeek AI API key
DEEPSEEK_API_URL = ""  # Custom DeepSeek AI API URL (optional)

# ChatGPT Settings
CHATGPT_API_KEY = ""  # OpenAI API key for ChatGPT
CHATGPT_API_URL = ""  # Custom ChatGPT API URL (optional)

# Gemini AI Settings
GEMINI_API_KEY = ""  # Google Gemini API key
GEMINI_API_URL = ""  # Custom Gemini API URL (optional)

# Media Tools Settings
MEDIA_TOOLS_ENABLED = True  # Master switch to enable/disable all media tools features
MEDIAINFO_ENABLED = False  # Enable/disable mediainfo command for detailed media information

# Watermark Settings
WATERMARK_ENABLED = False  # Master switch to enable/disable watermark feature
WATERMARK_KEY = ""  # Default watermark text to apply to videos
WATERMARK_POSITION = "none"  # Position of watermark: none, top_left, top_right, bottom_left, bottom_right, center
WATERMARK_SIZE = 0  # Font size for watermark text (0 = auto-size based on video dimensions)
WATERMARK_COLOR = "none"  # Watermark text color: none, white, black, red, green, blue, yellow, etc.
WATERMARK_FONT = "none"  # Font for watermark text: none, Arial.ttf, Roboto, etc. (supports Google Fonts)
WATERMARK_OPACITY = 1.0  # Watermark opacity: 0.0 (transparent) to 1.0 (opaque)
WATERMARK_PRIORITY = 2  # Processing priority in pipeline (lower numbers run earlier)
WATERMARK_THREADING = True  # Use multi-threading for faster watermark processing
WATERMARK_THREAD_NUMBER = 4  # Number of threads for watermark processing
WATERMARK_FAST_MODE = True  # Use faster processing mode (may slightly reduce quality)
WATERMARK_MAINTAIN_QUALITY = True  # Maintain original video quality when adding watermark
WATERMARK_REMOVE_ORIGINAL = True  # Delete original files after successful watermarking

# Audio Watermark Settings
AUDIO_WATERMARK_ENABLED = False  # Enable/disable audio watermarking
AUDIO_WATERMARK_TEXT = ""  # Text for audio watermark (for text-to-speech watermarks)
AUDIO_WATERMARK_VOLUME = 0.0  # Volume level for audio watermark: 0.0 (silent) to 1.0 (full volume)

# Subtitle Watermark Settings
SUBTITLE_WATERMARK_ENABLED = False  # Enable/disable subtitle watermarking
SUBTITLE_WATERMARK_TEXT = ""  # Text for subtitle watermark
SUBTITLE_WATERMARK_STYLE = "none"  # Style for subtitle text: none, normal, bold, italic, bold_italic, underline, strikethrough

# Merge Settings
MERGE_ENABLED = False  # Master switch to enable/disable merge feature
MERGE_PRIORITY = 1  # Processing priority in pipeline (lower numbers run earlier)
MERGE_THREADING = True  # Use multi-threading for faster merge processing
MERGE_THREAD_NUMBER = 4  # Number of threads for merge processing
MERGE_REMOVE_ORIGINAL = True  # Delete original files after successful merge
CONCAT_DEMUXER_ENABLED = True  # Enable FFmpeg concat demuxer method (faster, requires same codecs)
FILTER_COMPLEX_ENABLED = False  # Enable FFmpeg filter_complex method (slower but more compatible)

# Merge Output Formats
MERGE_OUTPUT_FORMAT_VIDEO = "none"  # Output format for merged videos: none, mp4, mkv, avi, etc.
MERGE_OUTPUT_FORMAT_AUDIO = "none"  # Output format for merged audio: none, mp3, m4a, flac, etc.
MERGE_OUTPUT_FORMAT_IMAGE = "none"  # Output format for merged images: none, jpg, png, pdf, etc.
MERGE_OUTPUT_FORMAT_DOCUMENT = "none"  # Output format for merged documents: none, pdf, docx, etc.
MERGE_OUTPUT_FORMAT_SUBTITLE = "none"  # Output format for merged subtitles: none, srt, ass, etc.

# Merge Video Settings
MERGE_VIDEO_CODEC = "none"  # Video codec for merged files: none, copy, libx264, libx265, etc.
MERGE_VIDEO_QUALITY = "none"  # Video quality preset: none, ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
MERGE_VIDEO_PRESET = "none"  # Encoding preset: none, ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
MERGE_VIDEO_CRF = "none"  # Constant Rate Factor for quality (0-51, lower is better quality): none, 18, 23, 28, etc.
MERGE_VIDEO_PIXEL_FORMAT = "none"  # Pixel format: none, yuv420p, yuv444p, etc.
MERGE_VIDEO_TUNE = "none"  # Tune option for specific content: none, film, animation, grain, stillimage, etc.
MERGE_VIDEO_FASTSTART = False  # Enable fast start for web streaming

# Merge Audio Settings
MERGE_AUDIO_CODEC = "none"  # Audio codec for merged files: none, copy, aac, mp3, opus, etc.
MERGE_AUDIO_BITRATE = "none"  # Audio bitrate: none, 128k, 192k, 320k, etc.
MERGE_AUDIO_CHANNELS = "none"  # Number of audio channels: none, 1, 2, etc.
MERGE_AUDIO_SAMPLING = "none"  # Audio sampling rate: none, 44100, 48000, etc.
MERGE_AUDIO_VOLUME = "none"  # Volume adjustment: none, 1.0, 1.5, 0.5, etc.

# Merge Image Settings
MERGE_IMAGE_MODE = "none"  # Image merge mode: none, horizontal, vertical, grid, etc.
MERGE_IMAGE_COLUMNS = "none"  # Number of columns for grid mode: none, 2, 3, 4, etc.
MERGE_IMAGE_QUALITY = 90  # JPEG quality (0-100)
MERGE_IMAGE_DPI = "none"  # Image DPI: none, 72, 96, 300, etc.
MERGE_IMAGE_RESIZE = "none"  # Image resize dimensions: none, 1920x1080, 50%, etc.
MERGE_IMAGE_BACKGROUND = "none"  # Background color for transparent images: none, white, black, etc.

# Merge Subtitle Settings
MERGE_SUBTITLE_ENCODING = "none"  # Character encoding: none, utf-8, utf-16, etc.
MERGE_SUBTITLE_FONT = "none"  # Font for subtitles: none, Arial, Times New Roman, etc.
MERGE_SUBTITLE_FONT_SIZE = "none"  # Font size: none, 12, 16, etc.
MERGE_SUBTITLE_FONT_COLOR = "none"  # Font color: none, white, yellow, etc.
MERGE_SUBTITLE_BACKGROUND = "none"  # Background color: none, black, transparent, etc.

# Merge Document Settings
MERGE_DOCUMENT_PAPER_SIZE = "none"  # Paper size: none, a4, letter, etc.
MERGE_DOCUMENT_ORIENTATION = "none"  # Page orientation: none, portrait, landscape
MERGE_DOCUMENT_MARGIN = "none"  # Page margins in mm: none, 10, 20, etc.

# Merge Metadata Settings
MERGE_METADATA_TITLE = "none"  # Title metadata for merged file
MERGE_METADATA_AUTHOR = "none"  # Author metadata for merged file
MERGE_METADATA_COMMENT = "none"  # Comment metadata for merged file

# Compression Settings
COMPRESSION_ENABLED = False  # Master switch to enable/disable compression feature
COMPRESSION_PRIORITY = 4  # Processing priority in pipeline (lower numbers run earlier)
COMPRESSION_DELETE_ORIGINAL = False  # Delete original files after successful compression

# Video Compression Settings
COMPRESSION_VIDEO_ENABLED = False  # Enable/disable video compression
COMPRESSION_VIDEO_PRESET = "none"  # Compression preset: none, fast, medium, slow
COMPRESSION_VIDEO_CRF = 0  # Constant Rate Factor for quality (0-51, lower is better quality)
COMPRESSION_VIDEO_CODEC = "none"  # Video codec: none, libx264, libx265, etc.
COMPRESSION_VIDEO_TUNE = "none"  # Tune option for specific content: none, film, animation, grain, etc.
COMPRESSION_VIDEO_PIXEL_FORMAT = "none"  # Pixel format: none, yuv420p, yuv444p, etc.
COMPRESSION_VIDEO_FORMAT = "none"  # Output format: none, mp4, mkv, avi, etc.

# Audio Compression Settings
COMPRESSION_AUDIO_ENABLED = False  # Enable/disable audio compression
COMPRESSION_AUDIO_PRESET = "none"  # Compression preset: none, fast, medium, slow
COMPRESSION_AUDIO_CODEC = "none"  # Audio codec: none, aac, mp3, opus, etc.
COMPRESSION_AUDIO_BITRATE = "none"  # Audio bitrate: none, 128k, 192k, 320k, etc.
COMPRESSION_AUDIO_CHANNELS = 0  # Number of audio channels: 0 (original), 1 (mono), 2 (stereo), etc.
COMPRESSION_AUDIO_FORMAT = "none"  # Output format: none, mp3, m4a, flac, etc.

# Image Compression Settings
COMPRESSION_IMAGE_ENABLED = False  # Enable/disable image compression
COMPRESSION_IMAGE_PRESET = "none"  # Compression preset: none, fast, medium, slow
COMPRESSION_IMAGE_QUALITY = 0  # Image quality (0-100, higher is better quality)
COMPRESSION_IMAGE_RESIZE = "none"  # Image resize dimensions: none, 1920x1080, 50%, etc.
COMPRESSION_IMAGE_FORMAT = "none"  # Output format: none, jpg, png, webp, etc.

# Document Compression Settings
COMPRESSION_DOCUMENT_ENABLED = False  # Enable/disable document compression
COMPRESSION_DOCUMENT_PRESET = "none"  # Compression preset: none, fast, medium, slow
COMPRESSION_DOCUMENT_DPI = 0  # Document DPI: 0 (original), 72, 96, 300, etc.
COMPRESSION_DOCUMENT_FORMAT = "none"  # Output format: none, pdf, docx, etc.

# Subtitle Compression Settings
COMPRESSION_SUBTITLE_ENABLED = False  # Enable/disable subtitle compression
COMPRESSION_SUBTITLE_PRESET = "none"  # Compression preset: none, fast, medium, slow
COMPRESSION_SUBTITLE_ENCODING = "none"  # Character encoding: none, utf-8, utf-16, etc.
COMPRESSION_SUBTITLE_FORMAT = "none"  # Output format: none, srt, ass, vtt, etc.

# Archive Compression Settings
COMPRESSION_ARCHIVE_ENABLED = False  # Enable/disable archive compression
COMPRESSION_ARCHIVE_PRESET = "none"  # Compression preset: none, fast, medium, slow
COMPRESSION_ARCHIVE_LEVEL = 0  # Compression level (0-9, higher is more compression)
COMPRESSION_ARCHIVE_METHOD = "none"  # Compression method: none, deflate, lzma, etc.
COMPRESSION_ARCHIVE_FORMAT = "none"  # Output format: none, zip, 7z, tar.gz, etc.

# Trim Settings
TRIM_ENABLED = False  # Master switch to enable/disable trim feature
TRIM_PRIORITY = 5  # Processing priority in pipeline (lower numbers run earlier)
TRIM_START_TIME = "00:00:00"  # Start time for trimming in HH:MM:SS format
TRIM_END_TIME = ""  # End time for trimming in HH:MM:SS format (empty = end of file)
TRIM_DELETE_ORIGINAL = False  # Delete original files after successful trimming

# Video Trim Settings
TRIM_VIDEO_ENABLED = False  # Enable/disable video trimming
TRIM_VIDEO_CODEC = "none"  # Video codec: none, copy (fastest), libx264, libx265, etc.
TRIM_VIDEO_PRESET = "none"  # Encoding preset: none, ultrafast, fast, medium, slow, etc.
TRIM_VIDEO_FORMAT = "none"  # Output format: none, mp4, mkv, avi, etc.

# Audio Trim Settings
TRIM_AUDIO_ENABLED = False  # Enable/disable audio trimming
TRIM_AUDIO_CODEC = "none"  # Audio codec: none, copy (fastest), aac, mp3, etc.
TRIM_AUDIO_PRESET = "none"  # Encoding preset: none, fast, medium, slow
TRIM_AUDIO_FORMAT = "none"  # Output format: none, mp3, m4a, flac, etc.

# Image Trim Settings
TRIM_IMAGE_ENABLED = False  # Enable/disable image trimming (crop)
TRIM_IMAGE_QUALITY = 90  # Image quality (0-100, higher is better quality)
TRIM_IMAGE_FORMAT = "none"  # Output format: none, jpg, png, webp, etc.

# Document Trim Settings
TRIM_DOCUMENT_ENABLED = False  # Enable/disable document trimming (page range)
TRIM_DOCUMENT_QUALITY = 90  # Document quality (0-100, higher is better quality)
TRIM_DOCUMENT_FORMAT = "none"  # Output format: none, pdf, docx, etc.

# Subtitle Trim Settings
TRIM_SUBTITLE_ENABLED = False  # Enable/disable subtitle trimming (time range)
TRIM_SUBTITLE_ENCODING = "none"  # Character encoding: none, utf-8, utf-16, etc.
TRIM_SUBTITLE_FORMAT = "none"  # Output format: none, srt, ass, vtt, etc.

# Archive Trim Settings
TRIM_ARCHIVE_ENABLED = False  # Enable/disable archive trimming (file selection)
TRIM_ARCHIVE_FORMAT = "none"  # Output format: none, zip, 7z, tar.gz, etc.

# Extract Settings
EXTRACT_ENABLED = False  # Master switch to enable/disable extract feature
EXTRACT_PRIORITY = 6  # Processing priority in pipeline (lower numbers run earlier)
EXTRACT_DELETE_ORIGINAL = True  # Delete original files after successful extraction

# Video Extract Settings
EXTRACT_VIDEO_ENABLED = False  # Enable/disable video stream extraction
EXTRACT_VIDEO_CODEC = "none"  # Video codec: none, copy (fastest), libx264, libx265, etc.
EXTRACT_VIDEO_FORMAT = "none"  # Output format: none, mp4, mkv, avi, etc.
EXTRACT_VIDEO_INDEX = None  # Stream index to extract: None (all), 0, 1, 2, etc.
EXTRACT_VIDEO_QUALITY = "none"  # Video quality: none, high, medium, low, etc.
EXTRACT_VIDEO_PRESET = "none"  # Encoding preset: none, ultrafast, fast, medium, slow, etc.
EXTRACT_VIDEO_BITRATE = "none"  # Video bitrate: none, 1M, 5M, etc.
EXTRACT_VIDEO_RESOLUTION = "none"  # Video resolution: none, 1920x1080, 1280x720, etc.
EXTRACT_VIDEO_FPS = "none"  # Frame rate: none, 30, 60, etc.

# Audio Extract Settings
EXTRACT_AUDIO_ENABLED = False  # Enable/disable audio stream extraction
EXTRACT_AUDIO_CODEC = "none"  # Audio codec: none, copy (fastest), aac, mp3, etc.
EXTRACT_AUDIO_FORMAT = "none"  # Output format: none, mp3, m4a, flac, etc.
EXTRACT_AUDIO_INDEX = None  # Stream index to extract: None (all), 0, 1, 2, etc.
EXTRACT_AUDIO_BITRATE = "none"  # Audio bitrate: none, 128k, 192k, 320k, etc.
EXTRACT_AUDIO_CHANNELS = "none"  # Number of audio channels: none, 1 (mono), 2 (stereo), etc.
EXTRACT_AUDIO_SAMPLING = "none"  # Audio sampling rate: none, 44100, 48000, etc.
EXTRACT_AUDIO_VOLUME = "none"  # Volume adjustment: none, 1.0, 1.5, 0.5, etc.

# Subtitle Extract Settings
EXTRACT_SUBTITLE_ENABLED = False  # Enable/disable subtitle stream extraction
EXTRACT_SUBTITLE_CODEC = "none"  # Subtitle codec: none, copy, mov_text, etc.
EXTRACT_SUBTITLE_FORMAT = "none"  # Output format: none, srt, ass, vtt, etc.
EXTRACT_SUBTITLE_INDEX = None  # Stream index to extract: None (all), 0, 1, 2, etc.
EXTRACT_SUBTITLE_LANGUAGE = "none"  # Language code: none, eng, spa, etc.
EXTRACT_SUBTITLE_ENCODING = "none"  # Character encoding: none, utf-8, utf-16, etc.
EXTRACT_SUBTITLE_FONT = "none"  # Font for subtitles: none, Arial, Times New Roman, etc.
EXTRACT_SUBTITLE_FONT_SIZE = "none"  # Font size: none, 12, 16, etc.

# Attachment Extract Settings
EXTRACT_ATTACHMENT_ENABLED = False  # Enable/disable attachment extraction
EXTRACT_ATTACHMENT_FORMAT = "none"  # Output format: none, original, etc.
EXTRACT_ATTACHMENT_INDEX = None  # Attachment index to extract: None (all), 0, 1, 2, etc.
EXTRACT_ATTACHMENT_FILTER = "none"  # Filter pattern: none, *.ttf, *.png, etc.
EXTRACT_MAINTAIN_QUALITY = True  # Maintain original quality during extraction

# Convert Settings
CONVERT_ENABLED = False  # Master switch to enable/disable convert feature
CONVERT_PRIORITY = 3  # Processing priority in pipeline (lower numbers run earlier)
CONVERT_DELETE_ORIGINAL = False  # Delete original files after successful conversion

# Video Convert Settings
CONVERT_VIDEO_ENABLED = False  # Enable/disable video conversion
CONVERT_VIDEO_FORMAT = "none"  # Target format: none, mp4, mkv, avi, webm, etc.
CONVERT_VIDEO_CODEC = "none"  # Video codec: none, libx264, libx265, vp9, etc.
CONVERT_VIDEO_QUALITY = "none"  # Video quality preset: none, high, medium, low
CONVERT_VIDEO_CRF = 0  # Constant Rate Factor (0-51, lower is better quality)
CONVERT_VIDEO_PRESET = "none"  # Encoding preset: none, ultrafast, fast, medium, slow, etc.
CONVERT_VIDEO_MAINTAIN_QUALITY = True  # Maintain original quality during conversion
CONVERT_VIDEO_RESOLUTION = "none"  # Target resolution: none, 1920x1080, 1280x720, etc.
CONVERT_VIDEO_FPS = "none"  # Target frame rate: none, 30, 60, etc.

# Audio Convert Settings
CONVERT_AUDIO_ENABLED = False  # Enable/disable audio conversion
CONVERT_AUDIO_FORMAT = "none"  # Target format: none, mp3, m4a, flac, ogg, etc.
CONVERT_AUDIO_CODEC = "none"  # Audio codec: none, aac, mp3, opus, flac, etc.
CONVERT_AUDIO_BITRATE = "none"  # Target bitrate: none, 128k, 192k, 320k, etc.
CONVERT_AUDIO_CHANNELS = 0  # Target channels: 0 (original), 1 (mono), 2 (stereo), etc.
CONVERT_AUDIO_SAMPLING = 0  # Target sampling rate: 0 (original), 44100, 48000, etc.
CONVERT_AUDIO_VOLUME = 0.0  # Volume adjustment: 0.0 (original), 1.0, 1.5, 0.5, etc.

# Subtitle Convert Settings
CONVERT_SUBTITLE_ENABLED = False  # Enable/disable subtitle conversion
CONVERT_SUBTITLE_FORMAT = "none"  # Target format: none, srt, ass, vtt, etc.
CONVERT_SUBTITLE_ENCODING = "none"  # Target encoding: none, utf-8, utf-16, etc.
CONVERT_SUBTITLE_LANGUAGE = "none"  # Target language code: none, eng, spa, etc.

# Document Convert Settings
CONVERT_DOCUMENT_ENABLED = False  # Enable/disable document conversion
CONVERT_DOCUMENT_FORMAT = "none"  # Target format: none, pdf, docx, txt, etc.
CONVERT_DOCUMENT_QUALITY = 0  # Document quality (0-100, higher is better)
CONVERT_DOCUMENT_DPI = 0  # Document DPI: 0 (original), 72, 96, 300, etc.

# Archive Convert Settings
CONVERT_ARCHIVE_ENABLED = False  # Enable/disable archive conversion
CONVERT_ARCHIVE_FORMAT = "none"  # Target format: none, zip, 7z, tar.gz, etc.
CONVERT_ARCHIVE_LEVEL = 0  # Compression level (0-9, higher is more compression)
CONVERT_ARCHIVE_METHOD = "none"  # Compression method: none, deflate, lzma, etc.

# Metadata Settings
METADATA_ALL = ""  # Global metadata template for all media types
METADATA_TITLE = ""  # Default title metadata for all media types
METADATA_AUTHOR = ""  # Default author metadata for all media types
METADATA_COMMENT = ""  # Default comment metadata for all media types
METADATA_VIDEO_TITLE = ""  # Default title metadata specifically for video files
METADATA_VIDEO_AUTHOR = ""  # Default author metadata specifically for video files
METADATA_VIDEO_COMMENT = ""  # Default comment metadata specifically for video files
METADATA_AUDIO_TITLE = ""  # Default title metadata specifically for audio files
METADATA_AUDIO_AUTHOR = ""  # Default author metadata specifically for audio files
METADATA_AUDIO_COMMENT = ""  # Default comment metadata specifically for audio files
METADATA_SUBTITLE_TITLE = ""  # Default title metadata specifically for subtitle files
METADATA_SUBTITLE_AUTHOR = ""  # Default author metadata specifically for subtitle files
METADATA_SUBTITLE_COMMENT = ""  # Default comment metadata specifically for subtitle files
