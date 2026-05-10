@echo off
cd ../../
call korean_spell_checker\venv\Scripts\activate.bat
python -m korean_spell_checker.tests.test_spell_checker_engine
pause