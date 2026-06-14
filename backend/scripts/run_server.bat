@echo off
cd ..
venv\Scripts\uvicorn src.api:create_app --port 8765
pause