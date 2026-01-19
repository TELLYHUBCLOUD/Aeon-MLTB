from bot import LOGGER, task_dict_lock, bot_loop
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import arg_parser, is_flag_enabled
from bot.helper.ext_utils.bulk_links import extract_bulk_links
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
)

async def task_init_helper(listener):
    """
    Consolidated task initialization helper.
    Returns:
        tuple: (input_list, args, is_bulk, bulk_start, bulk_end) or None if error/handled.
    """
    if hasattr(listener, "_ensure_user_dict"):
        listener._ensure_user_dict()

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

    args = _get_default_args(listener)

    if getattr(listener, "auto_link", None):
        if not any(x.startswith("http") or "magnet" in x for x in input_list):
            input_list.append(listener.auto_link)

    if getattr(listener, "auto_ff", None):
        user_ff = any(item.strip() == "-ff" for item in input_list)
        if not user_ff:
             input_list.extend(listener.auto_ff.split())

    arg_parser(input_list[1:], args)

    for flag in list(args.keys()):
        if flag.startswith("-") and not is_flag_enabled(flag):
            if isinstance(args[flag], bool):
                args[flag] = False
            elif isinstance(args[flag], set):
                args[flag] = set()
            elif isinstance(args[flag], str):
                args[flag] = ""
            elif isinstance(args[flag], int):
                args[flag] = 0

    is_bulk = args.get("-b", False)
    bulk_start = 0
    bulk_end = 0

    if not isinstance(is_bulk, bool):
        dargs = is_bulk.split(":")
        bulk_start = int(dargs[0]) if dargs[0] else 0
        if len(dargs) == 2:
            bulk_end = int(dargs[1]) if dargs[1] else 0
        is_bulk = True

    if not is_bulk and (not hasattr(listener, "bulk") or len(listener.bulk) == 0):
        listener.bulk = await extract_bulk_links(message, bulk_start, bulk_end)
        if len(listener.bulk) > 1:
            is_bulk = True

    return input_list, args, is_bulk, bulk_start, bulk_end

def _get_default_args(listener):
    args = {
        "link": "",
        "-i": 0,
        "-b": False,
        "-n": "",
        "-up": "",
        "-rcf": "",
    }

    is_mirror = listener.__class__.__name__ == "Mirror"
    is_clone = listener.__class__.__name__ == "Clone"
    is_encode = listener.__class__.__name__ == "Encode"
    is_merge = listener.__class__.__name__ == "Merge"

    if is_clone:
        args["-sync"] = False
        return args

    if is_encode:
        args["-q"] = ""
        args["-an"] = False
        args["-sn"] = False
        return args

    if is_merge:
        return args

    if is_mirror:
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
        return args

    return args
