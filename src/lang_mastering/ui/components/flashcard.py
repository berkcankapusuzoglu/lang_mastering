"""Flip card component with audio support."""

import flet as ft

from lang_mastering.ui.theme import (
    SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY, ACCENT_COLOR,
    SUCCESS_COLOR, ERROR_COLOR, get_language_color,
)


def build_flashcard(
    front_text: str,
    back_text: str,
    hint_text: str = "",
    language: str = "es",
    on_flip=None,
) -> ft.Container:
    """Build a flip-card component.

    Returns a Container with the card. Call the returned on_flip to toggle.
    """
    lang_color = get_language_color(language)
    is_flipped = {"value": False}

    front_content = ft.Column(
        [
            ft.Text(front_text, size=32, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
            ft.Container(height=10),
            ft.Text(hint_text, size=14, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER, italic=True) if hint_text else ft.Container(),
            ft.Container(height=20),
            ft.Text("Tap to flip", size=12, color=TEXT_SECONDARY),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    back_content = ft.Column(
        [
            ft.Text(back_text, size=28, weight=ft.FontWeight.BOLD, color=lang_color, text_align=ft.TextAlign.CENTER),
            ft.Container(height=10),
            ft.Text(front_text, size=16, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    card_content = ft.Container(
        content=front_content,
        bgcolor=SURFACE_COLOR,
        border_radius=16,
        padding=30,
        width=350,
        height=250,
        alignment=ft.alignment.center,
    )

    def flip(e):
        is_flipped["value"] = not is_flipped["value"]
        card_content.content = back_content if is_flipped["value"] else front_content
        card_content.update()
        if on_flip:
            on_flip(is_flipped["value"])

    card_content.on_click = flip
    return card_content


def build_rating_buttons(on_rate) -> ft.Row:
    """Build FSRS rating buttons (Again/Hard/Good/Easy)."""
    ratings = [
        (1, "Again", ERROR_COLOR),
        (2, "Hard", "#ff9800"),
        (3, "Good", SUCCESS_COLOR),
        (4, "Easy", "#2196f3"),
    ]

    buttons = []
    for rating, label, color in ratings:
        buttons.append(
            ft.ElevatedButton(
                text=label,
                on_click=lambda e, r=rating: on_rate(r),
                style=ft.ButtonStyle(bgcolor=color, color=TEXT_COLOR),
                width=80,
                height=40,
            )
        )

    return ft.Row(buttons, alignment=ft.MainAxisAlignment.CENTER, spacing=8)
