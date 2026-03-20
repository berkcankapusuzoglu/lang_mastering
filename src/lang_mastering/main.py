"""Flet app entry point."""

import os
import traceback

import flet as ft

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import UserRepo, VocabRepo, LessonRepo
from lang_mastering.models import User
from lang_mastering.data.seed import seed_all
from lang_mastering.core.srs import SRSEngine
from lang_mastering.core.exercises import ExerciseFactory


BG = "#1a1a2e"
SURFACE = "#16213e"
PRIMARY = "#0f3460"
ACCENT = "#e94560"
WHITE = "#ffffff"
GRAY = "#a0a0b0"
SPANISH = "#ff9800"
TURKISH = "#009688"
GREEN = "#4caf50"
RED = "#f44336"


class AppState:
    """Simple key-value state store."""
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
    page.bgcolor = BG
    page.padding = 0

    try:
        state = AppState()
        page.app_state = state

        # Database
        db = Database()
        db.run_migrations()
        state.set("db", db)

        # Load user
        user_repo = UserRepo(db.conn)
        users = user_repo.get_all()
        if users:
            state.set("current_user", users[0])

        # Current page content ref
        current = [None]

        def set_content(control, nav_idx=0):
            """Replace page content with a new control."""
            if current[0] is not None:
                try:
                    page.controls.remove(current[0])
                except (ValueError, Exception):
                    pass
            current[0] = control
            page.add(control)
            page.bottom_appbar = _nav_bar(nav_idx, navigate)
            page.update()

        def navigate(route):
            """Navigate to a route."""
            try:
                if route == "/":
                    _show_home(page, state, navigate, set_content)
                elif route == "/settings":
                    _show_settings(page, state, db, navigate, set_content)
                elif route == "/learn":
                    _show_learn(page, state, db, navigate, set_content)
                elif route == "/review":
                    _show_review(page, state, db, navigate, set_content)
                elif route == "/progress":
                    _show_progress(page, state, db, set_content)
                else:
                    set_content(_placeholder(route))
            except Exception:
                set_content(ft.Container(
                    content=ft.Text(f"Error: {traceback.format_exc()}", size=12, color=RED),
                    bgcolor=BG, expand=True, padding=20,
                ))

        state.set("navigate", navigate)

        # Start at home
        navigate("/")

    except Exception:
        page.add(ft.Text("Startup error:", size=20, color="red"))
        page.add(ft.Text(traceback.format_exc(), size=12, color="yellow"))
        page.update()


def _nav_bar(active, navigate):
    icons = [
        (ft.Icons.HOME, "Home", "/"),
        (ft.Icons.MENU_BOOK, "Learn", "/learn"),
        (ft.Icons.EDIT_NOTE, "Review", "/review"),
        (ft.Icons.BAR_CHART, "Progress", "/progress"),
        (ft.Icons.SETTINGS, "Settings", "/settings"),
    ]
    buttons = []
    for i, (icon, label, route) in enumerate(icons):
        r = route
        buttons.append(ft.IconButton(
            icon=icon, icon_color=ACCENT if i == active else GRAY,
            tooltip=label, on_click=lambda _, r=r: navigate(r),
        ))
    return ft.BottomAppBar(
        bgcolor=SURFACE,
        content=ft.Row(buttons, alignment=ft.MainAxisAlignment.SPACE_AROUND),
    )


def _placeholder(route):
    return ft.Container(
        content=ft.Column(
            [ft.Text(f"Page: {route}", size=24, color=WHITE),
             ft.Text("Coming soon...", size=16, color=GRAY)],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER, expand=True,
        ), bgcolor=BG, expand=True, padding=20,
    )


def _show_home(page, state, navigate, set_content):
    user = state.get("current_user")
    if user is None:
        content = ft.Column(
            [
                ft.Icon(ft.Icons.SCHOOL, size=80, color=ACCENT),
                ft.Text("Welcome to Lang Mastering!", size=28, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Text("Your personal language learning companion", size=16, color=GRAY),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Get Started", icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda _: navigate("/settings"),
                    style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=200, height=50,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER, expand=True,
        )
    else:
        lang_color = SPANISH if user.target_language == "es" else TURKISH
        lang_name = "Spanish" if user.target_language == "es" else "Turkish"
        content = ft.Column(
            [
                ft.Container(height=10),
                ft.Text(f"Hello, {user.name}!", size=26, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Text(f"Learning {lang_name} · Level {user.current_level}", size=16, color=GRAY),
                ft.Container(height=20),
                ft.Row([
                    _stat_card("Streak", f"{user.streak_days}d", lang_color),
                    _stat_card("XP", str(user.xp), ACCENT),
                    _stat_card("Level", user.current_level, lang_color),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                ft.Container(height=30),
                ft.ElevatedButton(
                    "Start Review", icon=ft.Icons.PLAY_ARROW,
                    on_click=lambda _: navigate("/review"),
                    style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=250, height=55,
                ),
                ft.Container(height=15),
                ft.OutlinedButton(
                    "Browse Lessons", icon=ft.Icons.MENU_BOOK,
                    on_click=lambda _: navigate("/learn"), width=250, height=45,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START, expand=True,
        )
    set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), 0)


def _stat_card(label, value, color):
    return ft.Container(
        content=ft.Column([
            ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=WHITE),
            ft.Text(label, size=12, color=GRAY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        bgcolor=SURFACE, border_radius=12, padding=15, width=100,
    )


def _show_settings(page, state, db, navigate, set_content):
    user = state.get("current_user")
    name_field = ft.TextField(
        label="Your Name", value=user.name if user else "",
        border_color=ACCENT, color=WHITE, label_style=ft.TextStyle(color=GRAY), width=300,
    )
    lang_group = ft.RadioGroup(
        value=user.target_language if user else "es",
        content=ft.Column([
            ft.Radio(value="es", label="Spanish", fill_color=SPANISH, label_style=ft.TextStyle(color=WHITE)),
            ft.Radio(value="tr", label="Turkish", fill_color=TURKISH, label_style=ft.TextStyle(color=WHITE)),
        ]),
    )
    goal_slider = ft.Slider(
        min=5, max=50, divisions=9, value=user.daily_goal if user else 20,
        active_color=ACCENT, width=300,
    )
    goal_text = ft.Text(f"{int(user.daily_goal if user else 20)} cards/day", size=14, color=GRAY)

    def on_slider(e):
        goal_text.value = f"{int(e.control.value)} cards/day"
        goal_text.update()

    goal_slider.on_change = on_slider

    def save(e):
        repo = UserRepo(db.conn)
        if user is None:
            new_user = User(name=name_field.value, target_language=lang_group.value,
                            daily_goal=int(goal_slider.value))
            new_user = repo.create(new_user)
            state.set("current_user", new_user)
            vocab_repo = VocabRepo(db.conn)
            lesson_repo = LessonRepo(db.conn)
            seed_all(vocab_repo, lesson_repo, new_user.target_language)
        else:
            user.name = name_field.value
            user.target_language = lang_group.value
            user.daily_goal = int(goal_slider.value)
            repo.update(user)
            state.set("current_user", user)
        navigate("/")

    content = ft.Column([
        ft.Container(height=10),
        ft.Text("Create Profile" if user is None else "Settings",
                 size=24, weight=ft.FontWeight.BOLD, color=WHITE),
        ft.Container(height=20),
        name_field, ft.Container(height=15),
        ft.Text("I want to learn:", size=16, color=WHITE),
        lang_group, ft.Container(height=15),
        ft.Text("Daily goal:", size=16, color=WHITE),
        goal_slider, goal_text, ft.Container(height=25),
        ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=save,
                           style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=200, height=45),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, expand=True)

    set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), 4)


def _show_learn(page, state, db, navigate, set_content):
    user = state.get("current_user")
    if user is None:
        set_content(ft.Container(
            content=ft.Text("Create a profile first!", size=18, color=GRAY),
            bgcolor=BG, expand=True, padding=20,
        ), 1)
        return

    lesson_repo = LessonRepo(db.conn)
    lessons = lesson_repo.get_by_language(user.target_language)

    rows = [ft.Text("Lessons", size=24, weight=ft.FontWeight.BOLD, color=WHITE), ft.Container(height=10)]
    for lesson in lessons:
        rows.append(ft.Container(
            content=ft.Column([
                ft.Text(lesson.title, size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Text(f"{lesson.cefr_level} · {lesson.category}", size=12, color=GRAY),
            ]),
            bgcolor=SURFACE, border_radius=8, padding=12, margin=ft.margin.only(bottom=8),
        ))

    if not lessons:
        rows.append(ft.Text("No lessons yet. They'll appear after you create a profile.", size=14, color=GRAY))

    content = ft.Column(rows, scroll=ft.ScrollMode.AUTO, expand=True)
    set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), 1)


def _show_review(page, state, db, navigate, set_content):
    user = state.get("current_user")
    if user is None:
        set_content(ft.Container(
            content=ft.Text("Create a profile first!", size=18, color=GRAY),
            bgcolor=BG, expand=True, padding=20,
        ), 2)
        return

    srs = SRSEngine(db)
    cards = srs.get_session_mix(user.id)

    if not cards:
        content = ft.Column([
            ft.Icon(ft.Icons.CHECK_CIRCLE, size=80, color=GREEN),
            ft.Text("All caught up!", size=24, weight=ft.FontWeight.BOLD, color=WHITE),
            ft.Text("No cards due for review right now.", size=16, color=GRAY),
            ft.Container(height=20),
            ft.ElevatedButton("Back to Home", on_click=lambda _: navigate("/"),
                               style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=200),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           alignment=ft.MainAxisAlignment.CENTER, expand=True)
        set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), 2)
        return

    # Review session
    vocab_repo = VocabRepo(db.conn)
    idx = [0]
    correct_count = [0]

    def show_card():
        if idx[0] >= len(cards):
            # Session complete
            total = len(cards)
            acc = int(correct_count[0] / total * 100) if total > 0 else 0
            summary = ft.Column([
                ft.Icon(ft.Icons.CELEBRATION, size=60, color=ACCENT),
                ft.Text("Session Complete!", size=24, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Text(f"{correct_count[0]}/{total} correct ({acc}%)", size=18, color=GRAY),
                ft.Container(height=20),
                ft.ElevatedButton("Back to Home", on_click=lambda _: navigate("/"),
                                   style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER, expand=True)
            set_content(ft.Container(content=summary, bgcolor=BG, expand=True, padding=20), 2)
            return

        card = cards[idx[0]]
        vocab = vocab_repo.get(card.vocabulary_id)
        if vocab is None:
            idx[0] += 1
            show_card()
            return

        # Simple flashcard exercise
        answer_shown = [False]
        answer_col = ft.Column([], visible=False)

        def flip(e):
            if not answer_shown[0]:
                answer_shown[0] = True
                answer_col.controls.append(
                    ft.Text(vocab.translation, size=24, weight=ft.FontWeight.BOLD, color=GREEN)
                )
                answer_col.visible = True
                rating_row.visible = True
                flip_btn.visible = False
                page.update()

        def rate(rating):
            def handler(e):
                from fsrs import Rating
                fsrs_rating = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}[rating]
                srs.review(card, fsrs_rating)
                if rating >= 3:
                    correct_count[0] += 1
                idx[0] += 1
                show_card()
            return handler

        progress_text = ft.Text(f"Card {idx[0]+1} of {len(cards)}", size=14, color=GRAY)
        progress_bar = ft.ProgressBar(
            value=(idx[0]+1)/len(cards), color=ACCENT, bgcolor=SURFACE, width=300,
        )

        flip_btn = ft.ElevatedButton("Show Answer", on_click=flip,
                                      style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE), width=200)

        rating_row = ft.Row([
            ft.ElevatedButton("Again", on_click=rate(1), style=ft.ButtonStyle(bgcolor=RED, color=WHITE)),
            ft.ElevatedButton("Hard", on_click=rate(2), style=ft.ButtonStyle(bgcolor="#ff9800", color=WHITE)),
            ft.ElevatedButton("Good", on_click=rate(3), style=ft.ButtonStyle(bgcolor=GREEN, color=WHITE)),
            ft.ElevatedButton("Easy", on_click=rate(4), style=ft.ButtonStyle(bgcolor="#2196f3", color=WHITE)),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, visible=False)

        card_content = ft.Column([
            progress_text, progress_bar,
            ft.Container(height=30),
            ft.Text(vocab.word, size=32, weight=ft.FontWeight.BOLD, color=WHITE),
            ft.Text(f"({vocab.part_of_speech or 'word'})", size=14, color=GRAY),
            ft.Container(height=10),
            answer_col,
            ft.Container(height=20),
            flip_btn,
            rating_row,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           alignment=ft.MainAxisAlignment.CENTER, expand=True)

        set_content(ft.Container(content=card_content, bgcolor=BG, expand=True, padding=20), 2)

    show_card()


def _show_progress(page, state, db, set_content):
    user = state.get("current_user")
    if user is None:
        set_content(ft.Container(
            content=ft.Text("Create a profile first!", size=18, color=GRAY),
            bgcolor=BG, expand=True, padding=20,
        ), 3)
        return

    from lang_mastering.db.repositories import ReviewLogRepo, CardRepo
    review_repo = ReviewLogRepo(db.conn)
    card_repo = CardRepo(db.conn)

    total_reviews = review_repo.count_by_user(user.id)
    total_cards = card_repo.count_by_user(user.id)

    lang_name = "Spanish" if user.target_language == "es" else "Turkish"
    lang_color = SPANISH if user.target_language == "es" else TURKISH

    content = ft.Column([
        ft.Text("Your Progress", size=24, weight=ft.FontWeight.BOLD, color=WHITE),
        ft.Container(height=20),
        ft.Row([
            _stat_card("Streak", f"{user.streak_days}d", lang_color),
            _stat_card("Reviews", str(total_reviews), ACCENT),
            _stat_card("Cards", str(total_cards), lang_color),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Container(height=20),
        ft.Container(
            content=ft.Column([
                ft.Text(f"Level: {user.current_level}", size=18, color=WHITE),
                ft.Text(f"XP: {user.xp}", size=14, color=GRAY),
                ft.Text(f"Language: {lang_name}", size=14, color=GRAY),
                ft.Text(f"Daily Goal: {user.daily_goal} cards", size=14, color=GRAY),
            ]),
            bgcolor=SURFACE, border_radius=12, padding=20, width=320,
        ),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True, scroll=ft.ScrollMode.AUTO)

    set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), 3)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(main, view=None, port=port, host="0.0.0.0")
