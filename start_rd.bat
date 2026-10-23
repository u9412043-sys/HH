@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python "rd_sweep.py" %*
) else (
  py -3 "rd_sweep.py" %*
)
pause
