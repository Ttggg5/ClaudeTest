from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QListWidget,
    QListWidgetItem, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
import requests
from PyQt6.QtCore import QRunnable, QThreadPool, QObject


class _ThumbSignals(QObject):
    loaded = pyqtSignal(str, QPixmap)


class _ThumbLoader(QRunnable):
    def __init__(self, video_id: str, url: str):
        super().__init__()
        self.video_id = video_id
        self.url = url
        self.signals = _ThumbSignals()

    def run(self):
        try:
            data = requests.get(self.url, timeout=8).content
            px = QPixmap()
            px.loadFromData(data)
            if not px.isNull():
                self.signals.loaded.emit(self.video_id, px.scaled(
                    80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            pass


class HomeView(QFrame):
    """Home view showing recommended songs."""

    play_track = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(60)
        self._tracks = {}
        self._pool = QThreadPool.globalInstance()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Trending Songs")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(title)

        # Songs list
        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #1E1E1E;
                border-radius: 4px;
                padding: 6px;
                margin: 2px 0;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #282828;
            }
        """)
        self._list.setIconSize(QSize(80, 80))
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

    def set_recommendations(self, tracks: list[dict]):
        """Load recommended songs into list."""
        self._list.clear()
        self._tracks.clear()

        for idx, track in enumerate(tracks[:20]):  # Show top 20
            video_id = track.get("video_id")
            title = track.get("title", "Unknown")
            artist = track.get("channel", "Unknown")
            thumbnail = track.get("thumbnail_url")

            # Create item
            item = QListWidgetItem()
            item.setText(f"{idx + 1}. {title}\n    {artist}")
            item.setData(Qt.ItemDataRole.UserRole, track)  # Store track data

            self._list.addItem(item)
            self._tracks[video_id] = (item, track)

            # Load thumbnail
            if thumbnail:
                loader = _ThumbLoader(video_id, thumbnail)
                loader.signals.loaded.connect(self._on_thumb_loaded)
                self._pool.start(loader)

    def _on_item_clicked(self, item: QListWidgetItem):
        """Play track when clicked."""
        track = item.data(Qt.ItemDataRole.UserRole)
        if track:
            self.play_track.emit(track)

    def _on_thumb_loaded(self, video_id: str, px: QPixmap):
        """Update item with thumbnail."""
        if video_id in self._tracks:
            item, track = self._tracks[video_id]
            item.setIcon(QIcon(px))

    def clear(self):
        """Clear recommendations."""
        self._list.clear()
        self._tracks.clear()
