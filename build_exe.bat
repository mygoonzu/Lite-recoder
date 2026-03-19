@echo off
setlocal

if not exist .venv (
  py -m venv .venv
  if errorlevel 1 exit /b %errorlevel%
)

call .venv\Scripts\activate.bat
if errorlevel 1 exit /b %errorlevel%

python -m pip install --upgrade pip
if errorlevel 1 goto :build_failed

pip install -r requirements.txt
if errorlevel 1 goto :build_failed

pip install pyinstaller
if errorlevel 1 goto :build_failed

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name LiteRecorder ^
  --add-data "config.json;." ^
  app.py
if errorlevel 1 goto :build_failed

echo.
echo Build complete. EXE is in dist\LiteRecorder\
endlocal
exit /b 0

:build_failed
echo.
echo Build failed.
echo Make sure the app is closed and no file in dist\LiteRecorder is open in Explorer or another process.
endlocal
exit /b 1
