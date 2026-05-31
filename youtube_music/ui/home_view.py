from PyQt6.QtWidgets import QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import pyqtSignal

from ui.song_list import SongList


class HomeView(QFrame):
    """Home view showing trending songs (shares SongList with search results)."""

    play_track = pyqtSignal(dict)
    load_more = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(60)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("Trending Songs")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(title)

        self._song_list = SongList(numbered=True)
        self._song_list.play_track.connect(self.play_track)
        self._song_list.load_more.connect(self.load_more)
        layout.addWidget(self._song_list, stretch=1)

    def set_loading(self, loading: bool, text: str | None = None):
        """Show/hide the loading spinner over the song list."""
        self._song_list.set_loading(loading, text)

    def set_recommendations(self, tracks: list[dict], has_more: bool = False):
        """Load the first page of trending songs."""
        self._song_list.set_results(tracks, has_more)

    def append_recommendations(self, tracks: list[dict], has_more: bool = False):
        """Append the next page of trending songs (infinite scroll)."""
        self._song_list.append_results(tracks, has_more)

    def clear(self):
        self._song_list.clear()
