"""The bundled application under test.

Why ship an app instead of testing a public demo site?
-----------------------------------------------------
1. Hermetic. No network, no rate limits, no "the demo site changed its DOM and
   now 30 people's forks are red".
2. Deterministic. We control the delays, so a test can prove auto-waiting works
   rather than hoping.
3. It lets CI demonstrate a real service-startup + readiness-probe step, which
   is what you will actually do at work.

The public-site tests still exist in tests/05_external/ so you can see the
difference -- they are marked `external` and are non-blocking in CI.

Run it:  python -m app.server     (or: make app)
"""

from __future__ import annotations

import io
import os

from flask import Flask, redirect, render_template, request, send_file, session, url_for

from app.api import api_bp

VALID_USERS = {"demo": "Password123", "admin": "Admin123"}


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("APP_SECRET", "not-a-real-secret-for-tests-only")
    app.register_blueprint(api_bp)

    @app.get("/health")
    def health():
        """Readiness probe used by CI and docker-compose."""
        return {"status": "ok"}, 200

    @app.get("/")
    def index():
        return render_template("index.html", error=None)

    @app.post("/login")
    def login():
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "on"

        if VALID_USERS.get(username) == password:
            session["user"] = username
            session["remember"] = remember
            return redirect(url_for("dashboard"))

        # Deliberately generic message: good security practice AND a nice
        # example of asserting on a stable, user-visible string.
        return render_template("index.html", error="Invalid username or password"), 401

    @app.get("/dashboard")
    def dashboard():
        if "user" not in session:
            return redirect(url_for("index"))
        return render_template("dashboard.html", user=session["user"])

    @app.get("/upload")
    def upload_form():
        if "user" not in session:
            return redirect(url_for("index"))
        return render_template("upload.html", uploaded=None)

    @app.post("/upload")
    def upload_file():
        if "user" not in session:
            return redirect(url_for("index"))
        uploaded = request.files.get("document")
        if not uploaded or not uploaded.filename:
            return render_template("upload.html", uploaded=None, error="Choose a file first"), 400
        content = uploaded.read().decode("utf-8", errors="replace")
        return render_template(
            "upload.html",
            uploaded={"name": uploaded.filename, "size": len(content), "preview": content[:200]},
        )

    @app.get("/download")
    def download():
        """Serves a small file so learners can practise expect_download()."""
        payload = "id,name,role\n1,Ada Lovelace,admin\n2,Alan Turing,tester\n"
        return send_file(
            io.BytesIO(payload.encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="users-export.csv",
        )

    @app.get("/flaky")
    def flaky():
        """Renders content after a client-side delay.

        Lesson: you never need time.sleep(). Playwright's auto-waiting handles
        this, and the delay is query-configurable so the test can be explicit
        about what it is proving.
        """
        delay_ms = int(request.args.get("delay", 1500))
        return render_template("flaky.html", delay_ms=delay_ms)

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_PORT", "5000")),
        debug=False,
    )
