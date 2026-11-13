"""Min&Su Library — FastAPI entrypoint.

Vercel loads the module-level `app`. Locally:

    uvicorn app:app --reload
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

load_dotenv()

from config import SITE_NAME
from routes.chapters import router as chapters_router
from routes.content import router as content_router
from routes.identity import apply_pending_cookies, router as identity_router
from templating import render

logger = logging.getLogger("minsu")
BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Copy .env.example to .env and add one.")

app = FastAPI(title=SITE_NAME, docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(identity_router)
app.include_router(chapters_router)
app.include_router(content_router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    apply_pending_cookies(request, response)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    location = None
    if exc.headers:
        location = exc.headers.get("Location")
    if exc.status_code in {301, 302, 303, 307, 308} and location:
        return RedirectResponse(location, status_code=exc.status_code)
    if exc.status_code == 404:
        return render(request, "404.html", status_code=404)
    if exc.status_code == 403:
        return render(request, "403.html", status_code=403)
    logger.warning("HTTP %s on %s", exc.status_code, request.url.path)
    return render(request, "500.html", status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def invalid_path(request: Request, _exc: RequestValidationError):
    # /chapter/not-a-number and other bad paths use the same page as a missing chapter.
    return render(request, "404.html", status_code=404)


@app.exception_handler(Exception)
async def unhandled(request: Request, _exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return render(request, "500.html", status_code=500)


def _mount_local_files() -> None:
    """Serve public/ for local uvicorn.

    Vercel serves that directory from the CDN and does not want it mounted.
    """
    if os.environ.get("VERCEL") == "1":
        return
    public = BASE_DIR / "public"
    app.mount("/css", StaticFiles(directory=public / "css"), name="css")
    app.mount("/js", StaticFiles(directory=public / "js"), name="js")
    app.mount("/assets", StaticFiles(directory=public / "assets"), name="assets")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> FileResponse:
        return FileResponse(public / "assets" / "brand" / "favicon-32.png")

    @app.get("/robots.txt", include_in_schema=False)
    def robots() -> FileResponse:
        return FileResponse(public / "robots.txt", media_type="text/plain")


_mount_local_files()
