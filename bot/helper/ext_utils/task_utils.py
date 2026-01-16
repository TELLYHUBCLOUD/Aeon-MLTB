from bot import LOGGER
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import arg_parser
from bot.helper.ext_utils.bulk_links import extract_bulk_links
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
)
from bot.core.config_manager import Config

async def task_init_helper(message):
    """
    Unifies task initialization for Mirror, Clone, Encode, and Merge modules.
    Handles message validation, error checks, argument parsing, and bulk link extraction.

    Args:
        message: The Pyrogram message object.

    Returns:
        tuple: (args, bulk, multi, input_list, is_bulk, bulk_start, bulk_end)
        If initialization fails, returns None.
    """
    # Check if message text exists
    if not message or not hasattr(message, "text") or message.text is None:
        LOGGER.error("Message text is None or message doesn't have text attribute")
        error_msg = "Invalid message format. Please make sure your message contains text."
        error = await send_message(message, error_msg)
        await auto_delete_message(error, time=300)
        return None

    text = message.text.split("\n")
    input_list = text[0].split(" ")

    # Check permissions and errors
    error_msg, error_button = await error_check(message)
    if error_msg:
        await delete_links(message)
        error = await send_message(message, error_msg, error_button)
        await auto_delete_message(error, time=300)
        return None

    # Base Arguments Dictionary
    args = {
        "-doc": False,
        "-med": False,
        "-d": False,
        "-j": False,
        "-s": False,
        "-b": False,
        "-e": False,
        "-z": False,
        "-sv": False,
        "-ss": False,
        "-f": False,
        "-fd": False,
        "-fu": False,
        "-hl": False,
        "-bt": False,
        "-ut": False,
        "-mt": False,
        "-merge-video": False,
        "-merge-audio": False,
        "-merge-subtitle": False,
        "-merge-all": False,
        "-merge-image": False,
        "-merge-pdf": False,
        "-i": 0,
        "-sp": 0,
        "link": "",
        "-n": "",
        "-m": "",
        "-watermark": "",
        "-iwm": "",
        "-up": "",
        "-rcf": "",
        "-au": "",
        "-ap": "",
        "-h": [],
        "-t": "",
        "-ca": "",
        "-cv": "",
        "-ns": "",
        "-md": "",
        "-metadata-title": "",
        "-metadata-author": "",
        "-metadata-comment": "",
        "-metadata-all": "",
        "-metadata-video-title": "",
        "-metadata-video-author": "",
        "-metadata-video-comment": "",
        "-metadata-audio-title": "",
        "-metadata-audio-author": "",
        "-metadata-audio-comment": "",
        "-metadata-subtitle-title": "",
        "-metadata-subtitle-author": "",
        "-metadata-subtitle-comment": "",
        "-tl": "",
        "-ff": set(),
        "-compress": False,
        "-comp-video": False,
        "-comp-audio": False,
        "-comp-image": False,
        "-comp-document": False,
        "-comp-subtitle": False,
        "-comp-archive": False,
        "-video-fast": False,
        "-video-medium": False,
        "-video-slow": False,
        "-audio-fast": False,
        "-audio-medium": False,
        "-audio-slow": False,
        "-image-fast": False,
        "-image-medium": False,
        "-image-slow": False,
        "-document-fast": False,
        "-document-medium": False,
        "-document-slow": False,
        "-subtitle-fast": False,
        "-subtitle-medium": False,
        "-subtitle-slow": False,
        "-archive-fast": False,
        "-archive-medium": False,
        "-archive-slow": False,
        "-trim": "",
        "-extract": False,
        "-extract-video": False,
        "-extract-audio": False,
        "-extract-subtitle": False,
        "-extract-attachment": False,
        "-extract-video-index": "",
        "-extract-audio-index": "",
        "-extract-subtitle-index": "",
        "-extract-attachment-index": "",
        "-extract-video-codec": "",
        "-extract-audio-codec": "",
        "-extract-subtitle-codec": "",
        "-extract-maintain-quality": "",
        "-extract-priority": "",
        "-remove": False,
        "-remove-video": False,
        "-remove-audio": False,
        "-remove-subtitle": False,
        "-remove-attachment": False,
        "-remove-metadata": False,
        "-remove-video-index": "",
        "-remove-audio-index": "",
        "-remove-subtitle-index": "",
        "-remove-attachment-index": "",
        "-remove-priority": "",
        "-add": False,
        "-add-video": False,
        "-add-audio": False,
        "-add-subtitle": False,
        "-add-attachment": False,
        "-del": "",
        "-preserve": False,
        "-replace": False,
        "-vi": "",
        "-ai": "",
        "-si": "",
        "-ati": "",
        "-rvi": "",
        "-rai": "",
        "-rsi": "",
        "-rati": "",
        "-swap": False,
        "-swap-audio": False,
        "-swap-video": False,
        "-swap-subtitle": False,
        "-lulu": False,
        "-buz": False,
        "-pix": False,
        "-q": "",
        "-an": False,
        "-sn": False,
        "-sync": False,
    }

    arg_parser(input_list[1:], args)

    try:
        multi = int(args["-i"])
    except Exception:
        multi = 0

    is_bulk = args["-b"]
    bulk_start = 0
    bulk_end = 0

    if not isinstance(is_bulk, bool):
        dargs = is_bulk.split(":")
        bulk_start = int(dargs[0]) if dargs[0] else 0
        if len(dargs) == 2:
            bulk_end = int(dargs[1]) if dargs[1] else 0
        is_bulk = True

    bulk = []
    if not is_bulk:
        bulk = await extract_bulk_links(message, bulk_start, bulk_end)
        if len(bulk) > 1:
            is_bulk = True

    return args, bulk, multi, input_list, is_bulk, bulk_start, bulk_end
