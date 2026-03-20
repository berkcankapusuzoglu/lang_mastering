from dataclasses import dataclass
from typing import Optional


@dataclass
class VocabularyItem:
    id: Optional[int] = None
    language: str = ""  # 'es' or 'tr'
    cefr_level: str = "A1"
    category: str = ""
    word: str = ""
    translation: str = ""
    phonetic: str = ""
    example_sentence: str = ""
    example_translation: str = ""
    gender: str = ""  # for Spanish: m/f/n
    part_of_speech: str = ""  # noun, verb, adj, etc.
    notes: str = ""
    audio_cache_path: str = ""
    tags: str = ""  # comma-separated
