"""Streak display component."""

import flet as ft

from lang_mastering.ui.theme import TEXT_COLOR, TEXT_SECONDARY, ACCENT_COLOR


def build_streak_display(streak_days: int, size: str = "medium") -> ft.Row:
    """Build a streak display with flame icon.

    Args:
        streak_days: Number of consecutive days
        size: "small", "medium", or "large"
    """
    sizes = {
        "small": (16, 14),
        "medium": (24, 20),
        "large": (36, 32),
    }
    icon_size, text_size = sizes.get(size, sizes["medium"])

    color = ACCENT_COLOR if streak_days > 0 else TEXT_SECONDARY

    return ft.Row([
        ft.Text("\U0001f525", size=icon_size),
        ft.Text(
            str(streak_days),
            size=text_size,
            weight=ft.FontWeight.BOLD,
            color=color,
        ),
    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
