"""Who-you-are and the optional edit passcode, kept in signed cookies.

There is no account and no session. Anyone can read the library. Adding or
editing needs a chosen person (Min or Su). If EDIT_PASSCODE is set, writing
also needs that shared passcode.
"""

from __future__ import annotations

import asyncio
import hmac
import os
import re
import secrets
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import PEOPLE
from db import queries

router = APIRouter()

WHO_COOKIE = "ms_who"
EDIT_COOKIE = "ms_edit"
CSRF_COOKIE = "ms_csrf"
FLASH_COOKIE = "ms_flash"
FORM_COOKIE = "ms_form"

YEAR = 60 * 60 * 24 * 365
_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Wrong passcodes are counted in this process only. On Vercel each isolate
# has its own memory, and a cold start forgets the count, so two instances
# do not share a limit. This is a light brake for a two-person site, not a
# lock that holds across the platform.
_PASSCODE_FAILS: dict[str, list[float]] = {}
_PASSCODE_WINDOW = 60 * 10
_PASSCODE_MAX = 5


def passcode_required() -> bool:
    return bool(os.environ.get("EDIT_PASSCODE", "").strip())


def current_user(request: Request) -> dict | None:
    """The person named in the who-cookie, or None if they have not chosen."""
    if getattr(request.state, "user_loaded", False):
        return getattr(request.state, "user", None)

    request.state.user_loaded = True
    request.state.user = None
    raw = request.cookies.get(WHO_COOKIE)
    if not raw:
        return None

    slug = _unsign(raw, max_age=YEAR, salt="who")
    if not isinstance(slug, str):
        request.state.who_clear = True
        return None

    user = queries.get_user_by_slug(slug)
    if user is None:
        request.state.who_clear = True
        return None

    profile = dict(user)
    profile["accent_color"] = _safe_color(profile.get("accent_color"), PEOPLE[0]["accent_color"])
    request.state.user = profile
    return profile


def require_writer(request: Request) -> dict:
    """The chosen person, once any edit passcode has been unlocked.

    Viewing never calls this. A missing choice or a locked passcode sends
    the browser back to the page they were writing on.
    """
    user = current_user(request)
    back = _write_return_path(request)
    if user is None:
        flash(request, "Choose Min or Su before adding or editing.", "error")
        raise HTTPException(status_code=303, headers={"Location": f"{back}?switch=1#who"})
    if passcode_required() and not edit_unlocked(request):
        flash(request, "Enter our passcode to edit.", "error")
        raise HTTPException(status_code=303, headers={"Location": f"{back}#passcode"})
    return user


def edit_unlocked(request: Request) -> bool:
    if not passcode_required():
        return True
    raw = request.cookies.get(EDIT_COOKIE)
    if not raw:
        return False
    if _unsign(raw, max_age=YEAR, salt="edit") == "ok":
        return True
    request.state.edit_clear = True
    return False


def ensure_csrf(request: Request) -> str:
    """Double-submit token: the same value lives in a cookie and in the form."""
    existing = request.cookies.get(CSRF_COOKIE) or ""
    if _csrf_ok(existing):
        return existing
    token = secrets.token_urlsafe(32)
    request.state.csrf_set = token
    return token


def check_csrf(request: Request, token: str) -> None:
    expected = request.cookies.get(CSRF_COOKIE) or getattr(request.state, "csrf_set", "") or ""
    if not expected or not secrets.compare_digest(expected, token or ""):
        raise HTTPException(
            status_code=403,
            detail="This form expired. Refresh the page and try again.",
        )


def flash(request: Request, message: str, category: str = "success") -> None:
    request.state.flash_set = {"message": message, "category": category}


def pop_flash(request: Request) -> dict | None:
    raw = request.cookies.get(FLASH_COOKIE)
    if not raw:
        return None
    request.state.flash_clear = True
    data = _unsign(raw, max_age=120, salt="flash")
    if not isinstance(data, dict):
        return None
    message = data.get("message")
    if not isinstance(message, str) or not message:
        return None
    category = data.get("category")
    if category not in {"success", "error"}:
        category = "success"
    return {"message": message, "category": category}


def set_form_error(request: Request, form_name: str, errors: dict, values: dict) -> None:
    trimmed = {key: ("" if value is None else str(value)[:1500]) for key, value in values.items()}
    request.state.form_set = {"form": form_name, "errors": errors, "values": trimmed}


def pop_form_error(request: Request) -> dict | None:
    raw = request.cookies.get(FORM_COOKIE)
    if not raw:
        return None
    request.state.form_clear = True
    data = _unsign(raw, max_age=120, salt="form")
    if not isinstance(data, dict) or not isinstance(data.get("form"), str):
        return None
    errors = data.get("errors") if isinstance(data.get("errors"), dict) else {}
    values = data.get("values") if isinstance(data.get("values"), dict) else {}
    return {"form": data["form"], "errors": errors, "values": values}


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def safe_next(value: str | None) -> str:
    """Only allow a same-site path after choosing a name or unlocking edits."""
    if not value or not value.startswith("/") or value.startswith("//") or value.startswith("/\\"):
        return "/"
    if "\\" in value or "://" in value or "#" in value or "?" in value:
        return "/"
    return value


def apply_pending_cookies(request: Request, response) -> None:
    """Write the cookies the route asked for. Called once per response."""
    secure = os.environ.get("VERCEL") == "1"
    base = {"secure": secure, "samesite": "lax", "path": "/"}

    if getattr(request.state, "csrf_set", None):
        response.set_cookie(
            CSRF_COOKIE,
            request.state.csrf_set,
            max_age=YEAR,
            httponly=False,
            **base,
        )

    if getattr(request.state, "who_set", None):
        response.set_cookie(
            WHO_COOKIE,
            _sign(request.state.who_set, salt="who"),
            max_age=YEAR,
            httponly=True,
            **base,
        )
    elif getattr(request.state, "who_clear", False):
        response.delete_cookie(WHO_COOKIE, path="/", secure=secure, samesite="lax")

    if getattr(request.state, "edit_set", False):
        response.set_cookie(
            EDIT_COOKIE,
            _sign("ok", salt="edit"),
            max_age=YEAR,
            httponly=True,
            **base,
        )
    elif getattr(request.state, "edit_clear", False):
        response.delete_cookie(EDIT_COOKIE, path="/", secure=secure, samesite="lax")

    if getattr(request.state, "flash_set", None):
        response.set_cookie(
            FLASH_COOKIE,
            _sign(request.state.flash_set, salt="flash"),
            max_age=120,
            httponly=True,
            **base,
        )
    elif getattr(request.state, "flash_clear", False):
        response.delete_cookie(FLASH_COOKIE, path="/", secure=secure, samesite="lax")

    if getattr(request.state, "form_set", None):
        response.set_cookie(
            FORM_COOKIE,
            _sign_form(request.state.form_set),
            max_age=120,
            httponly=True,
            **base,
        )
    elif getattr(request.state, "form_clear", False):
        response.delete_cookie(FORM_COOKIE, path="/", secure=secure, samesite="lax")


async def posted_form(request: Request) -> dict[str, str]:
    """Read a POST form and reject it when the CSRF token does not match."""
    form = await request.form()
    token = form.get("csrf_token")
    check_csrf(request, str(token or ""))
    values: dict[str, str] = {}
    for key, value in form.multi_items():
        if key == "csrf_token":
            continue
        values[key] = value if isinstance(value, str) else ""
    return values


@router.post("/who")
async def choose_who(request: Request):
    raw = await posted_form(request)
    slug = raw.get("slug", "").strip().lower()
    nxt = safe_next(raw.get("next"))
    known = {person["slug"]: person for person in PEOPLE}
    if slug not in known:
        flash(request, "Pick Min or Su.", "error")
        return redirect(f"{nxt}?switch=1#who")

    user = queries.get_user_by_slug(slug)
    if user is None:
        flash(request, "That name isn't in the library yet.", "error")
        return redirect(f"{nxt}?switch=1#who")

    request.state.who_set = slug
    request.state.user_loaded = True
    request.state.user = user
    flash(request, f"Hi, {user['display_name']}.")
    return redirect(nxt)


@router.post("/passcode")
async def unlock_editing(request: Request):
    raw = await posted_form(request)
    nxt = safe_next(raw.get("next"))
    if not passcode_required():
        return redirect(nxt)

    ip = _client_ip(request)
    if _too_many_attempts(ip):
        await asyncio.sleep(0.8)
        flash(request, "Too many tries. Wait a few minutes and try again.", "error")
        return redirect(f"{nxt}#passcode")

    expected = os.environ.get("EDIT_PASSCODE", "").strip()
    given = raw.get("passcode", "")
    if not _same_secret(given, expected):
        _note_failure(ip)
        await asyncio.sleep(0.5)
        flash(request, "That passcode isn't the one.", "error")
        return redirect(f"{nxt}#passcode")

    request.state.edit_set = True
    flash(request, "Editing is unlocked on this browser.")
    return redirect(nxt)


def _write_return_path(request: Request) -> str:
    path = request.url.path
    if path == "/chapters":
        return "/"
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "chapter" and parts[1].isdigit():
        return f"/chapter/{parts[1]}"
    return "/"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _too_many_attempts(ip: str) -> bool:
    now = time.monotonic()
    recent = [stamp for stamp in _PASSCODE_FAILS.get(ip, []) if now - stamp < _PASSCODE_WINDOW]
    _PASSCODE_FAILS[ip] = recent
    return len(recent) >= _PASSCODE_MAX


def _note_failure(ip: str) -> None:
    now = time.monotonic()
    recent = [stamp for stamp in _PASSCODE_FAILS.get(ip, []) if now - stamp < _PASSCODE_WINDOW]
    recent.append(now)
    _PASSCODE_FAILS[ip] = recent
    if len(_PASSCODE_FAILS) > 500:
        oldest = sorted(_PASSCODE_FAILS, key=lambda key: _PASSCODE_FAILS[key][-1])[:100]
        for key in oldest:
            _PASSCODE_FAILS.pop(key, None)


def _same_secret(given: str, expected: str) -> bool:
    try:
        return hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))
    except (TypeError, ValueError):
        return False


def _secret() -> str:
    key = os.environ.get("SECRET_KEY", "").strip()
    if not key:
        raise RuntimeError("SECRET_KEY is not set.")
    return key


def _serializer(salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(_secret(), salt=salt)


def _sign(value, *, salt: str) -> str:
    return _serializer(salt).dumps(value)


def _unsign(token: str, *, max_age: int, salt: str):
    try:
        return _serializer(salt).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def _sign_form(payload: dict) -> str:
    signed = _sign(payload, salt="form")
    if len(signed) <= 3500:
        return signed
    slim = {"form": payload.get("form", ""), "errors": payload.get("errors", {}), "values": {}}
    return _sign(slim, salt="form")


def _csrf_ok(value: str) -> bool:
    return 20 <= len(value) <= 128 and all(char.isalnum() or char in "-_" for char in value)


def _safe_color(value: object, fallback: str) -> str:
    if isinstance(value, str) and _COLOR.match(value):
        return value
    return fallback
