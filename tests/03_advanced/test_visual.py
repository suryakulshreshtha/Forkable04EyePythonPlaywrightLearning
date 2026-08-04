"""LESSON 11 -- Visual regression testing.

FIRST RUN generates baselines and reports a failure -- that is by design; you
are expected to eyeball the generated PNGs and commit them.

    pytest tests/03_advanced/test_visual.py --update-snapshots

Honest assessment before you sprinkle these everywhere
------------------------------------------------------
Pixel comparison is the flakiest thing in this repo. Fonts render differently
on macOS vs the Ubuntu CI runner, GPU antialiasing varies, and any dynamic
content (dates, IDs, avatars) breaks it. Mitigations used below: mask dynamic
regions, set a threshold, freeze animations (reduced_motion in conftest), and
run visual tests on ONE browser/OS only -- the one CI uses.

These tests are marked `visual` and are excluded from the PR gate. They are also
excluded from the nightly's main run, and live in their own non-blocking job --
because a fresh fork has no committed baselines, and Playwright's documented
behaviour on a missing baseline is to generate it and FAIL that run.

Run them locally on purpose with:
    VISUAL=1 pytest -m visual --update-snapshots
...then look at every generated PNG before you commit it. A baseline you did
not inspect is a bug you have just frozen into the suite.
"""

import os

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.visual
@pytest.mark.skipif(
    "CI" not in os.environ and "VISUAL" not in os.environ,
    reason="Baselines are generated on the CI OS (ubuntu-latest); local fonts differ. "
    "Set VISUAL=1 to run anyway.",
)
def test_login_page_appearance(page: Page) -> None:
    page.goto("/")
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()

    # max_diff_pixel_ratio absorbs sub-pixel antialiasing without hiding real
    # layout breakage.
    expect(page).to_have_screenshot("login-page.png", max_diff_pixel_ratio=0.02)


@pytest.mark.visual
@pytest.mark.skipif(
    "CI" not in os.environ and "VISUAL" not in os.environ,
    reason="Baselines are generated on the CI OS (ubuntu-latest); local fonts differ. "
    "Set VISUAL=1 to run anyway.",
)
def test_dashboard_appearance_with_masking(authenticated_page: Page) -> None:
    authenticated_page.goto("/dashboard")
    authenticated_page.get_by_role("button", name="Load users").click()
    expect(authenticated_page.get_by_test_id("user-row")).to_have_count(5)

    # Mask the region whose content is not stable across runs.
    expect(authenticated_page).to_have_screenshot(
        "dashboard-loaded.png",
        mask=[authenticated_page.get_by_test_id("current-user")],
        max_diff_pixel_ratio=0.02,
        full_page=True,
    )


@pytest.mark.visual
def test_component_level_screenshot_is_more_stable(page: Page) -> None:
    """Prefer element screenshots over full-page ones: a footer change should
    not fail your login-form test."""
    page.goto("/")
    form = page.locator("form")
    assert form.is_visible()
    # Element screenshots are compared the same way:
    #   expect(form).to_have_screenshot("login-form.png")
    # Left commented so a fresh clone stays green without baselines.
