from secrets import token_hex

from bot import LOGGER, task_dict, task_dict_lock
from bot.helper.ext_utils.task_manager import (
    check_running_tasks,
    stop_duplicate_check,
)
from bot.helper.listeners.direct_listener import DirectListener
from bot.helper.mirror_leech_utils.status_utils.direct_status import DirectStatus
from bot.helper.mirror_leech_utils.status_utils.queue_status import QueueStatus
from bot.helper.telegram_helper.message_utils import send_status_message


async def add_direct_download(listener, path):
    details = listener.link
    if not (contents := details.contents):
        await listener.on_download_error("There is nothing to download!")
        return
    listener.size = details.total_size

    if not listener.name:
        listener.name = details.title
    path = f"{path}/{listener.name}"

    msg, button = await stop_duplicate_check(listener)
    if msg:
        await listener.on_download_error(msg, button)
        return

    gid = token_hex(4)
    add_to_queue, event = await check_running_tasks(listener)
    if add_to_queue:
        LOGGER.info(f"Added to Queue/Download: {listener.name}")
        async with task_dict_lock:
            task_dict[listener.mid] = QueueStatus(listener, gid, "dl")
        await listener.on_download_start()
        if listener.multi <= 1:
            await send_status_message(listener.message)
        await event.wait()
        if listener.is_cancelled:
            return

    a2c_opt = {"follow-torrent": "false", "follow-metalink": "false"}
    if headers_dict := details.headers:
        headers = [f"{k}: {v}" for k, v in headers_dict.items()]
        a2c_opt["header"] = headers
    directListener = DirectListener(path, listener, a2c_opt)

    async with task_dict_lock:
        task_dict[listener.mid] = DirectStatus(listener, directListener, gid)

    if add_to_queue:
        LOGGER.info(f"Start Queued Download from Direct Download: {listener.name}")
    else:
        LOGGER.info(f"Download from Direct Download: {listener.name}")
        await listener.on_download_start()
        if listener.multi <= 1:
            await send_status_message(listener.message)

    await directListener.download(contents)
