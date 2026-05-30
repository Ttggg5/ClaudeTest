"""Animated loading spinner widget."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class LoadingSpinner(QWidget):
    """Rotating loading spinner with text."""

    def __init__(self, text: str = "Loading...", parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self._rotation = 0
        self._text = text
        self._build()
        self._start_animation()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Spinner icon
        self._spinner = QLabel("⟳")
        self._spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner.setStyleSheet("font-size: 40px; color: #FF0000;")
        layout.addWidget(self._spinner)

        # Text label
        self._label = QLabel(self._text)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: #8088a0; font-size: 12px;")
        layout.addWidget(self._label)

    def _start_animation(self):
        """Start the rotation animation."""
        self._timer = QTimer()
        self._timer.timeout.connect(self._rotate)
        self._timer.start(50)  # Update every 50ms for smooth rotation

    def _rotate(self):
        """Rotate the spinner."""
        self._rotation = (self._rotation + 15) % 360
        transform = f"transform: rotate({self._rotation}deg);"
        self._spinner.setStyleSheet(
            f"font-size: 40px; color: #FF0000; {transform}"
        )

    def set_text(self, text: str):
        """Update the loading text."""
        self._label.setText(text)

    def stop(self):
        """Stop the animation."""
        if hasattr(self, "_timer"):
            self._timer.stop()
