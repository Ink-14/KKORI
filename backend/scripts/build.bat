@echo off
cd /d %~dp0..
..\venv\Scripts\maturin build --release -o assets
pause
