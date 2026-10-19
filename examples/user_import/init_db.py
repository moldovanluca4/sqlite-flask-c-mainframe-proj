import os
import sqlite3
from contextlib import closing
from pathlib import Path

from cvt_dashboard.security import private_database

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = Path(os.environ.get("CVT_EXAMPLE_INSTANCE_PATH", "instance-user-import")).absolute()
DB_PATH = INSTANCE_DIR / "users.sqlite"
SCHEMA_SQL_PATH = BASE_DIR / "table_creator.sql"


def require_db(db_path=DB_PATH, schema_file=SCHEMA_SQL_PATH):
    sql_script = Path(schema_file).read_text(encoding="utf-8")
    private_database(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.executescript(sql_script)
    print(f"Database created at: {db_path}")


if __name__ == "__main__":
    require_db()
