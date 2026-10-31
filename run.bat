@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your Python installation and internet connection.
  pause
  exit /b 1
)
%PY% app.py
if errorlevel 1 (
  echo GOFTA stopped with an error.
  pause
  exit /b 1
)
endlocal
