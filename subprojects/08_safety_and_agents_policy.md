# 08 — Safety and AGENTS.md policy

Add this to `AGENTS.md` in the repo.

```markdown
# Chrome Tools Agent Policy

This repo provides human-supervised Chrome control through a narrow CDP-based tool layer.

## Goal

Grow `chrome_tools.py` into a safe, auditable, Claude-friendly browser-control layer over raw Chrome DevTools Protocol.

The tool should help an agent observe and interact with a visible browser page using structured refs, not raw selectors or coordinates.

## Allowed

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

## Not allowed

- Submit, finalize, complete, accept, or start tasks.
- Bypass login, captchas, timers, rate limits, or access controls.
- Mass scrape platform content.
- Hide actions from the human.
- Click destructive or final-action buttons.
- Use raw screen coordinates as a normal operation.
- Run arbitrary JavaScript as a normal Claude-facing operation.
- Navigate away from the current page without explicit human approval.
- Dump all cookies, passwords, or sensitive browser storage by default.

## Operating rules

- Always call `browser_snapshot` before acting.
- Prefer refs returned by the latest snapshot.
- Do not invent selectors.
- Do not use coordinates.
- If a ref is missing or stale, take a new snapshot.
- Every mutating action must be logged.
- After filling, clicking, expanding, or uploading, take a screenshot.
- If a tool reports `blocked: true`, stop and report the reason.
- The human performs final submission manually.

## Code style

- Keep the implementation plain Python.
- Prefer synchronous code.
- Keep dependencies minimal.
- Do not introduce Playwright, Selenium, MCP, FastAPI, or a web server in the first implementation.
- Keep implementation in `chrome_tools.py` during branch `0.1`.
- Preserve existing `sim_test` classmethod style.
- Use four-space indentation.
- Avoid unnecessary try/except wrappers.
- Avoid over-engineering before the command surface is stable.

## Test expectations

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
```
