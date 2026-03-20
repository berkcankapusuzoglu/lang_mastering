"""Page navigation router for the Flet app — using page.views."""

import traceback
import flet as ft


class Router:
    """Manages page routing using Flet's native page.views stack."""

    def __init__(self, page: ft.Page, pages: dict):
        self.page = page
        self.pages = pages
        self._current_route = None

    def navigate(self, route: str):
        """Navigate to a route using page.views."""
        if route not in self.pages:
            route = "/"
        self._current_route = route

        try:
            view = self.pages[route](self.page)
        except Exception:
            view = ft.View(
                route,
                [ft.Text(f"Page error: {traceback.format_exc()}", size=12, color="red")],
            )

        if not isinstance(view, ft.View):
            view = ft.View(route, [view])

        # Replace all views with just this one
        self.page.views.clear()
        self.page.views.append(view)
        self.page.update()
