"""Page navigation router for the Flet app — no Views, direct page.add."""

import traceback
import flet as ft


class Router:
    """Manages page routing using direct page.add/remove.

    Pages return a dict with 'content' (Container) and optional 'nav_bar'.
    Router swaps the content Container on navigate.
    """

    def __init__(self, page: ft.Page, pages: dict):
        self.page = page
        self.pages = pages
        self._current_route = None
        self._current_content = None

    def navigate(self, route: str):
        """Navigate to a route."""
        if route not in self.pages:
            route = "/"
        self._current_route = route

        try:
            result = self.pages[route](self.page)
        except Exception:
            self.page.add(ft.Text(f"Page error: {traceback.format_exc()}", size=12, color="red"))
            self.page.update()
            return

        # Handle both dict and View returns for backwards compat
        if isinstance(result, dict):
            content = result.get("content")
            nav_bar = result.get("nav_bar")
        elif isinstance(result, ft.View):
            # Legacy View: extract first control as content
            content = result.controls[0] if result.controls else ft.Text("Empty page")
            nav_bar = result.bottom_appbar
        else:
            content = result
            nav_bar = None

        # Remove previous content
        if self._current_content is not None:
            try:
                self.page.controls.remove(self._current_content)
            except (ValueError, Exception):
                pass

        # Add new content
        self._current_content = content
        self.page.add(content)

        # Set nav bar
        if nav_bar is not None:
            self.page.bottom_appbar = nav_bar

        self.page.update()
