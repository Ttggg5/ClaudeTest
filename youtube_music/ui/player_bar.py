import requests
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap

from core.api import format_duration


class _ThumbSignals(QObject):
    loaded = pyqtSignal(QPixmap)


class _ThumbLoader(QRunnable):
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals = _ThumbSignals()

    def run(self):
        try:
            data = requests.get(self.url, timeout=8).content
            px = QPixmap()
            px.loadFromData(data)
            if not px.isNull():
                self.signals.loaded.emit(px.scaled(
                    56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            pass


class PlayerBar(QFrame):
    play_pause = pyqtSignal()
    next_track = pyqtSignal()
    prev_track = pyqtSignal()
    seek = pyqtSignal(int)          # seconds
    volume_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playerBar")
        self.setFixedHeight(150)
        self._is_seeking = False
        self._duration = 0
        self._pool = QThreadPool.globalInstance()
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(12)

        # ── top row: thumbnail + info + controls ────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(16)

        # thumbnail
        self._thumb = QLabel()
        self._thumb.setFixedSize(64, 64)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            "background:#2a2a46; border-radius:12px; color:#6060a0; font-size:24px;"
        )
        self._thumb.setText("♪")
        top.addWidget(self._thumb)

        # title + artist
        info = QVBoxLayout()
        info.setSpacing(4)
        self._title_lbl = QLabel("Not playing")
        self._title_lbl.setObjectName("nowTitle")
        self._title_lbl.setMaximumWidth(280)
        info.addWidget(self._title_lbl)
        self._artist_lbl = QLabel("")
        self._artist_lbl.setObjectName("nowArtist")
        info.addWidget(self._artist_lbl)
        top.addLayout(info, stretch=1)

        # controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self._prev_btn = QPushButton("⏮")
        self._prev_btn.setObjectName("iconBtn")
        self._prev_btn.setFixedSize(48, 48)
        self._prev_btn.clicked.connect(self.prev_track)
        ctrl.addWidget(self._prev_btn)

        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("playBtn")
        self._play_btn.clicked.connect(self.play_pause)
        ctrl.addWidget(self._play_btn)

        self._next_btn = QPushButton("⏭")
        self._next_btn.setObjectName("iconBtn")
        self._next_btn.setFixedSize(48, 48)
        self._next_btn.clicked.connect(self.next_track)
        ctrl.addWidget(self._next_btn)

        top.addLayout(ctrl)

        # volume
        vol_layout = QHBoxLayout()
        vol_layout.setSpacing(8)
        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet("font-size: 16px;")
        vol_layout.addWidget(vol_icon)

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(70)
        self._vol_slider.setFixedWidth(100)
        self._vol_slider.valueChanged.connect(self.volume_changed)
        vol_layout.addWidget(self._vol_slider)

        top.addLayout(vol_layout)
        outer.addLayout(top)

        # ── bottom row: time + seek bar ────────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        self._pos_lbl = QLabel("0:00")
        self._pos_lbl.setObjectName("timeLabel")
        self._pos_lbl.setFixedWidth(40)
        bottom.addWidget(self._pos_lbl)

        self._seek = QSlider(Qt.Orientation.Horizontal)
        self._seek.setRange(0, 0)
        self._seek.sliderPressed.connect(self._start_seek)
        self._seek.sliderReleased.connect(self._end_seek)
        bottom.addWidget(self._seek, stretch=1)

        self._dur_lbl = QLabel("0:00")
        self._dur_lbl.setObjectName("timeLabel")
        self._dur_lbl.setFixedWidth(40)
        self._dur_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        bottom.addWidget(self._dur_lbl)

        outer.addLayout(bottom)

    # ------------------------------------------------------------------ public

    def set_track(self, track: dict | None):
        if not track:
            self._title_lbl.setText("Not playing")
            self._artist_lbl.setText("")
            self._thumb.setPixmap(QPixmap())
            self._thumb.setText("♪")
            return

        self._title_lbl.setText(track["title"])
        self._artist_lbl.setText(track["channel"])
        self._thumb.setText("♪")
        self._thumb.setPixmap(QPixmap())

        if track.get("thumbnail_url"):
            loader = _ThumbLoader(track["thumbnail_url"])
            loader.signals.loaded.connect(self._set_thumb)
            self._pool.start(loader)

    def set_state(self, state: str):
        if state == "playing":
            self._play_btn.setText("⏸")
        elif state == "loading":
            self._play_btn.setText("⏳")
        else:
            self._play_btn.setText("▶")

    def set_position(self, seconds: int):
        if not self._is_seeking:
            self._seek.setValue(seconds)
        self._pos_lbl.setText(format_duration(seconds))

    def set_duration(self, seconds: int):
        self._duration = seconds
        self._seek.setRange(0, seconds)
        self._dur_lbl.setText(format_duration(seconds))

    # ----------------------------------------------------------------- private

    def _set_thumb(self, px: QPixmap):
        self._thumb.setPixmap(px)
        self._thumb.setText("")

    def _start_seek(self):
        self._is_seeking = True

    def _end_seek(self):
        self._is_seeking = False
        self.seek.emit(self._seek.value())
