"""Tests for language-specific exercises."""

import pytest

from lang_mastering.core.language_specific.spanish import (
    VerbConjugationExercise,
    SerEstarExercise,
    GenderAgreementExercise,
    VERB_CONJUGATIONS,
    SER_ESTAR_SENTENCES,
)
from lang_mastering.core.language_specific.turkish import (
    VowelHarmonyExercise,
    SuffixStackingExercise,
    SOVWordOrderExercise,
    get_vowel_type,
    get_last_vowel,
    VOWEL_HARMONY_WORDS,
)


class TestSpanishConjugation:
    def test_correct_conjugation(self):
        ex = VerbConjugationExercise("ser", "presente", "yo", "soy")
        result = ex.check_answer("soy")
        assert result.is_correct is True

    def test_wrong_conjugation(self):
        ex = VerbConjugationExercise("ser", "presente", "yo", "soy")
        result = ex.check_answer("estoy")
        assert result.is_correct is False

    def test_random_creates_valid(self):
        ex = VerbConjugationExercise.random()
        assert ex.correct_answer != ""
        assert ex.prompt != ""

    def test_all_verbs_have_conjugations(self):
        for verb, tenses in VERB_CONJUGATIONS.items():
            for tense, forms in tenses.items():
                for pronoun, form in forms.items():
                    assert form, f"Missing: {verb} {tense} {pronoun}"


class TestSerEstar:
    def test_correct_answer(self):
        data = SER_ESTAR_SENTENCES[0]  # "Yo ___ estudiante." -> soy
        ex = SerEstarExercise(data)
        result = ex.check_answer(data["answer"])
        assert result.is_correct is True

    def test_wrong_answer(self):
        data = SER_ESTAR_SENTENCES[0]
        ex = SerEstarExercise(data)
        result = ex.check_answer("estoy")
        assert result.is_correct is False

    def test_feedback_includes_reason(self):
        data = SER_ESTAR_SENTENCES[4]  # estar - temporary state
        ex = SerEstarExercise(data)
        result = ex.check_answer("soy")
        assert "temporary state" in result.feedback


class TestGenderAgreement:
    def test_correct_article(self):
        data = {"word": "casa", "article": "la", "gender": "f"}
        ex = GenderAgreementExercise(data)
        result = ex.check_answer("la")
        assert result.is_correct is True

    def test_wrong_article(self):
        data = {"word": "casa", "article": "la", "gender": "f"}
        ex = GenderAgreementExercise(data)
        result = ex.check_answer("el")
        assert result.is_correct is False

    def test_has_two_options(self):
        ex = GenderAgreementExercise()
        assert len(ex.options) == 2


class TestTurkishVowelHarmony:
    def test_get_vowel_type_back(self):
        assert get_vowel_type("araba") == "back"
        assert get_vowel_type("okul") == "back"

    def test_get_vowel_type_front(self):
        assert get_vowel_type("ev") == "front"
        assert get_vowel_type("göz") == "front"

    def test_get_last_vowel(self):
        assert get_last_vowel("ev") == "e"
        assert get_last_vowel("araba") == "a"

    def test_correct_suffix(self):
        data = {"word": "ev", "last_vowel": "e", "type": "front", "meaning": "house"}
        ex = VowelHarmonyExercise(data, "plural")
        result = ex.check_answer("evler")
        assert result.is_correct is True

    def test_wrong_suffix(self):
        data = {"word": "ev", "last_vowel": "e", "type": "front", "meaning": "house"}
        ex = VowelHarmonyExercise(data, "plural")
        result = ex.check_answer("evlar")
        assert result.is_correct is False


class TestSuffixStacking:
    def test_correct_stacked_form(self):
        example = {"root": "ev", "steps": [("ev", "house"), ("evler", "+ler"), ("evlerde", "+de")], "final": "evlerde", "meaning": "in the houses"}
        ex = SuffixStackingExercise(example)
        result = ex.check_answer("evlerde")
        assert result.is_correct is True

    def test_wrong_form(self):
        example = {"root": "ev", "steps": [("ev", "house"), ("evler", "+ler"), ("evlerde", "+de")], "final": "evlerde", "meaning": "in the houses"}
        ex = SuffixStackingExercise(example)
        result = ex.check_answer("evlarda")
        assert result.is_correct is False


class TestSOVWordOrder:
    def test_correct_order(self):
        data = {"words": ["Ben", "okula", "gidiyorum"], "translation": "I am going to school"}
        ex = SOVWordOrderExercise(data)
        result = ex.check_answer("Ben okula gidiyorum")
        assert result.is_correct is True

    def test_wrong_order(self):
        data = {"words": ["Ben", "okula", "gidiyorum"], "translation": "I am going to school"}
        ex = SOVWordOrderExercise(data)
        result = ex.check_answer("gidiyorum Ben okula")
        assert result.is_correct is False

    def test_scrambles_words(self):
        data = {"words": ["Ben", "okula", "gidiyorum"], "translation": "I am going to school"}
        ex = SOVWordOrderExercise(data)
        assert len(ex.options) == 3
