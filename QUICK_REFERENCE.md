# 🎬 VIDEO COMPRESSOR - QUICK REFERENCE

## ⚡ Quick Start (3 Steps)

1. **Start Bot:** Double-click `fix_and_start.bat`
2. **Send Video:** Send video to bot in Telegram
3. **Compress:** Reply with `/compress`

## 📊 What It Does

```
INPUT: Video (any size/format) with audio & subtitles
  ↓
PROCESSING: Remove audio, remove subtitles, compress video
  ↓
OUTPUT: Clean MP4 video, 70% smaller, upload-ready
```

## 🎯 FFmpeg Command Used

```bash
ffmpeg -i input.mp4 \
  -map 0:v:0 \              # Video only
  -vf scale=iw/2:ih/2 \     # 50% size
  -c:v libx264 \            # H.264
  -preset veryfast \        # Fast
  -crf 28 \                 # Balanced quality
  -an \                     # NO AUDIO ✓
  -sn \                     # NO SUBS ✓
  -map_metadata -1 \        # Clean
  -movflags +faststart \    # Optimized
  output.mp4
```

## 📈 Typical Results

| Original | Compressed | Saved |
|----------|-----------|-------|
| 200 MB | 50-70 MB | 70% |
| 500 MB | 100-150 MB | 75% |
| 1 GB | 200-300 MB | 75% |
| 2 GB | 400-600 MB | 75% |

## ⚙️ Settings

- **Resolution:** 50% (1080p → 540p)
- **Quality (CRF):** 28 (balanced)
- **Speed:** veryfast preset
- **Audio:** Completely removed
- **Subtitles:** Completely removed
- **Format:** MP4 (universal)

## 🔧 Customization

Edit `bot/modules/compress.py` line ~175:

```python
# Change quality (lower CRF = better but bigger)
crf=23,  # High quality
crf=28,  # Balanced (default)
crf=32,  # Maximum compression

# Change resolution
scale="iw/1:ih/1",  # Keep original (no resize)
scale="iw/2:ih/2",  # 50% (default)
scale="iw/4:ih/4",  # 25% (very small)
scale="1280:720",   # Fixed 720p

# Change speed
preset="ultrafast",  # Fastest
preset="veryfast",   # Fast (default)
preset="medium",     # Better compression
```

## 📁 Important Files

```
fix_and_start.bat              ← START HERE
COMPRESS_GUIDE.md              ← Full documentation
bot/modules/compress.py        ← Main code
bot/modules/__init__.py        ← Registration
```

## ✅ Requirements

- Python 3.9+
- FFmpeg installed
- Telegram bot token configured
- Enough disk space for temp files

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| Command not working | Restart bot, clear cache |
| FFmpeg error | Install FFmpeg |
| Video too large | Try smaller video first |
| Quality too poor | Lower CRF (23 instead of 28) |
| File still big | Higher CRF (32) or smaller scale |

## 💡 Use Cases

✅ Telegram uploads (fits 2GB limit)  
✅ Storage saving (70%+ reduction)  
✅ Fast sharing (smaller = faster)  
✅ Silent videos (no audio needed)  
✅ Screen recordings (clean output)  
✅ Preview clips (quick versions)  

## 📞 Support

Full guide: `COMPRESS_GUIDE.md`  
Bot command: `/compress` (reply to video)  
Credits: @TellYCloudBots

---

**Version:** 1.0  
**Last Updated:** 2025-12-14  
**Status:** ✅ Production Ready
