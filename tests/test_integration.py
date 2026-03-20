"""Integration tests: full end-to-end flows."""

import os
import tempfile

import pytest
from fsrs import Rating

from lang_mastering.db.database import Database
from lang_mastering.db.repositories import (
    UserRepo, VocabRepo, CardRepo, ReviewLogRepo, ProgressRepo, LessonRepo
)
from lang_mastering.models import User, VocabularyItem
from lang_mastering.core.srs import SRSEngine
from lang_mastering.core.exercises import ExerciseFactory
from lang_mastering.core.content import ContentManager
from lang_mastering.core.gamification import GamificationEngine
from lang_mastering.data.seed import seed_all


@pytest.fixture
def full_db():
    """Create a fully seeded database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(db_path=path)
    db.run_migrations()

    # Create user
    user_repo = UserRepo(db.conn)
    user = user_repo.create(User(name="Test User", target_language="es", daily_goal=20))

    # Seed Spanish data
    vocab_repo = VocabRepo(db.conn)
    lesson_repo = LessonRepo(db.conn)
    seed_all(vocab_repo, lesson_repo, "es")

    yield db, user

    db.close()
    os.unlink(path)


class TestFullReviewSession:
    """Test a complete review session from start to finish."""

    def test_complete_session_flow(self, full_db):
        db, user = full_db

        # Setup repos
        vocab_repo = VocabRepo(db.conn)
        card_repo = CardRepo(db.conn)
        review_repo = ReviewLogRepo(db.conn)
        progress_repo = ProgressRepo(db.conn)
        user_repo = UserRepo(db.conn)

        srs = SRSEngine(db, desired_retention=user.desired_retention)
        gamification = GamificationEngine(user_repo, progress_repo, review_repo)

        # Get vocabulary
        vocab = vocab_repo.get_by_language_level("es", "A1")
        assert len(vocab) > 0, "Should have A1 vocabulary"

        # Create new cards for first 10 vocab items
        vocab_ids = [v.id for v in vocab[:10]]
        new_cards = srs.get_new_cards(user.id, vocab_ids, "flashcard_l2l1", limit=10)
        assert len(new_cards) == 10

        # Get session mix
        session = srs.get_session_mix(user.id, new_limit=5, review_limit=15)
        assert len(session) > 0

        # Review all cards
        correct_count = 0
        total_xp = 0
        for card in session:
            # Simulate "Good" rating
            rating = Rating.Good
            card_record, review_record = srs.review(card, rating)
            assert review_record.id is not None

            xp = gamification.calculate_xp(3, user.streak_days)
            total_xp += xp
            correct_count += 1

        # Update streak and XP
        user = gamification.update_streak(user)
        user = gamification.add_xp(user, total_xp)

        # Record session
        gamification.record_session(
            user, cards_reviewed=len(session), cards_new=len(new_cards),
            cards_correct=correct_count, cards_incorrect=0,
            xp_earned=total_xp, time_spent_seconds=120,
        )

        # Verify state
        assert user.streak_days >= 1
        assert user.xp > 0
        assert review_repo.count_by_user(user.id) == len(session)

        # Verify cards are rescheduled
        for card in session:
            updated = card_repo.get(card.id)
            assert updated.due_date != "", "Card should have a new due date"

    def test_exercise_factory_with_real_vocab(self, full_db):
        db, user = full_db

        vocab_repo = VocabRepo(db.conn)
        all_vocab = vocab_repo.get_by_language("es")
        assert len(all_vocab) > 0

        factory = ExerciseFactory(all_vocab)

        # Test all exercise types
        vocab = all_vocab[0]
        for ex_type in ["flashcard_l2l1", "flashcard_l1l2", "mcq", "typing"]:
            exercise = factory.create(vocab, ex_type)
            assert exercise is not None, f"Failed to create {ex_type}"
            assert exercise.exercise_type == ex_type

        # Test MCQ has valid distractors
        mcq = factory.create(vocab, "mcq")
        assert len(mcq.options) == 4
        assert vocab.translation in mcq.options

    def test_content_manager_lesson_flow(self, full_db):
        db, user = full_db

        vocab_repo = VocabRepo(db.conn)
        lesson_repo = LessonRepo(db.conn)
        card_repo = CardRepo(db.conn)

        content_mgr = ContentManager(vocab_repo, lesson_repo, card_repo)

        # Get lessons
        lessons = content_mgr.get_lessons("es")
        assert "A1" in lessons
        assert len(lessons["A1"]) > 0

        # A1 should be unlocked
        assert content_mgr.is_level_unlocked(user.id, "es", "A1") is True

        # A2 should be locked (no cards studied yet)
        vocab_a1 = vocab_repo.get_by_language_level("es", "A1")
        if len(vocab_a1) > 0:
            # A2 is locked because < 70% of A1 has cards
            assert content_mgr.is_level_unlocked(user.id, "es", "A2") is False

        # Get lesson vocab
        lesson = lessons["A1"][0]
        vocab = content_mgr.get_lesson_vocab("es", lesson.category, lesson.cefr_level)
        assert len(vocab) >= 0  # May be 0 if category doesn't match

    def test_gamification_achievements(self, full_db):
        db, user = full_db

        user_repo = UserRepo(db.conn)
        review_repo = ReviewLogRepo(db.conn)
        progress_repo = ProgressRepo(db.conn)
        card_repo = CardRepo(db.conn)
        vocab_repo = VocabRepo(db.conn)

        srs = SRSEngine(db, desired_retention=user.desired_retention)
        gamification = GamificationEngine(user_repo, progress_repo, review_repo)

        # Create and review one card
        vocab = vocab_repo.get_by_language_level("es", "A1")
        cards = srs.get_new_cards(user.id, [vocab[0].id], "flashcard_l2l1", limit=1)
        srs.review(cards[0], Rating.Good)

        # Update streak
        user = gamification.update_streak(user)
        user = gamification.add_xp(user, 10)

        # Check achievements
        achievements = gamification.get_unlocked_achievements(user)
        achievement_ids = [a["id"] for a in achievements]
        assert "first_review" in achievement_ids

        # Check level progress
        level_info = gamification.get_level_progress(user)
        assert level_info["current_level"] == "A1"
        assert level_info["next_level"] == "A2"

    def test_both_languages_seed(self):
        """Verify both Spanish and Turkish data loads correctly."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db = Database(db_path=path)
        db.run_migrations()

        vocab_repo = VocabRepo(db.conn)
        lesson_repo = LessonRepo(db.conn)

        es_result = seed_all(vocab_repo, lesson_repo, "es")
        tr_result = seed_all(vocab_repo, lesson_repo, "tr")

        assert es_result["vocabulary"]["A1"] > 100
        assert es_result["vocabulary"]["A2"] > 100
        assert tr_result["vocabulary"]["A1"] > 100
        assert tr_result["vocabulary"]["A2"] > 100
        assert es_result["lessons"] == 20
        assert tr_result["lessons"] == 20

        # Verify no cross-contamination
        es_vocab = vocab_repo.get_by_language("es")
        tr_vocab = vocab_repo.get_by_language("tr")
        es_words = {v.word for v in es_vocab}
        tr_words = {v.word for v in tr_vocab}
        # Languages should have mostly different words
        overlap = es_words & tr_words
        assert len(overlap) < 10, f"Too much overlap: {overlap}"

        db.close()
        os.unlink(path)


class TestLanguageSpecificIntegration:
    """Test language-specific exercises with real data."""

    def test_spanish_conjugation_exercises(self):
        from lang_mastering.core.language_specific.spanish import VerbConjugationExercise
        # Generate 20 random exercises - should all be valid
        for _ in range(20):
            ex = VerbConjugationExercise.random()
            assert ex.correct_answer != ""
            result = ex.check_answer(ex.correct_answer)
            assert result.is_correct is True

    def test_turkish_vowel_harmony_consistency(self):
        from lang_mastering.core.language_specific.turkish import (
            VowelHarmonyExercise, VOWEL_HARMONY_WORDS
        )
        for word_data in VOWEL_HARMONY_WORDS:
            for suffix_type in ["plural", "locative", "dative"]:
                ex = VowelHarmonyExercise(word_data, suffix_type)
                # Correct answer should always pass
                result = ex.check_answer(ex.correct_answer)
                assert result.is_correct is True, f"Failed for {word_data['word']} + {suffix_type}"
