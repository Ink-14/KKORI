@echo off
cd ../
call venv\scripts\activate
start "" venv\Scripts\python.exe scripts\quick_launcher.pyw
