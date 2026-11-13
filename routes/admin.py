"""Temporary page that runs db/setup_all.sql on the live database.

It does not use the shared layout, so an empty database can still open it.
"""

from __future__ import annotations

import hmac
import html
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()
SETUP_SQL = Path(__file__).resolve().parents[1] / "db" / "setup_all.sql"
_URL = re.compile(r"postgres(?:ql)?://\S+")


def _page(message: str = "", status_code: int = 200) -> HTMLResponse:
    shown = f"<p>{html.escape(message)}</p>" if message else ""
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Setup</title>
</head>
<body>
  <h1>Setup</h1>
  {shown}
  <form method="post" action="/admin/setup">
    <label for="passcode">Passcode</label>
    <input id="passcode" name="passcode" type="password" autocomplete="off" required>
    <button type="submit">Run setup</button>
  </form>
</body>
</html>
"""
    return HTMLResponse(body, status_code=status_code)


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL_UNPOOLED", "").strip()
    if not url:
        url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    return url


def _redact(text: str) -> str:
    secrets: list[str] = []
    for key in ("DATABASE_URL_UNPOOLED", "DATABASE_URL"):
        raw = os.environ.get(key, "")
        if not raw:
            continue
        secrets.append(raw)
        password = urlsplit(raw).password
        if password:
            secrets.append(password)
            secrets.append(unquote(password))
    for secret in secrets:
        text = text.replace(secret, "[redacted]")
    return _URL.sub("[redacted]", text)


def _passcode_matches(given: str) -> bool:
    expected = os.environ.get("EDIT_PASSCODE", "").strip()
    if not expected:
        return False
    return hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))


@router.get("/admin/setup")
async def setup_page() -> HTMLResponse:
    return _page()


@router.post("/admin/setup")
async def run_setup(request: Request) -> HTMLResponse:
    try:
        form = await request.form()
    except Exception as exc:
        return _page(_redact(f"{type(exc).__name__}: {exc}"), status_code=400)

    given = form.get("passcode")
    if not isinstance(given, str) or not _passcode_matches(given):
        if not os.environ.get("EDIT_PASSCODE", "").strip():
            return _page("EDIT_PASSCODE is not set.", status_code=403)
        return _page("The passcode does not match.", status_code=403)

    try:
        script = SETUP_SQL.read_text(encoding="utf-8")
        with psycopg.connect(_database_url(), autocommit=True) as conn:
            conn.execute(script)
    except Exception as exc:
        return _page(_redact(f"{type(exc).__name__}: {exc}"), status_code=500)
    return _page("Setup complete")
