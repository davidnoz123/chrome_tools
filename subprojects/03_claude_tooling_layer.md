# 03 — Claude tooling layer

## Purpose

The Claude tooling layer is the command surface Claude uses from VS Code or another coding-agent environment.

It should be:

```text
small
JSON-based
safe by default
auditable
ref-based
independent of Playwright/Selenium/MCP
```

## Initial interface style

Use a simple CLI first.

Example commands:

```bash
python chrome_tools.py status
python chrome_tools.py pages
python chrome_tools.py attach-first
python chrome_tools.py snapshot
python chrome_tools.py visible-text
python chrome_tools.py list-controls
python chrome_tools.py list-fields
python chrome_tools.py list-uploads
python chrome_tools.py screenshot
python chrome_tools.py scroll-to-text "Verifier creation"
python chrome_tools.py click-ref e4
python chrome_tools.py focus-ref e7
python chrome_tools.py fill-ref e7 answer.md
python chrome_tools.py paste-text "short text"
python chrome_tools.py upload-file-ref e12 C:\path\problem_checker_results.md
python chrome_tools.py save-state
```

The CLI should print JSON to stdout.

## Why CLI first?

Claude in VS Code can reliably run terminal commands and read files.

A CLI avoids:

```text
MCP setup friction
extension-specific behaviour
hidden browser automation layers
new dependency stacks
```

MCP can come later as a thin wrapper around the same service functions.

## Tool response contract

All commands should return JSON with the same top-level shape:

```json
{
  "ok": true,
  "command": "snapshot",
  "message": "...",
  "data": {},
  "warnings": []
}
```

For blocked actions:

```json
{
  "ok": false,
  "blocked": true,
  "command": "click-ref",
  "reason": "Dangerous click text",
  "message": "Blocked click on Submit. Manual user action required.",
  "data": {
    "ref": "e9",
    "label": "Submit"
  }
}
```

For failures:

```json
{
  "ok": false,
  "blocked": false,
  "command": "snapshot",
  "reason": "Chrome CDP endpoint not reachable",
  "message": "Start Chrome with remote debugging enabled.",
  "data": {}
}
```

## Claude operating loop

Claude should follow this loop:

```text
1. status
2. pages
3. snapshot
4. reason from visible text and element refs
5. ask user or act with ref-based tools
6. save_state after meaningful changes
7. snapshot again
8. explain what changed
```

## Tool safety rules for Claude

Claude must:

```text
Call snapshot before acting.
Use refs returned by the latest snapshot.
Never invent CSS selectors.
Never use coordinates.
Never ask for raw CDP unless the human explicitly switches to developer debugging.
Stop when a tool returns blocked=true.
Never submit/finalize/accept/complete a task.
```

## Future MCP wrapper

Later, map the same commands to MCP tools:

```text
browser.status
browser.pages
browser.snapshot
browser.visible_text
browser.list_controls
browser.list_fields
browser.click_ref
browser.fill_ref
browser.upload_file_ref
browser.save_state
```

The implementation should remain shared. CLI and MCP should be wrappers only.
