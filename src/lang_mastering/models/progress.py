from dataclasses import dataclass
from typing import Optional


@dataclass
class DailyProgress:
    id: Optional[int] = None
    user_id: int = 0
    date: str = ""  # ISO format date string
    cards_reviewed: int = 0
    cards_new: int = 0
    cards_correct: int = 0
    cards_incorrect: int = 0
    xp_earned: int = 0
    time_spent_seconds: int = 0
