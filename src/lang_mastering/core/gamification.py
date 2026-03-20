"""XP calculation, streak tracking, and achievements."""

from datetime import date, timedelta
from typing import Optional

from lang_mastering.db.repositories import UserRepo, ProgressRepo, ReviewLogRepo
from lang_mastering.models import User, DailyProgress


# XP values per rating
XP_PER_RATING = {
    1: 0,   # Again
    2: 5,   # Hard
    3: 10,  # Good
    4: 15,  # Easy
}

# Streak multiplier thresholds
STREAK_MULTIPLIERS = {
    0: 1.0,
    3: 1.2,   # 3+ days: 20% bonus
    7: 1.5,   # 7+ days: 50% bonus
    14: 1.8,  # 14+ days: 80% bonus
    30: 2.0,  # 30+ days: double XP
}

# Level thresholds (XP required for each level)
LEVEL_THRESHOLDS = {
    "A1": 0,
    "A2": 1000,
    "B1": 3000,
    "B2": 7000,
    "C1": 15000,
    "C2": 30000,
}

# Achievements
ACHIEVEMENTS = [
    {"id": "first_review", "name": "First Steps", "description": "Complete your first review", "icon": "\U0001f3af", "condition": lambda stats: stats["total_reviews"] >= 1},
    {"id": "streak_3", "name": "On a Roll", "description": "3-day streak", "icon": "\U0001f525", "condition": lambda stats: stats["streak"] >= 3},
    {"id": "streak_7", "name": "Week Warrior", "description": "7-day streak", "icon": "\u26a1", "condition": lambda stats: stats["streak"] >= 7},
    {"id": "streak_30", "name": "Monthly Master", "description": "30-day streak", "icon": "\U0001f3c6", "condition": lambda stats: stats["streak"] >= 30},
    {"id": "reviews_100", "name": "Century", "description": "100 reviews completed", "icon": "\U0001f4af", "condition": lambda stats: stats["total_reviews"] >= 100},
    {"id": "reviews_500", "name": "Dedicated", "description": "500 reviews completed", "icon": "\U0001f4da", "condition": lambda stats: stats["total_reviews"] >= 500},
    {"id": "accuracy_90", "name": "Sharp Mind", "description": "90%+ accuracy in a session", "icon": "\U0001f3af", "condition": lambda stats: stats["session_accuracy"] >= 90},
    {"id": "xp_1000", "name": "Rising Star", "description": "Earn 1000 XP", "icon": "\u2b50", "condition": lambda stats: stats["total_xp"] >= 1000},
    {"id": "xp_5000", "name": "Knowledge Seeker", "description": "Earn 5000 XP", "icon": "\U0001f31f", "condition": lambda stats: stats["total_xp"] >= 5000},
]


class GamificationEngine:
    """Manages XP, streaks, levels, and achievements."""

    def __init__(self, user_repo: UserRepo, progress_repo: ProgressRepo, review_repo: ReviewLogRepo):
        self.user_repo = user_repo
        self.progress_repo = progress_repo
        self.review_repo = review_repo

    def calculate_xp(self, rating: int, streak_days: int) -> int:
        """Calculate XP for a single review."""
        base_xp = XP_PER_RATING.get(rating, 0)
        multiplier = 1.0
        for threshold, mult in sorted(STREAK_MULTIPLIERS.items(), reverse=True):
            if streak_days >= threshold:
                multiplier = mult
                break
        return int(base_xp * multiplier)

    def update_streak(self, user: User) -> User:
        """Update user's streak based on last review date."""
        today = date.today().isoformat()

        if user.last_review_date is None:
            user.streak_days = 1
        elif user.last_review_date == today:
            pass  # Already reviewed today
        elif user.last_review_date == (date.today() - timedelta(days=1)).isoformat():
            user.streak_days += 1
        else:
            user.streak_days = 1  # Streak broken

        user.last_review_date = today
        self.user_repo.update(user)
        return user

    def add_xp(self, user: User, xp: int) -> User:
        """Add XP to user and check for level up."""
        user.xp += xp

        # Check for level up
        for level, threshold in sorted(LEVEL_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if user.xp >= threshold:
                if LEVEL_THRESHOLDS.get(user.current_level, 0) < threshold:
                    user.current_level = level
                break

        self.user_repo.update(user)
        return user

    def record_session(
        self, user: User, cards_reviewed: int, cards_new: int,
        cards_correct: int, cards_incorrect: int, xp_earned: int,
        time_spent_seconds: int,
    ) -> DailyProgress:
        """Record a session's progress."""
        today = date.today().isoformat()

        # Get or create today's progress
        existing = self.progress_repo.get_by_user_date(user.id, today)
        if existing:
            existing.cards_reviewed += cards_reviewed
            existing.cards_new += cards_new
            existing.cards_correct += cards_correct
            existing.cards_incorrect += cards_incorrect
            existing.xp_earned += xp_earned
            existing.time_spent_seconds += time_spent_seconds
            return self.progress_repo.upsert(existing)
        else:
            progress = DailyProgress(
                user_id=user.id, date=today,
                cards_reviewed=cards_reviewed, cards_new=cards_new,
                cards_correct=cards_correct, cards_incorrect=cards_incorrect,
                xp_earned=xp_earned, time_spent_seconds=time_spent_seconds,
            )
            return self.progress_repo.upsert(progress)

    def get_unlocked_achievements(self, user: User) -> list[dict]:
        """Check which achievements the user has unlocked."""
        total_reviews = self.review_repo.count_by_user(user.id)
        stats = {
            "total_reviews": total_reviews,
            "streak": user.streak_days,
            "total_xp": user.xp,
            "session_accuracy": 0,  # Would need session context
        }
        return [a for a in ACHIEVEMENTS if a["condition"](stats)]

    def get_level_progress(self, user: User) -> dict:
        """Get progress toward next level."""
        current_threshold = LEVEL_THRESHOLDS.get(user.current_level, 0)
        levels = sorted(LEVEL_THRESHOLDS.items(), key=lambda x: x[1])
        next_level = None
        next_threshold = None
        for level, threshold in levels:
            if threshold > current_threshold:
                next_level = level
                next_threshold = threshold
                break

        if next_threshold is None:
            return {"current_level": user.current_level, "progress": 1.0, "xp_to_next": 0, "next_level": None}

        xp_in_level = user.xp - current_threshold
        xp_needed = next_threshold - current_threshold
        progress = min(xp_in_level / xp_needed, 1.0) if xp_needed > 0 else 1.0

        return {
            "current_level": user.current_level,
            "next_level": next_level,
            "progress": progress,
            "xp_to_next": max(next_threshold - user.xp, 0),
        }
