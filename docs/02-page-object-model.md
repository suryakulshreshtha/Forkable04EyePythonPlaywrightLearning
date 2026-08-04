# 02 — Page Object Model

## The problem POM solves

Twelve tests each containing `page.locator("#login-btn")`. A dev renames the id. Twelve failures,
one cause, twelve edits. POM makes that one edit.

## The rules

**A page object exposes actions and state. It never asserts.**

```python
# pages/login_page.py
class LoginPage(BasePage):
    def login(self, username, password) -> DashboardPage:   # returns the NEXT page
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()
        return DashboardPage(self.page)
```

```python
# tests/02_pom/test_login.py
def test_valid_login(login_page):
    dashboard = login_page.login("demo", "Password123")
    expect(dashboard.welcome).to_have_text("Welcome back, demo.")   # the TEST asserts
```

Why no assertions inside page objects? Because a page object with assertions can only be used one
way. `login()` is needed by tests that are not about login at all, and they must not inherit
somebody else's expectations.

**Return the destination.** `login()` returns `DashboardPage`; `login_expecting_failure()` returns
`self`. Your IDE then autocompletes the next legal step, and a redirect change becomes a type
error rather than a mystery.

**Locators live in `__init__`.** They are lazy — nothing touches the DOM until used — so defining
them before navigation is safe.

## Component objects

The nav bar appears on several pages. It gets its own class (`pages/components/nav_bar.py`), and
pages *compose* it:

```python
class DashboardPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.nav = NavBar(page)     # dashboard_page.nav.logout()
```

Composition over inheritance. A deep page-object inheritance tree is the most common way POM turns
into the thing it was meant to prevent.

## What goes in `BasePage`

Only what *every* page shares: `open()`, `current_url`, `alert()`, `screenshot()`. Not `login()`.
If you find yourself adding a method that three pages use and four do not, that is a component
object, not a base-class method.

## Fixtures over constructors

```python
@pytest.fixture
def dashboard_page(authenticated_page) -> DashboardPage:
    return DashboardPage(authenticated_page).open()
```

Tests then read as one line of intent, and changing the constructor is a one-file change.

## When POM is not worth it

- Under ~20 tests, or a throwaway spike
- A page used by exactly one test
- When the object is a thin pass-through (`def click_x(self): self.x.click()`) that adds a layer
  without adding meaning

Signs it has rotted: page objects that assert; methods returning `None` when they should return a
page; a `BasePage` over 200 lines; page objects that know about test data.

## Exercise

`pages/upload_page.py` exists but has no POM tests. Write `tests/02_pom/test_upload.py`.
