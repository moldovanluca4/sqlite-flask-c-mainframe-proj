# Contributing

See [the development guide](docs/development.md) for prerequisites, installation,
configuration, and commands, and [the architecture guide](docs/architecture.md)
for the repository layout and snapshot flow.

1. Create a focused branch for your change.
2. Keep maintained application code in `src/cvt_dashboard/` and automated tests
   in `tests/`. Keep historical examples separate.
3. Add or update tests when behavior or component integration changes.
4. Run `make check` and `make build` before opening a pull request.
5. Describe the problem, resulting behavior, and checks performed in the pull
   request. Update `docs/` when setup or architecture changes.

Do not commit virtual environments, local configuration, databases, compiled
executables, generated output, or personal IDE settings. Keep changes to
`README.md` limited to explicitly requested edits so the original project
presentation is preserved.

For changes to input handling, persistence, native execution, or configuration,
also install `.[security]` and run `make security`. See the
[security review](docs/security-review.md) for the local-access boundary and
remaining limitations.
