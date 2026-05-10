# 10 — Ready-to-paste Claude prompt

Paste this into Claude Code or your VS Code agent while on branch `0.1`.

```text
We are continuing the `chrome_tools` repo on branch `0.1`.

Current state:
- The repo currently has `chrome_tools.py`.
- It already contains ChromeLaunchConfig, ChromeLauncher, ChromeHealth, EventBus, CDPClient, CDPSession, _EventWaiter, _wait_for, and sim_test methods.
- It uses raw Chrome DevTools Protocol over websocket.
- It uses lazy dependencies through `versholn.install_and_import`.
- Do not introduce Playwright, Selenium, MCP, FastAPI, or a web server in this iteration.

Goal:
Grow `chrome_tools.py` into a narrow, safe, Claude-friendly browser-control layer over CDP.

Important design rule:
Claude must not use raw CDP directly. Add a structured PageController and a CLI-style command layer that exposes safe browser operations using element refs.

Keep implementation in a single file for now:
- Add new code to `chrome_tools.py`.
- Preserve the current style: plain Python, synchronous, simple classes, classmethod sim_test methods, minimal dependencies.
- Use four-space indentation.
- Do not over-engineer.

Implement these classes:

1. SafetyPolicy
   - dangerous words:
     - submit
     - complete
     - finish
     - finalize
     - accept
     - start task
     - delete
     - discard
     - leave page
   - method `is_dangerous_text(text: str) -> bool`
   - method `assert_safe_click(element: dict, allow_dangerous: bool = False) -> None`

2. ElementRefStore
   - Rebuilt on every snapshot.
   - Assign refs like e1, e2, e3.
   - Refs are valid only for the current snapshot.
   - Store element records by ref.
   - Each element record should include:
     - ref
     - kind
     - tag
     - role
     - text
     - label
     - id
     - name
     - type
     - placeholder
     - value_preview
     - visible
     - enabled
     - aria_expanded
     - dangerous

3. ActionLogger
   - Append JSON lines to `browser_states/action_log.jsonl`.
   - Log timestamp, action, URL, title, ref, element summary, old value preview, new value preview, screenshot path, blocked/reason where applicable.

4. PageController
   - wraps a CDPSession.
   - methods:
     - attach_to_first_page(client)
     - evaluate(expression, return_by_value=True)
     - observe_page()
     - visible_text()
     - list_controls()
     - list_fields()
     - list_uploads()
     - list_expandables()
     - active_element()
     - screenshot(path)
     - save_state(output_dir=None)
     - scroll_to_text(text)
     - scroll_ref_into_view(ref)
     - click_ref(ref, allow_dangerous=False)
     - focus_ref(ref)
     - fill_ref(ref, text)
     - paste_text(text)
   - Use `Runtime.evaluate` internally.
   - Use `Page.captureScreenshot` for screenshots.
   - Do not use x/y coordinates.
   - Do not expose arbitrary JavaScript as a normal command.

Snapshot implementation:
- Inject JavaScript via Runtime.evaluate.
- Scan visible and relevant elements:
  - button
  - input
  - textarea
  - select
  - a
  - summary
  - details
  - [role=button]
  - [aria-expanded]
  - [contenteditable=true]
  - input[type=file]
- Assign each element a DOM attribute like `data-chrome-tools-ref="e1"`.
- Return page title, URL, viewport, visible text preview, active element, and categorized elements.
- Categorize elements as controls, fields, uploads, expandables where possible.

Action implementation:
- click_ref:
  - resolve ref
  - reject missing/stale refs
  - check SafetyPolicy
  - scroll into view
  - click internally with element.click()
  - log action
  - screenshot after action
- fill_ref:
  - resolve ref
  - focus element
  - set value using native setter for input/textarea
  - dispatch input and change events
  - support contenteditable if straightforward
  - log old/new previews
  - screenshot after action
- paste_text:
  - insert into current active element
  - log and screenshot
- scroll_to_text:
  - find text node containing the requested text
  - scroll parent element into view
  - return found true/false

Add a simple CLI in the same file:
- `python chrome_tools.py status`
- `python chrome_tools.py pages`
- `python chrome_tools.py snapshot`
- `python chrome_tools.py visible-text`
- `python chrome_tools.py list-controls`
- `python chrome_tools.py list-fields`
- `python chrome_tools.py list-uploads`
- `python chrome_tools.py active-element`
- `python chrome_tools.py screenshot`
- `python chrome_tools.py save-state`
- `python chrome_tools.py scroll-to-text "..."`
- `python chrome_tools.py click-ref e4`
- `python chrome_tools.py focus-ref e7`
- `python chrome_tools.py fill-ref e7 answer.md`
- `python chrome_tools.py paste-text "..."`
- `python chrome_tools.py upload-file-ref e12 C:\path\problem_checker_results.md` may be stubbed or left for the next iteration if file upload is too fiddly.

CLI output:
- Always print JSON.
- Use top-level keys:
  - ok
  - command
  - message
  - data
  - warnings
  - blocked when applicable
  - reason when applicable

Add PageController.sim_test:
- Launch Chrome with delete_profile=True.
- Connect CDPClient.
- Attach PageController to first page.
- Navigate to a data: URL fixture page containing:
  - heading
  - harmless button
  - fake Submit button
  - input
  - textarea
  - details/summary collapsible section
  - file input
  - enough vertical space to test scrolling
  - bottom marker text
- Assert snapshot sees controls and fields.
- Assert Submit is marked dangerous.
- Click harmless button and assert page changed.
- Try clicking Submit and assert it is blocked.
- Fill input and textarea.
- Scroll to bottom marker.
- Save screenshot.
- Save state.
- Stop Chrome.

Safety:
- Do not implement final submission automation.
- Do not implement accept/start/complete task automation.
- Do not bypass login, captcha, timers, rate limits, or access controls.
- Do not use coordinates except as an explicitly disabled future debug fallback.

Also add/update AGENTS.md with the Chrome Tools Agent Policy:
- Claude must snapshot before acting.
- Claude must use refs from latest snapshot.
- Claude must not invent selectors.
- Claude must not use coordinates.
- Mutating actions must be logged.
- Final submission is manual.
```
