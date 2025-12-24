import aiohttp
import io
import os
from urllib.parse import quote
from bot import LOGGER

class LuluStream:
    def __init__(self, api_key):
        self.api_key = api_key.strip()
        self.base_url = "https://lulustream.com/api/"

    async def get_upload_server(self):
        # URL-encode the API key to handle special characters
        encoded_key = quote(self.api_key, safe='')
        url = f"{self.base_url}upload/server?key={encoded_key}"
        LOGGER.info(f"LuluStream Key Diagnostic: Length={len(self.api_key)}, Key={self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else ''}")
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                async with session.get(url, headers=headers, timeout=15) as resp:
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

    async def upload_file(self, file_path, file_title=None, progress_callback=None):
        server_url = await self.get_upload_server()
        if not server_url:
            return None
        
        filename = os.path.basename(file_path)
        title = file_title or filename
        
        try:
            # Read file in chunks to track progress
            file_size = os.path.getsize(file_path)
            
            if progress_callback:
                # Read file into memory with progress tracking
                file_data = bytearray()
                chunk_size = 1024 * 1024  # 1MB chunks
                
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        file_data.extend(chunk)
                        progress_callback(len(file_data))
                
                # Upload the complete data
                data = aiohttp.FormData()
                data.add_field('key', self.api_key)
                data.add_field('file', bytes(file_data), filename=filename, content_type='application/octet-stream')
                data.add_field('file_title', title)
            else:
                # No progress tracking, read file directly
                data = aiohttp.FormData()
                data.add_field('key', self.api_key)
                
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                data.add_field('file', file_content, filename=filename, content_type='application/octet-stream')
                data.add_field('file_title', title)
            
            # Upload (works for both progress and non-progress cases)
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
                        error_text = await resp.text()
                        LOGGER.error(f"LuluStream Upload HTTP Error: {resp.status} | Response: {error_text[:500]}")
        except Exception as e:
            LOGGER.error(f"LuluStream Upload Exception: {e}")
        return None
