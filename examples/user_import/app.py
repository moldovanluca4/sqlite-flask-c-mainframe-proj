import csv
import os
import secrets
import sqlite3
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, flash, g, redirect, render_template, request, url_for

from cvt_dashboard.security import init_security, private_database, private_directory

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = Path(os.environ.get("CVT_EXAMPLE_INSTANCE_PATH", "instance-user-import")).absolute()
CPP_SRC = BASE_DIR / "some_users.cpp"
CPP_BIN = INSTANCE_DIR / "build" / "some_users"
INPUT_FILE = BASE_DIR / "input_users_for_cpp.txt"
DB_FILE = INSTANCE_DIR / "users.sqlite"
SCHEMA_FILE = BASE_DIR / "table_creator.sql"

app = Flask(__name__)
app.secret_key = os.environ.get("CVT_SECRET_KEY") or secrets.token_hex(32)
if len(app.secret_key) < 32:
    raise ValueError("CVT_SECRET_KEY must contain at least 32 characters")
init_security(app)


def get_conn():
    if "example_database" not in g:
        private_database(DB_FILE)
        g.example_database = sqlite3.connect(DB_FILE)
        g.example_database.row_factory = sqlite3.Row
    return g.example_database


@app.teardown_appcontext
def close_conn(error=None):
    conn = g.pop("example_database", None)
    if conn is not None:
        conn.close()


def ensure_schema():
    get_conn().executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def compile_cpp():
    private_directory(INSTANCE_DIR)
    private_directory(CPP_BIN.parent)
    if CPP_BIN.is_symlink():
        raise PermissionError("Collector executable must not be a symbolic link")
    if CPP_BIN.is_file() and CPP_BIN.stat().st_mtime_ns >= CPP_SRC.stat().st_mtime_ns:
        return
    with TemporaryDirectory(dir=CPP_BIN.parent) as temporary:
        binary = Path(temporary) / "some_users"
        subprocess.run(
            [os.environ.get("CXX", "g++"), "-std=c++17", "-O2", "-o", str(binary), str(CPP_SRC)],
            check=True,
            timeout=30,
        )
        binary.replace(CPP_BIN)


def run_cpp():
    if not INPUT_FILE.is_file():
        raise FileNotFoundError("User import input file is missing")
    with TemporaryDirectory(dir=CPP_BIN.parent) as temporary:
        output = Path(temporary) / "users.csv"
        subprocess.run([str(CPP_BIN), str(INPUT_FILE), str(output)], check=True, timeout=30)
        with output.open(newline="", encoding="utf-8") as stream:
            return list(csv.reader(stream))


def import_rows(rows):
    with get_conn() as conn:
        conn.executemany("INSERT INTO users (name, email) VALUES (?, ?)", rows)


@app.get("/")
def index():
    ensure_schema()
    users = get_conn().execute("SELECT * FROM users ORDER BY id DESC LIMIT 100").fetchall()
    return render_template("interface.html", users=users)


@app.post("/add")
def add():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name or not email or len(name) > 255 or len(email) > 255:
        flash("Name and email are required and must be at most 255 characters.")
        return redirect(url_for("index"), code=303)
    try:
        ensure_schema()
        with get_conn() as conn:
            conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    except sqlite3.Error:
        app.logger.exception("User creation failed")
        flash("Could not save the user. Check the application logs for details.")
    return redirect(url_for("index"), code=303)


@app.post("/import")
def import_from_cpp():
    try:
        ensure_schema()
        compile_cpp()
        rows = run_cpp()
        import_rows(rows)
        flash(f"Imported {len(rows)} users from C++.")
    except (OSError, subprocess.SubprocessError, sqlite3.Error, ValueError):
        app.logger.exception("User import failed")
        flash("Import failed. Check the application logs for details.")
    return redirect(url_for("index"), code=303)


if __name__ == "__main__":
    app.run()
