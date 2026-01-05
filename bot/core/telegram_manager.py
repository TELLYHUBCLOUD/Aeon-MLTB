from asyncio import Lock

from pyrogram import Client, enums
try:
    from pyrogram.types import LinkPreviewOptions
except ImportError:
    LinkPreviewOptions = None


from bot import LOGGER

from .config_manager import Config


class TgClient:
    _lock = Lock()
    bot = None
    user = None
    NAME = ""
    ID = 0
    IS_PREMIUM_USER = False
    MAX_SPLIT_SIZE = 2097152000

    @classmethod
    async def start_bot(cls):
        LOGGER.info("Creating client from BOT_TOKEN")
        cls.ID = Config.BOT_TOKEN.split(":", 1)[0]
        kwargs = {
            "name": cls.ID,
            "api_id": Config.TELEGRAM_API,
            "api_hash": Config.TELEGRAM_HASH,
            "proxy": Config.TG_PROXY,
            "bot_token": Config.BOT_TOKEN,
            "workdir": "/app",
            "parse_mode": enums.ParseMode.HTML,
            "max_concurrent_transmissions": 100,
            "max_message_cache_size": 15000,
            "max_topic_cache_size": 15000,
            "sleep_threshold": 0,
        }
        if LinkPreviewOptions:
            kwargs["link_preview_options"] = LinkPreviewOptions(is_disabled=True)
        cls.bot = Client(**kwargs)
        await cls.bot.start()
        cls.NAME = cls.bot.me.username
        await cls.start_user()
        cls.IS_PREMIUM_USER = cls.bot.me.is_premium
        LOGGER.info("Bot Started")

    @classmethod
    async def start_user(cls):
        if Config.USER_SESSION_STRING:
            if cls.user is None:
                kwargs = {
                    "name": "User",
                    "api_id": Config.TELEGRAM_API,
                    "api_hash": Config.TELEGRAM_HASH,
                    "proxy": Config.TG_PROXY,
                    "session_string": Config.USER_SESSION_STRING,
                    "workdir": "/app",
                    "parse_mode": enums.ParseMode.HTML,
                    "no_updates": True,
                    "max_concurrent_transmissions": 100,
                    "max_message_cache_size": 15000,
                    "max_topic_cache_size": 15000,
                }
                if LinkPreviewOptions:
                    kwargs["link_preview_options"] = LinkPreviewOptions(is_disabled=True)
                cls.user = Client(**kwargs)
                await cls.user.start()
                cls.IS_PREMIUM_USER = cls.user.me.is_premium
                if cls.IS_PREMIUM_USER:
                    cls.MAX_SPLIT_SIZE = 4194304000

    @classmethod
    async def stop(cls):
        if cls.bot:
            await cls.bot.stop()
            cls.bot = None
            LOGGER.info("Bot client stopped.")

        if cls.user:
            await cls.user.stop()
            cls.user = None
            LOGGER.info("User client stopped.")

        cls.IS_PREMIUM_USER = False
        cls.MAX_SPLIT_SIZE = 2097152000

    @classmethod
    async def reload(cls):
        async with cls._lock:
            await cls.bot.restart()
            if cls.user:
                await cls.user.restart()
            LOGGER.info("Client restarted")
