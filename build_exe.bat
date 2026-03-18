@echo off
setlocal

if not exist .venv (
  py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name Win11Recorder ^
  --add-data "config.json;." ^
  app.py

echo.
echo Build xong. File EXE nam trong thu muc dist\Win11Recorder\
endlocal
