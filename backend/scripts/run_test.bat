@echo off
"%~dp0..\venv\Scripts\python" -m pytest "%~dp0..\tests" -s
pause