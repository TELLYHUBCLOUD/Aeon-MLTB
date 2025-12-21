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


import asyncio
from re import match as re_match
# -----------------------------------------------------------
# API List (UPDATED)
# -----------------------------------------------------------
API_CONFIGS = [
    {"name": "API1", "url_template": "https://terabox-pro-api.vercel.app/api?link={url}"},
    {"name": "API2", "url_template": "https://wdzone-terabox-api.vercel.app/api?url={url}"},
    {"name": "API3", "url_template": "https://my-noor-queen-api.woodmirror.workers.dev/?url={url}"},
    {"name": "API4", "url_template": "https://silent-noor-stream-api.woodmirror.workers.dev/api?url={url}"},
    {"name": "API5", "url_template": "https://terabox-api.tellycloudapi.workers.dev/?url={url}"},
    {"name": "API6", "url_template": "https://teraboxdl.tellycloudapi.workers.dev/?url={url}"},
    {"name": "STREAMAPI", "url_template": "https://teraplay.tellycloudapi.workers.dev/?url={url}"},
]

async def fetch_api(session, target_url, api_config):
    api_name = api_config["name"]
    api_url = api_config["url_template"].format(url=quote(target_url))

    try:
        async with session.get(api_url, timeout=30) as response:
            if response.status != 200:
                 return {"success": False, "api": api_name, "error": f"HTTP {response.status}"}
            data = await response.json()

            # ---------------- API1 ----------------
            if api_name == "API1":
                info = data.get("📋 Extracted Info", [{}])[0] if data.get("📋 Extracted Info") else {}
                thumbnails = info.get("🖼️ Thumbnails", {})
                return {
                    "success": True,
                    "api": api_name,
                    "links": {"dl1": info.get("🔗 Direct Download Link"), "dl2": info.get("🔗 Direct Download Link")},
                    "metadata": {"file_name": info.get("📄 Title"), "thumb": thumbnails.get("360x270"), "size": info.get("📦 Size")}
                }
            # ---------------- API2 ----------------
            if api_name == "API2":
                info = data.get("📜 Extracted Info", [{}])[0] if data.get("📜 Extracted Info") else {}
                thumbnails = info.get("🖼️ Thumbnails", {})
                thumb = thumbnails.get("850x580") or (list(thumbnails.values())[0] if thumbnails else None)
                return {
                    "success": True,
                    "api": api_name,
                    "links": {"dl1": info.get("🔽 Direct Download Link"), "dl2": info.get("🚀 Fast Download Link")},
                    "metadata": {"file_name": info.get("📂 Title"), "thumb": thumb, "size": info.get("📏 Size")}
                }
            # ---------------- API3 ----------------
            if api_name == "API3":
                return {
                    "success": True,
                    "api": api_name,
                    "links": {"dl1": data.get("download_link"), "dl2": data.get("proxy_url")},
                    "metadata": {"file_name": data.get("file_name"), "thumb": data.get("thumbnail"), "size": data.get("file_size")}
                }
            # ---------------- API4 ----------------
            if api_name == "API4":
                return {
                    "success": True,
                    "api": api_name,
                    "links": {"dl1": data.get("download_link"), "dl2": data.get("proxy_url")},
                    "metadata": {"file_name": data.get("file_name"), "thumb": data.get("thumbnail"), "size": data.get("file_size")}
                }
            # ---------------- API5 & API6 ----------------
            if api_name in ["API5", "API6"]:
                if data.get("success"):
                    return {
                        "success": True,
                        "api": api_name,
                        "links": {"dl1": data.get("download_link"), "dl2": data.get("download_proxy")},
                        "metadata": {"file_name": data.get("file_name"), "thumb": data.get("thumb"), "size": data.get("file_size") or data.get("size")}
                    }
                return {"success": False, "api": api_name, "error": data.get("error", "API failed")}
            # ---------------- STREAMAPI ----------------
            if api_name == "STREAMAPI":
                if data.get("success"):
                     return {"success": True, "api": api_name, "links": {"stream": data.get("links", {}).get("Stream1")}, "metadata": data.get("metadata", {})}
                return {"success": False, "api": api_name, "error": "StreamAPI failed"}

            return {"success": False, "api": api_name, "error": "Unknown format"}
    except Exception as e:
        return {"success": False, "api": api_name, "error": str(e)}

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

        if not is_valid_terabox_url(self.link):
             if len(input_list) == 1 and not reply_to:
                await send_message(self.message, COMMAND_USAGE["terabox"][0], COMMAND_USAGE["terabox"][1])
             else:
                await send_message(self.message, "Provide a valid Terabox link to download.")
             return

        LOGGER.info(f"Terabox Link: {self.link}")
        
        await self.get_tag(text)
        
        try:
            await self.process_terabox()
        except Exception as e:
            LOGGER.error(f"Terabox Error: {e}", exc_info=True)
            await send_message(self.message, f"Terabox Error: {e}")

    async def process_terabox(self):
        msg = await send_message(self.message, "Processing Terabox Link with Multi-API...")
        
        # Check direct link
        if "1024tera.com/file/" in self.link or "terabox.com/file/" in self.link:
             LOGGER.info(f"Direct Terabox link detected: {self.link}")
             if not self.name: self.name = "Terabox_Download"
             await msg.delete()
             from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download
             await self.before_start()
             await self.on_download_start()
             headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"]
             await add_aria2_download(self, f"{DOWNLOAD_DIR}{self.mid}/", headers, None, None)
             return

        async with ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
            tasks = [fetch_api(session, self.link, config) for config in API_CONFIGS]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        best_link = None
        for res in results:
            if isinstance(res, dict) and res.get("success"):
                links = res.get("links", {})
                metadata = res.get("metadata", {})
                
                # Check for DL links
                if link := (links.get("dl1") or links.get("dl2")):
                    best_link = link
                    # Update metadata if not set
                    if not self.name and metadata.get("file_name"):
                        self.name = metadata.get("file_name")
                    break
        
        if not best_link:
             # Try stream link as fallback?
             for res in results:
                if isinstance(res, dict) and res.get("success"):
                    if link := res.get("links", {}).get("stream"):
                        best_link = link
                        if not self.name and res.get("metadata", {}).get("file_name"):
                             self.name = res.get("metadata").get("file_name")
                        break

        if not best_link:
            await msg.edit("All APIs failed to provide a valid download link.")
            return

        if self.name:
             LOGGER.info(f"Terabox Filename: {self.name}")

        await msg.delete()
        from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download    
        await self.before_start()
        await self.on_download_start()
        headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"]
        await add_aria2_download(self, f"{DOWNLOAD_DIR}{self.mid}/", headers, None, None)

def is_valid_terabox_url(url: str) -> bool:
    pattern = (
        r"^(https?://)?(www\.)?"
        r"(terabox\.com|teraboxapp\.com|teraboxlink\.com|"
        r"terabox\.app|terabox\.fun|terabox\.link|terabox\.club|terabox\.click|"
        r"teraboxurl\.com|teraboxshare\.com|teraboxfree\.com|teraboxfan\.com|"
        r"teraboxshortlink\.com|teraboxshort\.com|teraboxsharefile\.com|teraboxlinks\.com|"
        r"terafileshare\.com|terasharelink\.com|terasharefile\.com|terashareus\.com|"
        r"1024tera\.com|1024tera\.co|1024terabox\.com|1024-terabox\.com|1024box\.com|"
        r"1024teraboxlink\.com|tera1024box\.com|"
        r"mirrobox\.com|nephobox\.com|momerybox\.com|tibibox\.com|"
        r"gibibox\.com|pebibox\.com|"
        r"4funbox\.com|4funbox\.co|4funbox\.in|"
        r"freeterabox\.com|urlshortterabox\.com|shortlinkshare\.com|"
        r"fancybox\.in|bestclouddrive\.com|"
        r"dubox\.com|theteraboxmod\.app)"
        r"/s/[a-zA-Z0-9]+"
    )
    return re_match(pattern, url) is not None

async def terabox(client, message):
    bot_loop.create_task(TeraboxListener(client, message, is_leech=True).new_event())

async def terabox_mirror(client, message):
    bot_loop.create_task(TeraboxListener(client, message, is_leech=False).new_event())