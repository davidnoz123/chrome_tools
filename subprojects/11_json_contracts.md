# 11 — JSON contracts

## Success response

```json
{
  "ok": true,
  "command": "snapshot",
  "message": "Snapshot captured.",
  "data": {},
  "warnings": []
}
```

## Blocked response

```json
{
  "ok": false,
  "blocked": true,
  "command": "click-ref",
  "reason": "dangerous_click",
  "message": "Blocked click on Submit. Manual user action required.",
  "data": {
    "ref": "e9",
    "label": "Submit"
  },
  "warnings": []
}
```

## Error response

```json
{
  "ok": false,
  "blocked": false,
  "command": "snapshot",
  "reason": "cdp_unavailable",
  "message": "Chrome CDP endpoint is not reachable on localhost:9222.",
  "data": {},
  "warnings": []
}
```

## Snapshot response data

```json
{
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
  "active": {
    "ref": "e4",
    "tag": "TEXTAREA",
    "label": "Problem statement",
    "value_preview": "..."
  },
  "elements": [
    {
      "ref": "e1",
      "kind": "button",
      "tag": "BUTTON",
      "role": "button",
      "label": "Show instructions",
      "text": "Show instructions",
      "id": "",
      "name": "",
      "type": "",
      "placeholder": "",
      "value_preview": "",
      "visible": true,
      "enabled": true,
      "aria_expanded": null,
      "dangerous": false
    }
  ],
  "controls": [],
  "fields": [],
  "uploads": [],
  "expandables": []
}
```

## Action log JSONL

```json
{"ts":"2026-05-06T15:30:12+12:00","action":"click_ref","url":"https://...","title":"Task page","ref":"e1","kind":"button","label":"Show instructions","blocked":false,"screenshot":"browser_states/20260506_153012/screenshot.png"}
{"ts":"2026-05-06T15:31:04+12:00","action":"fill_ref","url":"https://...","title":"Task page","ref":"e7","kind":"textarea","label":"Problem statement","old_value_preview":"","new_value_preview":"Implement a virtualized table...","blocked":false,"screenshot":"browser_states/20260506_153104/screenshot.png"}
```
