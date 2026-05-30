from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal


class SidebarNavigation(QFrame):
    """Left sidebar with navigation and queue/library tabs."""

    nav_home = pyqtSignal()
    nav_explore = pyqtSignal()
    nav_library = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(280)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo section
        logo_frame = QFrame()
        logo_frame.setFixedHeight(70)
        logo_frame.setStyleSheet("background-color: #0a0a0a; border-bottom: 1px solid #282828;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 16, 20, 16)

        logo = QLabel("▶ Music")
        logo.setStyleSheet("font-size: 20px; font-weight: 600; color: #FF0000;")
        logo_layout.addWidget(logo)
        layout.addWidget(logo_frame)

        # Navigation section
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background-color: transparent;")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 16, 0, 16)
        nav_layout.setSpacing(0)

        nav_section = QLabel("MENU")
        nav_section.setObjectName("sectionHeader")
        nav_section.setStyleSheet("color: #B3B3B3; font-size: 11px; font-weight: 600; letter-spacing: 1px; padding: 0 20px 12px 20px;")
        nav_layout.addWidget(nav_section)

        home_btn = self._create_nav_button("🏠 Home", self.nav_home)
        explore_btn = self._create_nav_button("🔍 Explore", self.nav_explore)
        library_btn = self._create_nav_button("📚 Library", self.nav_library)

        nav_layout.addWidget(home_btn)
        nav_layout.addWidget(explore_btn)
        nav_layout.addWidget(library_btn)
        nav_layout.addSpacing(16)

        layout.addWidget(nav_frame)

        # Tab widget for Queue / Playlists
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabBar::tab {
                background-color: transparent;
                border: none;
                padding: 8px 20px;
                color: #B3B3B3;
                font-size: 12px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #FFFFFF;
                border-bottom: 2px solid #FF0000;
            }
        """)

        # Queue tab will be added dynamically
        layout.addWidget(self._tabs, stretch=1)

    def _create_nav_button(self, text: str, signal):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #B3B3B3;
                text-align: left;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.12);
            }
        """)
        btn.clicked.connect(signal)
        return btn

    def add_queue_tab(self, queue_widget):
        """Add the queue widget as a tab."""
        self._tabs.addTab(queue_widget, "📋 Queue")

    def add_playlists_tab(self, playlists_widget):
        """Add playlists widget as a tab."""
        self._tabs.addTab(playlists_widget, "⭐ Playlists")
