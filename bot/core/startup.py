from asyncio import (
    create_subprocess_exec,
    create_subprocess_shell,
    create_task,
    sleep,
)
from os import environ
from time import time

from aiofiles import open as aiopen
from aiofiles.os import makedirs, remove
from aiofiles.os import path as aiopath
from aioshutil import rmtree  # type: ignore

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
from sabnzbdapi.exception import APIConnectionError, APIError

from .aeon_client import TgClient
from .config_manager import Config
from .torrent_manager import TorrentManager


async def update_qb_options():
    if not qbit_options:
        opt = await TorrentManager.qbittorrent.app.preferences()
        qbit_options.update(opt)
        del qbit_options["listen_port"]
        for k in list(qbit_options.keys()):
            if k.startswith("rss"):
                del qbit_options[k]
        # Set username to 'admin' and password to LOGIN_PASS (or 'admin' if not set)
        username = "admin"
        password = Config.LOGIN_PASS or "admin"
        qbit_options["web_ui_username"] = username
        qbit_options["web_ui_password"] = password
        await TorrentManager.qbittorrent.app.set_preferences(
            {"web_ui_username": username, "web_ui_password": password},
        )
    else:
        await TorrentManager.qbittorrent.app.set_preferences(qbit_options)


async def update_aria2_options():
    if not aria2_options:
        op = await TorrentManager.aria2.getGlobalOption()
        aria2_options.update(op)
    else:
        await TorrentManager.aria2.changeGlobalOption(aria2_options)


async def update_nzb_options():
    try:
        if sabnzbd_client is None:
            return

        # Try to connect to SABnzbd with a timeout
        try:
            # First check if SABnzbd is responding at all
            status_response = await sabnzbd_client.call(
                {"mode": "version"},
                requests_args={"timeout": 5},
            )
            if not status_response:
                return
        except Exception:
            return

        # Now try to get the config
        try:
            config_response = await sabnzbd_client.get_config()
            if (
                config_response
                and isinstance(config_response, dict)
                and "config" in config_response
                and "misc" in config_response["config"]
            ):
                no = config_response["config"]["misc"]
                nzb_options.update(no)
                LOGGER.info("Successfully updated NZB options")
            else:
                pass
        except Exception:
            pass
    except APIError as e:
        LOGGER.error(f"SABnzbd API error: {e}")
        # Continue with the bot startup even if NZB options update fails
    except APIConnectionError as e:
        LOGGER.error(f"SABnzbd connection error: {e}")
        # Continue with the bot startup even if NZB options update fails
    except Exception as e:
        LOGGER.error(f"Error updating NZB options: {e}")
        # Continue with the bot startup even if NZB options update fails


async def load_settings():
    if not Config.DATABASE_URL:
        return
    for p in ["thumbnails", "tokens", "rclone", "cookies"]:
        if await aiopath.exists(p):
            await rmtree(p, ignore_errors=True)
    await database.connect()
    if database.db is not None:
        # Process any pending message deletions
        await process_pending_deletions()

        # Use TgClient.ID for consistency across the codebase
        current_deploy_config = Config.get_all()
        old_deploy_config = await database.db.settings.deployConfig.find_one(
            {"_id": TgClient.ID},
            {"_id": 0},
        )

        if old_deploy_config is None:
            await database.db.settings.deployConfig.replace_one(
                {"_id": TgClient.ID},
                current_deploy_config,
                upsert=True,
            )
        elif old_deploy_config != current_deploy_config:
            runtime_config = (
                await database.db.settings.config.find_one(
                    {"_id": TgClient.ID},
                    {"_id": 0},
                )
                or {}
            )

            # Find all variables that are new or have changed values
            changed_vars = {}
            for k, v in current_deploy_config.items():
                # Add new variables or update variables with changed values
                if k not in runtime_config or runtime_config.get(k) != v:
                    changed_vars[k] = v

            if changed_vars:
                # Update runtime configuration with all changed variables
                runtime_config.update(changed_vars)
                await database.db.settings.config.replace_one(
                    {"_id": TgClient.ID},
                    runtime_config,
                    upsert=True,
                )
                LOGGER.info(f"Updated variables from config.py: {list(changed_vars.keys())}")

            # Update the deploy config with the current config
            await database.db.settings.deployConfig.replace_one(
                {"_id": TgClient.ID},
                current_deploy_config,
                upsert=True,
            )

        runtime_config = await database.db.settings.config.find_one(
            {"_id": TgClient.ID},
            {"_id": 0},
        )
        if runtime_config:
            Config.load_dict(runtime_config)

        if pf_dict := await database.db.settings.files.find_one(
            {"_id": TgClient.ID},
            {"_id": 0},
        ):
            for key, value in pf_dict.items():
                if value:
                    file_ = key.replace("__", ".")
                    async with aiopen(file_, "wb+") as f:
                        await f.write(value)

        if a2c_options := await database.db.settings.aria2c.find_one(
            {"_id": TgClient.ID},
            {"_id": 0},
        ):
            aria2_options.update(a2c_options)

        if qbit_opt := await database.db.settings.qbittorrent.find_one(
            {"_id": TgClient.ID},
            {"_id": 0},
        ):
            qbit_options.update(qbit_opt)

        # Load SABnzbd config if it exists in the database
        try:
            if nzb_opt := await database.db.settings.nzb.find_one(
                {"_id": TgClient.ID},
                {"_id": 0},
            ):
                # Make sure the sabnzbd directory exists
                try:
                    if not await aiopath.exists("sabnzbd"):
                        await makedirs("sabnzbd")

                    # Remove backup file if it exists
                    if await aiopath.exists("sabnzbd/SABnzbd.ini.bak"):
                        await remove("sabnzbd/SABnzbd.ini.bak")

                    # Extract the key-value pair from the database
                    if len(nzb_opt) > 0:
                        ((key, value),) = nzb_opt.items()
                        file_ = key.replace("__", ".")

                        # Write the config file
                        async with aiopen(f"sabnzbd/{file_}", "wb+") as f:
                            await f.write(value)
                        LOGGER.info("SABnzbd configuration loaded from database")
                    else:
                        pass
                except Exception:
                    pass
        except Exception as e:
            LOGGER.error(f"Error loading SABnzbd configuration from database: {e}")

        if await database.db.users.find_one():
            for p in ["thumbnails", "tokens", "rclone", "cookies"]:
                if not await aiopath.exists(p):
                    await makedirs(p)

            # Set secure permissions for cookies directory
            if await aiopath.exists("cookies"):
                await create_subprocess_exec("chmod", "700", "cookies")
            rows = database.db.users.find({})
            async for row in rows:
                uid = row["_id"]
                del row["_id"]
                thumb_path = f"thumbnails/{uid}.jpg"
                rclone_config_path = f"rclone/{uid}.conf"
                token_path = f"tokens/{uid}.pickle"
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
                # Load user cookies if available
                cookies_path = f"cookies/{uid}.txt"
                if row.get("USER_COOKIES"):
                    async with aiopen(cookies_path, "wb+") as f:
                        await f.write(row["USER_COOKIES"])
                    row["USER_COOKIES"] = cookies_path
                    # Set secure permissions for individual cookie files
                    await create_subprocess_exec("chmod", "600", cookies_path)
                    # Silently load user cookies without logging
                user_data[uid] = row
            LOGGER.info("Users data has been imported from Database")

        # Convert TgClient.ID to string for collection name
        if await database.db.rss[str(TgClient.ID)].find_one():
            rows = database.db.rss[str(TgClient.ID)].find({})
            async for row in rows:
                user_id = row["_id"]
                del row["_id"]
                rss_dict[user_id] = row
            LOGGER.info("Rss data has been imported from Database.")


async def save_settings():
    if database.db is None:
        return
    config_dict = Config.get_all()
    await database.db.settings.config.replace_one(
        {"_id": TgClient.ID},
        config_dict,
        upsert=True,
    )
    if await database.db.settings.aria2c.find_one({"_id": TgClient.ID}) is None:
        await database.db.settings.aria2c.update_one(
            {"_id": TgClient.ID},
            {"$set": aria2_options},
            upsert=True,
        )
    if await database.db.settings.qbittorrent.find_one({"_id": TgClient.ID}) is None:
        await database.save_qbit_settings()
    # Save SABnzbd config if it exists and hasn't been saved before
    try:
        if await database.db.settings.nzb.find_one({"_id": TgClient.ID}) is None:
            try:
                if await aiopath.exists("sabnzbd/SABnzbd.ini"):
                    try:
                        async with aiopen("sabnzbd/SABnzbd.ini", "rb+") as pf:
                            nzb_conf = await pf.read()

                        if nzb_conf:  # Make sure we have actual content
                            await database.db.settings.nzb.update_one(
                                {"_id": TgClient.ID},
                                {"$set": {"SABnzbd__ini": nzb_conf}},
                                upsert=True,
                            )
                            LOGGER.info("SABnzbd configuration saved to database")
                        else:
                            pass
                    except Exception:
                        pass
                else:
                    LOGGER.info(
                        "SABnzbd configuration file not found, skipping save",
                    )
            except Exception:
                pass
    except Exception as e:
        LOGGER.error(f"Error saving SABnzbd configuration to database: {e}")


async def update_variables():
    # Calculate max split size based on owner's session only
    max_split_size = (
        TgClient.MAX_SPLIT_SIZE
        if hasattr(Config, "USER_SESSION_STRING") and Config.USER_SESSION_STRING
        else 2097152000
    )

    # Set default leech split size to max split size based on owner session premium status
    # Only if not explicitly set by owner or if it exceeds max split size
    if (
        not Config.LEECH_SPLIT_SIZE  # Not set
        or max_split_size < Config.LEECH_SPLIT_SIZE  # Exceeds max allowed
        or Config.LEECH_SPLIT_SIZE == 2097152000  # Default value, not custom
    ):
        Config.LEECH_SPLIT_SIZE = max_split_size

    Config.HYBRID_LEECH = bool(Config.HYBRID_LEECH and TgClient.IS_PREMIUM_USER)
    Config.USER_TRANSMISSION = bool(
        Config.USER_TRANSMISSION and TgClient.IS_PREMIUM_USER,
    )

    if Config.AUTHORIZED_CHATS:
        aid = Config.AUTHORIZED_CHATS.split()
        for id_ in aid:
            chat_id, *thread_ids = id_.split("|")
            chat_id = int(chat_id.strip())
            if thread_ids:
                thread_ids = [int(x.strip()) for x in thread_ids]
                auth_chats[chat_id] = thread_ids
            else:
                auth_chats[chat_id] = []

    if Config.SUDO_USERS:
        aid = Config.SUDO_USERS.split()
        for id_ in aid:
            sudo_users.append(int(id_.strip()))

    if Config.EXCLUDED_EXTENSIONS:
        fx = Config.EXCLUDED_EXTENSIONS.split()
        for x in fx:
            x = x.lstrip(".")
            excluded_extensions.append(x.strip().lower())

    if Config.GDRIVE_ID:
        drives_names.append("Main")
        drives_ids.append(Config.GDRIVE_ID)
        index_urls.append(Config.INDEX_URL)

    if await aiopath.exists("list_drives.txt"):
        async with aiopen("list_drives.txt", "r+") as f:
            lines = await f.readlines()
            for line in lines:
                temp = line.split()
                drives_ids.append(temp[1])
                drives_names.append(temp[0].replace("_", " "))
                if len(temp) > 2:
                    index_urls.append(temp[2])
                else:
                    index_urls.append("")


async def load_configurations():
    if not await aiopath.exists(".netrc"):
        async with aiopen(".netrc", "w"):
            pass
    await (
        await create_subprocess_shell(
            "chmod 600 .netrc && cp .netrc /root/.netrc && chmod +x aria.sh && ./aria.sh",
        )
    ).wait()

    # First, kill any running web server processes regardless of configuration
    try:
        LOGGER.info("Killing any existing web server processes...")
        await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
    except Exception as e:
        LOGGER.error(f"Error killing web server processes: {e}")

    # Check if web server should be started (BASE_URL_PORT = 0 means disabled)
    if Config.BASE_URL_PORT == 0:
        LOGGER.info("Web server is disabled (BASE_URL_PORT = 0)")
        # Double-check to make sure no web server is running
        try:
            # Use pgrep to check if any gunicorn processes are still running
            process = await create_subprocess_exec(
                "pgrep", "-f", "gunicorn",
                stdout=-1
            )
            stdout, _ = await process.communicate()
            if stdout:
                LOGGER.warning("Gunicorn processes still detected, attempting to kill again...")
                await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
        except Exception as e:
            LOGGER.error(f"Error checking for gunicorn processes: {e}")
    else:
        # Use Config.BASE_URL_PORT instead of environment variable
        # Explicitly convert to string to avoid any type issues
        PORT = environ.get("PORT") or str(Config.BASE_URL_PORT) or "80"
        LOGGER.info(f"Starting web server on port {PORT}")
        await create_subprocess_shell(
            f"gunicorn -k uvicorn.workers.UvicornWorker -w 1 web.wserver:app --bind 0.0.0.0:{PORT}",
        )

    if await aiopath.exists("cfg.zip"):
        if await aiopath.exists("/JDownloader/cfg"):
            await rmtree("/JDownloader/cfg", ignore_errors=True)
        await (
            await create_subprocess_exec("7z", "x", "cfg.zip", "-o/JDownloader")
        ).wait()

    if await aiopath.exists("shorteners.txt"):
        async with aiopen("shorteners.txt") as f:
            lines = await f.readlines()
            for line in lines:
                temp = line.strip().split()
                if len(temp) == 2:
                    shorteners_list.append({"domain": temp[0], "api_key": temp[1]})

    if await aiopath.exists("accounts.zip"):
        if await aiopath.exists("accounts"):
            await rmtree("accounts")
        await (
            await create_subprocess_exec(
                "7z",
                "x",
                "-o.",
                "-aoa",
                "accounts.zip",
                "accounts/*.json",
            )
        ).wait()
        await (await create_subprocess_exec("chmod", "-R", "777", "accounts")).wait()
        await remove("accounts.zip")

    if not await aiopath.exists("accounts"):
        Config.USE_SERVICE_ACCOUNTS = False


async def process_pending_deletions():
    """Process messages that were scheduled for deletion"""
    if database.db is None:
        LOGGER.info("Database is None, skipping pending deletions check")
        return

    # Check if TgClient.bot is initialized
    if not hasattr(TgClient, "bot") or TgClient.bot is None:
        # TgClient.bot not initialized yet, skipping pending deletions
        return

    # Check all scheduled deletions for debugging
    await database.get_all_scheduled_deletions()

    # Clean up old scheduled deletion entries once a day
    current_time = int(time())
    last_cleanup_time = getattr(process_pending_deletions, "last_cleanup_time", 0)
    if current_time - last_cleanup_time > 86400:  # 86400 seconds = 1 day
        await database.clean_old_scheduled_deletions(days=1)
        process_pending_deletions.last_cleanup_time = current_time

    pending_deletions = await database.get_pending_deletions()

    if not pending_deletions:
        return

    # Process each pending deletion individually
    success_count = 0
    fail_count = 0
    removed_from_db_count = 0

    for chat_id, msg_id, bot_id in pending_deletions:
        # Get the appropriate bot client
        bot_client = None
        if bot_id == TgClient.ID:
            bot_client = TgClient.bot
        elif hasattr(TgClient, "helper_bots") and bot_id in TgClient.helper_bots:
            bot_client = TgClient.helper_bots[bot_id]

        if bot_client is None:
            # Bot not found, skipping message
            fail_count += 1
            continue

        try:
            # Try to get the message first to verify it exists
            try:
                msg = await bot_client.get_messages(
                    chat_id=chat_id,
                    message_ids=int(msg_id),
                )

                if msg is None or getattr(msg, "empty", False):
                    # Message not found, removing from database
                    await database.remove_scheduled_deletion(chat_id, msg_id)
                    removed_from_db_count += 1
                    continue

                # Message found, will attempt to delete
            except Exception:
                # Error getting message, skipping
                continue

            # Make sure message_id is an integer
            message_id_int = int(msg_id)
            await bot_client.delete_messages(
                chat_id=chat_id,
                message_ids=[message_id_int],  # Pass as a list with a single item
            )
            # Successfully deleted the message
            success_count += 1
            # Remove from database after successful deletion
            await database.remove_scheduled_deletion(chat_id, msg_id)
            removed_from_db_count += 1
        except Exception as e:
            # Failed to delete message
            fail_count += 1
            # Check if it's a CHANNEL_INVALID or similar error
            if (
                "CHANNEL_INVALID" in str(e)
                or "CHAT_INVALID" in str(e)
                or "USER_INVALID" in str(e)
                or "PEER_ID_INVALID" in str(e)
            ):
                # Chat is invalid, removing from database
                # Remove from database since the chat is invalid
                await database.remove_scheduled_deletion(chat_id, msg_id)
                removed_from_db_count += 1

    # Log summary
    LOGGER.info(
        f"Auto-deletion results: {success_count} deleted, {fail_count} failed, {removed_from_db_count} removed from database",
    )


async def scheduled_deletion_checker():
    LOGGER.info("Scheduled deletion checker started")
    while True:
        try:
            await process_pending_deletions()
        except Exception as e:
            LOGGER.error(f"Error in scheduled deletion checker: {e}")
        await sleep(600)  # Check every 10 minutes


async def start_bot():
    # Only start the scheduled deletion checker after TgClient is initialized
    if hasattr(TgClient, "bot") and TgClient.bot is not None:
        LOGGER.info("Starting scheduled deletion checker")
        create_task(scheduled_deletion_checker())  # noqa: RUF006
    else:
        # Create a task to wait for TgClient.bot to be initialized and then start the checker
        create_task(wait_for_bot_and_start_checker())  # noqa: RUF006


async def wait_for_bot_and_start_checker():
    """Wait for TgClient.bot to be initialized and then start the scheduled deletion checker"""
    # Check less frequently to reduce resource usage
    # The bot initialization is a one-time event that happens during startup
    await sleep(60)  # Initial delay to allow bot to initialize normally

    # Check a few times with longer intervals
    for _ in range(5):  # Try 5 times
        if hasattr(TgClient, "bot") and TgClient.bot is not None:
            LOGGER.info(
                "TgClient.bot is now initialized, starting scheduled deletion checker",
            )
            create_task(scheduled_deletion_checker())  # noqa: RUF006
            return
        await sleep(60)  # Check every minute

    # If we get here, the bot still isn't initialized after 5 minutes
