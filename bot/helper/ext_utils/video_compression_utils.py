"""
Video Compression Utilities

Helper functions for video compression operations including
metadata extraction, FFmpeg command building, and size estimation.
"""

import json
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE

from bot import LOGGER, cpu_no


async def extract_metadata_from_partial(file_path: str) -> dict:
    """
    Extract complete metadata from a partial video file using ffprobe.

    Args:
        file_path: Path to the partial video file

    Returns:
        Dictionary containing streams, format info, and parsed tracks
    """
    cmd = [
        "ffprobe",
        "-hide_banner",
        "-loglevel",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        file_path,
    ]

    try:
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            LOGGER.error(f"FFprobe error: {stderr.decode().strip()}")
            return {}

        metadata = json.loads(stdout)

        # Parse streams into organized tracks
        audio_tracks = []
        subtitle_tracks = []
        video_tracks = []

        for stream in metadata.get("streams", []):
            stream_type = stream.get("codec_type")
            index = stream.get("index")

            if stream_type == "audio":
                audio_tracks.append(
                    {
                        "index": index,
                        "codec": stream.get("codec_name", "unknown"),
                        "language": stream.get("tags", {}).get("language", "und"),
                        "title": stream.get("tags", {}).get("title", ""),
                        "channels": stream.get("channels", 0),
                        "sample_rate": stream.get("sample_rate", ""),
                        "bitrate": stream.get("bit_rate", "N/A"),
                    },
                )
            elif stream_type == "subtitle":
                subtitle_tracks.append(
                    {
                        "index": index,
                        "codec": stream.get("codec_name", "unknown"),
                        "language": stream.get("tags", {}).get("language", "und"),
                        "title": stream.get("tags", {}).get("title", ""),
                        "forced": stream.get("disposition", {}).get("forced", 0),
                    },
                )
            elif stream_type == "video":
                video_tracks.append(
                    {
                        "index": index,
                        "codec": stream.get("codec_name", "unknown"),
                        "width": stream.get("width", 0),
                        "height": stream.get("height", 0),
                        "fps": eval(stream.get("r_frame_rate", "0/1")),
                        "bitrate": stream.get("bit_rate", "N/A"),
                    },
                )

        # Extract format info
        format_info = metadata.get("format", {})
        duration = int(float(format_info.get("duration", 0)))
        file_size = int(format_info.get("size", 0))
        format_name = format_info.get("format_name", "unknown")

        # Get resolution from first video track
        resolution = ""
        if video_tracks:
            width = video_tracks[0].get("width", 0)
            height = video_tracks[0].get("height", 0)
            resolution = f"{width}x{height}"

        return {
            "audio_tracks": audio_tracks,
            "subtitle_tracks": subtitle_tracks,
            "video_tracks": video_tracks,
            "duration": duration,
            "file_size": file_size,
            "format_name": format_name,
            "resolution": resolution,
        }

    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse ffprobe JSON output: {e}")
        return {}
    except Exception as e:
        LOGGER.error(f"Metadata extraction failed: {e}")
        return {}


def get_compression_preset(level: str) -> dict:
    """
    Get FFmpeg compression parameters for the specified level.

    Args:
        level: Compression level ('low', 'medium', or 'high')

    Returns:
        Dictionary with CRF, preset, and description
    """
    presets = {
        "low": {
            "crf": "28",
            "preset": "fast",
            "description": "Maximum compression, smaller file size",
        },
        "medium": {
            "crf": "23",
            "preset": "medium",
            "description": "Balanced quality and size",
        },
        "high": {
            "crf": "18",
            "preset": "slow",
            "description": "Better quality, less compression",
        },
    }

    return presets.get(level.lower(), presets["medium"])


def build_ffmpeg_compress_cmd(
    input_file: str,
    output_file: str,
    audio_tracks: list[int],
    subtitle_tracks: list[int],
    compression_level: str = "medium",
) -> list:
    """
    Build FFmpeg command for video compression with selective track mapping.

    Args:
        input_file: Path to input video
        output_file: Path to output video
        audio_tracks: List of audio track indices to keep (empty = remove all)
        subtitle_tracks: List of subtitle track indices to keep (empty = remove all)
        compression_level: Compression level ('low', 'medium', 'high')

    Returns:
        List of command arguments for FFmpeg
    """
    preset = get_compression_preset(compression_level)

    cmd = [
        "xtra",  # FFmpeg binary name in this project
        "-hide_banner",
        "-loglevel",
        "error",
        "-progress",
        "pipe:1",
        "-i",
        input_file,
    ]

    # Map video stream (first video track)
    cmd.extend(["-map", "0:v:0"])

    # Map selected audio tracks
    if audio_tracks:
        for audio_idx in audio_tracks:
            cmd.extend(["-map", f"0:{audio_idx}"])
    # If no audio tracks selected, explicitly exclude audio
    else:
        cmd.extend(["-an"])

    # Map selected subtitle tracks
    if subtitle_tracks:
        for sub_idx in subtitle_tracks:
            cmd.extend(["-map", f"0:{sub_idx}"])
    # If no subtitle tracks selected, explicitly exclude subtitles
    else:
        cmd.extend(["-sn"])

    # Video codec settings
    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-crf",
            preset["crf"],
            "-preset",
            preset["preset"],
        ],
    )

    # Audio codec (if any audio tracks selected)
    if audio_tracks:
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])

    # Subtitle codec (if any subtitle tracks selected)
    if subtitle_tracks:
        cmd.extend(["-c:s", "mov_text"])  # For MP4 container

    # Threading and output
    cmd.extend(
        [
            "-threads",
            f"{max(1, cpu_no // 2)}",
            output_file,
        ],
    )

    return cmd


def estimate_compressed_size(original_size: int, compression_level: str) -> int:
    """
    Estimate the compressed file size based on compression level.

    Args:
        original_size: Original file size in bytes
        compression_level: Compression level ('low', 'medium', 'high')

    Returns:
        Estimated compressed size in bytes
    """
    # Rough compression ratios based on CRF values
    ratios = {
        "low": 0.3,  # ~70% reduction
        "medium": 0.5,  # ~50% reduction
        "high": 0.7,  # ~30% reduction
    }

    ratio = ratios.get(compression_level.lower(), 0.5)
    return int(original_size * ratio)


def format_track_info(tracks: list, track_type: str) -> str:
    """
    Format track information for user display.

    Args:
        tracks: List of track dictionaries
        track_type: Type of track ('audio' or 'subtitle')

    Returns:
        Formatted string describing the tracks
    """
    if not tracks:
        return f"No {track_type} tracks found"

    lines = []
    for i, track in enumerate(tracks, 1):
        index = track.get("index", "?")
        codec = track.get("codec", "unknown")
        language = track.get("language", "und")
        title = track.get("title", "")

        if track_type == "audio":
            channels = track.get("channels", 0)
            ch_text = f"{channels}ch"
            info = f"{i}. Track {index}: {language} ({codec}, {ch_text})"
            if title:
                info += f' - "{title}"'

        elif track_type == "subtitle":
            forced = " [Forced]" if track.get("forced") else ""
            info = f"{i}. Track {index}: {language} ({codec}){forced}"
            if title:
                info += f' - "{title}"'

        else:
            info = f"{i}. Track {index}: {language} ({codec})"

        lines.append(info)

    return "\n".join(lines)


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 GB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: int) -> str:
    """
    Format duration in HH:MM:SS format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
