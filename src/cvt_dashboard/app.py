import os
import secrets
import shutil
import sqlite3
import subprocess
from pathlib import Path

import click
from flask import Flask, flash, redirect, render_template, url_for

from . import collector, database
from .security import init_security


def create_app(test_config=None):
    instance_path = Path(os.environ.get("CVT_INSTANCE_PATH", "instance")).absolute()
    app = Flask(__name__, instance_path=str(instance_path), instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("CVT_SECRET_KEY") or secrets.token_hex(32),
        DATABASE=instance_path / "snapshots.sqlite",
        BUILD_DIR=instance_path / "build",
        INPUT_FILE=Path(__file__).parent / "data" / "fields.txt",
        CC=os.environ.get("CC", "gcc"),
        PS=shutil.which("ps"),
        MAX_SNAPSHOTS=1000,
        DISPLAY_LIMIT=100,
    )
    if test_config:
        app.config.update(test_config)
    if len(app.config["SECRET_KEY"]) < 32:
        raise ValueError("CVT_SECRET_KEY must contain at least 32 characters")

    init_security(app)
    database.init_app(app)

    @app.cli.command("init-db", help="Create the schema without deleting existing snapshots.")
    def init_db_command():
        database.init_db()
        click.echo("Database initialized.")

    @app.cli.command("build-collector", help="Compile the bundled C collector when needed.")
    def build_collector_command():
        click.echo(collector.compile_collector())

    @app.get("/")
    def index():
        database.init_db()
        rows = (
            database.get_connection()
            .execute(
                "SELECT * FROM cvt ORDER BY captured_at DESC, id DESC LIMIT ?",
                (app.config["DISPLAY_LIMIT"],),
            )
            .fetchall()
        )
        return render_template("index.html", rows=rows)

    @app.post("/import")
    def importing():
        try:
            database.init_db()
            database.import_snapshot(collector.collect_snapshot())
            flash("Snapshot imported.")
        except (OSError, subprocess.SubprocessError, ValueError, sqlite3.Error):
            app.logger.exception("Snapshot collection failed")
            flash("Snapshot collection failed. Check the application logs for details.")
        return redirect(url_for("index"), code=303)

    return app
