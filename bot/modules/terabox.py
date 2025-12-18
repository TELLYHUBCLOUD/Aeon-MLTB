import asyncio
from typing import Dict, List, Optional
from urllib.parse import quote, urlparse

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from bot import LOGGER, bot_loop
from bot.core.aeon_client import TgClient
from bot.core.config_manager import Config
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
    get_readable_file_size,
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
    """Terabox download listener with improved error handling and reliability."""
    
    def __init__(self, client, message):
        super().__init__(client, message, is_leech=True)
        self.fallback_links: List[str] = []
        self.file_size: int = 0
        self.file_type: str = "Unknown"

    async def new_event(self):
        """Main entry point for processing Terabox download requests."""
        text = self.message.text.split("\n")
        input_list = text[0].split(" ")
        
        # Access check
        error_msg, error_button = await error_check(self.message)
        if error_msg:
            await delete_links(self.message)
            error = await send_message(self.message, error_msg, error_button)
            return await auto_delete_message(error, time=300)

        # Parse arguments
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

        # Check reply message for link
        if not self.link and (reply_to := self.message.reply_to_message):
            if reply_text := reply_to.text:
                self.link = reply_text.split("\n", 1)[0].strip()

        # Validate link
        if not self.link or not is_url(self.link):
            await send_message(
                self.message,
                "❌ Please provide a valid Terabox link to download.",
            )
            return

        # Validate Terabox link format
        if not self._is_terabox_link(self.link):
            await send_message(
                self.message,
                "❌ Invalid Terabox link format. Please provide a valid Terabox URL.",
            )
            return

        # Check API configuration
        if not Config.TERABOX_API:
            await send_message(
                self.message,
                "⚠️ TERABOX_API not configured! Please contact the administrator.",
            )
            return

        if not self._validate_api_url(Config.TERABOX_API):
            LOGGER.error(f"Invalid TERABOX_API URL format: {Config.TERABOX_API}")
            await send_message(
                self.message,
                "⚠️ Invalid TERABOX_API configuration. Please contact the administrator.",
            )
            return

        LOGGER.info(
            f"Processing Terabox | User: {self.message.from_user.id} | "
            f"Username: {self.message.from_user.username or 'N/A'} | Link: {self.link}"
        )
        
        try:
            await self.process_terabox()
        except Exception as e:
            LOGGER.error(f"Terabox Error: {e}", exc_info=True)
            await send_message(
                self.message, 
                f"❌ Terabox Error: {str(e)[:200]}\n\nPlease try again or contact support."
            )

    def _is_terabox_link(self, link: str) -> bool:
        """Validate if the link is a Terabox URL."""
        try:
            parsed = urlparse(link.lower())
            valid_domains = ['terabox.com', 'www.terabox.com', '1024terabox.com', 'teraboxapp.com']
            return any(domain in parsed.netloc for domain in valid_domains)
        except Exception:
            return False

    def _validate_api_url(self, api_url: str) -> bool:
        """Validate API URL format."""
        try:
            return api_url.startswith(('http://', 'https://'))
        except Exception:
            return False

    def _extract_download_links(self, data: Dict) -> List[str]:
        """
        Extract download links with priority order.
        
        Priority: api5.dl2 > api5.dl1 > api6.dl2 > api6.dl1 > api3.dl2 > api3.dl1
        
        Args:
            data: API response data
            
        Returns:
            List of valid download links in priority order
        """
        valid_links = []
        priority_order = [
            ("api5", "dl2"), ("api5", "dl1"),
            ("api6", "dl2"), ("api6", "dl1"),
            ("api3", "dl2"), ("api3", "dl1"),
        ]
        
        for api_key, dl_key in priority_order:
            try:
                if api_data := data.get(api_key):
                    if link := api_data.get(dl_key):
                        # Strip whitespace and validate
                        clean_link = str(link).strip()
                        if clean_link and clean_link.startswith(('http://', 'https://')):
                            valid_links.append(clean_link)
                            LOGGER.debug(f"Found valid link in {api_key}.{dl_key}")
            except Exception as e:
                LOGGER.warning(f"Error extracting from {api_key}.{dl_key}: {e}")
                continue
        
        return valid_links

    def _extract_metadata(self, data: Dict) -> bool:
        """
        Extract file metadata from API response.
        
        Args:
            data: API response data
            
        Returns:
            True if metadata was successfully extracted, False otherwise
        """
        try:
            if metadata := data.get("metadata"):
                self.name = metadata.get("file_name", "Unknown")
                self.file_size = metadata.get("size", 0)
                self.file_type = metadata.get("type", "Unknown")
                
                size_str = get_readable_file_size(self.file_size) if self.file_size > 0 else "Unknown"
                LOGGER.info(
                    f"Terabox Metadata - Name: {self.name}, "
                    f"Size: {size_str}, Type: {self.file_type}"
                )
                return True
            else:
                LOGGER.warning("No metadata found in API response")
                return False
        except Exception as e:
            LOGGER.error(f"Error extracting metadata: {e}")
            return False

    async def _fetch_api_with_retry(
        self, 
        api_url: str, 
        max_retries: int = 3,
        timeout_seconds: int = 30
    ) -> Optional[Dict]:
        """
        Fetch data from Terabox API with retry logic.
        
        Args:
            api_url: The API URL to fetch
            max_retries: Maximum number of retry attempts
            timeout_seconds: Request timeout in seconds
            
        Returns:
            API response as dictionary, or None if failed
        """
        timeout = ClientTimeout(total=timeout_seconds)
        
        for attempt in range(max_retries):
            try:
                async with ClientSession(
                    connector=TCPConnector(verify_ssl=False),
                    timeout=timeout
                ) as session:
                    LOGGER.debug(f"API Request attempt {attempt + 1}/{max_retries}")
                    
                    async with session.get(api_url) as resp:
                        if resp.status != 200:
                            try:
                                resp_text = await resp.text()
                            except Exception:
                                resp_text = "N/A"
                            
                            LOGGER.error(
                                f"Terabox API Error | Status: {resp.status} | "
                                f"Attempt: {attempt + 1}/{max_retries} | "
                                f"Body: {resp_text[:200]}"
                            )
                            
                            if attempt == max_retries - 1:
                                raise Exception(f"API returned status {resp.status}: {resp_text[:100]}")
                            
                            # Exponential backoff
                            await asyncio.sleep(2 ** attempt)
                            continue
                        
                        try:
                            data = await resp.json()
                            LOGGER.debug(f"API Response Keys: {list(data.keys()) if data else 'None'}")
                            return data
                        except Exception as e:
                            LOGGER.error(f"JSON parsing error: {e}")
                            if attempt == max_retries - 1:
                                raise Exception(f"Failed to parse API response: {e}")
                            await asyncio.sleep(2 ** attempt)
                            continue
                            
            except asyncio.TimeoutError:
                LOGGER.warning(f"API request timeout on attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise Exception("API request timeout after multiple retries")
                await asyncio.sleep(2 ** attempt)
                continue
                
            except Exception as e:
                LOGGER.error(f"API request error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                continue
        
        return None

    async def process_terabox(self) -> None:
        """
        Process Terabox link and initiate download.
        
        Fetches download links from API with priority and initiates aria2 download.
        """
        msg = None
        try:
            msg = await send_message(
                self.message, 
                "🔄 Processing Terabox Link...\n📊 Fetching download information..."
            )
            
            # Build API URL
            api_url = f"{Config.TERABOX_API}{quote(self.link)}"
            LOGGER.info(f"Terabox API URL: {api_url}")
            
            # Fetch data with retry
            data = await self._fetch_api_with_retry(api_url)
            
            if not data or not isinstance(data, dict):
                await msg.edit("❌ Invalid or empty API response received.")
                return

            # Extract download links with priority
            valid_links = self._extract_download_links(data)

            if not valid_links:
                await msg.edit(
                    "❌ No valid download links found from API.\n"
                    "The link may be expired or invalid."
                )
                return

            LOGGER.info(f"Found {len(valid_links)} valid download link(s)")
            
            # Set primary link and fallbacks
            self.link = valid_links[0]
            if len(valid_links) > 1:
                self.fallback_links = valid_links[1:]
                LOGGER.info(f"Using {len(self.fallback_links)} fallback link(s) for redundancy")

            # Extract metadata
            has_metadata = self._extract_metadata(data)
            
            # Update progress message
            if has_metadata and self.file_size > 0:
                size_str = get_readable_file_size(self.file_size)
                await msg.edit(
                    f"✅ File Found!\n\n"
                    f"📄 Name: {self.name}\n"
                    f"📦 Size: {size_str}\n"
                    f"📂 Type: {self.file_type}\n\n"
                    f"⬇️ Starting download..."
                )
            else:
                await msg.edit("✅ Download link obtained!\n⬇️ Starting download...")

            # Delete progress message after a short delay
            await asyncio.sleep(2)
            try:
                await msg.delete()
            except Exception:
                pass
            
            # Import download helper
            from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download
            
            # Start download process
            await self.on_download_start()
            
            # Set custom headers for aria2
            headers = [
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept: */*",
                "Accept-Language: en-US,en;q=0.9",
                "Connection: keep-alive",
            ]
            
            LOGGER.info(f"Initiating aria2 download for: {self.name}")
            await add_aria2_download(self, f"{self.mid}/", headers, None, None)
            
        except Exception as e:
            LOGGER.error(f"Error in process_terabox: {e}", exc_info=True)
            if msg:
                try:
                    await msg.edit(f"❌ Error: {str(e)[:200]}")
                except Exception:
                    pass
            raise
        finally:
            # Cleanup
            if msg:
                try:
                    await asyncio.sleep(5)
                    await msg.delete()
                except Exception:
                    pass


async def terabox(client, message):
    """
    Main command handler for Terabox downloads.
    
    Args:
        client: Telegram client instance
        message: Telegram message object
    """
    bot_loop.create_task(TeraboxListener(client, message).new_event())