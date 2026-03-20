# Lang Mastering

A language learning desktop app combining **FSRS spaced repetition**, **active recall exercises**, **TTS audio**, **pronunciation practice**, and **gamification**. Built with Python and Flet.

Currently supports **Spanish** and **Turkish** for English speakers.

## Features

- **FSRS Spaced Repetition** - State-of-the-art algorithm (20-30% fewer reviews than SM-2)
- **8 Exercise Types** - Flashcards, multiple choice, typing, listening, speaking, cloze deletion, sentence building, and language-specific drills
- **TTS Audio** - Neural voices via edge-tts with offline pyttsx3 fallback
- **Pronunciation Practice** - Record yourself and get scored via OpenAI Whisper
- **Language-Specific Drills** - Spanish verb conjugation, ser/estar, gender agreement; Turkish vowel harmony, suffix stacking, SOV word order
- **Gamification** - XP, streaks, levels, achievements, progress dashboard
- **800+ Vocabulary Items** - A1 and A2 levels for both languages with example sentences
- **40 Structured Lessons** - Organized curriculum by CEFR level

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/lang_mastering.git
cd lang_mastering

# Install dependencies
pip install -e ".[dev]"
```

**Note:** Whisper requires `ffmpeg` on your system for pronunciation features.

## Usage

```bash
# Run the app
python -m lang_mastering.main

# Or with flet
flet run src/lang_mastering/main.py
```

1. Create a profile (choose name, language, daily goal)
2. Browse lessons by CEFR level
3. Start a review session
4. Track your progress on the dashboard

## Running Tests

```bash
pytest tests/ -v
```

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | Flet (Flutter-based, cross-platform) |
| SRS Algorithm | FSRS (state-of-the-art spaced repetition) |
| Database | SQLite (zero-config, WAL mode) |
| TTS | edge-tts + pyttsx3 fallback |
| Speech Recognition | OpenAI Whisper |
| Fuzzy Matching | python-Levenshtein |

## Project Structure

```
src/lang_mastering/
├── main.py                    # App entry point
├── ui/                        # Flet UI layer
│   ├── theme.py               # Material 3 dark theme
│   ├── router.py              # Page navigation
│   ├── pages/                 # Home, Learn, Review, Progress, Settings
│   └── components/            # Flashcard, audio player, pronunciation, etc.
├── core/                      # Business logic
│   ├── srs.py                 # FSRS integration
│   ├── exercises.py           # 8 exercise types + factory
│   ├── audio.py               # TTS generation + caching
│   ├── pronunciation.py       # Whisper transcription + scoring
│   ├── content.py             # Lesson/vocab management
│   ├── gamification.py        # XP, streaks, achievements
│   └── language_specific/     # Spanish & Turkish drills
├── models/                    # Dataclasses
├── db/                        # SQLite database layer
│   ├── database.py            # Connection + migrations
│   ├── migrations.py          # Schema SQL
│   └── repositories.py        # CRUD for all tables
└── data/                      # Seed data
    ├── vocabularies/           # ~800 words (JSON)
    └── curricula/              # 40 lessons (JSON)
```
