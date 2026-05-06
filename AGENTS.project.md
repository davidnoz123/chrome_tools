# AGENTS.md

## Python Environment

- **Python interpreter**: `C:\analytics\projects\git\lexi\demos\venv\Scripts\python.exe`

---

## Code Editing Policy

### Syntax-check after every Python edit

After editing any `.py` file, immediately verify it parses cleanly before committing:

```powershell
& "C:\analytics\projects\git\lexi\demos\venv\Scripts\python.exe" -m py_compile path\to\edited_file.py
```

A `SyntaxError` or `IndentationError` at module level causes a completely silent crash — the process dies before any log call is reached.

### `safe_local_imports` — blast-radius limitation

Any Python file with an `if __name__ == "__main__":` block that imports non-stdlib modules must centralise those imports in a single function named `safe_local_imports`:

```python
def safe_local_imports(g: dict) -> None:
    """Load all non-stdlib local-module imports into *g* (pass globals()).

    Centralising imports here limits blast radius: if any import raises
    (e.g. a SyntaxError or ImportError buried in an imported module), the
    exception is caught, logged with a full traceback, then re-raised —
    so the log always contains a FATAL line before the process dies.

    Call once at the top of `if __name__ == "__main__":`, before calling main():
        safe_local_imports(globals())
    """
    try:
        from mymodule import MyClass         # <- replace with this file's actual imports
        g["MyClass"] = MyClass
        # ... all other non-stdlib imports ...
    except Exception:
        import traceback as _tb
        _log(f"FATAL: safe_local_imports failed:\n{_tb.format_exc()}")
        raise


if __name__ == "__main__":
    safe_local_imports(globals())
    main()   # MyClass etc. now available as module globals
```

**Scope:**
- Same-repo local imports only.
- stdlib imports do not belong here.

**Why "blast radius":** A `SyntaxError` or `ImportError` buried inside an imported module kills the process before `_log` is even defined. Without `safe_local_imports`, a hidden-window process exits with no log entry. With it, there is always at least one `FATAL` line in the log.

---

## Chrome Tools Agent Policy

This repo provides human-supervised Chrome control through a narrow CDP-based tool layer.

### Goal

Grow `chrome_tools.py` into a safe, auditable, Claude-friendly browser-control layer over raw Chrome DevTools Protocol.

The tool should help an agent observe and interact with a visible browser page using structured refs, not raw selectors or coordinates.

### Allowed

- Observe the current browser page.
- Read visible text and listed controls.
- Take screenshots.
- Scroll to text or controls.
- Expand and collapse non-final UI sections.
- Focus fields.
- Fill or paste human-reviewed text.
- Upload files explicitly identified by the human.
- Save page state and action logs.
- Capture console/runtime/network diagnostics for debugging.

### Not allowed

- Submit, finalize, complete, accept, or start tasks.
- Bypass login, captchas, timers, rate limits, or access controls.
- Mass scrape platform content.
- Hide actions from the human.
- Click destructive or final-action buttons.
- Use raw screen coordinates as a normal operation.
- Run arbitrary JavaScript as a normal Claude-facing operation.
- Navigate away from the current page without explicit human approval.
- Dump all cookies, passwords, or sensitive browser storage by default.

### Operating rules

- Always call `browser_snapshot` before acting.
- Prefer refs returned by the latest snapshot.
- Do not invent selectors.
- Do not use coordinates.
- If a ref is missing or stale, take a new snapshot.
- Every mutating action must be logged.
- After filling, clicking, expanding, or uploading, take a screenshot.
- If a tool reports `blocked: true`, stop and report the reason.
- The human performs final submission manually.

### Code style

- Keep the implementation plain Python.
- Prefer synchronous code.
- Keep dependencies minimal.
- Do not introduce Playwright, Selenium, MCP, FastAPI, or a web server in the first implementation.
- Keep implementation in `chrome_tools.py` during branch `0.1`.
- Preserve existing `sim_test` classmethod style.
- Use four-space indentation.
- Avoid unnecessary try/except wrappers.
- Avoid over-engineering before the command surface is stable.

### Test expectations

Any new browser tool should have a `sim_test` that uses a local `data:` URL fixture page and verifies behaviour without needing external websites.

Tests must verify at least:

- snapshot returns controls and fields
- refs are assigned
- harmless click works
- dangerous click is blocked
- fill_ref updates input/textarea
- scroll_to_text works
- screenshot is saved
- action_log.jsonl is written
