"""Tests for the SRS engine (FSRS integration)."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from fsrs import Card, Rating, Scheduler

from lang_mastering.core.srs import SRSEngine
from lang_mastering.db.database import Database
from lang_mastering.db.repositories import (
    CardRepo, ReviewLogRepo, UserRepo, VocabRepo,
)
from lang_mastering.models import CardRecord, ReviewRecord, User, VocabularyItem


# ---- Fixtures ----

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
def engine(db):
    return SRSEngine(db)


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
def sample_user(user_repo):
    return user_repo.create(
        User(name="Tester", target_language="es", current_level="A1")
    )


@pytest.fixture
def sample_vocabs(vocab_repo):
    items = [
        VocabularyItem(language="es", cefr_level="A1", word="hola", translation="hello"),
        VocabularyItem(language="es", cefr_level="A1", word="adiós", translation="goodbye"),
        VocabularyItem(language="es", cefr_level="A1", word="gracias", translation="thanks"),
    ]
    return vocab_repo.create_many(items)


# ---- Tests ----

class TestCreateNewCards:
    def test_create_new_cards(self, engine, sample_user, sample_vocabs):
        """Cards are created for vocab items that don't have cards yet."""
        vocab_ids = [v.id for v in sample_vocabs]
        created = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        assert len(created) == 3
        for card in created:
            assert card.id is not None
            assert card.user_id == sample_user.id
            assert card.exercise_type == "flashcard_l2l1"
            # FSRS card JSON should be valid
            fsrs_data = json.loads(card.fsrs_card_json)
            assert "state" in fsrs_data
            assert "due" in fsrs_data

    def test_no_duplicate_cards(self, engine, sample_user, sample_vocabs):
        """Calling get_new_cards again doesn't create duplicates."""
        vocab_ids = [v.id for v in sample_vocabs]
        first = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        assert len(first) == 3

        second = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        assert len(second) == 0

    def test_respects_limit(self, engine, sample_user, sample_vocabs):
        """Only creates up to `limit` cards."""
        vocab_ids = [v.id for v in sample_vocabs]
        created = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
            limit=2,
        )
        assert len(created) == 2

    def test_different_exercise_types(self, engine, sample_user, sample_vocabs):
        """Cards for different exercise types are created independently."""
        vocab_ids = [v.id for v in sample_vocabs]
        flashcards = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        mcqs = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="mcq",
        )
        assert len(flashcards) == 3
        assert len(mcqs) == 3


class TestReviewCardGood:
    def test_review_card_good(self, engine, sample_user, sample_vocabs):
        """Reviewing with Rating.Good advances the due date."""
        vocab_ids = [v.id for v in sample_vocabs]
        cards = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        card = cards[0]
        original_due = card.due_date

        updated_card, review_record = engine.review(card, Rating.Good)

        # Due date should have advanced
        assert updated_card.due_date > original_due
        # Review record should be persisted
        assert review_record.id is not None
        assert review_record.rating == int(Rating.Good)
        assert review_record.was_correct is True


class TestReviewCardAgain:
    def test_review_card_again(self, engine, sample_user, sample_vocabs):
        """Reviewing with Rating.Again results in a short re-study interval."""
        vocab_ids = [v.id for v in sample_vocabs]
        cards = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        card = cards[0]

        updated_card, review_record = engine.review(card, Rating.Again)

        # The card should still be due soon (short interval for Again)
        fsrs_data = json.loads(updated_card.fsrs_card_json)
        due = datetime.fromisoformat(fsrs_data["due"])
        now = datetime.now(timezone.utc)
        # Again interval should be very short (< 5 minutes typically)
        assert (due - now).total_seconds() < 300

        assert review_record.was_correct is False
        assert review_record.rating == int(Rating.Again)


class TestGetDueCards:
    def test_get_due_cards(self, engine, sample_user, sample_vocabs, card_repo):
        """Cards with past due dates are returned by get_due_cards."""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

        fsrs_card = Card()

        # Card due in the past
        card_repo.create(CardRecord(
            user_id=sample_user.id,
            vocabulary_id=sample_vocabs[0].id,
            exercise_type="flashcard_l2l1",
            fsrs_card_json=json.dumps(fsrs_card.to_dict()),
            due_date=past,
        ))
        # Card due in the future
        card_repo.create(CardRecord(
            user_id=sample_user.id,
            vocabulary_id=sample_vocabs[1].id,
            exercise_type="flashcard_l2l1",
            fsrs_card_json=json.dumps(fsrs_card.to_dict()),
            due_date=future,
        ))

        due_cards = engine.get_due_cards(sample_user.id)
        assert len(due_cards) == 1
        assert due_cards[0].vocabulary_id == sample_vocabs[0].id

    def test_get_due_cards_respects_limit(self, engine, sample_user, sample_vocabs, card_repo):
        """Limit parameter caps the number of returned cards."""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        fsrs_card = Card()

        for vocab in sample_vocabs:
            card_repo.create(CardRecord(
                user_id=sample_user.id,
                vocabulary_id=vocab.id,
                exercise_type="flashcard_l2l1",
                fsrs_card_json=json.dumps(fsrs_card.to_dict()),
                due_date=past,
            ))

        due_cards = engine.get_due_cards(sample_user.id, limit=2)
        assert len(due_cards) == 2


class TestGetSessionMix:
    def test_get_session_mix(self, engine, sample_user, sample_vocabs, card_repo):
        """Session mix includes both new and review cards."""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(hours=1)).isoformat()

        # Create a "new" card (never reviewed, due now)
        new_fsrs = Card()
        new_dict = new_fsrs.to_dict()
        card_repo.create(CardRecord(
            user_id=sample_user.id,
            vocabulary_id=sample_vocabs[0].id,
            exercise_type="flashcard_l2l1",
            fsrs_card_json=json.dumps(new_dict),
            due_date=past,
        ))

        # Create a "review" card (has been reviewed before, due now)
        scheduler = Scheduler()
        reviewed_fsrs = Card()
        reviewed_fsrs, _ = scheduler.review_card(reviewed_fsrs, Rating.Good)
        reviewed_fsrs, _ = scheduler.review_card(reviewed_fsrs, Rating.Good)
        reviewed_dict = reviewed_fsrs.to_dict()
        # Force due date to the past so it shows up
        reviewed_dict["due"] = past
        card_repo.create(CardRecord(
            user_id=sample_user.id,
            vocabulary_id=sample_vocabs[1].id,
            exercise_type="flashcard_l2l1",
            fsrs_card_json=json.dumps(reviewed_dict),
            due_date=past,
        ))

        mix = engine.get_session_mix(sample_user.id, new_limit=5, review_limit=15)
        assert len(mix) == 2

        # First should be the review card, then the new card
        review_data = json.loads(mix[0].fsrs_card_json)
        new_data = json.loads(mix[1].fsrs_card_json)
        assert review_data.get("last_review") is not None
        assert new_data.get("last_review") is None


class TestReviewUpdatesDb:
    def test_review_updates_db(self, engine, sample_user, sample_vocabs, card_repo, review_repo):
        """After review, both card state and review log are persisted in the DB."""
        vocab_ids = [v.id for v in sample_vocabs]
        cards = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        card = cards[0]
        card_id = card.id

        # Review the card
        engine.review(card, Rating.Good, response_time_ms=1200)

        # Verify card state is updated in DB
        fetched_card = card_repo.get(card_id)
        assert fetched_card is not None
        fsrs_data = json.loads(fetched_card.fsrs_card_json)
        assert fsrs_data.get("last_review") is not None  # Has been reviewed
        assert fsrs_data.get("stability") is not None

        # Verify review log is persisted
        logs = review_repo.get_by_card(card_id)
        assert len(logs) == 1
        assert logs[0].rating == int(Rating.Good)
        assert logs[0].response_time_ms == 1200
        assert logs[0].was_correct is True

    def test_multiple_reviews_accumulate(self, engine, sample_user, sample_vocabs, review_repo):
        """Multiple reviews on the same card create multiple log entries."""
        vocab_ids = [v.id for v in sample_vocabs]
        cards = engine.get_new_cards(
            user_id=sample_user.id,
            vocabulary_ids=vocab_ids,
            exercise_type="flashcard_l2l1",
        )
        card = cards[0]

        engine.review(card, Rating.Good)
        engine.review(card, Rating.Again)
        engine.review(card, Rating.Easy)

        logs = review_repo.get_by_card(card.id)
        assert len(logs) == 3
        assert logs[0].rating == int(Rating.Good)
        assert logs[1].rating == int(Rating.Again)
        assert logs[2].rating == int(Rating.Easy)
