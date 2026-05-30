import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QFrame, QSizePolicy, QMenu,
)
from PyQt6.QtCore import Qt, QSize, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QIcon, QCursor

from core.api import YouTubeAPI, SearchWorker, format_duration


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
                    80, 45, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            pass


class ResultItem(QWidget):
    play_now = pyqtSignal(dict)
    add_to_queue = pyqtSignal(dict)

    def __init__(self, track: dict, parent=None):
        super().__init__(parent)
        self.track = track
        self.setObjectName("card")
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self._thumb = QLabel()
        self._thumb.setFixedSize(90, 90)
        self._thumb.setStyleSheet(
            "background:#1a1a2e; border-radius:12px; color:#3a3a5c; font-size:24px;"
        )
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setText("♪")
        layout.addWidget(self._thumb)

        # Info section
        info = QVBoxLayout()
        info.setSpacing(4)

        title_lbl = QLabel(self.track["title"])
        title_lbl.setObjectName("resultTitle")
        title_lbl.setMaximumWidth(320)
        title_lbl.setWordWrap(False)
        title_lbl.setToolTip(self.track["title"])
        info.addWidget(title_lbl)

        meta = QLabel(f"{self.track['channel']}  ·  {format_duration(self.track['duration'])}")
        meta.setObjectName("resultMeta")
        info.addWidget(meta)

        info.addStretch()
        layout.addLayout(info, stretch=1)

        # Action buttons
        actions = QHBoxLayout()
        actions.setSpacing(8)

        play_btn = QPushButton("▶")
        play_btn.setObjectName("iconBtn")
        play_btn.setFixedSize(40, 40)
        play_btn.setToolTip("Play now")
        play_btn.clicked.connect(lambda: self.play_now.emit(self.track))
        actions.addWidget(play_btn)

        add_btn = QPushButton("✓")
        add_btn.setObjectName("iconBtn")
        add_btn.setFixedSize(40, 40)
        add_btn.setToolTip("Add to queue")
        add_btn.clicked.connect(lambda: self.add_to_queue.emit(self.track))
        actions.addWidget(add_btn)

        layout.addLayout(actions)

    def set_thumbnail(self, px: QPixmap):
        self._thumb.setPixmap(px)
        self._thumb.setText("")

    def mouseDoubleClickEvent(self, _event):
        self.play_now.emit(self.track)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("▶  Play now").triggered.connect(lambda: self.play_now.emit(self.track))
        menu.addAction("✓ Add to queue").triggered.connect(lambda: self.add_to_queue.emit(self.track))
        menu.exec(QCursor.pos())


class SearchPanel(QWidget):
    play_now = pyqtSignal(dict)
    add_to_queue = pyqtSignal(dict)
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api: YouTubeAPI | None = None
        self._worker: SearchWorker | None = None
        self._pool = QThreadPool.globalInstance()
        self._item_map: dict[str, ResultItem] = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── search bar ─────────────────────────────────────────────────────
        bar = QFrame()
        bar.setObjectName("searchArea")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 12, 16, 12)
        bar_layout.setSpacing(12)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search songs, artists, albums…")
        self._search_input.returnPressed.connect(self._do_search)
        bar_layout.addWidget(self._search_input, stretch=1)

        self._search_btn = QPushButton("Search")
        self._search_btn.setObjectName("filledBtn")
        self._search_btn.setFixedWidth(120)
        self._search_btn.clicked.connect(self._do_search)
        bar_layout.addWidget(self._search_btn)

        layout.addWidget(bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a46;")
        layout.addWidget(sep)

        # ── results ────────────────────────────────────────────────────────
        self._list = QListWidget()
        self._list.setSpacing(2)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._list, stretch=1)

        # ── empty state ────────────────────────────────────────────────────
        self._empty_lbl = QLabel("Search for music above to get started")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #3a3a5c; font-size: 14px; padding: 40px;")
        layout.addWidget(self._empty_lbl)

    def set_api(self, api: YouTubeAPI):
        self._api = api

    def _do_search(self):
        if not self._api:
            self.status_message.emit("Configure your API key in Settings first.")
            return
        query = self._search_input.text().strip()
        if not query:
            return

        self._search_btn.setEnabled(False)
        self._list.clear()
        self._item_map.clear()
        self._empty_lbl.hide()
        self.status_message.emit(f'Searching for "{query}"...')

        self._worker = SearchWorker(self._api, query)
        self._worker.results_ready.connect(self._on_results)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(lambda: self._search_btn.setEnabled(True))
        self._worker.start()

    def _on_results(self, tracks: list[dict]):
        self._list.clear()
        self._item_map.clear()

        if not tracks:
            self._empty_lbl.setText("No results found.")
            self._empty_lbl.show()
            self.status_message.emit("No results found.")
            return

        self._empty_lbl.hide()
        self.status_message.emit(f"{len(tracks)} results")

        for track in tracks:
            widget = ResultItem(track)
            widget.play_now.connect(self.play_now)
            widget.add_to_queue.connect(self.add_to_queue)

            item = QListWidgetItem(self._list)
            item.setSizeHint(QSize(0, 64))
            self._list.setItemWidget(item, widget)
            self._item_map[track["video_id"]] = widget

            if track["thumbnail_url"]:
                loader = _ThumbLoader(track["video_id"], track["thumbnail_url"])
                loader.signals.loaded.connect(self._on_thumb)
                self._pool.start(loader)

    def _on_thumb(self, video_id: str, px: QPixmap):
        if video_id in self._item_map:
            self._item_map[video_id].set_thumbnail(px)

    def _on_error(self, msg: str):
        self._empty_lbl.setText(f'Search failed:\n{msg}')
        self._empty_lbl.show()
        self.status_message.emit(f'Error: {msg}')
        print(f'[SearchPanel] Error: {msg}')  # Debug output
