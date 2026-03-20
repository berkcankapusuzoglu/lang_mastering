"""Bottom navigation bar component."""

import flet as ft

from lang_mastering.ui.theme import BG_COLOR, SURFACE_COLOR, ACCENT_COLOR, TEXT_SECONDARY


def build_nav_bar(page: ft.Page, selected_index: int = 0) -> ft.BottomAppBar:
    """Build the bottom navigation bar."""
    destinations = [
        {"icon": ft.Icons.HOME_OUTLINED, "selected_icon": ft.Icons.HOME, "label": "Home", "route": "/"},
        {"icon": ft.Icons.MENU_BOOK_OUTLINED, "selected_icon": ft.Icons.MENU_BOOK, "label": "Learn", "route": "/learn"},
        {"icon": ft.Icons.RATE_REVIEW_OUTLINED, "selected_icon": ft.Icons.RATE_REVIEW, "label": "Review", "route": "/review"},
        {"icon": ft.Icons.BAR_CHART_OUTLINED, "selected_icon": ft.Icons.BAR_CHART, "label": "Progress", "route": "/progress"},
        {"icon": ft.Icons.SETTINGS_OUTLINED, "selected_icon": ft.Icons.SETTINGS, "label": "Settings", "route": "/settings"},
    ]

    def on_nav_click(e):
        idx = e.control.data
        page.session.store.get("router").navigate(destinations[idx]["route"])

    buttons = []
    for i, dest in enumerate(destinations):
        is_selected = i == selected_index
        buttons.append(
            ft.IconButton(
                icon=dest["selected_icon"] if is_selected else dest["icon"],
                icon_color=ACCENT_COLOR if is_selected else TEXT_SECONDARY,
                tooltip=dest["label"],
                data=i,
                on_click=on_nav_click,
            )
        )

    return ft.BottomAppBar(
        bgcolor=SURFACE_COLOR,
        content=ft.Row(
            buttons,
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
    )
