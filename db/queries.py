"""Parameterized SQL for users, chapters, and the five section tables."""

from __future__ import annotations

from datetime import date

from db.connection import connect

def list_users() -> list[dict]:
    with connect() as conn:
        return conn.execute(
            """
            SELECT id, display_name, slug, accent_color
            FROM users
            ORDER BY id
            """
        ).fetchall()


def get_user_by_slug(slug: str) -> dict | None:
    with connect() as conn:
        return conn.execute(
            """
            SELECT id, display_name, slug, accent_color
            FROM users
            WHERE slug = %s
            """,
            (slug.strip().lower(),),
        ).fetchone()


def get_user_by_id(user_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(
            """
            SELECT id, display_name, slug, accent_color
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        ).fetchone()


def list_chapters() -> list[dict]:
    with connect() as conn:
        return conn.execute(
            """
            SELECT
                id, number, title, subtitle, start_date, end_date,
                cover_image, intro_text, created_by, created_at
            FROM chapters
            ORDER BY number
            """
        ).fetchall()


def get_chapter_by_number(number: int) -> dict | None:
    with connect() as conn:
        return conn.execute(
            """
            SELECT
                id, number, title, subtitle, start_date, end_date,
                cover_image, intro_text, created_by, created_at
            FROM chapters
            WHERE number = %s
            """,
            (number,),
        ).fetchone()


def get_chapter_bundle(number: int) -> dict | None:
    """Load one chapter and every section, in one short-lived connection."""
    with connect() as conn:
        chapter = conn.execute(
            """
            SELECT
                id, number, title, subtitle, start_date, end_date,
                cover_image, intro_text, created_by, created_at
            FROM chapters
            WHERE number = %s
            """,
            (number,),
        ).fetchone()
        if chapter is None:
            return None
        chapter_id = chapter["id"]
        return {
            "chapter": chapter,
            "photos": _rows(conn, _PHOTOS, chapter_id),
            "trips": _rows(conn, _TRIPS, chapter_id),
            "dates": _rows(conn, _DATES, chapter_id),
            "notes": _rows(conn, _NOTES, chapter_id),
            "achievements": _rows(conn, _ACHIEVEMENTS, chapter_id),
        }


def create_chapter(
    *,
    number: int,
    title: str,
    subtitle: str | None,
    start_date: date,
    end_date: date | None,
    cover_image: str | None,
    intro_text: str | None,
    created_by: int,
) -> int:
    with connect() as conn:
        row = conn.execute(
            """
            INSERT INTO chapters (
                number, title, subtitle, start_date, end_date,
                cover_image, intro_text, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (number, title, subtitle, start_date, end_date, cover_image, intro_text, created_by),
        ).fetchone()
        return row["id"]


def update_chapter(
    *,
    chapter_id: int,
    number: int,
    title: str,
    subtitle: str | None,
    start_date: date,
    end_date: date | None,
    cover_image: str | None,
    intro_text: str | None,
) -> bool:
    with connect() as conn:
        row = conn.execute(
            """
            UPDATE chapters
            SET number = %s,
                title = %s,
                subtitle = %s,
                start_date = %s,
                end_date = %s,
                cover_image = %s,
                intro_text = %s
            WHERE id = %s
            RETURNING id
            """,
            (number, title, subtitle, start_date, end_date, cover_image, intro_text, chapter_id),
        ).fetchone()
        return row is not None


def delete_chapter(chapter_id: int) -> bool:
    with connect() as conn:
        row = conn.execute(
            "DELETE FROM chapters WHERE id = %s RETURNING id",
            (chapter_id,),
        ).fetchone()
        return row is not None


def create_photo(*, chapter_id: int, created_by: int, image_path: str, caption: str | None, taken_on: date | None) -> int:
    return _insert(
        """
        INSERT INTO photos (chapter_id, created_by, image_path, caption, taken_on)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (chapter_id, created_by, image_path, caption, taken_on),
    )


def update_photo(*, photo_id: int, chapter_id: int, image_path: str, caption: str | None, taken_on: date | None) -> bool:
    return _update(
        """
        UPDATE photos
        SET image_path = %s, caption = %s, taken_on = %s
        WHERE id = %s AND chapter_id = %s
        RETURNING id
        """,
        (image_path, caption, taken_on, photo_id, chapter_id),
    )


def delete_photo(*, photo_id: int, chapter_id: int) -> bool:
    return _delete("DELETE FROM photos WHERE id = %s AND chapter_id = %s RETURNING id", photo_id, chapter_id)


def create_trip(
    *,
    chapter_id: int,
    created_by: int,
    title: str,
    location: str | None,
    start_date: date | None,
    end_date: date | None,
    description: str | None,
    cover_photo: str | None,
) -> int:
    return _insert(
        """
        INSERT INTO trips (
            chapter_id, created_by, title, location, start_date, end_date, description, cover_photo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (chapter_id, created_by, title, location, start_date, end_date, description, cover_photo),
    )


def update_trip(
    *,
    trip_id: int,
    chapter_id: int,
    title: str,
    location: str | None,
    start_date: date | None,
    end_date: date | None,
    description: str | None,
    cover_photo: str | None,
) -> bool:
    return _update(
        """
        UPDATE trips
        SET title = %s, location = %s, start_date = %s, end_date = %s,
            description = %s, cover_photo = %s
        WHERE id = %s AND chapter_id = %s
        RETURNING id
        """,
        (title, location, start_date, end_date, description, cover_photo, trip_id, chapter_id),
    )


def delete_trip(*, trip_id: int, chapter_id: int) -> bool:
    return _delete("DELETE FROM trips WHERE id = %s AND chapter_id = %s RETURNING id", trip_id, chapter_id)


def create_date(
    *,
    chapter_id: int,
    created_by: int,
    title: str,
    place: str | None,
    happened_on: date | None,
    description: str | None,
    rating: int | None,
    photo: str | None,
) -> int:
    return _insert(
        """
        INSERT INTO dates (
            chapter_id, created_by, title, place, happened_on, description, rating, photo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (chapter_id, created_by, title, place, happened_on, description, rating, photo),
    )


def update_date(
    *,
    date_id: int,
    chapter_id: int,
    title: str,
    place: str | None,
    happened_on: date | None,
    description: str | None,
    rating: int | None,
    photo: str | None,
) -> bool:
    return _update(
        """
        UPDATE dates
        SET title = %s, place = %s, happened_on = %s, description = %s, rating = %s, photo = %s
        WHERE id = %s AND chapter_id = %s
        RETURNING id
        """,
        (title, place, happened_on, description, rating, photo, date_id, chapter_id),
    )


def delete_date(*, date_id: int, chapter_id: int) -> bool:
    return _delete("DELETE FROM dates WHERE id = %s AND chapter_id = %s RETURNING id", date_id, chapter_id)


def create_note(*, chapter_id: int, created_by: int, body: str, written_on: date | None) -> int:
    return _insert(
        """
        INSERT INTO notes (chapter_id, created_by, body, written_on)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (chapter_id, created_by, body, written_on),
    )


def update_note(*, note_id: int, chapter_id: int, user_id: int, body: str, written_on: date | None) -> str:
    """Return ok, missing, or forbidden. Only the author may change a note."""
    with connect() as conn:
        access = _note_access(conn, note_id, chapter_id, user_id)
        if access != "ok":
            return access
        conn.execute(
            """
            UPDATE notes
            SET body = %s, written_on = %s
            WHERE id = %s AND chapter_id = %s AND created_by = %s
            """,
            (body, written_on, note_id, chapter_id, user_id),
        )
        return "ok"


def delete_note(*, note_id: int, chapter_id: int, user_id: int) -> str:
    with connect() as conn:
        access = _note_access(conn, note_id, chapter_id, user_id)
        if access != "ok":
            return access
        conn.execute(
            """
            DELETE FROM notes
            WHERE id = %s AND chapter_id = %s AND created_by = %s
            """,
            (note_id, chapter_id, user_id),
        )
        return "ok"


def create_achievement(
    *,
    chapter_id: int,
    created_by: int,
    title: str,
    achieved_on: date | None,
    description: str | None,
    photo: str | None,
    kind: str,
) -> int:
    return _insert(
        """
        INSERT INTO achievements (
            chapter_id, created_by, title, achieved_on, description, photo, kind
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (chapter_id, created_by, title, achieved_on, description, photo, kind),
    )


def update_achievement(
    *,
    achievement_id: int,
    chapter_id: int,
    title: str,
    achieved_on: date | None,
    description: str | None,
    photo: str | None,
    kind: str,
) -> bool:
    return _update(
        """
        UPDATE achievements
        SET title = %s, achieved_on = %s, description = %s, photo = %s, kind = %s
        WHERE id = %s AND chapter_id = %s
        RETURNING id
        """,
        (title, achieved_on, description, photo, kind, achievement_id, chapter_id),
    )


def delete_achievement(*, achievement_id: int, chapter_id: int) -> bool:
    return _delete(
        "DELETE FROM achievements WHERE id = %s AND chapter_id = %s RETURNING id",
        achievement_id,
        chapter_id,
    )


def _rows(conn, sql: str, chapter_id: int) -> list[dict]:
    return conn.execute(sql, (chapter_id,)).fetchall()


def _insert(sql: str, params: tuple) -> int:
    with connect() as conn:
        row = conn.execute(sql, params).fetchone()
        return row["id"]


def _update(sql: str, params: tuple) -> bool:
    with connect() as conn:
        return conn.execute(sql, params).fetchone() is not None


def _delete(sql: str, item_id: int, chapter_id: int) -> bool:
    with connect() as conn:
        return conn.execute(sql, (item_id, chapter_id)).fetchone() is not None


def _note_access(conn, note_id: int, chapter_id: int, user_id: int) -> str:
    row = conn.execute(
        """
        SELECT created_by
        FROM notes
        WHERE id = %s AND chapter_id = %s
        """,
        (note_id, chapter_id),
    ).fetchone()
    if row is None:
        return "missing"
    if row["created_by"] != user_id:
        return "forbidden"
    return "ok"


_PHOTOS = """
    SELECT
        t.id, t.chapter_id, t.created_by, t.created_at,
        t.image_path, t.caption, t.taken_on,
        u.display_name AS author_name
    FROM photos t
    JOIN users u ON u.id = t.created_by
    WHERE t.chapter_id = %s
    ORDER BY t.taken_on NULLS LAST, t.id
"""

_TRIPS = """
    SELECT
        t.id, t.chapter_id, t.created_by, t.created_at,
        t.title, t.location, t.start_date, t.end_date, t.description, t.cover_photo,
        u.display_name AS author_name
    FROM trips t
    JOIN users u ON u.id = t.created_by
    WHERE t.chapter_id = %s
    ORDER BY t.start_date NULLS LAST, t.id
"""

_DATES = """
    SELECT
        t.id, t.chapter_id, t.created_by, t.created_at,
        t.title, t.place, t.happened_on, t.description, t.rating, t.photo,
        u.display_name AS author_name
    FROM dates t
    JOIN users u ON u.id = t.created_by
    WHERE t.chapter_id = %s
    ORDER BY t.happened_on NULLS LAST, t.id
"""

_NOTES = """
    SELECT
        t.id, t.chapter_id, t.created_by, t.created_at,
        t.body, t.written_on,
        u.display_name AS author_name
    FROM notes t
    JOIN users u ON u.id = t.created_by
    WHERE t.chapter_id = %s
    ORDER BY t.written_on NULLS LAST, t.id
"""

_ACHIEVEMENTS = """
    SELECT
        t.id, t.chapter_id, t.created_by, t.created_at,
        t.title, t.achieved_on, t.description, t.photo, t.kind,
        u.display_name AS author_name
    FROM achievements t
    JOIN users u ON u.id = t.created_by
    WHERE t.chapter_id = %s
    ORDER BY t.achieved_on NULLS LAST, t.id
"""
