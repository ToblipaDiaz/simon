@echo off
setlocal
cd /d "%~dp0"

echo ======================================================
echo Instalador Windows - Proyecto Jorge Ambulatorio
echo ======================================================
echo.

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)

if not exist ".venv\Scripts\python.exe" (
    echo No se pudo crear el entorno virtual .venv
    echo Instala Python 3.11 o 3.12 desde https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Se creo .env desde .env.example. Editalo y pega tu OPENAI_API_KEY.
)

echo.
echo Instalacion terminada.
echo Ahora ejecuta run_windows.bat
echo.
pause
