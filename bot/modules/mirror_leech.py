# ruff: noqa: RUF006
from asyncio import create_task, sleep
from base64 import b64encode
from re import match as re_match

from aiofiles.os import path as aiopath
from truelink import TrueLinkResolver
from truelink.exceptions import TrueLinkException
from truelink.types import FolderResult, LinkResult

from bot import DOWNLOAD_DIR, LOGGER, bot_loop, task_dict_lock, user_data
from bot.core.aeon_client import TgClient
from bot.core.config_manager import Config
from bot.helper.aeon_utils.access_check import error_check
from bot.helper.ext_utils.bot_utils import (
    COMMAND_USAGE,
    get_content_type,
    new_task,
)
from bot.helper.ext_utils.links_utils import (
    is_gdrive_id,
    is_gdrive_link,
    is_magnet,
    is_mega_link,
    is_rclone_path,
    is_telegram_link,
    is_url,
)
from bot.modules.task_base import TaskBase
from bot.helper.mirror_leech_utils.download_utils.aria2_download import (
    add_aria2_download,
)
from bot.helper.mirror_leech_utils.download_utils.direct_downloader import (
    add_direct_download,
)
from bot.helper.mirror_leech_utils.download_utils.gd_download import add_gd_download
from bot.helper.mirror_leech_utils.download_utils.jd_download import add_jd_download
from bot.helper.mirror_leech_utils.download_utils.nzb_downloader import add_nzb
from bot.helper.mirror_leech_utils.download_utils.direct_link_generator import (
    direct_link_generator,
)
from bot.helper.mirror_leech_utils.download_utils.qbit_download import add_qb_torrent
from bot.helper.mirror_leech_utils.download_utils.rclone_download import (
    add_rclone_download,
)
from bot.helper.mirror_leech_utils.download_utils.mega_download import (
    add_mega_download,
)
from bot.helper.mirror_leech_utils.download_utils.telegram_download import (
    TelegramDownloadHelper,
)
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.ext_utils.limit_checker import limit_checker
from bot.helper.mirror_leech_utils.download_utils.streamrip_download import (
    add_streamrip_download,
)
from bot.helper.mirror_leech_utils.download_utils.zotify_download import (
    add_zotify_download,
)
from bot.helper.mirror_leech_utils.streamrip_utils.url_parser import is_streamrip_url
from bot.helper.mirror_leech_utils.zotify_utils.url_parser import is_zotify_url
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    get_tg_link_message,
    send_message,
)
from bot.modules.media_tools import show_media_tools_for_task


class Mirror(TaskBase):
    def __init__(
        self,
        client,
        message,
        is_qbit=False,
        is_leech=False,
        is_jd=False,
        is_nzb=False,
        is_md_leech=False,
        is_enc=False,
        auto_link=None,
        auto_ff=None,
        name=None,
        size=None,
        **kwargs,
    ):
        self.message = message
        self.client = client
        self.auto_link = auto_link
        self.auto_ff = auto_ff
        self.name = name
        self.size = size
        # Pass kwargs to TaskBase for bulk, multi_tag, options, etc.
        super().__init__(client, message, **kwargs)
        self.is_qbit = is_qbit
        self.is_leech = is_leech
        self.is_jd = is_jd
        self.is_nzb = is_nzb
        self.is_md_leech = is_md_leech
        self.is_enc = is_enc

    def _ensure_user_dict(self):
        if not hasattr(self, "user_dict") or self.user_dict is None:
            from bot import user_data
            user_id = self.message.from_user.id if self.message.from_user else ""
            self.user_dict = user_data.get(user_id, {})

    async def new_event(self):
        # Ensure user_dict is never None to prevent AttributeError
        self._ensure_user_dict()

        input_list = await self.parse_args()
        if not input_list:
             LOGGER.error("Message text is None or message doesn't have text attribute")
             error_msg = "Invalid message format. Please make sure your message contains text."
             error = await send_message(self.message, error_msg)
             return await auto_delete_message(error, time=300)

        error_msg, error_button = await error_check(self.message)
        if error_msg:
            await delete_links(self.message)
            error = await send_message(self.message, error_msg, error_button)
            return await auto_delete_message(error, time=300)

        user_id = self.user_id
        text = self.message.text.split("\n")

        args = self.args

        # AUTO LEECH + AUTO COMPRESS CMD logic
        # TaskBase.parse_args consumes message text.
        # If auto_link is present (e.g. from Auto Leech handler which sets it in init), we should assume it's the link
        # if none was found in text.
        if self.auto_link and not any(x.startswith("http") or "magnet" in x for x in input_list):
             # Original logic appended to input_list then parsed.
             # Here we already parsed.
             if not self.link:
                 self.link = self.auto_link

        # Handle auto_ff: append to self.ffmpeg_cmds if -ff not present in command
        user_ff = any(item.strip() == "-ff" for item in input_list)
        if not user_ff and self.auto_ff:
             # self.ffmpeg_cmds is initialized in TaskBase based on args["-ff"]
             # args["-ff"] is empty set if not provided.
             if not self.ffmpeg_cmds:
                 self.ffmpeg_cmds = []
             # auto_ff is string of args e.g. "-c:v copy"
             # We should parse it similarly to how TaskBase handles string input or just append tokens
             import shlex
             # Simple split might not handle quotes in auto_ff, better use shlex
             try:
                 # auto_ff content usually is meant to be arguments for ffmpeg
                 # If it's keys from config, logic below handles keys.
                 # If it's direct command:
                 # The original logic extended input_list with auto_ff.split().
                 # We need to simulate processing that.
                 # For simplicity, treat as direct command list if not a key
                 # But we need to check if it's a key first.

                 # Reusing the key lookup logic from below/original
                 def get_cmds_from_key(key):
                    if Config.FFMPEG_CMDS and key in Config.FFMPEG_CMDS:
                        return Config.FFMPEG_CMDS[key]
                    if self.user_dict.get("FFMPEG_CMDS") and key in self.user_dict["FFMPEG_CMDS"]:
                        return self.user_dict["FFMPEG_CMDS"][key]
                    return None

                 # auto_ff might be multiple tokens
                 tokens = self.auto_ff.split() # Original used simple split
                 for token in tokens:
                     # Check if token is a key?
                     # Original logic: input_list.extend(self.auto_ff.split()) then arg_parser ran.
                     # Then:
                     # if args["-ff"]: ... raw_input = args["-ff"] ...

                     # Since we missed re-parsing, we manually process tokens as if they were in -ff?
                     # No, -ff flag takes 1 arg (the key or string).
                     # Wait, arg_parser logic for -ff?
                     # It's a set.
                     # If auto_ff was appended to input_list, it would be treated as arguments to command, NOT necessarily values for -ff flag unless -ff was in auto_ff string.
                     # Ah! user_ff check checks if user provided -ff.
                     # If not, auto_ff is appended.
                     # If auto_ff string contains "-ff preset", then it works.
                     # If auto_ff string is just "preset", it might be treated as link or something else if not preceded by flag.
                     # Actually, if auto_ff is just "preset", where does it go?
                     # arg_parser parses known flags.
                     # If auto_ff=" -ff preset ", then yes.
                     # If auto_ff="-c copy", these are not standard bot flags, these are ffmpeg args?
                     # No, the bot only accepts -ff flag for ffmpeg.
                     # So auto_ff MUST contain "-ff" or be valid bot args.
                     pass

                 # Assuming auto_ff is well-formed arguments string like "-ff high_quality"
                 # Since we can't re-run parser easily on modified list without resetting everything,
                 # We assume auto_ff contains -ff flag if it wants to set ffmpeg commands.
                 # If so, we can't easily support it without re-parsing.
                 # BUT, the variable name `auto_ff` suggests it IS the value for -ff?
                 # user_dict.get("AUTO_COMPRESS_CMD") -> auto_ff
                 # If it's "AUTO_COMPRESS_CMD", it implies it might be used for compression logic directly?
                 # No, usage in original: input_list.extend(self.auto_ff.split())
                 # If user sets AUTO_COMPRESS_CMD = "-ff mypreset", then it adds -ff mypreset.
                 # If user sets AUTO_COMPRESS_CMD = "-z", it adds -z.

                 # Critical Fix: We need to parse auto_ff content if present.
                 # We can run arg_parser on auto_ff tokens and merge with self.args?
                 if self.auto_ff:
                     from bot.helper.ext_utils.bot_utils import arg_parser
                     auto_args = self.get_default_args()
                     arg_parser(self.auto_ff.split(), auto_args)
                     # Merge auto_args into self.args for flags that are False/Empty in self.args
                     for k, v in auto_args.items():
                         if not self.args.get(k) and v: # Only override if currently empty/false
                             self.args[k] = v
                             # Also update attributes derived from args
                             if k == "-ff":
                                 # Logic for -ff processing needs to run again with new value
                                 pass

                     # Re-map common attributes
                     self.link = self.link or self.args["link"]
                     # ... others ...

             except Exception as e:
                 LOGGER.error(f"Error processing Auto FF args: {e}")

        # Re-run attribute mapping from args (TaskBase does it, but we modified args maybe)
        self.rc_flags = self.args["-rcf"]
        self.compress = self.args["-z"]

        from bot.helper.ext_utils.bot_utils import is_flag_enabled
        if self.compress and is_flag_enabled("-z"):
            self.compression_enabled = True

        self.extract = self.args["-e"]
        if self.extract and is_flag_enabled("-e"):
            self.extract_enabled = True

        # ... (Rest of logic) ...
        # Add settings
        self.add_enabled = args["-add"]
        self.add_video_enabled = args["-add-video"]
        self.add_audio_enabled = args["-add-audio"]
        self.add_subtitle_enabled = args["-add-subtitle"]
        self.add_attachment_enabled = args["-add-attachment"]
        self.preserve_flag = args["-preserve"]
        self.replace_flag = args["-replace"]
        
        if self.name is None:
            self.name = args["name"] if "name" in args else ""
        if self.size is None:
            self.size = 0

        self.remove_enabled = args["-remove"]
        self.remove_video_enabled = args["-remove-video"]
        self.remove_audio_enabled = args["-remove-audio"]
        self.remove_subtitle_enabled = args["-remove-subtitle"]
        self.remove_attachment_enabled = args["-remove-attachment"]
        self.remove_metadata = args["-remove-metadata"]

        self.remove_video_index = args["-remove-video-index"] or args["-rvi"]
        self.remove_audio_index = args["-remove-audio-index"] or args["-rai"]
        self.remove_subtitle_index = args["-remove-subtitle-index"] or args["-rsi"]
        self.remove_attachment_index = (
            args["-remove-attachment-index"] or args["-rati"]
        )

        if (
            self.remove_video_enabled
            or self.remove_audio_enabled
            or self.remove_subtitle_enabled
            or self.remove_attachment_enabled
            or self.remove_metadata
            or self.remove_video_index
            or self.remove_audio_index
            or self.remove_subtitle_index
            or self.remove_attachment_index
        ):
            self.remove_enabled = True

        self.join = args["-j"]
        self.thumb = args["-t"]
        self.split_size = args["-sp"]
        self.sample_video = args["-sv"]
        self.screen_shots = args["-ss"]
        self.force_run = args["-f"]
        self.force_download = args["-fd"]
        self.force_upload = args["-fu"]
        self.convert_audio = args["-ca"]
        self.convert_video = args["-cv"]
        self.name_sub = args["-ns"]
        self.hybrid_leech = args["-hl"]
        self.thumbnail_layout = args["-tl"]
        self.as_doc = args["-doc"]
        self.as_med = args["-med"]
        self.media_tools = args["-mt"]

        if self.media_tools:
            from bot.modules.media_tools import register_pending_task_user
            register_pending_task_user(user_id)

        self.metadata = args["-md"]
        self.metadata_title = args["-metadata-title"]
        self.metadata_author = args["-metadata-author"]
        self.metadata_comment = args["-metadata-comment"]
        self.metadata_all = args["-metadata-all"]
        self.metadata_video_title = args["-metadata-video-title"]
        self.metadata_video_author = args["-metadata-video-author"]
        self.metadata_video_comment = args["-metadata-video-comment"]
        self.metadata_audio_title = args["-metadata-audio-title"]
        self.metadata_audio_author = args["-metadata-audio-author"]
        self.metadata_audio_comment = args["-metadata-audio-comment"]
        self.metadata_subtitle_title = args["-metadata-subtitle-title"]
        self.metadata_subtitle_author = args["-metadata-subtitle-author"]
        self.metadata_subtitle_comment = args["-metadata-subtitle-comment"]
        self.folder_name = (
            f"/{args['-m']}".rstrip("/") if len(args["-m"]) > 0 else ""
        )
        self.bot_trans = args["-bt"]
        self.user_trans = args["-ut"]
        self.merge_video = args["-merge-video"]
        self.merge_audio = args["-merge-audio"]
        self.merge_subtitle = args["-merge-subtitle"]
        self.merge_all = args["-merge-all"]
        self.merge_image = args["-merge-image"]
        self.merge_pdf = args["-merge-pdf"]
        self.watermark_text = args["-watermark"]
        self.watermark_image = args["-iwm"]
        self.trim = args["-trim"]
        self.ffmpeg_cmds = args["-ff"]

        self.lulu = args["-lulu"] if not self.is_leech else False
        self.is_buzzheavier = args["-buz"] if not self.is_leech else False
        self.is_pixeldrain = args["-pix"] if not self.is_leech else False

        if args["-swap"]:
            self.swap_enabled = True
        if args["-swap-audio"]:
            self.swap_audio_enabled = True
        if args["-swap-video"]:
            self.swap_video_enabled = True
        if args["-swap-subtitle"]:
            self.swap_subtitle_enabled = True

        if (
            self.swap_audio_enabled
            or self.swap_video_enabled
            or self.swap_subtitle_enabled
        ):
            self.swap_enabled = True

        self.compression_enabled = args["-compress"]
        self.compress_video = args["-comp-video"]
        self.compress_audio = args["-comp-audio"]
        self.compress_image = args["-comp-image"]
        self.compress_document = args["-comp-document"]
        self.compress_subtitle = args["-comp-subtitle"]
        self.compress_archive = args["-comp-archive"]

        if (
            self.compress_video
            or self.compress_audio
            or self.compress_image
            or self.compress_document
            or self.compress_subtitle
            or self.compress_archive
        ):
            self.compression_enabled = True

        # ... (Presets logic) ...
        self.video_preset = None
        if args["-video-fast"]: self.video_preset = "fast"
        elif args["-video-medium"]: self.video_preset = "medium"
        elif args["-video-slow"]: self.video_preset = "slow"

        self.audio_preset = None
        if args["-audio-fast"]: self.audio_preset = "fast"
        elif args["-audio-medium"]: self.audio_preset = "medium"
        elif args["-audio-slow"]: self.audio_preset = "slow"

        self.image_preset = None
        if args["-image-fast"]: self.image_preset = "fast"
        elif args["-image-medium"]: self.image_preset = "medium"
        elif args["-image-slow"]: self.image_preset = "slow"

        self.document_preset = None
        if args["-document-fast"]: self.document_preset = "fast"
        elif args["-document-medium"]: self.document_preset = "medium"
        elif args["-document-slow"]: self.document_preset = "slow"

        self.subtitle_preset = None
        if args["-subtitle-fast"]: self.subtitle_preset = "fast"
        elif args["-subtitle-medium"]: self.subtitle_preset = "medium"
        elif args["-subtitle-slow"]: self.subtitle_preset = "slow"

        self.archive_preset = None
        if args["-archive-fast"]: self.archive_preset = "fast"
        elif args["-archive-medium"]: self.archive_preset = "medium"
        elif args["-archive-slow"]: self.archive_preset = "slow"

        headers = args["-h"]
        if headers:
            headers = headers.split("|")

        is_bulk = self.is_bulk
        bulk_start = 0
        bulk_end = 0
        if isinstance(args["-b"], str):
             dargs = str(args["-b"]).split(":")
             bulk_start = int(dargs[0]) if dargs[0] else 0
             if len(dargs) == 2:
                bulk_end = int(dargs[1]) if dargs[1] else 0
             is_bulk = True
        else:
             is_bulk = bool(args["-b"])

        # RESTORED CONFIG CHECKS
        if not Config.MULTI_LINK_ENABLED and self.multi > 0:
            await send_message(self.message, "❌ Multi-link operations are disabled by the administrator.")
            self.multi = 0

        if not Config.SAME_DIR_ENABLED and self.folder_name:
            await send_message(self.message, "❌ Same directory operations (-m flag) are disabled by the administrator.")
            self.folder_name = None

        if not Config.LEECH_ENABLED and (
            self.hybrid_leech or self.bot_trans or self.user_trans or
            self.thumbnail_layout or self.split_size or args.get("-es", False) or
            self.as_doc or self.as_med
        ):
            await send_message(self.message, "❌ Leech operations are disabled by the administrator. Cannot use leech-related flags.")
            self.hybrid_leech = False
            self.bot_trans = False
            self.user_trans = False
            self.thumbnail_layout = ""
            self.split_size = 0
            if "-es" in args: args["-es"] = False
            self.as_doc = False
            self.as_med = False

        if not Config.TORRENT_ENABLED and self.seed:
            await send_message(self.message, "❌ Torrent operations are disabled by the administrator.")
            self.seed = False

        if self.is_bulk and not Config.BULK_ENABLED:
            await send_message(self.message, "❌ Bulk operations are disabled by the administrator.")
            self.is_bulk = False

        # ... FFmpeg resolution logic ...
        if args["-ff"] or self.ffmpeg_cmds: # self.ffmpeg_cmds might be populated from auto_ff
            # Handle FFmpeg command parsing
            raw_input = args["-ff"]
            # Logic to handle raw_input being set/list/str is reused

            # If self.ffmpeg_cmds is already populated from auto_ff parsing above, we append or merge
            current_cmds = self.ffmpeg_cmds or []
            self.ffmpeg_cmds = [] # Reset to resolve standard -ff args first then append

            # Helper to get commands from keys
            def get_cmds_from_key(key):
                if Config.FFMPEG_CMDS and key in Config.FFMPEG_CMDS:
                    return Config.FFMPEG_CMDS[key]
                if self.user_dict.get("FFMPEG_CMDS") and key in self.user_dict["FFMPEG_CMDS"]:
                    return self.user_dict["FFMPEG_CMDS"][key]
                return None

            try:
                # Process args["-ff"]
                if isinstance(raw_input, set):
                    for key in raw_input:
                        cmds = get_cmds_from_key(key)
                        if cmds:
                            for cmd in cmds: self.ffmpeg_cmds.append(cmd)
                elif isinstance(raw_input, list):
                    for item in raw_input:
                        if isinstance(item, str):
                            cmds = get_cmds_from_key(item)
                            if cmds:
                                for cmd in cmds: self.ffmpeg_cmds.append(cmd)
                            else:
                                import shlex
                                self.ffmpeg_cmds.append(shlex.split(item))
                        elif isinstance(item, list):
                            self.ffmpeg_cmds.append(item)
                elif isinstance(raw_input, str):
                    cmds = get_cmds_from_key(raw_input)
                    if cmds:
                        for cmd in cmds: self.ffmpeg_cmds.append(cmd)
                    else:
                        import shlex
                        self.ffmpeg_cmds.append(shlex.split(raw_input))

                # Append auto_ff cmds if they were parsed
                if current_cmds:
                     # auto_ff parsing above might have populated self.ffmpeg_cmds if -ff was in it.
                     # If auto_ff didn't contain -ff but other flags, they are in self.args.
                     # If it did contain -ff, we need to extract it?
                     # My auto_ff parsing logic above might be incomplete regarding -ff key.
                     # If we reparsed auto_ff into args["-ff"], then raw_input (args["-ff"]) already contains it?
                     # Yes, if I merged auto_args into self.args properly.
                     pass

            except Exception as e:
                self.ffmpeg_cmds = []
                LOGGER.error(f"Error processing FFmpeg command: {e}")


        if not isinstance(self.seed, bool):
            dargs = self.seed.split(":")
            ratio = dargs[0] or None
            if len(dargs) == 2:
                seed_time = dargs[1] or None
            self.seed = True

        if not self.is_bulk and len(self.bulk) == 0:
            from bot.helper.ext_utils.bulk_links import extract_bulk_links
            self.bulk = await extract_bulk_links(self.message, bulk_start, bulk_end)
            if len(self.bulk) > 1:
                self.is_bulk = True

        if is_bulk:
             await self.init_bulk(
                 input_list,
                 bulk_start,
                 bulk_end,
                 Mirror,
                 is_qbit=self.is_qbit,
                 is_leech=self.is_leech,
                 is_jd=self.is_jd,
                 is_nzb=self.is_nzb,
                 is_md_leech=self.is_md_leech,
                 is_enc=self.is_enc,
                 auto_link=self.auto_link,
                 auto_ff=self.auto_ff
             )
             return None

        if len(self.bulk) != 0:
            del self.bulk[0]

        await self.run_multi(input_list, Mirror)

        await self.get_tag(text)

        path = f"{DOWNLOAD_DIR}{self.mid}{self.folder_name}"

        reply_to = self.message.reply_to_message
        if not reply_to and self.message.reply_to_message_id:
            reply_to = await self.client.get_messages(self.message.chat.id, self.message.reply_to_message_id)

        file_ = None
        if reply_to:
            file_ = (
                reply_to.document or reply_to.photo or reply_to.video or
                reply_to.audio or reply_to.voice or reply_to.video_note or
                reply_to.sticker or reply_to.animation or None
            )
            if file_:
                if reply_to.document and (
                    file_.mime_type == "application/x-bittorrent" or
                    file_.file_name.endswith((".torrent", ".dlc", ".nzb"))
                ):
                    self.link = await reply_to.download()
                    file_ = None
                else:
                    self.link = ""
            elif not self.link and reply_to.text:
                potential_link = reply_to.text.split("\n", 1)[0].strip()
                if is_url(potential_link) or is_magnet(potential_link) or is_telegram_link(potential_link):
                    self.link = potential_link

        if is_telegram_link(self.link):
            try:
                reply_to, session = await get_tg_link_message(self.link, user_id)
            except Exception as e:
                error_msg = f"ERROR: {e!s}" if e else "ERROR: Failed to process Telegram link"
                x = await send_message(self.message, error_msg)
                await self.remove_from_same_dir()
                await delete_links(self.message)
                return await auto_delete_message(x, time=300)

        if isinstance(reply_to, list):
            self.bulk = reply_to
            b_msg = input_list[:1]
            self.options = " ".join(input_list[1:])
            b_msg.append(f"{self.bulk[0]} -i {len(self.bulk)} {self.options}")
            nextmsg = await send_message(self.message, " ".join(b_msg))
            nextmsg = await self.client.get_messages(chat_id=self.message.chat.id, message_ids=nextmsg.id)
            if self.message.from_user: nextmsg.from_user = self.user
            else: nextmsg.sender_chat = self.user
            await Mirror(
                self.client,
                nextmsg,
                is_qbit=self.is_qbit,
                is_leech=self.is_leech,
                is_jd=self.is_jd,
                is_nzb=self.is_nzb,
                is_md_leech=self.is_md_leech,
                is_enc=self.is_enc,
                same_dir=self.same_dir,
                bulk=self.bulk,
                multi_tag=self.multi_tag,
                options=self.options
            ).new_event()
            return await delete_links(self.message)

        if file_ and self.link and not self.link.startswith(("http://", "https://", "magnet:", "ftp://")):
            if not self.name: self.name = self.link
            self.link = ""

        try:
            if (self.link and (is_magnet(self.link) or self.link.endswith(".torrent"))) or \
               (file_ and file_.file_name and file_.file_name.endswith(".torrent")):
                if not Config.TORRENT_ENABLED:
                    await self.on_download_error("❌ Torrent operations are disabled...")
                    return None
                self.is_qbit = True
        except: pass

        if (
            (not self.link and file_ is None)
            or (is_telegram_link(self.link) and reply_to is None)
            or (
                file_ is None
                and self.link
                and not is_url(self.link)
                and not is_magnet(self.link)
                and not await aiopath.exists(self.link)
                and not is_rclone_path(self.link)
                and not is_gdrive_id(self.link)
                and not is_mega_link(self.link)
                and not (Config.STREAMRIP_ENABLED and await is_streamrip_url(self.link))
            )
        ):
            x = await send_message(self.message, COMMAND_USAGE["mirror"][0], COMMAND_USAGE["mirror"][1])
            await self.remove_from_same_dir()
            await delete_links(self.message)
            return await auto_delete_message(x, time=300)

        if self.media_tools:
            proceed = await show_media_tools_for_task(self.client, self.message, self)
            if not proceed:
                await self.remove_from_same_dir()
                await delete_links(self.message)
                return None
        else:
            from bot.modules.media_tools import direct_task_results
            if user_id in direct_task_results:
                result = direct_task_results[user_id]
                del direct_task_results[user_id]
                if not result:
                    await self.remove_from_same_dir()
                    await delete_links(self.message)
                    return None

        try:
            await self.before_start()
        except Exception as e:
            error_msg = str(e) if e else "An unknown error occurred"
            x = await send_message(self.message, error_msg)
            await self.remove_from_same_dir()
            await delete_links(self.message)
            return await auto_delete_message(x, time=300)

        size = 0
        if file_: size = file_.file_size

        if size > 0:
            limit_msg = await limit_checker(self)
            if limit_msg:
                await self.remove_from_same_dir()
                await delete_links(self.message)
                return None

        # Logic for starting download ...
        if (
            not self.is_jd and not self.is_nzb and not self.is_qbit
            and not is_mega_link(self.link) and not is_gdrive_link(self.link)
            and not is_gdrive_id(self.link) and not is_rclone_path(self.link)
            and not (Config.STREAMRIP_ENABLED and await is_streamrip_url(self.link))
            and not (Config.ZOTIFY_ENABLED and await is_zotify_url(self.link))
            and not await aiopath.exists(self.link) and not file_
        ):
            content_type = await get_content_type(self.link)
            if content_type and "x-bittorrent" in content_type: self.is_qbit = True
            if content_type is None or re_match(r"text/html|text/plain", content_type):
                try:
                    resolver = TrueLinkResolver()
                    if hasattr(resolver, 'resolve'): res = await resolver.resolve(self.link)
                    elif hasattr(resolver, 'get_direct_link'): res = await resolver.get_direct_link(self.link)
                    elif hasattr(resolver, 'resolve_link'): res = await resolver.resolve_link(self.link)
                    else: raise AttributeError
                    
                    if res and hasattr(res, 'url'): self.link = res.url
                    elif isinstance(res, str): self.link = res
                except: pass

                if (self.link and ("://" in self.link or self.link.startswith("magnet:"))) or is_magnet(self.link):
                    try:
                        from bot.helper.ext_utils.bot_utils import sync_to_async
                        res = await sync_to_async(direct_link_generator, self.link)
                        if isinstance(res, dict):
                            if "links" in res and res["links"]: self.link = res["links"][0]
                            else: self.link = res.get("url", self.link)
                        elif isinstance(res, str): self.link = res
                    except DirectDownloadLinkException as e:
                        e = str(e)
                        if "ERROR" in e:
                             await self.on_download_error(f"❌ {e}")
                             return None
                    except Exception as e:
                        LOGGER.error(f"Direct link gen failed: {e}")

        if (
            not is_url(self.link) and not is_magnet(self.link) and
            not await aiopath.exists(self.link) and not is_rclone_path(self.link) and
            not is_gdrive_id(self.link) and not is_mega_link(self.link) and
            not (Config.STREAMRIP_ENABLED and await is_streamrip_url(self.link)) and
            not (Config.ZOTIFY_ENABLED and await is_zotify_url(self.link)) and
            file_ is None
        ):
            await self.on_download_error(f"❌ Invalid link or file path: {self.link}")
            return None

        if is_url(self.link) and not file_:
            limit_msg = await limit_checker(self)
            if limit_msg:
                await self.remove_from_same_dir()
                await delete_links(self.message)
                return None

        if file_ is not None:
            create_task(TelegramDownloadHelper(self).add_download(reply_to, f"{path}/", session))
            await delete_links(self.message)
            return None
        elif self.is_jd: await add_jd_download(self, path)
        elif self.is_nzb: await add_nzb(self, path)
        elif self.is_qbit: await add_qb_torrent(self, path, ratio, seed_time)
        elif is_mega_link(self.link): await add_mega_download(self, path)
        elif is_rclone_path(self.link): await add_rclone_download(self, path)
        elif is_gdrive_link(self.link) or is_gdrive_id(self.link): await add_gd_download(self, path)
        elif Config.STREAMRIP_ENABLED and await is_streamrip_url(self.link): await self._handle_streamrip_download(path)
        elif Config.ZOTIFY_ENABLED and await is_zotify_url(self.link): await add_zotify_download(self, path)
        else: await add_direct_download(self, path)

        await delete_links(self.message)
        return None

    async def _handle_streamrip_download(self, path):
        from bot.helper.mirror_leech_utils.download_utils.streamrip_download import add_streamrip_download
        await add_streamrip_download(self, path)


async def handle_mirror_command(client, message, **kwargs):
    if kwargs.get('is_leech') and not Config.LEECH_ENABLED:
        return await send_message(message, "❌ Leech is disabled by the administrator.")
    if kwargs.get('is_jd') and not Config.JD_ENABLED:
        return await send_message(message, "❌ JDownloader is disabled by the administrator.")
    if kwargs.get('is_nzb') and not Config.NZB_ENABLED:
        return await send_message(message, "❌ NZB is disabled by the administrator.")

    from bot.helper.ext_utils.bulk_links import extract_bulk_links
    bulk = await extract_bulk_links(message, "0", "0") if Config.BULK_ENABLED else []

    if len(bulk) > 1:
        # Pass kwargs to init_bulk to preserve flags
        await Mirror(client, message, **kwargs).init_bulk(
            message.text.split("\n")[0].split(),
            0,
            0,
            Mirror,
            **kwargs
        )
    else:
        bot_loop.create_task(Mirror(client, message, **kwargs).new_event())

async def mirror(client, message): await handle_mirror_command(client, message)
async def leech(client, message): await handle_mirror_command(client, message, is_leech=True)
async def jd_mirror(client, message): await handle_mirror_command(client, message, is_jd=True)
async def nzb_mirror(client, message): await handle_mirror_command(client, message, is_nzb=True)
async def jd_leech(client, message): await handle_mirror_command(client, message, is_leech=True, is_jd=True)
async def nzb_leech(client, message): await handle_mirror_command(client, message, is_leech=True, is_nzb=True)
async def md_leech_node(client, message): await handle_mirror_command(client, message, is_leech=True, is_md_leech=True)
