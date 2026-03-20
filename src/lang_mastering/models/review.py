from dataclasses import dataclass
from typing import Optional


@dataclass
class ReviewRecord:
    id: Optional[int] = None
    card_id: int = 0
    user_id: int = 0
    rating: int = 0  # 1=Again, 2=Hard, 3=Good, 4=Easy
    fsrs_review_log_json: str = "{}"
    exercise_type: str = ""
    response_time_ms: int = 0
    was_correct: bool = False
    reviewed_at: str = ""  # ISO format datetime string
