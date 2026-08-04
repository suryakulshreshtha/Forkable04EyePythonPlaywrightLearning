"""Login page object.

Locator strategy, best to worst:
  1. get_by_role(...)   - matches how a user/AT perceives the page, survives CSS
  2. get_by_label(...)  - great for form fields, forces accessible markup
  3. get_by_test_id(...)- explicit contract with devs, immune to copy changes
  4. CSS                - fine for structural hooks
  5. XPath              - last resort; brittle and unreadable

We deliberately mix 1-3 here so you can compare them side by side.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage
from pages.dashboard_page import DashboardPage


class LoginPage(BasePage):
    path = "/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Locators are lazy: nothing touches the DOM until an action or
        # assertion runs. That is why defining them in __init__ is safe even
        # before navigation.
        self.username: Locator = page.get_by_label("Username")
        self.password: Locator = page.get_by_label("Password")
        self.remember_me: Locator = page.get_by_label("Remember me")
        self.submit: Locator = page.get_by_role("button", name="Log in")
        self.error_banner: Locator = page.get_by_test_id("login-error")

    # ---- actions -----------------------------------------------------------
    def login(self, username: str, password: str, remember: bool = False) -> DashboardPage:
        """Happy-path action. Returns the NEXT page object.

        Returning the destination page is the POM idiom that makes tests read
        like prose:  dashboard = LoginPage(page).open().login(u, p)
        """
        self.username.fill(username)
        self.password.fill(password)
        if remember:
            self.remember_me.check()
        self.submit.click()
        return DashboardPage(self.page)

    def login_expecting_failure(self, username: str, password: str) -> LoginPage:
        """Unhappy path stays on this page, so return self."""
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()
        return self

    # ---- state -------------------------------------------------------------
    def error_text(self) -> str:
        return self.error_banner.inner_text()
