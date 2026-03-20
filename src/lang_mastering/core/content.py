"""Content management: lessons, vocabulary, unlock progression."""

import json
from typing import Optional

from lang_mastering.db.repositories import VocabRepo, LessonRepo, CardRepo
from lang_mastering.models import Lesson, VocabularyItem


CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


class ContentManager:
    """Manages lesson content and progression."""

    def __init__(self, vocab_repo: VocabRepo, lesson_repo: LessonRepo, card_repo: CardRepo):
        self.vocab_repo = vocab_repo
        self.lesson_repo = lesson_repo
        self.card_repo = card_repo

    def get_lessons(self, language: str) -> dict[str, list[Lesson]]:
        """Get all lessons grouped by CEFR level."""
        lessons = self.lesson_repo.get_by_language(language)
        grouped = {}
        for lesson in lessons:
            if lesson.cefr_level not in grouped:
                grouped[lesson.cefr_level] = []
            grouped[lesson.cefr_level].append(lesson)
        return grouped

    def get_lesson_vocab(self, language: str, category: str, cefr_level: str) -> list[VocabularyItem]:
        """Get vocabulary items for a specific lesson category."""
        all_vocab = self.vocab_repo.get_by_language_level(language, cefr_level)
        if not category or category == "mixed":
            return all_vocab
        return [v for v in all_vocab if v.category == category]

    def get_lesson_exercise_types(self, lesson: Lesson) -> list[str]:
        """Get exercise types for a lesson."""
        return json.loads(lesson.exercise_types_json)

    def get_lesson_progress(self, user_id: int, lesson: Lesson, language: str) -> float:
        """Calculate completion percentage for a lesson (0.0 to 1.0)."""
        vocab = self.get_lesson_vocab(language, lesson.category, lesson.cefr_level)
        if not vocab:
            return 0.0

        reviewed_count = 0
        for v in vocab:
            cards = self.card_repo.get_by_user_and_vocab(user_id, v.id)
            if cards:
                reviewed_count += 1

        return reviewed_count / len(vocab)

    def is_level_unlocked(self, user_id: int, language: str, cefr_level: str) -> bool:
        """Check if a CEFR level is unlocked. A1 is always unlocked.
        Higher levels unlock when 70% of previous level vocab has cards."""
        level_idx = CEFR_ORDER.index(cefr_level) if cefr_level in CEFR_ORDER else 0
        if level_idx == 0:
            return True

        prev_level = CEFR_ORDER[level_idx - 1]
        prev_vocab = self.vocab_repo.get_by_language_level(language, prev_level)
        if not prev_vocab:
            return True  # No content for previous level

        studied = 0
        for v in prev_vocab:
            if self.card_repo.get_by_user_and_vocab(user_id, v.id):
                studied += 1

        return (studied / len(prev_vocab)) >= 0.7

    def get_vocab_count(self, language: str, cefr_level: str) -> int:
        """Get total vocabulary count for a language+level."""
        return len(self.vocab_repo.get_by_language_level(language, cefr_level))
