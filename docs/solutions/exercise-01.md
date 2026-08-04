# Exercise 1 — log in as admin

```python
def test_admin_can_log_in(page: Page) -> None:
    page.goto("/")
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("Admin123")
    page.get_by_role("button", name="Log in").click()

    expect(page).to_have_url(re.compile(r"/dashboard$"))
    expect(page.get_by_test_id("current-user")).to_have_text("Signed in as admin")
```

**Points to notice**

- `to_have_url` with a plain string compares **exactly**. Use a regex for "ends with".
- `get_by_test_id("current-user")` rather than `get_by_text("admin")` — the latter would also match
  the "admin" role cells in the table once users are loaded, and strict mode would reject it.
- Better still, this belongs in `tests/02_pom/` using `LoginPage`, and the credentials belong in
  `test-data/users.json` — which is exactly what `test_all_valid_users_can_log_in` does.
