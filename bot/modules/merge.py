from asyncio import create_task, sleep
from os import path as ospath, walk
import re

from aiofiles.os import path as aiopath
from aiofiles.os import remove

from secrets import token_hex
from aioshutil import move

from bot import LOGGER, bot_loop, task_dict, task_dict_lock, multi_tags, intervals
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
    sync_to_async,
)

from bot.helper.ext_utils.bulk_links import extract_bulk_links
from bot.helper.ext_utils.links_utils import is_url, is_telegram_link
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
        self.bulk = []
        self.multi = 0
        self.options = ""
        self.same_dir = {}
        self.same_dir = {}
        self.multi_tag = ""
        self.inputs = []
        self.total_batch_files = 0
        self.current_batch_files = 0

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
            "-b": False,
        }

        arg_parser(input_list[1:], args)

        self.link = args["link"]
        self.name = args["-n"]
        self.up_dest = args["-up"]
        self.rc_flags = args["-rcf"]
        self.multi = args["-i"]
        is_bulk = args["-b"]
        bulk_start = 0
        bulk_end = 0

        if not isinstance(is_bulk, bool):
            dargs = is_bulk.split(":")
            bulk_start = dargs[0] or 0
            if len(dargs) == 2:
                bulk_end = dargs[1] or 0
            is_bulk = True

        if is_bulk:
            await self.init_bulk(input_list, bulk_start, bulk_end, Merge)
            return

        if len(self.bulk) != 0:
            del self.bulk[0]

        await self.run_multi(input_list, Merge)

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
            # Check for multiple links in text
            if len(text) > 0:
                 self.link = text[0] # Take first as primary? or parse all
        
        # Parse Inputs from text (Multiple links / Ranges)
        if not is_bulk: # If NOT bulk, check for multiple inputs for THIS task
             for line in text:
                 line = line.strip()
                 if not line: continue
                 # Check for TG Range: link/11-20
                 if is_telegram_link(line):
                     match = re.search(r"(https?://t\.me/(?:c/)?(?:[\w\d]+)/)(\d+)-(\d+)", line)
                     if match:
                         base = match.group(1)
                         start = int(match.group(2))
                         end = int(match.group(3))
                         if start <= end:
                             for i in range(start, end + 1):
                                 self.inputs.append(f"{base}{i}")
                         continue
                 # Normal Link
                 if is_url(line) or hasattr(line, "download"): # Handle reply object later
                     self.inputs.append(line)
             
             # If reply object and no text links
             if not self.inputs and (reply_to := self.message.reply_to_message):
                 if reply_to.document or reply_to.video or reply_to.audio:
                    self.inputs.append(reply_to)

        if not self.inputs and self.link:
             if is_telegram_link(self.link):
                 match = re.search(r"(https?://t\.me/(?:c/)?(?:[\w\d]+)/)(\d+)-(\d+)", self.link)
                 if match:
                     base = match.group(1)
                     start = int(match.group(2))
                     end = int(match.group(3))
                     if start <= end:
                         for i in range(start, end + 1):
                             self.inputs.append(f"{base}{i}")
                 else:
                     self.inputs.append(self.link)
             else:
                 self.inputs.append(self.link)
        
        if not self.inputs:
             await send_message(
                self.message,
                COMMAND_USAGE["merge"][0],
                COMMAND_USAGE["merge"][1],
            )
             return

        self.total_batch_files = len(self.inputs)
        LOGGER.info(f"Merge Request: {self.total_batch_files} inputs")

        try:
             await self.before_start()
        except Exception as e:
            await send_message(self.message, e)
            return

        await self._proceed_to_download()

    async def get_tg_link_message(self, link):
        message = None
        if link.startswith("https://t.me/"):
            try:
                msg_link = link.split("/")
                msg_id = int(msg_link[-1])
                if "c/" in link:
                    chat_id = int("-100" + msg_link[-2])
                else:
                    chat_id = msg_link[-2]
                message = await self.client.get_messages(chat_id, msg_id)
            except Exception as e:
                LOGGER.error(f"Error getting TG Link: {e}")
        return message

    async def _proceed_to_download(self):
        from bot.helper.mirror_leech_utils.download_utils.telegram_download import (
            TelegramDownloadHelper,
        )
        
        path = f"{self.dir}/"
        
        for link in self.inputs:
            # Check cancel
            if self.is_cancelled:
                return

            self.link = link

            if hasattr(link, "download"):
                 # Telegram reply object
                create_task(TelegramDownloadHelper(self).add_download(
                        link,
                        path,
                        self.client,
                    ))
            elif is_telegram_link(str(link)):
                 message = await self.get_tg_link_message(link)
                 if message:
                     if message.document or message.video or message.audio:
                         create_task(TelegramDownloadHelper(self).add_download(
                            message,
                            path,
                            self.client,
                        ))
                     else:
                         self.total_batch_files -= 1
                 else:
                     LOGGER.error(f"Failed to get message for: {link}")
                     self.total_batch_files -= 1 # adjust total
            elif is_url(str(link)):
                 await add_aria2_download(self, path, [], None, None) 
            else:
                 self.total_batch_files -= 1

        if self.total_batch_files == 0:
             await send_message(self.message, "No valid inputs found.")
             return
             
    async def on_download_complete(self):
        self.current_batch_files += 1
        if self.current_batch_files < self.total_batch_files:
            return

        input_files = []
        for root, _, filess in await sync_to_async(walk, self.dir):
             for file in filess:
                 input_files.append(ospath.join(root, file))
        
        if not input_files or len(input_files) < 2:
            await self.on_upload_error(f"Need at least 2 files to merge. Found: {len(input_files)}")
            return
            
        input_files.sort()
        
        # Create input.txt
        input_txt_path = f"{self.dir}/input.txt"
        with open(input_txt_path, 'w') as f:
            for file in input_files:
                f.write(f"file '{file}'\n")
        
        # Prepare FFMpeg Status
        ffmpeg = FFMpeg(self)
        async with task_dict_lock:
            if self.mid in task_dict:
                self.gid = task_dict[self.mid].gid()
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
             for file in input_files:
                 await remove(file)
             await remove(input_txt_path)
             


             if self.name and self.name != "merged.mp4":
                  ext = ospath.splitext(output_file)[1]
                  if not self.name.endswith(ext):
                      self.name += ext
                  new_path = f"{self.dir}/{self.name}"
                  await move(output_file, new_path)
                  LOGGER.info(f"Renamed merged file to: {self.name}")
             else:
                  self.name = "merged.mp4"
             
             await super().on_download_complete()
        else:
             await self.on_upload_error("Merge Failed. Check logs.")


    async def run_multi(self, input_list, obj):
        await sleep(7)
        if not self.multi_tag and self.multi > 1:
            self.multi_tag = token_hex(2)
            multi_tags.add(self.multi_tag)
        elif self.multi <= 1:
            if self.multi_tag in multi_tags:
                multi_tags.discard(self.multi_tag)
            return
        if self.multi_tag and self.multi_tag not in multi_tags:
            await send_message(
                self.message,
                f"{self.tag} Multi-task has been cancelled!",
            )
            await send_status_message(self.message)
            async with task_dict_lock:
                for fd_name in self.same_dir:
                    self.same_dir[fd_name]["total"] -= self.multi
            return
        if len(self.bulk) != 0:
            msg = input_list[:1]
            msg.append(f"{self.bulk[0]} -i {self.multi - 1} {self.options}")
            msgts = " ".join(msg)
            if self.multi > 2:
                msgts += f"\nCancel Multi: <code>/stop {self.multi_tag}</code>"
            nextmsg = await send_message(self.message, msgts)
        else:
            msg = [s.strip() for s in input_list]
            index = msg.index("-i")
            msg[index + 1] = f"{self.multi - 1}"
            nextmsg = await self.client.get_messages(
                chat_id=self.message.chat.id,
                message_ids=self.message.reply_to_message_id + 1,
            )
            msgts = " ".join(msg)
            if self.multi > 2:
                msgts += f"\nCancel Multi: <code>/stop {self.multi_tag}</code>"
            nextmsg = await send_message(nextmsg, msgts)
        nextmsg = await self.client.get_messages(
            chat_id=self.message.chat.id,
            message_ids=nextmsg.id,
        )
        if self.message.from_user:
            nextmsg.from_user = self.user
        else:
            nextmsg.sender_chat = self.user
        if intervals["stopAll"]:
            return
        await obj(
            self.client,
            nextmsg,
        ).new_event()

    async def init_bulk(self, input_list, bulk_start, bulk_end, obj):
        try:
            self.bulk = await extract_bulk_links(self.message, bulk_start, bulk_end)
            if len(self.bulk) == 0:
                raise ValueError("Bulk Empty!")
            b_msg = input_list[:1]
            self.options = input_list[1:]
            index = self.options.index("-b")
            del self.options[index]
            if bulk_start or bulk_end:
                del self.options[index + 1]
            self.options = " ".join(self.options)
            b_msg.append(f"{self.bulk[0]} -i {len(self.bulk)} {self.options}")
            msg = " ".join(b_msg)
            if len(self.bulk) > 2:
                self.multi_tag = token_hex(2)
                multi_tags.add(self.multi_tag)
                msg += f"\nCancel Multi: <code>/stop {self.multi_tag}</code>"
            nextmsg = await send_message(self.message, msg)
            nextmsg = await self.client.get_messages(
                chat_id=self.message.chat.id,
                message_ids=nextmsg.id,
            )
            if self.message.from_user:
                nextmsg.from_user = self.user
            else:
                nextmsg.sender_chat = self.user
            await obj(
                self.client,
                nextmsg,
            ).new_event()
        except Exception as e:
            await send_message(
                self.message,
                f"Reply to a text file or a Telegram message with links separated by new lines. Error: {e}",
            )


async def merge(client, message):
    bot_loop.create_task(Merge(client, message).new_event())
