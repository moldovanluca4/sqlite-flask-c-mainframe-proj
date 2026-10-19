import csv
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import current_app

from .security import private_directory

SOURCE = Path(__file__).parent / "native" / "cvt.c"


def compile_collector():
    build_dir = Path(current_app.config["BUILD_DIR"])
    private_directory(build_dir.parent)
    private_directory(build_dir)
    binary = build_dir / "cvt"
    if binary.is_symlink():
        raise PermissionError("Collector executable must not be a symbolic link")
    if binary.is_file() and binary.stat().st_mtime_ns >= SOURCE.stat().st_mtime_ns:
        return binary

    with TemporaryDirectory(dir=build_dir) as temporary:
        target = Path(temporary) / "cvt"
        subprocess.run(
            [
                current_app.config["CC"],
                "-std=c11",
                "-D_POSIX_C_SOURCE=200809L",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-O2",
                "-o",
                str(target),
                str(SOURCE),
            ],
            check=True,
            timeout=30,
        )
        target.replace(binary)
    return binary


def collect_snapshot():
    process_command = current_app.config["PS"]
    if not process_command:
        raise FileNotFoundError("The ps executable is required")
    binary = compile_collector()
    input_file = Path(current_app.config["INPUT_FILE"])
    if not input_file.is_file():
        raise FileNotFoundError(f"Collector input file not found: {input_file}")

    with TemporaryDirectory(dir=current_app.config["BUILD_DIR"]) as temporary:
        output_file = Path(temporary) / "snapshot.csv"
        subprocess.run(
            [str(binary), str(input_file), str(output_file), str(process_command)],
            check=True,
            timeout=30,
        )
        with output_file.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != ["field", "value"]:
                raise ValueError("Unexpected collector output header")
            return {row["field"]: row["value"] for row in reader}
