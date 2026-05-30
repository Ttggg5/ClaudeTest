import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject, QRunnable, QThreadPool
from PyQt6.QtGui import QPixmap


class _ArtistThumbSignals(QObject):
    loaded = pyqtSignal(QPixmap)


class _ArtistThumbLoader(QRunnable):
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals = _ArtistThumbSignals()

    def run(self):
        try:
            data = requests.get(self.url, timeout=8).content
            px = QPixmap()
            px.loadFromData(data)
            if not px.isNull():
                self.signals.loaded.emit(px.scaled(
                    140, 140, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            pass


class ArtistProfile(QFrame):
    """Artist profile card showing now-playing artist with stats."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(220)
        self._pool = QThreadPool.globalInstance()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Top: Thumbnail
        thumb_container = QHBoxLayout()
        thumb_container.setContentsMargins(0, 0, 0, 0)

        self._thumb = QLabel()
        self._thumb.setFixedSize(140, 140)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            "background-color: #282828; border-radius: 70px; color: #B3B3B3; font-size: 32px;"
        )
        self._thumb.setText("♪")
        thumb_container.addWidget(self._thumb)
        thumb_container.addStretch()

        layout.addLayout(thumb_container)

        # Artist name
        self._name_lbl = QLabel("No artist")
        self._name_lbl.setStyleSheet("font-size: 18px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(self._name_lbl)

        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)

        self._listeners_lbl = QLabel("0 listeners")
        self._listeners_lbl.setStyleSheet("font-size: 12px; color: #B3B3B3;")
        stats_layout.addWidget(self._listeners_lbl)

        self._followers_lbl = QLabel("0 followers")
        self._followers_lbl.setStyleSheet("font-size: 12px; color: #B3B3B3;")
        stats_layout.addWidget(self._followers_lbl)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        layout.addStretch()

    def set_artist(self, artist_name: str, thumbnail_url: str | None = None):
        """Update artist profile with name and optional thumbnail."""
        self._name_lbl.setText(artist_name)
        self._listeners_lbl.setText("0 listeners")
        self._followers_lbl.setText("0 followers")
        self._thumb.setText("♪")
        self._thumb.setPixmap(QPixmap())

        if thumbnail_url:
            loader = _ArtistThumbLoader(thumbnail_url)
            loader.signals.loaded.connect(self._set_thumb)
            self._pool.start(loader)

    def set_stats(self, listeners: int = 0, followers: int = 0):
        """Update listener and follower counts."""
        self._listeners_lbl.setText(f"{listeners:,} listeners" if listeners > 0 else "0 listeners")
        self._followers_lbl.setText(f"{followers:,} followers" if followers > 0 else "0 followers")

    def clear(self):
        """Clear the artist profile."""
        self._name_lbl.setText("Select a song")
        self._listeners_lbl.setText("0 listeners")
        self._followers_lbl.setText("0 followers")
        self._thumb.setText("♪")
        self._thumb.setPixmap(QPixmap())

    def _set_thumb(self, px: QPixmap):
        self._thumb.setPixmap(px)
        self._thumb.setText("")
