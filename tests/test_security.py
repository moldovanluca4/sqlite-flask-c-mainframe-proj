import importlib.util
import re
import secrets
import stat
import sys
from pathlib import Path

import pytest

from cvt_dashboard import create_app, database
from cvt_dashboard.collector import compile_collector
from cvt_dashboard.security import private_database, private_directory


def test_get_requests_do_not_capture_or_compile(app):
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/import").status_code == 405
    assert not Path(app.config["BUILD_DIR"]).exists()
    with app.app_context():
        assert database.get_connection().execute("SELECT COUNT(*) FROM cvt").fetchone()[0] == 0


def test_capture_requires_valid_session_bound_csrf_token(app):
    client = app.test_client()
    response = client.get("/")
    assert client.post("/import").status_code == 400
    assert client.post("/import", data={"csrf_token": secrets.token_hex(32)}).status_code == 400
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)
    assert app.test_client().post("/import", data={"csrf_token": token}).status_code == 400
    assert not Path(app.config["BUILD_DIR"]).exists()


def test_remote_clients_and_untrusted_hosts_are_denied(app):
    client = app.test_client()
    assert client.get("/", environ_overrides={"REMOTE_ADDR": "192.0.2.1"}).status_code == 403
    assert client.get("/", headers={"Host": "attacker.example"}).status_code == 400
    assert (
        client.get(
            "/",
            headers={"X-Forwarded-For": "127.0.0.1"},
            environ_overrides={"REMOTE_ADDR": "192.0.2.1"},
        ).status_code
        == 403
    )


def test_html_is_escaped_and_security_headers_are_present(app):
    with app.app_context():
        database.init_db()
        database.import_snapshot({"CVTDATE": "2025-177", "TASKS": '<script>alert("x")</script>'})
    response = app.test_client().get("/")
    assert b"<script>" not in response.data
    assert b"&lt;script&gt;" in response.data
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert "SameSite=Strict" in response.headers["Set-Cookie"]


def test_request_and_history_sizes_are_bounded(app):
    response = app.test_client().post("/import", data={"payload": "x" * (17 * 1024)})
    assert response.status_code == 413
    app.config.update(MAX_SNAPSHOTS=3, DISPLAY_LIMIT=2)
    with app.app_context():
        database.init_db()
        for day in range(100, 105):
            database.import_snapshot({"CVTDATE": f"2025-{day}"})
        assert database.get_connection().execute("SELECT COUNT(*) FROM cvt").fetchone()[0] == 3
    response = app.test_client().get("/")
    assert b"2025-104" in response.data
    assert b"2025-103" in response.data
    assert b"2025-102" not in response.data


def test_runtime_permissions_and_symlink_rejection(app, tmp_path):
    app.test_client().get("/")
    assert stat.S_IMODE(Path(app.config["DATABASE"]).stat().st_mode) == 0o600
    with app.app_context():
        binary = compile_collector()
        assert stat.S_IMODE(binary.parent.stat().st_mode) == 0o700
        binary.unlink()
        binary.symlink_to(tmp_path / "untrusted")
        with pytest.raises(PermissionError):
            compile_collector()
    link = tmp_path / "linked.sqlite"
    link.symlink_to(app.config["DATABASE"])
    with pytest.raises(OSError):
        private_database(link)
    public = tmp_path / "public"
    public.mkdir(mode=0o755)
    with pytest.raises(PermissionError):
        private_directory(public)


def test_weak_configured_key_is_rejected(monkeypatch):
    monkeypatch.setenv("CVT_SECRET_KEY", "short")
    with pytest.raises(ValueError):
        create_app()


def test_example_forms_are_protected_and_do_not_leak_errors(tmp_path, monkeypatch, post_form):
    monkeypatch.setenv("CVT_EXAMPLE_INSTANCE_PATH", str(tmp_path / "example"))
    monkeypatch.setenv("CVT_SECRET_KEY", secrets.token_hex(32))
    source = Path(__file__).parents[1] / "examples" / "user_import" / "app.py"
    spec = importlib.util.spec_from_file_location("user_import_security_test", source)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    client = module.app.test_client()
    assert not module.app.debug
    assert client.get("/").status_code == 200
    assert client.get("/import").status_code == 405
    assert (
        client.post("/add", data={"name": "test", "email": "test@example.com"}).status_code == 400
    )
    response = post_form(client, "/add", {"name": '<script>alert("x")</script>', "email": "x@y"})
    assert b"<script>" not in response.data
    assert b"&lt;script&gt;" in response.data
    csv_input = tmp_path / "quoted-users.txt"
    csv_input.write_text('name,"quoted" test@example.com\n')
    module.INPUT_FILE = csv_input
    response = post_form(client)
    assert b"Imported" in response.data
    with module.app.app_context():
        rows = module.get_conn().execute("SELECT name FROM users ORDER BY id DESC").fetchall()
        assert rows[0]["name"] == 'name,"quoted"'
    module.CPP_BIN.unlink()
    monkeypatch.setenv("CXX", str(tmp_path / "missing-compiler"))
    response = post_form(client)
    assert b"Import failed." in response.data
    assert str(tmp_path).encode() not in response.data
