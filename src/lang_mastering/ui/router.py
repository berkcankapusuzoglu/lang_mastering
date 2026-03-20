"""Page navigation router for the Flet app — web-compatible version."""

import traceback
import flet as ft


class Router:
    """Manages page routing for Flet web mode.

    Uses page.add/remove to swap page content controls.
    Never calls page.controls.clear() which breaks Flet 0.82 web.
    """

    def __init__(self, page: ft.Page, pages: dict):
        self.page = page
        self.pages = pages
        self._current_route = None
        self._current_control = None

    def navigate(self, route: str):
        """Navigate to a route by swapping the page content."""
        if route not in self.pages:
            route = "/"
        self._current_route = route

        try:
            view = self.pages[route](self.page)
        except Exception:
            err = ft.Text(f"Page error: {traceback.format_exc()}", size=12, color="red")
            self.page.add(err)
            self.page.update()
            return

        # Remove previous content control (if any)
        if self._current_control is not None:
            try:
                self.page.controls.remove(self._current_control)
            except ValueError:
                pass

        # Extract content and nav bar from the View
        if isinstance(view, ft.View):
            # Wrap view controls in a single Container
            content = ft.Container(
                content=ft.Column(
                    view.controls,
                    expand=True,
                    spacing=0,
                ),
                bgcolor=view.bgcolor or "#1a1a2e",
                expand=True,
            )
            self.page.bottom_appbar = view.bottom_appbar
            if view.bgcolor:
                self.page.bgcolor = view.bgcolor
        else:
            content = view

        self._current_control = content
        self.page.add(content)
        self.page.update()
