"""Short-lived Postgres connections for a serverless app.

Each call opens one connection and closes it before returning. Vercel runs
this as short-lived isolates, so a process-wide pool would hold connections
that the next request cannot reuse.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    """Return DATABASE_URL, adding sslmode=require when the URL has no sslmode."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    if "sslmode=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}sslmode=require"


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Open a connection, commit on success, and always close it.

    prepare_threshold=None stays safe behind TigerData's connection pooler
    (PgBouncer in transaction mode cannot share prepared statements). Direct
    connections work the same way.
    """
    with psycopg.connect(
        database_url(),
        row_factory=dict_row,
        prepare_threshold=None,
        connect_timeout=10,
        application_name="min-su-library",
    ) as conn:
        yield conn
