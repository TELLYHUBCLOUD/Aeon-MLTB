from asyncio import create_task, Event, wait_for, sleep
from os import path as ospath, walk, makedirs
from time import time
from functools import partial
import json

from aiofiles.os import path as aiopath
from aiofiles.os import remove, listdir
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove

from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex, user

from aioshutil import move, rmtree

from bot import LOGGER, bot_loop, task_dict, task_dict_lock, DOWNLOAD_DIR
from bot.core.aeon_client import TgClient
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    cmd_exec,
    sync_to_async,
)
from bot.helper.ext_utils.media_utils import FFMpeg, get_remote_media_info, get_streams
from bot.helper.ext_utils.status_utils import get_readable_time
from bot.helper.mirror_leech_utils.status_utils.ffmpeg_status import FFmpegStatus
from bot.helper.telegram_helper.message_utils import (
    delete_message,
    send_message,
    send_status_message,
    edit_message,
)
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.modules.mirror_leech import Mirror


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


class Encode(Mirror):
    def __init__(self, client, message, **kwargs):
        super().__init__(client, message, **kwargs)
        self.quality = ""
        self.remove_audio = False
        self.remove_subs = False
        self.audio_map = {}
        self.sub_map = {}
        self.has_metadata_selection = False
        self.is_leech = True # Default to leech for encode unless overridden

    async def new_event(self):
        # reuse Mirror's ensure_user_dict
        self._ensure_user_dict()
        
        if not self.message or not self.message.text:
             return await send_message(self.message, "Invalid message")

        # We need to get the link to check metadata BEFORE calling super().new_event() which starts download.
        # However, Mirror.new_event() handles argument parsing.
        # We can:
        # 1. Parse args manually here (duplicated code) - BAD
        # 2. Let Mirror parse args, but we need to intercept before 'proceed_to_download'.
        #    Mirror calls self.before_start(). We can use that hook?
        #    Mirror calls self.before_start() just before download.
        #    Let's override before_start!

        await super().new_event()

    async def before_start(self):
        await super().before_start()

        # This runs after Mirror has parsed arguments and set self.link
        # Now we can do our interactive metadata check.
        
        streams = []
        
        if (isinstance(self.link, str) and is_url(self.link)) or self.message.reply_to_message:
            wait_msg = await send_message(self.message, "⏳ Fetching Metadata...")
            if isinstance(self.link, str) and is_url(self.link):
                streams = await get_remote_media_info(self.link)
            else:
                # Telegram media (Message object)
                reply = self.message.reply_to_message
                media = reply.document or reply.video or reply.audio if reply else None
                if media:
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
                pass # success
            
            await delete_message(wait_msg)
        
        # Interactive Menu (Pre-Download)
        selector = EncodeSelection(self, streams)
        if hasattr(self, 'quality') and self.quality: selector.quality = self.quality
        
        # Pre-apply flags if passed via CLI (Mirror args parsing handled this?)
        # Mirror doesn't have -an, -sn specifically map to self.remove_audio...
        # Wait, Mirror has "-remove-audio": False etc.
        # We should map Mirror's args to Encode's needs if possible.
        if hasattr(self, 'remove_audio_enabled') and self.remove_audio_enabled:
             if streams:
                 for idx in selector.audio_map: selector.audio_map[idx] = False
             else:
                 selector.remove_audio = True

        if hasattr(self, 'remove_subtitle_enabled') and self.remove_subtitle_enabled:
             if streams:
                 for idx in selector.sub_map: selector.sub_map[idx] = False
             else:
                 selector.remove_subs = True

        qual, map1, map2 = await selector.get_selection()

        if qual is None: # Cancelled
            raise Exception("Task Cancelled by User")

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


    async def on_download_complete(self):
        # Override to perform encoding
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
                    from bot.helper.ext_utils.files_utils import get_path_size
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
                          LOGGER.info(f"Renamed encoded file to: {self.name}")
                     else:
                          self.name = encoded_file_name
                          new_path = f"{self.dir}/{self.name}"
                          # If output_file is in subdir, move it to root self.dir
                          if ospath.dirname(output_file) != self.dir:
                                await move(output_file, new_path)
                          LOGGER.info(f"Encoded File: {self.name}")
                     
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
                
             # Call TaskListener's on_download_complete (which does Upload)
             # NOTE: Mirror does NOT implement on_download_complete, it uses TaskListener's.
             # So super().on_download_complete() calls TaskListener.on_download_complete().
             # But TaskListener.on_download_complete() does renaming, extracting, etc.
             # We already did encoding.
             # We should ensure TaskListener doesn't try to re-process things we already handled?
             # TaskListener.proceed_ffmpeg checks self.ffmpeg_cmds.
             # We manually ran ffmpeg.
             # So we should be fine as long as we don't set self.ffmpeg_cmds again.
             await super().on_download_complete()
        else:
             await self.on_upload_error("Encoding Failed. Check logs.")

from bot.helper.ext_utils.bot_utils import new_task
@new_task
async def encode(client, message):
    from bot.helper.ext_utils.bulk_links import extract_bulk_links
    bulk = await extract_bulk_links(message, "0", "0")
    if len(bulk) > 1:
        await Encode(client, message).init_bulk(message.text.split("\n")[0].split(), 0, 0, Encode)
    else:
        bot_loop.create_task(Encode(client, message).new_event())
