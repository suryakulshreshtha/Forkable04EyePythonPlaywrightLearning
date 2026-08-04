"""Dashboard page object, including a nested component object."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage
from pages.components.nav_bar import NavBar


class DashboardPage(BasePage):
    path = "/dashboard"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Composition over inheritance: the nav bar appears on several pages,
        # so it is its own object rather than duplicated methods.
        self.nav = NavBar(page)

        self.welcome: Locator = page.get_by_test_id("welcome")
        self.load_button: Locator = page.get_by_role("button", name="Load users")
        self.search: Locator = page.get_by_label("Filter by name")
        self.role_filter: Locator = page.get_by_label("Role")
        self.table: Locator = page.get_by_role("table", name="Users")
        self.rows: Locator = page.get_by_test_id("user-row")
        self.table_status: Locator = page.get_by_test_id("table-status")
        self.download_button: Locator = page.get_by_test_id("download-csv")

    # ---- actions -----------------------------------------------------------
    def load_users(self) -> DashboardPage:
        self.load_button.click()
        return self

    def filter_by_name(self, term: str) -> DashboardPage:
        self.search.fill(term)
        return self

    def filter_by_role(self, role: str) -> DashboardPage:
        self.role_filter.select_option(role)
        return self

    def download_csv(self):
        """Returns the Playwright Download object.

        expect_download() is a *context manager* -- you must start waiting
        BEFORE the click, otherwise you race the browser.
        """
        with self.page.expect_download() as download_info:
            self.download_button.click()
        return download_info.value

    # ---- state -------------------------------------------------------------
    def row_count(self) -> int:
        return self.rows.count()

    def row_for(self, name: str) -> Locator:
        """Filter a locator list by inner text -- the readable alternative to
        an XPath with contains()."""
        return self.rows.filter(has_text=name)

    def names(self) -> list[str]:
        return [cell.strip() for cell in self.rows.locator("td:nth-child(2)").all_inner_texts()]
