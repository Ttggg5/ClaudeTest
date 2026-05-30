@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the app.
    echo.
    echo Make sure:
    echo  - Python is installed and in your PATH
    echo  - You have an API key in config.json
    echo  - VLC media player is installed
    echo.
    pause
)
