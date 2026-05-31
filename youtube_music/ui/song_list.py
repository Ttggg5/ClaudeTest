import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRunnable, QThreadPool, QObject
from PyQt6.QtGui import QPixmap, QIcon

from ui.loading_spinner import LoadingSpinner


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


class SongList(QWidget):
    """Reusable song list with thumbnails, click-to-play, and infinite scroll.

    Shared by the home (trending) view and the explore (search results) view so
    both behave identically.
    """

    play_track = pyqtSignal(dict)   # emitted when a row is clicked
    load_more = pyqtSignal()        # emitted when scrolled near the bottom

    _TRACK_ROLE = 1001

    def __init__(self, parent=None, numbered: bool = False):
        super().__init__(parent)
        self._numbered = numbered
        self._tracks = {}
        self._items = {}
        self._count = 0
        self._has_more = False
        self._pool = QThreadPool.globalInstance()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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
        self._list.verticalScrollBar().valueChanged.connect(self._on_scroll)
        layout.addWidget(self._list)

        # Loading spinner overlay (centered, hidden by default)
        self._spinner = LoadingSpinner("Loading songs…", self)
        self._spinner.setStyleSheet("background-color: rgba(18, 18, 18, 180); border-radius: 8px;")
        self._spinner.hide()

    # ------------------------------------------------------------------ public

    def set_loading(self, loading: bool, text: str | None = None):
        """Show or hide the centered loading spinner overlay."""
        if loading:
            if text:
                self._spinner.set_text(text)
            self._position_spinner()
            self._spinner.show()
            self._spinner.raise_()
        else:
            self._spinner.hide()

    def set_results(self, tracks: list[dict], has_more: bool = False):
        """Replace the list with a fresh page of tracks."""
        self.set_loading(False)
        self._list.clear()
        self._tracks.clear()
        self._items.clear()
        self._count = 0
        self._has_more = has_more

        if not tracks:
            item = QListWidgetItem("No results found")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._list.addItem(item)
            return

        self._append(tracks)

    def append_results(self, tracks: list[dict], has_more: bool = False):
        """Append the next page of tracks (infinite scroll)."""
        self.set_loading(False)
        self._has_more = has_more
        self._append(tracks)

    def clear(self):
        self._list.clear()
        self._tracks.clear()
        self._items.clear()
        self._count = 0
        self._has_more = False

    # ----------------------------------------------------------------- private

    def _append(self, tracks: list[dict]):
        for track in tracks:
            self._count += 1
            video_id = track.get("video_id")
            title = track.get("title", "Unknown")
            artist = track.get("channel", "Unknown")
            thumbnail = track.get("thumbnail_url")

            if self._numbered:
                text = f"{self._count}. {title}\n    {artist}"
            else:
                text = f"{title}\n    {artist}"

            item = QListWidgetItem(text)
            item.setData(self._TRACK_ROLE, track)
            self._list.addItem(item)
            self._tracks[video_id] = track
            self._items[video_id] = item

            if thumbnail:
                loader = _ThumbLoader(video_id, thumbnail)
                loader.signals.loaded.connect(self._on_thumb_loaded)
                self._pool.start(loader)

    def _on_scroll(self, value: int):
        if not self._has_more:
            return
        bar = self._list.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() * 0.9:
            self._has_more = False  # guard until the next page arrives
            self.load_more.emit()

    def _on_thumb_loaded(self, video_id: str, px: QPixmap):
        item = self._items.get(video_id)
        if item is not None:
            item.setIcon(QIcon(px))

    def _on_item_clicked(self, item: QListWidgetItem):
        track = item.data(self._TRACK_ROLE)
        if track:
            self.play_track.emit(track)

    def _position_spinner(self):
        """Center the spinner overlay over the list."""
        size = self._spinner.sizeHint()
        w, h = size.width(), size.height()
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        self._spinner.setGeometry(x, y, w, h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._spinner.isVisible():
            self._position_spinner()
