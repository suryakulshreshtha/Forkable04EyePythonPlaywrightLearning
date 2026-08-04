"""LESSON 5 -- Waiting: the one habit that separates flaky suites from stable ones.

THE RULE
--------
    time.sleep() is never the answer.

A sleep is a bet that the app is slower than X and faster than X. In CI, on a
cold, shared, 2-core runner, you lose that bet. Playwright gives you three
better tools, in order of preference:

  1. Do nothing. Actions and expect() auto-wait. This covers ~90% of cases.
  2. expect(...) with a longer timeout, for genuinely slow operations.
  3. page.wait_for_* / expect_* for events you cannot express as an assertion
     (a network response, a popup, a download).

/flaky renders its banner after a configurable delay, so we can prove all this
deterministically.
"""

import time

import pytest
from playwright.sync_api import Page, expect


def test_auto_waiting_needs_no_code(page: Page) -> None:
    page.goto("/flaky?delay=1500")

    # The banner does not exist yet. We write ZERO waiting code.
    expect(page.get_by_test_id("late-banner")).to_be_visible()


def test_actionability_waits_for_enabled(page: Page) -> None:
    page.goto("/flaky?delay=1000")

    # The button appears at 1000ms but stays DISABLED until 1500ms.
    # click() waits for it to become enabled before dispatching the event --
    # it does not click a disabled button and silently do nothing.
    page.get_by_test_id("late-button").click()
    expect(page.get_by_test_id("click-result")).to_be_visible()


def test_custom_timeout_for_a_genuinely_slow_thing(page: Page) -> None:
    page.goto("/flaky?delay=4000")

    # Our default timeout is 10s (conftest), but be explicit when a specific
    # step is known to be slow. Raise the timeout on the ASSERTION, not
    # globally -- a global bump hides regressions everywhere else.
    expect(page.get_by_test_id("late-banner")).to_be_visible(timeout=8000)


def test_wait_for_a_network_response(page: Page) -> None:
    """Sometimes the thing you care about is not visible in the DOM."""
    page.goto("/")
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("Password123")
    page.get_by_role("button", name="Log in").click()

    with page.expect_response("**/api/users") as response_info:
        page.get_by_role("button", name="Load users").click()

    response = response_info.value
    assert response.status == 200
    assert response.json()["count"] == 5


def test_wait_for_function_for_client_side_state(page: Page) -> None:
    """Escape hatch: poll arbitrary JS until it is truthy.

    Legitimate when the state you need lives in JS, not the DOM (a global flag,
    a chart library finishing its render). Still not a sleep -- it polls and
    exits as soon as the condition holds.
    """
    page.goto("/flaky?delay=800")
    page.wait_for_function("() => !document.getElementById('late-content').hidden")
    expect(page.get_by_test_id("late-banner")).to_be_visible()


@pytest.mark.slow
def test_why_sleep_is_wrong(page: Page) -> None:
    """Demonstration, not a pattern to copy.

    Note what a sleep costs even when it 'works': this test is always 3s slow,
    even though the content is ready at 500ms. Multiply by 300 tests.
    """
    page.goto("/flaky?delay=500")
    start = time.time()
    time.sleep(3)  # noqa: E501 - deliberately bad, see the docstring
    slept = time.time() - start

    assert slept >= 3
    expect(page.get_by_test_id("late-banner")).to_be_visible()

    # The correct version of this whole test is one line:
    #   expect(page.get_by_test_id("late-banner")).to_be_visible()
    # ...and it finishes in ~0.5s.


# YOUR TURN (exercise 5):
# Point a test at /flaky?delay=12000 and make it pass. What is the minimum
# change? What does the failure message look like if you do nothing?
