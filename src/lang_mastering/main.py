"""Flet app entry point."""

import os
import traceback

import flet as ft

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import UserRepo, VocabRepo, LessonRepo
from lang_mastering.data.seed import seed_all
from lang_mastering.ui.theme import get_theme, BG_COLOR
from lang_mastering.ui.router import Router
from lang_mastering.ui.pages.home import home_page
from lang_mastering.ui.pages.learn import learn_page
from lang_mastering.ui.pages.review import review_page
from lang_mastering.ui.pages.progress import progress_page
from lang_mastering.ui.pages.settings import settings_page


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


def _show_error(page: ft.Page, msg: str):
    """Show error without clearing page controls."""
    page.add(ft.Text(f"ERROR: {msg}", size=12, color="red"))
    page.update()


def main(page: ft.Page):
    """Main Flet app entry point."""
    page.title = "Lang Mastering"

    # Show loading immediately (proves page works)
    status = ft.Text("Loading...", size=16, color="yellow")
    page.add(status)
    page.update()

    try:
        page.theme = get_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG_COLOR
        page.padding = 0

        page.app_state = AppState()

        status.value = "Initializing database..."
        status.update()

        db = Database()
        db.run_migrations()
        page.app_state.set("db", db)

        status.value = "Loading user data..."
        status.update()

        user_repo = UserRepo(db.conn)
        users = user_repo.get_all()
        if users:
            page.app_state.set("current_user", users[0])

        status.value = "Setting up router..."
        status.update()

        pages = {
            "/": home_page,
            "/learn": learn_page,
            "/review": review_page,
            "/progress": progress_page,
            "/settings": settings_page,
        }
        router = Router(page, pages)
        page.app_state.set("router", router)

        status.value = "Navigating to home..."
        status.update()

        router.navigate("/")

    except Exception:
        _show_error(page, traceback.format_exc())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(main, view=None, port=port, host="0.0.0.0")
