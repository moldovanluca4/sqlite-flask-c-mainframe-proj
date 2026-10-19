import os
import stat
from ipaddress import ip_address
from pathlib import Path

from flask import abort, request
from flask_wtf.csrf import CSRFProtect


def init_security(app):
    app.config.update(
        TRUSTED_HOSTS=["localhost", "127.0.0.1", "[::1]"],
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        MAX_CONTENT_LENGTH=16 * 1024,
        MAX_FORM_MEMORY_SIZE=16 * 1024,
        MAX_FORM_PARTS=20,
    )

    @app.before_request
    def require_loopback():
        try:
            local = ip_address(request.remote_addr or "").is_loopback
        except ValueError:
            local = False
        if not local:
            abort(403)

    CSRFProtect(app)

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'unsafe-inline'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response


def private_directory(path):
    path = Path(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) & 0o077
    ):
        raise PermissionError("Runtime directories must be owned by you with mode 0700")
    return path


def private_database(path):
    path = Path(path)
    private_directory(path.parent)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise PermissionError("Database must be a regular file owned by you")
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)
    return path
