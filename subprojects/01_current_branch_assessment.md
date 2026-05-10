# 01 — Current branch assessment

Branch inspected: `0.1`

The branch currently appears to contain a single main implementation file:

```text
chrome_tools.py
```

The file already provides a useful raw-CDP foundation:

```text
ChromeLaunchConfig
ChromeLauncher
ChromeHealth
EventBus
CDPClient
CDPSession
_EventWaiter
_wait_for
```

## Existing strengths

### Chrome lifecycle

The current code can launch Chrome with:

```text
--remote-debugging-port=9222
--user-data-dir=...
--remote-allow-origins=*
--no-first-run
--no-default-browser-check
```

It can also adopt an already-running Chrome process by finding a TCP listener on the configured debug port.

### CDP connection

`CDPClient` connects to:

```text
http://localhost:9222/json/version
```

It reads `webSocketDebuggerUrl`, opens a WebSocket, sends CDP commands, receives replies, and dispatches browser/session events.

### Session support

`CDPSession` can attach to a page target using `Target.attachToTarget` with `flatten=True`, send session-scoped commands, subscribe to session events, and detach.

### Existing sim tests

The branch already uses `sim_test` classmethods. That style should be preserved.

Existing tests cover:

```text
Chrome launch/stop
Chrome adoption
CDP health/version check
Browser.getVersion
Target discovery event path
Runtime.evaluate
Page.navigate / Page.loadEventFired
CDPSession attach/detach
```

## What is missing

The current code does not yet expose Claude-friendly browser tools.

Missing pieces:

```text
PageController
SafetyPolicy
ElementRefStore
DOM/control snapshot
field/control/upload/expandable listing
safe click/fill/paste/upload operations
screenshot save helper
action_log.jsonl
console/runtime/network diagnostics
CLI command layer
DataAnnotation-specific workflow layer
```

## Main conclusion

The branch is in the right state for incremental growth.

Do not replace the existing raw-CDP foundation with Playwright/Selenium/MCP at this point. Instead, add a narrow, explicit browser-control layer on top.

The first implementation should still live in `chrome_tools.py` to match the current repo style. Split into multiple files later only after the API stabilizes.
