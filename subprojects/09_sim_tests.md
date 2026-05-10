# 09 — Sim tests

The repo already uses `sim_test` classmethods. Continue that pattern.

## Test page fixture

Use a generated `data:` URL or local temporary HTML file.

The fixture should include:

```html
<h1>Chrome Tools Fixture</h1>

<button id="safe-button">Harmless button</button>
<button id="submit-button">Submit</button>

<label>
  GitHub URL
  <input id="repo-url" type="text" placeholder="Repository URL">
</label>

<label for="problem">Problem statement</label>
<textarea id="problem"></textarea>

<details>
  <summary>Part 3: Verifier creation</summary>
  <p>Verifier instructions inside collapsed section.</p>
</details>

<input id="upload" type="file" accept=".md">

<div style="height: 2000px"></div>
<p id="bottom-text">Bottom marker for scroll test</p>
```

## PageController.sim_test

Suggested assertions:

```text
Launch Chrome with delete_profile=True.
Connect CDPClient.
Attach PageController to first page.
Navigate to fixture.
Run snapshot.
Assert title/url/text present.
Assert safe button present.
Assert Submit button present and dangerous=true.
Assert input/textarea fields present.
Assert upload input present.
Click safe button and assert page changed.
Attempt click_ref on Submit and assert blocked.
Fill input.
Fill textarea.
Scroll to bottom marker.
Save screenshot.
Save state.
Check action_log.jsonl exists.
Close client and stop launcher.
```

## Test dangerous blocking

Expected:

```text
click_ref(submit_ref) raises/returns blocked
click_ref(submit_ref, allow_dangerous=True) is available only for developer tests, not normal CLI
```

Normal CLI should not expose `allow_dangerous=True` initially.

## Test stale refs

Expected:

```text
Take snapshot.
Navigate or rebuild snapshot.
Try using old ref.
Return stale_or_missing_ref.
```

This can be added after the first version.

## Test fill behaviour

For React-style input compatibility, use native setter and dispatch events.

Test should verify:

```text
element.value changed
input event count incremented
change event count incremented
```

## Test screenshots

Use `Page.captureScreenshot`.

Write to:

```text
browser_states/sim_test/screenshot.png
```

Assert file exists and size > 0.

## Test save_state

Should create:

```text
snapshot.json
visible_text.txt
screenshot.png
```

Assert all exist.

## Test console/errors later

Once console support exists, fixture can intentionally log:

```js
console.error("fixture error")
```

Then assert `browser_console` reports it.
