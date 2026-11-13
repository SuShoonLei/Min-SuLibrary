"""Shared Jinja setup for pages and error screens."""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger("minsu")

BASE_DIR = Path(__file__).resolve().parent
# Autoescape is on for .html, so chapter text and notes cannot inject markup.
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def media_url(path: object) -> str:
    """Turn a stored path or URL into something an <img> can load."""
    if path is None:
        return "/assets/placeholder.svg"
    text = str(path).strip()
    if not text:
        return "/assets/placeholder.svg"
    if text.startswith(("http://", "https://", "/")):
        return text
    return "/" + text.lstrip("./")


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def pretty_date(value: object) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        return ""
    return f"{_MONTHS[value.month - 1]} {value.day}, {value.year}"


def date_range(start: object, end: object, open_ended: bool = False) -> str:
    start_text = pretty_date(start)
    end_text = pretty_date(end)
    if start_text and end_text:
        return f"{start_text} — {end_text}"
    if start_text and open_ended:
        return f"{start_text} — present"
    return start_text or end_text


def iso_date(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return ""


def paragraphs(text: object) -> list[str]:
    if text is None:
        return []
    return [line.strip() for line in str(text).splitlines() if line.strip()]


templates.env.filters["media_url"] = media_url
templates.env.filters["pretty_date"] = pretty_date
templates.env.filters["date_range"] = date_range
templates.env.filters["iso_date"] = iso_date
templates.env.filters["paragraphs"] = paragraphs


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    payload = _page_context(request, swallow_errors=status_code >= 400)
    if context:
        payload.update(context)
    payload["request"] = request
    try:
        return templates.TemplateResponse(
            request=request,
            name=name,
            context=payload,
            status_code=status_code,
        )
    except Exception:
        logger.exception("Template %s failed", name)
        if status_code < 400:
            raise
        return HTMLResponse(_PLAIN_ERROR, status_code=status_code)


def _page_context(request: Request, *, swallow_errors: bool) -> dict:
    from config import MET_ON, PEOPLE, SHOW_CRYSTAL_BALL, SITE_DESCRIPTION, SITE_NAME, TOGETHER_SINCE, days_together
    from routes.identity import current_user, edit_unlocked, ensure_csrf, passcode_required, pop_flash, pop_form_error

    context = {
        "site_name": SITE_NAME,
        "site_description": SITE_DESCRIPTION,
        "show_crystal_ball": SHOW_CRYSTAL_BALL,
        "together_since": TOGETHER_SINCE,
        "met_on": MET_ON,
        "days_together": days_together(),
        "user": None,
        "flash": None,
        "form_error": None,
        "csrf_token": "",
        "show_who": False,
        "needs_passcode": False,
        "people": list(PEOPLE),
    }
    steps = (
        ("csrf_token", lambda: ensure_csrf(request)),
        ("flash", lambda: pop_flash(request)),
        ("form_error", lambda: pop_form_error(request)),
        ("user", lambda: current_user(request)),
    )
    for key, load in steps:
        try:
            context[key] = load()
        except Exception:
            if not swallow_errors:
                raise
            logger.exception("Could not prepare %s for the error page", key)
    if not swallow_errors:
        switching = request.query_params.get("switch") == "1"
        context["show_who"] = context["user"] is None or switching
        context["needs_passcode"] = passcode_required() and not edit_unlocked(request)
    return context


_PLAIN_ERROR = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Something went wrong · Min&amp;Su Library</title>
  <style>
    body { margin: 0; font-family: Georgia, serif; background: #f7f4ef; color: #232c4b; }
    main { max-width: 36rem; margin: 4rem auto; padding: 0 1.5rem; }
    a { color: #232c4b; }
  </style>
</head>
<body>
  <main>
    <p>Something went wrong on our side.</p>
    <p><a href="/">Back home</a></p>
  </main>
</body>
</html>
"""
