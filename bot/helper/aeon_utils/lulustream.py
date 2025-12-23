import aiohttp
import os
from bot import LOGGER

class LuluStream:
    def __init__(self, api_key):
        self.api_key = api_key.strip()
        self.base_url = "https://lulustream.com/api/"

    async def get_upload_server(self):
        url = f"{self.base_url}upload/server?key={self.api_key}"
        LOGGER.info(f"LuluStream Key Diagnostic: Length={len(self.api_key)}, Key={self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else ''}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == 200:
                            return data.get("result")
                        else:
                            LOGGER.error(f"LuluStream API Error: {data.get('msg')} | Full Response: {data}")
                    else:
                        LOGGER.error(f"LuluStream Server Error: {resp.status}")
        except Exception as e:
            LOGGER.error(f"LuluStream Request Exception: {e}")
        return None

    async def upload_file(self, file_path, file_title=None):
        server_url = await self.get_upload_server()
        if not server_url:
            return None
        
        filename = os.path.basename(file_path)
        title = file_title or filename

        try:
            # Note: For very large files, this might consume memory. 
            # But usually it's fine for small to medium video files.
            data = aiohttp.FormData()
            data.add_field('key', self.api_key)
            data.add_field('file', open(file_path, 'rb'), filename=filename)
            data.add_field('file_title', title)

            async with aiohttp.ClientSession() as session:
                async with session.post(server_url, data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("status") == 200:
                            files = result.get("files", [])
                            if files:
                                file_code = files[0].get("filecode")
                                return f"https://lulustream.com/{file_code}"
                        else:
                            LOGGER.error(f"LuluStream Upload API Error: {result.get('msg')}")
                    else:
                        LOGGER.error(f"LuluStream Upload HTTP Error: {resp.status}")
        except Exception as e:
            LOGGER.error(f"LuluStream Upload Exception: {e}")
        return None
