@echo off
cd /d "%~dp0"
echo Open http://127.0.0.1:8770/ in your browser.
echo Keep this window open while using the lesson. Ctrl+C stops the server.
python serve_site.py --directory . --port 8770
if errorlevel 1 pause
