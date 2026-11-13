"""Image references for photos, covers, and milestones.

The database stores a path or a URL, never the file itself. This module is the
only place that decides how an image gets stored, so a later upload service
can replace the body of save_image() without route changes.
"""

from __future__ import annotations

from urllib.parse import urlparse


class StorageError(ValueError):
    """The image reference is missing or not allowed."""


def save_image(source: str) -> str:
    """Validate an image reference and return the value to store.

    Accepts either an http(s) URL or a path under public/assets/
    (for example assets/photo.jpg, /assets/photo.jpg, or public/assets/photo.jpg).

    # TODO: replace with Vercel Blob upload
    When file uploads arrive, accept the uploaded file here, send it to
    Vercel Blob, and return the blob URL. Callers should keep using
    save_image() and should not learn where the bytes live.
    """
    cleaned = (source or "").strip()
    if not cleaned:
        raise StorageError("Add an image path or URL.")
    if len(cleaned) > 2000:
        raise StorageError("That image path is too long.")

    if cleaned.lower().startswith(("http://", "https://")):
        return _http_url(cleaned)

    return _asset_path(cleaned)


def _http_url(source: str) -> str:
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise StorageError("That image URL doesn't look right.")
    if parsed.username or parsed.password:
        raise StorageError("That image URL doesn't look right.")
    return source


def _asset_path(source: str) -> str:
    if "\\" in source or source.startswith("//"):
        raise StorageError("Use a path like assets/photo.jpg, or a full image URL.")

    relative = source.lstrip("/")
    if relative.startswith("public/"):
        relative = relative[len("public/") :]

    parts = [part for part in relative.split("/") if part not in {"", "."}]
    if (
        not parts
        or any(part == ".." for part in parts)
        or any("?" in part or "#" in part for part in parts)
    ):
        raise StorageError("Use a path like assets/photo.jpg, or a full image URL.")
    if len(parts) < 2 or parts[0] != "assets":
        raise StorageError(
            "Put the file in public/assets and use a path like assets/photo.jpg, or paste an image URL."
        )
    return "/".join(parts)
