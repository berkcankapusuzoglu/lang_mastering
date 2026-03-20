"""Home/Dashboard page: greeting, streak, XP, quick start."""

import flet as ft

from lang_mastering.ui.theme import (
    BG_COLOR, SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY,
    ACCENT_COLOR, get_language_color,
)


def home_page(page: ft.Page) -> ft.View:
    """Build the home/dashboard page."""
    # Get current user from page session
    user = page.session.store.get("current_user")

    if user is None:
        # No user yet - show welcome
        content = ft.Column(
            [
                ft.Icon(ft.Icons.SCHOOL, size=80, color=ACCENT_COLOR),
                ft.Text("Welcome to Lang Mastering!", size=28, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text("Your personal language learning companion", size=16, color=TEXT_SECONDARY),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Get Started",
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda _: page.session.store.get("router").navigate("/settings"),
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

        content = ft.Column(
            [
                ft.Container(height=10),
                ft.Text(f"Hello, {user.name}!", size=26, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text(f"Learning {lang_name} · Level {user.current_level}", size=16, color=TEXT_SECONDARY),
                ft.Container(height=20),
                # Stats row
                ft.Row(
                    [
                        _stat_card("🔥", "Streak", f"{user.streak_days} days", lang_color),
                        _stat_card("⭐", "XP", str(user.xp), ACCENT_COLOR),
                        _stat_card("📊", "Level", user.current_level, lang_color),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=15,
                ),
                ft.Container(height=30),
                # Quick start button
                ft.ElevatedButton(
                    "Start Review",
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=lambda _: page.session.store.get("router").navigate("/review"),
                    style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                    width=250, height=55,
                ),
                ft.Container(height=15),
                ft.OutlinedButton(
                    "Browse Lessons",
                    icon=ft.Icons.MENU_BOOK,
                    on_click=lambda _: page.session.store.get("router").navigate("/learn"),
                    width=250, height=45,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )

    from lang_mastering.ui.components.nav_bar import build_nav_bar
    return ft.View(
        "/",
        [
            ft.Container(
                content=content,
                bgcolor=BG_COLOR,
                expand=True,
                padding=20,
            ),
        ],
        bgcolor=BG_COLOR,
        bottom_appbar=build_nav_bar(page, 0),
    )


def _stat_card(emoji: str, label: str, value: str, color) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(emoji, size=24),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text(label, size=12, color=TEXT_SECONDARY),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        bgcolor=SURFACE_COLOR,
        border_radius=12,
        padding=15,
        width=100,
    )
