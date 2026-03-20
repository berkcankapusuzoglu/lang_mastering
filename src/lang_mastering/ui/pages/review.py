"""Review session page: active review loop with exercises."""

import json
import time
import threading

import flet as ft
from fsrs import Rating

from lang_mastering.core.exercises import ExerciseFactory, Exercise
from lang_mastering.core.srs import SRSEngine
from lang_mastering.core.gamification import GamificationEngine
from lang_mastering.db.repositories import (
    VocabRepo, CardRepo, LessonRepo, UserRepo, ReviewLogRepo, ProgressRepo,
)
from lang_mastering.models import CardRecord, VocabularyItem
from lang_mastering.ui.theme import (
    BG_COLOR, SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY,
    ACCENT_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR, get_language_color,
)

LANGUAGE_NAMES = {"es": "Spanish", "tr": "Turkish"}


def review_page(page: ft.Page) -> ft.View:
    """Build the review session page."""
    user = page.app_state.get("current_user")
    db = page.app_state.get("db")

    if user is None:
        from lang_mastering.ui.components.nav_bar import build_nav_bar
        return ft.View(
            "/review",
            [ft.Container(
                content=ft.Column([
                    ft.Text("Please create a profile first", size=18, color=TEXT_SECONDARY),
                    ft.ElevatedButton("Go to Settings", on_click=lambda _: page.app_state.get("router").navigate("/settings")),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                bgcolor=BG_COLOR, expand=True, padding=20,
            )],
            bgcolor=BG_COLOR,
            bottom_appbar=build_nav_bar(page, 2),
        )

    # Initialize engine and repos
    srs = SRSEngine(db, desired_retention=user.desired_retention)
    vocab_repo = VocabRepo(db.conn)
    card_repo = CardRepo(db.conn)
    user_repo = UserRepo(db.conn)
    review_repo = ReviewLogRepo(db.conn)
    progress_repo = ProgressRepo(db.conn)
    gamification = GamificationEngine(user_repo, progress_repo, review_repo)

    # Get or create session cards
    lesson = page.app_state.get("current_lesson")
    lang_color = get_language_color(user.target_language)

    # Build session cards
    session_cards = srs.get_session_mix(user.id, new_limit=5, review_limit=15)

    # If we have a lesson selected, create new cards for that lesson's vocab
    new_card_count = 0
    if lesson and len(session_cards) < 20:
        from lang_mastering.core.content import ContentManager
        lesson_repo = LessonRepo(db.conn)
        content_mgr = ContentManager(vocab_repo, lesson_repo, card_repo)
        lesson_vocab = content_mgr.get_lesson_vocab(user.target_language, lesson.category, lesson.cefr_level)
        vocab_ids = [v.id for v in lesson_vocab if v.id is not None]
        exercise_types = json.loads(lesson.exercise_types_json)
        for ex_type in exercise_types:
            if ex_type in ("vowel_harmony", "suffix"):
                continue  # Language-specific drills handled separately
            new = srs.get_new_cards(user.id, vocab_ids, ex_type, limit=5)
            new_card_count += len(new)
            session_cards.extend(new)
        if page.app_state.contains_key("current_lesson"):
            page.app_state.remove("current_lesson")

    if not session_cards:
        from lang_mastering.ui.components.nav_bar import build_nav_bar
        return ft.View(
            "/review",
            [ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=80, color=SUCCESS_COLOR),
                    ft.Text("All caught up!", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ft.Text("No cards due for review right now.", size=16, color=TEXT_SECONDARY),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Browse Lessons",
                        icon=ft.Icons.MENU_BOOK,
                        on_click=lambda _: page.app_state.get("router").navigate("/learn"),
                        style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                bgcolor=BG_COLOR, expand=True, padding=20,
            )],
            bgcolor=BG_COLOR,
            bottom_appbar=build_nav_bar(page, 2),
        )

    # Load all vocab for distractor generation
    all_vocab = vocab_repo.get_by_language(user.target_language)
    factory = ExerciseFactory(all_vocab)

    # Audio manager for listening exercises (lazy init)
    audio_mgr_ref = {"mgr": None}

    def get_audio_manager():
        if audio_mgr_ref["mgr"] is None:
            from lang_mastering.core.audio import AudioManager
            audio_mgr_ref["mgr"] = AudioManager()
        return audio_mgr_ref["mgr"]

    # Session state
    state = {
        "index": 0,
        "correct": 0,
        "incorrect": 0,
        "xp_earned": 0,
        "start_time": time.time(),
        "card_start_time": time.time(),
    }

    # UI containers
    progress_text = ft.Text(f"1/{len(session_cards)}", size=14, color=TEXT_SECONDARY)
    progress_bar = ft.ProgressBar(value=0, color=ACCENT_COLOR, bgcolor=SURFACE_COLOR, height=6)
    exercise_container = ft.Container(expand=True)
    feedback_text = ft.Text("", size=16, text_align=ft.TextAlign.CENTER)

    def get_vocab_for_card(card: CardRecord) -> VocabularyItem:
        return vocab_repo.get(card.vocabulary_id)

    def show_exercise():
        """Render the current exercise."""
        if state["index"] >= len(session_cards):
            show_summary()
            return

        card = session_cards[state["index"]]
        vocab = get_vocab_for_card(card)
        if vocab is None:
            advance()
            return

        exercise = factory.create(vocab, card.exercise_type)
        if exercise is None:
            exercise = factory.create(vocab, "flashcard_l2l1")
        if exercise is None:
            advance()
            return

        state["card_start_time"] = time.time()
        feedback_text.value = ""
        feedback_text.color = TEXT_SECONDARY

        # Update progress
        progress_text.value = f"{state['index'] + 1}/{len(session_cards)}"
        progress_bar.value = state["index"] / len(session_cards)

        # Render based on exercise type
        if card.exercise_type.startswith("flashcard"):
            render_flashcard(exercise, card)
        elif card.exercise_type == "mcq":
            render_mcq(exercise, card)
        elif card.exercise_type in ("typing", "cloze"):
            render_typing(exercise, card)
        elif card.exercise_type == "sentence_building":
            render_sentence_building(exercise, card)
        elif card.exercise_type == "listening":
            render_listening(exercise, card)
        elif card.exercise_type == "speaking":
            render_speaking(exercise, card)
        else:
            render_flashcard(exercise, card)

        page.update()

    def submit_answer(card: CardRecord, exercise: Exercise, answer: str):
        """Process answer and update SRS."""
        result = exercise.check_answer(answer)
        response_ms = int((time.time() - state["card_start_time"]) * 1000)

        rating_map = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}
        rating = rating_map.get(result.suggested_rating, Rating.Good)

        srs.review(card, rating, response_ms)

        # Calculate XP
        xp = gamification.calculate_xp(result.suggested_rating, user.streak_days)
        state["xp_earned"] += xp

        if result.is_correct:
            state["correct"] += 1
            feedback_text.color = SUCCESS_COLOR
        else:
            state["incorrect"] += 1
            feedback_text.color = ERROR_COLOR

        feedback_text.value = result.feedback
        page.update()

        # Brief delay then advance (thread-safe via page.run_task-like approach)
        def delayed_advance():
            time.sleep(0.8)
            advance()
        threading.Thread(target=delayed_advance, daemon=True).start()

    def advance():
        """Move to next card."""
        state["index"] += 1
        show_exercise()

    def render_flashcard(exercise: Exercise, card: CardRecord):
        """Render a flashcard exercise."""
        is_flipped = {"value": False}

        front = ft.Column([
            ft.Text(exercise.prompt, size=32, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
            ft.Container(height=10),
            ft.Text(exercise.hint, size=14, color=TEXT_SECONDARY, italic=True, text_align=ft.TextAlign.CENTER) if exercise.hint else ft.Container(),
            ft.Container(height=20),
            ft.Text("Tap card to flip", size=12, color=TEXT_SECONDARY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)

        back = ft.Column([
            ft.Text(exercise.correct_answer, size=28, weight=ft.FontWeight.BOLD, color=lang_color, text_align=ft.TextAlign.CENTER),
            ft.Container(height=10),
            ft.Text(exercise.prompt, size=16, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)

        card_display = ft.Container(
            content=front, bgcolor=SURFACE_COLOR, border_radius=16,
            padding=30, width=350, height=250, alignment=ft.alignment.center,
        )

        rating_row = ft.Row(
            [
                ft.ElevatedButton("Again", on_click=lambda _: rate(1), style=ft.ButtonStyle(bgcolor=ERROR_COLOR, color=TEXT_COLOR), width=80),
                ft.ElevatedButton("Hard", on_click=lambda _: rate(2), style=ft.ButtonStyle(bgcolor=WARNING_COLOR, color=TEXT_COLOR), width=80),
                ft.ElevatedButton("Good", on_click=lambda _: rate(3), style=ft.ButtonStyle(bgcolor=SUCCESS_COLOR, color=TEXT_COLOR), width=80),
                ft.ElevatedButton("Easy", on_click=lambda _: rate(4), style=ft.ButtonStyle(bgcolor="#2196f3", color=TEXT_COLOR), width=80),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False,
        )

        def flip(e):
            is_flipped["value"] = not is_flipped["value"]
            card_display.content = back if is_flipped["value"] else front
            rating_row.visible = is_flipped["value"]
            page.update()

        def rate(r):
            response_ms = int((time.time() - state["card_start_time"]) * 1000)
            rating_map = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}
            srs.review(card, rating_map[r], response_ms)
            xp = gamification.calculate_xp(r, user.streak_days)
            state["xp_earned"] += xp
            if r >= 3:
                state["correct"] += 1
            else:
                state["incorrect"] += 1
            advance()

        card_display.on_click = flip

        exercise_container.content = ft.Column([
            ft.Container(height=20),
            ft.Text(
                "What does this mean?" if card.exercise_type == "flashcard_l2l1" else "How do you say this?",
                size=16, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=15),
            card_display,
            ft.Container(height=15),
            rating_row,
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START)

    def render_mcq(exercise: Exercise, card: CardRecord):
        """Render a multiple choice exercise."""
        option_buttons = []
        for opt in exercise.options:
            option_buttons.append(
                ft.ElevatedButton(
                    text=opt,
                    on_click=lambda e, o=opt: submit_answer(card, exercise, o),
                    style=ft.ButtonStyle(bgcolor=SURFACE_COLOR, color=TEXT_COLOR),
                    width=300, height=45,
                )
            )

        exercise_container.content = ft.Column([
            ft.Container(height=20),
            ft.Text("Choose the correct translation:", size=16, color=TEXT_SECONDARY),
            ft.Container(height=15),
            ft.Container(
                content=ft.Text(exercise.prompt, size=28, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                bgcolor=SURFACE_COLOR, border_radius=12, padding=20, width=350,
            ),
            ft.Container(height=20),
            *option_buttons,
            ft.Container(height=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START, spacing=8)

    def render_typing(exercise: Exercise, card: CardRecord):
        """Render a typing exercise."""
        input_field = ft.TextField(
            label="Type your answer",
            border_color=ACCENT_COLOR,
            color=TEXT_COLOR,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            width=300,
            autofocus=True,
        )

        def on_submit(e):
            submit_answer(card, exercise, input_field.value or "")

        input_field.on_submit = on_submit

        prompt_label = "Fill in the blank:" if card.exercise_type == "cloze" else "Type the translation:"

        exercise_container.content = ft.Column([
            ft.Container(height=20),
            ft.Text(prompt_label, size=16, color=TEXT_SECONDARY),
            ft.Container(height=15),
            ft.Container(
                content=ft.Text(exercise.prompt, size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                bgcolor=SURFACE_COLOR, border_radius=12, padding=20, width=350,
            ),
            ft.Container(height=5),
            ft.Text(f"Hint: {exercise.hint}", size=13, color=TEXT_SECONDARY, italic=True) if exercise.hint else ft.Container(),
            ft.Container(height=15),
            input_field,
            ft.Container(height=10),
            ft.ElevatedButton(
                "Check",
                on_click=on_submit,
                style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                width=200,
            ),
            ft.Container(height=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START)

    def render_listening(exercise: Exercise, card: CardRecord):
        """Render a listening exercise: play audio, select/type what was heard."""
        audio_mgr = get_audio_manager()
        vocab = exercise.vocab_item

        status_text = ft.Text("Tap speaker to hear the word", size=14, color=TEXT_SECONDARY)

        def play_audio(e):
            status_text.value = "Playing..."
            page.update()

            def _play():
                path = audio_mgr.generate_audio_sync(vocab.word, vocab.language)
                if path:
                    audio = ft.Audio(src=path, autoplay=True)
                    page.overlay.append(audio)
                    status_text.value = "What did you hear?"
                else:
                    status_text.value = "Audio unavailable - type what you think it is"
                page.update()

            threading.Thread(target=_play, daemon=True).start()

        speaker_btn = ft.IconButton(
            icon=ft.Icons.VOLUME_UP,
            icon_color=ACCENT_COLOR,
            icon_size=48,
            tooltip="Play audio",
            on_click=play_audio,
        )

        # If MCQ-style (has options), show buttons; otherwise show text input
        if exercise.options:
            option_buttons = []
            for opt in exercise.options:
                option_buttons.append(
                    ft.ElevatedButton(
                        text=opt,
                        on_click=lambda e, o=opt: submit_answer(card, exercise, o),
                        style=ft.ButtonStyle(bgcolor=SURFACE_COLOR, color=TEXT_COLOR),
                        width=300, height=45,
                    )
                )
            answer_area = ft.Column(option_buttons, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            input_field = ft.TextField(
                label="Type what you heard",
                border_color=ACCENT_COLOR,
                color=TEXT_COLOR,
                label_style=ft.TextStyle(color=TEXT_SECONDARY),
                width=300,
            )
            input_field.on_submit = lambda e: submit_answer(card, exercise, input_field.value or "")
            answer_area = ft.Column([
                input_field,
                ft.ElevatedButton(
                    "Check", on_click=lambda e: submit_answer(card, exercise, input_field.value or ""),
                    style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR), width=200,
                ),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        exercise_container.content = ft.Column([
            ft.Container(height=20),
            ft.Text("Listen and identify the word:", size=16, color=TEXT_SECONDARY),
            ft.Container(height=15),
            speaker_btn,
            status_text,
            ft.Container(height=5),
            ft.Text(f"Hint: {exercise.hint}", size=13, color=TEXT_SECONDARY, italic=True) if exercise.hint else ft.Container(),
            ft.Container(height=15),
            answer_area,
            ft.Container(height=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START)

    def render_speaking(exercise: Exercise, card: CardRecord):
        """Render a speaking exercise: see word, record, get pronunciation score."""
        from lang_mastering.ui.components.pronunciation import build_pronunciation_recorder

        def on_pronunciation_result(result):
            score = result.get("score", 0)
            submit_answer(card, exercise, str(score))

        recorder = build_pronunciation_recorder(
            expected_text=exercise.prompt,
            language=user.target_language,
            on_result=on_pronunciation_result,
        )

        exercise_container.content = ft.Column([
            ft.Container(height=20),
            ft.Text("Say this word aloud:", size=16, color=TEXT_SECONDARY),
            ft.Container(height=5),
            ft.Text(f"({exercise.hint})", size=13, color=TEXT_SECONDARY, italic=True) if exercise.hint else ft.Container(),
            ft.Container(height=15),
            recorder,
            ft.Container(height=10),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START)

    def render_sentence_building(exercise: Exercise, card: CardRecord):
        """Render a sentence building exercise."""
        selected_words = {"words": []}
        available_words = {"words": list(exercise.options)}

        word_chips_row = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=6)
        answer_chips_row = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=6)

        def update_display():
            word_chips_row.controls = [
                ft.ElevatedButton(
                    w, on_click=lambda e, word=w, idx=i: select_word(word, idx),
                    style=ft.ButtonStyle(bgcolor=SURFACE_COLOR, color=TEXT_COLOR),
                ) for i, w in enumerate(available_words["words"]) if w is not None
            ]
            answer_chips_row.controls = [
                ft.ElevatedButton(
                    w, on_click=lambda e, word=w, idx=i: deselect_word(word, idx),
                    style=ft.ButtonStyle(bgcolor=lang_color, color=TEXT_COLOR),
                ) for i, w in enumerate(selected_words["words"])
            ]
            page.update()

        def select_word(word, idx):
            selected_words["words"].append(word)
            available_words["words"][idx] = None
            update_display()

        def deselect_word(word, idx):
            selected_words["words"].pop(idx)
            for i, w in enumerate(available_words["words"]):
                if w is None:
                    available_words["words"][i] = word
                    break
            update_display()

        def check_sentence(e):
            answer = " ".join(selected_words["words"])
            submit_answer(card, exercise, answer)

        update_display()

        exercise_container.content = ft.Column([
            ft.Container(height=20),
            ft.Text("Arrange the words:", size=16, color=TEXT_SECONDARY),
            ft.Container(height=10),
            ft.Container(
                content=ft.Text(exercise.prompt, size=18, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                bgcolor=SURFACE_COLOR, border_radius=12, padding=15, width=350,
            ),
            ft.Container(height=15),
            ft.Text("Your answer:", size=14, color=TEXT_SECONDARY),
            ft.Container(
                content=answer_chips_row,
                bgcolor=SURFACE_COLOR, border_radius=8, padding=10, width=350, min_height=50,
            ),
            ft.Container(height=10),
            ft.Text("Available words:", size=14, color=TEXT_SECONDARY),
            word_chips_row,
            ft.Container(height=15),
            ft.ElevatedButton(
                "Check",
                on_click=check_sentence,
                style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                width=200,
            ),
            feedback_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START)

    def show_summary():
        """Show end-of-session summary and persist gamification data."""
        total = state["correct"] + state["incorrect"]
        elapsed = int(time.time() - state["start_time"])
        accuracy = (state["correct"] / total * 100) if total > 0 else 0

        # Persist gamification
        nonlocal user
        user = gamification.update_streak(user)
        user = gamification.add_xp(user, state["xp_earned"])
        gamification.record_session(
            user, cards_reviewed=total, cards_new=new_card_count,
            cards_correct=state["correct"], cards_incorrect=state["incorrect"],
            xp_earned=state["xp_earned"], time_spent_seconds=elapsed,
        )
        # Refresh user in session
        page.app_state.set("current_user", user)

        progress_text.value = f"{total}/{total}"
        progress_bar.value = 1.0

        exercise_container.content = ft.Column([
            ft.Container(height=30),
            ft.Icon(ft.Icons.CELEBRATION, size=60, color=ACCENT_COLOR),
            ft.Text("Session Complete!", size=26, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    _summary_row("Cards reviewed", str(total)),
                    _summary_row("Correct", str(state["correct"]), SUCCESS_COLOR),
                    _summary_row("Incorrect", str(state["incorrect"]), ERROR_COLOR),
                    _summary_row("Accuracy", f"{accuracy:.0f}%"),
                    _summary_row("XP earned", f"+{state['xp_earned']}", ACCENT_COLOR),
                    _summary_row("Streak", f"{user.streak_days} days"),
                    _summary_row("Time", f"{elapsed // 60}m {elapsed % 60}s"),
                ], spacing=8),
                bgcolor=SURFACE_COLOR, border_radius=12, padding=20, width=300,
            ),
            ft.Container(height=25),
            ft.ElevatedButton(
                "Back to Home",
                icon=ft.Icons.HOME,
                on_click=lambda _: page.app_state.get("router").navigate("/"),
                style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color=TEXT_COLOR),
                width=200,
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START)
        page.update()

    # Start the session
    show_exercise()

    from lang_mastering.ui.components.nav_bar import build_nav_bar
    return ft.View(
        "/review",
        [
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        progress_text,
                        ft.IconButton(
                            ft.Icons.CLOSE,
                            icon_color=TEXT_SECONDARY,
                            on_click=lambda _: page.app_state.get("router").navigate("/"),
                            tooltip="End session",
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    progress_bar,
                    exercise_container,
                ], expand=True),
                bgcolor=BG_COLOR,
                expand=True,
                padding=20,
            ),
        ],
        bgcolor=BG_COLOR,
        bottom_appbar=build_nav_bar(page, 2),
    )


def _summary_row(label: str, value: str, color=TEXT_COLOR) -> ft.Row:
    return ft.Row([
        ft.Text(label, size=16, color=TEXT_SECONDARY),
        ft.Text(value, size=16, weight=ft.FontWeight.BOLD, color=color),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
