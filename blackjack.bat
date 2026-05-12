@echo off
REM Launcher de blackjack21 para Windows.
REM Doble-clic abre la TUI; tambien acepta argumentos:
REM     blackjack.bat play --demo --seed 42
REM     blackjack.bat doctor

setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 "%~dp0blackjack.py" %*
) else (
    python "%~dp0blackjack.py" %*
)

if errorlevel 1 (
    echo.
    echo blackjack21 termino con error %errorlevel%.
    pause
)
endlocal
