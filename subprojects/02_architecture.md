# 02 — Architecture

## Target shape

```text
Claude / VS Code agent
    ↓
CLI commands / optional future MCP wrapper
    ↓
Claude-safe tool API
    ↓
PageController
    ↓
CDPSession / CDPClient
    ↓
Chrome DevTools Protocol
    ↓
Visible Chrome tab
```

## Guiding principle

Claude should see a browser page as a structured object:

```text
page metadata
visible text
fields
controls
uploads
expandables
active element
console/runtime errors
network summary
```

Claude should not see or directly use:

```text
Runtime.evaluate
DOM.querySelector
Input.dispatchMouseEvent
Page.navigate
arbitrary JavaScript
raw x/y coordinates
```

## Core object model

### SafetyPolicy

Responsible for deciding whether an operation is allowed.

Initial dangerous words:

```text
submit
complete
finish
finalize
accept
start task
delete
discard
leave page
```

Important methods:

```python
is_dangerous_text(text) -> bool
assert_safe_click(element, allow_dangerous=False) -> None
```

### ElementRefStore

Stores current snapshot elements by ref.

Example refs:

```text
e1
e2
e3
```

Rules:

```text
Refs are rebuilt on every snapshot.
Refs are only valid for the latest snapshot.
Action methods reject missing/stale refs.
Element records include enough information for logging and safety checks.
```

### PageController

High-level CDP wrapper.

Responsibilities:

```text
attach to selected page
enable Runtime/Page/DOM/Console/Network as needed
evaluate internal JavaScript
produce snapshots
resolve refs
perform guarded actions
save screenshots/state/logs
```

### BrowserToolService

Optional later wrapper around `PageController`.

This is the Claude-facing boundary. It turns CLI/MCP calls into PageController method calls and formats JSON responses.

For now, this can be a set of functions or a small command dispatcher in the same file.

## Why not expose CDP directly?

Raw CDP is too low-level and too powerful for agent use.

Bad Claude-facing interface:

```text
cdp_send Runtime.evaluate "document.querySelector(...).click()"
cdp_send Input.dispatchMouseEvent ...
```

Good Claude-facing interface:

```text
browser_snapshot
browser_click_ref e4
browser_fill_ref e7 answer.md
browser_upload_file_ref e12 problem_checker_results.md
```

## Single-file approach

For branch `0.1`, keep implementation in one file:

```text
chrome_tools.py
```

Add new classes near the bottom:

```text
SafetyPolicy
ElementRefStore
PageController
ActionLogger
BrowserToolCLI
```

This keeps the current repo simple and makes it easy for Claude to work in one place.

Later split if needed:

```text
chrome_tools/
    launcher.py
    cdp.py
    page_controller.py
    safety.py
    cli.py
```
