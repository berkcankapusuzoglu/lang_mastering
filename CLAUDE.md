# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Run the app
python -m lang_mastering.main
# Or: flet run src/lang_mastering/main.py

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_database.py -v

# Run a single test
pytest tests/test_exercises.py::test_flashcard_l2_to_l1 -v
```

Whisper requires `ffmpeg` on the system for pronunciation features.

## Architecture

Layered architecture: **UI → Core → DB → Models**. No upward imports.

- **Models** (`models/`): Pure dataclasses — `User`, `VocabularyItem`, `CardRecord`, `ReviewRecord`, `DailyProgress`. No logic, no dependencies.
- **DB** (`db/`): SQLite with WAL mode. `Database` handles connection + migration runner. `repositories.py` has one repo class per table (UserRepo, VocabRepo, CardRepo, ReviewLogRepo, ProgressRepo, LessonRepo). CRUD only, no business logic.
- **Core** (`core/`): Business logic layer.
  - `srs.py`: Wraps FSRS library. Card state stored as JSON blob in DB. `SRSEngine.review()` calls `Scheduler.review_card()` and persists both updated card and review log.
  - `exercises.py`: `ExerciseFactory` creates 8 exercise types (flashcard L2→L1, L1→L2, MCQ, typing, listening, speaking, cloze, sentence building). Each returns `ExerciseResult` from `check_answer()`.
  - `language_specific/`: Spanish (conjugation, ser/estar, gender) and Turkish (vowel harmony, suffix stacking, SOV order) drill generators.
  - `gamification.py`: XP calc (rating-based + streak multiplier), level progression, 9 achievements.
  - `content.py`: `ContentManager` manages lessons, vocab, CEFR level unlocking.
- **UI** (`ui/`): Flet-based. Pages return `ft.View` objects.
  - `router.py`: Custom `Router` extracts View contents into `page.controls` (Flet 0.82 compatibility — `page.views` doesn't render in web mode).
  - Navigation: `page.session.store.get("router").navigate("/route")` — all state stored via `page.session.store`.
  - `pages/`: home, learn, review, progress, settings. Each is a builder function `fn(page) -> ft.View`.
  - `components/`: Reusable widgets (flashcard, audio player, pronunciation recorder, nav bar, session summary).

## Key Patterns

- **Flet 0.82 session API**: Use `page.session.store.set()`/`.get()`/`.contains_key()` — not `page.session.set()`/`.get()`.
- **FSRS card lifecycle**: `fsrs.Card()` → `.to_json()` stored in `cards.fsrs_card_json` → `Card.from_json()` to restore → `Scheduler.review_card(card, rating)` returns `(updated_card, review_log)`.
- **Seed data**: JSON vocab files in `data/vocabularies/`, curriculum in `data/curricula/`. `seed.py` loads into DB, skips duplicates.
- **Theme**: Dark mode, hex color strings (not `ft.Colors` enum). Language accent: Spanish=#ff9800, Turkish=#009688.

## Languages Supported

Spanish (`es`) and Turkish (`tr`) for English speakers. A1 and A2 CEFR levels, ~200 vocab items per level per language.
