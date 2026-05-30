import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize, QRunnable, QThreadPool
from PyQt6.QtGui import QPixmap


class _AlbumThumbSignals(QObject):
    loaded = pyqtSignal(str, QPixmap)


class _AlbumThumbLoader(QRunnable):
    def __init__(self, video_id: str, url: str):
        super().__init__()
        self.video_id = video_id
        self.url = url
        self.signals = _AlbumThumbSignals()

    def run(self):
        try:
            data = requests.get(self.url, timeout=8).content
            px = QPixmap()
            px.loadFromData(data)
            if not px.isNull():
                self.signals.loaded.emit(self.video_id, px.scaled(
                    150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            pass


class AlbumCard(QFrame):
    """Single album/publication card."""

    play = pyqtSignal(dict)

    def __init__(self, track: dict, parent=None):
        super().__init__(parent)
        self.track = track
        self.setObjectName("card")
        self.setFixedSize(160, 200)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._thumb = QLabel()
        self._thumb.setFixedSize(144, 144)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            "background-color: #282828; border-radius: 8px; color: #B3B3B3; font-size: 32px;"
        )
        self._thumb.setText("♪")
        layout.addWidget(self._thumb)

        self._title = QLabel(self.track.get("title", "Unknown"))
        self._title.setStyleSheet("font-size: 12px; font-weight: 500; color: #FFFFFF;")
        self._title.setWordWrap(True)
        self._title.setMaximumHeight(40)
        layout.addWidget(self._title)

        # Play button
        play_btn = QPushButton("▶")
        play_btn.setObjectName("smallBtn")
        play_btn.setFixedHeight(32)
        play_btn.clicked.connect(lambda: self.play.emit(self.track))
        layout.addWidget(play_btn)

    def set_thumbnail(self, px: QPixmap):
        self._thumb.setPixmap(px)
        self._thumb.setText("")


class AlbumGrid(QFrame):
    """Grid view of albums/publications."""

    play_album = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(60)
        self._pool = QThreadPool.globalInstance()
        self._cards = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QLabel("Popular Albums")
        header.setObjectName("sectionHeader")
        header.setStyleSheet("font-size: 14px; font-weight: 600; color: #FFFFFF; letter-spacing: 0.5px;")
        layout.addWidget(header)

        # Grid container
        grid_frame = QFrame()
        grid_frame.setStyleSheet("background-color: transparent;")
        self._grid = QGridLayout(grid_frame)
        self._grid.setSpacing(16)
        self._grid.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(grid_frame, stretch=1)

    def add_albums(self, tracks: list[dict]):
        """Add album cards from tracks."""
        # Clear existing cards
        for i in reversed(range(self._grid.count())):
            self._grid.itemAt(i).widget().deleteLater()
        self._cards.clear()

        # Add up to 6 cards in a 3x2 grid
        for idx, track in enumerate(tracks[:6]):
            row = idx // 3
            col = idx % 3

            card = AlbumCard(track)
            card.play.connect(self.play_album.emit)
            self._grid.addWidget(card, row, col)
            self._cards[track["videoId"]] = card

            # Load thumbnail
            if track.get("thumbnail_url"):
                loader = _AlbumThumbLoader(track["videoId"], track["thumbnail_url"])
                loader.signals.loaded.connect(self._on_thumb_loaded)
                self._pool.start(loader)

    def _on_thumb_loaded(self, video_id: str, px: QPixmap):
        if video_id in self._cards:
            self._cards[video_id].set_thumbnail(px)

    def clear(self):
        """Clear all album cards."""
        for i in reversed(range(self._grid.count())):
            self._grid.itemAt(i).widget().deleteLater()
        self._cards.clear()
