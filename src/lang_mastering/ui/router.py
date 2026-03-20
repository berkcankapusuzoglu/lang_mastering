"""Page navigation router for the Flet app."""

import flet as ft


class Router:
    """Manages page routing using page.controls (Flet 0.82+ compatible)."""

    def __init__(self, page: ft.Page, pages: dict):
        self.page = page
        self.pages = pages  # {route_str: page_builder_fn}
        self._current_route = None

    def navigate(self, route: str):
        """Navigate to a route by rebuilding page controls."""
        if route not in self.pages:
            route = "/"
        self._current_route = route
        view = self.pages[route](self.page)

        # Extract controls and bottom bar from the View
        self.page.controls.clear()
        if isinstance(view, ft.View):
            for ctrl in view.controls:
                self.page.controls.append(ctrl)
            self.page.bottom_appbar = view.bottom_appbar
            if view.bgcolor:
                self.page.bgcolor = view.bgcolor
        else:
            self.page.controls.append(view)

        self.page.update()
