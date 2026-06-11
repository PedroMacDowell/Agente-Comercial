@echo off
setlocal
cd /d "%~dp0"

python -m PyInstaller --noconfirm --onefile --windowed --name AgenteIA launch_gui.py

pause

