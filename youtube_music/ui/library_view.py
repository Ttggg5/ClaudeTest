from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QListWidget,
    QListWidgetItem, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal


class LibraryView(QFrame):
    """Library view showing playlists and liked songs."""

    play_track = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(200)  # Flexible height
        self._queue_tracks = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Library")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(title)

        # Playlists section
        pl_header = QLabel("Playlists")
        pl_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(pl_header)

        # Playlist list
        self._playlists = QListWidget()
        self._playlists.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #1E1E1E;
                border-radius: 8px;
                padding: 12px;
                margin: 4px 0;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #282828;
            }
            QListWidget::item:selected {
                background-color: #282828;
                color: #FF0000;
            }
        """)

        playlists = [
            "❤️ Liked Songs",
            "🎵 Recently Played",
            "⭐ Top Tracks",
            "🎉 Party Mix",
            "😴 Chill Vibes",
            "💪 Workout",
        ]

        for pl in playlists:
            item = QListWidgetItem(pl)
            self._playlists.addItem(item)

        layout.addWidget(self._playlists)

        # Now playing section
        now_header = QLabel("Now Playing Queue")
        now_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF; margin-top: 16px;")
        layout.addWidget(now_header)

        # Queue list
        self._queue_list = QListWidget()
        self._queue_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #1E1E1E;
                border-radius: 8px;
                padding: 8px;
                margin: 2px 0;
                color: #B3B3B3;
                font-size: 12px;
            }
            QListWidget::item:hover {
                background-color: #282828;
            }
            QListWidget::item:selected {
                background-color: #282828;
                color: #FF0000;
            }
        """)
        self._queue_list.setMaximumHeight(200)
        layout.addWidget(self._queue_list)

        layout.addStretch()

    def update_queue(self, tracks: list[dict], current_index: int = -1):
        """Update the queue display."""
        self._queue_tracks = tracks
        self._queue_list.clear()

        for idx, track in enumerate(tracks):
            title = track.get("title", "Unknown")
            artist = track.get("channel", "Unknown Artist")
            text = f"{idx + 1}. {title} - {artist}"

            item = QListWidgetItem(text)
            if idx == current_index:
                item.setForeground(__import__("PyQt6.QtGui", fromlist=["QColor"]).QColor("#FF0000"))
                item.setFont(__import__("PyQt6.QtGui", fromlist=["QFont"]).QFont("Segoe UI", 11, 500))
            self._queue_list.addItem(item)

    def clear_queue(self):
        """Clear queue display."""
        self._queue_list.clear()
        self._queue_tracks.clear()
