"""End-of-session summary overlay."""

import flet as ft

from lang_mastering.ui.theme import (
    BG_COLOR, SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY,
    ACCENT_COLOR, SUCCESS_COLOR, ERROR_COLOR,
)


def build_session_summary(
    cards_reviewed: int,
    cards_correct: int,
    cards_incorrect: int,
    xp_earned: int,
    time_seconds: int,
    streak_days: int,
    on_close=None,
) -> ft.Container:
    """Build a session summary overlay."""
    accuracy = (cards_correct / cards_reviewed * 100) if cards_reviewed > 0 else 0

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CELEBRATION, size=50, color=ACCENT_COLOR),
            ft.Text("Session Complete!", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    _row("Cards", str(cards_reviewed)),
                    _row("Correct", str(cards_correct), SUCCESS_COLOR),
                    _row("Incorrect", str(cards_incorrect), ERROR_COLOR),
                    _row("Accuracy", f"{accuracy:.0f}%"),
                    _row("XP Earned", f"+{xp_earned}", ACCENT_COLOR),
                    _row("Time", f"{time_seconds // 60}m {time_seconds % 60}s"),
                    _row("Streak", f"\U0001f525 {streak_days} days"),
                ], spacing=8),
                bgcolor=SURFACE_COLOR, border_radius=12, padding=20, width=280,
            ),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Continue",
                on_click=on_close,
                style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                width=180, height=45,
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=BG_COLOR,
        border_radius=16,
        padding=30,
        width=340,
    )


def _row(label: str, value: str, color=TEXT_COLOR) -> ft.Row:
    return ft.Row([
        ft.Text(label, size=15, color=TEXT_SECONDARY),
        ft.Text(value, size=15, weight=ft.FontWeight.BOLD, color=color),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
