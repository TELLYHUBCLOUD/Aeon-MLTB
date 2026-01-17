from bot import LOGGER
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import arg_parser
from bot.helper.ext_utils.bulk_links import extract_bulk_links
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
)
from bot.helper.ext_utils.links_utils import is_url, is_telegram_link, is_magnet, is_rclone_path, is_gdrive_id, is_gdrive_link, is_mega_link
from re import search as re_search

async def task_init_helper(listener):
    message = listener.message
    client = listener.client

    if not message or not hasattr(message, "text") or message.text is None:
        LOGGER.error("Message text is None or message doesn't have text attribute")
        error_msg = "Invalid message format. Please make sure your message contains text."
        error = await send_message(message, error_msg)
        await auto_delete_message(error, time=300)
        return None

    text = message.text.split("\n")
    input_list = text[0].split(" ")

    # Handle Auto Link/FF (Mirror/Clone specific)
    if hasattr(listener, "auto_link") and listener.auto_link:
         if not any(x.startswith("http") or "magnet" in x for x in input_list):
                input_list.append(listener.auto_link)

    if hasattr(listener, "auto_ff") and listener.auto_ff:
         user_ff = any(item.strip() == "-ff" for item in input_list)
         if not user_ff:
             input_list.extend(listener.auto_ff.split())

    error_msg, error_button = await error_check(message)
    if error_msg:
        await delete_links(message)
        error = await send_message(message, error_msg, error_button)
        await auto_delete_message(error, time=300)
        return None

    # Comprehensive Args Dict to cover all modules
    args = {
        "link": "",
        "-i": 0,
        "-b": False,
        "-n": "",
        "-up": "",
        "-rcf": "",
        "-m": "",
        "-d": False, "-j": False, "-s": False, "-e": False, "-z": False,
        "-sv": False, "-ss": False, "-f": False, "-fd": False, "-fu": False,
        "-hl": False, "-bt": False, "-ut": False, "-mt": False, "-sync": False,
        "-doc": False, "-med": False,
        "-q": "", "-an": False, "-sn": False, # Encode specific
        "-watermark": "", "-iwm": "", "-au": "", "-ap": "", "-t": "",
        "-ca": "", "-cv": "", "-ns": "", "-md": "",
        # Metadata
        "-metadata-title": "", "-metadata-author": "", "-metadata-comment": "", "-metadata-all": "",
        "-metadata-video-title": "", "-metadata-video-author": "", "-metadata-video-comment": "",
        "-metadata-audio-title": "", "-metadata-audio-author": "", "-metadata-audio-comment": "",
        "-metadata-subtitle-title": "", "-metadata-subtitle-author": "", "-metadata-subtitle-comment": "",
        "-tl": "", "-ff": set(), "-trim": "",
        # Merge/Convert/Extract/Remove/Add/Compress flags
        "-merge-video": False, "-merge-audio": False, "-merge-subtitle": False,
        "-merge-all": False, "-merge-image": False, "-merge-pdf": False,
        "-compress": False, "-comp-video": False, "-comp-audio": False,
        "-comp-image": False, "-comp-document": False, "-comp-subtitle": False, "-comp-archive": False,
        "-video-fast": False, "-video-medium": False, "-video-slow": False,
        "-audio-fast": False, "-audio-medium": False, "-audio-slow": False,
        "-image-fast": False, "-image-medium": False, "-image-slow": False,
        "-document-fast": False, "-document-medium": False, "-document-slow": False,
        "-subtitle-fast": False, "-subtitle-medium": False, "-subtitle-slow": False,
        "-archive-fast": False, "-archive-medium": False, "-archive-slow": False,
        "-extract": False, "-extract-video": False, "-extract-audio": False,
        "-extract-subtitle": False, "-extract-attachment": False,
        "-extract-video-index": "", "-extract-audio-index": "", "-extract-subtitle-index": "", "-extract-attachment-index": "",
        "-extract-video-codec": "", "-extract-audio-codec": "", "-extract-subtitle-codec": "",
        "-extract-maintain-quality": "", "-extract-priority": "",
        "-remove": False, "-remove-video": False, "-remove-audio": False,
        "-remove-subtitle": False, "-remove-attachment": False, "-remove-metadata": False,
        "-remove-video-index": "", "-remove-audio-index": "", "-remove-subtitle-index": "", "-remove-attachment-index": "",
        "-remove-priority": "",
        "-add": False, "-add-video": False, "-add-audio": False, "-add-subtitle": False, "-add-attachment": False,
        "-del": "", "-preserve": False, "-replace": False,
        "-vi": "", "-ai": "", "-si": "", "-ati": "",
        "-rvi": "", "-rai": "", "-rsi": "", "-rati": "",
        "-swap": False, "-swap-audio": False, "-swap-video": False, "-swap-subtitle": False,
        "-lulu": False, "-buz": False, "-pix": False,
        "-sp": 0, "-h": [],
    }

    arg_parser(input_list[1:], args)

    link = args["link"]
    name = args["-n"]
    folder_name = args["-m"]

    try:
        multi = int(args["-i"])
    except:
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

    bulk_links = []

    # 1. Expand Telegram Ranges from text inputs first (The "New Feature" consolidation)
    # This logic was previously in Encode/Merge only. Now available for all.
    expanded_links = []

    # Check lines in the message for TG ranges
    # We iterate ALL lines in message for potential range links
    for line in text:
        line = line.strip()
        if not line: continue
        if is_telegram_link(line):
             # Try to match range pattern
             match = re_search(r"(https?://t\.me/(?:c/)?(?:[\w\d]+)/)(\d+)-(\d+)", line)
             if match:
                 base = match.group(1)
                 start = int(match.group(2))
                 end = int(match.group(3))
                 if start <= end:
                     for i in range(start, end + 1):
                         expanded_links.append(f"{base}{i}")
                 # We consumed this line as a range
                 continue
        # Also check if it's just a normal link not in arg_parser's link
        # Actually `extract_bulk_links` does this.
        # But `extract_bulk_links` handles the "Reply" logic too.
        # If we found ranges, we should treat this as BULK.

    if expanded_links:
        bulk_links.extend(expanded_links)
        is_bulk = True

    # 2. Standard Bulk Extraction
    # If not already bulk from ranges, check standard methods
    # But even if we found ranges, we might want to check for other links?
    # extract_bulk_links gets links from message text OR reply.
    extracted = await extract_bulk_links(message, bulk_start, bulk_end)

    # If we have expanded links, we merge them.
    # Be careful not to duplicate if extract_bulk_links also picked up the range string as a link (it likely picked up the range string itself as a "link" if it passed is_telegram_link check)
    # But is_telegram_link(".../10-20") might return True?
    # links_utils.is_telegram_link checks prefix.
    # So extracted might contain ".../10-20". We should filter that out if we expanded it.

    final_bulk = []
    if expanded_links:
        # Filter out the raw range strings from extracted if they exist
        # This is hard because we don't know which one was the range string exactly unless we re-parse.
        # Simpler approach:
        # Add expanded links to final.
        # Add extracted links to final IF they are NOT ranges (we assume ranges were handled).

        # Actually, let's just use a Set to avoid exact dupes, but expanded links are different strings.
        # We need to trust `expanded_links` for the range parts.

        final_bulk.extend(expanded_links)

        for l in extracted:
            # If l is a range link, ignore it (we expanded it).
            # If l is normal link, keep it.
             match = re_search(r"(https?://t\.me/(?:c/)?(?:[\w\d]+)/)(\d+)-(\d+)", l)
             if not match:
                 final_bulk.append(l)
    else:
        final_bulk = extracted

    # Update bulk_links
    bulk_links = final_bulk

    if len(bulk_links) > 1:
        is_bulk = True

    # 3. Resolve Primary Link from Reply if missing
    if not link and (reply_to := message.reply_to_message):
        if reply_to.document or reply_to.photo or reply_to.video or reply_to.audio or reply_to.voice or reply_to.video_note or reply_to.sticker or reply_to.animation:
            # Media reply - Caller handles this via `message.reply_to_message`
            pass
        elif reply_to.text:
            potential_link = reply_to.text.split("\n", 1)[0].strip()
            if is_url(potential_link) or is_magnet(potential_link) or is_telegram_link(potential_link) or is_rclone_path(potential_link) or is_gdrive_id(potential_link) or is_gdrive_link(potential_link) or is_mega_link(potential_link):
                link = potential_link

    return {
        "link": link,
        "args": args,
        "is_bulk": is_bulk,
        "bulk_links": bulk_links,
        "multi": multi,
        "name": name,
        "folder_name": folder_name,
        "input_list": input_list,
        "bulk_start": bulk_start,
        "bulk_end": bulk_end
    }
