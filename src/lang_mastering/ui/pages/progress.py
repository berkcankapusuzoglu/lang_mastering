"""Progress dashboard: charts, stats, streak heatmap, achievements."""

from datetime import date, timedelta

import flet as ft

from lang_mastering.core.gamification import GamificationEngine, ACHIEVEMENTS
from lang_mastering.db.repositories import UserRepo, ProgressRepo, ReviewLogRepo, CardRepo
from lang_mastering.ui.theme import (
    BG_COLOR, SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY,
    ACCENT_COLOR, SUCCESS_COLOR, ERROR_COLOR, get_language_color,
)


def progress_page(page: ft.Page) -> ft.View:
    """Build the progress dashboard page."""
    user = page.app_state.get("current_user")
    db = page.app_state.get("db")

    if user is None:
        from lang_mastering.ui.components.nav_bar import build_nav_bar
        return ft.View(
            "/progress",
            [ft.Container(
                content=ft.Column([
                    ft.Text("Please create a profile first", size=18, color=TEXT_SECONDARY),
                    ft.ElevatedButton("Go to Settings", on_click=lambda _: page.app_state.get("router").navigate("/settings")),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                bgcolor=BG_COLOR, expand=True, padding=20,
            )],
            bgcolor=BG_COLOR,
            bottom_appbar=build_nav_bar(page, 3),
        )

    user_repo = UserRepo(db.conn)
    progress_repo = ProgressRepo(db.conn)
    review_repo = ReviewLogRepo(db.conn)
    card_repo = CardRepo(db.conn)
    gamification = GamificationEngine(user_repo, progress_repo, review_repo)

    lang_color = get_language_color(user.target_language)
    level_info = gamification.get_level_progress(user)
    achievements = gamification.get_unlocked_achievements(user)

    # Get last 30 days of progress
    today = date.today()
    start = today - timedelta(days=29)
    daily_data = progress_repo.get_range(user.id, start.isoformat(), today.isoformat())

    # Stats
    total_reviews = review_repo.count_by_user(user.id)
    total_cards = card_repo.count_by_user(user.id)
    total_reviewed_today = 0
    total_correct_today = 0
    for d in daily_data:
        if d.date == today.isoformat():
            total_reviewed_today = d.cards_reviewed
            total_correct_today = d.cards_correct

    # Build streak heatmap (last 30 days)
    heatmap_cells = []
    date_set = {d.date: d for d in daily_data}
    for i in range(30):
        day = start + timedelta(days=i)
        day_str = day.isoformat()
        dp = date_set.get(day_str)
        if dp and dp.cards_reviewed > 0:
            intensity = min(dp.cards_reviewed / 20, 1.0)
            color = _interpolate_color("#1a1a2e", SUCCESS_COLOR, intensity)
        else:
            color = SURFACE_COLOR

        heatmap_cells.append(
            ft.Container(
                width=18, height=18, border_radius=3,
                bgcolor=color,
                tooltip=f"{day_str}: {dp.cards_reviewed if dp else 0} reviews",
            )
        )

    # Weekly review chart (bar chart using containers)
    chart_bars = []
    for i in range(7):
        day = today - timedelta(days=6 - i)
        day_str = day.isoformat()
        dp = date_set.get(day_str)
        count = dp.cards_reviewed if dp else 0
        max_height = 100
        bar_height = min(count / max(user.daily_goal, 1) * max_height, max_height)

        chart_bars.append(
            ft.Column([
                ft.Container(
                    width=30, height=max(bar_height, 2),
                    bgcolor=lang_color if count > 0 else SURFACE_COLOR,
                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                ),
                ft.Text(day.strftime("%a")[:2], size=10, color=TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        )

    # Achievements
    achievement_chips = []
    for a in achievements:
        achievement_chips.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(a["icon"], size=20),
                    ft.Column([
                        ft.Text(a["name"], size=12, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Text(a["description"], size=10, color=TEXT_SECONDARY),
                    ], spacing=2),
                ], spacing=8),
                bgcolor=SURFACE_COLOR, border_radius=8, padding=8,
            )
        )

    if not achievement_chips:
        achievement_chips = [ft.Text("Complete reviews to earn achievements!", size=14, color=TEXT_SECONDARY)]

    content = ft.Column([
        ft.Container(height=10),
        ft.Text("Progress", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
        ft.Container(height=15),

        # Level progress
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"Level {user.current_level}", size=18, weight=ft.FontWeight.BOLD, color=lang_color),
                    ft.Text(f"{user.xp} XP", size=16, color=ACCENT_COLOR),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=level_info["progress"], color=lang_color, bgcolor=BG_COLOR, height=8),
                ft.Text(
                    f"{level_info['xp_to_next']} XP to {level_info['next_level']}" if level_info["next_level"] else "Max level!",
                    size=12, color=TEXT_SECONDARY,
                ),
            ], spacing=6),
            bgcolor=SURFACE_COLOR, border_radius=12, padding=15,
        ),
        ft.Container(height=15),

        # Quick stats row
        ft.Row([
            _stat_box("\U0001f525", f"{user.streak_days}", "Streak"),
            _stat_box("\U0001f4dd", str(total_reviews), "Reviews"),
            _stat_box("\U0001f4e6", str(total_cards), "Cards"),
            _stat_box("\u2705", str(total_reviewed_today), "Today"),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        ft.Container(height=15),

        # Weekly chart
        ft.Container(
            content=ft.Column([
                ft.Text("This Week", size=16, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                ft.Container(height=8),
                ft.Row(chart_bars, alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ]),
            bgcolor=SURFACE_COLOR, border_radius=12, padding=15,
        ),
        ft.Container(height=15),

        # Streak heatmap
        ft.Container(
            content=ft.Column([
                ft.Text("30-Day Activity", size=16, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                ft.Container(height=8),
                ft.Row(heatmap_cells, wrap=True, spacing=3, run_spacing=3),
            ]),
            bgcolor=SURFACE_COLOR, border_radius=12, padding=15,
        ),
        ft.Container(height=15),

        # Achievements
        ft.Text("Achievements", size=16, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
        ft.Container(height=5),
        *achievement_chips,
        ft.Container(height=20),
    ], scroll=ft.ScrollMode.AUTO, expand=True)

    from lang_mastering.ui.components.nav_bar import build_nav_bar
    return ft.View(
        "/progress",
        [ft.Container(content=content, bgcolor=BG_COLOR, expand=True, padding=20)],
        bgcolor=BG_COLOR,
        bottom_appbar=build_nav_bar(page, 3),
    )


def _stat_box(emoji: str, value: str, label: str) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Text(emoji, size=20),
            ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Text(label, size=11, color=TEXT_SECONDARY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor=SURFACE_COLOR, border_radius=10, padding=10, width=80,
    )


def _interpolate_color(color1: str, color2: str, t: float) -> str:
    """Simple hex color interpolation."""
    c1 = tuple(int(color1.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    try:
        c2 = tuple(int(color2.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return color1
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"
