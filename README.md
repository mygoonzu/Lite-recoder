# Lite recoder

Ung dung ghi am desktop cho Windows 11, viet bang Python, co giao dien nho gon, tray icon, va ho tro ghi `M4A`.

## Tong quan

Lite recoder huong toi nhu cau ghi hop nhanh:

- preset mac dinh `Hop`
- dinh dang mac dinh `M4A (AAC)`
- chat luong mac dinh `44.1 kHz / Mono / 128 kbps`
- tu dong tach file theo `180 MB`
- an vao tray khi minimize
- bat dau hoac dung ghi ngay tu menu chuot phai cua tray icon

## Tinh nang

- Giao dien desktop de chon nguon ghi, dinh dang, chat luong, thu muc luu.
- Ho tro `Microphone` va `System Audio` neu may Windows co loopback/WASAPI.
- Ho tro cac dinh dang:
  - `M4A (AAC)`
  - `AAC`
  - `MP3`
  - `WAV`
  - `FLAC`
  - `OGG Vorbis`
- Ho tro cac tuy chon chat luong:
  - `Sample rate`: `22.05 / 32 / 44.1 / 48 / 96 kHz`
  - `Kenh`: `Mono / Stereo`
  - `Bitrate`: `64 / 96 / 128 / 160 / 192 / 256 / 320 kbps`
- Co preset:
  - `Hop`
  - `Giong noi`
  - `Nhac`
  - `Tuy chinh`
- Tu dong tach file:
  - theo `dung luong`
  - hoac theo `thoi luong`
- Luu cau hinh vao `config.json`.
- Ho tro tray icon:
  - `Bat dau ghi`
  - `Dung ghi`
  - `Mo lai`
  - `Thoat`

## Mac dinh hien tai

- `Preset`: `Hop`
- `Dinh dang`: `M4A (AAC)`
- `Sample rate`: `44.1 kHz`
- `Kenh`: `Mono`
- `Bitrate`: `128 kbps`
- `Tach file`: `180 MB`

## Yeu cau

- Windows 11
- Python 3.11+
- `ffmpeg.exe`

## Cai dat

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Can co `ffmpeg.exe` bang mot trong hai cach:

- dat trong `PATH`
- hoac chon truc tiep trong giao dien qua truong `FFmpeg`

## Chay app

```bash
python app.py
```

## Tray icon

- Khi minimize, app se an vao `system tray`
- Khi dong cua so, app tiep tuc chay trong tray cho den khi chon `Thoat`
- Chuot phai vao tray icon de:
  - `Bat dau ghi`
  - `Dung ghi`
  - `Mo lai`
  - `Thoat`

## Dong goi EXE

### Cach 1: Python script

```bash
python build_exe.py
```

### Cach 2: Batch file

```bat
build_exe.bat
```

Sau khi build xong, file EXE nam trong:

```text
dist\Win11Recorder\
```

### Dung trong Visual Studio

1. Mo thu muc du an
2. Chon Python environment
3. Mo `build_exe.py`
4. Run file
5. Lay ban build trong `dist\Win11Recorder\`

## Cau truc file chinh

- `app.py`: giao dien desktop va tray icon
- `recorder.py`: engine ghi am va xoay file
- `config.json`: cau hinh mac dinh va cau hinh da luu
- `build_exe.py`: script dong goi bang Python
- `build_exe.bat`: script dong goi bang batch

## Luu y

- `System Audio` phu thuoc vao driver va WASAPI loopback cua may Windows.
- Ghi `M4A` duoc ma hoa thong qua `FFmpeg`.
- Nen build tren chinh may Windows 11 ma ban se su dung.
- Lan build dau tien can internet de cai package.

## License

MIT
