"""Add, edit, and delete the five sections inside a chapter."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from db import queries
from routes.identity import flash, posted_form, redirect, require_writer, set_form_error
from routes import validate

router = APIRouter()


@router.post("/chapter/{number}/photos")
async def add_photo(request: Request, number: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.photo_form(raw)
    if errors:
        return _invalid(request, number, "photo-add", errors, raw)
    queries.create_photo(chapter_id=chapter["id"], created_by=user["id"], **cleaned)
    return _ok(request, number, "gallery", "Photo added.")


@router.post("/chapter/{number}/photos/{photo_id}/edit")
async def edit_photo(request: Request, number: int, photo_id: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.photo_form(raw)
    if errors:
        return _invalid(request, number, f"photo-edit-{photo_id}", errors, raw)
    if not queries.update_photo(photo_id=photo_id, chapter_id=chapter["id"], **cleaned):
        return _missing(request, number, "gallery", "That photo is no longer there.")
    return _ok(request, number, "gallery", "Photo updated.")


@router.post("/chapter/{number}/photos/{photo_id}/delete")
async def delete_photo(request: Request, number: int, photo_id: int, user: dict = Depends(require_writer)):
    await posted_form(request)
    chapter = _chapter_or_404(number)
    queries.delete_photo(photo_id=photo_id, chapter_id=chapter["id"])
    return _ok(request, number, "gallery", "Photo removed.")


@router.post("/chapter/{number}/trips")
async def add_trip(request: Request, number: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.trip_form(raw)
    if errors:
        return _invalid(request, number, "trip-add", errors, raw)
    queries.create_trip(chapter_id=chapter["id"], created_by=user["id"], **cleaned)
    return _ok(request, number, "trips", "Trip added.")


@router.post("/chapter/{number}/trips/{trip_id}/edit")
async def edit_trip(request: Request, number: int, trip_id: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.trip_form(raw)
    if errors:
        return _invalid(request, number, f"trip-edit-{trip_id}", errors, raw)
    if not queries.update_trip(trip_id=trip_id, chapter_id=chapter["id"], **cleaned):
        return _missing(request, number, "trips", "That trip is no longer there.")
    return _ok(request, number, "trips", "Trip updated.")


@router.post("/chapter/{number}/trips/{trip_id}/delete")
async def delete_trip(request: Request, number: int, trip_id: int, user: dict = Depends(require_writer)):
    await posted_form(request)
    chapter = _chapter_or_404(number)
    queries.delete_trip(trip_id=trip_id, chapter_id=chapter["id"])
    return _ok(request, number, "trips", "Trip removed.")


@router.post("/chapter/{number}/dates")
async def add_date(request: Request, number: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.date_form(raw)
    if errors:
        return _invalid(request, number, "date-add", errors, raw)
    queries.create_date(chapter_id=chapter["id"], created_by=user["id"], **cleaned)
    return _ok(request, number, "dates", "Date added.")


@router.post("/chapter/{number}/dates/{date_id}/edit")
async def edit_date(request: Request, number: int, date_id: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.date_form(raw)
    if errors:
        return _invalid(request, number, f"date-edit-{date_id}", errors, raw)
    if not queries.update_date(date_id=date_id, chapter_id=chapter["id"], **cleaned):
        return _missing(request, number, "dates", "That date is no longer there.")
    return _ok(request, number, "dates", "Date updated.")


@router.post("/chapter/{number}/dates/{date_id}/delete")
async def delete_date(request: Request, number: int, date_id: int, user: dict = Depends(require_writer)):
    await posted_form(request)
    chapter = _chapter_or_404(number)
    queries.delete_date(date_id=date_id, chapter_id=chapter["id"])
    return _ok(request, number, "dates", "Date removed.")


@router.post("/chapter/{number}/notes")
async def add_note(request: Request, number: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.note_form(raw)
    if errors:
        return _invalid(request, number, "note-add", errors, raw)
    queries.create_note(chapter_id=chapter["id"], created_by=user["id"], **cleaned)
    return _ok(request, number, "notes", "Note added.")


@router.post("/chapter/{number}/notes/{note_id}/edit")
async def edit_note(request: Request, number: int, note_id: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.note_form(raw)
    if errors:
        return _invalid(request, number, f"note-edit-{note_id}", errors, raw)
    return _note_result(
        request,
        number,
        queries.update_note(note_id=note_id, chapter_id=chapter["id"], user_id=user["id"], **cleaned),
        "Note updated.",
    )


@router.post("/chapter/{number}/notes/{note_id}/delete")
async def delete_note(request: Request, number: int, note_id: int, user: dict = Depends(require_writer)):
    await posted_form(request)
    chapter = _chapter_or_404(number)
    result = queries.delete_note(note_id=note_id, chapter_id=chapter["id"], user_id=user["id"])
    return _note_result(request, number, result, "Note removed.")


@router.post("/chapter/{number}/achievements")
async def add_achievement(request: Request, number: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.achievement_form(raw)
    if errors:
        return _invalid(request, number, "achievement-add", errors, raw)
    queries.create_achievement(chapter_id=chapter["id"], created_by=user["id"], **cleaned)
    return _ok(request, number, "achievements", "Achievement added.")


@router.post("/chapter/{number}/achievements/{achievement_id}/edit")
async def edit_achievement(
    request: Request,
    number: int,
    achievement_id: int,
    user: dict = Depends(require_writer),
):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.achievement_form(raw)
    if errors:
        return _invalid(request, number, f"achievement-edit-{achievement_id}", errors, raw)
    saved = queries.update_achievement(
        achievement_id=achievement_id,
        chapter_id=chapter["id"],
        **cleaned,
    )
    if not saved:
        return _missing(request, number, "achievements", "That achievement is no longer there.")
    return _ok(request, number, "achievements", "Achievement updated.")


@router.post("/chapter/{number}/achievements/{achievement_id}/delete")
async def delete_achievement(
    request: Request,
    number: int,
    achievement_id: int,
    user: dict = Depends(require_writer),
):
    await posted_form(request)
    chapter = _chapter_or_404(number)
    queries.delete_achievement(achievement_id=achievement_id, chapter_id=chapter["id"])
    return _ok(request, number, "achievements", "Achievement removed.")


def _chapter_or_404(number: int) -> dict:
    chapter = queries.get_chapter_by_number(number)
    if chapter is None:
        raise HTTPException(status_code=404)
    return chapter


def _invalid(request: Request, number: int, form_name: str, errors: dict, raw: dict):
    set_form_error(request, form_name, errors, raw)
    return redirect(f"/chapter/{number}#{form_name}")


def _ok(request: Request, number: int, anchor: str, message: str):
    flash(request, message)
    return redirect(f"/chapter/{number}#{anchor}")


def _missing(request: Request, number: int, anchor: str, message: str):
    flash(request, message, "error")
    return redirect(f"/chapter/{number}#{anchor}")


def _note_result(request: Request, number: int, result: str, success: str):
    if result == "ok":
        return _ok(request, number, "notes", success)
    if result == "forbidden":
        return _missing(request, number, "notes", "You can only change your own notes.")
    return _missing(request, number, "notes", "That note is no longer there.")
