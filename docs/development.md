# Development guide

This repository is a demonstration of the essential CVT snapshot workflow.
The packaged application uses a simulated CVT structure and real Linux process
names. It does not connect to an IBM mainframe or contain production code.

## Requirements

- Linux, or a Linux environment such as WSL.
- Python 3.10 or newer with pip and venv.
- GCC and the `ps` command from procps/procps-ng.
- GNU Make for the optional shortcuts below.

## Local setup

Run these commands from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade 'pip>=26.2.1'
python -m pip install -e '.[dev]'
make run
```

Open http://127.0.0.1:5000 and click Refresh Snapshot to capture data. The first
page request initializes an empty schema; only the CSRF-protected capture form
runs the C collector and stores a snapshot. Reloading the page displays history
without creating more data. The compiler is invoked only when the collector source
is newer than the binary, or the binary is missing.

To initialize or build components separately:

```bash
make init-db
make build-collector
```

Without Make, use `python -m flask --app cvt_dashboard:create_app run`,
`python -m flask --app cvt_dashboard:create_app init-db`, or
`python -m flask --app cvt_dashboard:create_app build-collector`.
Debug mode is disabled by default. Keep the application on localhost.

## Configuration and generated files

Set environment variables in your shell before starting the app:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CVT_INSTANCE_PATH` | `./instance` | Writable runtime directory; relative paths resolve from the working directory. |
| `CVT_SECRET_KEY` | Random key per application instance | Optional stable session signing key, at least 32 characters. |
| `CC` | `gcc` | Path or executable name of a compatible C compiler. |

For example:

```bash
export CVT_INSTANCE_PATH="$(mktemp -d)"
make run
```

The application writes `snapshots.sqlite` and `build/cvt` beneath the runtime
directory. Temporary CSV files are isolated per collection and removed afterward,
including when collection fails. Source files remain untouched.
Runtime directories must be owned by the current user and have mode 0700;
existing directories with broader permissions are rejected. Database files use
mode 0600. Tests use temporary directories and do not modify your local snapshots.

To retain an old checkout's snapshots, stop the app, back up its database, and
copy `my_database.sqlite` to `<CVT_INSTANCE_PATH>/snapshots.sqlite` before starting.
Ensure the containing runtime directory has mode 0700. The table layout is
compatible and initialization preserves existing rows.
The previously tracked databases and binaries are omitted from the new layout;
they remain available in Git history.

## Checks and distribution

```bash
make check
make build
```

CI runs these checks on Python 3.10, 3.12, and 3.14 under Linux. It also installs
the wheel and runs the application from outside the checkout to verify that
its HTML template, SQL schema, C source, and input directives are included.
A wheel still requires GCC and `ps` on the target machine; the C executable is
built locally rather than shipped as a platform-specific binary.

To run static and dependency security scans:

```bash
python -m pip install -e '.[security]'
make security
```

See [the security review](security-review.md) for findings, fixes, checked versions,
and remaining deployment boundaries.

## Historical examples

`examples/user_import/` preserves the earlier C++/Flask/SQLite experiment.
It is separate from the maintained dashboard and automated tests. After installing
the dependencies above, run it with:

```bash
python examples/user_import/init_db.py
python examples/user_import/app.py
```

This example also requires `g++`. It writes its private database and build output
under `./instance-user-import`, configurable with `CVT_EXAMPLE_INSTANCE_PATH`.
Use the Import users from C++ button to populate data. Its import and add-user forms
require CSRF tokens, and GET requests only display data. `square.c` is an independent early C exercise.

`examples/mainframe/cvt_address.c` preserves the original pointer illustration.
It prints a constant address and does not read an actual z/OS CVT. It is not used
by the dashboard or built by the package.

## Demonstration boundaries

The dashboard is a local development application. Its CVT date and extended
address are fixed demonstration values; the CVT address is the runtime address
of the simulated structure. The date is an ordinal `YYYY-DDD` value, despite the
legacy database column name `iso_date`. Only explicit captures create snapshots. The dashboard displays the latest 100
and retains the latest 1,000 after each capture. The app rejects direct remote
clients and untrusted Host headers; it has no authentication system and must not
be exposed through a public proxy.
