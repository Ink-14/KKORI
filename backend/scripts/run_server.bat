@echo off
cd ..
venv\Scripts\uvicorn src.api:app --port 8765
pause