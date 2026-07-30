"""Light / dark theme selection and shared paint colors."""

from __future__ import annotations

from repomanager.config import app_settings

KEY_THEME = "ui/theme"
THEMES = ("light", "dark")

# Colors used by custom-painted widgets (delegate, loading overlay).
PALETTE = {
    "light": {
        "name": "#1f2a33",
        "muted": "#5c6b76",
        "public": "#1b7f4a",
        "private": "#c62828",
        "accent": "#0d7a6f",
        "overlay_bg": (238, 242, 245, 215),
        "overlay_text": "#14353a",
        "spinner_track": (13, 122, 111, 45),
    },
    "dark": {
        "name": "#e6edf3",
        "muted": "#96a7b3",
        "public": "#4cc38a",
        "private": "#f2726f",
        "accent": "#19b3a6",
        "overlay_bg": (18, 26, 32, 220),
        "overlay_text": "#e6edf3",
        "spinner_track": (25, 179, 166, 60),
    },
}


def get_theme() -> str:
    value = str(app_settings().value(KEY_THEME, "light") or "light").strip().lower()
    return value if value in THEMES else "light"


def set_theme(value: str) -> None:
    value = value.strip().lower()
    if value not in THEMES:
        value = "light"
    settings = app_settings()
    settings.setValue(KEY_THEME, value)
    settings.sync()


def is_dark() -> bool:
    return get_theme() == "dark"


def color(key: str):
    return PALETTE[get_theme()][key]
