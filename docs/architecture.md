# Architecture

## Repository layout

```text
.github/workflows/ci.yml    Automated lint, tests, builds, and wheel smoke checks
src/cvt_dashboard/         Installable application package
  app.py                   Flask factory, routes, and CLI commands
  collector.py             C compilation, execution, and CSV parsing
  database.py              SQLite connections, schema, and snapshot persistence
  security.py              Local access, CSRF, headers, and runtime permissions
  schema.sql               Idempotent snapshot schema
  native/cvt.c             Linux collector with a simulated CVT
  data/fields.txt          Collector input directives
  templates/index.html     Snapshot dashboard
examples/                  Historical experiments and pointer illustration
tests/                     Integration and regression tests
docs/                      Development and architecture documentation
pyproject.toml             Package metadata, dependencies, and tool configuration
Makefile                   Common development commands
```

There is one maintained application source tree. Historical experiments are
kept as examples rather than presented as automated tests. Databases, compiled
executables, generated CSV output, and personal editor configuration are excluded
from version control.

## Snapshot lifecycle

1. Flask initializes the schema using `CREATE TABLE IF NOT EXISTS`.
2. The collector module compiles the bundled C source when necessary.
3. The native executable reads `CVTDATE`, `CVTADDR`, `ECVT`, and `TASKS` directives.
4. It writes a CSV snapshot with simulated control block values and Linux
   process names from `ps`.
5. Python parses the CSV and inserts one snapshot with a parameterized SQL query.
6. Flask displays saved snapshots, newest first.

Opening `/` displays history without running native code. The refresh form sends
a CSRF-protected POST to `/import`, which captures once and redirects to `/` using
HTTP 303. If compilation or collection fails, the app logs the error and displays
existing history with a generic failure message. Builds and collection subprocesses
have timeouts. The dashboard displays at most 100 rows and retains at most 1,000
after an import.

Both apps restrict direct access to loopback clients and trusted local Host headers.
They use Flask-WTF CSRF protection and response security headers. Runtime directories
are private, and database/binary symbolic links are rejected. The C collector uses
`posix_spawn` to run a resolved `ps` executable without a shell. See
[the security review](security-review.md) for remaining boundaries.

SQLite connections belong to a Flask application context and close at teardown.
A temporary output directory belongs to each collection, avoiding shared CSV
files between requests. Compilation writes to a temporary binary before replacing
the cached executable. These measures support local concurrent requests without
writing build products inside the installed package.

## Packaging boundary

The package includes the C source, input directives, schema, and HTML template.
Installation does not import the application, build native code, or create a
database. The application factory accepts configuration overrides for tests and
uses a writable runtime directory for persistent state and native compilation.
