@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo No existe .venv. Ejecuta primero install_windows.bat
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py
pause
