from asyncio import create_task
from os import path as ospath

from aiofiles.os import path as aiopath

from bot import LOGGER, bot_loop, task_dict, task_dict_lock
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
)
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.ext_utils.media_utils import FFMpeg
from bot.helper.ext_utils.status_utils import get_readable_file_size
from bot.helper.listeners.task_listener import TaskListener
from bot.helper.mirror_leech_utils.download_utils.aria2_download import (
    add_aria2_download,
)
from bot.helper.mirror_leech_utils.download_utils.direct_downloader import (
    add_direct_download,
)
from bot.helper.mirror_leech_utils.status_utils.ffmpeg_status import FFmpegStatus
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
    send_status_message,
    edit_message,
    delete_message,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import new_task, cmd_exec
from bot.helper.ext_utils.status_utils import get_readable_time, get_readable_file_size
from functools import partial
from time import time
from asyncio import Event, wait_for
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex, user
import json


@new_task
async def select_encode_options(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()

    if data[1] == "compress":
        await obj.compress_subbuttons()
    elif data[1] == "qual":
        obj.quality = data[2]
        await obj.main_menu()
    elif data[1] == "toggle_audio":
        index = int(data[2])
        obj.audio_map[index] = not obj.audio_map[index]
        await obj.main_menu()
    elif data[1] == "toggle_sub":
        index = int(data[2])
        obj.sub_map[index] = not obj.sub_map[index]
        await obj.main_menu()
    elif data[1] == "cancel":
        await edit_message(message, "Task Cancelled.")
        obj.is_cancelled = True
        obj.event.set()
    elif data[1] == "done":
        await delete_message(message)
        obj.event.set()


class EncodeSelection:
    def __init__(self, listener, streams):
        self.listener = listener
        self.streams = streams
        self.quality = "Original" # Original, 1080p, 720p, 480p, 360p
        self.audio_map = {} # index: bool (True = Keep)
        self.sub_map = {}   # index: bool (True = Keep)
        self.is_cancelled = False
        self.event = Event()
        self._reply_to = None
        self._timeout = 60
        self._start_time = time()

        # Initialize maps
        for stream in streams:
            if stream['codec_type'] == 'audio':
                self.audio_map[stream['index']] = True
            elif stream['codec_type'] == 'subtitle':
                self.sub_map[stream['index']] = True

    @property
    def is_timed_out(self):
        return (time() - self._start_time) > self._timeout

    async def get_selection(self):
        await self.main_menu()
        pfunc = partial(select_encode_options, obj=self)
        handler = self.listener.client.add_handler(
            CallbackQueryHandler(pfunc, filters=regex("^enc") & user(self.listener.user_id)),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except Exception:
            if self._reply_to:
                await delete_message(self._reply_to)
            # Timeout -> Proceed with defaults
            pass
        finally:
            self.listener.client.remove_handler(*handler)
        
        if self.is_cancelled:
            return None, None, None

        return self.quality, self.audio_map, self.sub_map

    async def main_menu(self):
        buttons = ButtonMaker()
        
        # Compress Button
        buttons.data_button(f"Compress: {self.quality}", "enc compress")

        # Audio Buttons
        for stream in self.streams:
            if stream['codec_type'] == 'audio':
                idx = stream['index']
                lang = stream.get('tags', {}).get('language', 'und')
                title = stream.get('tags', {}).get('title', '')
                label = f"{lang} ({stream.get('codec_name', 'unk')})"
                if title:
                    label += f" - {title}"
                
                icon = "✅" if self.audio_map.get(idx, True) else "❌"
                buttons.data_button(f"{icon} Audio: {label}", f"enc toggle_audio {idx}")
        
        # Subtitle Buttons
        for stream in self.streams:
            if stream['codec_type'] == 'subtitle':
                idx = stream['index']
                lang = stream.get('tags', {}).get('language', 'und')
                title = stream.get('tags', {}).get('title', '')
                label = f"{lang} ({stream.get('codec_name', 'unk')})"
                if title:
                    label += f" - {title}"
                
                icon = "✅" if self.sub_map.get(idx, True) else "❌"
                buttons.data_button(f"{icon} Sub: {label}", f"enc toggle_sub {idx}")

        buttons.data_button("Done", "enc done")
        buttons.data_button("Cancel", "enc cancel")

        msg_text = (
            f"<b>Encode Settings</b>\n"
            f"Timeout: {get_readable_time(self._timeout - (time() - self._start_time))}\n"
        )
        
        markup = buttons.build_menu(1)

        if not self._reply_to:
            self._reply_to = await send_message(self.listener.message, msg_text, markup)
        else:
            await edit_message(self._reply_to, msg_text, markup)

    async def compress_subbuttons(self):
        buttons = ButtonMaker() 
        options = ["Original", "1080p", "720p", "480p", "360p"]
        for opt in options:
             prefix = "✅ " if self.quality == opt else ""
             buttons.data_button(f"{prefix}{opt}", f"enc qual {opt}")
        
        buttons.data_button("Back", "enc done") # Re-using done as back to main menu loop essentially
        
        markup = buttons.build_menu(2)
        await edit_message(self._reply_to, "Select Quality", markup)


class Encode(TaskListener):
    def __init__(self, client, message):
        self.message = message
        self.client = client
        self.quality = ""
        self.remove_audio = False
        self.remove_subs = False
        super().__init__()
        self.is_leech = True

    async def new_event(self):
        text = self.message.text.split("\n")
        input_list = text[0].split(" ")
        error_msg, error_button = await error_check(self.message)
        if error_msg:
            await delete_links(self.message)
            error = await send_message(self.message, error_msg, error_button)
            return await auto_delete_message(error, time=300)

        args = {
            "link": "",
            "-i": 0,
            "-n": "",
            "-up": "",
            "-rcf": "",
            "-q": "",
            "-an": False,
            "-sn": False,
        }

        arg_parser(input_list[1:], args)

        self.link = args["link"]
        self.name = args["-n"]
        self.up_dest = args["-up"]
        self.rc_flags = args["-rcf"]
        self.quality = args["-q"]
        self.remove_audio = args["-an"]
        self.remove_subs = args["-sn"]

        if not self.link and (reply_to := self.message.reply_to_message):
            if reply_to.document or reply_to.video or reply_to.audio:
                self.link = reply_to
            elif reply_to.text:
                self.link = reply_to.text.split("\n", 1)[0].strip()

        if not self.link:
             await send_message(
                self.message,
                COMMAND_USAGE["encode"][0],
                COMMAND_USAGE["encode"][1],
            )
             return

        LOGGER.info(f"Encode Request: Link: {self.link} Quality: {self.quality}")

        try:
             await self.before_start()
        except Exception as e:
            await send_message(self.message, e)
            return

        await self._proceed_to_download()

    async def _proceed_to_download(self):
        if hasattr(self.link, "download"):
             # Telegram file in reply
             pass
             # We rely on TelegramDownloadHelper ?
             # Actually existing listeners use TelegramDownloadHelper via TaskListener / Mirror
             # But Encode is TaskListener.
             # We can't reuse Mirror fully because logic is different (AFTER download -> Encode -> Upload)
             # But on_download_complete logic in TaskListener handles 'upload'.
             # We need to inject "Encode" step between Download Complete and Upload.
             # The easiest way is to override on_download_complete.
             pass
        elif is_url(self.link):
            pass
        
        # We start download. On download complete, we will check if it's encode task (via checking class name or flag) behavior.
        # But wait, existing listeners like Mirror call on_download_complete which immediately queues Upload.
        # We need to intercept.
        
        from bot.helper.mirror_leech_utils.download_utils.telegram_download import (
            TelegramDownloadHelper,
        )
        
        path = f"{self.dir}/"
        
        if hasattr(self.link, "download"):
             # Telegram file
            create_task(
                TelegramDownloadHelper(self).add_download(
                    self.message.reply_to_message,
                    path,
                    self.client,
                ),
            )
        elif is_url(self.link):
             # For simplicity, assuming direct link or aria2 supported link
             create_task(add_aria2_download(self, path, [], None, None))
        else:
             await send_message(self.message, "Invalid input for encode.")
             return
             
    async def on_download_complete(self):
        from bot.helper.ext_utils.files_utils import listdir
        files = await listdir(self.dir)
        if not files:
            await self.on_upload_error("No files downloaded.")
            return
            
        file_path = f"{self.dir}/{files[0]}" 

        # Extract Metadata (Streams)
        try:
            result = await cmd_exec(
                [
                    "ffprobe", 
                    "-hide_banner", 
                    "-loglevel", "error", 
                    "-print_format", "json", 
                    "-show_streams", 
                    file_path
                ]
            )
            if result[0]:
                streams = json.loads(result[0]).get("streams", [])
            else:
                streams = []
        except Exception as e:
            LOGGER.error(f"Metadata Extraction Failed: {e}")
            streams = []

        # Interactive Menu
        selector = EncodeSelection(self, streams)
        qual, audio_map, sub_map = await selector.get_selection()

        if qual is None: # Cancelled
            await self.on_upload_error("User Cancelled Task")
            return

        # Prepare FFMpeg Status
        ffmpeg = FFMpeg(self)
        
        async with task_dict_lock:
            if self.mid in task_dict:
                self.gid = task_dict[self.mid].gid()
            task_dict[self.mid] = FFmpegStatus(self, ffmpeg, self.gid, "encoding")
        
        await send_status_message(self.message)
        
        cmd = [
            "xtra",
            "-hide_banner",
            "-loglevel", "error", 
            "-progress", "pipe:1",
            "-i", file_path,
        ]

        # Map Streams
        has_video = False
        for stream in streams:
            idx = stream['index']
            ctype = stream['codec_type']
            if ctype == 'video':
                cmd.extend(["-map", f"0:{idx}"])
                has_video = True
            elif ctype == 'audio':
                if audio_map.get(idx, True):
                    cmd.extend(["-map", f"0:{idx}"])
            elif ctype == 'subtitle':
                if sub_map.get(idx, True):
                    cmd.extend(["-map", f"0:{idx}"])
            else:
                 cmd.extend(["-map", f"0:{idx}"]) # Map attachments/data by default
        
        if not streams: # Fallback if metadata failed
             cmd.extend(["-map", "0"])
             has_video = True 

        # Transcoding Options
        if qual != "Original" and has_video:
             cmd.extend(["-c:v", "libx264"])
             scale = ""
             if qual == "1080p": scale = "scale=-1:1080"
             elif qual == "720p": scale = "scale=-1:720"
             elif qual == "480p": scale = "scale=-1:480"
             elif qual == "360p": scale = "scale=-1:360"
             if scale:
                cmd.extend(["-vf", scale])
        else:
             cmd.extend(["-c:v", "copy"])

        cmd.extend(["-c:a", "copy", "-c:s", "copy"])
        
        output_file = f"{ospath.splitext(file_path)[0]}_encoded.mp4"
        cmd.append(output_file)
        
        LOGGER.info(f"Running Encode CMD: {cmd}")

        res = await ffmpeg.metadata_watermark_cmds(cmd, file_path)
        
        if res:
             try:
                await aiopath.remove(file_path)
                self.name = ospath.basename(output_file)
             except Exception as e:
                LOGGER.error(f"Error removing original: {e}")
                
             await super().on_download_complete()
        else:
             await self.on_upload_error("Encoding Failed. Check logs.")


async def encode(client, message):
    bot_loop.create_task(Encode(client, message).new_event())
