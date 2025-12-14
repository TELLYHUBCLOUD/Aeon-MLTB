# 🎬 Video Compressor - Complete Guide

## ✨ Features

Your compress command now does **EXACTLY** what you requested:

✅ **Removes ALL audio tracks** - Complete silence  
✅ **Removes ALL subtitles** - Clean video only  
✅ **Compresses to 50% resolution** - Massive size reduction  
✅ **H.264 encoding** - Maximum compatibility  
✅ **Optimized for uploads** - Fast streaming enabled  
✅ **Metadata cleaned** - No extra data  

## 🎯 FFmpeg Settings Used

```bash
ffmpeg -i input.mp4 \
  -map 0:v:0 \              # Only first video stream
  -vf scale=iw/2:ih/2 \     # 50% resolution
  -c:v libx264 \            # H.264 codec
  -preset veryfast \        # Fast encoding
  -crf 28 \                 # Good compression
  -an \                     # NO AUDIO
  -sn \                     # NO SUBTITLES
  -map_metadata -1 \        # Remove metadata
  -movflags +faststart \    # Optimize for streaming
  output.mp4
```

## 📖 How to Use

### Step 1: Start Your Bot

Run the helper script:
```bash
# Double-click this file:
fix_and_start.bat

# OR manually run:
py -m bot
```

### Step 2: Send Video to Bot

In Telegram, send a video file to your bot (or forward it).

### Step 3: Compress It

Reply to the video with:
```
/compress
```

### Step 4: Wait for Magic! ✨

The bot will:
1. 📥 Download your video
2. 🎬 Compress it (remove audio/subs, reduce size)
3. 📊 Show you the savings
4. 📤 Upload the compressed version

## 📊 What You'll See

**During compression:**
```
🎬 Compressing video...

⚙️ Removing audio & subtitles
📉 Reducing file size
⏳ This may take a few minutes...
```

**After completion:**
```
✅ Compression complete!

📊 Original: 150.5 MB
📉 Compressed: 45.2 MB
💾 Saved: 105.3 MB (70.0%)

📤 Uploading...
```

**Final uploaded video caption:**
```
🎬 Compressed Video

📊 Original: 150.5 MB
📉 Compressed: 45.2 MB
💾 Reduction: 70.0%

✅ Audio removed
✅ Subtitles removed
✅ Optimized for uploads

Credits: @TellYCloudBots
```

## ⚙️ Technical Specifications

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Codec** | H.264 (libx264) | Universal compatibility |
| **CRF** | 28 | Good balance (size vs quality) |
| **Preset** | veryfast | Fast encoding speed |
| **Resolution** | 50% of original | Huge size reduction |
| **Audio** | Removed (-an) | No audio tracks |
| **Subtitles** | Removed (-sn) | No subtitle streams |
| **Metadata** | Removed | Cleaner file |
| **Container** | MP4 | Maximum compatibility |
| **Streaming** | Optimized | Fast playback start |

## 🎨 Customization Options

Want different settings? Edit `bot/modules/compress.py`:

### Change Compression Level (CRF)

```python
# Line ~175
crf=28,  # Lower = better quality, bigger file (18-32)
         # 18 = almost lossless
         # 23 = high quality (default FFmpeg)
         # 28 = good balance (current)
         # 32 = very compressed
```

### Change Resolution Scale

```python
# Line ~176
scale="iw/2:ih/2",  # Current: 50% resolution
# Examples:
# "iw/1:ih/1"      # Keep original (no resize)
# "iw/2:ih/2"      # 50% (current)
# "iw/4:ih/4"      # 25% (very small)
# "1280:720"       # Fixed 720p
# "854:480"        # Fixed 480p
```

### Change Encoding Speed

```python
# Line ~177
preset="veryfast",  # Current setting
# Options (slower = better compression):
# "ultrafast"  # Fastest, bigger files
# "veryfast"   # Very fast (current)
# "fast"       # Fast, better compression
# "medium"     # Balanced
# "slow"       # Slow, best compression
```

## 💡 Examples

### Example 1: Normal Video
```
Input:  1080p video, 200 MB, with audio
Output: 540p video, 50-70 MB, no audio
Savings: 65-75%
```

### Example 2: Large Movie
```
Input:  1080p movie, 2 GB, with audio & subs
Output: 540p video, 400-600 MB, clean
Savings: 70-80%
```

### Example 3: Screen Recording
```
Input:  1080p recording, 500 MB
Output: 540p clean video, 100-150 MB
Savings: 70-80%
```

## 🚀 Performance Tips

### For FASTER encoding:
```python
preset="ultrafast"  # Much faster
crf=32              # More compression
```

### For BETTER quality:
```python
preset="medium"     # Slower but better
crf=23              # Less compression
scale="iw/1:ih/1"   # Keep original resolution
```

### For SMALLEST file:
```python
preset="veryfast"   # Good speed
crf=32              # Maximum compression
scale="iw/4:ih/4"   # 25% resolution
```

## ✅ Supported Formats

**Input formats:**
- MP4, MKV, AVI, MOV, WMV, FLV
- Any format FFmpeg supports

**Output format:**
- Always MP4 (best compatibility)
- Optimized for:
  - Telegram uploads
  - WhatsApp sharing
  - Web streaming
  - Cloud storage

## 🔧 Troubleshooting

### Error: "FFmpeg not found"
**Solution:** Install FFmpeg
```bash
# Windows (using chocolatey):
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

### Error: "Failed to download video"
**Possible causes:**
- Video too large
- Network issue
- Bot doesn't have permission

**Solution:** Try a smaller video first

### Video quality too poor
**Solution:** Use better CRF value:
```python
crf=23,  # Instead of 28
```

### File still too large
**Solution:** Increase compression:
```python
crf=32,           # More compression
scale="iw/4:ih/4" # Smaller resolution
```

## 📁 File Locations

| File | Purpose |
|------|---------|
| `bot/modules/compress.py` | Main compress handler |
| `bot/modules/__init__.py` | Module registration |
| `bot/core/handlers.py` | Command registration |
| `fix_and_start.bat` | Quick start script |

## 🎯 Use Cases

Perfect for:
- 📱 **Telegram uploads** - Fits 2GB limit easily
- 💾 **Storage saving** - 70%+ reduction
- 🌐 **Fast sharing** - Smaller = faster upload
- 🎥 **Silent videos** - Remove unwanted audio
- 📺 **Screen recordings** - Clean professional output
- 🎬 **Preview clips** - Quick small versions

## 🔄 Workflow

```
User sends video → Bot downloads → FFmpeg compresses → Bot uploads
     ↓                  ↓                  ↓                ↓
  Reply with       Temp storage      Remove audio      Optimized MP4
  /compress                          Remove subs
                                     Reduce size
```

## 💪 Why This Implementation?

✅ **Simple to use** - Just reply with /compress  
✅ **Effective** - 70%+ file size reduction  
✅ **Fast** - veryfast preset for speed  
✅ **Compatible** - Works everywhere  
✅ **Clean** - No audio/subs clutter  
✅ **Optimized** - Fast streaming ready  

## 📞 Need Help?

If something doesn't work:
1. Check bot logs for errors
2. Verify FFmpeg is installed: `ffmpeg -version`
3. Try with a small test video first
4. Check if you have enough disk space

---

**Created:** 2025-12-14  
**Status:** ✅ Ready to use  
**Command:** `/compress` (reply to video)  
**Credits:** @TellYCloudBots
