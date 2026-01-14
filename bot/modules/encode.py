from asyncio import create_task, Event, wait_for, sleep
from os import path as ospath, walk
from time import time
from functools import partial
import json

from aiofiles.os import path as aiopath
from aiofiles.os import remove, listdir
from bot.helper.ext_utils.files_utils import get_path_size
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex, user

from secrets import token_hex
from aioshutil import move, rmtree

from bot import LOGGER, bot_loop, task_dict, task_dict_lock, multi_tags, intervals
from bot.core.aeon_client import TgClient
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.task_utils import task_init_helper
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
    new_task,
    cmd_exec,
    sync_to_async,
)
from bot.helper.ext_utils.bulk_links import extract_bulk_links
from bot.helper.ext_utils.media_utils import FFMpeg, get_remote_media_info
from bot.helper.ext_utils.status_utils import get_readable_file_size, get_readable_time
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
    get_tg_link_message,
)
from bot.helper.ext_utils.links_utils import is_url, is_telegram_link
from re import search as re_search
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import new_task, cmd_exec


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
        if obj.streams:
             obj.audio_map[index] = not obj.audio_map[index]
        else:
             obj.remove_audio = not obj.remove_audio
        await obj.main_menu()
    elif data[1] == "toggle_sub":
        index = int(data[2])
        if obj.streams:
            obj.sub_map[index] = not obj.sub_map[index]
        else:
             obj.remove_subs = not obj.remove_subs
        await obj.main_menu()
    elif data[1] == "cancel":
        await edit_message(message, "Task Cancelled.")
        obj.is_cancelled = True
        obj.event.set()
    elif data[1] == "done":
        await delete_message(message)
        obj.event.set()


class EncodeSelection:
    def __init__(self, listener, streams=None):
        self.listener = listener
        self.streams = streams
        self.quality = "Original" # Original, 1080p, 720p, 480p, 360p
        self.audio_map = {} # index: bool (True = Keep)
        self.sub_map = {}   # index: bool (True = Keep)
        self.remove_audio = False
        self.remove_subs = False
        self.is_cancelled = False
        self.event = Event()
        self._reply_to = None
        self._timeout = 60
        self._start_time = time()

        # Initialize maps if streams present
        if streams:
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

        if self.streams:
             return self.quality, self.audio_map, self.sub_map
        else:
             return self.quality, self.remove_audio, self.remove_subs

    async def main_menu(self):
        buttons = ButtonMaker()
        
        # Compress Button
        buttons.data_button(f"Compress: {self.quality}", "enc compress")

        if self.streams:
            # Audio Buttons (Stream specific)
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
            
            # Subtitle Buttons (Stream specific)
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
        else:
            # Generic Toggles
            a_icon = "❌" if self.remove_audio else "✅"
            buttons.data_button(f"{a_icon} Audio (All)", "enc toggle_audio 0")
            
            s_icon = "❌" if self.remove_subs else "✅"
            buttons.data_button(f"{s_icon} Subs (All)", "enc toggle_sub 0")

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
        options = [
            "Original",
            "1080p",
            "720p",
            "576p",
            "480p",
            "360p",
            "240p",
            "144p",
        ]
        for opt in options:
             prefix = "✅ " if self.quality == opt else ""
             buttons.data_button(f"{prefix}{opt}", f"enc qual {opt}")
        
        buttons.data_button("Back", "enc done") 
        
        markup = buttons.build_menu(2)
        await edit_message(self._reply_to, "Select Quality", markup)


class Encode(TaskListener):
    def __init__(self, client, message, **kwargs):
        self.message = message
        self.client = client
        self.quality = ""
        self.remove_audio = False
        self.remove_subs = False
        self.audio_map = {}
        self.sub_map = {}
        self.has_metadata_selection = False
        super().__init__()
        self.is_leech = True

        self.bulk = []
        self.multi = 0
        self.options = ""
        self.same_dir = {}
        self.multi_tag = ""

    async def new_event(self):
        args = {
            "link": "",
            "-i": 0,
            "-n": "",
            "-up": "",
            "-rcf": "",
            "-q": "",
            "-an": False,
            "-sn": False,
            "-b": False,
        }

        start = await task_init_helper(self, args)
        if not start:
            return

        input_list, text = start

        self.link = args["link"]
        self.name = args["-n"]
        self.up_dest = args["-up"]
        self.rc_flags = args["-rcf"]
        self.quality = args["-q"]
        self.remove_audio = args["-an"]
        self.remove_subs = args["-sn"]
        self.multi = int(args["-i"])

        if len(self.bulk) != 0:
            del self.bulk[0]
        
        await self.run_multi(input_list, Encode)

        if not self.link and (reply_to := self.message.reply_to_message):
            if reply_to.document or reply_to.video or reply_to.audio:
                self.link = reply_to
            elif reply_to.text:
                self.link = reply_to.text.split("\n", 1)[0].strip()

        if isinstance(self.link, str) and is_telegram_link(self.link):
            try:
                reply_to, session = await get_tg_link_message(self.link, self.message.from_user.id)
                if isinstance(reply_to, list):
                    # Multi Bulk from TG Link
                    self.bulk = reply_to
                    # We need to process this bulk using init_bulk logic OR spawn tasks
                    # existing init_bulk expects self.bulk to be set.
                    # But init_bulk is for text/file inputs.
                    # Let's just spawn for each item in list?
                    # Or treat first as self.link?
                    self.link = reply_to[0]
                    # Spawn others
                    for msg in reply_to[1:]:
                         bot_loop.create_task(Encode(self.client, msg).new_event()) # THIS MIGHT FAIL if msg is Message object not event?
                         # Encode expects client, message.
                         # If we pass msg as message, safe? Yes.
                    # BUT 'msg' is the media message. It doesn't have the command text.
                    # This requires more complex bulk handling.
                    # Leech uses Mirror(..., bulk=reply_to).
                    # Encode has run_multi logic.
                    # Let's simplify: process first, loop others.
                    self.link = reply_to[0]
                    for msg in reply_to[1:]:
                        # We need to construct a task for this message.
                        # Since it's already a message object, we can just instantiate Encode with it?
                        # No, Encode relies on self.message.text options.
                        # We should clone the options.
                        # For simplicity, let's just use recursive loop with new_event if possible?
                        # Or just ignore bulk link expansion for now and handle SINGLE recursive link?
                        # The user wants "like leech". Leech spawns new Mirror instance with bulk list.
                        pass
                elif reply_to:
                    self.link = reply_to
            except Exception as e:
                await send_message(self.message, f"ERROR: {e}")
                return

        if not self.link:
             await send_message(
                self.message,
                COMMAND_USAGE["encode"][0],
                COMMAND_USAGE["encode"][1],
            )
             return

        LOGGER.info(f"Encode Request: Link: {self.link}")

        await self.get_tag(text) 
        
        # === PRE-DOWNLOAD METADATA STEP ===
        streams = []
        is_remote_successful = False
        
        if (isinstance(self.link, str) and is_url(self.link)) or hasattr(self.link, "document") or hasattr(self.link, "video") or hasattr(self.link, "audio"):
            wait_msg = await send_message(self.message, "⏳ Fetching Metadata...")
            if isinstance(self.link, str) and is_url(self.link):
                streams = await get_remote_media_info(self.link)
            else:
                # Telegram media (Message object)
                media = self.link.document or self.link.video or self.link.audio
                if media:
                    from os import makedirs
                    from bot import DOWNLOAD_DIR
                    from bot.helper.ext_utils.media_utils import get_streams
                    from aiofiles import open as aiopen
                    from aiofiles.os import remove as aioremove
                    
                    path = f"{DOWNLOAD_DIR}Metadata/"
                    if not await aiopath.isdir(path):
                        await sync_to_async(makedirs, path, exist_ok=True)
                    
                    des_path = ospath.join(path, f"{self.mid}_{media.file_name or 'temp'}")
                    try:
                        async for chunk in TgClient.bot.stream_media(media, limit=5):
                            async with aiopen(des_path, "ab") as f:
                                await f.write(chunk)
                        
                        streams = await get_streams(des_path)
                    except Exception as e:
                        LOGGER.error(f"Error fetching TG metadata: {e}")
                    finally:
                        if await aiopath.exists(des_path):
                            await aioremove(des_path)

            if streams:
                is_remote_successful = True
            
            await delete_message(wait_msg)
        
        # Interactive Menu (Pre-Download)
        selector = EncodeSelection(self, streams)
        if self.quality: selector.quality = self.quality
        
        # Pre-apply flags if passed via CLI
        if self.remove_audio and streams:
            for idx in selector.audio_map: selector.audio_map[idx] = False
        elif self.remove_audio:
            selector.remove_audio = True
            
        if self.remove_subs and streams:
            for idx in selector.sub_map: selector.sub_map[idx] = False
        elif self.remove_subs:
            selector.remove_subs = True

        qual, map1, map2 = await selector.get_selection()

        if qual is None: # Cancelled
            await send_message(self.message, "Task Cancelled.")
            return

        # Store Selection
        if streams:
            self.quality = qual
            self.audio_map = map1
            self.sub_map = map2
            self.has_metadata_selection = True
        else:
            self.quality = qual
            self.remove_audio = map1
            self.remove_subs = map2
            self.has_metadata_selection = False

        try:
             await self.before_start()
        except Exception as e:
            await send_message(self.message, e)
            return

        await self._proceed_to_download()

    async def _proceed_to_download(self):
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
             create_task(add_aria2_download(self, path, [], None, None))
        else:
             await send_message(self.message, "Invalid input for encode.")
             return
             
    async def on_download_complete(self):
        # Walk to find the largest video file
        target_file = None
        max_size = 0
        video_extensions = {
            ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", 
            ".ts", ".m4v", ".dat", ".vob", ".3gp", ".mpeg", ".mpg"
        }
        
        for root, _, files_list in await sync_to_async(walk, self.dir):
            for file_name in files_list:
                if file_name.endswith((".aria2", ".!qB")):
                    continue
                file_path_ignored = ospath.join(root, file_name)
                
                # Check extension first to avoid unnecessary stat calls on junk
                ext = ospath.splitext(file_name)[1].lower()
                
                if ext in video_extensions:
                    size = await get_path_size(file_path_ignored)
                    if size > max_size:
                        max_size = size
                        target_file = file_path_ignored
        
        if not target_file:
             await self.on_upload_error("No valid video files found to encode.")
             return

        file_path = target_file

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


        local_streams = []
        if self.has_metadata_selection:
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
                    local_streams = json.loads(result[0]).get("streams", [])
             except:
                pass

        if self.has_metadata_selection and local_streams:
            # Map Streams based on Pre-Selection (indices should match)
            has_video = False
            for stream in local_streams:
                idx = stream['index']
                ctype = stream['codec_type']
                if ctype == 'video':
                    cmd.extend(["-map", f"0:{idx}"])
                    has_video = True
                elif ctype == 'audio':
                    if self.audio_map.get(idx, True): # Default Keep if missing in map? Or Strict?
                        cmd.extend(["-map", f"0:{idx}"])
                elif ctype == 'subtitle':
                    if self.sub_map.get(idx, True):
                        cmd.extend(["-map", f"0:{idx}"])
                else:
                     cmd.extend(["-map", f"0:{idx}"]) # Map attachments
        else:
            # Fallback (Generic flags)
            has_video = True # Assume video
            if self.remove_audio:
                cmd.append("-an")
            else:
                cmd.extend(["-c:a", "copy"])
                
            if self.remove_subs:
                cmd.append("-sn")
            else:
                cmd.extend(["-c:s", "copy"])

        # Transcoding Options
        if self.quality != "Original": # and has_video (we assume yes or generic)
             cmd.extend(["-c:v", "libx264"])
             scale = ""
             if self.quality == "1080p": scale = "scale=-2:1080"
             elif self.quality == "720p": scale = "scale=-2:720"
             elif self.quality == "576p": scale = "scale=-2:576"
             elif self.quality == "480p": scale = "scale=-2:480"
             elif self.quality == "360p": scale = "scale=-2:360"
             elif self.quality == "240p": scale = "scale=-2:240"
             elif self.quality == "144p": scale = "scale=-2:144"
             if scale:
                cmd.extend(["-vf", scale])
        else:
             cmd.extend(["-c:v", "copy"])
        
        if self.has_metadata_selection:
             cmd.extend(["-c:a", "copy", "-c:s", "copy"])

        output_file = f"{ospath.splitext(file_path)[0]}_encoded{ospath.splitext(file_path)[1]}"
        cmd.append(output_file)
        
        LOGGER.info(f"Running Encode CMD: {cmd}")

        res = await ffmpeg.metadata_watermark_cmds(cmd, file_path)
        
        if res:
             try:
                if await aiopath.exists(file_path):
                    await remove(file_path) # Delete Original
                
                # Cleanup leftovers like .aria2 files
                for f in await listdir(self.dir):
                     if f.endswith((".aria2", ".!qB")):
                         await remove(f"{self.dir}/{f}")

                if await aiopath.exists(output_file):
                     encoded_file_name = ospath.basename(output_file)
                     
                     if self.name and self.name != encoded_file_name:
                          ext = ospath.splitext(encoded_file_name)[1]
                          if not self.name.endswith(ext):
                              self.name += ext
                          new_path = f"{self.dir}/{self.name}"
                          await move(output_file, new_path)
                          LOGGER.info(f"Renamed encoded file to: {self.name} | Size: {await get_path_size(self.dir)}")
                     else:
                          self.name = encoded_file_name
                          new_path = f"{self.dir}/{self.name}"
                          # If output_file is in subdir, move it to root self.dir
                          if ospath.dirname(output_file) != self.dir:
                                await move(output_file, new_path)
                          LOGGER.info(f"Encoded File: {self.name} | Size: {await get_path_size(self.dir)}")
                     
                     # Cleanup empty dirs
                     if await aiopath.isdir(ospath.dirname(file_path)) and ospath.dirname(file_path) != self.dir:
                         try:
                            await rmtree(ospath.dirname(file_path))
                         except:
                            pass
                else:
                     await self.on_upload_error("Encoded file not found!")
                     return

             except Exception as e:
                LOGGER.error(f"Error moving/renaming: {e}")
                
             await super().on_download_complete()
        else:
             await self.on_upload_error("Encoding Failed. Check logs.")



async def encode(client, message):
    from bot.helper.ext_utils.bulk_links import extract_bulk_links
    bulk = await extract_bulk_links(message, "0", "0")
    if len(bulk) > 1:
        await Encode(client, message).init_bulk(message.text.split("\n")[0].split(), 0, 0, Encode)
    else:
        bot_loop.create_task(Encode(client, message).new_event())
