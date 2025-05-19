# ruff: noqa: ARG005, B023
import contextlib
from logging import getLogger
from os import listdir
from os import path as ospath
from re import search as re_search
from secrets import token_hex
from typing import Any

from yt_dlp import DownloadError, YoutubeDL

from bot import task_dict, task_dict_lock
from bot.helper.ext_utils.bot_utils import async_to_sync, sync_to_async
from bot.helper.ext_utils.task_manager import (
    check_running_tasks,
    stop_duplicate_check,
)
from bot.helper.mirror_leech_utils.status_utils.queue_status import QueueStatus
from bot.helper.mirror_leech_utils.status_utils.yt_dlp_status import YtDlpStatus
from bot.helper.telegram_helper.message_utils import send_status_message

LOGGER = getLogger(__name__)


class MyLogger:
    def __init__(self, obj: "YoutubeDLHelper", listener: Any) -> None:
        self._obj = obj
        self._listener = listener

    def debug(self, msg: str) -> None:
        # Hack to fix changing extension
        if not self._obj.is_playlist and (
            match := re_search(
                r".Merger..Merging formats into..(.*?).$",
                msg,
            )
            or re_search(r".ExtractAudio..Destination..(.*?)$", msg)
        ):
            LOGGER.info(msg)
            newname = match.group(1)
            newname = newname.rsplit("/", 1)[-1]
            self._listener.name = newname

    @staticmethod
    def warning(msg: str) -> None:
        LOGGER.warning(msg)

    @staticmethod
    def error(msg: str) -> None:
        if msg != "ERROR: Cancelling...":
            LOGGER.error(msg)


class YoutubeDLHelper:
    def __init__(self, listener: Any) -> None:
        self._last_downloaded = 0
        self._progress = 0
        self._downloaded_bytes = 0
        self._download_speed = 0
        self._eta = "-"
        self._listener = listener
        self._gid = ""
        self._ext = ""
        self.is_playlist = False

        self._initialize_default_options()

    def _initialize_default_options(self) -> None:
        """Initialize default yt-dlp options"""
        self.opts: dict[str, Any] = {
            "progress_hooks": [self._on_download_progress],
            "logger": MyLogger(self, self._listener),
            "usenetrc": True,
            "cookiefile": "cookies.txt",
            "allow_multiple_video_streams": True,
            "allow_multiple_audio_streams": True,
            "noprogress": True,
            "allow_playlist_files": True,
            "overwrites": True,
            "writethumbnail": True,
            "trim_file_name": 220,
            "ffmpeg_location": "/bin/xtra",
            "fragment_retries": 10,
            "retries": 10,
            "retry_sleep_functions": {
                "http": lambda n: 3,
                "fragment": lambda n: 3,
                "file_access": lambda n: 3,
                "extractor": lambda n: 3,
            },
        }

    @property
    def download_speed(self) -> float:
        return self._download_speed

    @property
    def downloaded_bytes(self) -> int:
        return self._downloaded_bytes

    @property
    def size(self) -> int:
        return self._listener.size

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def eta(self) -> str:
        return self._eta

    def _on_download_progress(self, d: dict[str, Any]) -> None:
        """Callback for download progress updates"""
        if self._listener.is_cancelled:
            raise ValueError("Cancelling...")

        if d["status"] == "finished":
            if self.is_playlist:
                self._last_downloaded = 0
        elif d["status"] == "downloading":
            self._update_download_stats(d)

    def _update_download_stats(self, d: dict[str, Any]) -> None:
        """Update download statistics from progress data"""
        self._download_speed = d["speed"] or 0

        if self.is_playlist:
            self._update_playlist_stats(d)
        else:
            self._update_single_file_stats(d)

        self._calculate_progress()

    def _update_playlist_stats(self, d: dict[str, Any]) -> None:
        """Update stats for playlist downloads"""
        downloaded_bytes = d["downloaded_bytes"] or 0
        chunk_size = downloaded_bytes - self._last_downloaded
        self._last_downloaded = downloaded_bytes
        self._downloaded_bytes += chunk_size

    def _update_single_file_stats(self, d: dict[str, Any]) -> None:
        """Update stats for single file downloads"""
        if d.get("total_bytes"):
            self._listener.size = d["total_bytes"] or 0
        elif d.get("total_bytes_estimate"):
            self._listener.size = d["total_bytes_estimate"] or 0

        self._downloaded_bytes = d["downloaded_bytes"] or 0
        self._eta = d.get("eta", "-") or "-"

    def _calculate_progress(self) -> None:
        """Calculate download progress percentage"""
        with contextlib.suppress(Exception):
            if self._listener.size > 0:
                self._progress = (self._downloaded_bytes / self._listener.size) * 100

    async def _on_download_start(self, from_queue: bool = False) -> None:
        """Handle actions when download starts"""
        async with task_dict_lock:
            task_dict[self._listener.mid] = YtDlpStatus(
                self._listener,
                self,
                self._gid,
            )

        if not from_queue:
            await self._listener.on_download_start()
            if self._listener.multi <= 1:
                await send_status_message(self._listener.message)

    def _on_download_error(self, error: str) -> None:
        """Handle download errors"""
        self._listener.is_cancelled = True
        async_to_sync(self._listener.on_download_error, error)

    def _extract_meta_data(self) -> None:
        """Extract metadata from the video/playlist"""
        if self._listener.link.startswith(("rtmp", "mms", "rstp", "rtmps")):
            self.opts["external_downloader"] = "xtra"

        with YoutubeDL(self.opts) as ydl:
            try:
                result = ydl.extract_info(self._listener.link, download=False)
                if result is None:
                    raise ValueError("Info result is None")

                self._process_metadata_result(ydl, result)
            except Exception as e:
                self._on_download_error(str(e))

    def _process_metadata_result(
        self, ydl: YoutubeDL, result: dict[str, Any]
    ) -> None:
        """Process the metadata extraction result"""
        if "entries" in result:
            self._process_playlist_metadata(ydl, result)
        else:
            self._process_single_video_metadata(ydl, result)

    def _process_playlist_metadata(
        self, ydl: YoutubeDL, result: dict[str, Any]
    ) -> None:
        """Process metadata for playlists"""
        for entry in result["entries"]:
            if not entry:
                continue

            self._listener.size += (
                entry.get("filesize_approx", 0) or entry.get("filesize", 0) or 0
            )

            if not self._listener.name:
                outtmpl_ = "%(series,playlist_title,channel)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d.%(ext)s"
                self._listener.name, ext = ospath.splitext(
                    ydl.prepare_filename(entry, outtmpl=outtmpl_),
                )
                if not self._ext:
                    self._ext = ext

    def _process_single_video_metadata(
        self, ydl: YoutubeDL, result: dict[str, Any]
    ) -> None:
        """Process metadata for single videos"""
        outtmpl_ = "%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s"
        realName = ydl.prepare_filename(result, outtmpl=outtmpl_)
        ext = ospath.splitext(realName)[-1]

        self._listener.name = (
            f"{self._listener.name}{ext}" if self._listener.name else realName
        )

        if not self._ext:
            self._ext = ext

    def _download(self, path: str) -> None:
        """Perform the actual download"""
        try:
            with YoutubeDL(self.opts) as ydl:
                try:
                    ydl.download([self._listener.link])
                except DownloadError as e:
                    if not self._listener.is_cancelled:
                        self._on_download_error(str(e))
                    return

            self._verify_download_completion(path)
        except Exception as e:
            LOGGER.error(f"Error during download: {e}")
            self._on_download_error(str(e))

    def _verify_download_completion(self, path: str) -> None:
        """Verify that download completed successfully"""
        if self.is_playlist and (not ospath.exists(path) or len(listdir(path)) == 0):
            self._on_download_error(
                "No video available to download from this playlist. Check logs for more details",
            )
            return

        if self._listener.is_cancelled:
            return

        async_to_sync(self._listener.on_download_complete)

    async def add_download(
        self, path: str, qual: str, playlist: bool, options: dict[str, Any]
    ) -> None:
        """Add a new download task"""
        self._prepare_download_options(qual, playlist, options)
        self._gid = token_hex(4)

        await self._on_download_start()
        await sync_to_async(self._extract_meta_data)

        if self._listener.is_cancelled:
            return

        self._prepare_output_templates(path, options)
        self._handle_audio_format(qual)
        self._handle_thumbnail_options()

        if not await self._check_for_duplicates():
            return

        await self._process_download_queue(path)

    def _prepare_download_options(
        self, qual: str, playlist: bool, options: dict[str, Any]
    ) -> None:
        """Prepare download options based on parameters"""
        if playlist:
            self.opts["ignoreerrors"] = True
            self.is_playlist = True

        self._setup_post_processors()

        if options:
            self._set_options(options)

        self.opts["format"] = qual

    def _setup_post_processors(self) -> None:
        """Setup default post processors"""
        self.opts["postprocessors"] = [
            {
                "add_chapters": True,
                "add_infojson": "if_exists",
                "add_metadata": True,
                "key": "FFmpegMetadata",
            },
        ]

    def _handle_audio_format(self, qual: str) -> None:
        """Handle audio format options"""
        if qual.startswith("ba/b-"):
            audio_info = qual.split("-")
            audio_format = audio_info[1]
            rate = audio_info[2]

            self.opts["postprocessors"].append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": rate,
                },
            )

            self._ext = self._get_audio_extension(audio_format)

    def _get_audio_extension(self, audio_format: str) -> str:
        """Get the appropriate extension for audio format"""
        if audio_format == "vorbis":
            return ".ogg"
        if audio_format == "alac":
            return ".m4a"
        return f".{audio_format}"

    def _prepare_output_templates(self, path: str, options: dict[str, Any]) -> None:
        """Prepare output filename templates"""
        base_name, ext = ospath.splitext(self._listener.name)
        self._trim_filename_if_needed(base_name, ext)

        if self.is_playlist:
            self._setup_playlist_output(path)
        elif "download_ranges" in options:
            self._setup_ranged_output(path, base_name)
        elif self._has_metadata_options(options):
            self._setup_metadata_output(path, base_name)
        else:
            self._setup_default_output(path, base_name)

    def _trim_filename_if_needed(self, base_name: str, ext: str) -> None:
        """Trim filename if it's too long"""
        trim_name = self._listener.name if self.is_playlist else base_name
        if len(trim_name.encode()) > 200:
            self._listener.name = (
                self._listener.name[:200]
                if self.is_playlist
                else f"{base_name[:200]}{ext}"
            )

    def _setup_playlist_output(self, path: str) -> None:
        """Setup output template for playlists"""
        self.opts["outtmpl"] = {
            "default": f"{path}/{self._listener.name}/%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s",
            "thumbnail": f"{path}/yt-dlp-thumb/%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s",
        }

    def _setup_ranged_output(self, path: str, base_name: str) -> None:
        """Setup output template for ranged downloads"""
        self.opts["outtmpl"] = {
            "default": f"{path}/{base_name}/%(section_number|)s%(section_number&.|)s%(section_title|)s%(section_title&-|)s%(title,fulltitle,alt_title)s %(section_start)s to %(section_end)s.%(ext)s",
            "thumbnail": f"{path}/yt-dlp-thumb/%(section_number|)s%(section_number&.|)s%(section_title|)s%(section_title&-|)s%(title,fulltitle,alt_title)s %(section_start)s to %(section_end)s.%(ext)s",
        }

    def _has_metadata_options(self, options: dict[str, Any]) -> bool:
        """Check if metadata options are present"""
        return any(
            key in options
            for key in [
                "writedescription",
                "writeinfojson",
                "writeannotations",
                "writedesktoplink",
                "writewebloclink",
                "writeurllink",
                "writesubtitles",
                "writeautomaticsub",
            ]
        )

    def _setup_metadata_output(self, path: str, base_name: str) -> None:
        """Setup output template for metadata downloads"""
        self.opts["outtmpl"] = {
            "default": f"{path}/{base_name}/{self._listener.name}",
            "thumbnail": f"{path}/yt-dlp-thumb/{base_name}.%(ext)s",
        }

    def _setup_default_output(self, path: str, base_name: str) -> None:
        """Setup default output template"""
        self.opts["outtmpl"] = {
            "default": f"{path}/{self._listener.name}",
            "thumbnail": f"{path}/yt-dlp-thumb/{base_name}.%(ext)s",
        }

    def _handle_thumbnail_options(self) -> None:
        """Handle thumbnail embedding options"""
        if self._listener.is_leech and not self._listener.thumbnail_layout:
            self.opts["postprocessors"].append(
                {
                    "format": "jpg",
                    "key": "FFmpegThumbnailsConvertor",
                    "when": "before_dl",
                },
            )

        if self._ext in [
            ".mp3",
            ".mkv",
            ".mka",
            ".ogg",
            ".opus",
            ".flac",
            ".m4a",
            ".mp4",
            ".mov",
            ".m4v",
        ]:
            self._add_thumbnail_embedding()
        elif not self._listener.is_leech:
            self.opts["writethumbnail"] = False

    def _add_thumbnail_embedding(self) -> None:
        """Add thumbnail embedding postprocessor"""
        self.opts["postprocessors"].append(
            {
                "already_have_thumbnail": bool(
                    self._listener.is_leech and not self._listener.thumbnail_layout,
                ),
                "key": "EmbedThumbnail",
            },
        )

    async def _check_for_duplicates(self) -> bool:
        """Check for duplicate downloads"""
        msg, button = await stop_duplicate_check(self._listener)
        if msg:
            await self._listener.on_download_error(msg, button)
            return False
        return True

    async def _process_download_queue(self, path: str) -> None:
        """Process the download queue"""
        add_to_queue, event = await check_running_tasks(self._listener)

        if add_to_queue:
            await self._handle_queued_download(event)
        else:
            LOGGER.info(f"Download with YT_DLP: {self._listener.name}")

        await sync_to_async(self._download, path)

    async def _handle_queued_download(self, event: Any) -> None:
        """Handle queued downloads"""
        LOGGER.info(f"Added to Queue/Download: {self._listener.name}")
        async with task_dict_lock:
            task_dict[self._listener.mid] = QueueStatus(
                self._listener,
                self._gid,
                "dl",
            )

        await event.wait()

        if self._listener.is_cancelled:
            return

        LOGGER.info(f"Start Queued Download from YT_DLP: {self._listener.name}")
        await self._on_download_start(True)

    async def cancel_task(self) -> None:
        """Cancel the current download task"""
        self._listener.is_cancelled = True
        LOGGER.info(f"Cancelling Download: {self._listener.name}")
        await self._listener.on_download_error("Stopped by User!")

    def _set_options(self, options: dict[str, Any]) -> None:
        """Set additional options from dictionary"""
        for key, value in options.items():
            if key == "postprocessors":
                self._handle_postprocessors(value)
            elif key == "download_ranges":
                self._handle_download_ranges(value)
            else:
                self.opts[key] = value

    def _handle_postprocessors(self, value: Any) -> None:
        """Handle postprocessors option"""
        if isinstance(value, list):
            self.opts["postprocessors"].extend(tuple(value))
        elif isinstance(value, dict):
            self.opts["postprocessors"].append(value)

    def _handle_download_ranges(self, value: Any) -> None:
        """Handle download_ranges option"""
        if isinstance(value, list):
            self.opts["download_ranges"] = lambda info, ytdl: value
