# Exercise 3 — assert the admin names in one call

```python
def test_admin_filter_names(authenticated_page: Page) -> None:
    page = authenticated_page
    page.goto("/dashboard")
    page.get_by_role("button", name="Load users").click()
    expect(page.get_by_test_id("user-row")).to_have_count(5)   # wait for load first

    page.get_by_label("Role").select_option("admin")

    names = page.get_by_test_id("user-row").locator("td:nth-child(2)")
    expect(names).to_have_text(["Ada Lovelace", "Grace Hopper"])
```

**Points to notice**

- Passing a **list** to `to_have_text` asserts count *and* order in one polling assertion. That
  makes it a sorting regression test for free.
- The `to_have_count(5)` before filtering is not padding: without it you can filter an empty table
  and then assert on an empty result, which passes for the wrong reason.
