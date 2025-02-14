from bot import (
    queue_dict_lock,
    queued_dl,
    queued_up,
    task_dict,
    task_dict_lock,
    user_data,
)
from bot.core.config_manager import Config
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.status_utils import get_task_by_gid
from bot.helper.ext_utils.task_manager import (
    start_dl_from_queued,
    start_up_from_queued,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import send_message


@new_task
async def remove_from_queue(_, message):
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg = message.text.split()
    status = msg[1] if len(msg) > 1 and msg[1] in ["fd", "fu"] else ""

    if (status and len(msg) > 2) or (not status and len(msg) > 1):
        gid = msg[2] if status else msg[1]
        task = await get_task_by_gid(gid)
        if task is None:
            await send_message(message, f"❌ GID: <code>{gid}</code> Not Found.")
            return
    elif reply_to_id := message.reply_to_message_id:
        async with task_dict_lock:
            task = task_dict.get(reply_to_id)
        if task is None:
            await send_message(message, "⚠️ This is not an active task!")
            return
    elif len(msg) in {1, 2}:
        msg = f"""📌 **Usage Instructions:**
Reply to an active **Command message** used to start the **download/upload**.

🔹 Use <code>/{BotCommands.ForceStartCommand[0]}</code> `fd` (to remove from download queue) or `fu` (to remove from upload queue) or leave empty to remove from both.

🔹 You can also use <code>/{BotCommands.ForceStartCommand[0]} GID</code> `fu|fd` or just GID to **force start by removing from the queue**.

📌 **Examples:**
✅ <code>/{BotCommands.ForceStartCommand[1]}</code> `GID fu` (Force Upload 📤)
✅ <code>/{BotCommands.ForceStartCommand[1]}</code> `GID` (Force Download & Upload 📥📤)
✅ **By replying to task command:**
    - <code>/{BotCommands.ForceStartCommand[1]}</code> (Force Download & Upload 📥📤)
    - <code>/{BotCommands.ForceStartCommand[1]}</code> `fd` (Force Download 📥)
"""
        await send_message(message, msg)
        return

    if user_id not in (Config.OWNER_ID, task.listener.user_id) and (
        user_id not in user_data or not user_data[user_id].get("is_sudo")
    ):
        await send_message(message, "🚫 **This task is not for you!**")
        return

    listener = task.listener
    msg = ""

    async with queue_dict_lock:
        if status == "fu":
            listener.force_upload = True
            if listener.mid in queued_up:
                await start_up_from_queued(listener.mid)
                msg = "✅ **Task has been force started to upload!** 🚀📤"
            else:
                msg = "⚡ **Force Upload enabled for this task!**"
        elif status == "fd":
            listener.force_download = True
            if listener.mid in queued_dl:
                await start_dl_from_queued(listener.mid)
                msg = "✅ **Task has been force started to download only!** 📥"
            else:
                msg = "⚠️ **This task is not in the download queue!**"
        else:
            listener.force_download = True
            listener.force_upload = True
            if listener.mid in queued_up:
                await start_up_from_queued(listener.mid)
                msg = "✅ **Task has been force started to upload!** 🚀📤"
            elif listener.mid in queued_dl:
                await start_dl_from_queued(listener.mid)
                msg = "✅ **Task has been force started to download & upload will start after download!** 📥📤"
            else:
                msg = "⚠️ **This task is not in queue!**"

    if msg:
        await send_message(message, msg)
