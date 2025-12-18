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
)


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
        # Override to perform Encoding before Uploading
        # self.dir contains the downloaded file(s)
        
        from bot.helper.ext_utils.files_utils import listdir
        files = await listdir(self.dir)
        if not files:
            await self.on_upload_error("No files downloaded.")
            return
            
        file_path = f"{self.dir}/{files[0]}" # Assuming single file for encode
        
        # Prepare FFMpeg Status
        ffmpeg = FFMpeg(self)
        
        async with task_dict_lock:
            task_dict[self.mid] = FFmpegStatus(self, ffmpeg, self.gid, "encoding")
        
        await send_status_message(self.message)
        
        # Build Command
        # This part depends on user input
        # Basic presets
        scale = ""
        if self.quality == "1080p":
            scale = "scale=-1:1080"
        elif self.quality == "720p":
            scale = "scale=-1:720"
        elif self.quality == "480p":
            scale = "scale=-1:480"
            
        output_file = f"{ospath.splitext(file_path)[0]}_encoded.mp4"
        
        cmd = [
            "xtra",
            "-hide_banner",
            "-loglevel",
            "error",
            "-progress",
            "pipe:1",
            "-i",
            file_path,
        ]
        
        if scale:
            cmd.extend(["-vf", scale])
            
        if self.remove_audio:
            cmd.append("-an")
        else:
            cmd.extend(["-c:a", "copy"])
            
        if self.remove_subs:
            cmd.append("-sn")
            
        cmd.extend([
            "-c:v", "libx264",
            "-threads", "4",
            output_file
        ])
        
        LOGGER.info(f"Running Encode CMD: {cmd}")

        # Use FFMpeg class (it handles Subprocess and Progress)
        # But FFMpeg class in media_utils has specific methods like convert_video
        # It also has metadata_watermark_cmds which runs arbitrary commands?
        # Let's check FFMpeg.metadata_watermark_cmds: it takes 'ffmpeg' list argument and runs it.
        # It's generic enough.
        
        res = await ffmpeg.metadata_watermark_cmds(cmd, file_path)
        
        if res:
             # Encoding Success
             # Replace original file or upload output_file
             # TaskListener expects file to be at self.dir/self.name or similar?
             # TaskListener.on_download_complete scans self.dir.
             # We should delete original and rename encoded to original name? Or keep new name.
             
             try:
                await aiopath.remove(file_path)
                # Rename encoded to clean name?
                # For now let's keep output_file
                self.name = ospath.basename(output_file)
             except Exception as e:
                LOGGER.error(f"Error removing original: {e}")
                
             # Now call super().on_download_complete() to proceed to upload
             await super().on_download_complete()
        else:
             await self.on_upload_error("Encoding Failed. Check logs.")


async def encode(client, message):
    bot_loop.create_task(Encode(client, message).new_event())
