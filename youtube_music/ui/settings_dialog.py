from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QDialogButtonBox, QMessageBox,
)
from PyQt6.QtCore import Qt
import config as cfg


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("YouTube Music Player — Settings")
        header.setStyleSheet("font-size: 20px; font-weight: 600; color: #FF6B9D;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("AIza…")
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("YouTube Data API v3 key:", self._key_input)

        show_btn = QPushButton("Show / Hide")
        show_btn.setObjectName("iconBtn")
        show_btn.clicked.connect(self._toggle_echo)
        form.addRow("", show_btn)

        layout.addLayout(form)

        hint = QLabel(
            "Get a free API key at "
            "<a href='https://console.cloud.google.com/' style='color:#e63950;'>"
            'Google Cloud Console</a> → Enable "YouTube Data API v3".'
        )
        hint.setOpenExternalLinks(True)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6060a0; font-size: 11px;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self):
        conf = cfg.load_config()
        self._key_input.setText(conf.get("api_key", ""))

    def _toggle_echo(self):
        if self._key_input.echoMode() == QLineEdit.EchoMode.Password:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _save(self):
        key = self._key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Missing Key", "Please enter a YouTube Data API v3 key.")
            return
        conf = cfg.load_config()
        conf["api_key"] = key
        cfg.save_config(conf)
        self.accept()

    def get_key(self) -> str:
        return self._key_input.text().strip()
