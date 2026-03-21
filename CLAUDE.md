# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Run the app locally (opens in browser)
python -m lang_mastering.main

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

- **Models** (`models/`): Pure dataclasses — `User`, `VocabularyItem`, `CardRecord`, `ReviewRecord`, `DailyProgress`, `Lesson`. No logic.
- **DB** (`db/`): SQLite with WAL mode. `Database` handles connection + migrations. `repositories.py` has one repo class per table (UserRepo, VocabRepo, CardRepo, ReviewLogRepo, ProgressRepo, LessonRepo). CRUD only.
- **Core** (`core/`): Business logic.
  - `srs.py`: Wraps FSRS library. `SRSEngine(db)` — takes Database, not user. `get_session_mix(user_id)` and `get_new_cards(user_id, vocab_ids, exercise_type)` both require user_id. Card state stored as JSON blob.
  - `exercises.py`: `ExerciseFactory` creates 8 exercise types. Each returns `ExerciseResult` with `suggested_rating`.
  - `language_specific/`: Spanish (conjugation, ser/estar, gender) and Turkish (vowel harmony, suffix stacking, SOV) drills.
  - `gamification.py`: XP calc (rating-based + streak multiplier), CEFR level progression, 9 achievements.
  - `content.py`: `ContentManager` manages lessons, vocab, CEFR unlocking.
- **Data** (`data/`): `seed.py` loads JSON vocab/curriculum into DB on first profile creation. Files in `data/vocabularies/` and `data/curricula/`.

## Critical: Flet 0.82 Web Rendering

The `main.py` builds ALL pages inline (not using `ui/pages/` or `ui/router.py`) because of Flet 0.82 web mode constraints:

- **NEVER call `page.controls.clear()`** — breaks Flet web rendering permanently (blank page, no recovery).
- **NEVER use `ft.View` for content** — Views add a Material Scaffold layer that overrides background colors. Content appears as light gray.
- **Working pattern**: Build controls fresh, use `page.add(ft.Container(content=..., bgcolor=BG, expand=True))`. Swap content via `page.controls.remove(old)` then `page.add(new)`.
- **State**: Custom `AppState` class on `page.app_state` (not `page.session.store` — that API doesn't exist in Flet 0.82).
- **Navigation**: Closure-based `navigate(route)` function, bottom nav via `page.bottom_appbar`.

## Key Patterns

- **FSRS card lifecycle**: `fsrs.Card()` → `card.to_dict()` → JSON stored in `cards.fsrs_card_json` → `Card.from_dict(json.loads(...))` to restore → `Scheduler.review_card(card, rating)` returns `(updated_card, review_log)`.
- **Session creation**: Cards must be explicitly created via `srs.get_new_cards()` before `get_session_mix()` returns anything. First review auto-creates cards from vocabulary.
- **Theme**: Dark mode only, hex color strings (not `ft.Colors` enum). Language accent: Spanish=#ff9800, Turkish=#009688.
- **Seed data**: JSON vocab files loaded by `seed_all(vocab_repo, lesson_repo, language)` — called once during profile creation.

## Deployment

- **Live**: https://lang-mastering.onrender.com (Render free tier, Docker)
- **Dockerfile** uses `requirements.txt` (lightweight, no Whisper/torch) — `pyproject.toml` has full deps for local dev
- Render free tier: cold start ~30-60s, builds take 5-10 min, SQLite DB resets on each deploy
- Port: 8550 (set via `PORT` env var)

## Languages Supported

Spanish (`es`) and Turkish (`tr`) for English speakers. A1, A2, and B1 CEFR levels, ~200 vocab items per level per language. Lessons are clickable — each starts a flashcard practice session for that lesson's vocabulary.
