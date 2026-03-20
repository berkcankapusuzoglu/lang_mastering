"""Lesson browser page: CEFR level accordions, progress bars, lock/unlock."""

import json

import flet as ft

from lang_mastering.core.content import ContentManager, CEFR_ORDER
from lang_mastering.db.repositories import VocabRepo, LessonRepo, CardRepo
from lang_mastering.ui.theme import (
    BG_COLOR, SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY,
    ACCENT_COLOR, SUCCESS_COLOR, get_language_color,
)


def learn_page(page: ft.Page) -> ft.View:
    """Build the lesson browser page."""
    user = page.session.store.get("current_user")
    db = page.session.store.get("db")

    if user is None:
        from lang_mastering.ui.components.nav_bar import build_nav_bar
        return ft.View(
            "/learn",
            [ft.Container(
                content=ft.Column([
                    ft.Text("Please create a profile first", size=18, color=TEXT_SECONDARY),
                    ft.ElevatedButton("Go to Settings", on_click=lambda _: page.session.store.get("router").navigate("/settings")),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                bgcolor=BG_COLOR, expand=True, padding=20,
            )],
            bgcolor=BG_COLOR,
            bottom_appbar=build_nav_bar(page, 1),
        )

    vocab_repo = VocabRepo(db.conn)
    lesson_repo = LessonRepo(db.conn)
    card_repo = CardRepo(db.conn)
    content_mgr = ContentManager(vocab_repo, lesson_repo, card_repo)

    lang_color = get_language_color(user.target_language)
    lessons_by_level = content_mgr.get_lessons(user.target_language)

    level_panels = []
    for level in CEFR_ORDER:
        lessons = lessons_by_level.get(level, [])
        if not lessons:
            continue

        is_unlocked = content_mgr.is_level_unlocked(user.id, user.target_language, level)
        vocab_count = content_mgr.get_vocab_count(user.target_language, level)

        lesson_tiles = []
        for lesson in lessons:
            progress = content_mgr.get_lesson_progress(user.id, lesson, user.target_language)
            exercise_types = content_mgr.get_lesson_exercise_types(lesson)
            lesson_vocab = content_mgr.get_lesson_vocab(user.target_language, lesson.category, lesson.cefr_level)

            def start_lesson(e, les=lesson):
                page.session.store.set("current_lesson", les)
                page.session.store.get("router").navigate("/review")

            lesson_tiles.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(lesson.title, size=16, weight=ft.FontWeight.W_600, color=TEXT_COLOR, expand=True),
                            ft.Text(f"{int(progress * 100)}%", size=14, color=SUCCESS_COLOR if progress > 0 else TEXT_SECONDARY),
                        ]),
                        ft.ProgressBar(value=progress, color=lang_color, bgcolor=BG_COLOR, height=4),
                        ft.Row([
                            ft.Text(f"{len(lesson_vocab)} words", size=12, color=TEXT_SECONDARY),
                            ft.Text(" · ".join(exercise_types[:3]), size=11, color=TEXT_SECONDARY),
                        ]),
                    ], spacing=6),
                    bgcolor=SURFACE_COLOR,
                    border_radius=8,
                    padding=12,
                    on_click=start_lesson if is_unlocked else None,
                    opacity=1.0 if is_unlocked else 0.5,
                )
            )

        header = ft.Row([
            ft.Text(level, size=20, weight=ft.FontWeight.BOLD, color=lang_color),
            ft.Text(f"{vocab_count} words", size=14, color=TEXT_SECONDARY),
            ft.Icon(
                ft.Icons.LOCK_OPEN if is_unlocked else ft.Icons.LOCK,
                color=SUCCESS_COLOR if is_unlocked else TEXT_SECONDARY,
                size=18,
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        level_panels.append(
            ft.Container(
                content=ft.Column([header, *lesson_tiles], spacing=8),
                padding=ft.padding.only(bottom=20),
            )
        )

    content = ft.Column(
        [
            ft.Container(height=10),
            ft.Text("Lessons", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Container(height=10),
            *level_panels,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    from lang_mastering.ui.components.nav_bar import build_nav_bar
    return ft.View(
        "/learn",
        [ft.Container(content=content, bgcolor=BG_COLOR, expand=True, padding=20)],
        bgcolor=BG_COLOR,
        bottom_appbar=build_nav_bar(page, 1),
    )
