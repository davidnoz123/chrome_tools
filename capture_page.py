#!/usr/bin/env python3
"""Capture the current page in a CDP-attached Chrome instance.

import runpy ; temp = runpy._run_module_as_main("capture_page")

OPERATION controls what happens each run:
  "launch"   — connect to Chrome on PORT (or launch it), print URL, then wait
               for you to navigate to the page you want captured.
  "capture"  — connect to the already-running Chrome and call save_state(),
               writing screenshot.png + visible_text.txt + snapshot.json to
               OUTPUT_DIR.
"""

import pathlib
import sys

_log = lambda msg: print(msg, flush=True)


def safe_local_imports(g: dict) -> None:
    try:
        import sys as _sys
        import pathlib as _pathlib
        _here = _pathlib.Path(__file__).resolve().parent
        _sys.path.insert(0, str(_here))
        from chrome_tools import ChromeLaunchConfig, ChromeLauncher, CDPClient, PageController
        g["ChromeLaunchConfig"] = ChromeLaunchConfig
        g["ChromeLauncher"] = ChromeLauncher
        g["CDPClient"] = CDPClient
        g["PageController"] = PageController
    except Exception:
        import traceback as _tb
        _log(f"FATAL: safe_local_imports failed:\n{_tb.format_exc()}")
        raise


def main() -> int:
    OPERATION = "get_markdown"   # "launch" | "capture" | "navigate_and_capture" | "get_markdown"
    PORT      = 9222
    OUTPUT_DIR = "captured_page"
    NAVIGATE_URL = "https://chatgpt.com/c/6a0cb752-8484-83ec-8c9d-ad0bad176a06"

    if OPERATION == "launch":
        config = ChromeLaunchConfig(remote_debugging_port=PORT)
        launcher = ChromeLauncher(config)
        if launcher.adopt():
            _log(f"Adopted existing Chrome on port {PORT}")
        else:
            _log("Launching Chrome...")
            launcher.start()
            import time
            import urllib.request
            import urllib.error
            deadline = __import__("time").monotonic() + 20
            while True:
                try:
                    urllib.request.urlopen(
                        f"http://localhost:{PORT}/json/version", timeout=1
                    ).close()
                    break
                except Exception:
                    if __import__("time").monotonic() > deadline:
                        _log("FATAL: Chrome did not start in time")
                        return 1
                    __import__("time").sleep(0.5)
            _log(f"Chrome launched on port {PORT}")

        client = CDPClient(port=PORT)
        client.connect()
        pc = PageController.attach_to_first_page(client)
        snap = pc.observe_page()
        _log(f"Current URL  : {snap['page']['url']}")
        _log(f"Current title: {snap['page']['title']}")
        _log("")
        _log("Navigate to the page you want captured, then re-run with OPERATION = \"capture\"")
        client.close()
        return 0

    elif OPERATION == "capture":
        client = CDPClient(port=PORT)
        client.connect()
        pc = PageController.attach_to_first_page(client)
        snap = pc.observe_page()
        url   = snap["page"]["url"]
        title = snap["page"]["title"]
        _log(f"Capturing: {title}")
        _log(f"       at: {url}")
        out = pc.save_state(OUTPUT_DIR)
        _log(f"Saved to : {out}")
        client.close()
        return 0

    elif OPERATION == "navigate_and_capture":
        import time
        client = CDPClient(port=PORT)
        client.connect()
        pc = PageController.attach_to_first_page(client)
        _log(f"Navigating to {NAVIGATE_URL} ...")
        pc.session.send("Page.navigate", {"url": NAVIGATE_URL})
        # Wait for the page title to change away from "New Tab" / loading state
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            snap = pc.observe_page()
            title = snap["page"]["title"]
            url   = snap["page"]["url"]
            if NAVIGATE_URL.split("/c/")[1] in url and title not in ("", "New Tab"):
                break
            time.sleep(0.5)
        snap = pc.observe_page()
        _log(f"Page     : {snap['page']['title']}")
        _log(f"URL      : {snap['page']['url']}")
        # Extra settle time for React to finish rendering
        time.sleep(3)
        out = pc.save_state(OUTPUT_DIR)
        _log(f"Saved to : {out}")
        client.close()
        return 0

    else:
        _log(f"Unknown OPERATION: {OPERATION!r}")
        return 1


if __name__ == "__main__":
    safe_local_imports(globals())
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback
        _log(f"FATAL unhandled exception:\n{traceback.format_exc()}")
        raise
