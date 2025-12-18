from asyncio import create_task
from os import path as ospath

from aiofiles.os import path as aiopath
from aiofiles.os import remove

from bot import LOGGER, bot_loop, task_dict, task_dict_lock
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
)
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.ext_utils.media_utils import FFMpeg
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


class Merge(TaskListener):
    def __init__(self, client, message):
        self.message = message
        self.client = client
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
        }

        arg_parser(input_list[1:], args)

        self.link = args["link"]
        self.name = args["-n"]
        self.up_dest = args["-up"]
        self.rc_flags = args["-rcf"]

        # Merge usually works with Reply loop or Folder?
        # For simplicity, if replied to a message, treat it as input?
        # Or bulk input?
        # User said "/merge ... esmi video/media file ko merge kari"
        # Strategy: Download provided link(s). If folder, merge all files inside. 
        # If single link, maybe useless unless standard inputs?
        # Let's assume it works like Mirror: Download -> Merge content of folder -> Upload single file.

        if not self.link and (reply_to := self.message.reply_to_message):
             # Logic to handle reply
             if reply_to.document or reply_to.video or reply_to.audio:
                self.link = reply_to
             elif reply_to.text:
                self.link = reply_to.text.split("\n", 1)[0].strip()

        if not self.link:
             await send_message(
                self.message,
                COMMAND_USAGE["merge"][0],
                COMMAND_USAGE["merge"][1],
            )
             return

        LOGGER.info(f"Merge Request: Link: {self.link}")

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
             await send_message(self.message, "Invalid input for merge.")
             return
             
    async def on_download_complete(self):
        from bot.helper.ext_utils.files_utils import listdir
        files = await listdir(self.dir)
        if not files or len(files) < 2:
            await self.on_upload_error(f"Need at least 2 files to merge. Found: {len(files)}")
            return
            
        files.sort() # Sort by name
        
        # Create input.txt
        input_txt_path = f"{self.dir}/input.txt"
        with open(input_txt_path, 'w') as f:
            for file in files:
                f.write(f"file '{file}'\n")
        
        # Prepare FFMpeg Status
        ffmpeg = FFMpeg(self)
        async with task_dict_lock:
            task_dict[self.mid] = FFmpegStatus(self, ffmpeg, self.gid, "merging")
        
        await send_status_message(self.message)
        
        output_file = f"{self.dir}/merged.mp4"
        
        cmd = [
            "xtra",
            "-hide_banner",
            "-loglevel",
            "error",
            "-progress",
            "pipe:1",
            "-f", "concat",
            "-safe", "0",
            "-i", input_txt_path,
            "-c", "copy",
            output_file
        ]
        
        LOGGER.info(f"Running Merge CMD: {cmd}")
        
        res = await ffmpeg.metadata_watermark_cmds(cmd, output_file) 
        # Note: metadata_watermark_cmds uses get_media_info on "f_path" argument to set total_time.
        # But output_file doesn't exist yet!
        # This might cause FFMpegStatus to have 0 total time / progress issues.
        # But we can't get total time of concat input easily without probing all files.
        # We can sum up duration of inputs?
        
        if res:
             # Cleanup inputs
             for file in files:
                 await remove(f"{self.dir}/{file}")
             await remove(input_txt_path)
             
             self.name = "merged.mp4"
             await super().on_download_complete()
        else:
             await self.on_upload_error("Merge Failed. Check logs.")


async def merge(client, message):
    bot_loop.create_task(Merge(client, message).new_event())
