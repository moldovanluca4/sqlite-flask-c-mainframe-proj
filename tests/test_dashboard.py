from pathlib import Path

from cvt_dashboard import database


def test_fresh_dashboard_builds_collects_persists_and_renders(app, post_form):
    response = post_form(app.test_client())

    assert response.status_code == 200
    assert b"CVT Snapshot Dashboard" in response.data
    assert b"Snapshot collection failed" not in response.data
    with app.app_context():
        row = database.get_connection().execute("SELECT * FROM cvt").fetchone()
        assert row["iso_date"] == "2025-177"
        assert row["yday"] == 177
        assert row["cvt_address"].startswith("0x")
        assert row["ecvt_address"] == "0x7ffbcafe"
        assert row["tasks"]
        assert row["iso_date"].encode() in response.data
    assert (Path(app.config["BUILD_DIR"]) / "cvt").is_file()
    assert not list(Path(app.config["BUILD_DIR"]).glob("**/*.csv"))


def test_refresh_captures_exactly_once(app, post_form):
    client = app.test_client()
    post_form(client)
    response = post_form(client)

    assert response.status_code == 200
    with app.app_context():
        assert database.get_connection().execute("SELECT COUNT(*) FROM cvt").fetchone()[0] == 2


def test_missing_compiler_preserves_history_and_displays_failure(app, post_form):
    client = app.test_client()
    post_form(client)
    binary = Path(app.config["BUILD_DIR"]) / "cvt"
    binary.unlink()
    app.config["CC"] = str(binary.parent / "missing-compiler")

    response = post_form(client)

    assert response.status_code == 200
    assert b"Snapshot collection failed" in response.data
    assert b"2025-177" in response.data
    with app.app_context():
        assert database.get_connection().execute("SELECT COUNT(*) FROM cvt").fetchone()[0] == 1


def test_init_db_command_is_repeatable_and_preserves_snapshots(app, post_form):
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    post_form(app.test_client())
    assert runner.invoke(args=["init-db"]).exit_code == 0
    with app.app_context():
        assert database.get_connection().execute("SELECT COUNT(*) FROM cvt").fetchone()[0] == 1
