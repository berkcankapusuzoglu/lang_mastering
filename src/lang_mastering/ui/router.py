"""Page navigation router for the Flet app."""

import flet as ft


class Router:
    """Manages page routing via a persistent content container."""

    def __init__(self, page: ft.Page, pages: dict):
        self.page = page
        self.pages = pages
        self._current_route = None
        # Single persistent container that holds all page content
        self._container = ft.Column(expand=True, spacing=0)
        self.page.add(self._container)

    def navigate(self, route: str):
        """Navigate to a route by swapping container content."""
        if route not in self.pages:
            route = "/"
        self._current_route = route
        view = self.pages[route](self.page)

        # Replace container content
        self._container.controls.clear()
        if isinstance(view, ft.View):
            for ctrl in view.controls:
                self._container.controls.append(ctrl)
            self.page.bottom_appbar = view.bottom_appbar
            if view.bgcolor:
                self.page.bgcolor = view.bgcolor
        else:
            self._container.controls.append(view)

        self._container.update()
