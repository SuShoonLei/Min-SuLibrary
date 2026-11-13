"""Home, one page per chapter, and the form that adds a chapter."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg.errors import UniqueViolation

from db import queries
from routes.identity import flash, posted_form, redirect, require_writer, set_form_error
from routes import validate

router = APIRouter()


@router.get("/")
def home(request: Request):
    from templating import render

    return render(request, "home.html", {"chapters": queries.list_chapters()})


@router.get("/chapter/{number}")
def chapter_page(request: Request, number: int):
    from templating import render

    bundle = queries.get_chapter_bundle(number)
    if bundle is None:
        raise HTTPException(status_code=404)
    return render(request, "chapter.html", bundle)


@router.post("/chapters")
async def add_chapter(request: Request, user: dict = Depends(require_writer)):
    raw = await posted_form(request)
    cleaned, errors = validate.chapter_form(raw)
    if errors:
        set_form_error(request, "chapter-add", errors, raw)
        return redirect("/#chapter-add")
    try:
        _insert_chapter(cleaned, user["id"])
    except UniqueViolation:
        set_form_error(request, "chapter-add", {"number": "That chapter number is already used."}, raw)
        return redirect("/#chapter-add")
    flash(request, f"Chapter {cleaned['number']} is ready.")
    return redirect(f"/chapter/{cleaned['number']}")


@router.post("/chapter/{number}/edit")
async def edit_chapter(request: Request, number: int, user: dict = Depends(require_writer)):
    chapter = _chapter_or_404(number)
    raw = await posted_form(request)
    cleaned, errors = validate.chapter_form(raw)
    if errors:
        set_form_error(request, "chapter-edit", errors, raw)
        return redirect(f"/chapter/{number}#chapter-edit")
    try:
        saved = queries.update_chapter(chapter_id=chapter["id"], **cleaned)
    except UniqueViolation:
        set_form_error(request, "chapter-edit", {"number": "That chapter number is already used."}, raw)
        return redirect(f"/chapter/{number}#chapter-edit")
    if not saved:
        flash(request, "That chapter is no longer there.", "error")
        return redirect("/")
    flash(request, "Chapter updated.")
    return redirect(f"/chapter/{cleaned['number']}")


@router.post("/chapter/{number}/delete")
async def delete_chapter(request: Request, number: int, user: dict = Depends(require_writer)):
    await posted_form(request)
    chapter = _chapter_or_404(number)
    queries.delete_chapter(chapter["id"])
    flash(request, f"Chapter {number} was deleted.")
    return redirect("/")


def _chapter_or_404(number: int) -> dict:
    chapter = queries.get_chapter_by_number(number)
    if chapter is None:
        raise HTTPException(status_code=404)
    return chapter


def _insert_chapter(cleaned: dict, created_by: int) -> None:
    queries.create_chapter(
        number=cleaned["number"],
        title=cleaned["title"],
        subtitle=cleaned["subtitle"],
        start_date=cleaned["start_date"],
        end_date=cleaned["end_date"],
        cover_image=cleaned["cover_image"],
        intro_text=cleaned["intro_text"],
        created_by=created_by,
    )
