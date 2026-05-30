from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QMenu,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QCursor

from core.api import format_duration


class QueuePanel(QWidget):
    play_index = pyqtSignal(int)
    remove_index = pyqtSignal(int)
    move_track = pyqtSignal(int, int)   # from_index, to_index
    clear_queue = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        self._current_index = -1
        self._ignore_move = False
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── header ─────────────────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet("background-color: #0c0c18;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 10, 8, 10)

        title = QLabel("QUEUE")
        title.setObjectName("sectionHeader")
        hl.addWidget(title, stretch=1)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("smallBtn")
        clear_btn.clicked.connect(self.clear_queue)
        hl.addWidget(clear_btn)

        layout.addWidget(header)

        # ── list ───────────────────────────────────────────────────────────
        self._list = QListWidget()
        self._list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.itemDoubleClicked.connect(self._on_double_click)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context)
        self._list.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self._list, stretch=1)

        # ── empty hint ─────────────────────────────────────────────────────
        self._empty = QLabel("Queue is empty\n\nAdd songs from\nsearch results")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setStyleSheet("color: #3a3a5c; font-size: 12px; padding: 20px;")
        layout.addWidget(self._empty)

    # ------------------------------------------------------------------ public

    def refresh(self, tracks: list[dict], current_index: int):
        """Rebuild the list from the authoritative queue data."""
        self._ignore_move = True
        self._current_index = current_index

        self._list.clear()
        for i, t in enumerate(tracks):
            dur = format_duration(t["duration"])
            item = QListWidgetItem(f"{t['title']}\n{t['channel']}  ·  {dur}")
            item.setSizeHint(QSize(0, 52))
            if i == current_index:
                item.setForeground(QColor("#e63950"))
            self._list.addItem(item)

        has_items = bool(tracks)
        self._list.setVisible(has_items)
        self._empty.setVisible(not has_items)
        self._ignore_move = False

    # ----------------------------------------------------------------- private

    def _on_double_click(self, item: QListWidgetItem):
        self.play_index.emit(self._list.row(item))

    def _on_context(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        row = self._list.row(item)
        menu = QMenu(self)
        menu.addAction("▶  Play now").triggered.connect(lambda: self.play_index.emit(row))
        menu.addSeparator()
        menu.addAction("Remove").triggered.connect(lambda: self.remove_index.emit(row))
        menu.exec(QCursor.pos())

    def _on_rows_moved(self, _parent, src_first, src_last, _dest, dest_row):
        if self._ignore_move:
            return
        # Qt moves rows to dest_row; adjust for the gap left by the source
        to = dest_row - 1 if dest_row > src_first else dest_row
        self.move_track.emit(src_first, to)
