from html import escape
from time import time
from uuid import uuid4

from aiofiles import open as aiopen

from bot import LOGGER, user_data
from bot.core.aeon_client import TgClient
from bot.core.config_manager import Config
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.db_handler import database
from bot.helper.ext_utils.status_utils import get_readable_time
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_message,
    edit_message,
    send_file,
    send_message,
)


@new_task
async def start(client, message):
    if len(message.command) > 1 and message.command[1] == "private":
        await delete_message(message)
    elif len(message.command) > 1 and len(message.command[1]) == 36:
        userid = message.from_user.id
        input_token = message.command[1]
        stored_token = await database.get_user_token(userid)
        if stored_token is None:
            return await send_message(
                message,
                "<blockquote expandable>╭❌ <b>Error</b>\n╰<b>This token is not for you!</b> Please generate your own.</blockquote>",
            )
        if input_token != stored_token:
            return await send_message(
                message,
                "<blockquote expandable>╭❌ <b>Error</b>\n╰Invalid token. Please generate a new one.</blockquote>",
            )
        if userid not in user_data:
            return await send_message(
                message,
                "<blockquote expandable>╭❌ <b>Error</b>\n╰This token is not yours! Kindly generate your own.</blockquote>",
            )
        data = user_data[userid]
        if "TOKEN" not in data or data["TOKEN"] != input_token:
            return await send_message(
                message,
                "<blockquote expandable>╭❌ <b>Error</b>\n╰<b>This token has already been used!</b> Please get a new one.</blockquote>",
            )
        token = str(uuid4())
        token_time = time()
        data["TOKEN"] = token
        data["TIME"] = token_time
        user_data[userid].update(data)
        await database.update_user_tdata(userid, token, token_time)
        msg = "<blockquote expandable>╭✅ <b>Success</b>\n╰Your token has been successfully generated!\n\n"
        msg += (
            f"<b>Validity:</b> {get_readable_time(int(Config.TOKEN_TIMEOUT), True)}"
        )
        return await send_message(message, msg)
    elif await CustomFilters.authorized(client, message):
        help_command = f"/{BotCommands.HelpCommand}"
        start_string = f"╭🤖 <b>Aeon MLTB</b>\n┊This bot can mirror all your links, files, and torrents to Google Drive, Rclone, or Telegram.\n╰<b>Type {help_command} to get a list of available commands</b>"
        await send_message(message, start_string)
    else:
        await send_message(
            message, "<blockquote expandable>╭⚠️ <b>Warning</b>\n╰You are not an authorized user!</blockquote>"
        )
    await database.update_pm_users(message.from_user.id)
    return None


@new_task
async def ping(_, message):
    start_time = round(time() * 1000)
    reply = await send_message(
        message, "<blockquote expandable>╭⚡ <b>Starting Ping...</b>\n╰<b>Please wait...</b></blockquote>"
    )
    end_time = round(time() * 1000)
    await edit_message(
        reply, f"<blockquote expandable>╭📶 <b>Ping</b>\n╰<code>{end_time - start_time} ms</code></blockquote>"
    )


@new_task
async def log(_, message):
    buttons = ButtonMaker()
    buttons.data_button("View log", f"aeon {message.from_user.id} view")
    reply_message = await send_file(
        message,
        "<blockquote expandable>log.txt</blockquote>",
        buttons=buttons.build_menu(1),
    )
    await delete_message(message)
    await auto_delete_message(reply_message, time=300)


@new_task
async def aeon_callback(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    if user_id != int(data[1]):
        return await query.answer(text="This message not your's!", show_alert=True)
    if data[2] == "view":
        await query.answer()
        async with aiopen("log.txt") as f:
            log_file_lines = (await f.read()).splitlines()

        def parseline(line):
            try:
                return line.split("] ", 1)[1]
            except IndexError:
                return line

        ind, log_lines = 1, ""
        try:
            while len(log_lines) <= 3500:
                log_lines = parseline(log_file_lines[-ind]) + "\n" + log_lines
                if ind == len(log_file_lines):
                    break
                ind += 1
            start_line = "<pre language='python'>"
            end_line = "</pre>"
            btn = ButtonMaker()
            btn.data_button("Close", f"aeon {user_id} close")
            reply_message = await send_message(
                message,
                start_line + escape(log_lines) + end_line,
                btn.build_menu(1),
            )
            await query.edit_message_reply_markup(None)
            await delete_message(message)
            await auto_delete_message(reply_message, time=300)
        except Exception as err:
            LOGGER.error(f"TG Log Display : {err!s}")
    elif data[2] == "private":
        await query.answer(url=f"https://t.me/{TgClient.NAME}?start=private")
        return None
    else:
        await query.answer()
        await delete_message(message)
        return None

