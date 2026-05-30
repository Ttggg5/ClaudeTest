from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStatusBar, QMessageBox,
)
from PyQt6.QtCore import Qt

import config as cfg
from core.api import YouTubeAPI
from core.player import AudioPlayer, URLExtractWorker
from core.queue import Queue
from ui.search_panel import SearchPanel
from ui.queue_panel import QueuePanel
from ui.player_bar import PlayerBar
from ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Music Player")
        self.resize(1100, 700)
        self.setMinimumSize(800, 550)

        self._api: YouTubeAPI | None = None
        self._queue = Queue()
        self._url_worker: URLExtractWorker | None = None

        try:
            self._player = AudioPlayer()
        except RuntimeError as e:
            QMessageBox.critical(self, "VLC Not Found", str(e))
            raise SystemExit(1) from e

        self._build_ui()
        self._connect_signals()
        self._init_api()

    # ─────────────────────────────────────────────────── build

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── top toolbar (Material App Bar) ─────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet(f"background-color: #1a1a2e; border-bottom: 1px solid #2a2a46;")
        toolbar.setFixedHeight(56)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(20, 0, 16, 0)

        from PyQt6.QtWidgets import QLabel
        app_name = QLabel("▶  YouTube Music")
        app_name.setObjectName("appTitle")
        tl.addWidget(app_name)
        tl.addStretch()

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("iconBtn")
        settings_btn.setFixedSize(48, 48)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._open_settings)
        tl.addWidget(settings_btn)

        root.addWidget(toolbar)

        # ── main content: queue sidebar + search ───────────────────────────
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        self._queue_panel = QueuePanel()
        content.addWidget(self._queue_panel)

        self._search_panel = SearchPanel()
        content.addWidget(self._search_panel, stretch=1)

        root.addLayout(content, stretch=1)

        # ── player bar ─────────────────────────────────────────────────────
        self._player_bar = PlayerBar()
        root.addWidget(self._player_bar)

        # ── status bar ─────────────────────────────────────────────────────
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    # ─────────────────────────────────────────────────── signals

    def _connect_signals(self):
        # search panel → this window
        self._search_panel.play_now.connect(self._play_track)
        self._search_panel.add_to_queue.connect(self._add_to_queue)
        self._search_panel.status_message.connect(self.statusBar().showMessage)

        # queue panel → this window
        self._queue_panel.play_index.connect(self._play_at_index)
        self._queue_panel.remove_index.connect(self._remove_from_queue)
        self._queue_panel.move_track.connect(self._move_in_queue)
        self._queue_panel.clear_queue.connect(self._clear_queue)

        # queue model → queue panel refresh
        self._queue.queue_updated.connect(self._refresh_queue_panel)

        # player bar controls → this window
        self._player_bar.play_pause.connect(self._toggle_play_pause)
        self._player_bar.next_track.connect(self._next_track)
        self._player_bar.prev_track.connect(self._prev_track)
        self._player_bar.seek.connect(self._on_seek)  # Custom handler
        self._player_bar.volume_changed.connect(self._player.set_volume)

        # player → player bar
        self._player.position_changed.connect(self._player_bar.set_position)
        self._player.duration_changed.connect(self._player_bar.set_duration)
        self._player.state_changed.connect(self._on_player_state)

    # ─────────────────────────────────────────────────── api init

    def _init_api(self):
        conf = cfg.load_config()
        key = conf.get("api_key", "")
        if key:
            self._api = YouTubeAPI(key)
            self._search_panel.set_api(self._api)
        else:
            self.statusBar().showMessage("No API key — open Settings to add one.")
            self._open_settings()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            key = dlg.get_key()
            self._api = YouTubeAPI(key)
            self._search_panel.set_api(self._api)
            self.statusBar().showMessage("API key saved.")

    # ─────────────────────────────────────────────────── playback

    def _play_track(self, track: dict):
        self._queue.play_now(track)
        self._load_and_play(track)

    def _load_and_play(self, track: dict):
        self._player.stop()
        self._player_bar.set_track(track)
        self._player_bar.set_state("loading")
        self.statusBar().showMessage(f"Loading: {track['title']}…")

        # cancel any running extraction
        if self._url_worker and self._url_worker.isRunning():
            self._url_worker.terminate()
            self._url_worker.wait()

        self._url_worker = URLExtractWorker(track)
        self._url_worker.url_ready.connect(self._on_url_ready)
        self._url_worker.error.connect(self._on_url_error)
        self._url_worker.start()

    def _on_url_ready(self, url: str, track: dict):
        self._player.play_url(url)
        self._player.set_volume(self._player_bar._vol_slider.value())
        self.statusBar().showMessage(f"Now playing: {track['title']}")

    def _on_url_error(self, msg: str, track: dict):
        self._player_bar.set_state("stopped")
        self.statusBar().showMessage(f'Failed to load "{track["title"]}": {msg}')

    def _on_player_state(self, state: str):
        self._player_bar.set_state(state)
        if state == "ended":
            self._next_track()

    def _toggle_play_pause(self):
        if self._player.state in ("stopped", "ended"):
            # nothing loaded — try replaying current queue track
            t = self._queue.current
            if t:
                self._load_and_play(t)
        else:
            self._player.play_pause()

    def _next_track(self):
        t = self._queue.next()
        if t:
            self._load_and_play(t)
        else:
            self._player_bar.set_state("stopped")
            self.statusBar().showMessage("End of queue.")

    def _prev_track(self):
        if self._player.get_position() > 3:
            self._player.seek(0)
        else:
            t = self._queue.previous()
            if t:
                self._load_and_play(t)

    def _on_seek(self, seconds: int) -> None:
        """Handle seek events. If seeking to ~95%+, skip to next instead."""
        dur = self._player.get_duration()
        if dur > 0 and seconds >= dur * 0.95:
            # Dragged to near the end; skip to next song instead
            self._next_track()
        else:
            self._player.seek(seconds)

    # ─────────────────────────────────────────────────── queue ops

    def _add_to_queue(self, track: dict):
        self._queue.add(track)
        self.statusBar().showMessage(f"Added to queue: {track['title']}")

    def _play_at_index(self, index: int):
        t = self._queue.play_at(index)
        if t:
            self._load_and_play(t)

    def _remove_from_queue(self, index: int):
        self._queue.remove(index)

    def _move_in_queue(self, from_idx: int, to_idx: int):
        self._queue.move(from_idx, to_idx)

    def _clear_queue(self):
        self._queue.clear()
        self._player.stop()
        self._player_bar.set_track(None)
        self._player_bar.set_state("stopped")

    def _refresh_queue_panel(self, tracks: list[dict]):
        self._queue_panel.refresh(tracks, self._queue.current_index)

    # ─────────────────────────────────────────────────── close

    def closeEvent(self, event):
        self._player.stop()
        if self._url_worker and self._url_worker.isRunning():
            self._url_worker.terminate()
            self._url_worker.wait()
        event.accept()
