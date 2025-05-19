from typing import Optional, Union
from bot.helper.ext_utils.status_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
)


class YtDlpStatus:
    """Status class for tracking yt-dlp download progress."""
    
    def __init__(self, listener: object, obj: object, gid: str) -> None:
        """
        Initialize YtDlpStatus.
        
        Args:
            listener: The listener object for callbacks
            obj: The download helper object containing progress info
            gid: The download group ID
        """
        self._obj = obj
        self._gid = gid
        self.listener = listener
        self.tool = "yt-dlp"

    def gid(self) -> str:
        """Get the download group ID."""
        return self._gid

    def processed_bytes(self) -> str:
        """Get the processed bytes in human-readable format."""
        return get_readable_file_size(self._obj.downloaded_bytes)

    def size(self) -> str:
        """Get the total size in human-readable format."""
        return get_readable_file_size(self._obj.size)

    def status(self) -> str:
        """Get the current download status."""
        return MirrorStatus.STATUS_DOWNLOADING

    def name(self) -> str:
        """Get the name of the download."""
        return self.listener.name

    def progress(self) -> str:
        """Get the download progress percentage."""
        return f"{round(self._obj.progress, 2)}%"

    def speed(self) -> str:
        """Get the download speed in human-readable format."""
        return f"{get_readable_file_size(self._obj.download_speed)}/s"

    def eta(self) -> str:
        """Get the estimated time remaining for download completion."""
        if self._obj.eta != "-":
            return get_readable_time(self._obj.eta)
        
        return self._calculate_eta()

    def _calculate_eta(self) -> str:
        """Calculate ETA when not directly available."""
        try:
            remaining_bytes = self._obj.size - self._obj.downloaded_bytes
            if remaining_bytes <= 0 or self._obj.download_speed <= 0:
                return "-"
                
            seconds = remaining_bytes / self._obj.download_speed
            return get_readable_time(seconds)
        except (AttributeError, TypeError, ZeroDivisionError):
            return "-"

    def task(self) -> object:
        """Get the underlying download task object."""
        return self._obj
