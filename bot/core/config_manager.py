import ast
import logging
import os
from importlib import import_module
from typing import Any, ClassVar

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Config:
    AS_DOCUMENT: bool = False
    AUTHORIZED_CHATS: str = ""
    AUTO_CAPTION_REMOVE: str = r"re:[Vv]egamovies[.\ ]?NL|\[HindiAnimeZone\.com\]|Moviesmod\.app|Moviesverse\.App|Moviesflix\.red|-?Moviesflix\.red|NF WEB-DL x264 \(DD\+ 5\.1 - 192Kbps\)|\[RareToonsIndia\]_|\[RareToonsIndia\]|MoviesRock"
    AUTO_CAPTION_REPLACE: str = ""
    AUTO_LEECH: bool = False
    AUTO_MIRROR: bool = False
    AUTO_ENCODE: bool = False
    AUTO_RESUME: bool = False
    AUTO_LEECH_CMD: str = "leech"
    AUTO_MIRROR_CMD: str = "mirror"
    AUTO_COMPRESS_CMD: str = ""
    BASE_URL: str = ""
    BASE_URL_PORT: int = 80
    BOT_TOKEN: str = ""
    CMD_SUFFIX: str = ""
    DATABASE_URL: str = ""
    DATABASE_NUM: str = ""
    DEFAULT_UPLOAD: str = "gd"
    EXCLUDED_EXTENSIONS: str = ""
    FFMPEG_CMDS: ClassVar[dict[str, list[str]]] = {}
    FILELION_API: str = ""
    GDRIVE_ID: str = ""
    GOFILE_API: str = ""
    GOFILE_FOLDER_ID: str = ""
    INCOMPLETE_TASK_NOTIFIER: bool = False
    INDEX_URL: str = ""
    JD_EMAIL: str = ""
    JD_PASS: str = ""
    IS_TEAM_DRIVE: bool = False
    LEECH_DUMP_CHAT: ClassVar[list[str]] = []
    BOT_PM: bool = True  # Enable/disable sending media to user's bot PM
    LEECH_FILENAME_PREFIX: str = ""
    LEECH_SPLIT_SIZE: int = 2097152000
    MEDIA_GROUP: bool = False
    HYBRID_LEECH: bool = False
    HYDRA_IP: str = ""
    HYDRA_API_KEY: str = ""
    NAME_SUBSTITUTE: str = r""
    LEECH_FILENAME_SUFFIX: str = ""
    LEECH_CAPTION_FONT: str = ""
    FILENAME_REPLACE: str = ""
    CLEAN_FILENAME: bool = False
    OWNER_ID: int = 0
    QUEUE_ALL: int = 0
    QUEUE_DOWNLOAD: int = 0
    QUEUE_UPLOAD: int = 0
    USER_TASK_LIMIT: int = 0
    LEECH_LIMIT: int = 0
    MIRROR_LIMIT: int = 0
    CLONE_LIMIT: int = 0
    RCLONE_FLAGS: str = ""
    RCLONE_PATH: str = ""
    RCLONE_SERVE_URL: str = ""
    RCLONE_SERVE_USER: str = ""
    RCLONE_SERVE_PASS: str = ""
    RCLONE_SERVE_PORT: int = 8080
    RSS_CHAT: str = ""
    RSS_DELAY: int = 600
    RSS_SIZE_LIMIT: int = 0
    STOP_DUPLICATE: bool = False
    STREAMWISH_API: str = ""
    LULU_API_KEY: str = ""
    SUDO_USERS: str = ""
    TELEGRAM_API: int = 0
    TELEGRAM_HASH: str = ""

    TG_PROXY: ClassVar[dict[str, str]] = {}
    THUMBNAIL_LAYOUT: str = ""
    TORRENT_TIMEOUT: int = 0
    UPLOAD_PATHS: ClassVar[dict[str, str]] = {}
    UPSTREAM_REPO: str = ""
    USENET_SERVERS: ClassVar[list[dict[str, object]]] = []
    UPSTREAM_BRANCH: str = "main"
    USER_SESSION_STRING: str = ""
    USER_TRANSMISSION: bool = False
    USE_SERVICE_ACCOUNTS: bool = False
    WEB_PINCODE: bool = False
    YT_DLP_OPTIONS: ClassVar[dict[str, Any]] = {}

    # Aeon-MLTB Specific / Custom Features
    METADATA_KEY: str = ""
    WATERMARK_KEY: str = ""
    SET_COMMANDS: bool = True
    TOKEN_TIMEOUT: int = 0
    PAID_CHANNEL_ID: int = 0
    PAID_CHANNEL_LINK: str = ""
    DELETE_LINKS: bool = False
    FSUB_IDS: str = ""
    LOG_CHAT_ID: int = 0
    LEECH_FILENAME_CAPTION: str = ""
    INSTADL_API: str = ""
    HEROKU_APP_NAME: str = ""
    HEROKU_API_KEY: str = ""
    MEGA_EMAIL: str = ""
    MEGA_PASSWORD: str = ""
    BUZZHEAVIER_TOKEN: str = ""
    BUZZHEAVIER_FOLDER_ID: str = ""
    PIXELDRAIN_KEY: str = ""
    METADATA: str = ""
    AUDIO_METADATA: str = ""
    VIDEO_METADATA: str = ""
    SUBTITLE_METADATA: str = ""

    # Feature Enablement Flags
    LEECH_ENABLED: bool = True
    TORRENT_ENABLED: bool = True
    GDRIVE_UPLOAD_ENABLED: bool = True
    MEGA_ENABLED: bool = True
    MEGA_UPLOAD_ENABLED: bool = True
    YOUTUBE_UPLOAD_ENABLED: bool = True
    DDL_ENABLED: bool = True
    MULTI_LINK_ENABLED: bool = True
    BULK_ENABLED: bool = True
    SAME_DIR_ENABLED: bool = True
    JD_ENABLED: bool = True
    NZB_ENABLED: bool = True
    MEDIA_TOOLS: bool = True

    # Auto Thumbnail & Rename Settings
    TMDB_API_KEY: str = ""
    TMDB_ENABLED: bool = True
    IMDB_ENABLED: bool = True
    AUTO_THUMBNAIL_ENABLED: bool = False
    AUTO_THUMBNAIL_FORMAT: str = "poster"
    AUTO_RENAME_ENABLED: bool = False
    AUTO_RENAME_TEMPLATE: str = "{title} S{season}E{episode} {quality}"
    AUTO_RENAME_START_EPISODE: int = 1
    AUTO_RENAME_START_SEASON: int = 1

    # Premium Debrid Services
    DEBRID_LINK_API: str = ""
    DEBRID_LINK_ACCESS_TOKEN: str = ""
    DEBRID_LINK_REFRESH_TOKEN: str = ""
    DEBRID_LINK_CLIENT_ID: str = ""
    DEBRID_LINK_CLIENT_SECRET: str = ""
    DEBRID_LINK_TOKEN_EXPIRES: int = 0
    ALLDEBRID_API_KEY: str = ""
    REAL_DEBRID_API_KEY: str = ""
    REAL_DEBRID_ACCESS_TOKEN: str = ""
    REAL_DEBRID_REFRESH_TOKEN: str = ""
    REAL_DEBRID_CLIENT_ID: str = ""
    REAL_DEBRID_CLIENT_SECRET: str = ""
    REAL_DEBRID_TOKEN_EXPIRES: int = 0
    MEGA_DEBRID_API_TOKEN: str = ""
    MEGA_DEBRID_LOGIN: str = ""
    MEGA_DEBRID_PASSWORD: str = ""
    TORBOX_API_KEY: str = ""
    MEDIAFIRE_EMAIL: str = ""
    MEDIAFIRE_PASSWORD: str = ""
    MEDIAFIRE_APP_ID: str = ""
    MEDIAFIRE_API_KEY: str = ""

    # Zotify Settings
    ZOTIFY_ENABLED: bool = False
    ZOTIFY_CREDENTIALS_PATH: str = "zotify_credentials.json"
    ZOTIFY_DOWNLOAD_QUALITY: str = "auto"
    ZOTIFY_AUDIO_FORMAT: str = "vorbis"
    ZOTIFY_ARTWORK_SIZE: str = "large"

    # Streamrip Settings
    STREAMRIP_ENABLED: bool = False
    STREAMRIP_QOBUZ_EMAIL: str = ""
    STREAMRIP_QOBUZ_PASSWORD: str = ""
    STREAMRIP_QOBUZ_APP_ID: str = ""
    STREAMRIP_QOBUZ_SECRETS: ClassVar[list[str]] = []
    STREAMRIP_TIDAL_ACCESS_TOKEN: str = ""
    STREAMRIP_TIDAL_REFRESH_TOKEN: str = ""
    STREAMRIP_TIDAL_USER_ID: str = ""
    STREAMRIP_TIDAL_COUNTRY_CODE: str = "US"
    STREAMRIP_TIDAL_TOKEN_EXPIRY: str = "1748842786"
    STREAMRIP_DEEZER_ARL: str = ""
    STREAMRIP_SOUNDCLOUD_CLIENT_ID: str = ""
    STREAMRIP_SOUNDCLOUD_APP_VERSION: str = ""
    STREAMRIP_SOURCE_SUBDIRECTORIES: bool = False
    STREAMRIP_DISC_SUBDIRECTORIES: bool = True
    STREAMRIP_CONCURRENCY: bool = True
    STREAMRIP_MAX_CONNECTIONS: int = 6
    STREAMRIP_REQUESTS_PER_MINUTE: int = 60
    STREAMRIP_VERIFY_SSL: bool = True
    STREAMRIP_QOBUZ_QUALITY: int = 3
    STREAMRIP_QOBUZ_DOWNLOAD_BOOKLETS: bool = True
    STREAMRIP_QOBUZ_USE_AUTH_TOKEN: bool = False
    STREAMRIP_TIDAL_QUALITY: int = 3
    STREAMRIP_TIDAL_DOWNLOAD_VIDEOS: bool = True
    STREAMRIP_DEEZER_QUALITY: int = 2
    STREAMRIP_DEEZER_USE_DEEZLOADER: bool = True
    STREAMRIP_DEEZER_DEEZLOADER_WARNINGS: bool = True
    STREAMRIP_SOUNDCLOUD_QUALITY: int = 0
    STREAMRIP_YOUTUBE_QUALITY: int = 0
    STREAMRIP_YOUTUBE_DOWNLOAD_VIDEOS: bool = False
    STREAMRIP_YOUTUBE_VIDEO_DOWNLOADS_FOLDER: str = ""
    STREAMRIP_DATABASE_DOWNLOADS_ENABLED: bool = True
    STREAMRIP_DATABASE_DOWNLOADS_PATH: str = "./downloads.db"
    STREAMRIP_DATABASE_FAILED_DOWNLOADS_ENABLED: bool = True
    STREAMRIP_DATABASE_FAILED_DOWNLOADS_PATH: str = "./failed_downloads.db"
    STREAMRIP_CONVERSION_ENABLED: bool = False
    STREAMRIP_CONVERSION_CODEC: str = "ALAC"
    STREAMRIP_CONVERSION_SAMPLING_RATE: int = 48000
    STREAMRIP_CONVERSION_BIT_DEPTH: int = 24
    STREAMRIP_CONVERSION_LOSSY_BITRATE: int = 320
    STREAMRIP_QOBUZ_FILTERS_EXTRAS: bool = False
    STREAMRIP_QOBUZ_FILTERS_REPEATS: bool = False
    STREAMRIP_QOBUZ_FILTERS_NON_ALBUMS: bool = False
    STREAMRIP_QOBUZ_FILTERS_FEATURES: bool = False
    STREAMRIP_QOBUZ_FILTERS_NON_STUDIO_ALBUMS: bool = False
    STREAMRIP_QOBUZ_FILTERS_NON_REMASTER: bool = False
    STREAMRIP_EMBED_COVER_ART: bool = True
    STREAMRIP_COVER_ART_SIZE: str = "large"
    STREAMRIP_ARTWORK_EMBED_MAX_WIDTH: int = -1
    STREAMRIP_SAVE_COVER_ART: bool = True
    STREAMRIP_ARTWORK_SAVED_MAX_WIDTH: int = -1
    STREAMRIP_METADATA_SET_PLAYLIST_TO_ALBUM: bool = True
    STREAMRIP_METADATA_RENUMBER_PLAYLIST_TRACKS: bool = True
    STREAMRIP_METADATA_EXCLUDE: ClassVar[list[str]] = []
    STREAMRIP_FILEPATHS_ADD_SINGLES_TO_FOLDER: bool = False
    STREAMRIP_FILEPATHS_FOLDER_FORMAT: str = "{albumartist} - {title} ({year}) [{container}] [{bit_depth}B-{sampling_rate}kHz]"
    STREAMRIP_FILEPATHS_TRACK_FORMAT: str = "{tracknumber:02}. {artist} - {title}{explicit}"
    STREAMRIP_FILEPATHS_RESTRICT_CHARACTERS: bool = False
    STREAMRIP_FILEPATHS_TRUNCATE_TO: int = 120
    STREAMRIP_LASTFM_SOURCE: str = "qobuz"
    STREAMRIP_LASTFM_FALLBACK_SOURCE: str = ""
    STREAMRIP_CLI_TEXT_OUTPUT: bool = True
    STREAMRIP_CLI_PROGRESS_BARS: bool = False
    STREAMRIP_CLI_MAX_SEARCH_RESULTS: int = 100
    STREAMRIP_MISC_VERSION: str = "2.1.0"
    STREAMRIP_MISC_CHECK_FOR_UPDATES: bool = False

    @classmethod
    def _convert(cls, key, value):
        expected_type = type(getattr(cls, key))
        if value is None:
            return None

        if key == "LEECH_DUMP_CHAT":
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]

            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return []
                try:
                    evaluated = ast.literal_eval(value)
                    if isinstance(evaluated, list):
                        return [str(v).strip() for v in evaluated if str(v).strip()]
                except (ValueError, SyntaxError):
                    pass
                return [value] if value else []

            raise TypeError(f"{key} should be list[str], got {type(value).__name__}")

        if isinstance(value, expected_type):
            return value

        if expected_type is bool:
            return str(value).strip().lower() in {"true", "1", "yes"}

        if expected_type in [list, dict]:
            if not isinstance(value, str):
                raise TypeError(
                    f"{key} should be {expected_type.__name__}, got {type(value).__name__}"
                )

            if not value:
                return expected_type()
            try:
                evaluated = ast.literal_eval(value)
                if isinstance(evaluated, expected_type):
                    return evaluated
                raise TypeError
            except (ValueError, SyntaxError, TypeError) as e:
                raise TypeError(
                    f"{key} should be {expected_type.__name__}, got invalid string: {value}"
                ) from e

        try:
            return expected_type(value)
        except (ValueError, TypeError) as exc:
            raise TypeError(
                f"Invalid type for {key}: expected {expected_type}, got {type(value)}"
            ) from exc

    @classmethod
    def _normalize_value(cls, key: str, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()

        if key == "DEFAULT_UPLOAD":
            if value.lower() not in ["yt", "gd", "rc", "gofile"]:
                return "gd"
            return value.lower()

        if key in {"BASE_URL", "RCLONE_SERVE_URL", "INDEX_URL"}:
            return value.strip("/")

        if key == "USENET_SERVERS" and (
            not isinstance(value, list)
            or not value
            or not isinstance(value[0], dict)
            or not value[0].get("host")
        ):
            return []

        return value

    @classmethod
    def get(cls, key: str) -> Any:
        return getattr(cls, key, None)

    @classmethod
    def set(cls, key: str, value: Any):
        if not hasattr(cls, key):
            raise KeyError(f"{key} is not a valid configuration key.")
        converted = cls._convert(key, value)
        normalized = cls._normalize_value(key, converted)
        setattr(cls, key, normalized)

    @classmethod
    def get_all(cls) -> dict:
        return {key: getattr(cls, key) for key in sorted(cls.__annotations__)}

    @classmethod
    def load(cls):
        try:
            settings = import_module("config")
        except ModuleNotFoundError:
            logger.warning("No config.py module found.")
            return

        for attr in dir(settings):
            if not cls._is_valid_config_attr(settings, attr):
                continue

            value = getattr(settings, attr)
            if not value:
                continue

            try:
                cls.set(attr, value)
            except Exception as e:
                logger.warning(f"Skipping config '{attr}' due to error: {e}")

    @classmethod
    def load_dict(cls, config_dict: dict[str, Any]):
        for key, value in config_dict.items():
            try:
                cls.set(key, value)
            except Exception as e:
                logger.warning(f"Skipping config '{key}' due to error: {e}")

    @classmethod
    def _is_valid_config_attr(cls, module, attr: str) -> bool:
        return (
            not attr.startswith("__")
            and not callable(getattr(module, attr))
            and attr in cls.__annotations__
        )


class SystemEnv:
    @classmethod
    def load(cls):
        for key in Config.__annotations__:
            env_value = os.getenv(key)
            if env_value is not None:
                try:
                    Config.set(key, env_value)
                except Exception as e:
                    logger.warning(f"Env override failed for '{key}': {e}")
