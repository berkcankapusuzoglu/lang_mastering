"""SRS Engine wrapping the FSRS library for spaced repetition scheduling."""

import json
from datetime import datetime, timezone
from typing import Optional

from fsrs import Card, Rating, Scheduler

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import CardRepo, ReviewLogRepo, VocabRepo
from lang_mastering.models import CardRecord, ReviewRecord


class SRSEngine:
    """Wraps the FSRS scheduler to manage spaced repetition cards.

    Responsibilities:
    - Create new FSRS Card objects for vocabulary items
    - Review cards and persist updated state to the database
    - Query due cards and build session mixes of new + review cards
    """

    def __init__(self, db: Database, desired_retention: float = 0.9):
        self.db = db
        self.scheduler = Scheduler(desired_retention=desired_retention)
        self.card_repo = CardRepo(db.conn)
        self.review_repo = ReviewLogRepo(db.conn)
        self.vocab_repo = VocabRepo(db.conn)

    # ---- Card Creation ----

    def get_new_cards(
        self,
        user_id: int,
        vocabulary_ids: list[int],
        exercise_type: str,
        limit: int = 10,
    ) -> list[CardRecord]:
        """Create new CardRecords for vocabulary items that don't have cards yet.

        For each vocabulary_id, checks if a card already exists for the given
        user + vocab + exercise_type combination. If not, creates a fresh FSRS
        Card and persists a CardRecord to the database.

        Returns the list of newly created CardRecords (up to ``limit``).
        """
        created: list[CardRecord] = []
        for vocab_id in vocabulary_ids:
            if len(created) >= limit:
                break
            # Check if card already exists for this combo
            existing = self.card_repo.get_by_user_and_vocab(user_id, vocab_id)
            already_has = any(c.exercise_type == exercise_type for c in existing)
            if already_has:
                continue

            # Create a fresh FSRS card
            fsrs_card = Card()
            now = datetime.now(timezone.utc)

            card_record = CardRecord(
                user_id=user_id,
                vocabulary_id=vocab_id,
                exercise_type=exercise_type,
                fsrs_card_json=json.dumps(fsrs_card.to_dict()),
                due_date=now.isoformat(),
            )
            card_record = self.card_repo.create(card_record)
            created.append(card_record)

        return created

    # ---- Review ----

    def review(
        self,
        card_record: CardRecord,
        rating: Rating,
        response_time_ms: int = 0,
    ) -> tuple[CardRecord, ReviewRecord]:
        """Review a card using the FSRS scheduler.

        Args:
            card_record: The CardRecord to review.
            rating: FSRS Rating (Again=1, Hard=2, Good=3, Easy=4).
            response_time_ms: How long the user took to answer in milliseconds.

        Returns:
            A tuple of (updated CardRecord, created ReviewRecord).
        """
        # Deserialize FSRS card from stored JSON
        fsrs_card = Card.from_dict(json.loads(card_record.fsrs_card_json))

        # Run FSRS scheduling
        updated_card, review_log = self.scheduler.review_card(fsrs_card, rating)

        # Update the card record with new FSRS state
        card_record.fsrs_card_json = json.dumps(updated_card.to_dict())
        card_record.due_date = updated_card.due.isoformat()
        self.card_repo.update(card_record)

        # Persist the review log
        was_correct = rating != Rating.Again
        review_record = ReviewRecord(
            card_id=card_record.id,
            user_id=card_record.user_id,
            rating=int(rating),
            fsrs_review_log_json=json.dumps(review_log.to_dict()),
            exercise_type=card_record.exercise_type,
            response_time_ms=response_time_ms,
            was_correct=was_correct,
            reviewed_at=datetime.now(timezone.utc).isoformat(),
        )
        review_record = self.review_repo.create(review_record)

        return card_record, review_record

    # ---- Queries ----

    def get_due_cards(
        self, user_id: int, limit: int = 50
    ) -> list[CardRecord]:
        """Return cards that are due for review (due_date <= now)."""
        now = datetime.now(timezone.utc).isoformat()
        return self.card_repo.get_due_cards(user_id, before=now, limit=limit)

    def get_session_mix(
        self,
        user_id: int,
        new_limit: int = 5,
        review_limit: int = 15,
    ) -> list[CardRecord]:
        """Build a study session mixing new and review cards.

        Returns up to ``review_limit`` due cards plus up to ``new_limit``
        cards that have never been reviewed (state is still Learning, step 0).
        Due review cards come first, followed by new cards.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Get cards due for review
        due_cards = self.card_repo.get_due_cards(
            user_id, before=now, limit=review_limit + new_limit
        )

        # Separate into review cards (have been reviewed at least once) and new cards
        review_cards: list[CardRecord] = []
        new_cards: list[CardRecord] = []

        for card in due_cards:
            fsrs_data = json.loads(card.fsrs_card_json)
            # A card is "new" if it has never been reviewed (last_review is None and step == 0)
            if fsrs_data.get("last_review") is None and fsrs_data.get("step", 0) == 0:
                new_cards.append(card)
            else:
                review_cards.append(card)

        # Apply limits
        review_cards = review_cards[:review_limit]
        new_cards = new_cards[:new_limit]

        return review_cards + new_cards
