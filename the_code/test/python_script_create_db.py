from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "the_database.sqlite"
SCHEMA_SQL_PATH = BASE_DIR / "table_creator.sql"

def require_db(db_path=DB_PATH, schema_file=SCHEMA_SQL_PATH):
    if not schema_file.is_file():
        raise FileNotFoundError(f"sql not found")

    sql_script = schema_file.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql_script)

    print(f"Database created at: {db_path}")

if __name__ == "__main__":
    require_db()
