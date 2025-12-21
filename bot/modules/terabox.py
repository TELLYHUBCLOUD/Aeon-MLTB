from urllib.parse import quote, urlparse

from aiohttp import ClientSession, TCPConnector
from bot import DOWNLOAD_DIR, LOGGER, bot_loop, task_dict_lock
from bot.core.aeon_client import TgClient
from bot.core.config_manager import Config
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
    new_task,
)
from bot.helper.ext_utils.links_utils import is_url, is_telegram_link
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
    send_status_message,
    get_tg_link_message,
)
from bot.modules.mirror_leech import Mirror


class TeraboxListener(Mirror):
    def __init__(
        self,
        client,
        message,
        is_qbit=False,
        is_leech=False,
        is_jd=False,
        is_nzb=False,
        same_dir=None,
        bulk=None,
        multi_tag=None,
        options="",
        auto_link=None,
        auto_ff=None,
    ):
        super().__init__(
            client,
            message,
            is_leech=is_leech,
            same_dir=same_dir,
            bulk=bulk,
            multi_tag=multi_tag,
            options=options,
            auto_link=auto_link,
            auto_ff=auto_ff,
        )

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
            "-m": "",
            "-up": "",
            "-rcf": "",
            "-n": "",
            "-t": "",
            "-ca": "",
            "-cv": "",
            "-ns": "",
            "-md": "",
            "-b": False,
        }

        arg_parser(input_list[1:], args)
        
        self.link = args["link"]
        self.multi = args["-i"]
        is_bulk = args["-b"]
        bulk_start = 0
        bulk_end = 0
        reply_to = None

        if not isinstance(is_bulk, bool):
            dargs = is_bulk.split(":")
            bulk_start = dargs[0] or 0
            if len(dargs) == 2:
                bulk_end = dargs[1] or 0
            is_bulk = True

        if not is_bulk:
            try:
                self.multi = int(self.multi)
            except:
                self.multi = 0

            if self.multi > 0:
                self.folder_name = f"/{args['-m']}".rstrip("/") if len(args["-m"]) > 0 else ""
                
                if self.folder_name:
                    async with task_dict_lock:
                        if self.folder_name in self.same_dir:
                            self.same_dir[self.folder_name]["tasks"].add(self.mid)
                            for fd_name in self.same_dir:
                                if fd_name != self.folder_name:
                                    self.same_dir[fd_name]["total"] -= 1
                        elif self.same_dir:
                            self.same_dir[self.folder_name] = {
                                "total": self.multi,
                                "tasks": {self.mid},
                            }
                            for fd_name in self.same_dir:
                                if fd_name != self.folder_name:
                                    self.same_dir[fd_name]["total"] -= 1
                        else:
                            self.same_dir = {
                                self.folder_name: {
                                    "total": self.multi,
                                    "tasks": {self.mid},
                                },
                            }
                elif self.same_dir:
                    async with task_dict_lock:
                        for fd_name in self.same_dir:
                            self.same_dir[fd_name]["total"] -= 1
        else:
            await self.init_bulk(input_list, bulk_start, bulk_end, TeraboxListener)
            return

        if len(self.bulk) != 0:
            del self.bulk[0]

        await self.run_multi(input_list, TeraboxListener)

        if not self.link and (reply_to := self.message.reply_to_message):
             if reply_text := reply_to.text:
                self.link = reply_text.split("\n", 1)[0].strip()
        
        if is_telegram_link(self.link):
            try:
                reply_to, session = await get_tg_link_message(self.link, self.message.from_user.id)
            except Exception as e:
                x = await send_message(self.message, f"ERROR: {e}")
                await self.remove_from_same_dir()
                await delete_links(self.message)
                return await auto_delete_message(x, time=300)

        if isinstance(reply_to, list):
            self.bulk = reply_to
            b_msg = input_list[:1]
            self.options = " ".join(input_list[1:])
            b_msg.append(f"{self.bulk[0]} -i {len(self.bulk)} {self.options}")
            nextmsg = await send_message(self.message, " ".join(b_msg))
            nextmsg = await self.client.get_messages(
                chat_id=self.message.chat.id,
                message_ids=nextmsg.id,
            )
            if self.message.from_user:
                nextmsg.from_user = self.user
            else:
                nextmsg.sender_chat = self.user
            await TeraboxListener(
                self.client,
                nextmsg,
                same_dir=self.same_dir,
                bulk=self.bulk,
                multi_tag=self.multi_tag,
                options=self.options,
            ).new_event()

            return await delete_links(self.message)
        elif reply_to:
             if reply_to.text:
                self.link = reply_to.text.split("\n", 1)[0].strip()
             elif reply_to.caption:
                self.link = reply_to.caption.split("\n", 1)[0].strip()

        if not is_url(self.link):
            if len(input_list) == 1 and not reply_to:
                await send_message(
                    self.message,
                    COMMAND_USAGE["terabox"][0],
                    COMMAND_USAGE["terabox"][1],
                )
            else:
                await send_message(
                    self.message,
                    "Provide a valid Terabox link to download.",
                )
            return

        if not Config.TERABOX_API:
             await send_message(
                self.message,
                "TERABOX_API not configured!",
            )
             return

        LOGGER.info(f"Terabox Link: {self.link}")
        
        await self.get_tag(text)
        
        try:
            await self.process_terabox()
        except Exception as e:
            LOGGER.error(f"Terabox Error: {e}")
            await send_message(self.message, f"Terabox Error: {e}")

    async def process_terabox(self):
        msg = await send_message(self.message, "Processing Terabox Link...")
        
        api_url = f"{Config.TERABOX_API}{quote(self.link)}"
        
        async with ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
            async with session.get(api_url) as resp:
                if resp.status != 200:
                    try:
                        resp_text = await resp.text()
                    except:
                        resp_text = "N/A"
                    LOGGER.error(f"Terabox API Error: {resp.status} | Body: {resp_text}")
                    await msg.edit(f"API Error: {resp.status}\nBody: {resp_text[:100]}")
                    return
                try:
                    data = await resp.json()
                except Exception as e:
                     await msg.edit(f"API JSON Error: {e}")
                     return

        valid_links = []
        
        # Helper to check and add non-empty links
        def check_add(api_key, dl_key):
            if api_data := data.get(api_key):
                if link := api_data.get(dl_key):
                    if link:
                        valid_links.append(link)
                        return True
            return False

        # 1. Check endpoints in priority order (Short-circuit)
        (check_add("api5", "dl1") or
         check_add("api5", "dl2") or
         check_add("api6", "dl1") or
         check_add("api6", "dl2") or
         check_add("api3", "dl1") or
         check_add("api3", "dl2"))

        if not valid_links:
            await msg.edit("No valid download links found from API.")
            return

        best_link = valid_links[0]
        self.link = best_link
        
        # Extract Filename from Metadata
        if metadata := data.get("metadata"):
            if file_name := metadata.get("file_name"):
                self.name = file_name
                LOGGER.info(f"Terabox Filename: {self.name}")

        await msg.delete()
        from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download    
        await self.before_start()
        await self.on_download_start()
        headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"]
        await add_aria2_download(self, f"{DOWNLOAD_DIR}{self.mid}/", headers, None, None)

async def terabox(client, message):
    bot_loop.create_task(TeraboxListener(client, message, is_leech=True).new_event())

async def terabox_mirror(client, message):
    bot_loop.create_task(TeraboxListener(client, message, is_leech=False).new_event())