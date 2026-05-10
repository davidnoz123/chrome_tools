# 05 — Action tools specification

Actions must be fewer and more heavily guarded than query tools.

## General rules

All mutating actions must:

```text
Require a valid ref from the latest snapshot where applicable.
Reject stale/missing refs.
Log action to action_log.jsonl.
Record page URL and element description.
For fields, log old value preview and new value preview.
Take a screenshot after the action.
Return structured JSON.
```

## `browser_scroll_to_text`

Purpose:

```text
Scroll page or nearest scrollable container to text.
```

Input:

```json
{
  "text": "Verifier creation"
}
```

Output:

```json
{
  "ok": true,
  "found": true,
  "message": "Scrolled to text."
}
```

## `browser_scroll_ref_into_view`

Purpose:

```text
Scroll an element ref into view.
```

## `browser_click_ref`

Purpose:

```text
Click a safe clickable element by ref.
```

Rules:

```text
Use ref only.
No selectors supplied by Claude.
No x/y coordinates.
Block dangerous labels by default.
```

Blocked example:

```json
{
  "ok": false,
  "blocked": true,
  "reason": "Dangerous click text",
  "message": "Blocked click on Submit. Manual user action required.",
  "data": {
    "ref": "e9",
    "label": "Submit"
  }
}
```

## `browser_expand_ref`

Purpose:

```text
Expand a collapsible section if it is collapsed.
```

Should be implemented as a wrapper around click/ref only when the element is known to be expandable.

## `browser_collapse_ref`

Purpose:

```text
Collapse a collapsible section if it is expanded.
```

## `browser_focus_ref`

Purpose:

```text
Focus a field/control by ref.
```

## `browser_fill_ref`

Purpose:

```text
Set field value by ref.
```

Recommended implementation:

```text
Use JavaScript internally.
Use native value setter for input/textarea.
Dispatch input and change events with bubbles=true.
Support contenteditable.
```

Do not expose arbitrary JavaScript to Claude.

## `browser_paste_text`

Purpose:

```text
Paste/insert text into currently focused field.
```

Safer for short text. For large answers, prefer:

```text
browser_fill_ref e7 answer.md
```

## `browser_upload_file_ref`

Purpose:

```text
Upload a specific file to a file input ref.
```

Rules:

```text
File path must be explicit.
Path must exist.
Ref must identify input[type=file] or a known associated upload control.
After upload, take screenshot and snapshot.
Return uploaded file name/path.
```

## `browser_clear_ref`

Optional, not in first version.

If implemented:

```text
Require allow_clear=true.
Log old value preview.
Reject if field value length is large unless explicit override.
```

## Actions not to expose

Do not expose these to Claude:

```text
submit_form
accept_task
complete_task
finalize_task
start_task
solve_captcha
bypass_login
click_coordinates
run_arbitrary_js
navigate_url
dump_all_cookies
```

Keep developer-only debug commands separate and disabled by default.
