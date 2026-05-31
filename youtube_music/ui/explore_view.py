import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRunnable, QThreadPool, QObject, QEvent
from PyQt6.QtGui import QPixmap, QIcon


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


class ExploreView(QFrame):
    """Explore view with search, categories, and mood browsing."""

    search_requested = pyqtSignal(str)  # Emits search query
    play_track = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(200)
        self._tracks = {}
        self._items = {}
        self._pool = QThreadPool.globalInstance()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # ── Search Bar ─────────────────────────────────────────────────
        search_frame = QFrame()
        self._search_frame = search_frame
        search_frame.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(8)

        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 18px;")
        search_layout.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search songs, artists, albums...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 4px;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
        """)
        self._search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self._search_input)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("smallBtn")
        search_btn.setFixedWidth(80)
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)

        layout.addWidget(search_frame)

        # ── Results List ───────────────────────────────────────────────
        results_header = QLabel("Search Results")
        results_header.setStyleSheet("font-size: 12px; font-weight: 600; color: #B3B3B3;")
        layout.addWidget(results_header)

        self._results_list = QListWidget()
        self._results_list.setStyleSheet("""
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
        self._results_list.setIconSize(QSize(80, 80))
        self._results_list.itemClicked.connect(self._on_result_clicked)
        layout.addWidget(self._results_list, stretch=1)

        # ── Browse panel (genres + moods) — floating overlay on focus ──
        # Parented to self (not added to the layout) so it floats over results.
        self._browse_panel = QWidget(self)
        self._browse_panel.setObjectName("browsePanel")
        self._browse_panel.setStyleSheet(
            "#browsePanel { background-color: #1A1A1A; border: 1px solid #282828; border-radius: 8px; }"
        )
        browse_layout = QVBoxLayout(self._browse_panel)
        browse_layout.setContentsMargins(12, 12, 12, 12)
        browse_layout.setSpacing(12)

        # Browse Genres
        genre_header = QLabel("Browse By Genre")
        genre_header.setStyleSheet("font-size: 12px; font-weight: 600; color: #B3B3B3; margin-top: 4px;")
        browse_layout.addWidget(genre_header)

        genres = [
            ("🎸 Rock", "rock"),
            ("🎹 Pop", "pop"),
            ("🎤 Hip Hop", "hip hop"),
            ("🎺 Jazz", "jazz"),
            ("🎼 Classical", "classical"),
            ("🎵 Indie", "indie"),
            ("⚡ Electronic", "electronic"),
            ("🎤 R&B", "r&b"),
            ("🎸 Metal", "metal"),
            ("🎧 Lo-Fi", "lo-fi hip hop"),
            ("🌍 World", "world music"),
            ("🎶 Ambient", "ambient"),
        ]

        genre_grid = QGridLayout()
        genre_grid.setSpacing(8)

        for idx, (label, query) in enumerate(genres):
            btn = self._create_category_btn(label, query)
            row = idx // 3
            col = idx % 3
            genre_grid.addWidget(btn, row, col)

        browse_layout.addLayout(genre_grid)

        # Browse Moods
        mood_header = QLabel("Listen By Mood")
        mood_header.setStyleSheet("font-size: 12px; font-weight: 600; color: #B3B3B3; margin-top: 4px;")
        browse_layout.addWidget(mood_header)

        moods = [
            ("😊 Happy", "happy upbeat"),
            ("😢 Sad", "sad melancholic"),
            ("💪 Workout", "workout gym"),
            ("😴 Sleep", "sleep relaxing"),
            ("🎉 Party", "party dance"),
            ("📚 Focus", "focus study"),
        ]

        mood_grid = QGridLayout()
        mood_grid.setSpacing(8)

        for idx, (label, query) in enumerate(moods):
            btn = self._create_category_btn(label, query)
            mood_grid.addWidget(btn, 0, idx)

        browse_layout.addLayout(mood_grid)

        # Floating overlay — hidden until the search bar is focused
        self._browse_panel.hide()
        self._search_input.installEventFilter(self)

    def _create_category_btn(self, label: str, query: str):
        """Create a category button."""
        btn = QPushButton(label)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                border: 1px solid #282828;
                border-radius: 6px;
                padding: 10px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 500;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #282828;
                border: 1px solid #FF0000;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        btn.clicked.connect(lambda: self._search_and_browse(query))
        return btn

    def eventFilter(self, obj, event):
        """Show the genre/mood browse panel when the search bar is focused."""
        if obj is self._search_input and event.type() == QEvent.Type.FocusIn:
            self._show_browse_panel()
        return super().eventFilter(obj, event)

    def _show_browse_panel(self):
        """Position the floating browse panel below the search bar and show it."""
        self._position_browse_panel()
        self._browse_panel.show()
        self._browse_panel.raise_()

    def _position_browse_panel(self):
        """Place the floating panel just below the search bar, full width."""
        geo = self._search_frame.geometry()
        x = geo.x()
        y = geo.bottom() + 6
        width = geo.width()
        height = self._browse_panel.sizeHint().height()
        # Don't overflow the bottom of the view
        max_height = self.height() - y - 12
        if max_height > 0:
            height = min(height, max_height)
        self._browse_panel.setGeometry(x, y, width, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._browse_panel.isVisible():
            self._position_browse_panel()

    def _on_search(self):
        """Handle search button click."""
        query = self._search_input.text().strip()
        if query:
            self._browse_panel.hide()
            self.search_requested.emit(query)

    def _search_and_browse(self, query: str):
        """Search for a category/mood."""
        self._search_input.setText(query)
        self._browse_panel.hide()
        self.search_requested.emit(query)

    def set_results(self, tracks: list[dict]):
        """Display search results."""
        self._results_list.clear()
        self._tracks.clear()
        self._items.clear()

        if not tracks:
            item = QListWidgetItem("No results found")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._results_list.addItem(item)
            return

        for idx, track in enumerate(tracks[:15]):  # Show top 15 results
            video_id = track.get("video_id")
            title = track.get("title", "Unknown")
            artist = track.get("channel", "Unknown")
            thumbnail = track.get("thumbnail_url")

            text = f"{title}\n    {artist}"
            item = QListWidgetItem(text)
            item.setData(1001, track)  # Store track data
            self._results_list.addItem(item)
            self._tracks[video_id] = track
            self._items[video_id] = item

            # Load thumbnail
            if thumbnail:
                loader = _ThumbLoader(video_id, thumbnail)
                loader.signals.loaded.connect(self._on_thumb_loaded)
                self._pool.start(loader)

    def _on_thumb_loaded(self, video_id: str, px: QPixmap):
        """Set the loaded thumbnail on the matching result item."""
        item = self._items.get(video_id)
        if item is not None:
            item.setIcon(QIcon(px))

    def _on_result_clicked(self, item: QListWidgetItem):
        """Play clicked track."""
        track = item.data(1001)
        if track:
            self.play_track.emit(track)

    def get_search_text(self):
        """Get current search text."""
        return self._search_input.text()

    def set_search_text(self, text: str):
        """Set search text."""
        self._search_input.setText(text)
