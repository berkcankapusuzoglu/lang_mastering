"""Flet app entry point."""

import os
import traceback

import flet as ft

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import UserRepo, VocabRepo, LessonRepo
from lang_mastering.data.seed import seed_all
from lang_mastering.ui.theme import BG_COLOR, SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY, ACCENT_COLOR, get_language_color
from lang_mastering.ui.pages.settings import settings_page
from lang_mastering.ui.pages.learn import learn_page
from lang_mastering.ui.pages.review import review_page
from lang_mastering.ui.pages.progress import progress_page


class AppState:
    """Simple key-value state store attached to each page session."""
    def __init__(self):
        self._data = {}
    def set(self, key, value):
        self._data[key] = value
    def get(self, key):
        return self._data.get(key)
    def contains_key(self, key):
        return key in self._data
    def remove(self, key):
        self._data.pop(key, None)


def _build_nav_bar(page, active_index, navigate_fn):
    """Build bottom navigation bar."""
    def make_nav(route, idx):
        def handler(e):
            navigate_fn(route)
        return handler

    icons = [
        (ft.Icons.HOME, "Home", "/"),
        (ft.Icons.MENU_BOOK, "Learn", "/learn"),
        (ft.Icons.EDIT_NOTE, "Review", "/review"),
        (ft.Icons.BAR_CHART, "Progress", "/progress"),
        (ft.Icons.SETTINGS, "Settings", "/settings"),
    ]

    buttons = []
    for i, (icon, label, route) in enumerate(icons):
        color = ACCENT_COLOR if i == active_index else TEXT_SECONDARY
        buttons.append(
            ft.IconButton(
                icon=icon,
                icon_color=color,
                tooltip=label,
                on_click=make_nav(route, i),
            )
        )

    return ft.BottomAppBar(
        bgcolor=SURFACE_COLOR,
        content=ft.Row(buttons, alignment=ft.MainAxisAlignment.SPACE_AROUND),
    )


def _build_home(page, navigate_fn):
    """Build home page content directly (no View)."""
    user = page.app_state.get("current_user")

    if user is None:
        content = ft.Column(
            [
                ft.Icon(ft.Icons.SCHOOL, size=80, color=ACCENT_COLOR),
                ft.Text("Welcome to Lang Mastering!", size=28, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text("Your personal language learning companion", size=16, color=TEXT_SECONDARY),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Get Started",
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda _: navigate_fn("/settings"),
                    style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                    width=200, height=50,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    else:
        lang_color = get_language_color(user.target_language)
        lang_names = {"es": "Spanish", "tr": "Turkish"}
        lang_name = lang_names.get(user.target_language, user.target_language.upper())

        def stat_card(emoji, label, value, color):
            return ft.Container(
                content=ft.Column(
                    [ft.Text(emoji, size=24), ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR), ft.Text(label, size=12, color=TEXT_SECONDARY)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
                ),
                bgcolor=SURFACE_COLOR, border_radius=12, padding=15, width=100,
            )

        content = ft.Column(
            [
                ft.Container(height=10),
                ft.Text(f"Hello, {user.name}!", size=26, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text(f"Learning {lang_name} · Level {user.current_level}", size=16, color=TEXT_SECONDARY),
                ft.Container(height=20),
                ft.Row(
                    [stat_card("fire", "Streak", f"{user.streak_days} days", lang_color),
                     stat_card("star", "XP", str(user.xp), ACCENT_COLOR),
                     stat_card("chart", "Level", user.current_level, lang_color)],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=15,
                ),
                ft.Container(height=30),
                ft.ElevatedButton(
                    "Start Review", icon=ft.Icons.PLAY_ARROW,
                    on_click=lambda _: navigate_fn("/review"),
                    style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                    width=250, height=55,
                ),
                ft.Container(height=15),
                ft.OutlinedButton(
                    "Browse Lessons", icon=ft.Icons.MENU_BOOK,
                    on_click=lambda _: navigate_fn("/learn"),
                    width=250, height=45,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )

    return ft.Container(content=content, bgcolor=BG_COLOR, expand=True, padding=20)


def main(page: ft.Page):
    """Main Flet app entry point."""
    page.title = "Lang Mastering"
    page.bgcolor = BG_COLOR
    page.padding = 0

    try:
        page.app_state = AppState()

        # Database
        db = Database()
        db.run_migrations()
        page.app_state.set("db", db)

        # Load existing user
        user_repo = UserRepo(db.conn)
        users = user_repo.get_all()
        if users:
            page.app_state.set("current_user", users[0])

        # Simple navigate function
        current_content = [None]  # mutable ref

        def navigate(route):
            # Remove old content
            if current_content[0] is not None:
                try:
                    page.controls.remove(current_content[0])
                except (ValueError, Exception):
                    pass

            # Build new content
            if route == "/":
                new_content = _build_home(page, navigate)
                nav_idx = 0
            elif route == "/settings":
                # Use settings page View, extract content
                try:
                    view = settings_page(page)
                    new_content = ft.Container(
                        content=ft.Column(
                            [c for c in view.controls] if hasattr(view, 'controls') else [view],
                            expand=True, spacing=0,
                        ),
                        bgcolor=BG_COLOR, expand=True,
                    )
                except Exception:
                    new_content = ft.Container(
                        content=ft.Text(f"Settings error: {traceback.format_exc()}", color="red"),
                        bgcolor=BG_COLOR, expand=True,
                    )
                nav_idx = 4
            else:
                new_content = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"Page: {route}", size=24, color=TEXT_COLOR),
                            ft.Text("Coming soon...", size=16, color=TEXT_SECONDARY),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=True,
                    ),
                    bgcolor=BG_COLOR, expand=True, padding=20,
                )
                nav_idx = {"/learn": 1, "/review": 2, "/progress": 3}.get(route, 0)

            current_content[0] = new_content
            page.add(new_content)
            page.bottom_appbar = _build_nav_bar(page, nav_idx, navigate)
            page.update()

        # Store navigate function in app_state for other pages
        page.app_state.set("router_navigate", navigate)

        # Start at home
        navigate("/")

    except Exception:
        page.add(ft.Text("Error:", size=20, color="red"))
        page.add(ft.Text(traceback.format_exc(), size=12, color="yellow"))
        page.update()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(main, view=None, port=port, host="0.0.0.0")
