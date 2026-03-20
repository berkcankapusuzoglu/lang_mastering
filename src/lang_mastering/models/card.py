from dataclasses import dataclass
from typing import Optional


@dataclass
class CardRecord:
    """Wraps an FSRS Card with DB metadata."""
    id: Optional[int] = None
    user_id: int = 0
    vocabulary_id: int = 0
    exercise_type: str = ""  # flashcard_l2l1, flashcard_l1l2, mcq, typing, listening, speaking, cloze, sentence_building
    fsrs_card_json: str = "{}"
    is_suspended: bool = False
    due_date: str = ""  # ISO format datetime string
