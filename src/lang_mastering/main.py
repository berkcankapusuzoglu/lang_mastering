"""Flet app entry point."""

import os
import traceback

import flet as ft

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import UserRepo, VocabRepo, LessonRepo
from lang_mastering.data.seed import seed_all
from lang_mastering.ui.theme import get_theme, BG_COLOR, ACCENT_COLOR, TEXT_COLOR, TEXT_SECONDARY
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
    page.title = "Lang Mastering"

    steps = []
    try:
        steps.append("1. Starting DB init")
        db = Database()
        steps.append("2. DB created")
        db.run_migrations()
        steps.append("3. Migrations done")
        user_repo = UserRepo(db.conn)
        users = user_repo.get_all()
        steps.append(f"4. Users found: {len(users)}")
    except Exception:
        steps.append(f"ERROR: {traceback.format_exc()}")

    # Always render something visible
    page.add(ft.Text("Lang Mastering Debug", size=24, color="white"))
    for s in steps:
        page.add(ft.Text(s, size=14, color="yellow"))
    page.update()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(main, view=None, port=port, host="0.0.0.0")
