"""Load JSON vocabulary and curriculum data into the database."""

import json
from pathlib import Path
from typing import Optional

from lang_mastering.db.repositories import VocabRepo, LessonRepo
from lang_mastering.models import VocabularyItem, Lesson


DATA_DIR = Path(__file__).parent


def seed_vocabulary(vocab_repo: VocabRepo, language: str, cefr_level: str, filename: Optional[str] = None) -> int:
    """Load vocabulary from a JSON file into the database. Returns count of items loaded."""
    if filename is None:
        lang_name = "spanish" if language == "es" else "turkish"
        filename = f"{lang_name}_{cefr_level.lower()}.json"

    filepath = DATA_DIR / "vocabularies" / filename
    if not filepath.exists():
        return 0

    with open(filepath, "r", encoding="utf-8") as f:
        items = json.load(f)

    # Check if already seeded
    existing = vocab_repo.get_by_language_level(language, cefr_level)
    if existing:
        return 0

    vocab_items = []
    for item in items:
        vocab_items.append(VocabularyItem(
            language=language,
            cefr_level=cefr_level,
            category=item.get("category", ""),
            word=item["word"],
            translation=item["translation"],
            phonetic=item.get("phonetic", ""),
            example_sentence=item.get("example_sentence", ""),
            example_translation=item.get("example_translation", ""),
            gender=item.get("gender", ""),
            part_of_speech=item.get("part_of_speech", ""),
            notes=item.get("notes", ""),
            tags=",".join(item["tags"]) if isinstance(item.get("tags"), list) else item.get("tags", ""),
        ))

    vocab_repo.create_many(vocab_items)
    return len(vocab_items)


def seed_curriculum(lesson_repo: LessonRepo, language: str) -> int:
    """Load curriculum from JSON into the database. Returns count of lessons loaded."""
    lang_name = "spanish" if language == "es" else "turkish"
    filepath = DATA_DIR / "curricula" / f"{lang_name}_curriculum.json"

    if not filepath.exists():
        return 0

    # Check if already seeded
    existing = lesson_repo.get_by_language(language)
    if existing:
        return 0

    with open(filepath, "r", encoding="utf-8") as f:
        lessons_data = json.load(f)

    lessons = []
    for item in lessons_data:
        lessons.append(Lesson(
            language=item["language"],
            cefr_level=item["cefr_level"],
            lesson_number=item["lesson_number"],
            title=item["title"],
            description=item.get("description", ""),
            category=item.get("category", ""),
            exercise_types_json=json.dumps(item.get("exercise_types", [])),
        ))

    lesson_repo.create_many(lessons)
    return len(lessons)


def seed_all(vocab_repo: VocabRepo, lesson_repo: LessonRepo, language: str) -> dict:
    """Seed all data for a language. Returns counts."""
    results = {"vocabulary": {}, "lessons": 0}

    for level in ["A1", "A2", "B1"]:
        count = seed_vocabulary(vocab_repo, language, level)
        if count > 0:
            results["vocabulary"][level] = count

    results["lessons"] = seed_curriculum(lesson_repo, language)
    return results
