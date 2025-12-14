"""
Compression State Manager

Manages user compression session state including selections,
temporary files, and session timeouts.
"""

from asyncio import Lock
from dataclasses import dataclass, field
from time import time
from typing import Optional

from aiofiles.os import path as aiopath
from aiofiles.os import remove as aioremove

from bot import LOGGER


@dataclass
class CompressionState:
    """Stores compression session state for a user"""

    user_id: int
    message_id: int
    video_url: Optional[str] = None
    video_file_path: Optional[str] = None
    partial_file_path: Optional[str] = None
    output_file_path: Optional[str] = None

    # Metadata
    duration: int = 0
    resolution: str = ""
    file_size: int = 0
    format_name: str = ""

    # Available tracks
    audio_tracks: list = field(default_factory=list)
    subtitle_tracks: list = field(default_factory=list)
    video_tracks: list = field(default_factory=list)

    # User selections
    selected_audio_tracks: list = field(default_factory=list)
    selected_subtitle_tracks: list = field(default_factory=list)
    compression_level: str = "medium"

    # State management
    created_at: float = field(default_factory=time)
    last_activity: float = field(default_factory=time)
    workflow_step: str = "initial"  # initial, selecting, confirmed, processing, completed
    is_cancelled: bool = False

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time()

    def is_expired(self, timeout: int = 600) -> bool:
        """Check if session has expired (default 10 minutes)"""
        return (time() - self.last_activity) > timeout

    async def cleanup_files(self):
        """Clean up temporary files"""
        files_to_remove = [
            self.partial_file_path,
            self.video_file_path,
            self.output_file_path,
        ]

        for file_path in files_to_remove:
            if file_path and await aiopath.exists(file_path):
                try:
                    await aioremove(file_path)
                    LOGGER.info(f"Cleaned up file: {file_path}")
                except Exception as e:
                    LOGGER.error(f"Failed to cleanup file {file_path}: {e}")


class CompressionStateManager:
    """Global manager for compression sessions"""

    def __init__(self):
        self._sessions: dict[int, CompressionState] = {}
        self._lock = Lock()

    async def create_session(self, user_id: int, message_id: int) -> CompressionState:
        """Create a new compression session"""
        async with self._lock:
            # Clean up old session if exists
            if user_id in self._sessions:
                await self.remove_session(user_id)

            session = CompressionState(user_id=user_id, message_id=message_id)
            self._sessions[user_id] = session
            LOGGER.info(f"Created compression session for user {user_id}")
            return session

    async def get_session(self, user_id: int) -> Optional[CompressionState]:
        """Get existing session"""
        async with self._lock:
            session = self._sessions.get(user_id)
            if session:
                if session.is_expired():
                    LOGGER.info(
                        f"Session expired for user {user_id}, cleaning up",
                    )
                    await self.remove_session(user_id)
                    return None
                session.update_activity()
            return session

    async def remove_session(self, user_id: int):
        """Remove and cleanup session"""
        async with self._lock:
            if user_id in self._sessions:
                session = self._sessions[user_id]
                await session.cleanup_files()
                del self._sessions[user_id]
                LOGGER.info(f"Removed compression session for user {user_id}")

    async def cleanup_expired_sessions(self):
        """Clean up all expired sessions"""
        async with self._lock:
            expired_users = [
                user_id
                for user_id, session in self._sessions.items()
                if session.is_expired()
            ]

            for user_id in expired_users:
                await self.remove_session(user_id)

            if expired_users:
                LOGGER.info(f"Cleaned up {len(expired_users)} expired sessions")


# Global state manager instance
compression_state_manager = CompressionStateManager()
