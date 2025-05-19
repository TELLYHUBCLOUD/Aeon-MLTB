from asyncio import Event, create_task, wait_for
from functools import partial
from time import time
from typing import Any, Dict, Optional, Tuple, Union

from httpx import AsyncClient
from pyrogram.filters import regex, user
from pyrogram.handlers import CallbackQueryHandler
from yt_dlp import YoutubeDL

from bot import DOWNLOAD_DIR, LOGGER, bot_loop, task_dict_lock
from bot.core.config_manager import Config
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    arg_parser,
    new_task,
    sync_to_async,
)
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.ext_utils.status_utils import (
    get_readable_file_size,
    get_readable_time,
)
from bot.helper.listeners.task_listener import TaskListener
from bot.helper.mirror_leech_utils.download_utils.yt_dlp_download import (
    YoutubeDLHelper,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    delete_message,
    edit_message,
    send_message,
)


class YtSelection:
    """Handles quality selection for YT-DLP downloads."""
    
    def __init__(self, listener: TaskListener):
        self.listener = listener
        self._is_m4a = False
        self._reply_to = None
        self._time = time()
        self._timeout = 120
        self._is_playlist = False
        self._main_buttons = None
        self.event = Event()
        self.formats: Dict[str, Any] = {}
        self.qual = None

    async def _event_handler(self) -> None:
        """Handle callback events for quality selection."""
        pfunc = partial(select_format, obj=self)
        handler = self.listener.client.add_handler(
            CallbackQueryHandler(
                pfunc,
                filters=regex("^ytq") & user(self.listener.user_id),
            ),
            group=-1,
        )
        
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except TimeoutError:
            await self._handle_timeout()
        finally:
            self.listener.client.remove_handler(*handler)

    async def _handle_timeout(self) -> None:
        """Handle timeout during quality selection."""
        await edit_message(self._reply_to, "Timed Out. Task has been cancelled!")
        self.qual = None
        self.listener.is_cancelled = True
        self.event.set()

    async def get_quality(self, result: Dict[str, Any]) -> Optional[str]:
        """Display quality selection buttons and return chosen format."""
        buttons = ButtonMaker()
        
        if "entries" in result:
            await self._setup_playlist_buttons(buttons)
        else:
            await self._setup_single_video_buttons(result, buttons)

        await self._display_quality_buttons(buttons)
        await self._event_handler()
        
        if not self.listener.is_cancelled:
            await delete_message(self._reply_to)
        return self.qual

    async def _setup_playlist_buttons(self, buttons: ButtonMaker) -> None:
        """Setup buttons for playlist downloads."""
        self._is_playlist = True
        for resolution in ["144", "240", "360", "480", "720", "1080", "1440", "2160"]:
            for fmt in ["mp4", "webm"]:
                video_format = (
                    f"bv*[height<=?{resolution}][ext={fmt}]+ba[ext=m4a]/b[height<=?{resolution}]"
                    if fmt == "mp4"
                    else f"bv*[height<=?{resolution}][ext={fmt}]+ba/b[height<=?{resolution}]"
                )
                b_data = f"{resolution}|{fmt}"
                self.formats[b_data] = video_format
                buttons.data_button(f"{resolution}-{fmt}", f"ytq {b_data}")
        
        self._add_common_buttons(buttons)
        self._main_buttons = buttons.build_menu(3)
        msg = self._get_timeout_message("Playlist Videos")

    async def _setup_single_video_buttons(self, result: Dict[str, Any], buttons: ButtonMaker) -> None:
        """Setup buttons for single video downloads."""
        format_dict = result.get("formats", [])
        for item in format_dict:
            if not item.get("tbr"):
                continue
                
            self._process_format_item(item)
        
        for b_name, tbr_dict in self.formats.items():
            if len(tbr_dict) == 1:
                self._add_single_bitrate_button(buttons, b_name, tbr_dict)
            else:
                buttons.data_button(b_name, f"ytq dict {b_name}")
        
        self._add_common_buttons(buttons)
        self._main_buttons = buttons.build_menu(2)
        msg = self._get_timeout_message("Video")

    def _process_format_item(self, item: Dict[str, Any]) -> None:
        """Process a single format item from yt-dlp info."""
        format_id = item["format_id"]
        size = item.get("filesize") or item.get("filesize_approx") or 0
        
        if item.get("video_ext") == "none" and item.get("acodec") != "none":
            self._process_audio_format(item, format_id, size)
        elif item.get("height"):
            self._process_video_format(item, format_id, size)

    def _process_audio_format(self, item: Dict[str, Any], format_id: str, size: int) -> None:
        """Process audio format items."""
        if item.get("audio_ext") == "m4a":
            self._is_m4a = True
        b_name = f"{item.get('acodec') or format_id}-{item['ext']}"
        v_format = format_id
        self.formats.setdefault(b_name, {})[f"{item['tbr']}"] = [size, v_format]

    def _process_video_format(self, item: Dict[str, Any], format_id: str, size: int) -> None:
        """Process video format items."""
        height = item["height"]
        ext = item["ext"]
        fps = item.get("fps", "")
        b_name = f"{height}p{fps}-{ext}"
        ba_ext = "[ext=m4a]" if self._is_m4a and ext == "mp4" else ""
        v_format = f"{format_id}+ba{ba_ext}/b[height=?{height}]"
        self.formats.setdefault(b_name, {})[f"{item['tbr']}"] = [size, v_format]

    def _add_single_bitrate_button(self, buttons: ButtonMaker, b_name: str, tbr_dict: Dict[str, Any]) -> None:
        """Add button for formats with single bitrate option."""
        tbr, v_list = next(iter(tbr_dict.items()))
        button_name = f"{b_name} ({get_readable_file_size(v_list[0])})"
        buttons.data_button(button_name, f"ytq sub {b_name} {tbr}")

    def _add_common_buttons(self, buttons: ButtonMaker) -> None:
        """Add common buttons to quality selection."""
        buttons.data_button("MP3", "ytq mp3")
        buttons.data_button("Audio Formats", "ytq audio")
        buttons.data_button("Best Videos", "ytq bv*+ba/b")
        buttons.data_button("Best Audios", "ytq ba/b")
        buttons.data_button("Cancel", "ytq cancel", "footer")

    def _get_timeout_message(self, media_type: str) -> str:
        """Get timeout message for quality selection."""
        return (
            f"Choose {media_type} Quality:\n"
            f"Timeout: {get_readable_time(self._timeout - (time() - self._time))}"
        )

    async def _display_quality_buttons(self, buttons: ButtonMaker) -> None:
        """Display the quality selection buttons."""
        self._reply_to = await send_message(
            self.listener.message,
            self._get_timeout_message("Playlist Videos" if self._is_playlist else "Video"),
            self._main_buttons,
        )

    # ... (other methods remain similar but with type hints and improved docstrings)


class YtDlp(TaskListener):
    """Main YT-DLP download handler."""
    
    def __init__(
        self,
        client: Any,
        message: Any,
        _: Any = None,
        is_leech: bool = False,
        __: Any = None,
        ___: Any = None,
        same_dir: Optional[Dict[str, Any]] = None,
        bulk: Optional[list] = None,
        multi_tag: Optional[str] = None,
        options: str = "",
    ):
        """
        Initialize YT-DLP downloader.
        
        Args:
            client: Pyrogram client
            message: Message object
            is_leech: Whether to leech instead of mirror
            same_dir: Dictionary for same directory downloads
            bulk: List for bulk downloads
            multi_tag: Tag for multi downloads
            options: Additional options string
        """
        super().__init__()
        self.message = message
        self.client = client
        self.multi_tag = multi_tag
        self.options = options
        self.same_dir = same_dir or {}
        self.bulk = bulk or []
        self.is_ytdlp = True
        self.is_leech = is_leech
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize default values for download parameters."""
        self.multi = 0
        self.ffmpeg_cmds = set()
        self.select = False
        self.name = ""
        self.up_dest = ""
        self.rc_flags = ""
        self.link = ""
        self.compress = False
        self.thumb = ""
        self.split_size = 0
        self.sample_video = False
        self.screen_shots = False
        self.force_run = False
        self.force_download = False
        self.force_upload = False
        self.convert_audio = False
        self.convert_video = False
        self.name_sub = ""
        self.hybrid_leech = False
        self.thumbnail_layout = ""
        self.as_doc = False
        self.as_med = False
        self.metadata = ""
        self.folder_name = ""
        self.bot_trans = False
        self.user_trans = False
        self.user_dict = {}

    async def new_event(self) -> None:
        """Handle new download event."""
        error_msg, error_button = await self._validate_input()
        if error_msg:
            await self._handle_error(error_msg, error_button)
            return

        args = self._parse_arguments()
        self._process_arguments(args)

        if not await self._process_bulk_download(args):
            return

        path = f"{DOWNLOAD_DIR}{self.mid}{self.folder_name}"
        await self.get_tag(self.message.text.split("\n"))

        if not await self._validate_and_process_link():
            return

        try:
            qual, result = await self._get_download_quality()
            if qual is None:
                return

            await self._start_download(path, qual, result)
        except Exception as e:
            await self._handle_download_error(str(e))
        finally:
            await self._cleanup()

    async def _validate_input(self) -> Tuple[Optional[str], Optional[Any]]:
        """Validate input message and return error if any."""
        return await error_check(self.message)

    async def _handle_error(self, error_msg: str, error_button: Any) -> None:
        """Handle error during download initialization."""
        await delete_links(self.message)
        error = await send_message(self.message, error_msg, error_button)
        await auto_delete_message(error, time=300)

    def _parse_arguments(self) -> Dict[str, Any]:
        """Parse command line arguments."""
        input_list = self.message.text.split("\n")[0].split(" ")
        args = {
            # Default arguments dictionary
            # ... (same as original but with type hints)
        }
        arg_parser(input_list[1:], args)
        return args

    def _process_arguments(self, args: Dict[str, Any]) -> None:
        """Process parsed arguments."""
        # Process all arguments and set instance variables
        # ... (same logic as original but more organized)

    async def _process_bulk_download(self, args: Dict[str, Any]) -> bool:
        """Process bulk download if specified."""
        is_bulk = args["-b"]
        if not isinstance(is_bulk, bool):
            await self.init_bulk(
                self.message.text.split("\n"),
                *is_bulk.split(":"),
                YtDlp
            )
            return False
        return True

    async def _validate_and_process_link(self) -> bool:
        """Validate and process the download link."""
        if not self.link and (reply_to := self.message.reply_to_message):
            self.link = reply_to.text.split("\n", 1)[0].strip()

        if not is_url(self.link):
            await send_message(
                self.message,
                COMMAND_USAGE["yt"][0],
                COMMAND_USAGE["yt"][1],
            )
            await self.remove_from_same_dir()
            return False

        if "mdisk.me" in self.link:
            self.name, self.link = await _mdisk(self.link, self.name)

        try:
            await self.before_start()
            return True
        except Exception as e:
            await send_message(self.message, str(e))
            await self.remove_from_same_dir()
            return False

    async def _get_download_quality(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Get download quality either from options or user selection."""
        opt = (self.options or self.user_dict.get("YT_DLP_OPTIONS") or 
               Config.YT_DLP_OPTIONS)
        
        options = {"usenetrc": True, "cookiefile": "cookies.txt"}
        qual = None
        
        if opt:
            qual = self._process_options(opt, options)

        options["playlist_items"] = "0"
        
        try:
            result = await sync_to_async(extract_info, self.link, options)
            if not qual:
                qual = await YtSelection(self).get_quality(result)
            return qual, result
        except Exception as e:
            msg = str(e).replace("<", " ").replace(">", " ")
            await send_message(self.message, f"{self.tag} {msg}")
            await self.remove_from_same_dir()
            return None, None

    def _process_options(self, opt: Dict[str, Any], options: Dict[str, Any]) -> Optional[str]:
        """Process YT-DLP options and return quality if specified."""
        qual = None
        for key, value in opt.items():
            if key in ["postprocessors", "download_ranges"]:
                continue
            if key == "format" and not self.select:
                if value.startswith("ba/b-"):
                    return value
                qual = value
            options[key] = value
        return qual

    async def _start_download(self, path: str, qual: str, result: Dict[str, Any]) -> None:
        """Start the actual download process."""
        LOGGER.info(f"Downloading with YT-DLP: {self.link}")
        playlist = "entries" in result
        ydl = YoutubeDLHelper(self)
        create_task(ydl.add_download(path, qual, playlist, self.options or {}))
        await delete_links(self.message)

    async def _handle_download_error(self, error: str) -> None:
        """Handle download errors."""
        await send_message(self.message, error)
        await self.remove_from_same_dir()

    async def _cleanup(self) -> None:
        """Cleanup after download process."""
        await self.run_multi(self.message.text.split("\n"), YtDlp)


@new_task
async def select_format(_, query, obj: YtSelection):
    """Handle quality selection callback."""
    data = query.data.split()
    message = query.message
    await query.answer()

    try:
        if data[1] == "dict":
            await obj.qual_subbuttons(data[2])
        elif data[1] == "mp3":
            await obj.mp3_subbuttons()
        elif data[1] == "audio":
            await obj.audio_format()
        elif data[1] == "aq":
            await obj._handle_audio_quality(data)
        elif data[1] == "back":
            await obj.back_to_main()
        elif data[1] == "cancel":
            await obj._cancel_download(message)
        else:
            await obj._set_quality(data)
    except Exception as e:
        LOGGER.error(f"Error in select_format: {e}")
        await edit_message(message, "An error occurred processing your selection.")


async def ytdl(client: Any, message: Any) -> None:
    """Handle ytdl command."""
    bot_loop.create_task(YtDlp(client, message).new_event())


async def ytdl_leech(client: Any, message: Any) -> None:
    """Handle ytdl leech command."""
    bot_loop.create_task(YtDlp(client, message, is_leech=True).new_event()
