import aiohttp
import aiofiles
import os
from urllib.parse import quote
from bot import LOGGER

# Supported video formats for LuluStream
VIDEO_FORMATS = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.m4v')

# Chunk size for streaming uploads (8MB chunks - balance between memory and upload efficiency)
CHUNK_SIZE = 8 * 1024 * 1024


class AsyncFileReader:
    """
    Async file reader that streams file content in chunks.
    Used for memory-efficient uploads without loading entire file into RAM.
    """
    def __init__(self, file_path, file_size, chunk_size=CHUNK_SIZE, progress_callback=None):
        self.file_path = file_path
        self.file_size = file_size
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback
        self.bytes_read = 0
        self._file = None
    
    async def __aenter__(self):
        self._file = await aiofiles.open(self.file_path, 'rb')
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            await self._file.close()
    
    async def read_chunk(self):
        """Read a single chunk from the file."""
        if self._file is None:
            return b''
        
        chunk = await self._file.read(self.chunk_size)
        if chunk:
            self.bytes_read += len(chunk)
            if self.progress_callback:
                try:
                    self.progress_callback(self.bytes_read)
                except Exception:
                    pass  # Ignore progress callback errors
        return chunk


async def async_file_generator(file_path, file_size, chunk_size=CHUNK_SIZE, progress_callback=None):
    """
    Async generator that yields file chunks for streaming upload.
    Memory efficient - only one chunk in memory at a time.
    """
    bytes_read = 0
    async with aiofiles.open(file_path, 'rb') as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            bytes_read += len(chunk)
            if progress_callback:
                try:
                    progress_callback(bytes_read)
                except Exception:
                    pass
            yield chunk


class LuluStream:
    """
    LuluStream API client for video hosting service.
    
    Handles authentication, server discovery, and file uploads to LuluStream.
    Uses streaming uploads to minimize memory usage for large files.
    
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
        Upload a video file to LuluStream using memory-efficient streaming.
        
        Args:
            file_path (str): Path to the video file to upload
            file_title (str, optional): Custom title for the video. Defaults to filename.
            progress_callback (callable, optional): Function called with bytes uploaded for progress tracking
            
        Returns:
            str: LuluStream video URL if successful, None otherwise
            
        Note:
            - Uses streaming upload to avoid loading entire file into memory
            - Only ~8MB chunk in memory at any time regardless of file size
            - Safe for large files on memory-constrained environments (e.g., Heroku)
        """
        server_url = await self.get_upload_server()
        if not server_url:
            return None
        
        filename = os.path.basename(file_path)
        title = file_title or filename
        
        try:
            # Get file size and log it in human-readable format
            file_size = os.path.getsize(file_path)
            
            if file_size >= 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
            elif file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            elif file_size >= 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size} bytes"
            
            LOGGER.info(f"LuluStream Upload Starting (Streaming): {filename} | Size: {size_str} | Title: {title}")
            
            # Use multipart/form-data with streaming file upload
            # This approach uses aiohttp's built-in streaming with file path
            with aiohttp.MultipartWriter('form-data') as mpwriter:
                # Add API key field
                key_part = mpwriter.append(self.api_key)
                key_part.set_content_disposition('form-data', name='key')
                
                # Add file title field
                title_part = mpwriter.append(title)
                title_part.set_content_disposition('form-data', name='file_title')
                
                # Add file with streaming - aiohttp will stream from disk
                file_part = mpwriter.append(open(file_path, 'rb'))
                file_part.set_content_disposition('form-data', name='file', filename=filename)
                file_part.headers['Content-Type'] = 'application/octet-stream'
                
                # Create timeout config for large files (1 hour total, no read timeout during upload)
                timeout = aiohttp.ClientTimeout(total=7200, connect=60, sock_read=None)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Signal start of upload
                    if progress_callback:
                        try:
                            progress_callback(0)
                        except Exception:
                            pass
                    
                    async with session.post(server_url, data=mpwriter) as resp:
                        # Signal completion
                        if progress_callback:
                            try:
                                progress_callback(file_size)
                            except Exception:
                                pass
                        
                        if resp.status == 200:
                            result = await resp.json()
                            if result.get("status") == 200:
                                files = result.get("files", [])
                                if files:
                                    file_code = files[0].get("filecode")
                                    LOGGER.info(f"LuluStream Upload Success: {filename} -> https://lulustream.com/{file_code}")
                                    return f"https://lulustream.com/{file_code}"
                            else:
                                LOGGER.error(f"LuluStream Upload API Error: {result.get('msg')}")
                        else:
                            error_text = await resp.text()
                            LOGGER.error(f"LuluStream Upload HTTP Error: {resp.status} | Response: {error_text[:500]}")
        except Exception as e:
            LOGGER.error(f"LuluStream Upload Exception: {type(e).__name__}: {e}")
        return None