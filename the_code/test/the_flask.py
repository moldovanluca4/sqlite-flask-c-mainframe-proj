from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, subprocess, csv, os, time

BASE_DIR     = Path(__file__).resolve().parent
CPP_SRC      = BASE_DIR / "some_users.cpp"
CPP_BIN      = BASE_DIR / "some_users"
INPUT_FILE   = BASE_DIR / "input_users_for_cpp.txt"
OUTPUT_FILE  = BASE_DIR / f"output_{int(time.time())}.csv"
DB_FILE      = BASE_DIR / "the_database.sqlite"
SCHEMA_FILE  = BASE_DIR / "table_creator.sql"

app = Flask(__name__)
app.secret_key = '1246gdgvgg'

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_schema():
    if DB_FILE.exists():
        return
    with get_conn() as conn, open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

def compile_cpp():
    if CPP_BIN.exists() and CPP_BIN.stat().st_mtime >= CPP_SRC.stat().st_mtime:
        return
    cmd = ["g++", "-std=c++17", "-O2", "-o", str(CPP_BIN), str(CPP_SRC)]
    subprocess.run(cmd, check=True)
    print("compiled successful!!")

def run_cpp():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found.")
    cmd = [str(CPP_BIN), str(INPUT_FILE), str(OUTPUT_FILE)]
    subprocess.run(cmd, check=True)
    print("Run successful")
    with open(OUTPUT_FILE, newline="", encoding="utf-8") as f:
        print("read outputfile")
        rows = list(csv.reader(f))
    try:
        print("ok")
        OUTPUT_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    return rows

def import_rows(rows):
    if not rows:
        print("no rows")
        return
    with get_conn() as conn:
        print("insert into database")
        conn.executemany("INSERT INTO users (name, email) VALUES (?, ?)", rows)
        conn.commit()

@app.route("/")
def index():
    try:
        compile_cpp()
        rows = run_cpp()
        import_rows(rows)
    except Exception as e:
        flash(f"Import failed: {e}")
  
    with get_conn() as conn:
        users = conn.execute("SELECT * FROM users").fetchall()
    return render_template("interface.html", users=users)


@app.route("/add", methods=["POST"])
def add():
    name  = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name or not email:
        flash("Both name and email are required.")
        return redirect(url_for("index"))
    try:
        with get_conn() as conn:
            conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
            conn.commit()
    except sqlite3.Error as exc:
        flash(f"Database error: {exc}")
    return redirect(url_for("index"))

@app.route("/import")
def import_from_cpp():
    try:
        compile_cpp()
        rows = run_cpp()
        import_rows(rows)
        flash(f"Imported {len(rows)} users from cpp")
    except Exception as e:
        flash(f"Import failed: {e}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
