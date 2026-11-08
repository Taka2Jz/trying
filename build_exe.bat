@echo off
cd /d "%~dp0"
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt pyinstaller
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name "EmulatorHub" --collect-all PySide6 main.py
echo.
echo Build finished. EXE: dist\EmulatorHub.exe
pause
