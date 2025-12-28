"""
Terabox Command Handler
Handles /terabox command to download and upload Terabox files.
"""

from bot import LOGGER
from bot.helper.aeon_utils.terabox_helper import get_terabox_direct_link
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import send_message
from bot.modules.mirror_leech import Mirror


@new_task
async def terabox_handler(client, message):
    """
    Handle /terabox command.
    Fetches direct link from Terabox API and starts leech.
    
    Usage: /terabox <terabox_link>
    """
    user_id = message.from_user.id
    input_text = message.text.split(maxsplit=1)
    
    # Check if link is provided
    if len(input_text) < 2:
        await send_message(
            message,
            "⚠️ <b>Usage:</b> <code>/terabox &lt;link&gt;</code>\n\n"
            "Send a Terabox link to download and upload to Telegram."
        )
        return
    
    terabox_url = input_text[1].strip()
    
    # Send processing message
    wait_msg = await send_message(message, "🔄 <b>Processing Terabox link...</b>")
    
    try:
        # Get direct download link from API
        result = await get_terabox_direct_link(terabox_url)
        
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            await wait_msg.edit(
                f"❌ <b>Failed to get download link</b>\n\n"
                f"<b>Error:</b> {error}"
            )
            return
        
        # Extract file info
        direct_link = result["download_link"]
        file_name = result["file_name"]
        file_size = result["file_size"]
        
        LOGGER.info(f"[{user_id}] Terabox: {file_name} ({file_size})")
        
        # Update message with file info
        await wait_msg.edit(
            f"✅ <b>Got file info:</b>\n\n"
            f"<b>Name:</b> <code>{file_name}</code>\n"
            f"<b>Size:</b> {file_size}\n\n"
            f"⏳ <b>Starting download...</b>"
        )
        
        # Create new message text for Mirror class
        # Format: /leech <direct_link>
        new_message_text = f"leech {direct_link}"
        message.text = new_message_text
        
        # Start mirror/leech process
        await Mirror(client, message, is_leech=True).new_event()
        
        # Delete processing message
        await wait_msg.delete()
        
    except Exception as e:
        LOGGER.error(f"Terabox handler error: {e}")
        await wait_msg.edit(
            f"❌ <b>Error processing Terabox link</b>\n\n"
            f"<code>{str(e)}</code>"
        )


def register_terabox_handlers(bot):
    """Register /terabox command handlers"""
    from pyrogram import filters
    from pyrogram.handlers import MessageHandler
    
    bot.add_handler(
        MessageHandler(
            terabox_handler,
            filters=filters.command(BotCommands.TeraboxCommand) & filters.incoming
        )
    )
    
    LOGGER.info("Terabox command handlers registered")
