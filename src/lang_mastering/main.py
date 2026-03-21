"""Flet app entry point."""

import json
import os
import random
import traceback

import flet as ft

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import (
    UserRepo, VocabRepo, LessonRepo, CardRepo, ReviewLogRepo, ProgressRepo,
)
from lang_mastering.models import User
from lang_mastering.data.seed import seed_all
from lang_mastering.core.srs import SRSEngine
from lang_mastering.core.exercises import ExerciseFactory
from lang_mastering.core.gamification import (
    GamificationEngine, ACHIEVEMENTS, LEVEL_THRESHOLDS, XP_PER_RATING,
)


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
BLUE = "#2196f3"
GOLD = "#ffd700"


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


def _stat_card(label, value, color):
    return ft.Container(
        content=ft.Column([
            ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=WHITE),
            ft.Text(label, size=12, color=GRAY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        bgcolor=SURFACE, border_radius=12, padding=15, width=100,
    )


# ── Helpers ──────────────────────────────────────────────────────────

def _get_lang_color(user):
    return SPANISH if user.target_language == "es" else TURKISH


def _get_lang_name(user):
    return "Spanish" if user.target_language == "es" else "Turkish"


def _get_card_maturity(card_record):
    """Return (label, color) for a card's FSRS state."""
    data = json.loads(card_record.fsrs_card_json)
    if data.get("last_review") is None and data.get("step", 0) == 0:
        return "New", GRAY
    stability = data.get("stability", 0)
    if stability < 1:
        return "Learning", RED
    elif stability < 7:
        return "Young", SPANISH
    else:
        return "Mature", GREEN


def _gamification_engine(db, user):
    """Create a GamificationEngine for the user."""
    return GamificationEngine(
        UserRepo(db.conn), ProgressRepo(db.conn), ReviewLogRepo(db.conn)
    )


def _build_exercise_ui(page, exercise, vocab, lang_color, on_done):
    """Build Flet controls for any exercise type. Calls on_done(rating) when complete."""
    etype = exercise.exercise_type

    # ── MCQ ──
    if etype == "mcq" and exercise.options:
        feedback_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)
        option_col = ft.Column([], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)

        def pick(e, choice):
            result = exercise.check_answer(choice)
            feedback_text.value = result.feedback
            feedback_text.color = GREEN if result.is_correct else RED
            # Disable buttons
            for ctrl in option_col.controls:
                ctrl.disabled = True
            page.update()
            import threading
            threading.Timer(1.2, lambda: on_done(result.suggested_rating)).start()

        for opt in exercise.options:
            o = opt
            option_col.controls.append(
                ft.ElevatedButton(
                    o, width=280, height=45,
                    on_click=lambda e, c=o: pick(e, c),
                    style=ft.ButtonStyle(bgcolor=SURFACE, color=WHITE),
                )
            )

        return ft.Column([
            ft.Text("Choose the correct translation:", size=14, color=GRAY, text_align=ft.TextAlign.CENTER),
            ft.Container(height=5),
            ft.Text(exercise.prompt, size=28, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            option_col,
            ft.Container(height=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)

    # ── Typing ──
    if etype == "typing":
        answer_field = ft.TextField(
            label="Type the word", border_color=lang_color, color=WHITE,
            label_style=ft.TextStyle(color=GRAY), width=280, text_align=ft.TextAlign.CENTER,
        )
        feedback_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)

        def submit(e):
            result = exercise.check_answer(answer_field.value or "")
            feedback_text.value = result.feedback
            feedback_text.color = GREEN if result.is_correct else RED
            answer_field.disabled = True
            page.update()
            import threading
            threading.Timer(1.5, lambda: on_done(result.suggested_rating)).start()

        return ft.Column([
            ft.Text("Type the translation:", size=14, color=GRAY, text_align=ft.TextAlign.CENTER),
            ft.Container(height=5),
            ft.Text(exercise.prompt, size=28, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            answer_field,
            ft.Container(height=10),
            ft.ElevatedButton("Check", on_click=submit, style=ft.ButtonStyle(bgcolor=lang_color, color=WHITE), width=200),
            ft.Container(height=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)

    # ── Cloze ──
    if etype == "cloze":
        answer_field = ft.TextField(
            label="Fill in the blank", border_color=lang_color, color=WHITE,
            label_style=ft.TextStyle(color=GRAY), width=280, text_align=ft.TextAlign.CENTER,
        )
        feedback_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)

        def submit(e):
            result = exercise.check_answer(answer_field.value or "")
            feedback_text.value = result.feedback
            feedback_text.color = GREEN if result.is_correct else RED
            answer_field.disabled = True
            page.update()
            import threading
            threading.Timer(1.5, lambda: on_done(result.suggested_rating)).start()

        return ft.Column([
            ft.Text("Fill in the blank:", size=14, color=GRAY, text_align=ft.TextAlign.CENTER),
            ft.Container(height=5),
            ft.Text(exercise.prompt, size=20, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
            ft.Text(f"Hint: {exercise.hint}", size=12, color=GRAY, text_align=ft.TextAlign.CENTER),
            ft.Container(height=15),
            answer_field,
            ft.Container(height=10),
            ft.ElevatedButton("Check", on_click=submit, style=ft.ButtonStyle(bgcolor=lang_color, color=WHITE), width=200),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)

    # ── Sentence Building ──
    if etype == "sentence_building" and exercise.options:
        selected_words = []
        word_display = ft.Text("", size=18, color=WHITE, text_align=ft.TextAlign.CENTER)
        feedback_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)
        word_buttons_row = ft.Row([], wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=6)

        available = list(exercise.options)

        def tap_word(e, w):
            selected_words.append(w)
            word_display.value = " ".join(selected_words)
            # Rebuild buttons
            word_buttons_row.controls.clear()
            remaining = list(exercise.options)
            for sw in selected_words:
                if sw in remaining:
                    remaining.remove(sw)
            for rw in remaining:
                r = rw
                word_buttons_row.controls.append(
                    ft.ElevatedButton(r, on_click=lambda e, w=r: tap_word(e, w),
                                       style=ft.ButtonStyle(bgcolor=SURFACE, color=WHITE))
                )
            page.update()

        def check_order(e):
            result = exercise.check_answer(" ".join(selected_words))
            feedback_text.value = result.feedback
            feedback_text.color = GREEN if result.is_correct else RED
            page.update()
            import threading
            threading.Timer(1.5, lambda: on_done(result.suggested_rating)).start()

        def reset_words(e):
            selected_words.clear()
            word_display.value = ""
            word_buttons_row.controls.clear()
            for rw in exercise.options:
                r = rw
                word_buttons_row.controls.append(
                    ft.ElevatedButton(r, on_click=lambda e, w=r: tap_word(e, w),
                                       style=ft.ButtonStyle(bgcolor=SURFACE, color=WHITE))
                )
            page.update()

        # Initial buttons
        for w in exercise.options:
            wd = w
            word_buttons_row.controls.append(
                ft.ElevatedButton(wd, on_click=lambda e, w=wd: tap_word(e, w),
                                   style=ft.ButtonStyle(bgcolor=SURFACE, color=WHITE))
            )

        return ft.Column([
            ft.Text("Arrange the words:", size=14, color=GRAY, text_align=ft.TextAlign.CENTER),
            ft.Text(exercise.prompt, size=16, color=WHITE, text_align=ft.TextAlign.CENTER),
            ft.Container(height=10),
            ft.Container(
                content=word_display, bgcolor=PRIMARY, border_radius=8,
                padding=15, width=320, min_height=50,
            ),
            ft.Container(height=10),
            word_buttons_row,
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("Check", on_click=check_order, style=ft.ButtonStyle(bgcolor=lang_color, color=WHITE)),
                ft.OutlinedButton("Reset", on_click=reset_words),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)

    # ── Language-specific: Vowel Harmony / Ser-Estar / Gender (MCQ-style with options) ──
    if exercise.options and etype in ("vowel_harmony", "gender", "ser_estar"):
        feedback_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)
        btn_row = ft.Row([], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        def pick_opt(e, choice):
            result = exercise.check_answer(choice)
            feedback_text.value = result.feedback
            feedback_text.color = GREEN if result.is_correct else RED
            for ctrl in btn_row.controls:
                ctrl.disabled = True
            page.update()
            import threading
            threading.Timer(1.5, lambda: on_done(result.suggested_rating)).start()

        for opt in exercise.options:
            o = opt
            btn_row.controls.append(
                ft.ElevatedButton(o, width=140, height=45,
                                   on_click=lambda e, c=o: pick_opt(e, c),
                                   style=ft.ButtonStyle(bgcolor=SURFACE, color=WHITE))
            )

        return ft.Column([
            ft.Text(exercise.prompt, size=22, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
            ft.Text(exercise.hint, size=12, color=GRAY, text_align=ft.TextAlign.CENTER) if exercise.hint else ft.Container(),
            ft.Container(height=20),
            btn_row,
            ft.Container(height=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)

    # ── Typing-based language drills (conjugation, suffix_stacking) ──
    if etype in ("conjugation", "suffix_stacking"):
        answer_field = ft.TextField(
            label="Type your answer", border_color=lang_color, color=WHITE,
            label_style=ft.TextStyle(color=GRAY), width=280, text_align=ft.TextAlign.CENTER,
        )
        feedback_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)

        def submit(e):
            result = exercise.check_answer(answer_field.value or "")
            feedback_text.value = result.feedback
            feedback_text.color = GREEN if result.is_correct else RED
            answer_field.disabled = True
            page.update()
            import threading
            threading.Timer(1.5, lambda: on_done(result.suggested_rating)).start()

        prompt_lines = exercise.prompt.split("\n")
        prompt_controls = [ft.Text(line, size=18 if i == 0 else 14,
                                    weight=ft.FontWeight.BOLD if i == 0 else None,
                                    color=WHITE if i == 0 else GRAY, text_align=ft.TextAlign.CENTER)
                           for i, line in enumerate(prompt_lines)]

        return ft.Column([
            *prompt_controls,
            ft.Container(height=15),
            answer_field,
            ft.Container(height=10),
            ft.ElevatedButton("Check", on_click=submit, style=ft.ButtonStyle(bgcolor=lang_color, color=WHITE), width=200),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)

    # ── Default: Flashcard (L2→L1 or L1→L2) ──
    answer_shown = [False]
    answer_col = ft.Column([], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    flip_btn = ft.ElevatedButton("Show Answer", style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE), width=200)
    rating_row = ft.Row([
        ft.ElevatedButton("Again", on_click=lambda _: on_done(1), style=ft.ButtonStyle(bgcolor=RED, color=WHITE)),
        ft.ElevatedButton("Hard", on_click=lambda _: on_done(2), style=ft.ButtonStyle(bgcolor="#ff9800", color=WHITE)),
        ft.ElevatedButton("Good", on_click=lambda _: on_done(3), style=ft.ButtonStyle(bgcolor=GREEN, color=WHITE)),
        ft.ElevatedButton("Easy", on_click=lambda _: on_done(4), style=ft.ButtonStyle(bgcolor=BLUE, color=WHITE)),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, visible=False)

    def flip(e):
        if not answer_shown[0]:
            answer_shown[0] = True
            answer_col.controls.append(
                ft.Text(exercise.correct_answer, size=24, weight=ft.FontWeight.BOLD, color=GREEN, text_align=ft.TextAlign.CENTER)
            )
            if vocab and vocab.example_sentence:
                answer_col.controls.append(ft.Container(height=8))
                answer_col.controls.append(
                    ft.Text(vocab.example_sentence, size=13, color=GRAY, italic=True, text_align=ft.TextAlign.CENTER)
                )
                answer_col.controls.append(
                    ft.Text(vocab.example_translation, size=12, color=GRAY, text_align=ft.TextAlign.CENTER)
                )
            answer_col.visible = True
            rating_row.visible = True
            flip_btn.visible = False
            page.update()

    flip_btn.on_click = flip

    return ft.Column([
        ft.Text(exercise.prompt, size=32, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
        ft.Text(f"({vocab.part_of_speech or 'word'})" if vocab else "", size=14, color=GRAY),
        ft.Text(vocab.phonetic if vocab and vocab.phonetic else "", size=12, color=GRAY),
        ft.Container(height=10),
        answer_col,
        ft.Container(height=20),
        flip_btn,
        rating_row,
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)


def _create_exercise_for_card(vocab, exercise_type, all_vocab, language):
    """Create an Exercise object based on type, including language-specific drills."""
    # Language-specific exercises
    if exercise_type == "vowel_harmony" and language == "tr":
        from lang_mastering.core.language_specific.turkish import VowelHarmonyExercise
        return VowelHarmonyExercise()
    if exercise_type == "suffix" and language == "tr":
        from lang_mastering.core.language_specific.turkish import SuffixStackingExercise
        return SuffixStackingExercise()
    if exercise_type == "sov_word_order" and language == "tr":
        from lang_mastering.core.language_specific.turkish import SOVWordOrderExercise
        return SOVWordOrderExercise()
    if exercise_type == "conjugation" and language == "es":
        from lang_mastering.core.language_specific.spanish import VerbConjugationExercise
        return VerbConjugationExercise.random()
    if exercise_type == "ser_estar" and language == "es":
        from lang_mastering.core.language_specific.spanish import SerEstarExercise
        return SerEstarExercise()
    if exercise_type == "gender" and language == "es":
        from lang_mastering.core.language_specific.spanish import GenderAgreementExercise
        return GenderAgreementExercise()

    # Standard exercises
    factory = ExerciseFactory(all_vocab)
    return factory.create(vocab, exercise_type)


def _pick_exercise_type(lesson_exercise_types, language):
    """Pick a random exercise type from the lesson's available types."""
    # Filter to types we can actually render
    renderable = {
        "flashcard_l2l1", "flashcard_l1l2", "mcq", "typing", "cloze",
        "sentence_building",
        "vowel_harmony", "suffix", "conjugation", "ser_estar", "gender",
        "suffix_stacking", "sov_word_order",
    }
    available = [t for t in lesson_exercise_types if t in renderable]
    if not available:
        available = ["flashcard_l2l1"]
    return random.choice(available)


# ── Session Summary with XP ──────────────────────────────────────────

def _show_session_summary(page, state, db, set_content, navigate, nav_idx,
                          correct_count, total, xp_earned, new_achievements, title="Session Complete!"):
    """Show a rich session summary with XP, achievements, and stats."""
    user = state.get("current_user")
    lang_color = _get_lang_color(user)
    acc = int(correct_count / total * 100) if total > 0 else 0

    rows = [
        ft.Icon(ft.Icons.CELEBRATION, size=60, color=lang_color),
        ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=WHITE),
        ft.Container(height=10),
        ft.Text(f"{correct_count}/{total} correct ({acc}%)", size=18, color=GRAY),
    ]

    # XP earned
    if xp_earned > 0:
        rows.append(ft.Container(height=10))
        rows.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.STAR, color=GOLD, size=20),
                ft.Text(f"+{xp_earned} XP", size=18, weight=ft.FontWeight.BOLD, color=GOLD),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
            bgcolor=SURFACE, border_radius=8, padding=10, width=180,
        ))

    # Streak info
    if user.streak_days > 0:
        rows.append(ft.Container(height=5))
        rows.append(ft.Text(f"Streak: {user.streak_days} day{'s' if user.streak_days != 1 else ''}", size=14, color=lang_color))

    # New achievements
    if new_achievements:
        rows.append(ft.Container(height=15))
        rows.append(ft.Text("New Achievements!", size=16, weight=ft.FontWeight.BOLD, color=GOLD))
        for ach in new_achievements:
            rows.append(ft.Container(
                content=ft.Row([
                    ft.Text(ach["icon"], size=24),
                    ft.Column([
                        ft.Text(ach["name"], size=14, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text(ach["description"], size=11, color=GRAY),
                    ], spacing=2),
                ], spacing=10),
                bgcolor=SURFACE, border_radius=8, padding=10, width=280,
                margin=ft.margin.only(top=4),
            ))

    rows.append(ft.Container(height=20))
    rows.append(ft.ElevatedButton(
        "Continue", on_click=lambda _: navigate("/"),
        style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=200,
    ))

    content = ft.Column(rows, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                         alignment=ft.MainAxisAlignment.CENTER, expand=True,
                         scroll=ft.ScrollMode.AUTO)
    set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), nav_idx)


# ── Home ─────────────────────────────────────────────────────────────

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
        lang_color = _get_lang_color(user)
        lang_name = _get_lang_name(user)
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


# ── Settings ─────────────────────────────────────────────────────────

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


# ── Learn (Lesson Browser) ──────────────────────────────────────────

def _show_learn(page, state, db, navigate, set_content):
    user = state.get("current_user")
    if user is None:
        set_content(ft.Container(
            content=ft.Text("Create a profile first!", size=18, color=GRAY),
            bgcolor=BG, expand=True, padding=20,
        ), 1)
        return

    lang_color = _get_lang_color(user)
    lesson_repo = LessonRepo(db.conn)
    card_repo = CardRepo(db.conn)
    vocab_repo = VocabRepo(db.conn)
    lessons = lesson_repo.get_by_language(user.target_language)

    # Group lessons by CEFR level
    grouped = {}
    for lesson in lessons:
        grouped.setdefault(lesson.cefr_level, []).append(lesson)

    rows = [
        ft.Text("Lessons", size=24, weight=ft.FontWeight.BOLD, color=WHITE),
        ft.Container(height=10),
    ]

    for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        level_lessons = grouped.get(level, [])
        if not level_lessons:
            continue

        rows.append(ft.Container(
            content=ft.Text(f"Level {level}", size=18, weight=ft.FontWeight.BOLD, color=lang_color),
            margin=ft.margin.only(top=15, bottom=5),
        ))

        for lesson in level_lessons:
            all_level_vocab = vocab_repo.get_by_language_level(user.target_language, lesson.cefr_level)
            if lesson.category and lesson.category != "mixed":
                lesson_vocab = [v for v in all_level_vocab if v.category == lesson.category]
            else:
                lesson_vocab = all_level_vocab
            word_count = len(lesson_vocab)

            reviewed = 0
            for v in lesson_vocab:
                if card_repo.get_by_user_and_vocab(user.id, v.id):
                    reviewed += 1
            progress = reviewed / word_count if word_count > 0 else 0.0

            if progress >= 1.0:
                status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=20, color=GREEN)
            elif progress > 0:
                status_icon = ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, size=20, color=lang_color)
            else:
                status_icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, size=20, color=GRAY)

            def on_lesson_click(e, l=lesson):
                _start_lesson_practice(page, state, db, l, navigate, set_content)

            rows.append(ft.Container(
                content=ft.Row([
                    status_icon,
                    ft.Column([
                        ft.Text(f"{lesson.lesson_number}. {lesson.title}",
                                size=15, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text(lesson.description, size=12, color=GRAY),
                        ft.Row([
                            ft.Text(f"{word_count} words", size=11, color=GRAY),
                            ft.Text("·", size=11, color=GRAY),
                            ft.Text(f"{int(progress * 100)}% done", size=11,
                                    color=GREEN if progress >= 1.0 else lang_color if progress > 0 else GRAY),
                        ], spacing=5),
                    ], expand=True, spacing=2),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color=GRAY),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=SURFACE, border_radius=10, padding=14,
                margin=ft.margin.only(bottom=6),
                on_click=on_lesson_click, ink=True,
            ))

    if not lessons:
        rows.append(ft.Text("No lessons yet. They'll appear after you create a profile.", size=14, color=GRAY))

    content = ft.Column(rows, scroll=ft.ScrollMode.AUTO, expand=True)
    set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), 1)


# ── Lesson Practice (Mixed Exercises) ────────────────────────────────

def _start_lesson_practice(page, state, db, lesson, navigate, set_content):
    """Start a practice session for a specific lesson with mixed exercise types."""
    user = state.get("current_user")
    lang_color = _get_lang_color(user)
    vocab_repo = VocabRepo(db.conn)
    srs = SRSEngine(db)
    gamification = _gamification_engine(db, user)

    # Get vocab for this lesson
    all_level_vocab = vocab_repo.get_by_language_level(user.target_language, lesson.cefr_level)
    if lesson.category and lesson.category != "mixed":
        lesson_vocab = [v for v in all_level_vocab if v.category == lesson.category]
    else:
        lesson_vocab = all_level_vocab

    if not lesson_vocab:
        set_content(ft.Container(
            content=ft.Column([
                ft.Text("No words available for this lesson.", size=18, color=GRAY),
                ft.ElevatedButton("Back to Lessons", on_click=lambda _: navigate("/learn"),
                                   style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER, expand=True),
            bgcolor=BG, expand=True, padding=20,
        ), 1)
        return

    # Create cards for this lesson's vocab if they don't exist yet
    vocab_ids = [v.id for v in lesson_vocab]
    srs.get_new_cards(user.id, vocab_ids, "flashcard", limit=len(vocab_ids))

    # Get cards for review (only this lesson's vocab)
    card_repo = CardRepo(db.conn)
    cards = []
    for v in lesson_vocab:
        v_cards = card_repo.get_by_user_and_vocab(user.id, v.id)
        if v_cards:
            cards.append(v_cards[0])

    random.shuffle(cards)
    cards = cards[:20]

    if not cards:
        set_content(ft.Container(
            content=ft.Column([
                ft.Text("No cards to practice.", size=18, color=GRAY),
                ft.ElevatedButton("Back to Lessons", on_click=lambda _: navigate("/learn"),
                                   style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER, expand=True),
            bgcolor=BG, expand=True, padding=20,
        ), 1)
        return

    # Get lesson exercise types
    lesson_etypes = json.loads(lesson.exercise_types_json) if lesson.exercise_types_json else ["flashcard_l2l1"]

    # Get achievements before session
    pre_achievements = gamification.get_unlocked_achievements(user)
    pre_ids = {a["id"] for a in pre_achievements}

    idx = [0]
    correct_count = [0]
    total_xp = [0]

    def show_card():
        if idx[0] >= len(cards):
            # Update streak and record session
            gamification.update_streak(user)
            gamification.add_xp(user, total_xp[0])
            state.set("current_user", user)

            # Check new achievements
            post_achievements = gamification.get_unlocked_achievements(user)
            new_achievements = [a for a in post_achievements if a["id"] not in pre_ids]

            acc = int(correct_count[0] / len(cards) * 100) if cards else 0
            # Check accuracy achievement
            if acc >= 90:
                accuracy_ach = [a for a in ACHIEVEMENTS if a["id"] == "accuracy_90"]
                for a in accuracy_ach:
                    if a["id"] not in pre_ids and a not in new_achievements:
                        new_achievements.append(a)

            _show_session_summary(page, state, db, set_content, navigate, 1,
                                  correct_count[0], len(cards), total_xp[0],
                                  new_achievements, title=f"{lesson.title} Complete!")
            return

        card = cards[idx[0]]
        vocab = vocab_repo.get(card.vocabulary_id)
        if vocab is None:
            idx[0] += 1
            show_card()
            return

        # Pick a random exercise type for this card
        etype = _pick_exercise_type(lesson_etypes, user.target_language)
        exercise = _create_exercise_for_card(vocab, etype, all_level_vocab, user.target_language)
        if exercise is None:
            exercise = _create_exercise_for_card(vocab, "flashcard_l2l1", all_level_vocab, user.target_language)

        def on_done(rating):
            from fsrs import Rating
            fsrs_rating = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}[rating]
            srs.review(card, fsrs_rating)
            xp = XP_PER_RATING.get(rating, 0)
            total_xp[0] += xp
            if rating >= 3:
                correct_count[0] += 1
            idx[0] += 1
            show_card()

        # Build exercise UI
        exercise_ui = _build_exercise_ui(page, exercise, vocab, lang_color, on_done)

        # Card maturity indicator
        maturity_label, maturity_color = _get_card_maturity(card)

        progress_text = ft.Text(f"{lesson.title} · {idx[0]+1}/{len(cards)}", size=13, color=GRAY)
        progress_bar = ft.ProgressBar(value=(idx[0]+1)/len(cards), color=lang_color, bgcolor=SURFACE, width=300)

        card_content = ft.Column([
            progress_text, progress_bar,
            ft.Row([
                ft.Container(
                    content=ft.Text(maturity_label, size=10, color=WHITE),
                    bgcolor=maturity_color, border_radius=4, padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
                ),
                ft.Container(
                    content=ft.Text(etype.replace("_", " ").title(), size=10, color=WHITE),
                    bgcolor=PRIMARY, border_radius=4, padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            ft.Container(height=10),
            exercise_ui,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

        set_content(ft.Container(content=card_content, bgcolor=BG, expand=True, padding=20), 1)

    show_card()


# ── Review (Mixed Session from SRS) ─────────────────────────────────

def _show_review(page, state, db, navigate, set_content):
    user = state.get("current_user")
    if user is None:
        set_content(ft.Container(
            content=ft.Text("Create a profile first!", size=18, color=GRAY),
            bgcolor=BG, expand=True, padding=20,
        ), 2)
        return

    lang_color = _get_lang_color(user)
    srs = SRSEngine(db)
    vocab_repo = VocabRepo(db.conn)
    gamification = _gamification_engine(db, user)
    cards = srs.get_session_mix(user.id)

    # If no cards exist yet, create new ones from vocabulary
    if not cards:
        all_vocab = vocab_repo.get_by_language(user.target_language)
        if all_vocab:
            vocab_ids = [v.id for v in all_vocab]
            srs.get_new_cards(user.id, vocab_ids, "flashcard", limit=20)
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

    all_vocab = vocab_repo.get_by_language(user.target_language)

    # Available exercise types for review: mix of common types
    review_exercise_types = ["flashcard_l2l1", "flashcard_l1l2", "mcq", "typing"]
    if user.target_language == "es":
        review_exercise_types.extend(["conjugation", "ser_estar", "gender"])
    elif user.target_language == "tr":
        review_exercise_types.extend(["vowel_harmony", "suffix"])

    pre_achievements = gamification.get_unlocked_achievements(user)
    pre_ids = {a["id"] for a in pre_achievements}

    idx = [0]
    correct_count = [0]
    total_xp = [0]

    def show_card():
        if idx[0] >= len(cards):
            gamification.update_streak(user)
            gamification.add_xp(user, total_xp[0])
            state.set("current_user", user)

            post_achievements = gamification.get_unlocked_achievements(user)
            new_achievements = [a for a in post_achievements if a["id"] not in pre_ids]

            acc = int(correct_count[0] / len(cards) * 100) if cards else 0
            if acc >= 90:
                accuracy_ach = [a for a in ACHIEVEMENTS if a["id"] == "accuracy_90"]
                for a in accuracy_ach:
                    if a["id"] not in pre_ids and a not in new_achievements:
                        new_achievements.append(a)

            _show_session_summary(page, state, db, set_content, navigate, 2,
                                  correct_count[0], len(cards), total_xp[0],
                                  new_achievements)
            return

        card = cards[idx[0]]
        vocab = vocab_repo.get(card.vocabulary_id)
        if vocab is None:
            idx[0] += 1
            show_card()
            return

        etype = _pick_exercise_type(review_exercise_types, user.target_language)
        exercise = _create_exercise_for_card(vocab, etype, all_vocab, user.target_language)
        if exercise is None:
            exercise = _create_exercise_for_card(vocab, "flashcard_l2l1", all_vocab, user.target_language)

        def on_done(rating):
            from fsrs import Rating
            fsrs_rating = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}[rating]
            srs.review(card, fsrs_rating)
            xp = XP_PER_RATING.get(rating, 0)
            total_xp[0] += xp
            if rating >= 3:
                correct_count[0] += 1
            idx[0] += 1
            show_card()

        exercise_ui = _build_exercise_ui(page, exercise, vocab, lang_color, on_done)

        maturity_label, maturity_color = _get_card_maturity(card)
        progress_text = ft.Text(f"Review · {idx[0]+1}/{len(cards)}", size=13, color=GRAY)
        progress_bar = ft.ProgressBar(value=(idx[0]+1)/len(cards), color=ACCENT, bgcolor=SURFACE, width=300)

        card_content = ft.Column([
            progress_text, progress_bar,
            ft.Row([
                ft.Container(
                    content=ft.Text(maturity_label, size=10, color=WHITE),
                    bgcolor=maturity_color, border_radius=4, padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
                ),
                ft.Container(
                    content=ft.Text(etype.replace("_", " ").title(), size=10, color=WHITE),
                    bgcolor=PRIMARY, border_radius=4, padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            ft.Container(height=10),
            exercise_ui,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

        set_content(ft.Container(content=card_content, bgcolor=BG, expand=True, padding=20), 2)

    show_card()


# ── Progress Page ────────────────────────────────────────────────────

def _show_progress(page, state, db, set_content):
    user = state.get("current_user")
    if user is None:
        set_content(ft.Container(
            content=ft.Text("Create a profile first!", size=18, color=GRAY),
            bgcolor=BG, expand=True, padding=20,
        ), 3)
        return

    review_repo = ReviewLogRepo(db.conn)
    card_repo = CardRepo(db.conn)
    lang_color = _get_lang_color(user)
    lang_name = _get_lang_name(user)
    gamification = _gamification_engine(db, user)

    total_reviews = review_repo.count_by_user(user.id)
    total_cards = card_repo.count_by_user(user.id)

    # Level progress
    level_info = gamification.get_level_progress(user)
    level_bar_value = level_info["progress"]
    if level_info["next_level"]:
        level_text = f"{user.current_level} → {level_info['next_level']} ({level_info['xp_to_next']} XP to go)"
    else:
        level_text = f"{user.current_level} (Max level!)"

    # Card maturity breakdown
    all_cards = card_repo.get_by_user(user.id)
    maturity_counts = {"New": 0, "Learning": 0, "Young": 0, "Mature": 0}
    for c in all_cards:
        label, _ = _get_card_maturity(c)
        maturity_counts[label] = maturity_counts.get(label, 0) + 1

    # Achievements
    unlocked = gamification.get_unlocked_achievements(user)
    unlocked_ids = {a["id"] for a in unlocked}

    rows = [
        ft.Text("Your Progress", size=24, weight=ft.FontWeight.BOLD, color=WHITE),
        ft.Container(height=15),

        # Stats row
        ft.Row([
            _stat_card("Streak", f"{user.streak_days}d", lang_color),
            _stat_card("Reviews", str(total_reviews), ACCENT),
            _stat_card("Cards", str(total_cards), lang_color),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Container(height=20),

        # Level progress
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STAR, color=GOLD, size=20),
                    ft.Text(f"Level {user.current_level}", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Text(f"· {user.xp} XP", size=14, color=GRAY),
                ], spacing=8),
                ft.ProgressBar(value=level_bar_value, color=lang_color, bgcolor=PRIMARY, width=280),
                ft.Text(level_text, size=12, color=GRAY),
            ], spacing=6),
            bgcolor=SURFACE, border_radius=12, padding=15, width=320,
        ),
        ft.Container(height=15),

        # Card maturity breakdown
        ft.Container(
            content=ft.Column([
                ft.Text("Card Mastery", size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Container(height=8),
                ft.Row([
                    ft.Column([
                        ft.Text(str(maturity_counts["New"]), size=18, weight=ft.FontWeight.BOLD, color=GRAY),
                        ft.Text("New", size=10, color=GRAY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text(str(maturity_counts["Learning"]), size=18, weight=ft.FontWeight.BOLD, color=RED),
                        ft.Text("Learning", size=10, color=RED),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text(str(maturity_counts["Young"]), size=18, weight=ft.FontWeight.BOLD, color=SPANISH),
                        ft.Text("Young", size=10, color=SPANISH),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text(str(maturity_counts["Mature"]), size=18, weight=ft.FontWeight.BOLD, color=GREEN),
                        ft.Text("Mature", size=10, color=GREEN),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, width=280),
            ]),
            bgcolor=SURFACE, border_radius=12, padding=15, width=320,
        ),
        ft.Container(height=15),

        # Info
        ft.Container(
            content=ft.Column([
                ft.Text(f"Language: {lang_name}", size=14, color=GRAY),
                ft.Text(f"Daily Goal: {user.daily_goal} cards", size=14, color=GRAY),
            ]),
            bgcolor=SURFACE, border_radius=12, padding=15, width=320,
        ),
        ft.Container(height=20),

        # Achievements
        ft.Text("Achievements", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
        ft.Container(height=8),
    ]

    for ach in ACHIEVEMENTS:
        is_unlocked = ach["id"] in unlocked_ids
        rows.append(ft.Container(
            content=ft.Row([
                ft.Text(ach["icon"] if is_unlocked else "?", size=24),
                ft.Column([
                    ft.Text(ach["name"], size=14, weight=ft.FontWeight.BOLD,
                            color=WHITE if is_unlocked else GRAY),
                    ft.Text(ach["description"], size=11,
                            color=GRAY if is_unlocked else "#555566"),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=GREEN) if is_unlocked else
                ft.Icon(ft.Icons.LOCK, size=18, color="#555566"),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE if is_unlocked else "#111122",
            border_radius=8, padding=12, width=320,
            margin=ft.margin.only(bottom=6),
            opacity=1.0 if is_unlocked else 0.6,
        ))

    content = ft.Column(rows, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                         expand=True, scroll=ft.ScrollMode.AUTO)
    set_content(ft.Container(content=content, bgcolor=BG, expand=True, padding=20), 3)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")
