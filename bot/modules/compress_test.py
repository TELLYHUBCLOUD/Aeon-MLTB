"""
Simple test compress handler - MINIMAL VERSION
This will help us debug if the issue is with the command registration or the code itself
"""

from bot import LOGGER, bot_loop
from bot.helper.telegram_helper.message_utils import send_message


async def _test_compress(client, message):
    """Minimal test version of compress"""
    try:
        await send_message(message, "✅ Compress command is working!")
        LOGGER.info(f"Compress command triggered by user {message.from_user.id}")
    except Exception as e:
        LOGGER.error(f"Error in test_compress: {e}")


async def compress_handler(client, message):
    """Wrapper for compress command"""
    bot_loop.create_task(_test_compress(client, message))


async def compression_callback_handler(client, query):
    """Dummy callback handler"""
    await query.answer("Test callback")
