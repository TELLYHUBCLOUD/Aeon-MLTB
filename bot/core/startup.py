from asyncio import create_subprocess_exec, create_subprocess_shell
from os import environ
import secrets
import aiohttp
from aiofiles import open as aiopen
from aiofiles.os import makedirs, remove
from aiofiles.os import path as aiopath
from aioshutil import rmtree

from bot import (
    LOGGER,
    aria2_options,
    auth_chats,
    drives_ids,
    drives_names,
    excluded_extensions,
    index_urls,
    nzb_options,
    qbit_options,
    rss_dict,
    sabnzbd_client,
    shorteners_list,
    sudo_users,
    user_data,
)
from bot.helper.ext_utils.db_handler import database

from .aeon_client import TgClient
from .config_manager import Config
from .torrent_manager import TorrentManager

# Constants
THUMBNAIL_DIR = "thumbnails"
TOKEN_DIR = "tokens"
RCLONE_DIR = "rclone"
SABNZBD_DIR = "sabnzbd"
ACCOUNTS_DIR = "accounts"
NETRC_FILE = ".netrc"
LIST_DRIVES_FILE = "list_drives.txt"
SHORTENERS_FILE = "shorteners.txt"
CFG_ZIP = "cfg.zip"
ACCOUNTS_ZIP = "accounts.zip"
SABNZBD_INI = "SABnzbd.ini"
SABNZBD_INI_BAK = "SABnzbd.ini.bak"


async def ensure_directory(path: str) -> None:
    """Safely create directory if it doesn't exist.
    
    Args:
        path: Directory path to create
    """
    try:
        await makedirs(path, exist_ok=True)
    except Exception as e:
        LOGGER.error(f"Failed to create directory {path}: {e}")
        raise


async def safe_remove_tree(path: str) -> None:
    """Safely remove directory tree if it exists.
    
    Args:
        path: Directory path to remove
    """
    try:
        if await aiopath.exists(path):
            await rmtree(path, ignore_errors=True)
    except Exception as e:
        LOGGER.warning(f"Error removing directory {path}: {e}")


async def safe_remove_file(path: str) -> None:
    """Safely remove file if it exists.
    
    Args:
        path: File path to remove
    """
    try:
        if await aiopath.exists(path):
            await remove(path)
    except Exception as e:
        LOGGER.warning(f"Error removing file {path}: {e}")


def generate_secure_password() -> str:
    """Generate a secure random password.
    
    Returns:
        A cryptographically secure random password
    """
    return secrets.token_urlsafe(32)


async def update_qb_options() -> None:
    """Updates qBittorrent options either from current preferences or saved configuration."""
    try:
        if not qbit_options:
            opt = await TorrentManager.qbittorrent.app.preferences()
            qbit_options.update(opt)
            
            # Remove listen_port
            qbit_options.pop("listen_port", None)
            
            # Remove RSS-related options
            for k in list(qbit_options.keys()):
                if k.startswith("rss"):
                    del qbit_options[k]
            
            # Use environment variable or generate secure password
            secure_password = environ.get("QBITTORRENT_PASSWORD") or generate_secure_password()
            qbit_options["web_ui_password"] = secure_password
            
            await TorrentManager.qbittorrent.app.set_preferences(
                {"web_ui_password": secure_password},
            )
            LOGGER.info("qBittorrent options updated with new password")
        else:
            await TorrentManager.qbittorrent.app.set_preferences(qbit_options)
            LOGGER.info("qBittorrent options applied from saved configuration")
    except Exception as e:
        LOGGER.error(f"Failed to update qBittorrent options: {e}")
        raise


async def update_aria2_options() -> None:
    """Updates Aria2c global options either from current settings or saved configuration."""
    try:
        if not aria2_options:
            op = await TorrentManager.aria2.getGlobalOption()
            aria2_options.update(op)
            LOGGER.info("Aria2 options loaded from current settings")
        else:
            await TorrentManager.aria2.changeGlobalOption(aria2_options)
            LOGGER.info("Aria2 options applied from saved configuration")
    except Exception as e:
        LOGGER.error(f"Failed to update Aria2 options: {e}")
        raise


async def update_nzb_options() -> None:
    """Updates NZB options from Sabnzbd client configuration."""
    try:
        config = await sabnzbd_client.get_config()
        no = config.get("config", {}).get("misc", {})
        nzb_options.update(no)
        LOGGER.info("NZB options updated from Sabnzbd client")
    except Exception as e:
        LOGGER.error(f"Failed to update NZB options: {e}")
        raise


async def load_settings() -> None:
    """Loads bot settings from the database (if DATABASE_URL is set)
    and applies them to the current runtime configuration.
    This includes deployment configs, general configs, private files,
    and user-specific data like thumbnails and rclone configs.
    """
    if not Config.DATABASE_URL:
        LOGGER.info("No DATABASE_URL configured, skipping settings load")
        return
    
    try:
        # Clean up existing directories
        for p in [THUMBNAIL_DIR, TOKEN_DIR, RCLONE_DIR]:
            await safe_remove_tree(p)
        
        await database.connect()
        
        if database.db is None:
            LOGGER.warning("Database connection failed")
            return
        
        BOT_ID = Config.BOT_TOKEN.split(":", 1)[0]
        current_deploy_config = Config.get_all()
        
        # Load or create deployment config
        old_deploy_config = await database.db.settings.deployConfig.find_one(
            {"_id": BOT_ID},
            {"_id": 0},
        )

        if old_deploy_config is None:
            await database.db.settings.deployConfig.replace_one(
                {"_id": BOT_ID},
                current_deploy_config,
                upsert=True,
            )
            LOGGER.info("Created new deployment config in database")
        elif old_deploy_config != current_deploy_config:
            runtime_config = (
                await database.db.settings.config.find_one(
                    {"_id": BOT_ID},
                    {"_id": 0},
                )
                or {}
            )

            new_vars = {
                k: v
                for k, v in current_deploy_config.items()
                if k not in runtime_config
            }
            
            if new_vars:
                runtime_config.update(new_vars)
                await database.db.settings.config.replace_one(
                    {"_id": BOT_ID},
                    runtime_config,
                    upsert=True,
                )
                LOGGER.info(f"Added new variables: {list(new_vars.keys())}")

            await database.db.settings.deployConfig.replace_one(
                {"_id": BOT_ID},
                current_deploy_config,
                upsert=True,
            )

        # Load runtime configuration
        runtime_config = await database.db.settings.config.find_one(
            {"_id": BOT_ID},
            {"_id": 0},
        )
        if runtime_config:
            Config.load_dict(runtime_config)
            LOGGER.info("Runtime configuration loaded from database")

        # Load private files
        pf_dict = await database.db.settings.files.find_one(
            {"_id": BOT_ID},
            {"_id": 0},
        )
        
        if pf_dict:
            for key, value in pf_dict.items():
                if value:
                    file_ = key.replace("__", ".")
                    try:
                        async with aiopen(file_, "wb+") as f:
                            await f.write(value)
                        LOGGER.info(f"Loaded private file: {file_}")
                    except Exception as e:
                        LOGGER.error(f"Failed to write file {file_}: {e}")

        # Load Aria2c options
        a2c_options = await database.db.settings.aria2c.find_one(
            {"_id": BOT_ID},
            {"_id": 0},
        )
        if a2c_options:
            aria2_options.update(a2c_options)
            LOGGER.info("Aria2c options loaded from database")

        # Load qBittorrent options
        qbit_opt = await database.db.settings.qbittorrent.find_one(
            {"_id": BOT_ID},
            {"_id": 0},
        )
        if qbit_opt:
            qbit_options.update(qbit_opt)
            LOGGER.info("qBittorrent options loaded from database")

        # Load NZB options
        nzb_opt = await database.db.settings.nzb.find_one(
            {"_id": BOT_ID},
            {"_id": 0},
        )
        if nzb_opt:
            bak_path = f"{SABNZBD_DIR}/{SABNZBD_INI_BAK}"
            await safe_remove_file(bak_path)
            
            ((key, value),) = nzb_opt.items()
            file_ = key.replace("__", ".")
            try:
                async with aiopen(f"{SABNZBD_DIR}/{file_}", "wb+") as f:
                    await f.write(value)
                LOGGER.info("NZB configuration loaded from database")
            except Exception as e:
                LOGGER.error(f"Failed to write NZB config: {e}")

        # Load user data
        if await database.db.users.find_one():
            for p in [THUMBNAIL_DIR, TOKEN_DIR, RCLONE_DIR]:
                await ensure_directory(p)
            
            rows = database.db.users.find({})
            user_count = 0
            
            async for row in rows:
                uid = row["_id"]
                del row["_id"]
                
                thumb_path = f"{THUMBNAIL_DIR}/{uid}.jpg"
                rclone_config_path = f"{RCLONE_DIR}/{uid}.conf"
                token_path = f"{TOKEN_DIR}/{uid}.pickle"
                
                try:
                    if row.get("THUMBNAIL"):
                        async with aiopen(thumb_path, "wb+") as f:
                            await f.write(row["THUMBNAIL"])
                        row["THUMBNAIL"] = thumb_path
                    
                    if row.get("RCLONE_CONFIG"):
                        async with aiopen(rclone_config_path, "wb+") as f:
                            await f.write(row["RCLONE_CONFIG"])
                        row["RCLONE_CONFIG"] = rclone_config_path
                    
                    if row.get("TOKEN_PICKLE"):
                        async with aiopen(token_path, "wb+") as f:
                            await f.write(row["TOKEN_PICKLE"])
                        row["TOKEN_PICKLE"] = token_path
                    
                    user_data[uid] = row
                    user_count += 1
                except Exception as e:
                    LOGGER.error(f"Failed to load data for user {uid}: {e}")
            
            LOGGER.info(f"User data has been imported from the Database ({user_count} users).")

        # Load RSS data
        if await database.db.rss[BOT_ID].find_one():
            rows = database.db.rss[BOT_ID].find({})
            rss_count = 0
            
            async for row in rows:
                user_id = row["_id"]
                del row["_id"]
                rss_dict[user_id] = row
                rss_count += 1
            
            LOGGER.info(f"RSS data has been imported from the Database ({rss_count} feeds).")
    
    except Exception as e:
        LOGGER.error(f"Error loading settings from database: {e}")
        raise


async def save_settings() -> None:
    """Saves the current bot configuration to the database if DATABASE_URL is set."""
    if database.db is None:
        LOGGER.warning("Database not connected, skipping settings save")
        return
    
    try:
        config_dict = Config.get_all()
        await database.db.settings.config.replace_one(
            {"_id": TgClient.ID},
            config_dict,
            upsert=True,
        )
        LOGGER.info("Configuration saved to database")
        
        # Save Aria2c options if not exists
        if await database.db.settings.aria2c.find_one({"_id": TgClient.ID}) is None:
            await database.db.settings.aria2c.update_one(
                {"_id": TgClient.ID},
                {"$set": aria2_options},
                upsert=True,
            )
            LOGGER.info("Aria2c options saved to database")
        
        # Save qBittorrent options if not exists
        if await database.db.settings.qbittorrent.find_one({"_id": TgClient.ID}) is None:
            await database.save_qbit_settings()
            LOGGER.info("qBittorrent options saved to database")
        
        # Save NZB options if not exists
        if await database.db.settings.nzb.find_one({"_id": TgClient.ID}) is None:
            nzb_ini_path = f"{SABNZBD_DIR}/{SABNZBD_INI}"
            if await aiopath.exists(nzb_ini_path):
                async with aiopen(nzb_ini_path, "rb+") as pf:
                    nzb_conf = await pf.read()
                await database.db.settings.nzb.update_one(
                    {"_id": TgClient.ID},
                    {"$set": {"SABnzbd__ini": nzb_conf}},
                    upsert=True,
                )
                LOGGER.info("NZB configuration saved to database")
    
    except Exception as e:
        LOGGER.error(f"Error saving settings to database: {e}")
        raise


async def update_variables() -> None:
    """Updates various global configuration variables and lists based on the
    loaded Config values. This includes setting up authorized chats, sudo users,
    excluded extensions, drive lists, and attempting to determine the BASE_URL
    if running on Heroku.
    """
    try:
        # Update LEECH_SPLIT_SIZE
        if (
            Config.LEECH_SPLIT_SIZE > TgClient.MAX_SPLIT_SIZE
            or Config.LEECH_SPLIT_SIZE == 2097152000
            or not Config.LEECH_SPLIT_SIZE
        ):
            Config.LEECH_SPLIT_SIZE = TgClient.MAX_SPLIT_SIZE

        # Update premium user features
        Config.HYBRID_LEECH = bool(Config.HYBRID_LEECH and TgClient.IS_PREMIUM_USER)
        Config.USER_TRANSMISSION = bool(
            Config.USER_TRANSMISSION and TgClient.IS_PREMIUM_USER,
        )

        # Load authorized chats
        if Config.AUTHORIZED_CHATS:
            aid = Config.AUTHORIZED_CHATS.split()
            for id_ in aid:
                try:
                    chat_id, *thread_ids = id_.split("|")
                    chat_id = int(chat_id.strip())
                    if thread_ids:
                        thread_ids = [int(x.strip()) for x in thread_ids]
                        auth_chats[chat_id] = thread_ids
                    else:
                        auth_chats[chat_id] = []
                except ValueError as e:
                    LOGGER.error(f"Invalid chat ID format: {id_} - {e}")

        # Load sudo users
        if Config.SUDO_USERS:
            aid = Config.SUDO_USERS.split()
            for id_ in aid:
                try:
                    sudo_users.append(int(id_.strip()))
                except ValueError as e:
                    LOGGER.error(f"Invalid sudo user ID: {id_} - {e}")

        # Load excluded extensions
        if Config.EXCLUDED_EXTENSIONS:
            fx = Config.EXCLUDED_EXTENSIONS.split()
            for x in fx:
                x = x.lstrip(".")
                excluded_extensions.append(x.strip().lower())

        # Load main Google Drive
        if Config.GDRIVE_ID:
            drives_names.append("Main")
            drives_ids.append(Config.GDRIVE_ID)
            index_urls.append(Config.INDEX_URL)

        # Load additional drives from file
        if await aiopath.exists(LIST_DRIVES_FILE):
            async with aiopen(LIST_DRIVES_FILE, "r+") as f:
                lines = await f.readlines()
                for line in lines:
                    temp = line.strip().split()
                    if len(temp) >= 2:
                        drives_ids.append(temp[1])
                        drives_names.append(temp[0].replace("_", " "))
                        if len(temp) > 2:
                            index_urls.append(temp[2].rstrip("/"))
                        else:
                            index_urls.append("")

        # Try to get BASE_URL from Heroku
        if Config.HEROKU_APP_NAME and Config.HEROKU_API_KEY:
            await fetch_heroku_base_url()
    
    except Exception as e:
        LOGGER.error(f"Error updating variables: {e}")
        raise


async def fetch_heroku_base_url() -> None:
    """Fetch BASE_URL from Heroku API."""
    headers = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": f"Bearer {Config.HEROKU_API_KEY}",
    }

    urls = [
        f"https://api.heroku.com/teams/apps/{Config.HEROKU_APP_NAME}",
        f"https://api.heroku.com/apps/{Config.HEROKU_APP_NAME}",
    ]

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        response.raise_for_status()
                        app_data = await response.json()
                        if web_url := app_data.get("web_url"):
                            Config.set("BASE_URL", web_url.rstrip("/"))
                            LOGGER.info(f"BASE_URL set from Heroku: {web_url}")
                            return
                except aiohttp.ClientResponseError as e:
                    if e.status == 401:
                        LOGGER.warning(
                            "Heroku API 401 Unauthorized: Invalid HEROKU_API_KEY or HEROKU_APP_NAME!"
                        )
                    else:
                        LOGGER.warning(f"BASE_URL Heroku response error: {e}")
                    continue
                except aiohttp.ClientError as e:
                    LOGGER.warning(f"BASE_URL network error: {e}")
                    continue
    except Exception as e:
        LOGGER.error(f"BASE_URL error: {e}")


async def load_configurations() -> None:
    """Performs initial setup for configurations like .netrc,
    starts the Gunicorn web server, extracts JDownloader config if present,
    loads shorteners, and sets up service accounts if accounts.zip exists.
    """
    try:
        # Install truelink dependency
        LOGGER.info("Installing truelink dependency...")
        process = await create_subprocess_shell("uv pip install -U truelink")
        await process.wait()
        if process.returncode != 0:
            LOGGER.warning("Failed to install truelink, continuing anyway")

        # Setup .netrc file
        if not await aiopath.exists(NETRC_FILE):
            async with aiopen(NETRC_FILE, "w"):
                pass
            LOGGER.info(".netrc file created")
        
        aria_setup = await create_subprocess_shell(
            "chmod 600 .netrc && cp .netrc /root/.netrc && chmod +x aria.sh && ./aria.sh"
        )
        await aria_setup.wait()
        LOGGER.info("Aria2 setup completed")

        # Start web server
        PORT = int(environ.get("PORT") or environ.get("BASE_URL_PORT") or "80")
        await create_subprocess_shell(
            f"gunicorn -k uvicorn.workers.UvicornWorker -w 1 web.wserver:app --bind 0.0.0.0:{PORT}"
        )
        LOGGER.info(f"Gunicorn web server started on port {PORT}")

        # Extract JDownloader config if exists
        if await aiopath.exists(CFG_ZIP):
            jd_cfg_path = "/JDownloader/cfg"
            await safe_remove_tree(jd_cfg_path)
            extract_cfg = await create_subprocess_exec("7z", "x", CFG_ZIP, "-o/JDownloader")
            await extract_cfg.wait()
            if extract_cfg.returncode == 0:
                LOGGER.info("JDownloader config extracted successfully")
            else:
                LOGGER.warning("Failed to extract JDownloader config")

        # Load shorteners
        if await aiopath.exists(SHORTENERS_FILE):
            async with aiopen(SHORTENERS_FILE) as f:
                lines = await f.readlines()
                for line in lines:
                    temp = line.strip().split()
                    if len(temp) == 2:
                        shorteners_list.append({"domain": temp[0], "api_key": temp[1]})
            LOGGER.info(f"Loaded {len(shorteners_list)} shorteners")

        # Setup service accounts
        if await aiopath.exists(ACCOUNTS_ZIP):
            await safe_remove_tree(ACCOUNTS_DIR)
            
            extract_accounts = await create_subprocess_exec(
                "7z", "x", "-o.", "-aoa", ACCOUNTS_ZIP, "accounts/*.json"
            )
            await extract_accounts.wait()
            
            if extract_accounts.returncode == 0:
                chmod_accounts = await create_subprocess_exec("chmod", "-R", "777", ACCOUNTS_DIR)
                await chmod_accounts.wait()
                await safe_remove_file(ACCOUNTS_ZIP)
                LOGGER.info("Service accounts extracted and configured")
            else:
                LOGGER.warning("Failed to extract service accounts")

        # Disable service accounts if accounts directory doesn't exist
        if not await aiopath.exists(ACCOUNTS_DIR):
            Config.USE_SERVICE_ACCOUNTS = False
            LOGGER.info("Service accounts disabled (no accounts directory found)")
    
    except Exception as e:
        LOGGER.error(f"Error loading configurations: {e}")
        raise


def parse_command(text: str, commands: list) -> bool:
    """Check if text starts with any of the given commands.
    
    Args:
        text: The command text to check
        commands: List of command strings to match against
    
    Returns:
        True if text starts with any command, False otherwise
    """
    if isinstance(commands, str):
        commands = [commands]
    return any(text.startswith(f"/{cmd}") for cmd in commands)


async def check_resume_tasks() -> None:
    """Check and resume incomplete tasks from database if AUTO_RESUME is enabled."""
    if not Config.AUTO_RESUME or not database.db:
        LOGGER.info("Auto-resume disabled or database not available")
        return

    try:
        config = await database.db.settings.config.find_one(
            {"_id": TgClient.ID},
            {"resume_tasks": 1},
        )
        
        resume_data = None
        
        if not config or "resume_tasks" not in config:
            if not await database.db.tasks[TgClient.ID].find_one():
                LOGGER.info("No tasks found to resume")
                return
            resume_data = [
                doc async for doc in database.db.tasks[TgClient.ID].find({})
            ]
        else:
            resume_data = config["resume_tasks"]

        if not resume_data:
            LOGGER.info("No resume data available")
            return

        LOGGER.info(f"Found {len(resume_data)} tasks to resume. Resuming...")

        from bot.modules.mirror_leech import Mirror
        from bot.modules.clone import Clone
        from bot.modules.encode import Encode
        from bot.helper.telegram_helper.bot_commands import BotCommands

        # Mock classes for task resumption
        class MockChat:
            def __init__(self, id):
                self.id = id

        class MockUser:
            def __init__(self, id):
                self.id = id
                self.is_bot = False

        class MockMessage:
            def __init__(self, text, chat_id, user_id):
                self.text = text
                self.chat = MockChat(chat_id)
                if user_id:
                    self.from_user = MockUser(user_id)
                    self.sender_chat = None
                else:
                    self.from_user = None
                    self.sender_chat = MockChat(chat_id)
                self.reply_to_message = None

        # Process each task
        for task in resume_data:
            try:
                text = task.get("text", "")
                chat_id = task.get("cid") or task.get("chat_id")
                user_id = task.get("user_id")
                
                if not text or not chat_id:
                    LOGGER.warning(f"Invalid task data: {task}")
                    continue
                
                message = MockMessage(text, chat_id, user_id)
                
                # Normalize command lists
                clone_cmds = BotCommands.CloneCommand if isinstance(BotCommands.CloneCommand, list) else [BotCommands.CloneCommand]
                encode_cmds = BotCommands.EncodeCommand if isinstance(BotCommands.EncodeCommand, list) else [BotCommands.EncodeCommand]
                
                # Handle Clone command
                if parse_command(text, clone_cmds):
                    await Clone(TgClient.bot, message).new_event()
                    LOGGER.info(f"Resumed clone task: {text[:50]}")
                
                # Handle Encode command
                elif parse_command(text, encode_cmds):
                    await Encode(TgClient.bot, message).new_event()
                    LOGGER.info(f"Resumed encode task: {text[:50]}")
                
                # Handle Mirror/Leech commands
                elif (parse_command(text, BotCommands.LeechCommand) or
                      parse_command(text, BotCommands.MirrorCommand) or
                      parse_command(text, BotCommands.JdMirrorCommand) or
                      parse_command(text, BotCommands.JdLeechCommand) or
                      parse_command(text, BotCommands.NzbMirrorCommand) or
                      parse_command(text, BotCommands.NzbLeechCommand) or
                      parse_command(text, BotCommands.YtdlCommand) or
                      parse_command(text, BotCommands.YtdlLeechCommand)):
                    
                    # Determine task type
                    c_text = text.split()[0].lstrip("/")
                    
                    is_leech = (parse_command(text, BotCommands.LeechCommand) or
                               parse_command(text, BotCommands.JdLeechCommand) or
                               parse_command(text, BotCommands.NzbLeechCommand) or
                               parse_command(text, BotCommands.YtdlLeechCommand))
                    
                    is_jd = (parse_command(text, BotCommands.JdMirrorCommand) or
                            parse_command(text, BotCommands.JdLeechCommand))
                    
                    is_nzb = (parse_command(text, BotCommands.NzbMirrorCommand) or
                             parse_command(text, BotCommands.NzbLeechCommand))
                    
                    await Mirror(
                        TgClient.bot,
                        message,
                        is_leech=is_leech,
                        is_jd=is_jd,
                        is_nzb=is_nzb
                    ).new_event()
                    LOGGER.info(f"Resumed mirror/leech task: {text[:50]}")
                
                else:
                    LOGGER.warning(f"Unknown command type for task: {text[:50]}")
            
            except Exception as e:
                LOGGER.error(f"Error resuming task '{text[:50] if 'text' in task else 'unknown'}': {e}")
                continue

        # Clear resume tasks from database
        await database.db.settings.config.update_one(
            {"_id": TgClient.ID},
            {"$unset": {"resume_tasks": ""}},
        )
        LOGGER.info("Resume tasks cleared from database")

    except Exception as e:
        LOGGER.error(f"Error in check_resume_tasks: {e}")