"""Page navigation router for the Flet app — web-compatible version."""

import traceback
import flet as ft


class Router:
    """Manages page routing for Flet web mode.

    Uses a single content Column added via page.add() to avoid
    page.controls.clear() which breaks Flet 0.82 web rendering.
    """

    def __init__(self, page: ft.Page, pages: dict):
        self.page = page
        self.pages = pages
        self._current_route = None
        self._content = ft.Column(expand=True, spacing=0)

    def get_container(self) -> ft.Column:
        """Return the content container to be added to the page."""
        return self._content

    def navigate(self, route: str):
        """Navigate to a route by swapping container children."""
        if route not in self.pages:
            route = "/"
        self._current_route = route

        try:
            view = self.pages[route](self.page)
        except Exception:
            self._content.controls.clear()
            self._content.controls.append(
                ft.Text(f"Page error: {traceback.format_exc()}", size=12, color="red")
            )
            self._content.update()
            return

        self._content.controls.clear()
        if isinstance(view, ft.View):
            for ctrl in view.controls:
                self._content.controls.append(ctrl)
            self.page.bottom_appbar = view.bottom_appbar
            if view.bgcolor:
                self.page.bgcolor = view.bgcolor
        else:
            self._content.controls.append(view)

        try:
            self._content.update()
        except Exception:
            pass
