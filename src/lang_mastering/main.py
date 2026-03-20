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


def main(page: ft.Page):
    """Main Flet app entry point."""
    try:
        page.title = "Lang Mastering"
        page.theme = get_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG_COLOR
        page.padding = 0

        # Custom state store (Flet Session has no set/get in 0.82)
        page.app_state = AppState()

        # Database init
        db = Database()
        db.run_migrations()
        page.app_state.set("db", db)

        # Load existing user (if any)
        user_repo = UserRepo(db.conn)
        users = user_repo.get_all()
        if users:
            page.app_state.set("current_user", users[0])

        # Router
        pages = {
            "/": home_page,
            "/learn": learn_page,
            "/review": review_page,
            "/progress": progress_page,
            "/settings": settings_page,
        }
        router = Router(page, pages)
        page.app_state.set("router", router)

        # Navigate to home
        router.navigate("/")

    except Exception:
        page.controls.clear()
        page.add(ft.Text("Error starting app:", size=20, color="red"))
        page.add(ft.Text(traceback.format_exc(), size=12, color="yellow"))
        page.update()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(main, view=None, port=port, host="0.0.0.0")
