#!/usr/bin/env python3
"""Create the tables and load the seed data.

From the project root, with DATABASE_URL in the environment or in .env:

    python scripts/init_db.py

Safe to run again. It will not delete chapters or rows you added.
The seed inserts a chapter or milestone only when that one is still missing.
Migrations in db/migrations run after the schema and are safe to repeat,
including on a database created by an older copy of this project.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from db.connection import connect  # noqa: E402

def main() -> None:
    schema = (ROOT / "db" / "schema.sql").read_text(encoding="utf-8")
    seed = (ROOT / "db" / "seed.sql").read_text(encoding="utf-8")
    migrations = sorted((ROOT / "db" / "migrations").glob("*.sql"))
    try:
        with connect() as conn:
            _run_script(conn, schema)
            for path in migrations:
                _run_script(conn, path.read_text(encoding="utf-8"))
            _run_script(conn, seed)
            counts = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM users) AS users,
                    (SELECT COUNT(*) FROM chapters) AS chapters,
                    (SELECT COUNT(*) FROM photos) AS photos
                """
            ).fetchone()
    except Exception as exc:
        name = exc.__class__.__name__
        sys.exit(
            "Could not set up the database. Check DATABASE_URL in .env. "
            "A TigerData URL should include sslmode=require.\n"
            f"{name}: {exc}"
        )

    print(
        "Database is ready. "
        f"Users: {counts['users']}, chapters: {counts['chapters']}, photos: {counts['photos']}."
    )
    print("The two people are Min (slug min) and Su (slug su). There is no password.")


def _run_script(conn, script: str) -> None:
    """Run one SQL file.

    psycopg executes a single statement per call. Full-line comments are
    removed first, then the file is split on ';'. The SQL files do not put
    semicolons inside strings or function bodies.
    """
    lines = [line for line in script.splitlines() if not line.strip().startswith("--")]
    for chunk in "\n".join(lines).split(";"):
        statement = chunk.strip()
        if statement:
            conn.execute(statement)


if __name__ == "__main__":
    main()
