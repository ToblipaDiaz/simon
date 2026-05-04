Set-Location -Path $PSScriptRoot
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "No existe .venv. Ejecuta primero install_windows.bat" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
