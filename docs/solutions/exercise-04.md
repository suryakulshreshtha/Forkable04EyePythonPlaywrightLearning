# Exercise 4 — combine both filters

```python
def test_combined_filters(dashboard_page) -> None:
    dashboard_page.load_users()
    expect(dashboard_page.rows).to_have_count(5)

    dashboard_page.filter_by_role("admin").filter_by_name("grace")

    expect(dashboard_page.rows).to_have_count(1)
    expect(dashboard_page.row_for("Grace Hopper")).to_be_visible()
```

**Points to notice**

- The page-object methods return `self`, so they chain. That is a deliberate design choice in
  `DashboardPage`, not a Playwright feature.
- The filter is case-insensitive in the app, so `"grace"` matches `Grace Hopper`. Asserting that
  is worthwhile — case sensitivity in search is a common regression.
- Also worth adding: filter to a combination with **no** results and assert the empty-state
  message. Empty states are under-tested almost everywhere.
