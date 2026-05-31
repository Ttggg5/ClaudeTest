from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStatusBar, QMessageBox, QStackedWidget,
)
from PyQt6.QtCore import Qt

import config as cfg
from core.api import YouTubeAPI, SearchWorker
from core.player import AudioPlayer, URLExtractWorker
from core.queue import Queue
from ui.queue_panel import QueuePanel
from ui.player_bar import PlayerBar
from ui.settings_dialog import SettingsDialog
from ui.sidebar import SidebarNavigation
from ui.home_view import HomeView
from ui.explore_view import ExploreView
from ui.library_view import LibraryView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Music Player")
        self.resize(1400, 800)
        self.setMinimumSize(1000, 600)

        self._api: YouTubeAPI | None = None
        self._queue = Queue()
        self._url_worker: URLExtractWorker | None = None
        self._current_track = None
        self._rec_worker = None
        self._search_worker = None
        self._search_query = None
        self._search_next_token = None
        self._loading_more = False
        # home (trending) pagination
        self._home_next_token = None
        self._home_loading = False

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

        # ── top toolbar ─────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #0a0a0a; border-bottom: 1px solid #282828;")
        toolbar.setFixedHeight(56)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(20, 0, 20, 0)

        from PyQt6.QtWidgets import QLabel
        app_name = QLabel("▶ YouTube Music")
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

        # ── main content: sidebar + center panel ─────────────────────────
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # Left sidebar with navigation and queue tabs
        self._sidebar = SidebarNavigation()
        self._queue_panel = QueuePanel()
        self._sidebar.add_queue_tab(self._queue_panel)
        content.addWidget(self._sidebar)

        # ── center panel: stacked widget for Home/Explore/Library ────────
        self._center_stack = QStackedWidget()

        # Home view
        self._home_view = HomeView()
        self._home_view.play_track.connect(self._play_track)
        self._center_stack.addWidget(self._home_view)

        # Explore view
        self._explore_view = ExploreView()
        self._center_stack.addWidget(self._explore_view)

        # Library view
        self._library_view = LibraryView()
        self._center_stack.addWidget(self._library_view)

        # Center panel with stacked views
        content.addWidget(self._center_stack, stretch=1)

        root.addLayout(content, stretch=1)

        # ── player bar ─────────────────────────────────────────────────────
        self._player_bar = PlayerBar()
        root.addWidget(self._player_bar)

        # ── status bar ─────────────────────────────────────────────────────
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    # ─────────────────────────────────────────────────── signals

    def _connect_signals(self):
        # sidebar navigation → view switching
        self._sidebar.nav_home.connect(self._show_home)
        self._sidebar.nav_explore.connect(self._show_explore)
        self._sidebar.nav_library.connect(self._show_library)

        # home view → this window
        self._home_view.play_track.connect(self._play_track)
        self._home_view.load_more.connect(self._on_home_load_more)

        # explore view → search
        self._explore_view.search_requested.connect(self._on_explore_search)
        self._explore_view.load_more.connect(self._on_load_more)
        self._explore_view.play_track.connect(self._play_track)

        # queue panel → this window
        self._queue_panel.play_index.connect(self._play_at_index)
        self._queue_panel.remove_index.connect(self._remove_from_queue)
        self._queue_panel.move_track.connect(self._move_in_queue)
        self._queue_panel.clear_queue.connect(self._clear_queue)

        # queue model → queue panel + library view refresh
        self._queue.queue_updated.connect(self._refresh_queue_panel)
        self._queue.queue_updated.connect(self._refresh_library_view)

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

    # ─────────────────────────────────────────────────── navigation

    def _show_home(self):
        """Switch to Home view."""
        self._center_stack.setCurrentWidget(self._home_view)
        self.statusBar().showMessage("Home - Recommended Songs")

    def _show_explore(self):
        """Switch to Explore view."""
        self._center_stack.setCurrentWidget(self._explore_view)
        self.statusBar().showMessage("Explore - Search, browse genres & moods")

    def _show_library(self):
        """Switch to Library view."""
        self._center_stack.setCurrentWidget(self._library_view)
        self._refresh_library_view(self._queue.tracks)
        self.statusBar().showMessage("Library - Your playlists and queue")

    def _on_explore_search(self, query: str):
        """Handle a new search from Explore view (first page)."""
        if not self._api:
            self.statusBar().showMessage("Configure API key first")
            return

        # Cancel any in-flight search
        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.quit()
            self._search_worker.wait()

        self._search_query = query
        self._search_next_token = None
        self._loading_more = False

        self.statusBar().showMessage(f'Searching for "{query}"...')
        self._search_worker = SearchWorker(self._api, query)
        self._search_worker.results_ready.connect(self._on_search_results)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()

    def _on_load_more(self):
        """Load the next page of search results (infinite scroll)."""
        if not self._api or not self._search_query or not self._search_next_token:
            return
        if self._loading_more:
            return
        if self._search_worker and self._search_worker.isRunning():
            return

        self._loading_more = True
        self.statusBar().showMessage("Loading more results…")
        self._search_worker = SearchWorker(
            self._api, self._search_query, page_token=self._search_next_token
        )
        self._search_worker.results_ready.connect(self._on_more_results)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()

    def _on_search_results(self, tracks: list[dict], next_token):
        """Display first-page search results in Explore view."""
        self._search_next_token = next_token
        self._explore_view.set_results(tracks, has_more=bool(next_token))
        self.statusBar().showMessage(f"Found {len(tracks)} results")

    def _on_more_results(self, tracks: list[dict], next_token):
        """Append next-page results in Explore view."""
        self._search_next_token = next_token
        self._loading_more = False
        self._explore_view.append_results(tracks, has_more=bool(next_token))

    def _on_search_error(self, msg: str):
        """Handle search error."""
        self._loading_more = False
        self.statusBar().showMessage(f"Search error: {msg}")

    # ─────────────────────────────────────────────────── api init

    def _init_api(self):
        conf = cfg.load_config()
        key = conf.get("api_key", "")
        if key:
            self._api = YouTubeAPI(key)
            self._load_recommendations()
        else:
            self.statusBar().showMessage("No API key — open Settings to add one.")
            self._open_settings()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            key = dlg.get_key()
            self._api = YouTubeAPI(key)
            self._load_recommendations()
            self.statusBar().showMessage("API key saved.")

    # ─────────────────────────────────────────────────── playback

    def _play_track(self, track: dict):
        self._queue.play_now(track)
        self._load_and_play(track)

    def _load_and_play(self, track: dict):
        self._current_track = track
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

    def _refresh_library_view(self, tracks: list[dict]):
        """Update library view with current queue."""
        self._library_view.update_queue(tracks, self._queue.current_index)

    def _load_recommendations(self):
        """Search trending songs and show them on the home screen (first page)."""
        if not self._api:
            return

        # Cancel previous worker if running
        if self._rec_worker and self._rec_worker.isRunning():
            self._rec_worker.quit()
            self._rec_worker.wait()

        self._home_next_token = None
        self._home_loading = False

        self.statusBar().showMessage("Loading trending songs…")
        self._rec_worker = SearchWorker(self._api, "trending music")
        self._rec_worker.results_ready.connect(self._on_recommendations_ready)
        self._rec_worker.error.connect(
            lambda msg: self.statusBar().showMessage(f"Couldn't load trending: {msg}")
        )
        self._rec_worker.start()
        self._show_home()

    def _on_home_load_more(self):
        """Load the next page of trending songs (infinite scroll)."""
        if not self._api or not self._home_next_token or self._home_loading:
            return
        if self._rec_worker and self._rec_worker.isRunning():
            return

        self._home_loading = True
        self.statusBar().showMessage("Loading more trending songs…")
        self._rec_worker = SearchWorker(
            self._api, "trending music", page_token=self._home_next_token
        )
        self._rec_worker.results_ready.connect(self._on_more_recommendations)
        self._rec_worker.error.connect(
            lambda msg: self.statusBar().showMessage(f"Couldn't load more: {msg}")
        )
        self._rec_worker.start()

    def _on_recommendations_ready(self, tracks: list[dict], next_token=None):
        self._home_next_token = next_token
        self._home_view.set_recommendations(tracks, has_more=bool(next_token))
        self.statusBar().showMessage(f"Showing {len(tracks)} trending songs")

    def _on_more_recommendations(self, tracks: list[dict], next_token=None):
        self._home_next_token = next_token
        self._home_loading = False
        self._home_view.append_recommendations(tracks, has_more=bool(next_token))

    # ─────────────────────────────────────────────────── close

    def closeEvent(self, event):
        self._player.stop()
        if self._url_worker and self._url_worker.isRunning():
            self._url_worker.terminate()
            self._url_worker.wait()
        if self._rec_worker and self._rec_worker.isRunning():
            self._rec_worker.quit()
            self._rec_worker.wait()
        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.quit()
            self._search_worker.wait()
        event.accept()
