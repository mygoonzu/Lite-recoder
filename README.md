# Lite recoder

Ứng dụng ghi âm desktop cho Windows 11, viết bằng Python, có giao diện gọn, tray icon, và hỗ trợ ghi `M4A`.

## Tổng quan

Lite recoder hướng tới nhu cầu ghi họp nhanh:

- preset mặc định `Họp`
- định dạng mặc định `M4A (AAC)`
- chất lượng mặc định `44.1 kHz / Mono / 128 kbps`
- tự động tách file theo `180 MB`
- ẩn vào tray khi thu nhỏ
- bắt đầu hoặc dừng ghi ngay từ menu chuột phải của tray icon

## Tính năng

- Giao diện desktop để chọn nguồn ghi, định dạng, chất lượng, thư mục lưu.
- Hỗ trợ `Microphone` và `System Audio` nếu máy Windows có loopback/WASAPI.
- Hỗ trợ các định dạng:
  - `M4A (AAC)`
  - `AAC`
  - `MP3`
  - `WAV`
  - `FLAC`
  - `OGG Vorbis`
- Hỗ trợ các tùy chọn chất lượng:
  - `Sample rate`: `22.05 / 32 / 44.1 / 48 / 96 kHz`
  - `Kênh`: `Mono / Stereo`
  - `Bitrate`: `64 / 96 / 128 / 160 / 192 / 256 / 320 kbps`
- Có preset:
  - `Họp`
  - `Giọng nói`
  - `Nhạc`
  - `Tùy chỉnh`
- Tự động tách file:
  - theo `dung lượng`
  - hoặc theo `thời lượng`
- Lưu cấu hình vào `config.json`.
- Hỗ trợ tray icon:
  - `Bắt đầu ghi`
  - `Dừng ghi`
  - `Mở lại`
  - `Thoát`

## Mặc định hiện tại

- `Preset`: `Họp`
- `Định dạng`: `M4A (AAC)`
- `Sample rate`: `44.1 kHz`
- `Kênh`: `Mono`
- `Bitrate`: `128 kbps`
- `Tách file`: `180 MB`

## Yêu cầu

- Windows 11
- Python 3.11+
- `ffmpeg.exe`

## Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Cần có `ffmpeg.exe` bằng một trong hai cách:

- đặt trong `PATH`
- hoặc chọn trực tiếp trong giao diện qua trường `FFmpeg`

## Chạy ứng dụng

```bash
python app.py
```

## Tray icon

- Khi thu nhỏ, ứng dụng sẽ ẩn vào `system tray`
- Khi đóng cửa sổ, ứng dụng tiếp tục chạy trong tray cho đến khi chọn `Thoát`
- Chuột phải vào tray icon để:
  - `Bắt đầu ghi`
  - `Dừng ghi`
  - `Mở lại`
  - `Thoát`

## Đóng gói EXE

### Cách 1: Python script

```bash
python build_exe.py
```

### Cách 2: Batch file

```bat
build_exe.bat
```

Sau khi build xong, file EXE nằm trong:

```text
dist\Win11Recorder\
```

### Dùng trong Visual Studio

1. Mở thư mục dự án
2. Chọn Python environment
3. Mở `build_exe.py`
4. Run file
5. Lấy bản build trong `dist\Win11Recorder\`

## Cấu trúc file chính

- `app.py`: giao diện desktop và tray icon
- `recorder.py`: engine ghi âm và xoay file
- `config.json`: cấu hình mặc định và cấu hình đã lưu
- `build_exe.py`: script đóng gói bằng Python
- `build_exe.bat`: script đóng gói bằng batch

## Lưu ý

- `System Audio` phụ thuộc vào driver và WASAPI loopback của máy Windows.
- Ghi `M4A` được mã hóa thông qua `FFmpeg`.
- Nên build trên chính máy Windows 11 mà bạn sẽ sử dụng.
- Lần build đầu tiên cần internet để cài package.

## License

MIT
