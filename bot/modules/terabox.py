from aiohttp import ClientSession
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
        api_url = f"{Config.TERABOX_API}{self.link}"
        
        async with ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status != 200:
                    await msg.edit(f"API Error: {resp.status}")
                    return
                try:
                    data = await resp.json()
                except Exception as e:
                     await msg.edit(f"API JSON Error: {e}")
                     return

        # Parsing Priority: api5 > api6 > api3
        # Keys: dl1, dl2
        
        valid_links = []
        
        # Helper to check and add non-empty links
        def check_add(api_key, dl_key):
            if api_data := data.get(api_key):
                if link := api_data.get(dl_key):
                    if link:
                        valid_links.append(link)

        # 1. api5.dl1
        check_add("api5", "dl1")
        # 2. api5.dl2
        check_add("api5", "dl2")
        # 3. api6.dl1
        check_add("api6", "dl1")
        # 4. api6.dl2
        check_add("api6", "dl2")
        # 5. api3.dl1
        check_add("api3", "dl1")
        # 6. api3.dl2
        check_add("api3", "dl2")

        if not valid_links:
            await msg.edit("No valid download links found from API.")
            return

        # Pass the first valid link as the main link, others as Fallback? 
        # Actually aria2 accepts multiple URIs for the same file.
        # But Mirror class structure takes self.link.
        # We will use the first one as source, and somehow pass others?
        # For now let's just use the first best one found. The list is priority sorted.
        
        best_link = valid_links[0]
        
        # Initialize Mirror with the extracted direct link
        self.link = best_link
        await msg.delete()
        
        # Call the parent class methods to start download
        # We need to set self.name if the API provides it?
        # The API response might have filename info, but user didn't specify structure.
        # Let's rely on aria2 resolving name or user provided -n.
        
        # Re-using the initialized instance to start download logic
        # We need to bypass the 'check if link is magnet/url' part of Mirror since we have direct link now
        # But Mirror.new_event does parsing again. 
        # Better approach: We are inside new_event. We can just call add_aria2_download directly or 
        # proceed with standard checks if it looks like a URL.
        
        # However, we inherited from Mirror. Mirror.new_event() parses arguments again unless we carefully set state.
        # Actually, we shouldn't use Mirror.new_event inside. We should setup the object and call standard download helpers.
        
        from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download
        
        # Set defaults if not parsed (but they were parsed in new_event)
        # We are effectively "Hijacking" the flow. 
        
        await self.on_download_start()
        
        # If we have multiple links, we can pass them as list to aria2 for reliability
        # But add_aria2_download expects just self.link usually?
        # Actually aria2_download helper calls aria2.addUri([listener.link], options)
        # We can modify 'self.link' to be valid_links[0] for now.
        # To support multiple URIs in add_aria2_download, we would need to change that helper.
        # For this turn, let's just stick to Valid Link 1.
        
        # If user wants Leech (default for /terabox as per user context usually implies leech bot), 
        # we set is_leech=True in __init__.
        
        await add_aria2_download(self, f"{self.mid}/", [], None, None)


async def terabox(client, message):
    bot_loop.create_task(TeraboxListener(client, message).new_event())
