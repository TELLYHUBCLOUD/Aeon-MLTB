from bot import LOGGER
from bot.core.config_manager import Config
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import arg_parser
from bot.helper.ext_utils.bulk_links import extract_bulk_links
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
)

def _get_default_args(task_type):
    """
    Returns the default argument dictionary for the specified task type.
    """
    args = {
        "link": "",
        "-i": 0,
        "-b": False,
        "-n": "",
        "-up": "",
        "-rcf": "",
    }

    if task_type == 'Mirror':
        args.update({
            "-doc": False,
            "-med": False,
            "-d": False,
            "-j": False,
            "-s": False,
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
            "-sp": 0,
            "-m": "",
            "-watermark": "",
            "-iwm": "",
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
        })
    elif task_type == 'Clone':
        args.update({
            "-sync": False,
        })
    elif task_type == 'Encode':
         args.update({
            "-q": "",
            "-an": False,
            "-sn": False,
        })

    return args

async def task_init_helper(listener, task_type):
    """
    Common initialization logic for Mirror, Clone, and Encode tasks.

    Args:
        listener: The task listener instance.
        task_type: 'Mirror', 'Clone', or 'Encode'.

    Returns:
        tuple: (args, input_list, is_bulk, bulk, valid)
        valid is False if initialization failed (e.g. error message sent).
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
        return None, None, False, [], False

    text = listener.message.text.split("\n")
    input_list = text[0].split(" ")

    error_msg, error_button = await error_check(listener.message)
    if error_msg:
        await delete_links(listener.message)
        error = await send_message(listener.message, error_msg, error_button)
        await auto_delete_message(error, time=300)
        return None, None, False, [], False

    args = _get_default_args(task_type)

    if hasattr(listener, 'auto_link') and listener.auto_link:
        if not any(x.startswith("http") or "magnet" in x for x in input_list):
             input_list.append(listener.auto_link)

    if hasattr(listener, 'auto_ff') and listener.auto_ff:
         user_ff = any(item.strip() == "-ff" for item in input_list)
         if not user_ff:
              input_list.extend(listener.auto_ff.split())

    arg_parser(input_list[1:], args)

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
        bulk = await extract_bulk_links(listener.message, bulk_start, bulk_end)
        if len(bulk) > 1:
            is_bulk = True
    elif is_bulk and not Config.BULK_ENABLED:
         await send_message(
            listener.message, "❌ Bulk operations are disabled by the administrator."
         )
         is_bulk = False

    return args, input_list, is_bulk, bulk, True
