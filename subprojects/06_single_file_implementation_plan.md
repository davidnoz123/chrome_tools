# 06 — Single-file implementation plan

## Decision

For branch `0.1`, keep the implementation in a single file:

```text
chrome_tools.py
```

This matches the current repo shape and makes Claude's editing task easier.

Add classes below the existing CDP primitives:

```text
SafetyPolicy
ElementRefStore
ActionLogger
PageController
BrowserToolCLI
```

## Phase 1 — Read-only browser visibility

Implement:

```text
PageController.attach_to_first_page(client)
PageController.evaluate(expression, return_by_value=True)
PageController.observe_page()
PageController.visible_text()
PageController.list_controls()
PageController.list_fields()
PageController.list_uploads()
PageController.active_element()
PageController.screenshot(path)
PageController.save_state(output_dir)
```

CLI commands:

```bash
python chrome_tools.py status
python chrome_tools.py pages
python chrome_tools.py snapshot
python chrome_tools.py visible-text
python chrome_tools.py list-controls
python chrome_tools.py list-fields
python chrome_tools.py list-uploads
python chrome_tools.py active-element
python chrome_tools.py screenshot
python chrome_tools.py save-state
```

## Phase 2 — Safe ref actions

Implement:

```text
PageController.scroll_to_text(text)
PageController.scroll_ref_into_view(ref)
PageController.click_ref(ref, allow_dangerous=False)
PageController.focus_ref(ref)
PageController.fill_ref(ref, text)
PageController.paste_text(text)
```

CLI commands:

```bash
python chrome_tools.py scroll-to-text "..."
python chrome_tools.py scroll-ref e4
python chrome_tools.py click-ref e4
python chrome_tools.py focus-ref e7
python chrome_tools.py fill-ref e7 answer.md
python chrome_tools.py paste-text "..."
```

## Phase 3 — Uploads

Implement:

```text
PageController.upload_file_ref(ref, path)
```

CLI command:

```bash
python chrome_tools.py upload-file-ref e12 C:\path\problem_checker_results.md
```

## Phase 4 — Debugging support

Implement:

```text
Console.enable
Runtime.enable
Network.enable
capture console messages
capture runtime exceptions
capture network request/response/failures
browser_console
browser_runtime_errors
browser_network_summary
```

## Phase 5 — DataAnnotation workflow helpers

Add higher-level helpers that only orchestrate the safe low-level tools.

Possible helpers:

```text
da_observe_task
da_extract_visible_instructions
da_list_form_fields
da_save_task_state
da_prepare_upload_manifest
da_verify_before_manual_submit
```

Do not implement submit/finalize/accept/complete.

## Internal JavaScript strategy

The snapshot should use internal JavaScript through `Runtime.evaluate`.

It should scan:

```text
button
input
textarea
select
a
summary
details
[role=button]
[aria-expanded]
[contenteditable=true]
input[type=file]
```

For each element, collect:

```text
tag
role
id
name
type
text
label
placeholder
value_preview
aria_label
aria_expanded
disabled/enabled
visible
bounding box
dangerous
```

Assign an attribute:

```text
data-chrome-tools-ref="e1"
```

Refs are recreated on every snapshot.

## Important ref rule

A ref is valid only for the latest snapshot.

If Claude calls an action and the ref is missing, return:

```json
{
  "ok": false,
  "reason": "stale_or_missing_ref",
  "message": "Take a new snapshot and retry using the new refs."
}
```

## Internal fill strategy

For input/textarea:

```text
focus element
use native value setter
dispatch input event
dispatch change event
```

For contenteditable:

```text
focus element
set textContent or use document.execCommand as fallback
dispatch input event
```

## Internal click strategy

For click ref:

```text
resolve ref
check visible/enabled
check SafetyPolicy
scroll into view
element.click()
```

Do not use coordinates in first version.

## Screenshot strategy

Use:

```text
Page.captureScreenshot
```

Save PNG to:

```text
browser_states/YYYYMMDD_HHMMSS/screenshot.png
```

## Logging strategy

Append to:

```text
browser_states/action_log.jsonl
```

Include:

```text
timestamp
command
url
title
snapshot_id
ref
element label/text/kind
old value preview
new value preview
screenshot path
blocked/reason
```

## CLI implementation style

Use plain standard library argument parsing first.

Suggested:

```python
def main(argv=None) -> int:
    ...
```

Do not over-engineer with subcommand frameworks unless needed.

## Dependency policy

Keep dependencies minimal.

Current lazy dependencies through `versholn.install_and_import` are acceptable.

Do not add:

```text
Playwright
Selenium
MCP
FastAPI
web server
```

in this iteration.
