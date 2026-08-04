# Exercise 6 — POM tests for the upload page

`tests/02_pom/test_upload.py`:

```python
import pytest
from playwright.sync_api import expect


@pytest.mark.smoke
def test_upload_from_disk(upload_page, tmp_text_file) -> None:
    upload_page.upload_path(tmp_text_file)

    expect(upload_page.result).to_be_visible()
    expect(upload_page.uploaded_name).to_have_text("sample-upload.txt")
    expect(upload_page.preview).to_contain_text("line two")


def test_upload_from_memory(upload_page) -> None:
    upload_page.upload_in_memory("report.csv", "id,name\n1,Ada\n", mime="text/csv")

    expect(upload_page.uploaded_name).to_have_text("report.csv")
    expect(upload_page.preview).to_contain_text("1,Ada")


def test_submitting_without_a_file_shows_an_error(upload_page) -> None:
    upload_page.submit.click()

    expect(upload_page.alert()).to_be_visible()
    expect(upload_page.alert()).to_have_text("Choose a file first")
    expect(upload_page.result).to_have_count(0)
```

**Points to notice**

- `upload_page` is a fixture (`tests/02_pom/conftest.py`) built on `authenticated_page`, so no test
  here touches the login form.
- `upload_in_memory` needs no file on disk — nothing to create, nothing to clean up, nothing to
  collide under `-n auto`. Prefer it in CI.
- `alert()` comes from `BasePage` — a generic `role="alert"` locator every page can reuse.
- The third test asserts the **negative** too (`result` has count 0). "The error appeared" and
  "the success banner did not" are two different bugs.
