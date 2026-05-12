@echo off
REM Launcher de blackjack21 para Windows.
REM Doble-clic abre la TUI; tambien acepta argumentos:
REM     programa.bat play --demo --seed 42
REM     programa.bat doctor

setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 "%~dp0programa.py" %*
) else (
    python "%~dp0programa.py" %*
)

if errorlevel 1 (
    echo.
    echo blackjack21 termino con error %errorlevel%.
    pause
)
endlocal
