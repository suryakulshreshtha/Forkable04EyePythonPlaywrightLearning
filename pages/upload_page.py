"""Upload page object -- file input handling."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class UploadPage(BasePage):
    path = "/upload"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.file_input: Locator = page.get_by_label("Document")
        self.submit: Locator = page.get_by_role("button", name="Upload")
        self.result: Locator = page.get_by_test_id("upload-result")
        self.uploaded_name: Locator = page.get_by_test_id("uploaded-name")
        self.preview: Locator = page.get_by_test_id("upload-preview")

    def upload_path(self, path: Path | str) -> UploadPage:
        self.file_input.set_input_files(str(path))
        self.submit.click()
        return self

    def upload_in_memory(self, name: str, content: str, mime: str = "text/plain") -> UploadPage:
        """No temp file on disk -- ideal for CI, nothing to clean up."""
        self.file_input.set_input_files(
            files=[{"name": name, "mimeType": mime, "buffer": content.encode()}]
        )
        self.submit.click()
        return self
