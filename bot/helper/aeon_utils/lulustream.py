import aiohttp
import io
import os
from urllib.parse import quote
from bot import LOGGER

# Supported video formats for LuluStream
VIDEO_FORMATS = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.m4v')

class LuluStream:
    """
    LuluStream API client for video hosting service.
    
    Handles authentication, server discovery, and file uploads to LuluStream.
    Supports progress tracking during uploads.
    
    Attributes:
        api_key (str): User's LuluStream API key
        base_url (str): Base URL for LuluStream API endpoints
    """
    def __init__(self, api_key):
        self.api_key = api_key.strip()
        self.base_url = "https://lulustream.com/api/"

    async def get_upload_server(self):
        """
        Get upload server URL from LuluStream API.
        
        Returns:
            str: Upload server URL if successful, None otherwise
            
        Note:
            The API key is URL-encoded to handle special characters properly.
        """
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
        """
        Upload a video file to LuluStream using streaming to minimize memory usage.
        
        Args:
            file_path (str): Path to the video file to upload
            file_title (str, optional): Custom title for the video. Defaults to filename.
            progress_callback (callable, optional): Function called with bytes uploaded for progress tracking
            
        Returns:
            str: LuluStream video URL if successful, None otherwise
            
        Note:
            - Uses aiohttp's built-in file streaming to avoid loading entire file into memory
            - Supports progress tracking with custom wrapper
        """
        server_url = await self.get_upload_server()
        if not server_url:
            return None
        
        filename = os.path.basename(file_path)
        title = file_title or filename
        
        try:
            file_size = os.path.getsize(file_path)
            
            if progress_callback:
                # Create a wrapper that tracks progress while reading
                class ProgressFileReader:
                    """File-like object that tracks upload progress."""
                    def __init__(self, path, callback):
                        self.path = path
                        self.callback = callback
                        self.uploaded_bytes = 0
                        self._file = open(path, 'rb')
                        self.mode = 'rb'
                        self.name = path
                    
                    def read(self, size=-1):
                        """Read method called by aiohttp during upload."""
                        chunk = self._file.read(size)
                        if chunk:
                            self.uploaded_bytes += len(chunk)
                            self.callback(self.uploaded_bytes)
                        return chunk
                    
                    def seek(self, offset, whence=0):
                        """Seek to position in file."""
                        return self._file.seek(offset, whence)
                    
                    def tell(self):
                        """Return current position in file."""
                        return self._file.tell()
                    
                    def close(self):
                        """Close the underlying file."""
                        if self._file:
                            self._file.close()
                    
                    def __enter__(self):
                        return self
                    
                    def __exit__(self, *args):
                        self.close()
                
                # Use progress wrapper
                file_obj = ProgressFileReader(file_path, progress_callback)
                
                # Prepare form data
                data = aiohttp.FormData()
                data.add_field('key', self.api_key)
                data.add_field('file', file_obj, filename=filename, content_type='application/octet-stream')
                data.add_field('file_title', title)
                
                try:
                    # Upload with progress tracking
                    async with aiohttp.ClientSession() as session:
                        async with session.post(server_url, data=data, timeout=aiohttp.ClientTimeout(total=3600)) as resp:
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
                finally:
                    file_obj.close()
            else:
                # No progress tracking - use simple file upload
                data = aiohttp.FormData()
                data.add_field('key', self.api_key)
                
                # Open file and add to form - aiohttp streams it automatically
                with open(file_path, 'rb') as f:
                    data.add_field('file', f, filename=filename, content_type='application/octet-stream')
                    
                    # Upload
                    async with aiohttp.ClientSession() as session:
                        async with session.post(server_url, data=data, timeout=aiohttp.ClientTimeout(total=3600)) as resp:
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
