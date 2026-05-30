import sys
import os

# Add project root to path so relative imports work from any CWD
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.theme import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Music Player")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
