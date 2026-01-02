"""
Gallery-dl quality selector
"""

import asyncio
import re
from time import time
from typing import Any, ClassVar

from bot import LOGGER

# Import Telegram helpers with error handling
try:
    from bot.helper.telegram_helper.button_build import ButtonMaker
    from bot.helper.telegram_helper.message_utils import (
        edit_message,
        send_message,
    )

    TELEGRAM_AVAILABLE = True
except Exception as e:
    LOGGER.warning(f"Telegram helpers not available: {e}")
    TELEGRAM_AVAILABLE = False

    # Mock classes for testing
    class ButtonMaker:
        def __init__(self):
            pass

        def data_button(self, text, data):
            pass

        def build_menu(self, cols):
            return []

    async def edit_message(message, text, buttons=None):
        pass

    async def send_message(message, text, buttons=None):
        pass


# Global registry for quality selectors (following streamrip pattern)
_gallery_dl_quality_selectors = {}


def register_gallery_dl_quality_selector(user_id: int, selector):
    """Register quality selector for user"""
    _gallery_dl_quality_selectors[user_id] = selector


def unregister_gallery_dl_quality_selector(user_id: int):
    """Unregister quality selector for user"""
    _gallery_dl_quality_selectors.pop(user_id, None)


def get_gallery_dl_quality_selector(user_id: int):
    """Get quality selector for user"""
    return _gallery_dl_quality_selectors.get(user_id)


class GalleryDLQualitySelector:
    """Gallery-dl quality selector following streamrip pattern"""

    # Platform-specific quality options based on comprehensive gallery-dl analysis
    # Supports 157 platforms with 626 extractors (excluding 40+ adult sites)
    PLATFORM_QUALITIES: ClassVar[dict[str, Any]] = {
        # Social Media Platforms (7 platforms, 6 require auth)
        "instagram": {
            "original": {
                "name": "Original Quality",
                "description": "Best available quality",
                "emoji": "💎",
            },
            "high": {
                "name": "High Quality",
                "description": "Compressed but high quality",
                "emoji": "🔸",
            },
            "medium": {
                "name": "Medium Quality",
                "description": "Balanced size/quality",
                "emoji": "🔹",
            },
            "low": {
                "name": "Low Quality",
                "description": "Smallest size",
                "emoji": "📱",
            },
        },
        "twitter": {
            "orig": {
                "name": "Original",
                "description": "Best quality (orig)",
                "emoji": "💎",
            },
            "4096x4096": {
                "name": "4K",
                "description": "4096x4096 resolution",
                "emoji": "🔸",
            },
            "large": {
                "name": "Large",
                "description": "High quality (large)",
                "emoji": "🔹",
            },
            "medium": {
                "name": "Medium",
                "description": "Medium quality",
                "emoji": "📱",
            },
            "small": {
                "name": "Small",
                "description": "Low quality (small)",
                "emoji": "📶",
            },
        },
        "tiktok": {
            "best": {
                "name": "Best Quality",
                "description": "Highest available",
                "emoji": "💎",
            },
            "720p": {
                "name": "720p HD",
                "description": "High definition",
                "emoji": "🔸",
            },
            "480p": {
                "name": "480p",
                "description": "Standard definition",
                "emoji": "🔹",
            },
            "360p": {"name": "360p", "description": "Low definition", "emoji": "📱"},
        },
        "facebook": {
            "original": {
                "name": "Original",
                "description": "Best available quality",
                "emoji": "💎",
            },
            "hd": {
                "name": "HD Quality",
                "description": "High definition",
                "emoji": "🔸",
            },
            "sd": {
                "name": "SD Quality",
                "description": "Standard definition",
                "emoji": "🔹",
            },
        },
        "youtube": {
            "best": {
                "name": "Best Quality",
                "description": "Highest available",
                "emoji": "💎",
            },
            "2160p": {
                "name": "4K (2160p)",
                "description": "Ultra HD",
                "emoji": "🔸",
            },
            "1440p": {"name": "1440p", "description": "Quad HD", "emoji": "🔹"},
            "1080p": {"name": "1080p", "description": "Full HD", "emoji": "📺"},
            "720p": {"name": "720p", "description": "HD", "emoji": "📱"},
            "480p": {"name": "480p", "description": "SD", "emoji": "📶"},
            "360p": {"name": "360p", "description": "Low quality", "emoji": "📉"},
        },
        "reddit": {
            "source": {
                "name": "Source",
                "description": "Original quality",
                "emoji": "💎",
            },
            "high": {"name": "High", "description": "High quality", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium quality",
                "emoji": "🔹",
            },
            "low": {"name": "Low", "description": "Low quality", "emoji": "📱"},
        },
        "tumblr": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "1280": {"name": "1280px", "description": "Large size", "emoji": "🔸"},
            "540": {"name": "540px", "description": "Medium size", "emoji": "🔹"},
            "250": {"name": "250px", "description": "Small size", "emoji": "📱"},
        },
        # Art & Photography Platforms
        "deviantart": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "fullview": {
                "name": "Full View",
                "description": "High quality view",
                "emoji": "🔸",
            },
            "preview": {
                "name": "Preview",
                "description": "Preview quality",
                "emoji": "🔹",
            },
        },
        "pixiv": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "large": {"name": "Large", "description": "Large size", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "🔹",
            },
            "square_medium": {
                "name": "Square Medium",
                "description": "Square thumbnail",
                "emoji": "📱",
            },
        },
        "artstation": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "large": {"name": "Large", "description": "Large size", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "🔹",
            },
            "small": {"name": "Small", "description": "Small size", "emoji": "📱"},
        },
        "flickr": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "large": {"name": "Large", "description": "Large size", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "🔹",
            },
            "small": {"name": "Small", "description": "Small size", "emoji": "📱"},
        },
        "500px": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "large": {"name": "Large", "description": "Large size", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "🔹",
            },
        },
        "behance": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "large": {"name": "Large", "description": "Large size", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "🔹",
            },
        },
        "pinterest": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "large": {"name": "Large", "description": "Large size", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "🔹",
            },
            "small": {"name": "Small", "description": "Small size", "emoji": "📱"},
        },
        "unsplash": {
            "full": {
                "name": "Full",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "regular": {
                "name": "Regular",
                "description": "Regular size",
                "emoji": "🔸",
            },
            "small": {"name": "Small", "description": "Small size", "emoji": "🔹"},
            "thumb": {
                "name": "Thumbnail",
                "description": "Thumbnail size",
                "emoji": "📱",
            },
        },
        # Image Hosting & File Sharing
        "imgur": {
            "original": {
                "name": "Original",
                "description": "Full size",
                "emoji": "💎",
            },
            "huge": {"name": "Huge", "description": "Large size", "emoji": "🔸"},
            "large": {
                "name": "Large",
                "description": "Medium-large size",
                "emoji": "🔹",
            },
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "📱",
            },
            "small": {"name": "Small", "description": "Small size", "emoji": "📶"},
        },
        "catbox": {
            "original": {
                "name": "Original",
                "description": "As uploaded",
                "emoji": "💎",
            },
        },
        "gofile": {
            "original": {
                "name": "Original",
                "description": "As uploaded",
                "emoji": "💎",
            },
        },
        "postimg": {
            "original": {
                "name": "Original",
                "description": "Full size",
                "emoji": "💎",
            },
        },
        # Booru Sites (SFW only)
        "danbooru": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "sample": {
                "name": "Sample",
                "description": "Sample size",
                "emoji": "🔸",
            },
            "preview": {
                "name": "Preview",
                "description": "Preview size",
                "emoji": "🔹",
            },
        },
        "safebooru": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "sample": {
                "name": "Sample",
                "description": "Sample size",
                "emoji": "🔸",
            },
            "preview": {
                "name": "Preview",
                "description": "Preview size",
                "emoji": "🔹",
            },
        },
        "gelbooru": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "sample": {
                "name": "Sample",
                "description": "Sample size",
                "emoji": "🔸",
            },
            "preview": {
                "name": "Preview",
                "description": "Preview size",
                "emoji": "🔹",
            },
        },
        # Manga & Comics
        "mangadex": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "high": {"name": "High", "description": "High quality", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium quality",
                "emoji": "🔹",
            },
            "low": {"name": "Low", "description": "Low quality", "emoji": "📱"},
        },
        "dynasty": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
        },
        "mangakakalot": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
        },
        # Video Platforms
        "bilibili": {
            "1080p": {"name": "1080p", "description": "Full HD", "emoji": "💎"},
            "720p": {"name": "720p", "description": "HD", "emoji": "🔸"},
            "480p": {"name": "480p", "description": "SD", "emoji": "🔹"},
            "360p": {"name": "360p", "description": "Low quality", "emoji": "📱"},
        },
        "vimeo": {
            "original": {
                "name": "Original",
                "description": "Best available",
                "emoji": "💎",
            },
            "1080p": {"name": "1080p", "description": "Full HD", "emoji": "🔸"},
            "720p": {"name": "720p", "description": "HD", "emoji": "🔹"},
            "480p": {"name": "480p", "description": "SD", "emoji": "📱"},
        },
        "twitch": {
            "source": {
                "name": "Source",
                "description": "Original quality",
                "emoji": "💎",
            },
            "1080p": {"name": "1080p", "description": "Full HD", "emoji": "🔸"},
            "720p": {"name": "720p", "description": "HD", "emoji": "🔹"},
            "480p": {"name": "480p", "description": "SD", "emoji": "📱"},
        },
        "dailymotion": {
            "auto": {"name": "Auto", "description": "Best available", "emoji": "💎"},
            "1080": {"name": "1080p", "description": "Full HD", "emoji": "🔸"},
            "720": {"name": "720p", "description": "HD", "emoji": "🔹"},
            "480": {"name": "480p", "description": "SD", "emoji": "📱"},
        },
        # Professional & Subscription Platforms
        "patreon": {
            "original": {
                "name": "Original",
                "description": "Full quality",
                "emoji": "💎",
            },
            "high": {"name": "High", "description": "High quality", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium quality",
                "emoji": "🔹",
            },
        },
        "fanbox": {
            "original": {
                "name": "Original",
                "description": "Full quality",
                "emoji": "💎",
            },
            "high": {"name": "High", "description": "High quality", "emoji": "🔸"},
        },
        "gumroad": {
            "original": {
                "name": "Original",
                "description": "Full quality",
                "emoji": "💎",
            },
        },
        # Alternative Social Media
        "mastodon": {
            "original": {
                "name": "Original",
                "description": "Full size",
                "emoji": "💎",
            },
            "small": {"name": "Small", "description": "Thumbnail", "emoji": "🔹"},
        },
        "bluesky": {
            "fullsize": {
                "name": "Full Size",
                "description": "Original size",
                "emoji": "💎",
            },
            "thumbnail": {
                "name": "Thumbnail",
                "description": "Small size",
                "emoji": "🔹",
            },
        },
        "discord": {
            "original": {
                "name": "Original",
                "description": "As uploaded",
                "emoji": "💎",
            },
        },
        # News & Media
        "bbc": {
            "original": {
                "name": "Original",
                "description": "Best available",
                "emoji": "💎",
            },
            "high": {"name": "High", "description": "High quality", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium quality",
                "emoji": "🔹",
            },
        },
        "cnn": {
            "original": {
                "name": "Original",
                "description": "Best available",
                "emoji": "💎",
            },
        },
        # Gaming & Entertainment
        "newgrounds": {
            "original": {
                "name": "Original",
                "description": "Best available",
                "emoji": "💎",
            },
            "high": {"name": "High", "description": "High quality", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium quality",
                "emoji": "🔹",
            },
        },
        "itch": {
            "original": {
                "name": "Original",
                "description": "As uploaded",
                "emoji": "💎",
            },
        },
        # Wallpaper & Design Sites
        "wallhaven": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
            "large": {"name": "Large", "description": "Large size", "emoji": "🔸"},
            "medium": {
                "name": "Medium",
                "description": "Medium size",
                "emoji": "🔹",
            },
        },
        "wallpaperscraft": {
            "original": {
                "name": "Original",
                "description": "Full resolution",
                "emoji": "💎",
            },
        },
        # Default fallback
        "default": {
            "original": {
                "name": "Original Quality",
                "description": "Best available",
                "emoji": "💎",
            },
            "high": {
                "name": "High Quality",
                "description": "High quality",
                "emoji": "🔸",
            },
            "medium": {
                "name": "Medium Quality",
                "description": "Medium quality",
                "emoji": "🔹",
            },
            "low": {
                "name": "Low Quality",
                "description": "Low quality",
                "emoji": "📱",
            },
        },
    }

    # Comprehensive platform detection mapping (80+ domains, 60+ platforms)
    # Based on gallery-dl v1.29.7 extractor analysis (excluding adult sites)
    PLATFORM_DETECTION = {
        # Social Media (7 platforms)
        "x.com": "twitter",
        "twitter.com": "twitter",
        "t.co": "twitter",
        "instagram.com": "instagram",
        "tiktok.com": "tiktok",
        "vm.tiktok.com": "tiktok",
        "facebook.com": "facebook",
        "fb.com": "facebook",
        "youtube.com": "youtube",
        "youtu.be": "youtube",
        "reddit.com": "reddit",
        "tumblr.com": "tumblr",
        # Art Platforms (8 platforms)
        "pixiv.net": "pixiv",
        "artstation.com": "artstation",
        "deviantart.com": "deviantart",
        "sta.sh": "deviantart",
        "flickr.com": "flickr",
        "500px.com": "500px",
        "behance.net": "behance",
        "pinterest.com": "pinterest",
        "unsplash.com": "unsplash",
        # Image Hosting (6 platforms)
        "imgur.com": "imgur",
        "catbox.moe": "catbox",
        "files.catbox.moe": "catbox",
        "gofile.io": "gofile",
        "postimg.cc": "postimg",
        "turboimagehost.com": "turboimagehost",
        "acidimg.cc": "acidimg",
        # Booru Sites - SFW (5 platforms)
        "danbooru.donmai.us": "danbooru",
        "safebooru.donmai.us": "safebooru",  # Fixed: safebooru uses donmai.us domain
        "safebooru.org": "safebooru",
        "gelbooru.com": "gelbooru",
        "twibooru.org": "twibooru",
        "zerochan.net": "zerochan",
        # Manga/Comics (6 platforms)
        "dynasty-scans.com": "dynastyscans",
        "xbato.org": "batoto",
        "mangadex.org": "mangadex",
        "tcbscans.me": "tcbscans",
        "webtoons.com": "webtoons",
        "tapas.io": "tapas",
        # Video Platforms (4 platforms)
        "bilibili.com": "bilibili",
        "space.bilibili.com": "bilibili",
        "vimeo.com": "vimeo",
        "twitch.tv": "twitch",
        "tenor.com": "tenor",
        # Professional (4 platforms)
        "patreon.com": "patreon",
        "fanbox.cc": "fanbox",
        "fantia.jp": "fantia",
        "boosty.to": "boosty",
        # News & Media (4 platforms)
        "bbc.co.uk": "bbc",
        "bbc.com": "bbc",
        "telegra.ph": "telegraph",
        "slideshare.net": "slideshare",
        "speakerdeck.com": "speakerdeck",
        # Gaming (3 platforms)
        "newgrounds.com": "newgrounds",
        "steamgriddb.com": "steamgriddb",
        "civitai.com": "civitai",
        # Wallpapers (3 platforms)
        "wallhaven.cc": "wallhaven",
        "wallpapercave.com": "wallpapercave",
        "desktopography.net": "desktopography",
        # Forums (4 platforms)
        "boards.4channel.org": "4chan",
        "boards.4chan.org": "4chan",
        "2ch.hk": "2ch",
        "8chan.moe": "8chan",
        "8kun.top": "8chan",
        "warosu.org": "warosu",
        # File Sharing (4 platforms)
        "cyberdrop.me": "cyberdrop",
        "bunkr.si": "bunkr",
        "saint2.su": "saint",
        "uploadir.com": "uploadir",
        # Alternative Social (2 platforms)
        "bsky.app": "bluesky",
        "discord.com": "discord",
        "mastodon": "mastodon",  # Various instances
        # Other Popular (8 platforms)
        "archiveofourown.org": "ao3",
        "weibo.com": "weibo",
        "vk.com": "vk",
        "wikiart.org": "wikiart",
        "vsco.co": "vsco",
        "arca.live": "arcalive",
        "architizer.com": "architizer",
        "toyhou.se": "toyhouse",
    }

    def __init__(
        self, listener, platform: str, content_type: str = "media", url: str = ""
    ):
        self.listener = listener
        self.platform = (
            self.detect_platform_from_url(url) if url else platform.lower()
        )
        self.content_type = content_type
        self.url = url
        self._reply_to = None
        self._time = time()
        self._timeout = 120
        self.event = asyncio.Event()
        self.selected_quality = None
        self.selected_format = None
        self._main_buttons = None

        # Set available qualities based on platform
        self.available_qualities = self.PLATFORM_QUALITIES.get(
            self.platform, self.PLATFORM_QUALITIES.get("default", {})
        )

    @classmethod
    def detect_platform_from_url(cls, url: str) -> str:
        """Detect platform from URL using comprehensive mapping"""
        if not url:
            return "default"

        url_lower = url.lower()

        # Extract domain from URL for more accurate matching
        domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url_lower)
        if domain_match:
            domain = domain_match.group(1)

            # Check for exact domain matches first (most specific)
            if domain in cls.PLATFORM_DETECTION:
                return cls.PLATFORM_DETECTION[domain]

            # Check for subdomain matches (e.g., user.tumblr.com)
            for detection_domain, platform in cls.PLATFORM_DETECTION.items():
                if (
                    domain.endswith("." + detection_domain)
                    or domain == detection_domain
                ):
                    return platform

        # Fallback: Check each domain in our detection mapping (less precise)
        # Sort by length (longest first) to avoid partial matches
        sorted_domains = sorted(
            cls.PLATFORM_DETECTION.items(), key=lambda x: len(x[0]), reverse=True
        )
        for domain, platform in sorted_domains:
            if domain in url_lower:
                return platform

        # Special handling for Mastodon instances (various domains)
        if any(
            mastodon_indicator in url_lower
            for mastodon_indicator in ["mastodon", "@", "/users/", "/web/@"]
        ) and not any(
            excluded in url_lower
            for excluded in ["twitter", "instagram", "facebook"]
        ):
            return "mastodon"

        # Default fallback
        return "default"

    @classmethod
    def get_platform_qualities(cls, platform: str) -> list[str]:
        """Get available quality options for a platform"""
        if not platform:
            platform = "default"

        platform = platform.lower()
        platform_config = cls.PLATFORM_QUALITIES.get(
            platform, cls.PLATFORM_QUALITIES.get("default", {})
        )

        return list(platform_config.keys())

    async def _register_handler_and_wait(self):
        """Register handler and wait for selection"""
        try:
            # Register in global registry
            register_gallery_dl_quality_selector(self.listener.user_id, self)

            # Wait for selection with timeout
            try:
                await asyncio.wait_for(self.event.wait(), timeout=self._timeout)
            except TimeoutError:
                from asyncio import create_task

                from bot.helper.telegram_helper.message_utils import (
                    auto_delete_message,
                    delete_message,
                    send_message,
                )

                LOGGER.warning(
                    f"Gallery-dl quality selection timeout for user {self.listener.user_id}"
                )

                # Send timeout message
                timeout_msg = await send_message(
                    self.listener.message,
                    f"{self.listener.tag} ⏰ Quality selection timed out. Task has been cancelled!",
                )

                # Delete the selection menu
                await delete_message(self._reply_to)

                # Delete the original command
                await delete_message(self.listener.message)

                # Create background task for auto-deletion
                create_task(
                    auto_delete_message(timeout_msg, time=300),
                )  # 5 minutes auto-delete

                # Cancel the task
                self.listener.is_cancelled = True
                self.selected_quality = None
                self.selected_format = None

        except Exception as e:
            LOGGER.error(f"Error in gallery-dl quality selection: {e}")
            # Use default quality on error
            self.selected_quality = "original"
            self.selected_format = "best"
        finally:
            # Clean up
            unregister_gallery_dl_quality_selector(self.listener.user_id)

    async def get_quality_selection(self) -> dict[str, Any] | None:
        """Show quality selection interface and get user choice"""
        try:
            # Show quality selection menu
            await self._show_quality_selection()

            # Register handler and wait for selection
            await self._register_handler_and_wait()

            # Check for cancellation
            if self.listener.is_cancelled or self.selected_quality is None:
                return None

            return {
                "quality": self.selected_quality,
                "format": self.selected_format or "best",
            }

        except Exception as e:
            LOGGER.error(f"Exception in gallery-dl quality selection: {e}")
            return None

    async def _show_quality_selection(self):
        """Show quality selection buttons"""
        if not TELEGRAM_AVAILABLE:
            LOGGER.warning("Telegram not available, skipping quality selection UI")
            return

        buttons = ButtonMaker()

        # Platform info header
        platform_name = self.platform.title()
        msg = f"<b>🖼️ Quality Selection for {platform_name}</b>\n"
        msg += (
            f"<b>📁 Content Type:</b> <code>{self.content_type.title()}</code>\n\n"
        )

        # Add quality buttons
        for quality_key, quality_info in self.available_qualities.items():
            button_text = f"{quality_info['emoji']} {quality_info['name']}"
            button_text += f"\n   {quality_info['description']}"

            # Add recommendation for original quality
            if quality_key == "original":
                button_text += " ⭐ RECOMMENDED"

            callback_data = f"gdlq quality {quality_key}"
            buttons.data_button(button_text, callback_data)

        # Add advanced options and cancel
        buttons.data_button("⚙️ Advanced Options", "gdlq advanced")
        buttons.data_button("❌ Cancel", "gdlq cancel")

        # Build menu with 1 column for better readability
        self._main_buttons = buttons.build_menu(1)

        msg += "<b>💡 Tip:</b> Original quality is recommended for best results\n"
        msg += f"<b>⏱️ Timeout:</b> {self._timeout}s"

        # Send message
        self._reply_to = await send_message(
            self.listener.message, msg, self._main_buttons
        )

    async def _show_advanced_options(self):
        """Show advanced format options"""
        buttons = ButtonMaker()

        msg = f"<b>⚙️ Advanced Options for {self.platform.title()}</b>\n\n"

        # Format options
        format_options = {
            "best": {
                "name": "Best Available",
                "description": "Automatically select best format",
                "emoji": "⚡",
            },
            "jpg": {
                "name": "JPEG",
                "description": "JPEG format (smaller size)",
                "emoji": "📷",
            },
            "png": {
                "name": "PNG",
                "description": "PNG format (lossless)",
                "emoji": "🖼️",
            },
            "webp": {
                "name": "WebP",
                "description": "Modern format (good compression)",
                "emoji": "🌐",
            },
            "mp4": {"name": "MP4", "description": "Video format", "emoji": "🎥"},
            "gif": {"name": "GIF", "description": "Animated format", "emoji": "🎞️"},
        }

        for format_key, format_info in format_options.items():
            button_text = f"{format_info['emoji']} {format_info['name']}"
            button_text += f"\n   {format_info['description']}"

            callback_data = f"gdlq format {format_key}"
            buttons.data_button(button_text, callback_data)

        # Navigation buttons
        buttons.data_button("🔙 Back to Quality", "gdlq back_quality")
        buttons.data_button("❌ Cancel", "gdlq cancel")

        self._main_buttons = buttons.build_menu(1)

        msg += "<b>💡 Tip:</b> 'Best Available' works for most cases"

        # Edit existing message
        await edit_message(self._reply_to, msg, self._main_buttons)

    async def handle_callback(self, data: list):
        """Handle callback query"""
        try:
            if len(data) < 2:
                return

            action = data[1]

            if action == "quality":
                if len(data) >= 3:
                    from bot.helper.telegram_helper.message_utils import (
                        delete_message,
                    )

                    self.selected_quality = data[2]
                    self.selected_format = "best"  # Default format

                    # Delete the selection menu after successful selection
                    await delete_message(self._reply_to)

                    # Delete the original command
                    await delete_message(self.listener.message)

                    self.event.set()

            elif action == "format":
                if len(data) >= 3:
                    from bot.helper.telegram_helper.message_utils import (
                        delete_message,
                    )

                    self.selected_format = data[2]
                    if not self.selected_quality:
                        self.selected_quality = "original"  # Default quality

                    # Delete the selection menu after successful selection
                    await delete_message(self._reply_to)

                    # Delete the original command
                    await delete_message(self.listener.message)

                    self.event.set()

            elif action == "advanced":
                await self._show_advanced_options()

            elif action == "back_quality":
                await self._show_quality_selection()

            elif action == "cancel":
                from asyncio import create_task

                from bot.helper.telegram_helper.message_utils import (
                    auto_delete_message,
                    delete_message,
                    send_message,
                )

                # Send cancellation message
                cancel_msg = await send_message(
                    self.listener.message,
                    f"{self.listener.tag} Gallery-dl task has been cancelled!",
                )

                # Delete the selection menu
                await delete_message(self._reply_to)

                # Delete the original command
                await delete_message(self.listener.message)

                # Create background task for auto-deletion
                create_task(
                    auto_delete_message(cancel_msg, time=300),
                )  # 5 minutes auto-delete

                self.listener.is_cancelled = True
                self.event.set()

        except Exception as e:
            LOGGER.error(f"Error handling gallery-dl quality callback: {e}")


async def show_gallery_dl_quality_selector(
    listener, platform: str, content_type: str = "media", url: str = ""
) -> dict[str, Any] | None:
    """Show gallery-dl quality selection interface with automatic platform detection"""
    selector = GalleryDLQualitySelector(listener, platform, content_type, url)
    return await selector.get_quality_selection()


def get_platform_from_url(url: str) -> str:
    """Get platform name from URL for external use"""
    return GalleryDLQualitySelector.detect_platform_from_url(url)


def get_supported_platforms() -> list[str]:
    """Get list of all supported platforms"""
    return list(GalleryDLQualitySelector.PLATFORM_QUALITIES.keys())


def get_platform_qualities(platform: str) -> list[str]:
    """Get available qualities for a specific platform"""
    return GalleryDLQualitySelector.get_platform_qualities(platform)


def is_platform_supported(platform: str) -> bool:
    """Check if a platform is supported"""
    return platform.lower() in GalleryDLQualitySelector.PLATFORM_QUALITIES


def get_platform_info(platform: str) -> dict[str, Any]:
    """Get comprehensive platform information"""
    platform = platform.lower()
    qualities = GalleryDLQualitySelector.PLATFORM_QUALITIES.get(platform, {})

    return {
        "platform": platform,
        "supported": bool(qualities),
        "qualities": list(qualities.keys()),
        "quality_details": qualities,
        "requires_auth": platform
        in [
            "twitter",
            "instagram",
            "tiktok",
            "reddit",
            "tumblr",
            "facebook",
            "pixiv",
            "deviantart",
            "flickr",
            "pinterest",
            "patreon",
            "fanbox",
            "discord",
            "twitch",
            "danbooru",
            "mangadex",
            "wallhaven",
        ],
    }
