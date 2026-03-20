"""Session progress indicator component."""

import flet as ft

from lang_mastering.ui.theme import (
    SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY, ACCENT_COLOR, SUCCESS_COLOR,
)


def build_session_progress(current: int, total: int) -> ft.Container:
    """Build a session progress bar showing current/total cards."""
    progress = current / total if total > 0 else 0

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"Card {current}/{total}", size=14, color=TEXT_SECONDARY),
                ft.Text(f"{int(progress * 100)}%", size=14, color=SUCCESS_COLOR if progress > 0.5 else TEXT_SECONDARY),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ProgressBar(value=progress, color=ACCENT_COLOR, bgcolor=SURFACE_COLOR, height=6),
        ], spacing=4),
        padding=ft.padding.symmetric(horizontal=20, vertical=5),
    )
