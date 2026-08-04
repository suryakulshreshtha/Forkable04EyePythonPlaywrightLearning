"""Base class every page object inherits from.

What belongs in a base page
---------------------------
Only things every page genuinely shares: navigation, generic waits, screenshot
helpers. Resist the urge to put `login()` here -- that is LoginPage's job. A
bloated base class is the most common way POM rots.

What must NEVER go in a page object
-----------------------------------
Assertions. Page objects expose state and actions; tests decide what is correct.
The one exception people make is `expect_loaded()` style guards, and even that
is arguable. We keep assertions in tests.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Locator, Page

from utils.config import settings
from utils.logger import get_logger

log = get_logger("pages")


class BasePage:
    #: Subclasses set this; used by open() and is_current().
    path: str = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    # ---- navigation --------------------------------------------------------
    def open(self, path: str | None = None) -> BasePage:
        target = settings.url(path if path is not None else self.path)
        log.info("navigating to %s", target)
        self.page.goto(target, wait_until="domcontentloaded")
        return self

    @property
    def title(self) -> str:
        return self.page.title()

    @property
    def current_url(self) -> str:
        return self.page.url

    # ---- generic helpers ---------------------------------------------------
    def alert(self) -> Locator:
        """Any role=alert on the page (error banners)."""
        return self.page.get_by_role("alert")

    def status_message(self) -> Locator:
        """Any role=status on the page (success banners)."""
        return self.page.get_by_role("status")

    def screenshot(self, name: str) -> Path:
        """Manual screenshot. Note pytest-playwright already captures one on
        failure -- use this only for deliberate documentation shots."""
        out = Path("reports/screenshots")
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{name}.png"
        self.page.screenshot(path=str(path), full_page=True)
        return path

    def reload(self) -> None:
        self.page.reload(wait_until="domcontentloaded")
