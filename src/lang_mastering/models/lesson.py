from dataclasses import dataclass
from typing import Optional


@dataclass
class Lesson:
    id: Optional[int] = None
    language: str = ""
    cefr_level: str = "A1"
    lesson_number: int = 0
    title: str = ""
    description: str = ""
    category: str = ""
    exercise_types_json: str = "[]"
