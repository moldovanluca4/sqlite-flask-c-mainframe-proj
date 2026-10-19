import csv
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from cvt_dashboard.collector import collect_snapshot, compile_collector


def test_cli_rejects_missing_arguments_and_missing_input(app, tmp_path):
    with app.app_context():
        binary = compile_collector()
    result = subprocess.run([str(binary)], capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "Usage:" in result.stderr

    output = tmp_path / "should-not-exist.csv"
    result = subprocess.run(
        [str(binary), str(tmp_path / "missing.txt"), str(output), app.config["PS"]], check=False
    )
    assert result.returncode == 2
    assert not output.exists()


def test_cached_binary_is_reused(app):
    with app.app_context():
        binary = compile_collector()
        modified = binary.stat().st_mtime_ns
        assert compile_collector().stat().st_mtime_ns == modified


def test_concurrent_collections_have_independent_output(app):
    def collect():
        with app.app_context():
            return collect_snapshot()

    with ThreadPoolExecutor(max_workers=4) as pool:
        snapshots = list(pool.map(lambda _: collect(), range(4)))

    assert all(snapshot["CVTDATE"] == "2025-177" for snapshot in snapshots)
    assert all(snapshot["TASKS"] for snapshot in snapshots)
    assert list(Path(app.config["BUILD_DIR"]).iterdir()) == [Path(app.config["BUILD_DIR"]) / "cvt"]


def test_large_process_list_is_complete_and_csv_safe(app, tmp_path):
    fake_ps = tmp_path / "ps"
    fake_ps.write_text(
        '#!/bin/sh\ni=0\nwhile [ "$i" -lt 1000 ]; do\n'
        '  printf \'task,"quoted"-%s\\n\' "$i"\n  i=$((i + 1))\ndone\n'
    )
    fake_ps.chmod(0o755)
    with app.app_context():
        binary = compile_collector()
    output = tmp_path / "snapshot.csv"
    subprocess.run(
        [str(binary), str(app.config["INPUT_FILE"]), str(output), str(fake_ps)],
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ.get("PATH", "")},
        check=True,
    )
    with output.open(newline="") as stream:
        snapshot = {row["field"]: row["value"] for row in csv.DictReader(stream)}
    tasks = snapshot["TASKS"].split("; ")
    assert len(tasks) == 1000
    assert tasks[0] == 'task,"quoted"-0'
    assert tasks[-1] == 'task,"quoted"-999'


def test_failed_process_command_is_reported(app, tmp_path):
    fake_ps = tmp_path / "ps"
    fake_ps.write_text("#!/bin/sh\nexit 1\n")
    fake_ps.chmod(0o755)
    with app.app_context():
        compile_collector()
        app.config["PS"] = str(fake_ps)
        with pytest.raises(subprocess.CalledProcessError):
            collect_snapshot()
    assert not list(Path(app.config["BUILD_DIR"]).glob("**/*.csv"))
