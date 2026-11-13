"""Turn posted form strings into values the database can store."""

from __future__ import annotations

from datetime import date, datetime

from storage import StorageError, save_image

MAX_TITLE = 200
MAX_SHORT = 300
MAX_TEXT = 5000


def photo_form(raw: dict) -> tuple[dict | None, dict[str, str]]:
    image_path, image_error = required_image(raw.get("image_path"))
    caption, caption_error = optional_text(raw.get("caption"), "Caption", MAX_SHORT)
    taken_on, taken_error = parse_date(raw.get("taken_on"), "Date", required=False)
    errors = _errors(image_path=image_error, caption=caption_error, taken_on=taken_error)
    if errors:
        return None, errors
    return {"image_path": image_path, "caption": caption, "taken_on": taken_on}, {}


def trip_form(raw: dict) -> tuple[dict | None, dict[str, str]]:
    title, title_error = required_text(raw.get("title"), "Title", MAX_TITLE)
    location, location_error = optional_text(raw.get("location"), "Location", MAX_TITLE)
    start_date, start_error = parse_date(raw.get("start_date"), "Start date", required=False)
    end_date, end_error = parse_date(raw.get("end_date"), "End date", required=False)
    description, description_error = optional_text(raw.get("description"), "Description", MAX_TEXT)
    cover_photo, cover_error = optional_image(raw.get("cover_photo"))
    end_error = end_error or _order_error(start_date, end_date, start_error, end_error)
    errors = _errors(
        title=title_error,
        location=location_error,
        start_date=start_error,
        end_date=end_error,
        description=description_error,
        cover_photo=cover_error,
    )
    if errors:
        return None, errors
    return {
        "title": title,
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "description": description,
        "cover_photo": cover_photo,
    }, {}


def date_form(raw: dict) -> tuple[dict | None, dict[str, str]]:
    title, title_error = required_text(raw.get("title"), "Title", MAX_TITLE)
    place, place_error = optional_text(raw.get("place"), "Place", MAX_TITLE)
    happened_on, date_error = parse_date(raw.get("happened_on"), "Date", required=False)
    description, description_error = optional_text(raw.get("description"), "Description", MAX_TEXT)
    rating, rating_error = parse_rating(raw.get("rating"))
    photo, photo_error = optional_image(raw.get("photo"))
    errors = _errors(
        title=title_error,
        place=place_error,
        happened_on=date_error,
        description=description_error,
        rating=rating_error,
        photo=photo_error,
    )
    if errors:
        return None, errors
    return {
        "title": title,
        "place": place,
        "happened_on": happened_on,
        "description": description,
        "rating": rating,
        "photo": photo,
    }, {}


def note_form(raw: dict) -> tuple[dict | None, dict[str, str]]:
    body, body_error = required_text(raw.get("body"), "Note", MAX_TEXT)
    written_on, date_error = parse_date(raw.get("written_on"), "Date", required=False)
    errors = _errors(body=body_error, written_on=date_error)
    if errors:
        return None, errors
    return {"body": body, "written_on": written_on}, {}


def achievement_form(raw: dict) -> tuple[dict | None, dict[str, str]]:
    title, title_error = required_text(raw.get("title"), "Title", MAX_TITLE)
    achieved_on, date_error = parse_date(raw.get("achieved_on"), "Date", required=False)
    description, description_error = optional_text(raw.get("description"), "Description", MAX_TEXT)
    photo, photo_error = optional_image(raw.get("photo"))
    kind, kind_error = parse_kind(raw.get("kind"))
    errors = _errors(
        title=title_error,
        achieved_on=date_error,
        description=description_error,
        photo=photo_error,
        kind=kind_error,
    )
    if errors:
        return None, errors
    return {
        "title": title,
        "achieved_on": achieved_on,
        "description": description,
        "photo": photo,
        "kind": kind,
    }, {}


def chapter_form(raw: dict) -> tuple[dict | None, dict[str, str]]:
    number, number_error = parse_number(raw.get("number"))
    title, title_error = required_text(raw.get("title"), "Title", MAX_TITLE)
    subtitle, subtitle_error = optional_text(raw.get("subtitle"), "Subtitle", MAX_SHORT)
    start_date, start_error = parse_date(raw.get("start_date"), "Start date", required=True)
    end_date, end_error = parse_date(raw.get("end_date"), "End date", required=False)
    cover_image, cover_error = optional_image(raw.get("cover_image"))
    intro_text, intro_error = optional_text(raw.get("intro_text"), "Intro", MAX_TEXT)
    end_error = end_error or _order_error(start_date, end_date, start_error, end_error)
    errors = _errors(
        number=number_error,
        title=title_error,
        subtitle=subtitle_error,
        start_date=start_error,
        end_date=end_error,
        cover_image=cover_error,
        intro_text=intro_error,
    )
    if errors:
        return None, errors
    return {
        "number": number,
        "title": title,
        "subtitle": subtitle,
        "start_date": start_date,
        "end_date": end_date,
        "cover_image": cover_image,
        "intro_text": intro_text,
    }, {}


def required_text(value: object, label: str, limit: int) -> tuple[str | None, str | None]:
    text = _clean(value)
    if not text:
        return None, f"{label} is required."
    if len(text) > limit:
        return None, f"{label} must be {limit} characters or fewer."
    return text, None


def optional_text(value: object, label: str, limit: int) -> tuple[str | None, str | None]:
    text = _clean(value)
    if not text:
        return None, None
    if len(text) > limit:
        return None, f"{label} must be {limit} characters or fewer."
    return text, None


def parse_date(value: object, label: str, *, required: bool) -> tuple[date | None, str | None]:
    text = _clean(value)
    if not text:
        if required:
            return None, f"{label} is required."
        return None, None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"{label} must be a real date."


def parse_number(value: object) -> tuple[int | None, str | None]:
    text = _clean(value)
    if not text:
        return None, "A chapter number is required."
    if not text.isdigit():
        return None, "Use a whole number, like 3."
    number = int(text)
    if number < 0 or number > 999:
        return None, "Chapter numbers run from 0 to 999."
    return number, None


def parse_rating(value: object) -> tuple[int | None, str | None]:
    text = _clean(value)
    if not text:
        return None, None
    if text not in {"1", "2", "3", "4", "5"}:
        return None, "Rating must be from 1 to 5."
    return int(text), None


def parse_kind(value: object) -> tuple[str | None, str | None]:
    text = _clean(value) or "shared"
    if text not in {"personal", "shared"}:
        return None, "Choose personal or shared."
    return text, None


def required_image(value: object) -> tuple[str | None, str | None]:
    if not _clean(value):
        return None, "Add an image path or URL."
    return optional_image(value)


def optional_image(value: object) -> tuple[str | None, str | None]:
    text = _clean(value)
    if not text:
        return None, None
    try:
        return save_image(text), None
    except StorageError as exc:
        return None, str(exc)


def _order_error(
    start: date | None,
    end: date | None,
    start_error: str | None,
    end_error: str | None,
) -> str | None:
    if start_error or end_error or start is None or end is None:
        return None
    if end < start:
        return "The end should be on or after the start."
    return None


def _errors(**items: str | None) -> dict[str, str]:
    return {key: message for key, message in items.items() if message}


def _clean(value: object) -> str:
    return str(value or "").strip()
