# Win11 Recorder

Ung dung ghi am desktop cho Windows 11, viet bang Python.

## Tinh nang

- Giao dien cau hinh truoc khi ghi.
- Ho tro nguon ghi `Microphone` va `System Audio` (loopback neu driver/Windows ho tro).
- Co the de trong `Dinh dang` va `Chat luong`; ung dung tu dung mac dinh:
  - `M4A (AAC)`
  - `44.1 kHz`
  - `Mono`
  - `128 kbps`
- Preset mac dinh khuyen dung la `Hop`:
  - `M4A (AAC)`
  - `44.1 kHz`
  - `Mono`
  - `128 kbps`
  - `Tach file theo dung luong 180 MB`
- Tuy chon dinh dang rong hon:
  - `M4A (AAC)`
  - `AAC`
  - `MP3`
  - `WAV`
  - `FLAC`
  - `OGG Vorbis`
- Tuy chon chat luong rong hon:
  - `Sample rate`: `22.05 / 32 / 44.1 / 48 / 96 kHz`
  - `Kenh`: `Mono / Stereo`
  - `Bitrate`: `64 / 96 / 128 / 160 / 192 / 256 / 320 kbps`
- Tu dong tach file khi vuot nguong:
  - theo thoi luong
  - hoac theo dung luong
- Tu dong tao file tiep theo ma khong can thao tac lai.

## Phu thuoc

- Python 3.11+
- `ffmpeg.exe` tren Windows
- Goi Python trong `requirements.txt`

## Cai dat

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Can tai `ffmpeg.exe` va:

- dat vao `PATH`, hoac
- chon truc tiep trong giao dien qua truong `FFmpeg`

## Chay

```bash
python app.py
```

## Cau hinh mac dinh

- App doc va ghi cau hinh tai `config.json` trong cung thu muc du an.
- Ban phat hanh hien tai mac dinh dung preset `Hop` va tach file `180 MB`.
- Khi ban thay doi tuy chon va bat dau ghi, app se luu lai de lan sau mo len van giu nguyen.

## Tray icon

- Khi thu nho cua so, app se an vao `system tray`
- Khi bam nut dong cua so, app van tiep tuc chay trong tray neu ban chua chon `Thoat`
- Bam chuot phai vao tray icon co cac muc:
  - `Bat dau ghi`
  - `Dung ghi`
  - `Mo lai`
  - `Thoat`
- Bam vao tray icon de mo lai cua so chinh

## Dong goi EXE

Co 2 cach dong goi tren Windows.

### Cach 1: chay bang Python

Neu ban dung Visual Studio, VS Code, hoac terminal Python:

```bash
python build_exe.py
```

Script se:

- cap nhat `pip`
- cai dependencies trong `requirements.txt`
- cai `PyInstaller`
- build file `.exe`

### Cach 2: chay bang batch file

Neu ban muon bam chay truc tiep:

```bat
build_exe.bat
```

Sau khi chay xong, file EXE se nam trong:

```text
dist\Win11Recorder\
```

### Cach mo trong Visual Studio

1. Mo thu muc du an `win11-recorder`
2. Chon Python environment phu hop
3. Mo file `build_exe.py`
4. Run file nay
5. Sau khi xong, lay file trong `dist\Win11Recorder\`

### Luu y

- Nen build tren chinh may Windows 11 ma ban se su dung
- Can co internet de cai package trong lan build dau tien
- Neu app ghi `m4a`, ban van can `ffmpeg.exe` tren may dich hoac cho phep nguoi dung tu chon duong dan `ffmpeg`

## Ghi chu

- Tinh nang `System Audio` phu thuoc vao WASAPI loopback tren may Windows. Neu khong thay thiet bi, hay cap nhat driver am thanh hoac dung Microphone.
- M4A duoc ma hoa qua FFmpeg. Trong moi file segment, app ghi lien tuc vao `ffmpeg` va xoay file khi dat nguong thoi gian hoac dung luong.
- Trong moi truong hien tai, GUI/FFmpeg khong co san, nen can thu tren Windows 11 de xac nhan thiet bi va encoder cu the.
