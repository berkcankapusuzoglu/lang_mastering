"""Pronunciation scoring using OpenAI Whisper for speech recognition."""

import os
import tempfile
from typing import Optional

from Levenshtein import distance as levenshtein_distance


class PronunciationEngine:
    """Handles speech-to-text transcription and pronunciation scoring."""

    def __init__(self, model_name: str = "base"):
        self._model = None
        self._model_name = model_name

    @property
    def model(self):
        """Lazy-load Whisper model on first use (~140MB for 'base')."""
        if self._model is None:
            import whisper
            self._model = whisper.load_model(self._model_name)
        return self._model

    def transcribe(self, audio_path: str, language: str = "es") -> str:
        """Transcribe an audio file to text."""
        lang_code = language  # 'es' for Spanish, 'tr' for Turkish
        result = self.model.transcribe(
            audio_path,
            language=lang_code,
            fp16=False,  # CPU-safe
        )
        return result["text"].strip()

    def score_pronunciation(
        self, audio_path: str, expected_text: str, language: str = "es"
    ) -> dict:
        """Score pronunciation by comparing transcription to expected text.

        Returns:
            dict with keys:
                - transcription: what Whisper heard
                - expected: what was expected
                - score: 0-100 overall score
                - word_scores: list of per-word results
                - feedback: human-readable feedback string
                - suggested_rating: FSRS rating (1-4)
        """
        transcription = self.transcribe(audio_path, language)

        # Normalize for comparison
        trans_lower = transcription.lower().strip()
        expected_lower = expected_text.lower().strip()

        # Overall similarity
        if not trans_lower or not expected_lower:
            return {
                "transcription": transcription,
                "expected": expected_text,
                "score": 0,
                "word_scores": [],
                "feedback": "Could not detect speech. Try again.",
                "suggested_rating": 1,
            }

        # Word-level scoring
        trans_words = trans_lower.split()
        expected_words = expected_lower.split()

        word_scores = []
        for i, exp_word in enumerate(expected_words):
            if i < len(trans_words):
                trans_word = trans_words[i]
                dist = levenshtein_distance(trans_word, exp_word)
                max_len = max(len(trans_word), len(exp_word))
                similarity = (1 - dist / max_len) * 100 if max_len > 0 else 0
                word_scores.append({
                    "expected": exp_word,
                    "heard": trans_word,
                    "score": round(similarity),
                    "correct": similarity >= 80,
                })
            else:
                word_scores.append({
                    "expected": exp_word,
                    "heard": "",
                    "score": 0,
                    "correct": False,
                })

        # Overall score
        if word_scores:
            overall_score = sum(w["score"] for w in word_scores) / len(word_scores)
        else:
            overall_score = 0

        overall_score = round(overall_score)

        # Determine feedback and rating
        if overall_score >= 90:
            feedback = "Excellent pronunciation!"
            suggested_rating = 4
        elif overall_score >= 80:
            feedback = "Good pronunciation!"
            suggested_rating = 3
        elif overall_score >= 60:
            feedback = "Keep practicing - some words need work."
            suggested_rating = 2
        else:
            feedback = "Try again - focus on the highlighted words."
            suggested_rating = 1

        return {
            "transcription": transcription,
            "expected": expected_text,
            "score": overall_score,
            "word_scores": word_scores,
            "feedback": feedback,
            "suggested_rating": suggested_rating,
        }
