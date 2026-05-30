"""
Material Design 3 theme for YouTube Music Player.
Supports system dark/light mode detection.
"""

import sys
from PyQt6.QtGui import QColor

# Detect system dark mode (Windows, macOS, Linux)
def _is_system_dark_mode() -> bool:
    try:
        if sys.platform == "win32":
            import winreg
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            registry_value = "AppsUseLightTheme"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
                value, _ = winreg.QueryValueEx(key, registry_value)
                return value == 0  # 0 = dark, 1 = light
            except Exception:
                return True  # default to dark
        else:
            return True  # default to dark on other platforms
    except Exception:
        return True


IS_DARK_MODE = _is_system_dark_mode()

# ── Material Design 3 Color System ────────────────────────────────────────────
if IS_DARK_MODE:
    # Dark theme colors (YouTube Music style)
    COLOR_PRIMARY = "#FF0000"           # YouTube Red
    COLOR_SECONDARY = "#E91E63"         # Pink (YouTube Music secondary)
    COLOR_TERTIARY = "#00BCD4"          # Cyan
    COLOR_BACKGROUND = "#121212"        # YouTube Music dark background
    COLOR_SURFACE = "#1E1E1E"           # Elevated surface
    COLOR_SURFACE_DIM = "#181818"       # Darker surface
    COLOR_ON_SURFACE = "#FFFFFF"        # White text (more contrast)
    COLOR_ON_SURFACE_VARIANT = "#B3B3B3"  # Light gray text
    COLOR_ERROR = "#FF5252"             # Red
    OVERLAY_LIGHT = "rgba(255, 255, 255, 0.1)"
    OVERLAY_DARK = "rgba(0, 0, 0, 0.3)"
else:
    # Light theme colors
    COLOR_PRIMARY = "#FF0000"           # YouTube Red
    COLOR_SECONDARY = "#FF6B9D"         # Pink
    COLOR_TERTIARY = "#14B8A6"          # Teal
    COLOR_BACKGROUND = "#FFFBFE"        # Off-white
    COLOR_SURFACE = "#FFF8FB"            # Light surface
    COLOR_SURFACE_DIM = "#F5EEF5"        # Dimmed surface
    COLOR_ON_SURFACE = "#1a1a1f"        # Dark text
    COLOR_ON_SURFACE_VARIANT = "#605d66"  # Muted text
    COLOR_ERROR = "#B3261E"             # Dark red
    OVERLAY_LIGHT = "rgba(0, 0, 0, 0.04)"
    OVERLAY_DARK = "rgba(0, 0, 0, 0.12)"

# ── Material Design 3 Typography ─────────────────────────────────────────────
FONT_FAMILY = "'Roboto', 'Segoe UI', sans-serif"
FONT_DISPLAY_LARGE = f"font-size: 32px; font-weight: 400; font-family: {FONT_FAMILY};"
FONT_DISPLAY_MEDIUM = f"font-size: 28px; font-weight: 500; font-family: {FONT_FAMILY};"
FONT_DISPLAY_SMALL = f"font-size: 24px; font-weight: 400; font-family: {FONT_FAMILY};"
FONT_HEADLINE_LARGE = f"font-size: 22px; font-weight: 500; font-family: {FONT_FAMILY};"
FONT_HEADLINE_MEDIUM = f"font-size: 20px; font-weight: 500; font-family: {FONT_FAMILY};"
FONT_HEADLINE_SMALL = f"font-size: 18px; font-weight: 500; font-family: {FONT_FAMILY};"
FONT_TITLE_LARGE = f"font-size: 16px; font-weight: 500; font-family: {FONT_FAMILY};"
FONT_TITLE_MEDIUM = f"font-size: 14px; font-weight: 500; font-family: {FONT_FAMILY};"
FONT_TITLE_SMALL = f"font-size: 12px; font-weight: 500; font-family: {FONT_FAMILY}; letter-spacing: 0.5px;"
FONT_BODY_LARGE = f"font-size: 16px; font-weight: 400; font-family: {FONT_FAMILY}; letter-spacing: 0.5px;"
FONT_BODY_MEDIUM = f"font-size: 14px; font-weight: 400; font-family: {FONT_FAMILY}; letter-spacing: 0.25px;"
FONT_BODY_SMALL = f"font-size: 12px; font-weight: 400; font-family: {FONT_FAMILY}; letter-spacing: 0.4px;"
FONT_LABEL_LARGE = f"font-size: 14px; font-weight: 500; font-family: {FONT_FAMILY}; letter-spacing: 0.1px;"
FONT_LABEL_MEDIUM = f"font-size: 12px; font-weight: 500; font-family: {FONT_FAMILY}; letter-spacing: 0.5px;"
FONT_LABEL_SMALL = f"font-size: 11px; font-weight: 500; font-family: {FONT_FAMILY}; letter-spacing: 0.5px;"

# ── Qt Stylesheet (Material Design 3) ──────────────────────────────────────────
STYLESHEET = f"""
/* ── global ─────────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {COLOR_BACKGROUND};
    color: {COLOR_ON_SURFACE};
    font-family: {FONT_FAMILY};
}}
QMainWindow {{
    background-color: {COLOR_BACKGROUND};
}}

/* ── scroll bars ────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {COLOR_SURFACE_DIM};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_SECONDARY};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_PRIMARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

/* ── line edits (Material Outlined TextField) ──────────────────────────── */
QLineEdit {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_ON_SURFACE_VARIANT};
    border-radius: 12px;
    padding: 12px 16px;
    color: {COLOR_ON_SURFACE};
    {FONT_BODY_LARGE}
    selection-background-color: {COLOR_PRIMARY};
}}
QLineEdit:focus {{
    border: 2px solid {COLOR_PRIMARY};
    padding: 11px 15px;
}}
QLineEdit::placeholder {{
    color: {COLOR_ON_SURFACE_VARIANT};
}}

/* ── push buttons (Material Button) ────────────────────────────────────── */
QPushButton {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_ON_SURFACE_VARIANT};
    border-radius: 20px;
    padding: 10px 24px;
    color: {COLOR_ON_SURFACE};
    {FONT_LABEL_LARGE}
    font-weight: 500;
    outline: none;
}}
QPushButton:hover {{
    background-color: {OVERLAY_LIGHT};
    border-color: {COLOR_ON_SURFACE};
}}
QPushButton:pressed {{
    background-color: {OVERLAY_DARK};
}}

/* ── filled button ──────────────────────────────────────────────────────── */
QPushButton#filledBtn {{
    background-color: {COLOR_PRIMARY};
    border: none;
    border-radius: 24px;
    padding: 12px 24px;
    color: #ffffff;
    {FONT_LABEL_LARGE}
    font-weight: 600;
}}
QPushButton#filledBtn:hover {{
    background-color: {COLOR_SECONDARY};
}}
QPushButton#filledBtn:pressed {{
    background-color: {COLOR_TERTIARY};
    opacity: 0.9;
}}

/* ── icon button ────────────────────────────────────────────────────────── */
QPushButton#iconBtn {{
    background-color: transparent;
    border: none;
    border-radius: 24px;
    padding: 8px;
    color: {COLOR_ON_SURFACE};
    font-size: 20px;
    min-width: 48px;
    min-height: 48px;
}}
QPushButton#iconBtn:hover {{
    background-color: {OVERLAY_LIGHT};
}}
QPushButton#iconBtn:pressed {{
    background-color: {OVERLAY_DARK};
}}

/* ── play button (FAB-like) ──────────────────────────────────────────────── */
QPushButton#playBtn {{
    background-color: {COLOR_PRIMARY};
    border: none;
    border-radius: 28px;
    padding: 8px;
    color: #ffffff;
    font-size: 22px;
    min-width: 56px;
    max-width: 56px;
    min-height: 56px;
    max-height: 56px;
    font-weight: bold;
}}
QPushButton#playBtn:hover {{
    background-color: {COLOR_SECONDARY};
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}}
QPushButton#playBtn:pressed {{
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}}

/* ── small button ──────────────────────────────────────────────────────── */
QPushButton#smallBtn {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_ON_SURFACE_VARIANT};
    border-radius: 8px;
    padding: 6px 12px;
    color: {COLOR_ON_SURFACE_VARIANT};
    {FONT_LABEL_SMALL}
}}
QPushButton#smallBtn:hover {{
    background-color: {OVERLAY_LIGHT};
    color: {COLOR_ON_SURFACE};
    border-color: {COLOR_PRIMARY};
}}

/* ── sliders (Material Slider) ──────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {COLOR_SURFACE_DIM};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {COLOR_PRIMARY};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLOR_PRIMARY};
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
    border: none;
}}
QSlider::handle:horizontal:hover {{
    background: {COLOR_SECONDARY};
    width: 20px;
    height: 20px;
    margin: -8px 0;
}}

/* ── labels ────────────────────────────────────────────────────────────── */
QLabel#appTitle {{
    {FONT_HEADLINE_LARGE}
    color: {COLOR_PRIMARY};
    font-weight: 600;
}}
QLabel#nowTitle {{
    {FONT_TITLE_LARGE}
    color: {COLOR_ON_SURFACE};
    font-weight: 500;
}}
QLabel#nowArtist {{
    {FONT_BODY_MEDIUM}
    color: {COLOR_ON_SURFACE_VARIANT};
}}
QLabel#sectionHeader {{
    {FONT_TITLE_SMALL}
    color: {COLOR_PRIMARY};
    font-weight: 600;
    letter-spacing: 1px;
}}
QLabel#timeLabel {{
    {FONT_BODY_SMALL}
    color: {COLOR_ON_SURFACE_VARIANT};
}}
QLabel#resultTitle {{
    {FONT_BODY_LARGE}
    color: {COLOR_ON_SURFACE};
    font-weight: 500;
}}
QLabel#resultMeta {{
    {FONT_BODY_SMALL}
    color: {COLOR_ON_SURFACE_VARIANT};
}}

/* ── list widgets ──────────────────────────────────────────────────────── */
QListWidget {{
    background-color: {COLOR_BACKGROUND};
    border: none;
    outline: none;
}}
QListWidget::item {{
    border-radius: 8px;
    padding: 0;
    margin: 4px 0;
}}
QListWidget::item:selected {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_PRIMARY};
}}
QListWidget::item:hover {{
    background-color: {OVERLAY_LIGHT};
}}

/* ── frames / cards ────────────────────────────────────────────────────── */
QFrame#playerBar {{
    background-color: {COLOR_SURFACE};
    border-top: 1px solid {COLOR_ON_SURFACE_VARIANT};
    border-radius: 0;
}}
QFrame#sidebar {{
    background-color: {COLOR_SURFACE_DIM};
    border-right: 1px solid {COLOR_ON_SURFACE_VARIANT};
}}
QFrame#searchArea {{
    background-color: {COLOR_SURFACE};
    border-bottom: 1px solid {COLOR_ON_SURFACE_VARIANT};
    padding: 16px;
}}
QFrame#card {{
    background-color: {COLOR_SURFACE};
    border-radius: 12px;
    border: none;
}}

/* ── status bar ────────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {COLOR_SURFACE_DIM};
    color: {COLOR_ON_SURFACE_VARIANT};
    border-top: 1px solid {COLOR_ON_SURFACE_VARIANT};
    {FONT_BODY_SMALL}
}}

/* ── dialogs ───────────────────────────────────────────────────────────── */
QDialog {{
    background-color: {COLOR_SURFACE};
}}
QDialog QLabel {{
    color: {COLOR_ON_SURFACE};
}}
QDialog QLineEdit {{
    background-color: {COLOR_SURFACE_DIM};
    border: 1px solid {COLOR_ON_SURFACE_VARIANT};
}}
"""
