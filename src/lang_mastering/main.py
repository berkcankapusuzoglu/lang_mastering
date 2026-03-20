"""Flet app entry point."""

import os
import traceback

import flet as ft

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import UserRepo


BG = "#1a1a2e"
SURFACE = "#16213e"
ACCENT = "#e94560"
WHITE = "#ffffff"
GRAY = "#a0a0b0"


def main(page: ft.Page):
    """Main Flet app entry point."""
    page.title = "Lang Mastering"
    page.bgcolor = BG
    page.padding = 0

    try:
        # Database
        db = Database()
        db.run_migrations()

        # Load user
        user_repo = UserRepo(db.conn)
        users = user_repo.get_all()
        user = users[0] if users else None

        # Build home content
        if user is None:
            home = ft.Column(
                [
                    ft.Icon(ft.Icons.SCHOOL, size=80, color=ACCENT),
                    ft.Text("Welcome to Lang Mastering!", size=28, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Text("Your personal language learning companion", size=16, color=GRAY),
                    ft.Container(height=20),
                    ft.Text("Tap Settings (gear icon) to create your profile", size=14, color=GRAY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
            )
        else:
            home = ft.Column(
                [
                    ft.Text(f"Hello, {user.name}!", size=26, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Text(f"Learning {user.target_language.upper()} · Level {user.current_level}", size=16, color=GRAY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
            )

        # Add content container
        page.add(
            ft.Container(content=home, bgcolor=BG, expand=True, padding=20)
        )

        # Add nav bar
        page.bottom_appbar = ft.BottomAppBar(
            bgcolor=SURFACE,
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.Icons.HOME, icon_color=ACCENT, tooltip="Home"),
                    ft.IconButton(icon=ft.Icons.MENU_BOOK, icon_color=GRAY, tooltip="Learn"),
                    ft.IconButton(icon=ft.Icons.EDIT_NOTE, icon_color=GRAY, tooltip="Review"),
                    ft.IconButton(icon=ft.Icons.BAR_CHART, icon_color=GRAY, tooltip="Progress"),
                    ft.IconButton(icon=ft.Icons.SETTINGS, icon_color=GRAY, tooltip="Settings"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
        )
        page.update()

    except Exception:
        page.add(ft.Text("Error:", size=20, color="red"))
        page.add(ft.Text(traceback.format_exc(), size=12, color="yellow"))
        page.update()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(main, view=None, port=port, host="0.0.0.0")
