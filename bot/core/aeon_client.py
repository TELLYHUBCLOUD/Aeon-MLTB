from asyncio import Lock

from pyrogram import Client, enums

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
        cls.bot = Client(
            cls.ID,
            Config.TELEGRAM_API,
            Config.TELEGRAM_HASH,
            proxy=Config.TG_PROXY,
            bot_token=Config.BOT_TOKEN,
            workdir="/usr/src/app",
            parse_mode=enums.ParseMode.HTML,
            #    max_concurrent_transmissions=100,
        )
        await cls.bot.start()
        cls.NAME = cls.bot.me.username

    @classmethod
    async def start_user(cls):
        if Config.USER_SESSION_STRING:
            LOGGER.info("Creating client from USER_SESSION_STRING")
            try:
                cls.user = Client(
                    "user",
                    Config.TELEGRAM_API,
                    Config.TELEGRAM_HASH,
                    proxy=Config.TG_PROXY,
                    session_string=Config.USER_SESSION_STRING,
                    parse_mode=enums.ParseMode.HTML,
                    no_updates=True,
                    max_concurrent_transmissions=100,
                )
                await cls.user.start()
                cls.IS_PREMIUM_USER = cls.user.me.is_premium
                if cls.IS_PREMIUM_USER:
                    cls.MAX_SPLIT_SIZE = 4194304000
            except Exception as e:
                LOGGER.error(f"Failed to start client from USER_SESSION_STRING. {e}")
                cls.IS_PREMIUM_USER = False
                cls.user = None

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
