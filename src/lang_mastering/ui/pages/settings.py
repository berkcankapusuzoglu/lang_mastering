"""Settings page: profile creation, language picker, daily goal."""

import flet as ft

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import UserRepo, VocabRepo, LessonRepo
from lang_mastering.models import User
from lang_mastering.data.seed import seed_all
from lang_mastering.ui.theme import (
    BG_COLOR, SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY,
    ACCENT_COLOR, SPANISH_COLOR, TURKISH_COLOR,
)


def settings_page(page: ft.Page) -> ft.View:
    """Build the settings page."""
    user = page.session.get("current_user")

    name_field = ft.TextField(
        label="Your Name",
        value=user.name if user else "",
        border_color=ACCENT_COLOR,
        color=TEXT_COLOR,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        width=300,
    )

    language_group = ft.RadioGroup(
        value=user.target_language if user else "es",
        content=ft.Column([
            ft.Radio(value="es", label="Spanish 🇪🇸", fill_color=SPANISH_COLOR, label_style=ft.TextStyle(color=TEXT_COLOR)),
            ft.Radio(value="tr", label="Turkish 🇹🇷", fill_color=TURKISH_COLOR, label_style=ft.TextStyle(color=TEXT_COLOR)),
        ]),
    )

    daily_goal_slider = ft.Slider(
        min=5, max=50, divisions=9,
        value=user.daily_goal if user else 20,
        label="{value} cards/day",
        active_color=ACCENT_COLOR,
        width=300,
    )

    goal_display = ft.Text(
        f"{int(user.daily_goal if user else 20)} cards/day",
        size=14, color=TEXT_SECONDARY,
    )

    def on_slider_change(e):
        goal_display.value = f"{int(e.control.value)} cards/day"
        page.update()

    daily_goal_slider.on_change = on_slider_change

    def save_profile(e):
        db: Database = page.session.get("db")
        repo = UserRepo(db.conn)

        if user is None:
            new_user = User(
                name=name_field.value,
                target_language=language_group.value,
                daily_goal=int(daily_goal_slider.value),
            )
            new_user = repo.create(new_user)
            page.session.set("current_user", new_user)
            # Seed vocabulary data for chosen language
            vocab_repo = VocabRepo(db.conn)
            lesson_repo = LessonRepo(db.conn)
            seed_all(vocab_repo, lesson_repo, new_user.target_language)
        else:
            user.name = name_field.value
            user.target_language = language_group.value
            user.daily_goal = int(daily_goal_slider.value)
            repo.update(user)
            page.session.set("current_user", user)

        page.session.get("router").navigate("/")

    content = ft.Column(
        [
            ft.Container(height=10),
            ft.Text(
                "Create Profile" if user is None else "Settings",
                size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR,
            ),
            ft.Container(height=20),
            name_field,
            ft.Container(height=15),
            ft.Text("I want to learn:", size=16, color=TEXT_COLOR),
            language_group,
            ft.Container(height=15),
            ft.Text("Daily goal:", size=16, color=TEXT_COLOR),
            daily_goal_slider,
            goal_display,
            ft.Container(height=25),
            ft.ElevatedButton(
                "Save",
                icon=ft.Icons.SAVE,
                on_click=save_profile,
                style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                width=200, height=45,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    from lang_mastering.ui.components.nav_bar import build_nav_bar
    return ft.View(
        "/settings",
        [ft.Container(content=content, bgcolor=BG_COLOR, expand=True, padding=20)],
        bgcolor=BG_COLOR,
        bottom_appbar=build_nav_bar(page, 4),
    )
