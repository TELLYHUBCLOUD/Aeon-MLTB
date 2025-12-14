"""
Video Compression Module - Remove Audio/Subtitles & Compress
Optimized for maximum size reduction and fast uploads
"""

import os
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from time import time

from aiofiles.os import path as aiopath
from aiofiles.os import remove as aioremove
from aiofiles.os import stat as aiostat

from bot import DOWNLOAD_DIR, LOGGER, bot_loop
from bot.core.aeon_client import TgClient
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.status_utils import get_readable_file_size
from bot.helper.telegram_helper.message_utils import (
    delete_message,
    edit_message,
    send_message,
)


async def get_video_duration(file_path: str) -> int:
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        process = await create_subprocess_exec(
            *cmd,
            stdout=PIPE,
            stderr=PIPE
        )
        
        stdout, _ = await process.communicate()
        
        if process.returncode == 0:
            return int(float(stdout.decode().strip()))
        return 0
        
    except Exception as e:
        LOGGER.error(f"Failed to get video duration: {e}")
        return 0


async def compress_video(
    input_file: str,
    output_file: str,
    crf: int = 28,
    scale: str = "iw/2:ih/2",
    preset: str = "veryfast",
    progress_msg=None
) -> bool:
    """
    Compress video with all audio and subtitles removed.
    
    Args:
        input_file: Path to input video
        output_file: Path to output video
        crf: Compression level (18-32, higher = smaller)
        scale: Resolution scale (default: 50%)
        preset: FFmpeg preset (ultrafast, veryfast, fast, medium)
        progress_msg: Message to update with progress
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-map", "0:v:0",  # Only first video stream
            "-vf", f"scale={scale}",  # Scale resolution
            "-c:v", "libx264",  # H.264 codec
            "-preset", preset,  # Encoding speed
            "-crf", str(crf),  # Quality (higher = smaller)
            "-an",  # Remove all audio
            "-sn",  # Remove all subtitles
            "-map_metadata", "-1",  # Remove metadata
            "-movflags", "+faststart",  # Optimize for streaming
            "-y",  # Overwrite output
            output_file
        ]
        
        LOGGER.info(f"FFmpeg command: {' '.join(cmd)}")
        
        # Update progress
        if progress_msg:
            await edit_message(
                progress_msg,
                "🎬 <b>Compressing video...</b>\n\n"
                "⚙️ Removing audio & subtitles\n"
                "📉 Reducing file size\n"
                "⏳ This may take a few minutes..."
            )
        
        # Run FFmpeg
        process = await create_subprocess_exec(
            *cmd,
            stdout=PIPE,
            stderr=PIPE
        )
        
        _, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            LOGGER.error(f"FFmpeg compression failed: {error_msg}")
            return False
            
        # Verify output exists
        if not await aiopath.exists(output_file):
            LOGGER.error("Output file not created")
            return False
            
        return True
        
    except Exception as e:
        LOGGER.error(f"Compression error: {e}")
        return False


async def download_telegram_video(message, output_path: str) -> tuple[bool, int]:
    """Download video from Telegram message"""
    try:
        video = message.video or message.document
        if not video:
            return False, 0
            
        file_size = video.file_size
        
        # Download file
        await message.download(output_path)
        
        return True, file_size
        
    except Exception as e:
        LOGGER.error(f"Telegram download failed: {e}")
        return False, 0


async def _compress_event(client, message):
    """Main compress handler"""
    user_id = message.from_user.id
    work_dir = None
    input_file = None
    output_file = None
    status_msg = None
    
    try:
        # Check if video is provided
        reply = message.reply_to_message
        
        if not reply or (not reply.video and not reply.document):
            help_text = (
                "🎬 <b>Video Compressor</b>\n\n"
                "<b>Usage:</b>\n"
                "Reply to a video with <code>/compress</code>\n\n"
                "<b>What it does:</b>\n"
                "✅ Removes ALL audio tracks\n"
                "✅ Removes ALL subtitles\n"
                "✅ Compresses video to 50% resolution\n"
                "✅ Reduces file size significantly\n"
                "✅ Optimized for fast uploads\n\n"
                "<b>Perfect for:</b>\n"
                "• Telegram uploads\n"
                "• Saving storage space\n"
                "• Faster sharing"
            )
            await send_message(message, help_text)
            return
            
        # Create working directory
        work_dir = os.path.join(DOWNLOAD_DIR, f"compress_{user_id}_{int(time())}")
        os.makedirs(work_dir, exist_ok=True)
        
        input_file = os.path.join(work_dir, "input_video.mp4")
        output_file = os.path.join(work_dir, "compressed.mp4")
        
        # Send initial message
        status_msg = await send_message(
            message,
            "📥 <b>Downloading video...</b>\n\n⏳ Please wait..."
        )
        
        # Download video
        success, original_size = await download_telegram_video(reply, input_file)
        
        if not success:
            await edit_message(status_msg, "❌ Failed to download video")
            return
            
        await edit_message(
            status_msg,
            f"✅ <b>Downloaded!</b>\n\n"
            f"📊 Original Size: {get_readable_file_size(original_size)}\n\n"
            f"🔄 Starting compression..."
        )
        
        # Get video duration for final upload
        duration = await get_video_duration(input_file)
        
        # Compress video
        compress_success = await compress_video(
            input_file,
            output_file,
            crf=28,  # Good balance of size/quality
            scale="iw/2:ih/2",  # 50% resolution
            preset="veryfast",  # Fast encoding
            progress_msg=status_msg
        )
        
        if not compress_success:
            await edit_message(
                status_msg,
                "❌ <b>Compression failed</b>\n\n"
                "Please try again or use a different video."
            )
            return
            
        # Get compressed file size
        file_stat = await aiostat(output_file)
        compressed_size = file_stat.st_size
        
        # Calculate reduction
        reduction = original_size - compressed_size
        reduction_percent = (reduction / original_size) * 100 if original_size > 0 else 0
        
        # Update message
        await edit_message(
            status_msg,
            f"✅ <b>Compression complete!</b>\n\n"
            f"📊 <b>Original:</b> {get_readable_file_size(original_size)}\n"
            f"📉 <b>Compressed:</b> {get_readable_file_size(compressed_size)}\n"
            f"💾 <b>Saved:</b> {get_readable_file_size(reduction)} ({reduction_percent:.1f}%)\n\n"
            f"📤 Uploading..."
        )
        
        # Upload compressed video
        caption = (
            f"🎬 <b>Compressed Video</b>\n\n"
            f"📊 <b>Original:</b> {get_readable_file_size(original_size)}\n"
            f"📉 <b>Compressed:</b> {get_readable_file_size(compressed_size)}\n"
            f"💾 <b>Reduction:</b> {reduction_percent:.1f}%\n\n"
            f"✅ Audio removed\n"
            f"✅ Subtitles removed\n"
            f"✅ Optimized for uploads\n\n"
            f"<b>Credits:</b> @TellYCloudBots"
        )
        
        await TgClient.bot.send_video(
            chat_id=message.chat.id,
            video=output_file,
            caption=caption,
            duration=duration,
            supports_streaming=True,
            reply_to_message_id=message.id
        )
        
        # Success message
        await edit_message(
            status_msg,
            f"✅ <b>Done!</b>\n\n"
            f"Compressed video uploaded successfully!"
        )
        
        # Delete status message after 10 seconds
        await sync_to_async(lambda: None).__await__()  # Small delay
        
    except Exception as e:
        error_text = f"❌ <b>Error:</b>\n\n<code>{str(e)}</code>"
        
        if status_msg:
            await edit_message(status_msg, error_text)
        else:
            await send_message(message, error_text)
            
        LOGGER.error(f"Compress error for user {user_id}: {e}")
        
    finally:
        # Cleanup files
        try:
            if input_file and await aiopath.exists(input_file):
                await aioremove(input_file)
                
            if output_file and await aiopath.exists(output_file):
                await aioremove(output_file)
                
            if work_dir and os.path.exists(work_dir):
                import shutil
                shutil.rmtree(work_dir, ignore_errors=True)
                
        except Exception as e:
            LOGGER.error(f"Cleanup error: {e}")


async def compress_handler(client, message):
    """Wrapper for compress command"""
    bot_loop.create_task(_compress_event(client, message))


async def compression_callback_handler(client, query):
    """Handle compress-related callbacks (placeholder for future features)"""
    await query.answer("✅ Compress feature active!", show_alert=False)
