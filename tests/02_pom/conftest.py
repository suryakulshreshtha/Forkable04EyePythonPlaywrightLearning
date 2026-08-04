"""Page-object fixtures.

Making page objects into fixtures (rather than constructing them in each test)
gives you:
  * one place to change the constructor signature
  * free dependency injection of `page` / `authenticated_page`
  * tests that read as a sentence with no setup noise
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.upload_page import UploadPage


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page).open()


@pytest.fixture
def dashboard_page(authenticated_page: Page) -> DashboardPage:
    """Skips the login form entirely by reusing saved storage state."""
    return DashboardPage(authenticated_page).open()


@pytest.fixture
def upload_page(authenticated_page: Page) -> UploadPage:
    return UploadPage(authenticated_page).open()
