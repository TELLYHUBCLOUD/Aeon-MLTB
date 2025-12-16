"""
Video Compression Module

Implements the /compress command for compressing videos with
user-selectable audio tracks, subtitle tracks, and quality levels.
"""

from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from os import path as ospath
from time import time

import aiohttp
from aiofiles import open as aiopen
from aiofiles.os import makedirs
from aiofiles.os import path as aiopath

from bot import DOWNLOAD_DIR, LOGGER
from bot.core.aeon_client import TgClient
from bot.helper.aeon_utils.access_check import token_check
from bot.helper.ext_utils.compression_state import compression_state_manager
from bot.helper.ext_utils.media_utils import FFMpeg
from bot.helper.ext_utils.video_compression_utils import (
    build_ffmpeg_compress_cmd,
    estimate_compressed_size,
    extract_metadata_from_partial,
    format_duration,
    format_size,
    format_track_info,
    get_compression_preset,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_links,
    delete_message,
    edit_message,
    send_message,
)

# Partial download size for metadata extraction (20 MB)
PARTIAL_DOWNLOAD_SIZE = 20 * 1024 * 1024


async def download_partial_video(
    url: str, output_path: str, size_limit: int
) -> bool:
    """
    Download partial video for metadata extraction.

    Args:
        url: Video URL
        output_path: Path to save partial file
        size_limit: Maximum bytes to download

    Returns:
        True if successful, False otherwise
    """
    try:
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers=headers) as response,
        ):
            if response.status != 200:
                LOGGER.error(f"Failed to download video: HTTP {response.status}")
                return False

            total_bytes = 0
            async with aiopen(output_path, "wb") as f:
                async for chunk in response.content.iter_chunked(1024 * 1024):
                    if total_bytes >= size_limit:
                        break
                    await f.write(chunk)
                    total_bytes += len(chunk)

            LOGGER.info(f"Downloaded {total_bytes} bytes for metadata extraction")
            return True

    except Exception as e:
        LOGGER.error(f"Partial download failed: {e}")
        return False


async def download_telegram_video(message, output_path: str) -> tuple[bool, int]:
    """
    Download video from Telegram message.

    Args:
        message: Telegram message containing video
        output_path: Path to save video

    Returns:
        Tuple of (success, file_size)
    """
    try:
        video = message.video or message.document
        if not video:
            return False, 0

        file_size = video.file_size
        await message.download(output_path)
        return True, file_size

    except Exception as e:
        LOGGER.error(f"Telegram download failed: {e}")
        return False, 0


async def download_full_video(url: str, output_path: str, progress_msg) -> bool:
    """
    Download complete video with progress updates.

    Args:
        url: Video URL
        output_path: Path to save video
        progress_msg: Message to update with progress

    Returns:
        True if successful, False otherwise
    """
    try:
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers=headers) as response,
        ):
            if response.status != 200:
                LOGGER.error(f"Failed to download video: HTTP {response.status}")
                return False

            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            last_update = time()

            async with aiopen(output_path, "wb") as f:
                async for chunk in response.content.iter_chunked(1024 * 1024):
                    await f.write(chunk)
                    downloaded += len(chunk)

                    # Update progress every 3 seconds
                    if time() - last_update > 3:
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            await edit_message(
                                progress_msg,
                                f"📥 <b>Downloading video...</b>\n\n"
                                f"Progress: {percent:.1f}%\n"
                                f"Downloaded: {format_size(downloaded)} / {format_size(total_size)}",
                            )
                        last_update = time()

            LOGGER.info(f"Downloaded complete video: {format_size(downloaded)}")
            return True

    except Exception as e:
        LOGGER.error(f"Full download failed: {e}")
        return False


async def compress_handler(client, message):
    """
    Main handler for /compress command.

    Usage:
        /compress <video_url>
        /compress (reply to video message)
    """
    user_id = message.from_user.id
    buttons = ButtonMaker()

    # Access check
    if message.chat.type != message.chat.type.PRIVATE:
        msg, buttons = await token_check(user_id, buttons)
        if msg is not None:
            reply_message = await send_message(message, msg, buttons.build_menu(1))
            await delete_links(message)
            await auto_delete_message(reply_message, time=300)
            return

    # Parse command
    reply = message.reply_to_message
    video_url = None
    video_message = None

    if len(message.command) > 1:
        video_url = message.command[1]
    elif reply and (reply.video or reply.document):
        video_message = reply
    elif reply and reply.text:
        video_url = reply.text
    else:
        help_msg = (
            f"<b>Video Compression Command</b>\n\n"
            f"<b>Usage:</b>\n"
            f"<code>/{BotCommands.CompressCommand} &lt;video_url&gt;</code>\n"
            f"or reply to a video message with:\n"
            f"<code>/{BotCommands.CompressCommand}</code>\n\n"
            f"<b>The bot will:</b>\n"
            f"1. Extract video metadata\n"
            f"2. Show available audio and subtitle tracks\n"
            f"3. Let you choose compression level\n"
            f"4. Compress and upload the video"
        )
        await send_message(message, help_msg)
        return

    # Create compression session
    session = await compression_state_manager.create_session(user_id, message.id)
    session.video_url = video_url

    # Create working directory
    work_dir = f"{DOWNLOAD_DIR}compress_{user_id}_{int(time())}"
    await makedirs(work_dir, exist_ok=True)

    status_msg = await send_message(
        message,
        "🔍 <b>Analyzing video...</b>\n\nExtracting metadata...",
    )

    try:
        # Download partial video for metadata extraction
        if video_message:
            # For Telegram videos, download the full file
            session.video_file_path = ospath.join(work_dir, "input_video.mp4")
            success, file_size = await download_telegram_video(
                video_message,
                session.video_file_path,
            )
            if not success:
                await edit_message(
                    status_msg, "❌ Failed to download Telegram video"
                )
                await compression_state_manager.remove_session(user_id)
                return
            session.file_size = file_size
            metadata_file = session.video_file_path

        else:
            # For URL videos, download partial for metadata
            session.partial_file_path = ospath.join(work_dir, "partial_video.mp4")
            success = await download_partial_video(
                video_url,
                session.partial_file_path,
                PARTIAL_DOWNLOAD_SIZE,
            )
            if not success:
                await edit_message(
                    status_msg, "❌ Failed to download video for analysis"
                )
                await compression_state_manager.remove_session(user_id)
                return
            metadata_file = session.partial_file_path

        # Extract metadata
        metadata = await extract_metadata_from_partial(metadata_file)

        if not metadata:
            await edit_message(
                status_msg,
                "❌ Failed to extract video metadata. The file may be corrupted or in an unsupported format.",
            )
            await compression_state_manager.remove_session(user_id)
            return

        # Store metadata in session
        session.audio_tracks = metadata.get("audio_tracks", [])
        session.subtitle_tracks = metadata.get("subtitle_tracks", [])
        session.video_tracks = metadata.get("video_tracks", [])
        session.duration = metadata.get("duration", 0)
        session.resolution = metadata.get("resolution", "unknown")
        session.format_name = metadata.get("format_name", "unknown")

        if not session.file_size:
            session.file_size = metadata.get("file_size", 0)

        # Initialize selections (select all by default)
        session.selected_audio_tracks = [t["index"] for t in session.audio_tracks]
        session.selected_subtitle_tracks = [
            t["index"] for t in session.subtitle_tracks
        ]

        # Build metadata display
        metadata_text = (
            f"📊 <b>Video Information</b>\n\n"
            f"<b>Duration:</b> {format_duration(session.duration)}\n"
            f"<b>Resolution:</b> {session.resolution}\n"
            f"<b>Size:</b> {format_size(session.file_size)}\n"
            f"<b>Format:</b> {session.format_name}\n\n"
        )

        if session.audio_tracks:
            metadata_text += f"<b>Audio Tracks ({len(session.audio_tracks)}):</b>\n"
            metadata_text += f"<code>{format_track_info(session.audio_tracks, 'audio')}</code>\n\n"
        else:
            metadata_text += "<b>Audio Tracks:</b> None\n\n"

        if session.subtitle_tracks:
            metadata_text += (
                f"<b>Subtitle Tracks ({len(session.subtitle_tracks)}):</b>\n"
            )
            metadata_text += f"<code>{format_track_info(session.subtitle_tracks, 'subtitle')}</code>\n\n"
        else:
            metadata_text += "<b>Subtitle Tracks:</b> None\n\n"

        metadata_text += "👇 <b>Select your preferences below:</b>"

        # Create selection buttons
        buttons = ButtonMaker()

        # Audio selection buttons
        if session.audio_tracks:
            buttons.data_button(
                "🔊 Select Audio Tracks", f"compress_{user_id}_audio"
            )
        buttons.data_button("🔇 Remove All Audio", f"compress_{user_id}_noaudio")

        # Subtitle selection buttons
        if session.subtitle_tracks:
            buttons.data_button(
                "📝 Select Subtitles",
                f"compress_{user_id}_subtitle",
            )
        buttons.data_button("❌ Remove All Subtitles", f"compress_{user_id}_nosub")

        # Compression level buttons
        buttons.data_button("🔴 Low Quality (Smaller)", f"compress_{user_id}_low")
        buttons.data_button(
            "🟡 Medium Quality (Balanced)",
            f"compress_{user_id}_medium",
        )
        buttons.data_button("🟢 High Quality (Larger)", f"compress_{user_id}_high")

        # Confirm/Cancel buttons
        buttons.data_button("✅ Start Compression", f"compress_{user_id}_confirm")
        buttons.data_button("🚫 Cancel", f"compress_{user_id}_cancel")

        session.workflow_step = "selecting"
        await edit_message(status_msg, metadata_text, buttons.build_menu(2))

    except Exception as e:
        LOGGER.error(f"Error in compress_handler: {e}")
        await edit_message(status_msg, f"❌ Error: {e!s}")
        await compression_state_manager.remove_session(user_id)


async def compression_callback_handler(client, query):
    """Handle button callbacks for compression workflow"""
    data = query.data.split("_")
    if len(data) < 3:
        await query.answer("Invalid callback data", show_alert=True)
        return

    user_id = int(data[1])
    action = "_".join(data[2:])

    # Verify user
    if query.from_user.id != user_id:
        await query.answer("This is not for you!", show_alert=True)
        return

    # Get session
    session = await compression_state_manager.get_session(user_id)
    if not session:
        await query.answer("Session expired. Please start again.", show_alert=True)
        return

    try:
        # Handle different actions
        if action == "noaudio":
            session.selected_audio_tracks = []
            await query.answer(
                "✓ All audio tracks will be removed", show_alert=False
            )

        elif action == "nosub":
            session.selected_subtitle_tracks = []
            await query.answer("✓ All subtitles will be removed", show_alert=False)

        elif action == "low":
            session.compression_level = "low"
            preset = get_compression_preset("low")
            await query.answer(
                f"✓ Selected: {preset['description']}",
                show_alert=False,
            )

        elif action == "medium":
            session.compression_level = "medium"
            preset = get_compression_preset("medium")
            await query.answer(
                f"✓ Selected: {preset['description']}",
                show_alert=False,
            )

        elif action == "high":
            session.compression_level = "high"
            preset = get_compression_preset("high")
            await query.answer(
                f"✓ Selected: {preset['description']}",
                show_alert=False,
            )

        elif action == "audio":
            # Show audio track selection menu
            await show_audio_selection(query, session)
            return

        elif action == "subtitle":
            # Show subtitle track selection menu
            await show_subtitle_selection(query, session)
            return

        elif action.startswith("audiotrack_"):
            # Toggle audio track selection
            track_idx = int(action.split("_")[1])
            if track_idx in session.selected_audio_tracks:
                session.selected_audio_tracks.remove(track_idx)
                await query.answer("✓ Audio track deselected", show_alert=False)
            else:
                session.selected_audio_tracks.append(track_idx)
                await query.answer("✓ Audio track selected", show_alert=False)
            await show_audio_selection(query, session)
            return

        elif action.startswith("subtrack_"):
            # Toggle subtitle track selection
            track_idx = int(action.split("_")[1])
            if track_idx in session.selected_subtitle_tracks:
                session.selected_subtitle_tracks.remove(track_idx)
                await query.answer("✓ Subtitle track deselected", show_alert=False)
            else:
                session.selected_subtitle_tracks.append(track_idx)
                await query.answer("✓ Subtitle track selected", show_alert=False)
            await show_subtitle_selection(query, session)
            return

        elif action == "back":
            # Go back to main menu
            await show_main_menu(query, session)
            return

        elif action == "confirm":
            # Start compression process
            await query.answer("🔄 Starting compression...", show_alert=False)
            await start_compression(query.message, session)
            return

        elif action == "cancel":
            await query.answer("✓ Compression cancelled", show_alert=True)
            await delete_message(query.message)
            await compression_state_manager.remove_session(user_id)
            return

    except Exception as e:
        LOGGER.error(f"Error in compression_callback_handler: {e}")
        await query.answer(f"Error: {e!s}", show_alert=True)


async def show_audio_selection(query, session):
    """Show audio track selection menu"""
    text = "<b>🔊 Select Audio Tracks to Keep</b>\n\n"

    for track in session.audio_tracks:
        idx = track["index"]
        selected = "✅" if idx in session.selected_audio_tracks else "☐"
        lang = track.get("language", "und")
        codec = track.get("codec", "unknown")
        channels = track.get("channels", 0)
        title = track.get("title", "")

        text += f"{selected} Track {idx}: {lang} ({codec}, {channels}ch)"
        if title:
            text += f' - "{title}"'
        text += "\n"

    buttons = ButtonMaker()

    # Track toggle buttons
    for track in session.audio_tracks:
        idx = track["index"]
        lang = track.get("language", "und")
        selected = "✅" if idx in session.selected_audio_tracks else "☐"
        buttons.data_button(
            f"{selected} {lang} ({idx})",
            f"compress_{session.user_id}_audiotrack_{idx}",
        )

    buttons.data_button("◀️ Back", f"compress_{session.user_id}_back")

    await query.message.edit(text, reply_markup=buttons.build_menu(2))


async def show_subtitle_selection(query, session):
    """Show subtitle track selection menu"""
    text = "<b>📝 Select Subtitle Tracks to Keep</b>\n\n"

    for track in session.subtitle_tracks:
        idx = track["index"]
        selected = "✅" if idx in session.selected_subtitle_tracks else "☐"
        lang = track.get("language", "und")
        codec = track.get("codec", "unknown")
        title = track.get("title", "")

        text += f"{selected} Track {idx}: {lang} ({codec})"
        if title:
            text += f' - "{title}"'
        text += "\n"

    buttons = ButtonMaker()

    # Track toggle buttons
    for track in session.subtitle_tracks:
        idx = track["index"]
        lang = track.get("language", "und")
        selected = "✅" if idx in session.selected_subtitle_tracks else "☐"
        buttons.data_button(
            f"{selected} {lang} ({idx})",
            f"compress_{session.user_id}_subtrack_{idx}",
        )

    buttons.data_button("◀️ Back", f"compress_{session.user_id}_back")

    await query.message.edit(text, reply_markup=buttons.build_menu(2))


async def show_main_menu(query, session):
    """Show main compression menu"""
    # Build summary
    text = "<b>📊 Compression Settings</b>\n\n"

    # Audio selection summary
    if session.selected_audio_tracks:
        text += (
            f"<b>Audio:</b> {len(session.selected_audio_tracks)} track(s) selected\n"
        )
    else:
        text += "<b>Audio:</b> All removed (muted video)\n"

    # Subtitle selection summary
    if session.selected_subtitle_tracks:
        text += f"<b>Subtitles:</b> {len(session.selected_subtitle_tracks)} track(s) selected\n"
    else:
        text += "<b>Subtitles:</b> All removed\n"

    # Compression level
    preset = get_compression_preset(session.compression_level)
    text += f"<b>Quality:</b> {session.compression_level.title()} - {preset['description']}\n\n"

    # Estimated size
    estimated = estimate_compressed_size(
        session.file_size, session.compression_level
    )
    text += f"<b>Original Size:</b> {format_size(session.file_size)}\n"
    text += f"<b>Estimated Size:</b> {format_size(estimated)}\n\n"
    text += "👇 <b>Adjust settings or confirm:</b>"

    # Recreate buttons
    buttons = ButtonMaker()

    if session.audio_tracks:
        buttons.data_button(
            "🔊 Select Audio Tracks", f"compress_{session.user_id}_audio"
        )
    buttons.data_button("🔇 Remove All Audio", f"compress_{session.user_id}_noaudio")

    if session.subtitle_tracks:
        buttons.data_button(
            "📝 Select Subtitles", f"compress_{session.user_id}_subtitle"
        )
    buttons.data_button(
        "❌ Remove All Subtitles", f"compress_{session.user_id}_nosub"
    )

    buttons.data_button("🔴 Low Quality", f"compress_{session.user_id}_low")
    buttons.data_button("🟡 Medium Quality", f"compress_{session.user_id}_medium")
    buttons.data_button("🟢 High Quality", f"compress_{session.user_id}_high")

    buttons.data_button(
        "✅ Start Compression", f"compress_{session.user_id}_confirm"
    )
    buttons.data_button("🚫 Cancel", f"compress_{session.user_id}_cancel")

    await query.message.edit(text, reply_markup=buttons.build_menu(2))


async def start_compression(message, session):
    """Start the video compression process"""
    try:
        await edit_message(message, "⏳ <b>Preparing for compression...</b>")

        # Download full video if not already downloaded
        if not session.video_file_path or not await aiopath.exists(
            session.video_file_path,
        ):
            if not session.video_url:
                await edit_message(message, "❌ No video URL available")
                await compression_state_manager.remove_session(session.user_id)
                return

            work_dir = ospath.dirname(
                session.partial_file_path
                or f"{DOWNLOAD_DIR}compress_{session.user_id}"
            )
            session.video_file_path = ospath.join(work_dir, "input_video.mp4")

            await edit_message(message, "📥 <b>Downloading full video...</b>")

            success = await download_full_video(
                session.video_url,
                session.video_file_path,
                message,
            )

            if not success:
                await edit_message(message, "❌ Failed to download video")
                await compression_state_manager.remove_session(session.user_id)
                return

        # Prepare output path
        work_dir = ospath.dirname(session.video_file_path)
        session.output_file_path = ospath.join(work_dir, "compressed_video.mp4")

        # Build FFmpeg command
        ffmpeg_cmd = build_ffmpeg_compress_cmd(
            session.video_file_path,
            session.output_file_path,
            session.selected_audio_tracks,
            session.selected_subtitle_tracks,
            session.compression_level,
        )

        LOGGER.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")

        await edit_message(
            message,
            "🎬 <b>Compressing video...</b>\n\nThis may take a while...",
        )

        # Run FFmpeg compression
        # Create a temporary listener object for FFmpeg class
        class TempListener:
            def __init__(self):
                self.subproc = None
                self.is_cancelled = False

        temp_listener = TempListener()
        FFMpeg(temp_listener)

        # Execute FFmpeg command
        process = await create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=PIPE,
            stderr=PIPE,
        )

        temp_listener.subproc = process
        _stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            LOGGER.error(f"FFmpeg compression failed: {error_msg}")
            await edit_message(
                message,
                f"❌ <b>Compression failed</b>\n\n<code>{error_msg[:500]}</code>",
            )
            await compression_state_manager.remove_session(session.user_id)
            return

        # Check output file
        if not await aiopath.exists(session.output_file_path):
            await edit_message(message, "❌ Compressed file not found")
            await compression_state_manager.remove_session(session.user_id)
            return

        # Get compressed file size
        from aiofiles.os import stat

        file_stat = await stat(session.output_file_path)
        compressed_size = file_stat.st_size

        await edit_message(
            message,
            f"📤 <b>Uploading compressed video...</b>\n\n"
            f"Original: {format_size(session.file_size)}\n"
            f"Compressed: {format_size(compressed_size)}\n"
            f"Saved: {format_size(session.file_size - compressed_size)} "
            f"({((session.file_size - compressed_size) / session.file_size * 100):.1f}%)",
        )

        # Upload compressed video
        caption = (
            f"🎬 <b>Compressed Video</b>\n\n"
            f"<b>Quality:</b> {session.compression_level.title()}\n"
            f"<b>Original Size:</b> {format_size(session.file_size)}\n"
            f"<b>Compressed Size:</b> {format_size(compressed_size)}\n"
            f"<b>Reduction:</b> {((session.file_size - compressed_size) / session.file_size * 100):.1f}%\n\n"
            f"<b>Credits:</b> @TellYCloudBots"
        )

        await TgClient.bot.send_video(
            chat_id=message.chat.id,
            video=session.output_file_path,
            caption=caption,
            duration=session.duration,
        )

        await edit_message(message, "✅ <b>Compression completed successfully!</b>")

        # Cleanup
        await compression_state_manager.remove_session(session.user_id)

    except Exception as e:
        LOGGER.error(f"Error in start_compression: {e}")
        await edit_message(
            message, f"❌ <b>Error during compression:</b>\n\n<code>{e!s}</code>"
        )
        await compression_state_manager.remove_session(session.user_id)
