@echo off
cd ..
call venv\Scripts\activate.bat
python -m pytest tests -m perf -s
pause