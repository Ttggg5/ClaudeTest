from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject


class ExploreView(QFrame):
    """Explore view with music categories and discovery."""

    search_category = pyqtSignal(str)  # Emits category name to search
    play_track = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)

        # Title
        title = QLabel("Explore")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(title)

        # Categories section
        cat_header = QLabel("Browse By Genre")
        cat_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(cat_header)

        # Genre grid
        categories = [
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

        grid = QGridLayout()
        grid.setSpacing(12)

        for idx, (label, category) in enumerate(categories):
            btn = self._create_category_btn(label, category)
            row = idx // 3
            col = idx % 3
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)

        # Mood section
        mood_header = QLabel("Listen By Mood")
        mood_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(mood_header)

        moods = [
            ("😊 Happy", "happy upbeat"),
            ("😢 Sad", "sad melancholic"),
            ("💪 Workout", "workout gym"),
            ("😴 Sleep", "sleep relaxing"),
            ("🎉 Party", "party dance"),
            ("📚 Focus", "focus study"),
        ]

        mood_grid = QGridLayout()
        mood_grid.setSpacing(12)

        for idx, (label, mood) in enumerate(moods):
            btn = self._create_category_btn(label, mood)
            mood_grid.addWidget(btn, 0, idx)

        layout.addLayout(mood_grid)
        layout.addStretch()

    def _create_category_btn(self, label: str, category: str):
        """Create a category button."""
        btn = QPushButton(label)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 16px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 500;
                min-height: 60px;
            }
            QPushButton:hover {
                background-color: #282828;
                border: 1px solid #FF0000;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        btn.clicked.connect(lambda: self.search_category.emit(category))
        return btn
