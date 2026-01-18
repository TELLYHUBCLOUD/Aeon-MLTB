from bot import LOGGER
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import arg_parser
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
)

async def task_init_helper(listener, args):
    """
    Centralized initialization helper for task listeners.
    Handles:
    - Message validation
    - Error checking (permissions, etc.)
    - Auto Link / Auto FF injection
    - Argument parsing

    Returns:
        input_list (list): The split command arguments, or None if failed.
    """
    if (
        not listener.message
        or not hasattr(listener.message, "text")
        or listener.message.text is None
    ):
        LOGGER.error(
            "Message text is None or message doesn't have text attribute"
        )
        error_msg = "Invalid message format. Please make sure your message contains text."
        error = await send_message(listener.message, error_msg)
        await auto_delete_message(error, time=300)
        return None

    text = listener.message.text.split("\n")
    input_list = text[0].split(" ")

    error_msg, error_button = await error_check(listener.message)
    if error_msg:
        await delete_links(listener.message)
        error = await send_message(listener.message, error_msg, error_button)
        await auto_delete_message(error, time=300)
        return None

    # Handle Auto Link Injection
    if hasattr(listener, "auto_link") and listener.auto_link:
        if not any(x.startswith("http") or "magnet" in x for x in input_list):
            input_list.append(listener.auto_link)

    # Handle Auto FFmpeg Injection
    if hasattr(listener, "auto_ff") and listener.auto_ff:
        user_ff = any(item.strip() == "-ff" for item in input_list)
        if not user_ff:
            input_list.extend(listener.auto_ff.split())

    # Parse Arguments
    arg_parser(input_list[1:], args)

    return input_list
