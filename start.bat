@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python "idd_sweep.py" %*
) else (
  py -3 "idd_sweep.py" %*
)
echo.
pause
