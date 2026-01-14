from bot import LOGGER
from bot.core.config_manager import Config
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
)
from bot.helper.ext_utils.bot_utils import arg_parser
from bot.helper.ext_utils.bulk_links import extract_bulk_links

async def task_init_helper(listener, args):
    """
    Common initialization logic for tasks (Mirror, Clone, Encode, Merge).
    - Checks message validity.
    - Checks user permissions.
    - Parses arguments.
    - Handles bulk link extraction and initialization.

    Returns:
        tuple: (input_list, text) if task should proceed.
        None: If task was stopped (error or bulk init).
    """
    message = listener.message
    if not message or not hasattr(message, "text") or message.text is None:
        LOGGER.error("Message text is None or message doesn't have text attribute")
        error_msg = "Invalid message format. Please make sure your message contains text."
        error = await send_message(message, error_msg)
        await auto_delete_message(error, time=300)
        return None

    text = message.text.split("\n")
    input_list = text[0].split(" ")
    error_msg, error_button = await error_check(message)
    if error_msg:
        await delete_links(message)
        error = await send_message(message, error_msg, error_button)
        await auto_delete_message(error, time=300)
        return None

    # Parse arguments
    arg_parser(input_list[1:], args)

    # Bulk Handling
    is_bulk = args.get("-b", False)
    bulk_start = 0
    bulk_end = 0

    if not isinstance(is_bulk, bool):
        dargs = is_bulk.split(":")
        bulk_start = int(dargs[0]) if dargs[0] else 0
        if len(dargs) == 2:
            bulk_end = int(dargs[1]) if dargs[1] else 0
        is_bulk = True

    if is_bulk and not Config.BULK_ENABLED:
        await send_message(
            message, "❌ Bulk operations are disabled by the administrator."
        )
        return None

    if not is_bulk:
        # listener.bulk might already be populated (e.g. from reply)
        if hasattr(listener, "bulk") and not listener.bulk:
             listener.bulk = await extract_bulk_links(message, bulk_start, bulk_end)
             if len(listener.bulk) > 1:
                 is_bulk = True
                 if not Config.BULK_ENABLED:
                     await send_message(
                         message, "❌ Bulk operations are disabled by the administrator."
                     )
                     return None

    if is_bulk:
        await listener.init_bulk(input_list, bulk_start, bulk_end, listener.__class__)
        return None

    return input_list, text
