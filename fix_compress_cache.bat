@echo off
echo ========================================
echo  Compress Command Fix Script
echo ========================================
echo.

echo Step 1: Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 >nul

echo Step 2: Clearing Python cache folders...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo Python cache cleared.

echo Step 3: Deleting .pyc files...
del /s /q *.pyc 2>nul
echo .pyc files deleted.

echo.
echo ========================================
echo  Cache Cleared Successfully!
echo ========================================
echo.
echo Now restart your bot with:
echo    python -m bot
echo.
echo Or if using a specific Python version:
echo    python3 -m bot
echo.
pause
