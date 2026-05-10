# 04 — Query tools specification

The query/read side should be richer than the action side. Claude should be able to ask what exists before acting.

## `browser_status`

Purpose:

```text
Check Chrome/CDP reachability and current attachment state.
```

Returns:

```json
{
  "ok": true,
  "chrome_running": true,
  "cdp_port": 9222,
  "attached": true,
  "current_url": "https://...",
  "title": "..."
}
```

## `browser_pages`

Purpose:

```text
List open page targets/tabs.
```

Returns:

```json
{
  "ok": true,
  "pages": [
    {
      "index": 0,
      "target_id": "...",
      "type": "page",
      "title": "Local App",
      "url": "http://localhost:5173/"
    }
  ]
}
```

## `browser_snapshot`

Purpose:

```text
Main query operation. Returns page metadata, visible text preview, and ref'd elements.
```

Returns:

```json
{
  "ok": true,
  "snapshot_id": "s42",
  "page": {
    "title": "Task page",
    "url": "https://example.com/task",
    "viewport": {
      "width": 1280,
      "height": 720,
      "scroll_x": 0,
      "scroll_y": 1840
    }
  },
  "text": {
    "visible_preview": "Part 2: Problem creation...",
    "full_length": 18392
  },
  "elements": [
    {
      "ref": "e1",
      "kind": "button",
      "tag": "BUTTON",
      "role": "button",
      "label": "Show instructions",
      "text": "Show instructions",
      "visible": true,
      "enabled": true,
      "dangerous": false
    }
  ],
  "warnings": []
}
```

## `browser_visible_text`

Purpose:

```text
Return page text for reading/instruction extraction.
```

Arguments:

```json
{
  "max_chars": 12000
}
```

Returns:

```json
{
  "ok": true,
  "url": "https://...",
  "visible_text": "..."
}
```

## `browser_find_text`

Purpose:

```text
Find text in the page and report whether it is visible or below/above viewport.
```

Arguments:

```json
{
  "text": "Verifier creation"
}
```

Returns:

```json
{
  "ok": true,
  "found": true,
  "matches": [
    {
      "text": "Part 3: Verifier creation",
      "visible": false,
      "approx_position": "below viewport"
    }
  ]
}
```

## `browser_list_controls`

Purpose:

```text
List clickable elements only.
```

Includes:

```text
button
a
summary
[role=button]
[aria-expanded]
tabs/menuitems where detectable
```

## `browser_list_fields`

Purpose:

```text
List editable fields.
```

Includes:

```text
input
textarea
select
contenteditable
```

Each field should include:

```text
ref
kind
tag
label
placeholder
name
id
type
value_preview
required
visible
enabled
```

## `browser_list_uploads`

Purpose:

```text
Find file upload controls.
```

Includes:

```text
input[type=file]
likely upload buttons
associated labels/buttons where detectable
accept
multiple
visible
```

## `browser_list_expandables`

Purpose:

```text
Find collapsed/expanded sections.
```

Includes:

```text
details/summary
[aria-expanded]
accordion buttons
disclosure controls
```

## `browser_active_element`

Purpose:

```text
Tell Claude what currently has focus.
```

Returns:

```json
{
  "ok": true,
  "active": {
    "ref": "e4",
    "tag": "TEXTAREA",
    "label": "Problem statement",
    "value_preview": "Implement a..."
  }
}
```

## `browser_screenshot`

Purpose:

```text
Save a screenshot and return path.
```

Returns:

```json
{
  "ok": true,
  "screenshot_path": "browser_states/current/screenshot.png"
}
```

## `browser_console`

Purpose:

```text
Return recent console logs/errors.
```

## `browser_runtime_errors`

Purpose:

```text
Return uncaught exceptions captured from Runtime.exceptionThrown.
```

## `browser_network_summary`

Purpose:

```text
Return recent network requests, statuses, and failures.
```

## `browser_save_state`

Purpose:

```text
Save snapshot, visible text, controls, screenshot, and metadata.
```

Returns:

```json
{
  "ok": true,
  "state_dir": "browser_states/2026-05-06_153012",
  "snapshot_path": "browser_states/2026-05-06_153012/snapshot.json",
  "screenshot_path": "browser_states/2026-05-06_153012/screenshot.png",
  "text_path": "browser_states/2026-05-06_153012/visible_text.txt"
}
```

## `browser_diff_last_snapshot`

Purpose:

```text
Show what changed after the last action.
```

Useful for:

```text
expand/collapse
file upload verification
field fill verification
page navigation detection
success/error message detection
```
