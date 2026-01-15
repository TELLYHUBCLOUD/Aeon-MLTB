from bot import LOGGER
from bot.helper.telegram_helper.message_utils import send_message, auto_delete_message, delete_links
from bot.helper.aeon_utils.access_check import error_check

async def task_init_helper(message):
    """
    Performs common initialization checks for tasks.
    Returns (text, input_list) or (None, None) if validation fails.
    """
    if not message or not hasattr(message, "text") or message.text is None:
        LOGGER.error("Message text is None or message doesn't have text attribute")
        error_msg = "Invalid message format. Please make sure your message contains text."
        error = await send_message(message, error_msg)
        await auto_delete_message(error, time=300)
        return None, None

    text = message.text.split("\n")
    input_list = text[0].split(" ")

    error_msg, error_button = await error_check(message)
    if error_msg:
        await delete_links(message)
        error = await send_message(message, error_msg, error_button)
        await auto_delete_message(error, time=300)
        return None, None

    return text, input_list
