# REQUIRED CONFIG
BOT_TOKEN = ""
OWNER_ID = 0
TELEGRAM_API = 0
TELEGRAM_HASH = ""

# Recommended for persisting settings, RSS feeds, and task history. Essential for some features.
DATABASE_URL = ""

# FEATURE ENABLEMENT FLAGS
LEECH_ENABLED = True
TORRENT_ENABLED = True
GDRIVE_UPLOAD_ENABLED = True
MEGA_ENABLED = True
MEGA_UPLOAD_ENABLED = True
YOUTUBE_UPLOAD_ENABLED = True
DDL_ENABLED = True
MULTI_LINK_ENABLED = True
BULK_ENABLED = True
SAME_DIR_ENABLED = True
JD_ENABLED = True
NZB_ENABLED = True
MEDIA_TOOLS = True

# OPTIONAL CONFIG
TG_PROXY = {}  # Example: {"scheme": "socks5", "hostname": "11.22.33.44", "port": 1234, "username": "user", "password": "pass"}
USER_SESSION_STRING = ""
CMD_SUFFIX = ""  # Suffix to add to all bot commands
AUTHORIZED_CHATS = ""  # Space separated chat_id/user_id to authorize
SUDO_USERS = ""  # Space separated user_id for sudo access
DEFAULT_UPLOAD = ""  # Default uploader if -ul is not specified. Options: "yt" (YouTube), "gd" (Google Drive), "rc" (Rclone), or "" (empty for no specific default).
FILELION_API = ""

STREAMWISH_API = ""
LULU_API_KEY = ""
EXCLUDED_EXTENSIONS = (
    ""  # Space separated file extensions to exclude (e.g., .log .exe)
)
INCOMPLETE_TASK_NOTIFIER = (
    False  # Notify for incomplete tasks on restart (requires DATABASE_URL)
)
YT_DLP_OPTIONS = {}  # Dictionary of yt-dlp options, e.g., {"format": "bestvideo+bestaudio/best"}
USE_SERVICE_ACCOUNTS = False
NAME_SUBSTITUTE = r""  # Replace/remove words: "source1/target1|source2/target2"
FFMPEG_CMDS = {}  # Predefined FFmpeg commands, e.g., {"preset_name": ["-vf", "scale=1280:-1"]}
UPLOAD_PATHS = {}  # Named upload paths, e.g., {"movies": "remote:movies/", "tv": "gdrive_id_tv_folder"}

# Aeon-MLTB Specific Features / Customizations
DELETE_LINKS = False  # Auto-delete links after a certain period or action
FSUB_IDS = ""  # Forced subscription channel IDs (comma-separated)
TOKEN_TIMEOUT = 0  # Timeout in seconds for user tokens (0 for no timeout)
PAID_CHANNEL_ID = 0  # Channel ID users must join to bypass token
PAID_CHANNEL_LINK = ""  # Invite link for the paid channel
SET_COMMANDS = True  # Register bot commands with BotFather on startup
METADATA_KEY = ""  # Key for tagging/fetching metadata
WATERMARK_KEY = ""  # Key for watermarking files
LOG_CHAT_ID = 0  # Chat ID for sending leech logs
LEECH_FILENAME_CAPTION = ""  # Template caption for leeched files
HYDRA_IP = ""  # IP of NZBHydra2 instance
HYDRA_API_KEY = ""  # API key for NZBHydra2
INSTADL_API = ""  # URL/endpoint for InstaDL API

# Auto Thumbnail & TMDB/IMDB Rename Configuration
TMDB_API_KEY = ""  # TMDB API key for metadata and thumbnails (get from https://www.themoviedb.org/settings/api)
TMDB_ENABLED = True  # Enable TMDB for auto thumbnails and metadata
IMDB_ENABLED = True  # Enable IMDB for auto thumbnails and metadata
AUTO_THUMBNAIL_ENABLED = False  # Enable automatic thumbnail generation from IMDB/TMDB
AUTO_THUMBNAIL_FORMAT = "poster"  # Thumbnail format: "poster" (default) or "backdrop" for background images
AUTO_RENAME_ENABLED = False  # Enable automatic file renaming with IMDB/TMDB metadata
AUTO_RENAME_TEMPLATE = "S{season}E{episode}Q{quality}"  # Template for file renaming
AUTO_RENAME_START_EPISODE = 1  # Starting episode number for sequential renaming
AUTO_RENAME_START_SEASON = 1  # Starting season number for sequential renaming

# Premium Debrid Services (for direct download link generation)
# Debrid-Link (supports 100+ file hosts and torrents)
DEBRID_LINK_API = ""  # Debrid-Link API key or access token (get from https://debrid-link.com/webapp/apikey)
DEBRID_LINK_ACCESS_TOKEN = ""  # OAuth2 access token (preferred for better security)
DEBRID_LINK_REFRESH_TOKEN = ""  # OAuth2 refresh token (for automatic token refresh)
DEBRID_LINK_CLIENT_ID = ""  # OAuth2 client ID (for apps)
DEBRID_LINK_CLIENT_SECRET = ""  # OAuth2 client secret (optional, for server-side apps)
DEBRID_LINK_TOKEN_EXPIRES = 0  # Token expiration timestamp (managed automatically)

# AllDebrid (supports 100+ file hosts, torrents, and streaming)
ALLDEBRID_API_KEY = ""  # AllDebrid API key (get from https://alldebrid.com/apikeys/)

# Real-Debrid (supports 100+ file hosts and torrents)
REAL_DEBRID_API_KEY = ""  # Real-Debrid API key or access token
REAL_DEBRID_ACCESS_TOKEN = ""  # OAuth2 access token (preferred for better security)
REAL_DEBRID_REFRESH_TOKEN = ""  # OAuth2 refresh token (for automatic token refresh)
REAL_DEBRID_CLIENT_ID = ""  # OAuth2 client ID (default: "X245A4XAIBGVM" for opensource apps)
REAL_DEBRID_CLIENT_SECRET = ""  # OAuth2 client secret (optional)
REAL_DEBRID_TOKEN_EXPIRES = 0  # Token expiration timestamp (managed automatically)

# Mega-Debrid (European debrid service with torrent/magnet support)
MEGA_DEBRID_API_TOKEN = ""  # Mega-Debrid API token
MEGA_DEBRID_LOGIN = ""  # Mega-Debrid login email (alternative to API token)
MEGA_DEBRID_PASSWORD = ""  # Mega-Debrid password (used with login)

# TorBox (supports torrents, usenet, and web downloads)
TORBOX_API_KEY = ""  # TorBox API key (get from https://torbox.app/settings)

# MediaFire API (for private file/folder access and higher rate limits)
MEDIAFIRE_EMAIL = ""  # MediaFire account email
MEDIAFIRE_PASSWORD = ""  # MediaFire account password
MEDIAFIRE_APP_ID = ""  # MediaFire app ID (get from https://www.mediafire.com/developers/)
MEDIAFIRE_API_KEY = ""  # MediaFire API key


# GDrive Tools
GDRIVE_ID = ""  # Default Google Drive Folder/TeamDrive ID or "root"
IS_TEAM_DRIVE = False  # Set True if GDRIVE_ID is a TeamDrive
STOP_DUPLICATE = False  # Check for duplicate file/folder names before uploading
INDEX_URL = ""  # Index URL for the GDrive_ID

# Rclone
RCLONE_PATH = ""  # Default Rclone upload path (e.g., myremote:path)
RCLONE_FLAGS = ""  # Additional Rclone flags (e.g., --drive-chunk-size=64M)
RCLONE_SERVE_URL = ""  # URL for Rclone serve (e.g., http://myip or http://myip:port)
RCLONE_SERVE_PORT = 8080  # Port for Rclone serve (Default: 8080)
RCLONE_SERVE_USER = ""  # Username for Rclone serve
RCLONE_SERVE_PASS = ""  # Password for Rclone serve

# Sabnzbd
USENET_SERVERS = [  # List of Usenet server configurations
    {
        "name": "main",  # Server name
        "host": "",  # Server host
        "port": 563,  # Server port (e.g., 563 for SSL, 119 for non-SSL)
        "timeout": 60,  # Connection timeout in seconds
        "username": "",  # Server username
        "password": "",  # Server password
        "connections": 8,  # Number of connections
        "ssl": 1,  # SSL usage: 0=None, 1=SSL, 2=TLS
        "ssl_verify": 2,  # SSL verification: 0=None, 1=Warn, 2=Abort
        "ssl_ciphers": "",  # Custom SSL ciphers
        "enable": 1,  # Enable this server: 1=Yes, 0=No
        "required": 0,  # Required server: 1=Yes, 0=No
        "optional": 0,  # Optional server: 1=Yes, 0=No
        "retention": 0,  # Server retention in days (0 for unknown)
        "send_group": 0,  # Send group names: 1=Yes, 0=No
        "priority": 0,  # Server priority (0-100, lower is higher priority)
    },
]

# Update
UPSTREAM_REPO = (
    "https://github.com/AeonOrg/Aeon-MLTB"  # Upstream repository for updates
)
UPSTREAM_BRANCH = "main"  # Default branch for updates

# Leech
AUTO_LEECH_CMD = "leech" # Command to run on auto-leech (e.g., "leech", "mirror", "clone")
LEECH_SPLIT_SIZE = 2097152000  # Split size for leeched files in bytes. Default: 2GB. Max: 4GB for Premium, 2GB for others. 0 for bot default.
AS_DOCUMENT = False  # Upload leeched files as documents instead of media
MEDIA_GROUP = False  # Send leeched files as a media group
USER_TRANSMISSION = False  # Use user session for uploads/downloads (Premium only)
HYBRID_LEECH = (
    False  # Switch between bot/user session based on file size (Premium only)
)
LEECH_FILENAME_PREFIX = ""  # Prefix for leeched filenames
LEECH_DUMP_CHAT = []  # List of chat_ids or channel_ids to dump leeched files, e.g., [-100123456789, "channel_username"]
THUMBNAIL_LAYOUT = ""  # Thumbnail layout for uploads (e.g., 2x2, 3x3)

# qBittorrent/Aria2c
TORRENT_TIMEOUT = 0  # Timeout in seconds for dead torrents. 0 for no timeout.
BASE_URL = ""  # Base URL of the bot, for web file selection (e.g., http://myip or http://myip:port)
BASE_URL_PORT = 80  # Port for the BASE_URL (Default: 80)
WEB_PINCODE = False  # Require a PIN code for web file selection

# Queueing system
# Queueing system
QUEUE_ALL = 0  # Max concurrent tasks (upload + download)
QUEUE_DOWNLOAD = 0  # Max concurrent download tasks
QUEUE_UPLOAD = 0  # Max concurrent upload tasks
USER_TASK_LIMIT = 0 # Max concurrent tasks per user
LEECH_LIMIT = 0 # Leech limit in GB
MIRROR_LIMIT = 0 # Mirror limit in GB
CLONE_LIMIT = 0 # Clone limit in GB

# RSS
RSS_DELAY = 600  # RSS feed check interval in seconds (Default: 600)
RSS_CHAT = ""  # Chat ID or username where RSS messages will be sent
RSS_SIZE_LIMIT = 0  # Max size for RSS items in bytes (0 for no limit)

# Heroku config for get BASE_URL automatically
HEROKU_APP_NAME = ""  # Name of your Heroku app, used to get BASE_URL automatically
HEROKU_API_KEY = ""  # API key for your Heroku account
 
# URL Shortener Configuration
SHORTENER_ENABLED = True  # Enable/disable URL shortener
SHORTENER_API_TOKEN = ""  # API token for shortener service
SHORTENER_API_URL = "https://arolinks.com/api"  #Your shortener API URL
SHORTENER_DOMAIN = "arolinks.com"  # Your shortener domain
SHORTENER_WORKER_URL = "https://antibypass.tellycloudapi.workers.dev/create"  # Cloudflare Worker URL
SHORTENER_CHANNELS = [  # Channels to show on shortened links
    {"name": "TellY Mirror", "url": "https://t.me/tellY_mirror"}
]
SHORTENER_DEFAULT_EXPIRY = 7  # Default link expiry in days
SHORTENER_USE_PASSWORD = True  # Auto-generate 4-digit password for links

# Terabox Configuration
TERABOX_API_URL = "https://teraboxdl.tellycloudapi.workers.dev/"  # Terabox API endpoint
# No newline at end of file
