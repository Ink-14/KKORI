@echo off
cd /d %~dp0..
venv\Scripts\pyinstaller korean_spell_checker.spec
pause
