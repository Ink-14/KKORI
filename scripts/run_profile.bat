@echo off
cd ../../
call korean_spell_checker\venv\Scripts\activate.bat
python -m korean_spell_checker.tests.test_spell_checker_engine
python -m pytest korean_spell_checker/tests -m perf -s
pause