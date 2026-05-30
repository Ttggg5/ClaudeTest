from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.artist_profile import ArtistProfile
from ui.album_grid import AlbumGrid


class HomeView(QFrame):
    """Home view showing trending music and recommendations."""

    play_track = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(100)  # Flexible height
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Home")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(title)

        # Artist profile
        self._artist_profile = ArtistProfile()
        layout.addWidget(self._artist_profile)

        # Album grid
        self._album_grid = AlbumGrid()
        self._album_grid.play_album.connect(self.play_track)
        layout.addWidget(self._album_grid)

        layout.addStretch()

    def set_artist(self, artist_name: str, thumbnail_url: str | None = None):
        """Update artist profile."""
        self._artist_profile.set_artist(artist_name, thumbnail_url)

    def set_recommendations(self, tracks: list[dict]):
        """Load recommendations into album grid."""
        self._album_grid.add_albums(tracks)

    def clear_artist(self):
        """Clear artist profile."""
        self._artist_profile.clear()
