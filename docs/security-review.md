# Security review

Reviewed on 2026-10-19. Scope: maintained application, historical examples,
native collectors, configuration, CI, and dependencies installed in an isolated
environment. This is a code review and automated scan, not a penetration test or
a guarantee that every vulnerability has been found.

## Findings and changes

| Priority | Finding | Resolution |
| --- | --- | --- |
| High when exposed | The user-import example enabled Flask's interactive debugger. | Removed automatic debug mode; the example starts on Flask's default loopback interface. |
| High when exposed | Both dashboards exposed local data without an access boundary. | Both reject non-loopback client addresses and untrusted Host headers. They remain local demonstration applications. |
| Medium | A fixed session signing key remained in the example. | Replaced it with a random per-process key or `CVT_SECRET_KEY`. Both apps reject configured keys shorter than 32 characters. |
| Medium | GET requests triggered native execution and database writes, and forms lacked CSRF protection. | GET now displays data. Capture/import use POST and Flask-WTF CSRF validation; the example's add-user form is also protected. |
| Medium | Snapshot history and response size grew without bounds. | Retain the latest 1,000 snapshots after each capture and render at most 100. Request bodies and multipart fields have limits. |
| Medium | Database files inherited permissive defaults; cached binaries could be symbolic links. | Require private runtime directories owned by the current user with mode 0700; database files use 0600 and reject symbolic links. Cached binary symbolic links are rejected. |
| Medium | The example returned exception details to browsers and reused an output filename across requests. | Log exceptions server-side, display generic errors, isolate temporary output, use subprocess timeouts, and close SQLite connections at teardown. |
| Low | The collector invoked a fixed `ps` command through a shell and resolved it through PATH on every execution. | Resolve `ps` when creating the app, then execute that explicit path with `posix_spawn` and an argument array. No shell parses the command. |
| Low | The C++ example did not quote CSV fields, and the standalone square helper could overflow a signed 32-bit result. | Escape CSV fields, fail on incomplete input, and calculate the square using a 64-bit result. |
| Supply chain | CI used mutable Action tags and retained checkout credentials. | Pin verified Action commits, disable credential persistence, retain read-only workflow permissions, and run dependency/static security scans. |

The previously fixed C aggregate-buffer overflow and CSV escaping remain covered
by the regression suite. SQL values are passed as query parameters. Templates
retain Jinja autoescaping. Both apps send a restrictive Content Security Policy,
anti-framing and MIME-sniffing headers, a no-referrer policy, and no-store cache
headers. Inline CSS remains allowed for the existing templates; scripts and
external resources are blocked.

## Paths, keys, and original comments

No developer-specific absolute paths or credential-like private keys/access tokens
were found in the current source/configuration scan. Package resources resolve
relative to the package. Runtime locations are configurable and are checked before
use. The CVT date, `0x7FFBCAFE`, and the mainframe illustration's `0x10` are
intentional demonstration values, not credentials.

The runtime build directory, compiler selection (`CC`/`CXX`), and input-file
configuration are trusted local settings. Do not let untrusted users control these
settings or the environment used to launch the app. The original fixed demo
session keys still exist in earlier Git revisions; they must never be reused.
Git history was not rewritten.

Assistant-added source comments and docstrings were removed. The original
mainframe illustration and its author's comments remain unchanged. The README
still contains only the previously requested extra sentence.

## Verification

- 17 integration and security tests pass on Python 3.14. Tests cover valid and
  invalid CSRF requests, remote-address and Host restrictions, escaping, response
  headers, request/history limits, file permissions and symlinks, native collection,
  concurrency, and the historical example's forms and error handling.
- Bandit reports no medium/high findings. Seven low findings remain for importing
  `subprocess` and executing compiler/collector argument arrays. These were reviewed:
  executable paths and input paths come from local configuration, not HTTP input;
  `shell=True` is not used. These findings have not been suppressed.
- GCC static analysis (`-fanalyzer`, with warnings treated as errors) passes for
  the maintained C collector and the C++ example. The square helper also passes
  an explicit `INT32_MIN` boundary check.
- The rebuilt wheel passes capture, CSRF, and Host-header checks when installed
  and run outside the checkout.
- `pip-audit` reports no known vulnerabilities across 48 installed distributions,
  including runtime dependencies and development/security tools. It skips this
  local editable project, whose source is reviewed separately.
- The initial audit flagged four distinct advisory IDs affecting pip 26.0.1 in
  the temporary review environment. That environment now uses pip 26.2.1. CI and
  setup instructions upgrade pip before installing dependencies. The host Python
  installation was not modified.

Audited runtime versions include Flask 3.1.3, Flask-WTF 1.3.0, Werkzeug 3.1.9,
Jinja2 3.1.6, and WTForms 3.2.2. Advisory results describe these installed versions
at review time; future resolutions must be scanned again.

To repeat the checks in an activated virtual environment:

```bash
python -m pip install --upgrade 'pip>=26.2.1'
python -m pip install -e '.[dev,security]'
make check
make security
```

`make security` fails on medium/high Bandit findings or known package advisories.
It requires network access for the dependency advisory lookup.

## Remaining boundaries

These applications have no user accounts, authentication, or authorization model.
The loopback and Host restrictions protect direct local use; they do not make the
apps suitable for deployment behind a proxy. A local reverse proxy can make remote
clients appear to come from loopback. Do not expose or proxy these dashboards to
untrusted clients without adding authentication, authorization, TLS, and deployment
controls. Process names and simulated-structure runtime addresses are intentionally
displayed to the local user.

Cookies use HttpOnly and SameSite=Strict. Secure cookies and HSTS are not enabled
for the default HTTP localhost workflow. A future HTTPS deployment must configure
those settings. Random session keys change on restart unless a stable secret is
supplied through the environment. A compromised OS account can still replace its
own code, binaries, configuration, and database.

The audit does not cover OS-level CVEs in Python, GCC, SQLite, procps, or the host,
and GitHub's remote CI matrix was not run during this local review. AddressSanitizer
and UndefinedBehaviorSanitizer could not be linked because their runtime libraries
are missing from this environment; dynamic sanitizer checks were not completed.

## References

- [Flask security considerations](https://flask.palletsprojects.com/en/stable/web-security/)
- [Flask-WTF CSRF protection](https://flask-wtf.readthedocs.io/en/latest/csrf/)
- [pip-audit scope and usage](https://github.com/pypa/pip-audit)
