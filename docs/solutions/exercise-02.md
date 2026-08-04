# Exercise 2 — find the role dropdown three ways

```python
def test_role_dropdown_locators(authenticated_page: Page) -> None:
    page = authenticated_page
    page.goto("/dashboard")

    by_label = page.get_by_label("Role")
    by_role = page.get_by_role("combobox", name="Role")
    by_css = page.locator("select#role-filter")

    for locator in (by_label, by_role, by_css):
        expect(locator).to_be_visible()
        expect(locator.locator("option")).to_have_count(4)
```

**Points to notice**

- A `<select>` has the implicit ARIA role **`combobox`**, not `listbox` or `select`.
- The element carries both `aria-label="Role"` and a `<label for="role-filter">`. `aria-label`
  wins for the accessible name; both resolve to the same single element, so strict mode is happy.
- Four options: the three roles plus "All roles".
