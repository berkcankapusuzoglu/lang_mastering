"""CRUD repositories for all database tables."""

import sqlite3
from typing import Optional

from lang_mastering.models import (
    User, VocabularyItem, CardRecord, ReviewRecord, DailyProgress, Lesson
)


class UserRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, user: User) -> User:
        cursor = self.conn.execute(
            "INSERT INTO users (name, target_language, current_level, xp, streak_days, last_review_date, daily_goal, desired_retention) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user.name, user.target_language, user.current_level, user.xp, user.streak_days, user.last_review_date, user.daily_goal, user.desired_retention)
        )
        self.conn.commit()
        user.id = cursor.lastrowid
        return user

    def get(self, user_id: int) -> Optional[User]:
        row = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        return User(**dict(row))

    def get_all(self) -> list[User]:
        rows = self.conn.execute("SELECT * FROM users").fetchall()
        return [User(**dict(r)) for r in rows]

    def update(self, user: User) -> User:
        self.conn.execute(
            "UPDATE users SET name=?, target_language=?, current_level=?, xp=?, streak_days=?, last_review_date=?, daily_goal=?, desired_retention=? WHERE id=?",
            (user.name, user.target_language, user.current_level, user.xp, user.streak_days, user.last_review_date, user.daily_goal, user.desired_retention, user.id)
        )
        self.conn.commit()
        return user

    def delete(self, user_id: int) -> None:
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()


class VocabRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, item: VocabularyItem) -> VocabularyItem:
        cursor = self.conn.execute(
            "INSERT INTO vocabulary (language, cefr_level, category, word, translation, phonetic, example_sentence, example_translation, gender, part_of_speech, notes, audio_cache_path, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item.language, item.cefr_level, item.category, item.word, item.translation, item.phonetic, item.example_sentence, item.example_translation, item.gender, item.part_of_speech, item.notes, item.audio_cache_path, item.tags)
        )
        self.conn.commit()
        item.id = cursor.lastrowid
        return item

    def get(self, vocab_id: int) -> Optional[VocabularyItem]:
        row = self.conn.execute("SELECT * FROM vocabulary WHERE id = ?", (vocab_id,)).fetchone()
        if row is None:
            return None
        return VocabularyItem(**dict(row))

    def get_by_language_level(self, language: str, cefr_level: str) -> list[VocabularyItem]:
        rows = self.conn.execute(
            "SELECT * FROM vocabulary WHERE language = ? AND cefr_level = ?",
            (language, cefr_level)
        ).fetchall()
        return [VocabularyItem(**dict(r)) for r in rows]

    def get_by_language(self, language: str) -> list[VocabularyItem]:
        rows = self.conn.execute(
            "SELECT * FROM vocabulary WHERE language = ?", (language,)
        ).fetchall()
        return [VocabularyItem(**dict(r)) for r in rows]

    def create_many(self, items: list[VocabularyItem]) -> list[VocabularyItem]:
        for item in items:
            self.create(item)
        return items

    def delete(self, vocab_id: int) -> None:
        self.conn.execute("DELETE FROM vocabulary WHERE id = ?", (vocab_id,))
        self.conn.commit()


class CardRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, card: CardRecord) -> CardRecord:
        cursor = self.conn.execute(
            "INSERT INTO cards (user_id, vocabulary_id, exercise_type, fsrs_card_json, is_suspended, due_date) VALUES (?, ?, ?, ?, ?, ?)",
            (card.user_id, card.vocabulary_id, card.exercise_type, card.fsrs_card_json, int(card.is_suspended), card.due_date)
        )
        self.conn.commit()
        card.id = cursor.lastrowid
        return card

    def get(self, card_id: int) -> Optional[CardRecord]:
        row = self.conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["is_suspended"] = bool(d["is_suspended"])
        return CardRecord(**d)

    def get_due_cards(self, user_id: int, before: str, limit: int = 50) -> list[CardRecord]:
        """Get cards due before a given datetime string, ordered by due date."""
        rows = self.conn.execute(
            "SELECT * FROM cards WHERE user_id = ? AND due_date <= ? AND is_suspended = 0 ORDER BY due_date ASC LIMIT ?",
            (user_id, before, limit)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["is_suspended"] = bool(d["is_suspended"])
            result.append(CardRecord(**d))
        return result

    def get_by_user(self, user_id: int) -> list[CardRecord]:
        rows = self.conn.execute(
            "SELECT * FROM cards WHERE user_id = ?", (user_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["is_suspended"] = bool(d["is_suspended"])
            result.append(CardRecord(**d))
        return result

    def get_by_user_and_vocab(self, user_id: int, vocabulary_id: int) -> list[CardRecord]:
        rows = self.conn.execute(
            "SELECT * FROM cards WHERE user_id = ? AND vocabulary_id = ?",
            (user_id, vocabulary_id)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["is_suspended"] = bool(d["is_suspended"])
            result.append(CardRecord(**d))
        return result

    def update(self, card: CardRecord) -> CardRecord:
        self.conn.execute(
            "UPDATE cards SET fsrs_card_json=?, is_suspended=?, due_date=? WHERE id=?",
            (card.fsrs_card_json, int(card.is_suspended), card.due_date, card.id)
        )
        self.conn.commit()
        return card

    def delete(self, card_id: int) -> None:
        self.conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        self.conn.commit()

    def count_by_user(self, user_id: int) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM cards WHERE user_id = ?", (user_id,)).fetchone()
        return row["cnt"]


class ReviewLogRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, review: ReviewRecord) -> ReviewRecord:
        cursor = self.conn.execute(
            "INSERT INTO review_logs (card_id, user_id, rating, fsrs_review_log_json, exercise_type, response_time_ms, was_correct, reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (review.card_id, review.user_id, review.rating, review.fsrs_review_log_json, review.exercise_type, review.response_time_ms, int(review.was_correct), review.reviewed_at)
        )
        self.conn.commit()
        review.id = cursor.lastrowid
        return review

    def get_by_card(self, card_id: int) -> list[ReviewRecord]:
        rows = self.conn.execute(
            "SELECT * FROM review_logs WHERE card_id = ? ORDER BY reviewed_at ASC",
            (card_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["was_correct"] = bool(d["was_correct"])
            result.append(ReviewRecord(**d))
        return result

    def get_by_user(self, user_id: int, limit: int = 100) -> list[ReviewRecord]:
        rows = self.conn.execute(
            "SELECT * FROM review_logs WHERE user_id = ? ORDER BY reviewed_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["was_correct"] = bool(d["was_correct"])
            result.append(ReviewRecord(**d))
        return result

    def count_by_user(self, user_id: int) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM review_logs WHERE user_id = ?", (user_id,)).fetchone()
        return row["cnt"]


class ProgressRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def upsert(self, progress: DailyProgress) -> DailyProgress:
        """Insert or update daily progress for a user+date combo."""
        cursor = self.conn.execute(
            """INSERT INTO daily_progress (user_id, date, cards_reviewed, cards_new, cards_correct, cards_incorrect, xp_earned, time_spent_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, date) DO UPDATE SET
                 cards_reviewed=excluded.cards_reviewed,
                 cards_new=excluded.cards_new,
                 cards_correct=excluded.cards_correct,
                 cards_incorrect=excluded.cards_incorrect,
                 xp_earned=excluded.xp_earned,
                 time_spent_seconds=excluded.time_spent_seconds""",
            (progress.user_id, progress.date, progress.cards_reviewed, progress.cards_new, progress.cards_correct, progress.cards_incorrect, progress.xp_earned, progress.time_spent_seconds)
        )
        self.conn.commit()
        if progress.id is None:
            progress.id = cursor.lastrowid
        return progress

    def get_by_user_date(self, user_id: int, date: str) -> Optional[DailyProgress]:
        row = self.conn.execute(
            "SELECT * FROM daily_progress WHERE user_id = ? AND date = ?",
            (user_id, date)
        ).fetchone()
        if row is None:
            return None
        return DailyProgress(**dict(row))

    def get_range(self, user_id: int, start_date: str, end_date: str) -> list[DailyProgress]:
        rows = self.conn.execute(
            "SELECT * FROM daily_progress WHERE user_id = ? AND date >= ? AND date <= ? ORDER BY date ASC",
            (user_id, start_date, end_date)
        ).fetchall()
        return [DailyProgress(**dict(r)) for r in rows]


class LessonRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, lesson: Lesson) -> Lesson:
        cursor = self.conn.execute(
            "INSERT INTO lessons (language, cefr_level, lesson_number, title, description, category, exercise_types_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (lesson.language, lesson.cefr_level, lesson.lesson_number, lesson.title, lesson.description, lesson.category, lesson.exercise_types_json)
        )
        self.conn.commit()
        lesson.id = cursor.lastrowid
        return lesson

    def get(self, lesson_id: int) -> Optional[Lesson]:
        row = self.conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
        if row is None:
            return None
        return Lesson(**dict(row))

    def get_by_language(self, language: str) -> list[Lesson]:
        rows = self.conn.execute(
            "SELECT * FROM lessons WHERE language = ? ORDER BY cefr_level, lesson_number",
            (language,)
        ).fetchall()
        return [Lesson(**dict(r)) for r in rows]

    def get_by_language_level(self, language: str, cefr_level: str) -> list[Lesson]:
        rows = self.conn.execute(
            "SELECT * FROM lessons WHERE language = ? AND cefr_level = ? ORDER BY lesson_number",
            (language, cefr_level)
        ).fetchall()
        return [Lesson(**dict(r)) for r in rows]

    def create_many(self, lessons: list[Lesson]) -> list[Lesson]:
        for lesson in lessons:
            self.create(lesson)
        return lessons

    def delete(self, lesson_id: int) -> None:
        self.conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
        self.conn.commit()
