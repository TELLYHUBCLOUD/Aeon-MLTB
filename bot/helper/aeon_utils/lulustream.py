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
            # Wrap file object to track progress
            file_size = os.path.getsize(file_path)
            
            # Using a custom reader or feeding chunks if possible, but aiohttp FormData handles files directly.
            # To track progress with aiohttp client, we can't easily hook into the request body write unless we provide a stream.
            # A simple way for smaller files is to read chunks, but for large files we need a proper async generator or 
            # we can rely on a custom IO wrapper.
            
            class ProgressReader:
                def __init__(self, filename, callback):
                    self._file = open(filename, 'rb')
                    self._callback = callback
                    self._total_read = 0

                def read(self, size=-1):
                    chunk = self._file.read(size)
                    if chunk:
                        self._total_read += len(chunk)
                        if self._callback:
                            self._callback(self._total_read)
                    return chunk

                def close(self):
                    self._file.close()

            # Note: For strict async with aiohttp, we ideally want async file read, but doing it sync in thread or simple read usually works for upload logic if main loop isn't blocked heavily. 
            # However, aiohttp FormData expects a file-like object or bytes.
            # A wrapper around the open file that updates progress on read() is the standard way.
            
            f = ProgressReader(file_path, progress_callback)
            
            data = aiohttp.FormData()
            data.add_field('key', self.api_key)
            data.add_field('file', f, filename=filename)
            data.add_field('file_title', title)

            async with aiohttp.ClientSession() as session:
                async with session.post(server_url, data=data) as resp:
                    f.close()
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
