import sqlite3
from pathlib import Path

from flask import current_app, g

from .security import private_database


def get_connection():
    if "database" not in g:
        database_path = Path(current_app.config["DATABASE"])
        private_database(database_path)
        g.database = sqlite3.connect(database_path)
        g.database.row_factory = sqlite3.Row
    return g.database


def close_connection(error=None):
    connection = g.pop("database", None)
    if connection is not None:
        connection.close()


def init_app(app):
    app.teardown_appcontext(close_connection)


def init_db():
    schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    get_connection().executescript(schema)


def import_snapshot(snapshot):
    if not snapshot:
        return
    iso_date = snapshot.get("CVTDATE", "")
    yday = int(iso_date.rsplit("-", 1)[1]) if "-" in iso_date else None
    connection = get_connection()
    with connection:
        connection.execute(
            """INSERT INTO cvt (iso_date, yday, cvt_address, ecvt_address, tasks)
               VALUES (?, ?, ?, ?, ?)""",
            (
                iso_date,
                yday,
                snapshot.get("CVTADDR"),
                snapshot.get("ECVT"),
                snapshot.get("TASKS", ""),
            ),
        )
        connection.execute(
            "DELETE FROM cvt WHERE id NOT IN (SELECT id FROM cvt ORDER BY id DESC LIMIT ?)",
            (current_app.config["MAX_SNAPSHOTS"],),
        )
