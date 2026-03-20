"""Material 3 theme configuration with language-specific accent colors."""

import flet as ft


# Language accent colors
SPANISH_COLOR = "#ff9800"
TURKISH_COLOR = "#009688"

# Common colors
BG_COLOR = "#1a1a2e"
SURFACE_COLOR = "#16213e"
PRIMARY_COLOR = "#0f3460"
ACCENT_COLOR = "#e94560"
TEXT_COLOR = "#ffffff"
TEXT_SECONDARY = "#a0a0b0"
SUCCESS_COLOR = "#4caf50"
ERROR_COLOR = "#f44336"
WARNING_COLOR = "#ff9800"


def get_theme(dark_mode: bool = True) -> ft.Theme:
    """Get the app theme."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            background=BG_COLOR,
            surface=BG_COLOR,
            surface_variant=SURFACE_COLOR,
            on_background=TEXT_COLOR,
            on_surface=TEXT_COLOR,
            primary=ACCENT_COLOR,
            on_primary=TEXT_COLOR,
            secondary=PRIMARY_COLOR,
            on_secondary=TEXT_COLOR,
        ),
        visual_density=ft.VisualDensity.COMFORTABLE,
    )


def get_language_color(language: str) -> str:
    """Get accent color for a language."""
    if language == "es":
        return SPANISH_COLOR
    elif language == "tr":
        return TURKISH_COLOR
    return ACCENT_COLOR
