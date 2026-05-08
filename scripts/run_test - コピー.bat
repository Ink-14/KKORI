@echo off
cd ../../
korean_spell_checker\venv\Scripts\python -m pytest korean_spell_checker/tests/test_spell_checker_engine.py -s
pause