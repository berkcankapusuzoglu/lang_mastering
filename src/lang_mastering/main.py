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
        page.app_state = AppState()
        page.title = "Lang Mastering"
        page.theme = get_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG_COLOR

        # Only set window size for desktop mode
        is_web = getattr(page, "web", True)
        if not is_web:
            page.window.width = 420
            page.window.height = 750

        # Initialize database
        db = Database()
        db.run_migrations()
        page.app_state.set("db", db)

        # Load existing user (if any)
        user_repo = UserRepo(db.conn)
        users = user_repo.get_all()
        if users:
            page.app_state.set("current_user", users[0])
            # Seed data for user's language
            vocab_repo = VocabRepo(db.conn)
            lesson_repo = LessonRepo(db.conn)
            seed_all(vocab_repo, lesson_repo, users[0].target_language)

        # Set up routes
        pages = {
            "/": home_page,
            "/learn": learn_page,
            "/review": review_page,
            "/progress": progress_page,
            "/settings": settings_page,
        }

        router = Router(page, pages)
        page.app_state.set("router", router)
        router.navigate("/")
    except Exception:
        traceback.print_exc()
        page.controls.clear()
        page.controls.append(ft.Text(f"Error: {traceback.format_exc()}", color="red"))
        page.update()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(main, view=None, port=port, host="0.0.0.0")
