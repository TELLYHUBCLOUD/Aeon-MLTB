from bot import bot_loop
from bot.core.config_manager import Config
from bot.helper.telegram_helper.message_utils import send_message
from bot.modules.mirror_leech import Mirror


async def enc_command(client, message):
    if not Config.LEECH_ENABLED:
        await send_message(
            message, "❌ Leech operations are disabled by the administrator."
        )
        return
    bot_loop.create_task(
        Mirror(client, message, is_leech=True, is_enc=True).new_event()
    )
