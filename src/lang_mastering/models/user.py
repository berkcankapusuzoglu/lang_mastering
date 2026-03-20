from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class User:
    id: Optional[int] = None
    name: str = ""
    target_language: str = "es"  # 'es' or 'tr'
    current_level: str = "A1"  # A1, A2, B1, B2, C1, C2
    xp: int = 0
    streak_days: int = 0
    last_review_date: Optional[str] = None  # ISO format date string
    daily_goal: int = 20  # cards per day
    desired_retention: float = 0.9
