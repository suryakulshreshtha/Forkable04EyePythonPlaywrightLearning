"""LESSON 7 -- Page objects + component objects + data-driven filtering."""

import re

import pytest
from playwright.sync_api import expect


@pytest.mark.smoke
def test_dashboard_loads_users(dashboard_page) -> None:
    dashboard_page.load_users()

    expect(dashboard_page.table).to_be_visible()
    expect(dashboard_page.rows).to_have_count(5)
    expect(dashboard_page.table_status).to_have_text("Showing 5 of 5 users")


@pytest.mark.parametrize(
    ("role", "expected"),
    [("admin", 2), ("tester", 1), ("dev", 2), ("", 5)],
    ids=["admins", "testers", "devs", "all-roles"],
)
def test_role_filter(dashboard_page, role: str, expected: int) -> None:
    dashboard_page.load_users()
    expect(dashboard_page.rows).to_have_count(5)  # wait for load before filtering

    dashboard_page.filter_by_role(role)
    expect(dashboard_page.rows).to_have_count(expected)


@pytest.mark.parametrize(
    ("term", "expected_names"),
    [
        ("ada", ["Ada Lovelace"]),
        # "ra" appears in Dijkstra and Barbara only. Note the expected ORDER --
        # the filter preserves the source order, so this also guards sorting.
        ("ra", ["Grace Hopper", "Edsger Dijkstra", "Barbara Liskov"]),
        ("zzz", []),
    ],
)
def test_name_search(dashboard_page, term: str, expected_names: list[str]) -> None:
    dashboard_page.load_users()
    expect(dashboard_page.rows).to_have_count(5)

    dashboard_page.filter_by_name(term)
    expect(dashboard_page.rows).to_have_count(len(expected_names))
    assert dashboard_page.names() == expected_names


def test_empty_state_message(dashboard_page) -> None:
    dashboard_page.load_users()
    expect(dashboard_page.rows).to_have_count(5)

    dashboard_page.filter_by_name("no-such-person")
    expect(dashboard_page.table_status).to_have_text("No users match your filter.")
    expect(dashboard_page.table).to_be_hidden()


def test_combined_filters(dashboard_page) -> None:
    dashboard_page.load_users()
    expect(dashboard_page.rows).to_have_count(5)

    dashboard_page.filter_by_role("admin").filter_by_name("grace")
    expect(dashboard_page.rows).to_have_count(1)
    expect(dashboard_page.row_for("Grace Hopper")).to_be_visible()


def test_csv_export(dashboard_page) -> None:
    download = dashboard_page.download_csv()

    assert download.suggested_filename == "users-export.csv"
    assert "Ada Lovelace" in download.path().read_text(encoding="utf-8")


def test_navigation_component(dashboard_page) -> None:
    assert dashboard_page.nav.signed_in_as() == "demo"

    dashboard_page.nav.go_to_upload()
    expect(dashboard_page.page).to_have_url(re.compile(r"/upload$"))
