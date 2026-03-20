"""Spanish-specific grammar exercises: conjugation, ser/estar, gender agreement."""

import random
from dataclasses import dataclass, field
from typing import Optional

from lang_mastering.core.exercises import Exercise, ExerciseResult
from lang_mastering.models import VocabularyItem


# Common verb conjugation data
VERB_CONJUGATIONS = {
    "ser": {
        "presente": {"yo": "soy", "tú": "eres", "él/ella": "es", "nosotros": "somos", "ellos/ellas": "son"},
        "pretérito": {"yo": "fui", "tú": "fuiste", "él/ella": "fue", "nosotros": "fuimos", "ellos/ellas": "fueron"},
    },
    "estar": {
        "presente": {"yo": "estoy", "tú": "estás", "él/ella": "está", "nosotros": "estamos", "ellos/ellas": "están"},
        "pretérito": {"yo": "estuve", "tú": "estuviste", "él/ella": "estuvo", "nosotros": "estuvimos", "ellos/ellas": "estuvieron"},
    },
    "tener": {
        "presente": {"yo": "tengo", "tú": "tienes", "él/ella": "tiene", "nosotros": "tenemos", "ellos/ellas": "tienen"},
        "pretérito": {"yo": "tuve", "tú": "tuviste", "él/ella": "tuvo", "nosotros": "tuvimos", "ellos/ellas": "tuvieron"},
    },
    "hacer": {
        "presente": {"yo": "hago", "tú": "haces", "él/ella": "hace", "nosotros": "hacemos", "ellos/ellas": "hacen"},
        "pretérito": {"yo": "hice", "tú": "hiciste", "él/ella": "hizo", "nosotros": "hicimos", "ellos/ellas": "hicieron"},
    },
    "ir": {
        "presente": {"yo": "voy", "tú": "vas", "él/ella": "va", "nosotros": "vamos", "ellos/ellas": "van"},
        "pretérito": {"yo": "fui", "tú": "fuiste", "él/ella": "fue", "nosotros": "fuimos", "ellos/ellas": "fueron"},
    },
    "comer": {
        "presente": {"yo": "como", "tú": "comes", "él/ella": "come", "nosotros": "comemos", "ellos/ellas": "comen"},
        "pretérito": {"yo": "comí", "tú": "comiste", "él/ella": "comió", "nosotros": "comimos", "ellos/ellas": "comieron"},
    },
    "hablar": {
        "presente": {"yo": "hablo", "tú": "hablas", "él/ella": "habla", "nosotros": "hablamos", "ellos/ellas": "hablan"},
        "pretérito": {"yo": "hablé", "tú": "hablaste", "él/ella": "habló", "nosotros": "hablamos", "ellos/ellas": "hablaron"},
    },
    "vivir": {
        "presente": {"yo": "vivo", "tú": "vives", "él/ella": "vive", "nosotros": "vivimos", "ellos/ellas": "viven"},
        "pretérito": {"yo": "viví", "tú": "viviste", "él/ella": "vivió", "nosotros": "vivimos", "ellos/ellas": "vivieron"},
    },
    "querer": {
        "presente": {"yo": "quiero", "tú": "quieres", "él/ella": "quiere", "nosotros": "queremos", "ellos/ellas": "quieren"},
        "pretérito": {"yo": "quise", "tú": "quisiste", "él/ella": "quiso", "nosotros": "quisimos", "ellos/ellas": "quisieron"},
    },
    "poder": {
        "presente": {"yo": "puedo", "tú": "puedes", "él/ella": "puede", "nosotros": "podemos", "ellos/ellas": "pueden"},
        "pretérito": {"yo": "pude", "tú": "pudiste", "él/ella": "pudo", "nosotros": "pudimos", "ellos/ellas": "pudieron"},
    },
}

# Ser vs Estar contexts
SER_ESTAR_SENTENCES = [
    {"sentence": "Yo ___ estudiante.", "answer": "soy", "verb": "ser", "reason": "occupation/identity"},
    {"sentence": "Ella ___ muy alta.", "answer": "es", "verb": "ser", "reason": "physical characteristic"},
    {"sentence": "Nosotros ___ de España.", "answer": "somos", "verb": "ser", "reason": "origin"},
    {"sentence": "La fiesta ___ el sábado.", "answer": "es", "verb": "ser", "reason": "event time"},
    {"sentence": "Yo ___ cansado.", "answer": "estoy", "verb": "estar", "reason": "temporary state"},
    {"sentence": "El café ___ caliente.", "answer": "está", "verb": "estar", "reason": "condition"},
    {"sentence": "Ellos ___ en la casa.", "answer": "están", "verb": "estar", "reason": "location"},
    {"sentence": "Tú ___ enfermo hoy.", "answer": "estás", "verb": "estar", "reason": "temporary condition"},
    {"sentence": "La comida ___ deliciosa.", "answer": "está", "verb": "estar", "reason": "subjective experience"},
    {"sentence": "Mi padre ___ médico.", "answer": "es", "verb": "ser", "reason": "profession"},
    {"sentence": "El libro ___ de María.", "answer": "es", "verb": "ser", "reason": "possession"},
    {"sentence": "Nosotros ___ contentos.", "answer": "estamos", "verb": "estar", "reason": "emotion/state"},
]


class VerbConjugationExercise(Exercise):
    """Conjugate a verb given infinitive + pronoun + tense."""

    def __init__(self, verb: str, tense: str, pronoun: str, correct_form: str):
        dummy_vocab = VocabularyItem(word=verb, translation=verb)
        super().__init__(
            exercise_type="conjugation",
            vocab_item=dummy_vocab,
            prompt=f"Conjugate '{verb}' for '{pronoun}' in {tense}:",
            correct_answer=correct_form,
            hint=f"{verb} ({tense})",
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

    @classmethod
    def random(cls) -> "VerbConjugationExercise":
        verb = random.choice(list(VERB_CONJUGATIONS.keys()))
        tense = random.choice(list(VERB_CONJUGATIONS[verb].keys()))
        pronoun = random.choice(list(VERB_CONJUGATIONS[verb][tense].keys()))
        correct = VERB_CONJUGATIONS[verb][tense][pronoun]
        return cls(verb, tense, pronoun, correct)


class SerEstarExercise(Exercise):
    """Fill in ser or estar in context."""

    def __init__(self, sentence_data: dict = None):
        if sentence_data is None:
            sentence_data = random.choice(SER_ESTAR_SENTENCES)
        dummy_vocab = VocabularyItem(word=sentence_data["verb"], translation=sentence_data["verb"])
        super().__init__(
            exercise_type="ser_estar",
            vocab_item=dummy_vocab,
            prompt=sentence_data["sentence"],
            correct_answer=sentence_data["answer"],
            hint=f"Reason: {sentence_data['reason']}",
        )

    def check_answer(self, user_answer: str) -> ExerciseResult:
        answer = user_answer.strip().lower()
        correct = self.correct_answer.strip().lower()
        if answer == correct:
            return ExerciseResult(
                is_correct=True, user_answer=user_answer,
                correct_answer=self.correct_answer,
                feedback=f"Correct! ({self.hint})", score=1.0, suggested_rating=3,
            )
        return ExerciseResult(
            is_correct=False, user_answer=user_answer,
            correct_answer=self.correct_answer,
            feedback=f"The answer is '{self.correct_answer}' ({self.hint})",
            score=0.0, suggested_rating=1,
        )


class GenderAgreementExercise(Exercise):
    """Select the correct article (el/la) or adjective ending."""

    GENDER_DATA = [
        {"word": "casa", "article": "la", "gender": "f"},
        {"word": "libro", "article": "el", "gender": "m"},
        {"word": "mesa", "article": "la", "gender": "f"},
        {"word": "perro", "article": "el", "gender": "m"},
        {"word": "gata", "article": "la", "gender": "f"},
        {"word": "coche", "article": "el", "gender": "m"},
        {"word": "ciudad", "article": "la", "gender": "f"},
        {"word": "problema", "article": "el", "gender": "m"},
        {"word": "mano", "article": "la", "gender": "f"},
        {"word": "día", "article": "el", "gender": "m"},
        {"word": "agua", "article": "el", "gender": "f"},  # el agua (fem with el)
        {"word": "noche", "article": "la", "gender": "f"},
        {"word": "sol", "article": "el", "gender": "m"},
        {"word": "flor", "article": "la", "gender": "f"},
        {"word": "color", "article": "el", "gender": "m"},
    ]

    def __init__(self, word_data: dict = None):
        if word_data is None:
            word_data = random.choice(self.GENDER_DATA)
        dummy_vocab = VocabularyItem(word=word_data["word"], translation="", gender=word_data["gender"])
        super().__init__(
            exercise_type="gender",
            vocab_item=dummy_vocab,
            prompt=f"___ {word_data['word']}",
            correct_answer=word_data["article"],
            options=["el", "la"],
            hint=f"Gender: {'masculine' if word_data['gender'] == 'm' else 'feminine'}",
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
            feedback=f"It's '{self.correct_answer} {self.vocab_item.word}'",
            score=0.0, suggested_rating=1,
        )
