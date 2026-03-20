"""Tests for database layer: migrations, all repositories."""

import os
import tempfile

import pytest

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import (
    UserRepo, VocabRepo, CardRepo, ReviewLogRepo, ProgressRepo, LessonRepo
)
from lang_mastering.models import (
    User, VocabularyItem, CardRecord, ReviewRecord, DailyProgress, Lesson
)


@pytest.fixture
def db():
    """Create a temporary database for each test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(db_path=path)
    database.run_migrations()
    yield database
    database.close()
    os.unlink(path)


@pytest.fixture
def user_repo(db):
    return UserRepo(db.conn)


@pytest.fixture
def vocab_repo(db):
    return VocabRepo(db.conn)


@pytest.fixture
def card_repo(db):
    return CardRepo(db.conn)


@pytest.fixture
def review_repo(db):
    return ReviewLogRepo(db.conn)


@pytest.fixture
def progress_repo(db):
    return ProgressRepo(db.conn)


@pytest.fixture
def lesson_repo(db):
    return LessonRepo(db.conn)


@pytest.fixture
def sample_user():
    return User(name="Alice", target_language="es", current_level="A1", daily_goal=20)


@pytest.fixture
def sample_vocab():
    return VocabularyItem(
        language="es", cefr_level="A1", category="greetings",
        word="hola", translation="hello", phonetic="'o.la",
        example_sentence="¡Hola, amigo!", example_translation="Hello, friend!",
        part_of_speech="interjection"
    )


# ---- Database Tests ----

class TestDatabase:
    def test_context_manager(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        with Database(db_path=path) as db:
            # Should be able to query after migrations run
            rows = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = {r["name"] for r in rows}
            assert "users" in table_names
            assert "vocabulary" in table_names
            assert "cards" in table_names
            assert "review_logs" in table_names
            assert "daily_progress" in table_names
            assert "lessons" in table_names
        os.unlink(path)

    def test_foreign_keys_enabled(self, db):
        row = db.conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1


# ---- User Repository Tests ----

class TestUserRepo:
    def test_create_and_get(self, user_repo, sample_user):
        created = user_repo.create(sample_user)
        assert created.id is not None

        fetched = user_repo.get(created.id)
        assert fetched is not None
        assert fetched.name == "Alice"
        assert fetched.target_language == "es"
        assert fetched.current_level == "A1"
        assert fetched.daily_goal == 20
        assert fetched.desired_retention == 0.9

    def test_get_nonexistent(self, user_repo):
        assert user_repo.get(999) is None

    def test_get_all(self, user_repo):
        user_repo.create(User(name="Alice", target_language="es"))
        user_repo.create(User(name="Bob", target_language="tr"))
        users = user_repo.get_all()
        assert len(users) == 2

    def test_update(self, user_repo, sample_user):
        created = user_repo.create(sample_user)
        created.xp = 100
        created.streak_days = 5
        user_repo.update(created)

        fetched = user_repo.get(created.id)
        assert fetched.xp == 100
        assert fetched.streak_days == 5

    def test_delete(self, user_repo, sample_user):
        created = user_repo.create(sample_user)
        user_repo.delete(created.id)
        assert user_repo.get(created.id) is None


# ---- Vocabulary Repository Tests ----

class TestVocabRepo:
    def test_create_and_get(self, vocab_repo, sample_vocab):
        created = vocab_repo.create(sample_vocab)
        assert created.id is not None

        fetched = vocab_repo.get(created.id)
        assert fetched.word == "hola"
        assert fetched.translation == "hello"
        assert fetched.language == "es"

    def test_get_by_language_level(self, vocab_repo):
        vocab_repo.create(VocabularyItem(language="es", cefr_level="A1", word="hola", translation="hello"))
        vocab_repo.create(VocabularyItem(language="es", cefr_level="A2", word="también", translation="also"))
        vocab_repo.create(VocabularyItem(language="tr", cefr_level="A1", word="merhaba", translation="hello"))

        es_a1 = vocab_repo.get_by_language_level("es", "A1")
        assert len(es_a1) == 1
        assert es_a1[0].word == "hola"

    def test_get_by_language(self, vocab_repo):
        vocab_repo.create(VocabularyItem(language="es", cefr_level="A1", word="hola", translation="hello"))
        vocab_repo.create(VocabularyItem(language="es", cefr_level="A2", word="también", translation="also"))
        vocab_repo.create(VocabularyItem(language="tr", cefr_level="A1", word="merhaba", translation="hello"))

        es_all = vocab_repo.get_by_language("es")
        assert len(es_all) == 2

    def test_create_many(self, vocab_repo):
        items = [
            VocabularyItem(language="es", cefr_level="A1", word="uno", translation="one"),
            VocabularyItem(language="es", cefr_level="A1", word="dos", translation="two"),
        ]
        vocab_repo.create_many(items)
        assert len(vocab_repo.get_by_language("es")) == 2

    def test_delete(self, vocab_repo, sample_vocab):
        created = vocab_repo.create(sample_vocab)
        vocab_repo.delete(created.id)
        assert vocab_repo.get(created.id) is None


# ---- Card Repository Tests ----

class TestCardRepo:
    def test_create_and_get(self, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)

        card = CardRecord(
            user_id=user.id, vocabulary_id=vocab.id,
            exercise_type="flashcard_l2l1",
            fsrs_card_json='{"stability": 1.0}',
            due_date="2025-01-01T00:00:00"
        )
        created = card_repo.create(card)
        assert created.id is not None

        fetched = card_repo.get(created.id)
        assert fetched.exercise_type == "flashcard_l2l1"
        assert fetched.is_suspended is False

    def test_get_due_cards(self, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)

        # One due card, one future card
        card_repo.create(CardRecord(
            user_id=user.id, vocabulary_id=vocab.id,
            exercise_type="flashcard_l2l1", due_date="2020-01-01T00:00:00"
        ))
        card_repo.create(CardRecord(
            user_id=user.id, vocabulary_id=vocab.id,
            exercise_type="mcq", due_date="2099-01-01T00:00:00"
        ))

        due = card_repo.get_due_cards(user.id, "2025-06-01T00:00:00")
        assert len(due) == 1
        assert due[0].exercise_type == "flashcard_l2l1"

    def test_get_by_user(self, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)

        card_repo.create(CardRecord(user_id=user.id, vocabulary_id=vocab.id, exercise_type="mcq", due_date="2025-01-01T00:00:00"))
        card_repo.create(CardRecord(user_id=user.id, vocabulary_id=vocab.id, exercise_type="typing", due_date="2025-01-01T00:00:00"))

        cards = card_repo.get_by_user(user.id)
        assert len(cards) == 2

    def test_update(self, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)

        card = card_repo.create(CardRecord(
            user_id=user.id, vocabulary_id=vocab.id,
            exercise_type="flashcard_l2l1", due_date="2025-01-01T00:00:00"
        ))
        card.fsrs_card_json = '{"stability": 5.0}'
        card.due_date = "2025-02-01T00:00:00"
        card_repo.update(card)

        fetched = card_repo.get(card.id)
        assert fetched.fsrs_card_json == '{"stability": 5.0}'
        assert fetched.due_date == "2025-02-01T00:00:00"

    def test_count_by_user(self, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)
        card_repo.create(CardRecord(user_id=user.id, vocabulary_id=vocab.id, exercise_type="mcq", due_date="2025-01-01T00:00:00"))
        assert card_repo.count_by_user(user.id) == 1


# ---- Review Log Repository Tests ----

class TestReviewLogRepo:
    def test_create_and_get_by_card(self, review_repo, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)
        card = card_repo.create(CardRecord(
            user_id=user.id, vocabulary_id=vocab.id,
            exercise_type="flashcard_l2l1", due_date="2025-01-01T00:00:00"
        ))

        review = ReviewRecord(
            card_id=card.id, user_id=user.id, rating=3,
            exercise_type="flashcard_l2l1", response_time_ms=1500,
            was_correct=True, reviewed_at="2025-01-01T10:00:00"
        )
        created = review_repo.create(review)
        assert created.id is not None

        logs = review_repo.get_by_card(card.id)
        assert len(logs) == 1
        assert logs[0].rating == 3
        assert logs[0].was_correct is True

    def test_get_by_user(self, review_repo, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)
        card = card_repo.create(CardRecord(
            user_id=user.id, vocabulary_id=vocab.id,
            exercise_type="mcq", due_date="2025-01-01T00:00:00"
        ))

        review_repo.create(ReviewRecord(
            card_id=card.id, user_id=user.id, rating=3,
            exercise_type="mcq", was_correct=True, reviewed_at="2025-01-01T10:00:00"
        ))
        review_repo.create(ReviewRecord(
            card_id=card.id, user_id=user.id, rating=1,
            exercise_type="mcq", was_correct=False, reviewed_at="2025-01-02T10:00:00"
        ))

        logs = review_repo.get_by_user(user.id)
        assert len(logs) == 2

    def test_count_by_user(self, review_repo, card_repo, user_repo, vocab_repo, sample_user, sample_vocab):
        user = user_repo.create(sample_user)
        vocab = vocab_repo.create(sample_vocab)
        card = card_repo.create(CardRecord(
            user_id=user.id, vocabulary_id=vocab.id,
            exercise_type="mcq", due_date="2025-01-01T00:00:00"
        ))
        review_repo.create(ReviewRecord(
            card_id=card.id, user_id=user.id, rating=3,
            exercise_type="mcq", was_correct=True, reviewed_at="2025-01-01T10:00:00"
        ))
        assert review_repo.count_by_user(user.id) == 1


# ---- Progress Repository Tests ----

class TestProgressRepo:
    def test_upsert_create(self, progress_repo, user_repo, sample_user):
        user = user_repo.create(sample_user)
        progress = DailyProgress(
            user_id=user.id, date="2025-01-01",
            cards_reviewed=20, cards_new=5, cards_correct=18,
            cards_incorrect=2, xp_earned=150, time_spent_seconds=600
        )
        created = progress_repo.upsert(progress)
        assert created.id is not None

        fetched = progress_repo.get_by_user_date(user.id, "2025-01-01")
        assert fetched.cards_reviewed == 20

    def test_upsert_update(self, progress_repo, user_repo, sample_user):
        user = user_repo.create(sample_user)
        progress_repo.upsert(DailyProgress(
            user_id=user.id, date="2025-01-01", cards_reviewed=10
        ))
        progress_repo.upsert(DailyProgress(
            user_id=user.id, date="2025-01-01", cards_reviewed=25
        ))

        fetched = progress_repo.get_by_user_date(user.id, "2025-01-01")
        assert fetched.cards_reviewed == 25

    def test_get_range(self, progress_repo, user_repo, sample_user):
        user = user_repo.create(sample_user)
        for i in range(1, 6):
            progress_repo.upsert(DailyProgress(
                user_id=user.id, date=f"2025-01-0{i}", cards_reviewed=i * 10
            ))

        results = progress_repo.get_range(user.id, "2025-01-02", "2025-01-04")
        assert len(results) == 3

    def test_get_nonexistent(self, progress_repo, user_repo, sample_user):
        user = user_repo.create(sample_user)
        assert progress_repo.get_by_user_date(user.id, "2099-01-01") is None


# ---- Lesson Repository Tests ----

class TestLessonRepo:
    def test_create_and_get(self, lesson_repo):
        lesson = Lesson(
            language="es", cefr_level="A1", lesson_number=1,
            title="Greetings", description="Basic greetings",
            category="communication", exercise_types_json='["flashcard_l2l1", "mcq"]'
        )
        created = lesson_repo.create(lesson)
        assert created.id is not None

        fetched = lesson_repo.get(created.id)
        assert fetched.title == "Greetings"

    def test_get_by_language(self, lesson_repo):
        lesson_repo.create(Lesson(language="es", cefr_level="A1", lesson_number=1, title="Greetings"))
        lesson_repo.create(Lesson(language="es", cefr_level="A2", lesson_number=1, title="Travel"))
        lesson_repo.create(Lesson(language="tr", cefr_level="A1", lesson_number=1, title="Selamlar"))

        es_lessons = lesson_repo.get_by_language("es")
        assert len(es_lessons) == 2

    def test_get_by_language_level(self, lesson_repo):
        lesson_repo.create(Lesson(language="es", cefr_level="A1", lesson_number=1, title="Greetings"))
        lesson_repo.create(Lesson(language="es", cefr_level="A1", lesson_number=2, title="Numbers"))
        lesson_repo.create(Lesson(language="es", cefr_level="A2", lesson_number=1, title="Travel"))

        a1_lessons = lesson_repo.get_by_language_level("es", "A1")
        assert len(a1_lessons) == 2
        assert a1_lessons[0].lesson_number < a1_lessons[1].lesson_number

    def test_create_many(self, lesson_repo):
        lessons = [
            Lesson(language="tr", cefr_level="A1", lesson_number=1, title="Selamlar"),
            Lesson(language="tr", cefr_level="A1", lesson_number=2, title="Sayılar"),
        ]
        lesson_repo.create_many(lessons)
        assert len(lesson_repo.get_by_language("tr")) == 2

    def test_delete(self, lesson_repo):
        lesson = lesson_repo.create(Lesson(language="es", cefr_level="A1", lesson_number=1, title="Test"))
        lesson_repo.delete(lesson.id)
        assert lesson_repo.get(lesson.id) is None
