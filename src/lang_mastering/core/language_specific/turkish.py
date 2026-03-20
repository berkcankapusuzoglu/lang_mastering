"""Turkish-specific grammar exercises: vowel harmony, suffix stacking, SOV word order."""

import random
from dataclasses import dataclass, field
from typing import Optional

from lang_mastering.core.exercises import Exercise, ExerciseResult
from lang_mastering.models import VocabularyItem


# Vowel harmony rules
BACK_VOWELS = set("aıou")
FRONT_VOWELS = set("eiöü")

# Suffix harmony pairs
SUFFIX_PAIRS = {
    "plural": {"back": "-lar", "front": "-ler"},
    "locative": {"back": "-da", "front": "-de"},
    "locative_voiceless": {"back": "-ta", "front": "-te"},
    "ablative": {"back": "-dan", "front": "-den"},
    "ablative_voiceless": {"back": "-tan", "front": "-ten"},
    "dative": {"back": "-a", "front": "-e"},
    "accusative": {"back": "-ı", "front": "-i"},
    "genitive": {"back": "-ın", "front": "-in"},
    "possessive_1s": {"back": "-ım", "front": "-im"},
}

# Voiceless consonants (require -t- instead of -d-)
VOICELESS = set("çfhkpqsşt")

VOWEL_HARMONY_WORDS = [
    {"word": "ev", "last_vowel": "e", "type": "front", "meaning": "house"},
    {"word": "araba", "last_vowel": "a", "type": "back", "meaning": "car"},
    {"word": "kitap", "last_vowel": "a", "type": "back", "meaning": "book"},
    {"word": "göz", "last_vowel": "ö", "type": "front", "meaning": "eye"},
    {"word": "okul", "last_vowel": "u", "type": "back", "meaning": "school"},
    {"word": "süt", "last_vowel": "ü", "type": "front", "meaning": "milk"},
    {"word": "çocuk", "last_vowel": "u", "type": "back", "meaning": "child"},
    {"word": "köpek", "last_vowel": "e", "type": "front", "meaning": "dog"},
    {"word": "kedi", "last_vowel": "i", "type": "front", "meaning": "cat"},
    {"word": "masa", "last_vowel": "a", "type": "back", "meaning": "table"},
    {"word": "gül", "last_vowel": "ü", "type": "front", "meaning": "rose"},
    {"word": "kuş", "last_vowel": "u", "type": "back", "meaning": "bird"},
    {"word": "deniz", "last_vowel": "i", "type": "front", "meaning": "sea"},
    {"word": "yol", "last_vowel": "o", "type": "back", "meaning": "road"},
    {"word": "ağaç", "last_vowel": "a", "type": "back", "meaning": "tree"},
]

# SOV sentence patterns
SOV_SENTENCES = [
    {"words": ["Ben", "okula", "gidiyorum"], "translation": "I am going to school"},
    {"words": ["O", "kitap", "okuyor"], "translation": "He/She is reading a book"},
    {"words": ["Biz", "Türkçe", "öğreniyoruz"], "translation": "We are learning Turkish"},
    {"words": ["Ali", "çay", "içiyor"], "translation": "Ali is drinking tea"},
    {"words": ["Çocuklar", "parkta", "oynuyor"], "translation": "Children are playing in the park"},
    {"words": ["Annem", "yemek", "pişiriyor"], "translation": "My mother is cooking food"},
    {"words": ["Babam", "gazete", "okuyor"], "translation": "My father is reading newspaper"},
    {"words": ["Kediler", "süt", "seviyor"], "translation": "Cats love milk"},
]


def get_last_vowel(word: str) -> str:
    """Get the last vowel in a Turkish word."""
    for char in reversed(word.lower()):
        if char in BACK_VOWELS | FRONT_VOWELS:
            return char
    return "a"  # default


def get_vowel_type(word: str) -> str:
    """Determine if a word uses front or back vowels."""
    last_v = get_last_vowel(word)
    return "front" if last_v in FRONT_VOWELS else "back"


class VowelHarmonyExercise(Exercise):
    """Select the correct suffix form based on vowel harmony."""

    def __init__(self, word_data: dict = None, suffix_type: str = None):
        if word_data is None:
            word_data = random.choice(VOWEL_HARMONY_WORDS)
        if suffix_type is None:
            suffix_type = random.choice(["plural", "locative", "dative"])

        vtype = word_data["type"]
        pair = SUFFIX_PAIRS[suffix_type]
        correct_suffix = pair[vtype]
        wrong_suffix = pair["front" if vtype == "back" else "back"]

        dummy_vocab = VocabularyItem(word=word_data["word"], translation=word_data["meaning"])
        options = [correct_suffix, wrong_suffix]
        random.shuffle(options)

        super().__init__(
            exercise_type="vowel_harmony",
            vocab_item=dummy_vocab,
            prompt=f"{word_data['word']} + {suffix_type} suffix = ?",
            correct_answer=f"{word_data['word']}{correct_suffix.lstrip('-')}",
            options=options,
            hint=f"Last vowel: {word_data['last_vowel']} ({vtype} vowel)",
        )
        self._correct_suffix = correct_suffix

    def check_answer(self, user_answer: str) -> ExerciseResult:
        answer = user_answer.strip().lower()
        # Accept either the full word or just the suffix
        if answer == self.correct_answer.lower() or answer == self._correct_suffix.lower() or answer == self._correct_suffix.lstrip("-").lower():
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"Correct! {self.hint}", score=1.0, suggested_rating=3,
            )
        return ExerciseResult(
            is_correct=False, user_answer=user_answer,
            correct_answer=self.correct_answer,
            feedback=f"The correct form is: {self.correct_answer} ({self.hint})",
            score=0.0, suggested_rating=1,
        )


class SuffixStackingExercise(Exercise):
    """Build a word by adding suffixes in sequence."""

    STACKING_EXAMPLES = [
        {"root": "ev", "steps": [("ev", "house"), ("evler", "+ler (plural)"), ("evlerde", "+de (locative)")], "final": "evlerde", "meaning": "in the houses"},
        {"root": "araba", "steps": [("araba", "car"), ("arabalar", "+lar (plural)"), ("arabalarda", "+da (locative)")], "final": "arabalarda", "meaning": "in the cars"},
        {"root": "göz", "steps": [("göz", "eye"), ("gözler", "+ler (plural)"), ("gözlerim", "+im (my)")], "final": "gözlerim", "meaning": "my eyes"},
        {"root": "kitap", "steps": [("kitap", "book"), ("kitaplar", "+lar (plural)"), ("kitaplarda", "+da (locative)")], "final": "kitaplarda", "meaning": "in the books"},
    ]

    def __init__(self, example: dict = None):
        if example is None:
            example = random.choice(self.STACKING_EXAMPLES)
        dummy_vocab = VocabularyItem(word=example["root"], translation=example["meaning"])
        steps_text = " → ".join(f"{s[0]} ({s[1]})" for s in example["steps"])
        super().__init__(
            exercise_type="suffix_stacking",
            vocab_item=dummy_vocab,
            prompt=f"Build: {example['meaning']}\nSteps: {steps_text}\nFinal form:",
            correct_answer=example["final"],
            hint=f"Root: {example['root']}",
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
        return ExerciseResult(
            is_correct=False, user_answer=user_answer,
            correct_answer=self.correct_answer,
            feedback=f"The correct form is: {self.correct_answer}",
            score=0.0, suggested_rating=1,
        )


class SOVWordOrderExercise(Exercise):
    """Arrange words into correct Turkish SOV order."""

    def __init__(self, sentence_data: dict = None):
        if sentence_data is None:
            sentence_data = random.choice(SOV_SENTENCES)

        correct_sentence = " ".join(sentence_data["words"])
        scrambled = sentence_data["words"].copy()
        for _ in range(10):
            random.shuffle(scrambled)
            if scrambled != sentence_data["words"]:
                break

        dummy_vocab = VocabularyItem(word=correct_sentence, translation=sentence_data["translation"])
        super().__init__(
            exercise_type="sov_word_order",
            vocab_item=dummy_vocab,
            prompt=sentence_data["translation"],
            correct_answer=correct_sentence,
            options=scrambled,
            hint="Turkish uses Subject-Object-Verb order",
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        answer = " ".join(user_answer.strip().split()).lower()
        correct = self.correct_answer.lower()
        if answer == correct:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback="Correct!", score=1.0, suggested_rating=3,
            )
        return ExerciseResult(
            is_correct=False, user_answer=user_answer,
            correct_answer=self.correct_answer,
            feedback=f"Correct order: {self.correct_answer}",
            score=0.0, suggested_rating=1,
        )
