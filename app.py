from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QStandardPaths, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QRadioButton,
    QMenu,
    QSpinBox,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from recorder import AudioRecorder, RecordingOptions, list_input_devices


FORMAT_OPTIONS = [
    ("Default (M4A)", ""),
    ("M4A (AAC)", "m4a"),
    ("AAC", "aac"),
    ("MP3", "mp3"),
    ("WAV", "wav"),
    ("FLAC", "flac"),
    ("OGG Vorbis", "ogg"),
]

SAMPLE_RATE_OPTIONS = [
    ("Default (44.1 kHz)", ""),
    ("22.05 kHz", "22050"),
    ("32 kHz", "32000"),
    ("44.1 kHz", "44100"),
    ("48 kHz", "48000"),
    ("96 kHz", "96000"),
]

CHANNEL_OPTIONS = [
    ("Default (Mono)", ""),
    ("Mono", "1"),
    ("Stereo", "2"),
]

BITRATE_OPTIONS = [
    ("Default (128 kbps)", ""),
    ("64 kbps", "64k"),
    ("96 kbps", "96k"),
    ("128 kbps", "128k"),
    ("160 kbps", "160k"),
    ("192 kbps", "192k"),
    ("256 kbps", "256k"),
    ("320 kbps", "320k"),
]

PRESET_OPTIONS = [
    ("Meeting (Recommended)", "meeting"),
    ("Voice", "voice"),
    ("Music", "music"),
    ("Custom", "custom"),
]

DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")


def user_config_path() -> Path:
    config_root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    if config_root:
        return Path(config_root) / "config.json"
    return Path.home() / ".litle-recoder" / "config.json"

FORMAT_HINTS = {
    "": {
        "sample_rates": {"22050", "32000", "44100", "48000", "96000"},
        "channels": {"1", "2"},
        "bitrates": {"64k", "96k", "128k", "160k", "192k", "256k", "320k"},
        "hint": "Default uses M4A (AAC), 44.1 kHz, Mono, 128 kbps.",
    },
    "m4a": {
        "sample_rates": {"32000", "44100", "48000"},
        "channels": {"1", "2"},
        "bitrates": {"96k", "128k", "160k", "192k", "256k"},
        "hint": "M4A (AAC) is a good default for everyday recording with balanced quality and size.",
    },
    "aac": {
        "sample_rates": {"32000", "44100", "48000"},
        "channels": {"1", "2"},
        "bitrates": {"96k", "128k", "160k", "192k", "256k"},
        "hint": "AAC keeps files compact with good quality; 128-192 kbps is typical.",
    },
    "mp3": {
        "sample_rates": {"32000", "44100", "48000"},
        "channels": {"1", "2"},
        "bitrates": {"96k", "128k", "160k", "192k", "256k", "320k"},
        "hint": "MP3 is broadly compatible; 128 kbps works for voice, 192 kbps or higher for music.",
    },
    "wav": {
        "sample_rates": {"22050", "32000", "44100", "48000", "96000"},
        "channels": {"1", "2"},
        "bitrates": set(),
        "hint": "WAV does not use bitrate; files are larger but easier for editing workflows.",
    },
    "flac": {
        "sample_rates": {"22050", "32000", "44100", "48000", "96000"},
        "channels": {"1", "2"},
        "bitrates": set(),
        "hint": "FLAC is lossless; bitrate does not apply.",
    },
    "ogg": {
        "sample_rates": {"32000", "44100", "48000"},
        "channels": {"1", "2"},
        "bitrates": {"96k", "128k", "160k", "192k", "256k"},
        "hint": "OGG Vorbis is suitable for smaller files; 128-192 kbps is typical.",
    },
}


class LogBridge(QObject):
    message = Signal(str)
    recording_state_changed = Signal(bool)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lite Recorder")
        self.resize(820, 560)

        self.log_bridge = LogBridge()
        self.log_bridge.message.connect(self.append_log)
        self.log_bridge.recording_state_changed.connect(self.set_recording_state)
        self.recorder = AudioRecorder(
            status_callback=self.log_bridge.message.emit,
            state_callback=self.log_bridge.recording_state_changed.emit,
        )

        self.ffmpeg_path_input = QLineEdit("ffmpeg.exe")
        self.output_dir_input = QLineEdit(str(Path.home() / "Recordings"))
        self.filename_prefix_input = QLineEdit("Record")
        self.ffmpeg_path_input.setPlaceholderText("ffmpeg.exe or full path to ffmpeg.exe")
        self.output_dir_input.setPlaceholderText("Folder to save recordings")
        self.filename_prefix_input.setPlaceholderText("Example: Meeting")

        self.microphone_radio = QRadioButton("Microphone")
        self.system_radio = QRadioButton("System Audio")
        self.microphone_radio.setChecked(True)

        self.device_combo = QComboBox()
        self.preset_combo = self._build_combo(PRESET_OPTIONS)
        self.format_combo = self._build_combo(FORMAT_OPTIONS)
        self.sample_rate_combo = self._build_combo(SAMPLE_RATE_OPTIONS)
        self.channels_combo = self._build_combo(CHANNEL_OPTIONS)
        self.bitrate_combo = self._build_combo(BITRATE_OPTIONS)
        self.format_hint_label = QLabel()
        self.format_hint_label.setWordWrap(True)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("padding: 8px; background: #f3f6f8; border: 1px solid #d7dee3;")

        self.no_split_radio = QRadioButton("No split")
        self.time_split_radio = QRadioButton("By duration")
        self.size_split_radio = QRadioButton("By size")
        self.no_split_radio.setChecked(True)

        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 24 * 60)
        self.time_spin.setValue(120)
        self.time_spin.setSuffix(" min")

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 10_240)
        self.size_spin.setValue(180)
        self.size_spin.setSuffix(" MB")

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.start_button.setMinimumWidth(120)
        self.stop_button.setMinimumWidth(120)
        self._is_quitting = False
        self.tray_icon: QSystemTrayIcon | None = None

        self.log_file_path = user_config_path().with_name("LiteRecorder.log")
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_view.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.log_view.setMaximumHeight(170)
        self.log_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.copy_log_action = self.log_view.addAction("Copy")
        self.copy_log_action.triggered.connect(self.log_view.copy)
        self.select_all_log_action = self.log_view.addAction("Select All")
        self.select_all_log_action.triggered.connect(self.log_view.selectAll)

        self._build_ui()
        self._wire_events()
        self._setup_tray()
        self.refresh_devices()
        self.load_config()

    def _build_combo(self, options: list[tuple[str, str]]) -> QComboBox:
        combo = QComboBox()
        for label, value in options:
            combo.addItem(label, value)
        return combo

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        intro = QLabel("Quick setup for meeting recordings. If unchanged, the app uses the Meeting preset and splits files at 180 MB.")
        intro.setWordWrap(True)

        config_group = QGroupBox("Recording Settings")
        config_layout = QGridLayout(config_group)
        config_layout.setHorizontalSpacing(12)
        config_layout.setVerticalSpacing(10)

        paths_group = QGroupBox("Paths")
        paths_layout = QFormLayout(paths_group)
        paths_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        ffmpeg_row = self._with_browse(self.ffmpeg_path_input, self.pick_ffmpeg)
        output_row = self._with_browse(self.output_dir_input, self.pick_output_dir)
        paths_layout.addRow("FFmpeg", ffmpeg_row)
        paths_layout.addRow("Output folder", output_row)
        paths_layout.addRow("Filename prefix", self.filename_prefix_input)

        source_group = QGroupBox("Input Source")
        source_layout = QFormLayout(source_group)
        source_choice = QWidget()
        source_choice_layout = QHBoxLayout(source_choice)
        source_choice_layout.setContentsMargins(0, 0, 0, 0)
        source_choice_layout.addWidget(self.microphone_radio)
        source_choice_layout.addWidget(self.system_radio)
        source_layout.addRow("Source type", source_choice)
        source_layout.addRow("Device", self.device_combo)

        quality_group = QGroupBox("Format and Quality")
        quality_layout = QFormLayout(quality_group)
        quality_layout.addRow("Preset", self.preset_combo)
        quality_layout.addRow("Format", self.format_combo)
        quality_layout.addRow("Sample rate", self.sample_rate_combo)
        quality_layout.addRow("Channels", self.channels_combo)
        quality_layout.addRow("Bitrate", self.bitrate_combo)
        quality_layout.addRow("Hint", self.format_hint_label)
        note = QLabel("If left unchanged, the app uses M4A / 44.1 kHz / Mono / 128 kbps.")
        note.setWordWrap(True)
        quality_layout.addRow("", note)

        split_group = QGroupBox("File Splitting")
        split_layout = QFormLayout(split_group)
        split_choice = QWidget()
        split_choice_layout = QHBoxLayout(split_choice)
        split_choice_layout.setContentsMargins(0, 0, 0, 0)
        split_choice_layout.addWidget(self.no_split_radio)
        split_choice_layout.addWidget(self.time_split_radio)
        split_choice_layout.addWidget(self.size_split_radio)
        split_layout.addRow("Mode", split_choice)
        split_layout.addRow("Duration", self.time_spin)
        split_layout.addRow("Size", self.size_spin)

        config_layout.addWidget(paths_group, 0, 0)
        config_layout.addWidget(source_group, 0, 1)
        config_layout.addWidget(quality_group, 1, 0)
        config_layout.addWidget(split_group, 1, 1)
        config_layout.setColumnStretch(0, 1)
        config_layout.setColumnStretch(1, 1)

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addStretch()

        root.addWidget(intro)
        root.addWidget(self.summary_label)
        root.addWidget(config_group)
        root.addWidget(buttons)
        root.addWidget(QLabel("Log"))
        root.addWidget(self.log_view, stretch=1)
        self.setCentralWidget(central)

    def _wire_events(self) -> None:
        self.microphone_radio.toggled.connect(self.refresh_devices)
        self.system_radio.toggled.connect(self.refresh_devices)
        self.no_split_radio.toggled.connect(self._update_split_inputs)
        self.time_split_radio.toggled.connect(self._update_split_inputs)
        self.size_split_radio.toggled.connect(self._update_split_inputs)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)
        self.format_combo.currentIndexChanged.connect(self.update_format_guidance)
        self.preset_combo.currentIndexChanged.connect(self.update_summary)
        self.device_combo.currentIndexChanged.connect(self.update_summary)
        self.sample_rate_combo.currentIndexChanged.connect(self.update_summary)
        self.channels_combo.currentIndexChanged.connect(self.update_summary)
        self.bitrate_combo.currentIndexChanged.connect(self.update_summary)
        self.time_spin.valueChanged.connect(self.update_summary)
        self.size_spin.valueChanged.connect(self.update_summary)
        self.microphone_radio.toggled.connect(self.update_summary)
        self.system_radio.toggled.connect(self.update_summary)
        self.no_split_radio.toggled.connect(self.update_summary)
        self.time_split_radio.toggled.connect(self.update_summary)
        self.size_split_radio.toggled.connect(self.update_summary)
        QApplication.instance().aboutToQuit.connect(self._mark_quitting)

    def _with_browse(self, line_edit: QLineEdit, picker) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        button = QPushButton("Browse...")
        button.clicked.connect(picker)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return wrapper

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        tray_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.tray_icon = QSystemTrayIcon(tray_icon, self)
        self.tray_icon.setToolTip("Lite Recorder")

        menu = QMenu(self)
        self.tray_start_action = menu.addAction("Start Recording")
        self.tray_stop_action = menu.addAction("Stop Recording")
        menu.addSeparator()
        self.tray_show_action = menu.addAction("Restore")
        menu.addSeparator()
        self.tray_quit_action = menu.addAction("Quit")

        self.tray_start_action.triggered.connect(self.start_recording)
        self.tray_stop_action.triggered.connect(self.stop_recording)
        self.tray_show_action.triggered.connect(self.restore_from_tray)
        self.tray_quit_action.triggered.connect(self.quit_application)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setContextMenu(menu)
        self._update_tray_actions()
        self.tray_icon.show()

    def pick_ffmpeg(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ffmpeg.exe",
            self.ffmpeg_path_input.text().strip() or "",
            "Executable (*.exe);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self.ffmpeg_path_input.setText(path)

    def pick_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
            self.output_dir_input.text().strip() or str(Path.home()),
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self.output_dir_input.setText(path)

    def current_source_kind(self) -> str:
        return "system" if self.system_radio.isChecked() else "microphone"

    def refresh_devices(self) -> None:
        self.device_combo.clear()
        try:
            devices = list_input_devices(self.current_source_kind())
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"Could not load input devices: {exc}")
            devices = []
        self.device_combo.addItem("Default", "")
        for device in devices:
            self.device_combo.addItem(device, device)

    def _update_split_inputs(self) -> None:
        self.time_spin.setEnabled(self.time_split_radio.isChecked())
        self.size_spin.setEnabled(self.size_split_radio.isChecked())
        self.update_summary()

    def update_format_guidance(self) -> None:
        fmt = self.format_combo.currentData() or ""
        spec = FORMAT_HINTS[fmt]
        self._apply_combo_filter(self.sample_rate_combo, SAMPLE_RATE_OPTIONS, spec["sample_rates"])
        self._apply_combo_filter(self.channels_combo, CHANNEL_OPTIONS, spec["channels"])
        self._apply_combo_filter(self.bitrate_combo, BITRATE_OPTIONS, spec["bitrates"])
        self.bitrate_combo.setEnabled(bool(spec["bitrates"]))
        self.format_hint_label.setText(spec["hint"])
        self.update_summary()

    def _apply_combo_filter(
        self,
        combo: QComboBox,
        all_options: list[tuple[str, str]],
        allowed_values: set[str],
    ) -> None:
        current_value = combo.currentData() or ""
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(all_options[0][0], all_options[0][1])
        for label, value in all_options[1:]:
            if value in allowed_values:
                combo.addItem(label, value)
        match_index = combo.findData(current_value)
        combo.setCurrentIndex(match_index if match_index >= 0 else 0)
        combo.blockSignals(False)

    def apply_preset(self) -> None:
        preset = self.preset_combo.currentData() or "meeting"
        if preset == "custom":
            self.update_format_guidance()
            self.update_summary()
            return

        mapping = {
            "meeting": {
                "format": "m4a",
                "sample_rate": "44100",
                "channels": "1",
                "bitrate": "128k",
                "split_mode": "size",
                "split_value": 180,
            },
            "voice": {
                "format": "m4a",
                "sample_rate": "32000",
                "channels": "1",
                "bitrate": "96k",
                "split_mode": "none",
                "split_value": 180,
            },
            "music": {
                "format": "m4a",
                "sample_rate": "48000",
                "channels": "2",
                "bitrate": "192k",
                "split_mode": "none",
                "split_value": 180,
            },
        }[preset]

        self._set_combo_data(self.format_combo, mapping["format"])
        self.update_format_guidance()
        self._set_combo_data(self.sample_rate_combo, mapping["sample_rate"])
        self._set_combo_data(self.channels_combo, mapping["channels"])
        self._set_combo_data(self.bitrate_combo, mapping["bitrate"])
        self._apply_split_preset(mapping["split_mode"], mapping["split_value"])
        self.update_summary()

    def _set_combo_data(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _apply_split_preset(self, mode: str, value: int) -> None:
        if mode == "size":
            self.size_split_radio.setChecked(True)
            self.size_spin.setValue(value)
        elif mode == "time":
            self.time_split_radio.setChecked(True)
            self.time_spin.setValue(value)
        else:
            self.no_split_radio.setChecked(True)
        self._update_split_inputs()

    def load_config(self) -> None:
        data: dict[str, object] = {}
        for config_path in (user_config_path(), DEFAULT_CONFIG_PATH):
            if not config_path.exists():
                continue
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                break
            except Exception:  # noqa: BLE001
                data = {}

        preset = str(data.get("preset", "meeting"))
        self._set_combo_data(self.preset_combo, preset)
        self.apply_preset()

        self.ffmpeg_path_input.setText(str(data.get("ffmpeg_path", self.ffmpeg_path_input.text())))
        self.output_dir_input.setText(str(data.get("output_dir", self.output_dir_input.text())))
        self.filename_prefix_input.setText(str(data.get("filename_prefix", self.filename_prefix_input.text())))

        source_kind = str(data.get("source_kind", "microphone"))
        self.system_radio.setChecked(source_kind == "system")
        self.microphone_radio.setChecked(source_kind != "system")
        self.refresh_devices()

        device_name = data.get("device_name")
        if isinstance(device_name, str) and device_name:
            self._set_combo_data(self.device_combo, device_name)

        if preset == "custom":
            self._set_combo_data(self.format_combo, str(data.get("file_format", "")))
            self.update_format_guidance()
            sample_rate = data.get("sample_rate")
            channels = data.get("channels")
            bitrate = data.get("bitrate")
            self._set_combo_data(self.sample_rate_combo, str(sample_rate) if sample_rate else "")
            self._set_combo_data(self.channels_combo, str(channels) if channels else "")
            self._set_combo_data(self.bitrate_combo, str(bitrate) if bitrate else "")

        split_mode = str(data.get("split_mode", "size" if preset == "meeting" else "none"))
        split_value = int(data.get("split_megabytes", 180))
        if split_mode == "time":
            split_value = int(data.get("split_minutes", 120))
        self._apply_split_preset(split_mode, split_value)
        self.update_format_guidance()

    def save_config(self) -> None:
        options = self.build_options()
        data = {
            "preset": self.preset_combo.currentData() or "meeting",
            "ffmpeg_path": self.ffmpeg_path_input.text().strip() or "ffmpeg.exe",
            "output_dir": self.output_dir_input.text().strip(),
            "filename_prefix": self.filename_prefix_input.text().strip() or "Record",
            "source_kind": self.current_source_kind(),
            "device_name": self.device_combo.currentData() or None,
            "file_format": options.file_format,
            "sample_rate": options.sample_rate,
            "channels": options.channels,
            "bitrate": options.bitrate,
            "split_mode": options.split_mode,
            "split_minutes": int(self.time_spin.value()),
            "split_megabytes": int(self.size_spin.value()),
        }
        config_path = user_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def update_summary(self) -> None:
        preset_text = self.preset_combo.currentText()
        source_text = "System Audio" if self.system_radio.isChecked() else "Microphone"
        format_text = self.format_combo.currentText()
        sample_rate_text = self.sample_rate_combo.currentText()
        channel_text = self.channels_combo.currentText()
        bitrate_text = self.bitrate_combo.currentText() if self.bitrate_combo.isEnabled() else "Not applicable"

        if self.size_split_radio.isChecked():
            split_text = f"Split by size at {self.size_spin.value()} MB"
        elif self.time_split_radio.isChecked():
            split_text = f"Split by duration every {self.time_spin.value()} min"
        else:
            split_text = "No file splitting"

        self.summary_label.setText(
            f"Summary: {preset_text} | {source_text} | {format_text} | "
            f"{sample_rate_text} | {channel_text} | {bitrate_text} | {split_text}"
        )

    def _update_tray_actions(self) -> None:
        if self.tray_icon is None:
            return
        is_running = self.recorder.is_running()
        self.tray_start_action.setEnabled(not is_running)
        self.tray_stop_action.setEnabled(is_running)

    def restore_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.restore_from_tray()

    def quit_application(self) -> None:
        self._is_quitting = True
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self.close()

    def _mark_quitting(self) -> None:
        self._is_quitting = True

    def set_recording_state(self, is_running: bool) -> None:
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self._update_tray_actions()

    def build_options(self) -> RecordingOptions:
        split_mode = "none"
        if self.time_split_radio.isChecked():
            split_mode = "time"
        if self.size_split_radio.isChecked():
            split_mode = "size"

        return RecordingOptions(
            ffmpeg_path=self.ffmpeg_path_input.text().strip() or "ffmpeg.exe",
            output_dir=self.output_dir_input.text().strip(),
            filename_prefix=self.filename_prefix_input.text().strip() or "Record",
            source_kind=self.current_source_kind(),
            device_name=self.device_combo.currentData() or None,
            file_format=self.format_combo.currentData() or None,
            sample_rate=int(self.sample_rate_combo.currentData()) if self.sample_rate_combo.currentData() else None,
            channels=int(self.channels_combo.currentData()) if self.channels_combo.currentData() else None,
            bitrate=self.bitrate_combo.currentData() or None,
            split_mode=split_mode,
            split_minutes=float(self.time_spin.value()),
            split_megabytes=float(self.size_spin.value()),
        )

    def start_recording(self) -> None:
        try:
            options = self.build_options()
            self.save_config()
            self.recorder.start(options)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Unable to Start Recording", str(exc))
            return

        self.append_log("Recording started.")

    def stop_recording(self) -> None:
        self.recorder.stop()

    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._write_log_file(message)

    def _write_log_file(self, message: str) -> None:
        try:
            with self.log_file_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(message + "\n")
        except Exception as exc:  # noqa: BLE001
            self.log_view.appendPlainText(f"Failed to write log file: {exc}")

    def changeEvent(self, event) -> None:  # noqa: N802
        if event.type() == event.Type.WindowStateChange and self.isMinimized() and self.tray_icon is not None:
            self.hide()
            self.tray_icon.showMessage(
                "Lite Recorder",
                "The app is hidden in the tray. Right-click the tray icon to start or stop recording.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        super().changeEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        if not self._is_quitting and self.tray_icon is not None:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Lite Recorder",
                "The app is still running in the tray.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )
            return
        try:
            self.save_config()
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"Could not save config: {exc}")
        if self.recorder.is_running():
            self.recorder.stop()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        super().closeEvent(event)


def main() -> int:
    QApplication.setOrganizationName("mygoonzu")
    QApplication.setApplicationName("Lite Recorder")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
