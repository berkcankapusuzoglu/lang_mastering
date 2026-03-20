"""Schema creation SQL for lang_mastering database."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    target_language TEXT NOT NULL CHECK(target_language IN ('es', 'tr')),
    current_level TEXT NOT NULL DEFAULT 'A1' CHECK(current_level IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    xp INTEGER NOT NULL DEFAULT 0,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_review_date TEXT,
    daily_goal INTEGER NOT NULL DEFAULT 20,
    desired_retention REAL NOT NULL DEFAULT 0.9
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL CHECK(language IN ('es', 'tr')),
    cefr_level TEXT NOT NULL DEFAULT 'A1',
    category TEXT NOT NULL DEFAULT '',
    word TEXT NOT NULL,
    translation TEXT NOT NULL,
    phonetic TEXT NOT NULL DEFAULT '',
    example_sentence TEXT NOT NULL DEFAULT '',
    example_translation TEXT NOT NULL DEFAULT '',
    gender TEXT NOT NULL DEFAULT '',
    part_of_speech TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    audio_cache_path TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vocabulary_id INTEGER NOT NULL,
    exercise_type TEXT NOT NULL,
    fsrs_card_json TEXT NOT NULL DEFAULT '{}',
    is_suspended INTEGER NOT NULL DEFAULT 0,
    due_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 4),
    fsrs_review_log_json TEXT NOT NULL DEFAULT '{}',
    exercise_type TEXT NOT NULL,
    response_time_ms INTEGER NOT NULL DEFAULT 0,
    was_correct INTEGER NOT NULL DEFAULT 0,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    cards_reviewed INTEGER NOT NULL DEFAULT 0,
    cards_new INTEGER NOT NULL DEFAULT 0,
    cards_correct INTEGER NOT NULL DEFAULT 0,
    cards_incorrect INTEGER NOT NULL DEFAULT 0,
    xp_earned INTEGER NOT NULL DEFAULT 0,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, date)
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL CHECK(language IN ('es', 'tr')),
    cefr_level TEXT NOT NULL DEFAULT 'A1',
    lesson_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    exercise_types_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_cards_user_due ON cards(user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_cards_user_vocab ON cards(user_id, vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_card ON review_logs(card_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_user ON review_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_language_level ON vocabulary(language, cefr_level);
CREATE INDEX IF NOT EXISTS idx_lessons_language ON lessons(language, cefr_level);
CREATE INDEX IF NOT EXISTS idx_daily_progress_user_date ON daily_progress(user_id, date);
"""
