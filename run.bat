@echo off
setlocal

cd /d "%~dp0"

:: Optional: set your Gemini API key here to enable AI outreach generation
:: set GEMINI_API_KEY=your-key-here

echo Starting SPARC local server...
python startup_shield_web\server.py 5174

pause
