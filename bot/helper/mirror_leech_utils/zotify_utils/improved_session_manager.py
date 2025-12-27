"""
Simple Zotify Session Manager
Maintains sessions for 1 hour of inactivity with minimal complexity
"""

import asyncio
import contextlib
import time
from typing import Any

from zotify import Session

from bot import LOGGER
from bot.helper.mirror_leech_utils.zotify_utils.zotify_config import zotify_config


class SimpleZotifySessionManager:
    """Simple session manager that keeps sessions alive for 1 hour of inactivity"""

    def __init__(self):
        self._session: Session | None = None
        self._last_activity = 0
        self._inactivity_timeout = 3600  # 1 hour of inactivity
        self._session_lock = asyncio.Lock()

    async def get_session(self) -> Session | None:
        """Get session, creating if needed or if inactive for 1 hour"""
        async with self._session_lock:
            current_time = time.time()

            # Check if session exists and is still active (within 1 hour)
            if self._session and self._last_activity > 0:
                time_since_activity = current_time - self._last_activity
                if time_since_activity <= self._inactivity_timeout:
                    # Session is still active, update activity and return
                    self._last_activity = current_time
                    return self._session
                # Session has been inactive for more than 1 hour, close it
                LOGGER.info(
                    f"Session inactive for {time_since_activity:.0f}s, closing"
                )
                await self._close_session()

            # Create new session
            if await self._create_session():
                self._last_activity = current_time
                return self._session

            return None

    def mark_activity(self):
        """Mark activity to keep session alive"""
        self._last_activity = time.time()

    async def _close_session(self):
        """Close the current session"""
        if self._session:
            with contextlib.suppress(Exception):
                self._session.close()
            self._session = None
            LOGGER.info("Session closed")

    async def _create_session(self) -> bool:
        """Create a new Zotify session"""
        try:
            LOGGER.info("Creating Zotify session...")

            # Close existing session if any
            await self._close_session()

            # Get credentials and create session
            auth_method = zotify_config.get_auth_method()
            if auth_method != "file":
                LOGGER.error("Only file-based authentication is supported")
                return False

            # Load credentials
            from bot.core.config_manager import Config

            owner_id = getattr(Config, "OWNER_ID", None)
            credentials = await zotify_config.load_credentials(owner_id)

            if not credentials:
                LOGGER.error("No credentials available for session creation")
                return False

            credentials_path = zotify_config.get_credentials_path()
            language = zotify_config.get_language()

            # Suppress librespot logs
            import logging

            librespot_logger = logging.getLogger("librespot.core")
            original_level = librespot_logger.level
            librespot_logger.setLevel(logging.ERROR)

            try:
                # Create session
                self._session = await asyncio.to_thread(
                    Session.from_file, credentials_path, language
                )
                LOGGER.info("Zotify session created successfully")
                return True
            finally:
                librespot_logger.setLevel(original_level)

        except Exception as e:
            LOGGER.error(f"Session creation failed: {e}")
            return False

    async def api_call(self, endpoint: str) -> dict[Any, Any] | None:
        """Simple API call without complex retry logic"""
        try:
            session = await self.get_session()
            if not session:
                return None

            # Mark activity
            self.mark_activity()

            # Make API call
            api = await asyncio.to_thread(session.api)
            return await asyncio.to_thread(api.invoke_url, endpoint)

        except Exception as e:
            LOGGER.error(f"API call failed for {endpoint}: {e}")
            return None

    async def search(
        self, query: str, content_types: list | None = None
    ) -> dict[str, list]:
        """Simple search functionality"""
        if not content_types:
            content_types = ["track", "album", "playlist", "artist"]

        results = {}
        for content_type in content_types:
            try:
                endpoint = f"search?q={query}&type={content_type}&limit=10"
                search_result = await self.api_call(endpoint)

                if search_result and f"{content_type}s" in search_result:
                    results[content_type] = search_result[f"{content_type}s"][
                        "items"
                    ]
                else:
                    results[content_type] = []

            except Exception as e:
                LOGGER.error(f"Search failed for {content_type}: {e}")
                results[content_type] = []

        return results

    async def get_track(self, track_id: str) -> Any | None:
        """Get track by ID"""
        try:
            session = await self.get_session()
            if not session:
                return None

            self.mark_activity()
            return await asyncio.to_thread(session.get_track, track_id)

        except Exception as e:
            LOGGER.error(f"Failed to get track {track_id}: {e}")
            return None

    async def get_episode(self, episode_id: str) -> Any | None:
        """Get episode by ID"""
        try:
            session = await self.get_session()
            if not session:
                return None

            self.mark_activity()
            return await asyncio.to_thread(session.get_episode, episode_id)

        except Exception as e:
            LOGGER.error(f"Failed to get episode {episode_id}: {e}")
            return None

    def get_session_health(self) -> dict[str, Any]:
        """Get simple session health information"""
        current_time = time.time()
        time_since_activity = (
            current_time - self._last_activity if self._last_activity else 0
        )

        return {
            "has_session": self._session is not None,
            "time_since_last_activity": time_since_activity,
            "inactivity_timeout": self._inactivity_timeout,
            "is_healthy": (
                self._session is not None
                and time_since_activity < self._inactivity_timeout
            ),
        }

    async def close(self):
        """Clean up session"""
        await self._close_session()


# Global instance
simple_session_manager = SimpleZotifySessionManager()


# Convenience functions
async def get_session() -> Session | None:
    """Get session instance"""
    return await simple_session_manager.get_session()


async def search_music(
    query: str, content_types: list | None = None
) -> dict[str, list]:
    """Perform search"""
    return await simple_session_manager.search(query, content_types)


async def api_call(endpoint: str) -> dict[Any, Any] | None:
    """Make API call"""
    return await simple_session_manager.api_call(endpoint)
