"""Exercise types and factory for generating exercises from vocabulary items."""

import random
from dataclasses import dataclass, field
from typing import Optional

from Levenshtein import distance as levenshtein_distance

from lang_mastering.models import VocabularyItem


@dataclass
class ExerciseResult:
    """Result of answering an exercise."""
    is_correct: bool
    user_answer: str
    correct_answer: str
    feedback: str = ""
    score: float = 0.0  # 0.0 to 1.0
    suggested_rating: int = 3  # FSRS rating: 1=Again, 2=Hard, 3=Good, 4=Easy


@dataclass
class Exercise:
    """Base exercise data."""
    exercise_type: str
    vocab_item: VocabularyItem
    prompt: str = ""
    correct_answer: str = ""
    options: list[str] = field(default_factory=list)  # For MCQ
    hint: str = ""

    def check_answer(self, user_answer: str) -> ExerciseResult:
        """Check the user's answer. Override in subclasses for custom logic."""
        raise NotImplementedError


class FlashcardL2L1Exercise(Exercise):
    """Show target language word, reveal English translation."""

    def __init__(self, vocab: VocabularyItem):
        super().__init__(
            exercise_type="flashcard_l2l1",
            vocab_item=vocab,
            prompt=vocab.word,
            correct_answer=vocab.translation,
            hint=vocab.example_sentence,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        # Flashcards are self-rated, so user_answer is the rating string
        rating = int(user_answer) if user_answer.isdigit() else 3
        return ExerciseResult(
            is_correct=rating >= 3,
            user_answer=user_answer,
            correct_answer=self.correct_answer,
            score=rating / 4.0,
            suggested_rating=rating,
        )


class FlashcardL1L2Exercise(Exercise):
    """Show English word, reveal target language translation."""

    def __init__(self, vocab: VocabularyItem):
        super().__init__(
            exercise_type="flashcard_l1l2",
            vocab_item=vocab,
            prompt=vocab.translation,
            correct_answer=vocab.word,
            hint=vocab.example_sentence,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        rating = int(user_answer) if user_answer.isdigit() else 3
        return ExerciseResult(
            is_correct=rating >= 3,
            user_answer=user_answer,
            correct_answer=self.correct_answer,
            score=rating / 4.0,
            suggested_rating=rating,
        )


class MultipleChoiceExercise(Exercise):
    """Select the correct translation from 4 options."""

    def __init__(self, vocab: VocabularyItem, distractors: list[str]):
        options = [vocab.translation] + distractors[:3]
        random.shuffle(options)
        super().__init__(
            exercise_type="mcq",
            vocab_item=vocab,
            prompt=vocab.word,
            correct_answer=vocab.translation,
            options=options,
            hint=vocab.example_sentence,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        is_correct = user_answer.strip().lower() == self.correct_answer.strip().lower()
        return ExerciseResult(
            is_correct=is_correct,
            user_answer=user_answer,
            correct_answer=self.correct_answer,
            feedback="Correct!" if is_correct else f"The answer is: {self.correct_answer}",
            score=1.0 if is_correct else 0.0,
            suggested_rating=3 if is_correct else 1,
        )


class TypingExercise(Exercise):
    """Type the target language word given the English translation."""

    def __init__(self, vocab: VocabularyItem):
        super().__init__(
            exercise_type="typing",
            vocab_item=vocab,
            prompt=vocab.translation,
            correct_answer=vocab.word,
            hint=vocab.example_sentence,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        answer = user_answer.strip().lower()
        correct = self.correct_answer.strip().lower()
        dist = levenshtein_distance(answer, correct)

        if dist == 0:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Perfect!", score=1.0, suggested_rating=3,
            )
        elif dist <= 1:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"Almost! Correct spelling: {self.correct_answer}",
                score=0.7, suggested_rating=2,
            )
        else:
            return ExerciseResult(
                is_correct=False, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"The correct answer is: {self.correct_answer}",
                score=0.0, suggested_rating=1,
            )


class ClozeExercise(Exercise):
    """Fill in the blank in a sentence."""

    def __init__(self, vocab: VocabularyItem):
        sentence = vocab.example_sentence
        word = vocab.word
        # Replace the word in the sentence with a blank
        cloze_sentence = sentence.replace(word, "______", 1)
        if cloze_sentence == sentence:
            # Word not found in example, try case-insensitive
            import re
            cloze_sentence = re.sub(re.escape(word), "______", sentence, count=1, flags=re.IGNORECASE)

        super().__init__(
            exercise_type="cloze",
            vocab_item=vocab,
            prompt=cloze_sentence,
            correct_answer=word,
            hint=vocab.translation,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        answer = user_answer.strip().lower()
        correct = self.correct_answer.strip().lower()
        dist = levenshtein_distance(answer, correct)

        if dist == 0:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Correct!", score=1.0, suggested_rating=3,
            )
        elif dist <= 1:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"Close! The exact word is: {self.correct_answer}",
                score=0.7, suggested_rating=2,
            )
        else:
            return ExerciseResult(
                is_correct=False, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"The correct word is: {self.correct_answer}",
                score=0.0, suggested_rating=1,
            )


class SentenceBuildingExercise(Exercise):
    """Arrange scrambled words into the correct sentence."""

    def __init__(self, vocab: VocabularyItem):
        sentence = vocab.example_sentence
        words = sentence.split()
        scrambled = words.copy()
        # Ensure we actually scramble
        for _ in range(10):
            random.shuffle(scrambled)
            if scrambled != words:
                break

        super().__init__(
            exercise_type="sentence_building",
            vocab_item=vocab,
            prompt=vocab.example_translation,
            correct_answer=sentence,
            options=scrambled,
            hint=vocab.translation,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        # Normalize whitespace and compare
        answer = " ".join(user_answer.strip().split()).lower()
        correct = " ".join(self.correct_answer.strip().split()).lower()
        # Strip punctuation for comparison
        import re
        answer_clean = re.sub(r'[^\w\s]', '', answer)
        correct_clean = re.sub(r'[^\w\s]', '', correct)

        if answer_clean == correct_clean:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Correct!", score=1.0, suggested_rating=3,
            )
        else:
            return ExerciseResult(
                is_correct=False, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"Correct order: {self.correct_answer}",
                score=0.0, suggested_rating=1,
            )


class ListeningExercise(Exercise):
    """Listen to audio, then select or type what was heard."""

    def __init__(self, vocab: VocabularyItem, distractors: list[str] = None):
        # Listening can be MCQ-style (select what you heard) or typing
        if distractors:
            options = [vocab.word] + distractors[:3]
            random.shuffle(options)
        else:
            options = []

        super().__init__(
            exercise_type="listening",
            vocab_item=vocab,
            prompt="[Listen to the audio]",
            correct_answer=vocab.word,
            options=options,
            hint=vocab.translation,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        answer = user_answer.strip().lower()
        correct = self.correct_answer.strip().lower()

        if answer == correct:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Correct!", score=1.0, suggested_rating=3,
            )
        else:
            dist = levenshtein_distance(answer, correct)
            if dist <= 1:
                return ExerciseResult(
                    is_correct=True, user_answer=user_answer,
                    correct_answer=self.correct_answer,
                    feedback=f"Almost! It was: {self.correct_answer}",
                    score=0.7, suggested_rating=2,
                )
            return ExerciseResult(
                is_correct=False, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"The word was: {self.correct_answer}",
                score=0.0, suggested_rating=1,
            )


class SpeakingExercise(Exercise):
    """See word/sentence, record yourself, Whisper compares."""

    def __init__(self, vocab: VocabularyItem):
        super().__init__(
            exercise_type="speaking",
            vocab_item=vocab,
            prompt=vocab.word,
            correct_answer=vocab.word,
            hint=vocab.translation,
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        # user_answer is the score from pronunciation engine (as string)
        try:
            score = int(user_answer)
        except (ValueError, TypeError):
            score = 0

        if score >= 80:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Great pronunciation!", score=score / 100,
                suggested_rating=3,
            )
        elif score >= 60:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Good try, keep practicing!", score=score / 100,
                suggested_rating=2,
            )
        else:
            return ExerciseResult(
                is_correct=False, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Try again!", score=score / 100,
                suggested_rating=1,
            )


class ExerciseFactory:
    """Creates exercises from vocabulary items."""

    EXERCISE_TYPES = {
        "flashcard_l2l1": FlashcardL2L1Exercise,
        "flashcard_l1l2": FlashcardL1L2Exercise,
        "mcq": MultipleChoiceExercise,
        "typing": TypingExercise,
        "cloze": ClozeExercise,
        "sentence_building": SentenceBuildingExercise,
        "listening": ListeningExercise,
        "speaking": SpeakingExercise,
    }

    def __init__(self, all_vocab: list[VocabularyItem]):
        """Initialize with all vocabulary for generating distractors."""
        self.all_vocab = all_vocab

    def create(self, vocab: VocabularyItem, exercise_type: str) -> Optional[Exercise]:
        """Create an exercise of the given type for the vocabulary item."""
        if exercise_type == "mcq":
            distractors = self._get_distractors(vocab, count=3)
            return MultipleChoiceExercise(vocab, distractors)

        if exercise_type == "listening":
            distractors = self._get_word_distractors(vocab, count=3)
            return ListeningExercise(vocab, distractors)

        cls = self.EXERCISE_TYPES.get(exercise_type)
        if cls is None:
            return None

        return cls(vocab)

    def _get_distractors(self, vocab: VocabularyItem, count: int = 3) -> list[str]:
        """Get random distractor translations for MCQ."""
        candidates = [
            v.translation for v in self.all_vocab
            if v.id != vocab.id and v.translation != vocab.translation
        ]
        if len(candidates) < count:
            return candidates
        return random.sample(candidates, count)

    def _get_word_distractors(self, vocab: VocabularyItem, count: int = 3) -> list[str]:
        """Get random distractor words (target language) for listening exercises."""
        candidates = [
            v.word for v in self.all_vocab
            if v.id != vocab.id and v.word != vocab.word
        ]
        if len(candidates) < count:
            return candidates
        return random.sample(candidates, count)
