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
            - Streams file in 1MB chunks to avoid loading entire file into memory
            - Supports progress tracking without memory accumulation
        """
        server_url = await self.get_upload_server()
        if not server_url:
            return None
        
        filename = os.path.basename(file_path)
        title = file_title or filename
        
        try:
            file_size = os.path.getsize(file_path)
            
            # Create async file stream iterator with progress tracking
            class FileStreamWithProgress:
                """Async iterator that streams file in chunks with progress tracking."""
                def __init__(self, path, chunk_size=1024*1024, callback=None):
                    self.path = path
                    self.chunk_size = chunk_size
                    self.callback = callback
                    self.uploaded_bytes = 0
                
                async def __aiter__(self):
                    # Import aiofiles for async file operations
                    try:
                        import aiofiles
                        async with aiofiles.open(self.path, 'rb') as f:
                            while True:
                                chunk = await f.read(self.chunk_size)
                                if not chunk:
                                    break
                                self.uploaded_bytes += len(chunk)
                                if self.callback:
                                    self.callback(self.uploaded_bytes)
                                yield chunk
                    except ImportError:
                        # Fallback to synchronous file operations if aiofiles not available
                        LOGGER.warning("aiofiles not available, using sync file operations")
                        with open(self.path, 'rb') as f:
                            while True:
                                chunk = f.read(self.chunk_size)
                                if not chunk:
                                    break
                                self.uploaded_bytes += len(chunk)
                                if self.callback:
                                    self.callback(self.uploaded_bytes)
                                yield chunk
            
            # Prepare form data with streaming file
            data = aiohttp.FormData()
            data.add_field('key', self.api_key)
            
            # Use streaming iterator - this doesn't load file into memory
            file_stream = FileStreamWithProgress(file_path, callback=progress_callback)
            data.add_field('file', file_stream, filename=filename, content_type='application/octet-stream')
            data.add_field('file_title', title)
            
            # Upload with streaming
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
