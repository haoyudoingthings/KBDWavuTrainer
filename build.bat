@echo off
echo Building KBDWavuTrainer.exe ...
pyinstaller --onefile --windowed --name KBDWavuTrainer main.py
echo.
echo Done. Output: dist\KBDWavuTrainer.exe
pause
