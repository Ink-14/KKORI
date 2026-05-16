@echo off
cd /d %~dp0..
venv\Scripts\maturin build --release -o assets
venv\Scripts\pip install --force-reinstall assets\korean_spell_checker-0.1.0-cp38-abi3-win_amd64.whl
pause
