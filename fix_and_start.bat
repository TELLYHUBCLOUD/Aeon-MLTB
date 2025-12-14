@echo off
cls
echo.
echo ============================================================
echo   VIDEO COMPRESSOR BOT - QUICK START
echo ============================================================  
echo.
echo  Features:
echo   - Removes ALL audio tracks
echo   - Removes ALL subtitles
echo   - Compresses to 50%% resolution
echo   - Reduces file size by 70%%+
echo   - Optimized for fast uploads
echo.
echo ============================================================
echo.

echo [1/5] Stopping running Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM python3.exe 2>nul
taskkill /F /IM py.exe 2>nul
timeout /t 2 >nul
echo   Done!
echo.

echo [2/5] Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo   Cache cleared!
echo.

echo [3/5] Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   [WARNING] FFmpeg not found!
    echo   Install from: https://ffmpeg.org/download.html
    echo   Or use: choco install ffmpeg
    echo.
    echo   Bot will start but /compress won't work without FFmpeg
    timeout /t 5
) else (
    echo   [OK] FFmpeg is installed!
)
echo.

echo [4/5] Verifying compress module...
if exist "bot\modules\compress.py" (
    echo   [OK] compress.py found
) else (
    echo   [ERROR] compress.py NOT found!
    pause
    exit /b 1
)
echo.

echo [5/5] Starting bot...
echo.
echo ============================================================
echo   BOT IS STARTING
echo ============================================================
echo.
echo  How to use:
echo   1. Send a video to your bot in Telegram
echo   2. Reply to the video with: /compress
echo   3. Wait for the magic!
echo.
echo  Press Ctrl+C to stop the bot
echo.
echo ------------------------------------------------------------
echo.

py -m bot

echo.
echo.
echo ============================================================
echo   BOT STOPPED
echo ============================================================
echo.
echo  To restart: Double-click fix_and_start.bat
echo.
pause
