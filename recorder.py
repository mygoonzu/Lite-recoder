from __future__ import annotations

import os
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import soundcard as sc


DEFAULT_FORMAT = "m4a"
DEFAULT_SAMPLE_RATE = 44_100
DEFAULT_CHANNELS = 1
DEFAULT_BITRATE = "128k"
BLOCK_FRAMES = 2048


class RecorderError(RuntimeError):
    pass


@dataclass(slots=True)
class RecordingOptions:
    ffmpeg_path: str = "ffmpeg.exe"
    output_dir: str = ""
    filename_prefix: str = "Record"
    source_kind: str = "microphone"
    device_name: Optional[str] = None
    file_format: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bitrate: Optional[str] = None
    split_mode: str = "none"
    split_minutes: float = 120.0
    split_megabytes: float = 180.0

    @property
    def effective_format(self) -> str:
        return (self.file_format or DEFAULT_FORMAT).lower()

    @property
    def effective_sample_rate(self) -> int:
        return self.sample_rate or DEFAULT_SAMPLE_RATE

    @property
    def effective_channels(self) -> int:
        return self.channels or DEFAULT_CHANNELS

    @property
    def effective_bitrate(self) -> str:
        return self.bitrate or DEFAULT_BITRATE

    @property
    def split_seconds(self) -> float:
        return max(self.split_minutes, 0) * 60.0

    @property
    def split_bytes(self) -> int:
        return int(max(self.split_megabytes, 0) * 1024 * 1024)


def list_input_devices(source_kind: str) -> list[str]:
    devices = sc.all_microphones(include_loopback=True)
    names: list[str] = []
    for device in devices:
        name = str(device)
        is_loopback = bool(getattr(device, "isloopback", False)) or "loopback" in name.lower()
        if source_kind == "system" and is_loopback:
            names.append(name)
        if source_kind == "microphone" and not is_loopback:
            names.append(name)
    return sorted(set(names))


class AudioRecorder:
    def __init__(self, status_callback: Optional[Callable[[str], None]] = None) -> None:
        self._status_callback = status_callback or (lambda _message: None)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._options: Optional[RecordingOptions] = None
        self._active_process: Optional[subprocess.Popen[bytes]] = None
        self._active_path: Optional[Path] = None
        self._segment_started_at = 0.0
        self._segment_index = 0
        self._message_queue: queue.Queue[str] = queue.Queue()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, options: RecordingOptions) -> None:
        if self.is_running():
            raise RecorderError("Dang ghi am.")
        self._validate_options(options)
        self._options = options
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._record_loop, name="audio-recorder", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        self._thread = None

    def _emit(self, message: str) -> None:
        self._message_queue.put(message)
        self._status_callback(message)

    def _validate_options(self, options: RecordingOptions) -> None:
        if not options.output_dir:
            raise RecorderError("Chua chon thu muc luu.")
        output_dir = Path(options.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        ffmpeg_path = options.ffmpeg_path.strip() or "ffmpeg.exe"
        if os.path.sep in ffmpeg_path or "/" in ffmpeg_path:
            if not Path(ffmpeg_path).exists():
                raise RecorderError("Khong tim thay ffmpeg.exe.")

        if options.split_mode == "time" and options.split_seconds <= 0:
            raise RecorderError("Thoi luong tach file phai lon hon 0.")
        if options.split_mode == "size" and options.split_bytes <= 0:
            raise RecorderError("Dung luong tach file phai lon hon 0.")

    def _record_loop(self) -> None:
        assert self._options is not None
        options = self._options
        recorder = None
        try:
            microphone = self._resolve_microphone(options)
            self._emit(f"Su dung thiet bi: {microphone}")
            recorder = microphone.recorder(
                samplerate=options.effective_sample_rate,
                channels=options.effective_channels,
                blocksize=BLOCK_FRAMES,
            )
            with recorder:
                self._open_new_segment()
                while not self._stop_event.is_set():
                    data = recorder.record(numframes=BLOCK_FRAMES)
                    pcm = self._to_pcm16(data, options.effective_channels)
                    if self._should_rotate():
                        self._rotate_segment()
                    self._write_audio(pcm)
        except Exception as exc:  # noqa: BLE001
            self._emit(f"Loi ghi am: {exc}")
        finally:
            self._close_active_process()
            self._emit("Da dung ghi am.")

    def _resolve_microphone(self, options: RecordingOptions):
        devices = sc.all_microphones(include_loopback=True)
        if options.device_name:
            for device in devices:
                if str(device) == options.device_name:
                    return device
            raise RecorderError("Khong tim thay thiet bi duoc chon.")

        if options.source_kind == "system":
            for device in devices:
                name = str(device)
                is_loopback = bool(getattr(device, "isloopback", False)) or "loopback" in name.lower()
                if is_loopback:
                    return device
            raise RecorderError("Khong tim thay thiet bi System Audio loopback.")

        return sc.default_microphone()

    def _segment_path(self) -> Path:
        assert self._options is not None
        output_dir = Path(self._options.output_dir)
        extension = self._options.effective_format
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        index = f"{self._segment_index:03d}"
        return output_dir / f"{self._options.filename_prefix}_{timestamp}_{index}.{extension}"

    def _open_new_segment(self) -> None:
        assert self._options is not None
        self._segment_index += 1
        self._active_path = self._segment_path()
        command = self._build_ffmpeg_command(self._active_path)
        self._active_process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._segment_started_at = time.monotonic()
        self._emit(f"Bat dau file: {self._active_path.name}")

    def _build_ffmpeg_command(self, output_path: Path) -> list[str]:
        assert self._options is not None
        options = self._options
        command = [
            options.ffmpeg_path.strip() or "ffmpeg.exe",
            "-y",
            "-f",
            "s16le",
            "-ar",
            str(options.effective_sample_rate),
            "-ac",
            str(options.effective_channels),
            "-i",
            "pipe:0",
        ]

        fmt = options.effective_format
        if fmt == "m4a":
            command += ["-c:a", "aac", "-b:a", options.effective_bitrate]
        elif fmt == "aac":
            command += ["-c:a", "aac", "-b:a", options.effective_bitrate, "-f", "adts"]
        elif fmt == "mp3":
            command += ["-c:a", "libmp3lame", "-b:a", options.effective_bitrate]
        elif fmt == "wav":
            command += ["-c:a", "pcm_s16le"]
        elif fmt == "flac":
            command += ["-c:a", "flac"]
        elif fmt == "ogg":
            command += ["-c:a", "libvorbis", "-b:a", options.effective_bitrate]
        else:
            raise RecorderError(f"Dinh dang khong duoc ho tro: {fmt}")

        command.append(str(output_path))
        return command

    def _to_pcm16(self, data: np.ndarray, channels: int) -> bytes:
        normalized = np.asarray(data, dtype=np.float32)
        if normalized.ndim == 1:
            normalized = normalized[:, np.newaxis]
        if normalized.shape[1] != channels:
            normalized = normalized[:, :channels]
        clipped = np.clip(normalized, -1.0, 1.0)
        pcm = (clipped * 32767.0).astype(np.int16)
        return pcm.tobytes()

    def _write_audio(self, pcm_bytes: bytes) -> None:
        if not self._active_process or not self._active_process.stdin:
            raise RecorderError("Tien trinh ffmpeg khong san sang.")
        self._active_process.stdin.write(pcm_bytes)

    def _should_rotate(self) -> bool:
        assert self._options is not None
        if self._options.split_mode == "time":
            return (time.monotonic() - self._segment_started_at) >= self._options.split_seconds
        if self._options.split_mode == "size" and self._active_path and self._active_path.exists():
            return self._active_path.stat().st_size >= self._options.split_bytes
        return False

    def _rotate_segment(self) -> None:
        self._close_active_process()
        if not self._stop_event.is_set():
            self._open_new_segment()

    def _close_active_process(self) -> None:
        process = self._active_process
        self._active_process = None
        if process is None:
            return
        try:
            if process.stdin:
                process.stdin.flush()
                process.stdin.close()
            process.wait(timeout=10)
        except Exception:  # noqa: BLE001
            process.kill()
        finally:
            self._active_path = None
