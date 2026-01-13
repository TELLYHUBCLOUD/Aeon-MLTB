from aiofiles import open as aiopen
from aiofiles.os import remove
from re import search as re_search
from bot.helper.ext_utils.links_utils import is_telegram_link

def filter_links(links_list: list, bulk_start: int, bulk_end: int) -> list:
    """
    Filters a list of links based on start and end indices.

    Args:
        links_list: The list of links to filter.
        bulk_start: The starting index (1-based). If 0, no start filtering.
        bulk_end: The ending index. If 0, no end filtering.

    Returns:
        The filtered list of links.
    """
    if bulk_start != 0 and bulk_end != 0:
        links_list = links_list[bulk_start:bulk_end]
    elif bulk_start != 0:
        links_list = links_list[bulk_start:]
    elif bulk_end != 0:
        links_list = links_list[:bulk_end]
    return links_list


def get_links_from_message(text: str) -> list:
    """
    Extracts valid links from a string, assuming one link per line or separated by spaces.
    Empty lines and lines starting with / (commands) are ignored.
    Only valid URLs, magnets, and Telegram links are returned.

    Args:
        text: The string containing links.

    Returns:
        A list of extracted links.
    """
    from bot.helper.ext_utils.links_utils import is_url, is_magnet, is_telegram_link
    
    links_list = text.split("\n")
    valid_links = []
    for line in links_list:
        line = line.strip()
        if not line or line.startswith("/"):
            continue

        # Check TG Range first (one per line usually)
        if is_telegram_link(line):
            match = re_search(r"(https?://t\.me/(?:c/)?(?:[\w\d]+)/)(\d+)-(\d+)", line)
            if match:
                base = match.group(1)
                start = int(match.group(2))
                end = int(match.group(3))
                if start <= end:
                    for i in range(start, end + 1):
                        valid_links.append(f"{base}{i}")
                continue

        # Split by space in case multiple links are on one line (though Usually it's one per line for bulk)
        parts = line.split()
        for part in parts:
            if is_url(part) or is_magnet(part) or is_telegram_link(part):
                valid_links.append(part)
    return valid_links


async def get_links_from_file(message) -> list:
    """
    Downloads a text file attached to a Pyrogram message and extracts links from it,
    assuming one link per line. Empty lines are ignored.

    Args:
        message: The Pyrogram message object with the attached text file.

    Returns:
        A list of extracted links.
    """
    links_list = []
    text_file_dir = await message.download()
    async with aiopen(text_file_dir, "r+") as f:
        lines = await f.readlines()
        for line in lines:
            line = line.strip()
            if not line: continue

            # Check TG Range
            if is_telegram_link(line):
                match = re_search(r"(https?://t\.me/(?:c/)?(?:[\w\d]+)/)(\d+)-(\d+)", line)
                if match:
                    base = match.group(1)
                    start = int(match.group(2))
                    end = int(match.group(3))
                    if start <= end:
                        for i in range(start, end + 1):
                            links_list.append(f"{base}{i}")
                    continue
            links_list.append(line)

    await remove(text_file_dir)
    return links_list


async def extract_bulk_links(message, bulk_start: str, bulk_end: str) -> list:
    """
    Extracts bulk links from a Pyrogram message.
    Links can be in the replied-to message, an attached text file, or the message itself.
    The extracted links are then filtered based on start and end indices.

    Args:
        message: The Pyrogram message object.
        bulk_start: The starting index for filtering (string, converted to int).
        bulk_end: The ending index for filtering (string, converted to int).

    Returns:
        A list of filtered links.
    """
    from bot import LOGGER
    
    bulk_start = int(bulk_start)
    bulk_end = int(bulk_end)
    links_list = []
    
    LOGGER.info(f"[BULK] Starting extraction - bulk_start={bulk_start}, bulk_end={bulk_end}")
    
    if reply_to := message.reply_to_message:
        LOGGER.info(f"[BULK] Found reply_to_message")
        if (file_ := reply_to.document) and (file_.mime_type == "text/plain"):
            LOGGER.info(f"[BULK] Extracting from text file")
            links_list = await get_links_from_file(reply_to)
        elif text := (reply_to.text or reply_to.caption):
            LOGGER.info(f"[BULK] Extracting from replied text/caption, length={len(text)}")
            # If it's a media message (caption), only extract links if no other media is present
            if reply_to.text or not any(
                [
                    reply_to.photo,
                    reply_to.video,
                    reply_to.audio,
                    reply_to.document,
                    reply_to.voice,
                    reply_to.video_note,
                    reply_to.animation,
                ]
            ):
                links_list = get_links_from_message(text)
                LOGGER.info(f"[BULK] Extracted {len(links_list)} links from reply")
            else:
                LOGGER.info(f"[BULK] Skipped - reply has media attached")
        else:
            LOGGER.info(f"[BULK] Reply has no text or caption")
    else:
        LOGGER.info(f"[BULK] No reply_to_message, checking current message")
        text = message.text or message.caption
        if text and "\n" in text:
            LOGGER.info(f"[BULK] Extracting from current message, length={len(text)}")
            links_list = get_links_from_message(text)
        else:
            LOGGER.info(f"[BULK] Current message has no multiline text")
    
    LOGGER.info(f"[BULK] Total links before filter: {len(links_list)}")
    result = filter_links(links_list, bulk_start, bulk_end) if links_list else []
    LOGGER.info(f"[BULK] Final links after filter: {len(result)}")
    return result
