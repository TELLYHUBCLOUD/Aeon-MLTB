"""Auto Leech Handler - Automatically trigger leech operations when users send links or media.

This module intercepts incoming messages and triggers the leech command automatically
when auto_leech is enabled in user settings.
"""

import re
from asyncio import sleep

from pyrogram.types import Message

from bot import LOGGER, user_data
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.telegram_helper.filters import CustomFilters


# Regex pattern to detect URLs in messages
URL_PATTERN = re.compile(
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


async def extract_link_or_media(message: Message) -> str | None:
    """Extract URL from message text or get media representation.
    
    Args:
        message: The incoming Telegram message
        
    Returns:
        str: The extracted URL or media file_id, None if no link/media found
    """
    # Check for URLs in message text
    if message.text:
        urls = URL_PATTERN.findall(message.text)
        if urls:
            return urls[0]  # Return the first URL found
    
    # Check for URLs in message caption
    if message.caption:
        urls = URL_PATTERN.findall(message.caption)
        if urls:
            return urls[0]
    
    # Check for Telegram media
    if message.document:
        return f"telegram:{message.document.file_id}"
    if message.video:
        return f"telegram:{message.video.file_id}"
    if message.audio:
        return f"telegram:{message.audio.file_id}"
    if message.photo:
        # Photos are stored as a list, get the largest one
        return f"telegram:{message.photo[-1].file_id}"
    if message.animation:
        return f"telegram:{message.animation.file_id}"
    if message.voice:
        return f"telegram:{message.voice.file_id}"
    if message.video_note:
        return f"telegram:{message.video_note.file_id}"
    
    return None


def build_auto_leech_command(
    auto_leech_cmd: str,
    link_or_media: str,
    auto_compress_cmd: str = ""
) -> str:
    """Build the final leech command by replacing {i} placeholder.
    
    Args:
        auto_leech_cmd: The command template (e.g., "leech {i}")
        link_or_media: The incoming link or media to replace {i} with
        auto_compress_cmd: Optional compression command to append
        
    Returns:
        str: The final command string
    """
    # Replace {i} placeholder with the actual link/media
    command = auto_leech_cmd.replace("{i}", link_or_media)
    
    # Append auto compress command if provided
    if auto_compress_cmd and auto_compress_cmd.strip():
        command = f"{command} {auto_compress_cmd.strip()}"
    
    return command


async def should_process_message(message: Message, user_id: int) -> bool:
    """Check if message should trigger auto leech.
    
    Args:
        message: The incoming message
        user_id: The user ID
        
    Returns:
        bool: True if message should be processed, False otherwise
    """
    # Ignore bot messages
    if message.from_user and message.from_user.is_bot:
        LOGGER.debug(f"Auto leech: Ignoring bot message from {user_id}")
        return False
    
    # Ignore edited messages
    if message.edit_date:
        LOGGER.debug(f"Auto leech: Ignoring edited message from {user_id}")
        return False
    
    # Check if auto_leech is enabled for this user
    user_dict = user_data.get(user_id, {})
    auto_leech_enabled = user_dict.get("auto_leech", False)
    
    if not auto_leech_enabled:
        LOGGER.debug(f"Auto leech: Disabled for user {user_id}")
        return False
    
    LOGGER.info(f"Auto leech: Enabled for user {user_id}, processing message")
    return True


async def trigger_auto_leech(client, message: Message):
    """Main handler to trigger automatic leech operation.
    
    This function:
    1. Checks if auto leech should be triggered
    2. Extracts link or media from message
    3. Builds the leech command
    4. Creates a modified message object
    5. Calls the existing Mirror/leech handler
    
    Args:
        client: The Pyrogram client
        message: The incoming message
    """
    try:
        user_id = message.from_user.id if message.from_user else message.sender_chat.id
        
        # Check if we should process this message
        if not await should_process_message(message, user_id):
            return
        
        # Extract link or media
        link_or_media = await extract_link_or_media(message)
        if not link_or_media:
            LOGGER.debug(f"Auto leech: No link or media found in message from {user_id}")
            return
        
        LOGGER.info(f"Auto leech: Found link/media: {link_or_media[:50]}...")
        
        # Get user settings
        user_dict = user_data.get(user_id, {})
        auto_leech_cmd = user_dict.get("auto_leech_cmd", "leech {i}")
        auto_compress_cmd = user_dict.get("auto_compress_cmd", "")
        
        # Build the command
        command_text = build_auto_leech_command(
            auto_leech_cmd,
            link_or_media,
            auto_compress_cmd
        )
        
        LOGGER.info(f"Auto leech: Built command: {command_text}")
        
        # Create a modified message object
        # We'll modify the message text to contain the built command
        modified_message = message
        
        # For Telegram media, we need to keep the media reference
        # but change the text/caption to the command
        if link_or_media.startswith("telegram:"):
            # For media messages, we set the caption to the command
            # The Mirror class will handle media download from the message
            if message.caption:
                modified_message.caption = command_text
            else:
                # Add a text field if it doesn't exist
                modified_message.text = command_text
        else:
            # For URL messages, replace the text with the command
            modified_message.text = command_text
        
        # Import Mirror class here to avoid circular imports
        from bot.modules.mirror_leech import Mirror
        
        # Log that we're triggering auto leech
        LOGGER.info(f"Auto leech: Triggering leech for user {user_id}")
        
        # Call the existing Mirror/leech handler
        # Use sync_to_async to properly await the coroutine
        await Mirror(
            client,
            modified_message,
            is_leech=True
        ).new_event()
        
    except Exception as e:
        LOGGER.error(f"Auto leech: Error processing message: {e}", exc_info=True)
        # Don't notify user about auto leech errors to avoid spam
        # Just log the error and continue


# This function will be registered as a message handler
async def auto_leech_message_handler(client, message: Message):
    """Message handler that will be registered with Pyrogram.
    
    This handler runs on every text/media message from authorized users.
    """
    # Add a small delay to avoid race conditions with other handlers
    await sleep(0.1)
    
    # Trigger auto leech
    await trigger_auto_leech(client, message)
