# 07 — DataAnnotation direction

## Purpose

The DataAnnotation use-case is a human-supervised assistant workflow, not an autonomous task bot.

The browser tooling should help with:

```text
reading task instructions
finding hidden sections
saving task state
extracting form field labels
pasting human-reviewed answers
uploading explicitly identified files
checking for visible errors
confirming page state before manual submission
```

It should not perform final submission or bypass platform controls.

## Safe DA workflow

A typical workflow should be:

```text
1. Human opens the task page in Chrome.
2. Human starts Chrome with remote debugging profile or uses the prepared debug profile.
3. Claude runs browser_status and browser_pages.
4. Claude attaches to the task page.
5. Claude runs browser_snapshot and browser_save_state.
6. Claude reads visible instructions and identifies expandable sections.
7. Claude scrolls/expands sections as needed.
8. Claude extracts form fields and upload controls.
9. Claude prepares local Markdown answers/files.
10. Human reviews the generated answer text.
11. Claude fills fields by ref.
12. Claude uploads explicit files by ref/path.
13. Claude saves screenshot/state.
14. Claude reports what fields appear filled and what files appear uploaded.
15. Human performs final submit manually.
```

## DA-specific helper commands

These helpers can be built after the generic browser tools are stable.

### `da_save_task_snapshot`

Saves:

```text
visible text
full text where available
controls
fields
uploads
screenshots
current URL
timestamp
```

### `da_extract_requirements`

Best-effort extraction from visible text and expanded sections.

Output:

```text
task parts
required files
required GitHub URL/SHA fields
required verifier/checker artifacts
warnings about hidden/collapsed sections
```

### `da_list_submission_fields`

Lists likely submission fields:

```text
GitHub repo URL
commit SHA
problem statement
difficulty explanation
checker results upload
verifier notes
```

This should still use generic field refs from the snapshot.

### `da_prepare_field_plan`

Outputs a proposed mapping:

```text
field ref e12 -> repo URL
field ref e13 -> commit SHA
field ref e14 -> problem statement
upload ref e20 -> problem_checker_results.md
```

Claude should show this to the human before filling.

### `da_verify_before_manual_submit`

Read-only check.

Reports:

```text
visible required fields
non-empty status
visible uploaded filenames
visible warnings/errors
current URL/title
screenshot path
```

It must not click Submit.

## DA actions that must remain manual

The following must not be implemented as automated tools:

```text
Accept task
Start timed task
Submit task
Complete task
Finalize task
Confirm final submission
Bypass login
Bypass captcha
Evade rate limits
Mass scrape platform content
```

## Audit trail for DA use

For each DA session, create:

```text
da_sessions/YYYYMMDD_HHMMSS/
    initial_snapshot.json
    initial_screenshot.png
    visible_text.txt
    action_log.jsonl
    field_plan.json
    final_pre_submit_snapshot.json
    final_pre_submit_screenshot.png
```

This is useful for:

```text
recovering from mistakes
checking what was submitted
documenting the human-reviewed workflow
debugging Claude/tool behaviour
```

## Framing

This tool is for:

```text
browser visibility
human-supervised drafting
form-entry assistance
workflow reliability
auditability
```

It is not for:

```text
end-to-end task automation
circumventing platform rules
silent or undisclosed auto-completion
```

## Disclosure and policy

Where task/platform rules require disclosure of AI/tool use, follow those rules.

Do not design features whose purpose is to hide automation or misrepresent who performed work.

The assistant should help the human comply with task instructions, not bypass them.
