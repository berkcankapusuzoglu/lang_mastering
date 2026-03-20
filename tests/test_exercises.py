"""Tests for exercise types and factory."""

import pytest

from lang_mastering.core.exercises import (
    ExerciseFactory,
    FlashcardL2L1Exercise,
    FlashcardL1L2Exercise,
    MultipleChoiceExercise,
    TypingExercise,
    ClozeExercise,
    SentenceBuildingExercise,
)
from lang_mastering.models import VocabularyItem


@pytest.fixture
def sample_vocab():
    return VocabularyItem(
        id=1, language="es", cefr_level="A1", category="greetings",
        word="hola", translation="hello", phonetic="'o.la",
        example_sentence="¡Hola, amigo!", example_translation="Hello, friend!",
        part_of_speech="interjection",
    )


@pytest.fixture
def vocab_list():
    return [
        VocabularyItem(id=1, language="es", word="hola", translation="hello", example_sentence="¡Hola, amigo!", example_translation="Hello, friend!"),
        VocabularyItem(id=2, language="es", word="adiós", translation="goodbye", example_sentence="¡Adiós, amigo!", example_translation="Goodbye, friend!"),
        VocabularyItem(id=3, language="es", word="gracias", translation="thank you", example_sentence="Muchas gracias.", example_translation="Thank you very much."),
        VocabularyItem(id=4, language="es", word="agua", translation="water", example_sentence="Quiero agua.", example_translation="I want water."),
        VocabularyItem(id=5, language="es", word="pan", translation="bread", example_sentence="El pan es fresco.", example_translation="The bread is fresh."),
    ]


class TestFlashcardL2L1:
    def test_creation(self, sample_vocab):
        ex = FlashcardL2L1Exercise(sample_vocab)
        assert ex.exercise_type == "flashcard_l2l1"
        assert ex.prompt == "hola"
        assert ex.correct_answer == "hello"

    def test_self_rate_good(self, sample_vocab):
        ex = FlashcardL2L1Exercise(sample_vocab)
        result = ex.check_answer("3")
        assert result.is_correct is True
        assert result.suggested_rating == 3

    def test_self_rate_again(self, sample_vocab):
        ex = FlashcardL2L1Exercise(sample_vocab)
        result = ex.check_answer("1")
        assert result.is_correct is False
        assert result.suggested_rating == 1


class TestFlashcardL1L2:
    def test_creation(self, sample_vocab):
        ex = FlashcardL1L2Exercise(sample_vocab)
        assert ex.prompt == "hello"
        assert ex.correct_answer == "hola"


class TestMultipleChoice:
    def test_has_four_options(self, sample_vocab):
        distractors = ["goodbye", "thank you", "water"]
        ex = MultipleChoiceExercise(sample_vocab, distractors)
        assert len(ex.options) == 4
        assert "hello" in ex.options

    def test_correct_answer(self, sample_vocab):
        distractors = ["goodbye", "thank you", "water"]
        ex = MultipleChoiceExercise(sample_vocab, distractors)
        result = ex.check_answer("hello")
        assert result.is_correct is True
        assert result.suggested_rating == 3

    def test_wrong_answer(self, sample_vocab):
        distractors = ["goodbye", "thank you", "water"]
        ex = MultipleChoiceExercise(sample_vocab, distractors)
        result = ex.check_answer("goodbye")
        assert result.is_correct is False
        assert result.suggested_rating == 1


class TestTyping:
    def test_exact_match(self, sample_vocab):
        ex = TypingExercise(sample_vocab)
        result = ex.check_answer("hola")
        assert result.is_correct is True
        assert result.suggested_rating == 3
        assert result.score == 1.0

    def test_one_typo(self, sample_vocab):
        ex = TypingExercise(sample_vocab)
        result = ex.check_answer("holá")
        assert result.is_correct is True
        assert result.suggested_rating == 2
        assert result.score == 0.7

    def test_wrong_answer(self, sample_vocab):
        ex = TypingExercise(sample_vocab)
        result = ex.check_answer("adios")
        assert result.is_correct is False
        assert result.suggested_rating == 1

    def test_case_insensitive(self, sample_vocab):
        ex = TypingExercise(sample_vocab)
        result = ex.check_answer("Hola")
        assert result.is_correct is True


class TestCloze:
    def test_creates_blank(self):
        vocab = VocabularyItem(
            id=1, language="es", word="agua",
            translation="water",
            example_sentence="Quiero agua por favor.",
            example_translation="I want water please.",
        )
        ex = ClozeExercise(vocab)
        assert "______" in ex.prompt
        assert "agua" not in ex.prompt

    def test_correct_fill(self):
        vocab = VocabularyItem(
            id=1, language="es", word="agua",
            translation="water",
            example_sentence="Quiero agua por favor.",
            example_translation="I want water please.",
        )
        ex = ClozeExercise(vocab)
        result = ex.check_answer("agua")
        assert result.is_correct is True


class TestSentenceBuilding:
    def test_scrambles_words(self):
        vocab = VocabularyItem(
            id=1, language="es", word="hola",
            translation="hello",
            example_sentence="Hola amigo como estas",
            example_translation="Hello friend how are you",
        )
        ex = SentenceBuildingExercise(vocab)
        assert len(ex.options) == 4

    def test_correct_order(self):
        vocab = VocabularyItem(
            id=1, language="es", word="hola",
            translation="hello",
            example_sentence="Hola amigo",
            example_translation="Hello friend",
        )
        ex = SentenceBuildingExercise(vocab)
        result = ex.check_answer("Hola amigo")
        assert result.is_correct is True


class TestExerciseFactory:
    def test_create_flashcard(self, vocab_list):
        factory = ExerciseFactory(vocab_list)
        ex = factory.create(vocab_list[0], "flashcard_l2l1")
        assert ex is not None
        assert ex.exercise_type == "flashcard_l2l1"

    def test_create_mcq(self, vocab_list):
        factory = ExerciseFactory(vocab_list)
        ex = factory.create(vocab_list[0], "mcq")
        assert ex is not None
        assert len(ex.options) == 4
        assert "hello" in ex.options

    def test_create_typing(self, vocab_list):
        factory = ExerciseFactory(vocab_list)
        ex = factory.create(vocab_list[0], "typing")
        assert ex is not None
        assert ex.exercise_type == "typing"

    def test_distractors_not_include_correct(self, vocab_list):
        factory = ExerciseFactory(vocab_list)
        distractors = factory._get_distractors(vocab_list[0], count=3)
        assert "hello" not in distractors
        assert len(distractors) == 3

    def test_unknown_type_returns_none(self, vocab_list):
        factory = ExerciseFactory(vocab_list)
        ex = factory.create(vocab_list[0], "unknown_type")
        assert ex is None
