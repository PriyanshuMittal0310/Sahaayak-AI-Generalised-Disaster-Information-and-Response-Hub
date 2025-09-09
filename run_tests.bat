@echo off
echo Installing test requirements...
pip install -r tests/requirements-test.txt

echo Running tests...
python -m pytest tests/ -v

pause
