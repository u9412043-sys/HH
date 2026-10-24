@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python "pa_workflow.py"
) else (
  py -3 "pa_workflow.py"
)
pause
