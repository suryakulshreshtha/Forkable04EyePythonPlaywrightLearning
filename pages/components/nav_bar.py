"""Component object for the shared navigation bar.

Component objects are page objects scoped to a fragment. They keep page classes
small and stop you copy-pasting the same three locators into six pages.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page


class NavBar:
    def __init__(self, page: Page) -> None:
        self.page = page
        # Scope everything to the <nav> so a stray "Dashboard" word elsewhere
        # on the page cannot make these locators ambiguous.
        self.root: Locator = page.get_by_role("navigation", name="Main")
        self.dashboard_link: Locator = self.root.get_by_role("link", name="Dashboard")
        self.upload_link: Locator = self.root.get_by_role("link", name="Upload")
        self.slow_page_link: Locator = self.root.get_by_role("link", name="Slow Page")
        self.current_user: Locator = page.get_by_test_id("current-user")
        self.logout_link: Locator = page.get_by_test_id("logout-link")

    def go_to_upload(self) -> None:
        self.upload_link.click()

    def logout(self) -> None:
        self.logout_link.click()

    def signed_in_as(self) -> str:
        return self.current_user.inner_text().replace("Signed in as", "").strip()
