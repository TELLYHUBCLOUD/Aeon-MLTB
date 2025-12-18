from urllib.parse import quote, urlparse

from aiohttp import ClientSession, TCPConnector
from bot import LOGGER, bot_loop
from bot.core.aeon_client import TgClient
from bot.core.config_manager import Config
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
    new_task,
)
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    send_message,
    send_status_message,
)
from bot.modules.mirror_leech import Mirror


class TeraboxListener(Mirror):
    def __init__(self, client, message):
        super().__init__(client, message, is_leech=True)

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
        }

        arg_parser(input_list[1:], args)
        
        self.link = args["link"]

        if not self.link and (reply_to := self.message.reply_to_message):
             if reply_text := reply_to.text:
                self.link = reply_text.split("\n", 1)[0].strip()

        if not is_url(self.link):
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

        # 1. api5.dl2
        check_add("api5", "dl1")
        check_add("api5", "dl2")
        check_add("api6", "dl1")
        check_add("api6", "dl2")
        check_add("api3", "dl1")
        check_add("api3", "dl2")

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
        await self.on_download_start()
        headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"]
        await add_aria2_download(self, f"{self.mid}/", headers, None, None)
async def terabox(client, message):
    bot_loop.create_task(TeraboxListener(client, message).new_event())