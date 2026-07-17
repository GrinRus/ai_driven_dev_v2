# Browser Testing Policy

## Decision

AIDD's provider-free rendered-browser lane uses the Python Playwright sync API and Chromium
as its single initial browser target. Playwright is development-only test infrastructure; it is
not part of the operator UI runtime, core, adapters, or published runtime dependencies.

The maintained commands are:

```bash
uv run --extra dev python -m playwright install chromium
uv run --extra dev pytest -q browser_tests
```

Browser tests live in the repository-root `browser_tests/` directory, outside the default
`tests/` collection. Until `W36-E7-S2` adds an explicit browser CI lane, ordinary
`uv run --extra dev pytest -q` and existing CI jobs do not require a browser binary.

## Packaging boundary

- `playwright` may be declared only in the `dev` extra; it must not appear as a runtime
  `Requires-Dist` entry in built-wheel metadata.
- Chromium binaries are installed into Playwright's external browser cache. They are never
  copied into the source tree, sdist, or wheel.
- The packaged UI remains Python-served static HTML, CSS, and JavaScript. No Node product
  runtime, Vite build, npm dependency, or npm lockfile is introduced.
- Browser tests exercise the installed/package resource paths through the public loopback UI;
  they do not import a second UI implementation.
- A missing Chromium executable is an actionable failure that prints the maintained install
  command. It is not a silent skip.

One target keeps the initial lane bounded while still executing real layout, browser networking,
DOM, and JavaScript behavior. Additional engines require a separate compatibility decision and
evidence; they are not inferred from Playwright support.

## Network and evidence boundary

The deterministic suite allows only the loopback origin created for its disposable local
project. Provider authentication, provider runtimes, remote repositories, arbitrary filesystem
reads, and external network requests are outside this lane. Screenshots and generated `.aidd/`
state remain temporary unless a later task defines a curated evidence bundle.
