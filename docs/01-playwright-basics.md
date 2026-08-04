# 01 — Playwright basics

Companion to `tests/01_basics/`. Read a section, then read the matching test file.

## The object model

```
Playwright  →  Browser  →  BrowserContext  →  Page  →  Locator
```

- **Browser** — one launched process. Expensive (~1s). Shared across the whole session.
- **BrowserContext** — an isolated profile: own cookies, own storage, own cache. Cheap (~5ms).
  **This is the unit of test isolation.**
- **Page** — a tab.
- **Locator** — a *description* of how to find elements. Lazy and re-resolved on every use.

`pytest-playwright` gives you a fresh context per test automatically. That is why two tests can
never leak login state into each other, and why parallelism is safe.

## Locators

Priority order, best first:

| Strategy | Example | Use when |
| --- | --- | --- |
| `get_by_role` | `get_by_role("button", name="Log in")` | almost always |
| `get_by_label` | `get_by_label("Username")` | form fields |
| `get_by_placeholder` | `get_by_placeholder("demo")` | no label exists (fix the app) |
| `get_by_text` | `get_by_text("Welcome back")` | static content |
| `get_by_test_id` | `get_by_test_id("login-error")` | explicit dev contract |
| CSS | `locator("#username")` | structural hooks |
| XPath | `locator("//input[@name='u']")` | last resort |

Two things that trip people up:

- **Roles are not tag names.** `<input type="password">` has *no* implicit ARIA role, so
  `get_by_role("textbox")` will not find it. When a role locator surprises you, check the ARIA
  spec rather than guessing.
- **Strict mode is on by default.** A locator matching two elements raises instead of silently
  taking the first. This is a feature — silent first-match is how false-green suites are born.
  Fix it by scoping (`nav.get_by_role(...)`) or filtering (`.filter(has_text=...)`), not by
  reaching for `.first`.

Chaining and filtering beat clever selectors:

```python
rows = page.get_by_test_id("user-row")
rows.filter(has_text="Ada Lovelace")                       # by text
rows.filter(has=page.get_by_text("admin", exact=True))     # by descendant
rows.filter(has_not_text="Inactive")                       # negation
```

## Assertions

```python
expect(locator).to_be_visible()          # polls until true, or times out
assert locator.is_visible()              # one snapshot, no retry — avoid
```

Web-first assertions retry. That single property removes most beginner flakiness.

Common ones:

```python
expect(page).to_have_title("...")
expect(page).to_have_url(re.compile(r"/dashboard$"))   # string args match EXACTLY
expect(loc).to_be_visible() / to_be_hidden() / to_be_enabled() / to_be_checked()
expect(loc).to_have_text("exact") / to_contain_text("part")
expect(loc).to_have_count(5)
expect(loc).to_have_value("demo") / to_have_attribute("accept", ".txt,.csv")
expect(loc).to_have_text(["a", "b", "c"])   # a list asserts count AND order
expect.soft(loc).to_be_visible()            # collect failures, keep going
```

Every one takes `timeout=`. Raise it on the specific slow assertion, never globally — a global
bump hides regressions everywhere else.

## Actions and actionability

Before any action Playwright waits for the element to be attached, visible, stable, receiving
events, and enabled. That is why `page.get_by_role("button").click()` on a button that is enabled
500ms from now just works.

```python
loc.fill("text")                  # clear + set, fires input events. Default choice.
loc.press_sequentially("t", delay=50)   # real keystrokes; only when the app reacts per-key
loc.check() / loc.uncheck()       # idempotent
loc.select_option("admin")        # or label=/index=/value=
loc.set_input_files(path)         # or a dict with an in-memory buffer
loc.press("Enter")
```

## Waiting

**Never `time.sleep()`.** In order of preference:

1. Do nothing — auto-waiting handles it.
2. `expect(...)` with a bigger `timeout=`.
3. Explicit waits for things that are not DOM state:

```python
with page.expect_response("**/api/users") as info: ...   # network
with page.expect_download() as info: ...                 # download
with page.expect_popup() as info: ...                    # new tab
page.wait_for_function("() => window.chartReady")        # JS state
page.wait_for_url("**/dashboard")                        # navigation (globs OK here)
```

Note the asymmetry: `wait_for_url` accepts glob patterns; `expect(page).to_have_url` compares a
plain string **exactly**. Use a regex when you mean "ends with".

## Try it

```bash
pytest tests/01_basics -v
pytest tests/01_basics/test_05_waiting.py --headed --slowmo 500
```
