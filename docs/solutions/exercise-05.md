# Exercise 5 — a 12-second delay

```python
def test_very_slow_content(page: Page) -> None:
    page.goto("/flaky?delay=12000")
    expect(page.get_by_test_id("late-banner")).to_be_visible(timeout=15000)
```

**The minimum change** is `timeout=` on that one assertion.

**What you get if you do nothing:**

```
TimeoutError: Locator expected to be visible
Call log:
  - waiting for get_by_test_id("late-banner")
  -   locator resolved to hidden <div id="late-content" hidden>...
```

The message names the locator, its resolved state, and how long it waited. Read it before
reaching for a debugger.

**What NOT to do**

- Do not raise `DEFAULT_TIMEOUT_MS` globally. Every failing test in the suite would then take 15
  seconds to fail, and a real 3-second regression elsewhere would go unnoticed.
- Do not `time.sleep(13)`. Same waiting, no polling, and a guaranteed 13 seconds even when the
  content arrives in one.

Raise the timeout on the specific assertion that is legitimately slow, and leave the default tight.
