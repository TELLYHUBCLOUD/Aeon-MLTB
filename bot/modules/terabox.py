from urllib.parse import quote, urlparse

import asyncio
from re import match as re_match

from aiohttp import ClientSession, TCPConnector, ClientTimeout

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


# -----------------------------------------------------------
# API List (UPDATED)
# -----------------------------------------------------------
API_CONFIGS = [
    {"name": "API5", "url_template": "https://terabox-api.tellycloudapi.workers.dev/?url={url}"},
    {"name": "API6", "url_template": "https://teraboxdl.tellycloudapi.workers.dev/?url={url}"},
]


async def fetch_api(session, target_url, api_config):
    api_name = api_config["name"]
    api_url = api_config["url_template"].format(url=quote(target_url))

    try:
        async with session.get(api_url, timeout=30) as response:
            if response.status != 200:
                return {"success": False, "api": api_name, "error": f"HTTP {response.status}"}
            data = await response.json()

            # ---------------- API5 & API6 ----------------
            if api_name in ["API5", "API6"]:
                if data.get("success"):
                    return {
                        "success": True,
                        "api": api_name,
                        "links": {
                            "dl1": data.get("download_link"),
                            "dl2": data.get("download_proxy"),
                        },
                        "metadata": {
                            "file_name": data.get("file_name"),
                            "thumb": data.get("thumb"),
                            "size": data.get("file_size") or data.get("size"),
                        },
                    }
                return {"success": False, "api": api_name, "error": data.get("error", "API failed")}

            return {"success": False, "api": api_name, "error": "Unknown format"}
    except Exception as e:
        LOGGER.error(f"Error calling {api_name}: {e}", exc_info=True)
        return {"success": False, "api": api_name, "error": str(e)}


class TeraboxListener(Mirror):
    def __init__(
        self,
        client,
        message,
        is_qbit: bool = False,
        is_leech: bool = False,
        is_jd: bool = False,
        is_nzb: bool = False,
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
            except Exception:
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
            # Bulk from Telegram messages
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
                await send_message(
                    self.message, COMMAND_USAGE["terabox"][0], COMMAND_USAGE["terabox"][1]
                )
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
        msg = await send_message(self.message, "Processing Terabox link with Multi-API...")

        # If it's already a direct file URL, just download it directly.
        if "1024tera.com/file/" in self.link or "terabox.com/file/" in self.link:
            LOGGER.info(f"Direct Terabox link detected: {self.link}")
            if not self.name:
                self.name = "Terabox_Download"

            await msg.edit("Direct link detected, starting download...")

            from bot.helper.mirror_leech_utils.download_utils.aria2_download import (
                add_aria2_download,
            )

            await self.before_start()
            await self.on_download_start()

            headers = [
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            ]
            await add_aria2_download(self, f"{DOWNLOAD_DIR}{self.mid}/", headers, None, None)
            return

        await msg.edit("Resolving Terabox link via APIs...")

        best_link = None
        best_metadata = {}
        api_errors = []

        timeout = ClientTimeout(total=60)

        async with ClientSession(
            connector=TCPConnector(verify_ssl=False),
            timeout=timeout,
        ) as session:
            # Create tasks for all APIs
            tasks = {
                asyncio.create_task(fetch_api(session, self.link, cfg)): cfg["name"]
                for cfg in API_CONFIGS
            }

            # Wait for the *first successful* API using as_completed
            for fut in asyncio.as_completed(tasks):
                api_name = tasks[fut]
                try:
                    res = await fut
                except Exception as e:
                    err_txt = f"{api_name}: {e}"
                    LOGGER.error(f"Terabox API error: {err_txt}", exc_info=True)
                    api_errors.append(err_txt)
                    continue

                if isinstance(res, dict) and res.get("success"):
                    links = res.get("links") or {}
                    best_link = links.get("dl1") or links.get("dl2")
                    best_metadata = res.get("metadata") or {}

                    await msg.edit(
                        f"Got direct link from {res.get('api', api_name)}, starting download..."
                    )
                    break
                else:
                    err_txt = f"{res.get('api', api_name)}: {res.get('error', 'Unknown error')}"
                    LOGGER.warning(f"Terabox API failed: {err_txt}")
                    api_errors.append(err_txt)

            # Cancel remaining API tasks (if any)
            for fut in tasks:
                if not fut.done():
                    fut.cancel()

        if not best_link:
            # No API succeeded
            error_text = "All APIs failed to provide a valid download link."
            if api_errors:
                error_text += "\n\nDetails:\n" + "\n".join(api_errors)
            error_text += "\n\n⚠️ Falling back to Leech command in 1 minute..."
            await msg.edit(error_text)
            
            await asyncio.sleep(60)
            
            await msg.delete()
            
            # Fallback to Leech logic
            await Mirror(
                self.client,
                self.message,
                is_leech=True,
                same_dir=self.same_dir,
                bulk=self.bulk,
                multi_tag=self.multi_tag,
                options=self.options,
            ).new_event()
            return

        # Use the API's direct link as the actual download URL
        self.link = best_link

        # Set filename from metadata if available
        if not self.name:
            self.name = best_metadata.get("file_name") or "Terabox_Download"

        LOGGER.info(f"Terabox direct link: {self.link}")
        LOGGER.info(f"Terabox filename: {self.name}")

        await msg.delete()

        from bot.helper.mirror_leech_utils.download_utils.aria2_download import (
            add_aria2_download,
        )

        await self.before_start()
        await self.on_download_start()

        headers = [
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ]
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
    bot_loop.create_task(TeraboxListener(client, message, is_leech=False).new_event())


async def terabox_mirror(client, message):
    bot_loop.create_task(TeraboxListener(client, message, is_leech=False).new_event())