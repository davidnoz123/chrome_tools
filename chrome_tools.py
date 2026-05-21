
r"""

C:\analytics\projects\git\lexi\demos\venv\Scripts\python.exe

import runpy ; temp = runpy._run_module_as_main("chrome_tools") 



"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-allow-origins=* --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\ChromeDebugProfile"

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-allow-origins=* --remote-debugging-port=9222 --user-data-dir="C:\Users\david\AppData\Local\Google\Chrome\User Data"

"""

import base64
import contextlib
import datetime
import json
import os
import sys
import pathlib
import shutil
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, field


def _get_versholn():
    """Load versholn without a module-level import (stdlib-safe bootstrap)."""
    import sys
    try:
        import versholn as _v
    except ImportError:
        import pathlib
        here = pathlib.Path(__file__).resolve()
        for parent in here.parents:
            candidate = parent / "versholn"
            if candidate.is_dir():
                sys.path.insert(0, str(candidate))
                break
        import versholn as _v
    return _v


def _log(msg: str) -> None:
    print(msg, flush=True)


@dataclass
class ChromeLaunchConfig:
    executable: str = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    remote_debugging_port: int = 9222
    user_data_dir: str = r"C:\Temp\chrome_debug_profile"
    headless: bool = False
    delete_profile: bool = False  # wipe user_data_dir before launch for a fresh session
    extra_args: list[str] = field(default_factory=list)


class ChromeLauncher:
    def __init__(self, config: ChromeLaunchConfig) -> None:
        self.config = config
        self.proc: subprocess.Popen | None = None
        self._adopted_proc = None

    def build_args(self) -> list[str]:
        args = [
            self.config.executable,
            f"--remote-debugging-port={self.config.remote_debugging_port}",
            f"--user-data-dir={self.config.user_data_dir}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        if self.config.headless:
            args.append("--headless=new")
        args.extend(self.config.extra_args)
        return args

    def start(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            return  # already running
        if self.config.delete_profile:
            import os
            p = self.config.user_data_dir
            if os.path.exists(p):
                shutil.rmtree(p, ignore_errors=True)
        self.proc = subprocess.Popen(
            self.build_args(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def adopt(self) -> bool:
        """Attach to an existing Chrome process listening on the configured port."""
        psutil = _get_versholn().install_and_import("psutil")
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr.port == self.config.remote_debugging_port and conn.status == "LISTEN" and conn.pid:
                try:
                    self._adopted_proc = psutil.Process(conn.pid)
                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        return False

    def stop(self) -> None:
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None
        elif self._adopted_proc is not None:
            self._adopted_proc.terminate()
            self._adopted_proc.wait(timeout=5)
            self._adopted_proc = None

    def status(self) -> str:
        if self.proc is not None:
            if self.proc.poll() is None:
                return "running"
            return "exited"
        if self._adopted_proc is not None:
            if self._adopted_proc.is_running():
                return "running"
            return "exited"
        return "stopped"

    @classmethod
    def sim_test_a(cls) -> None:
        """Tests build_args, status, headless flag, and live launch/stop."""
        config = ChromeLaunchConfig()
        launcher = cls(config)

        args = launcher.build_args()
        assert args[0] == config.executable, "executable must be first arg"
        assert any(f"--remote-debugging-port={config.remote_debugging_port}" == a for a in args)
        assert any(f"--user-data-dir={config.user_data_dir}" == a for a in args)
        assert launcher.status() == "stopped"

        # headless flag only appears when enabled
        config_hl = ChromeLaunchConfig(headless=True)
        args_hl = cls(config_hl).build_args()
        assert "--headless=new" in args_hl

        config_no_hl = ChromeLaunchConfig(headless=False)
        args_no_hl = cls(config_no_hl).build_args()
        assert "--headless=new" not in args_no_hl

        # live launch / stop
        launcher2 = cls(ChromeLaunchConfig())
        assert launcher2.status() == "stopped"
        launcher2.start()
        time.sleep(1)
        assert launcher2.status() == "running", f"expected running, got {launcher2.status()}"
        print(f"  Chrome pid={launcher2.proc.pid} running")
        launcher2.stop()
        assert launcher2.status() == "stopped"
        print("  Chrome stopped cleanly")

        print("ChromeLauncher.sim_test_a passed")

    @classmethod
    def sim_test_b(cls) -> None:
        """Tests adopt(): attach to an already-running Chrome and stop it via the adopted proc."""
        config = ChromeLaunchConfig()

        # launch Chrome externally (simulates an already-running instance)
        launcher_a = cls(config)
        launcher_a.start()
        time.sleep(1)

        # a second launcher with no proc adopts the running one
        launcher_b = cls(config)
        assert launcher_b.status() == "stopped", "should be stopped before adopt"
        adopted = launcher_b.adopt()
        assert adopted, "adopt() should find the running Chrome"
        assert launcher_b.status() == "running", f"expected running after adopt, got {launcher_b.status()}"
        print("  adopt(): status=running (correct)")

        launcher_b.stop()
        assert launcher_b.status() == "stopped", "expected stopped after stop()"
        print("  adopt(): stopped cleanly via adopted proc")

        print("ChromeLauncher.sim_test_b passed")

    @classmethod
    def sim_test(cls) -> None:
        cls.sim_test_a()
        cls.sim_test_b()
        print("ChromeLauncher.sim_test passed")


@contextlib.contextmanager
def chrome_session(config: ChromeLaunchConfig | None = None):
    """Context manager: launch Chrome, connect CDPClient, yield (launcher, client), then clean up.

    Usage::

        with chrome_session() as (launcher, client):
            result = client.send("Browser.getVersion")
    """
    cfg = config or ChromeLaunchConfig()
    launcher = ChromeLauncher(cfg)
    launcher.start()
    time.sleep(1)
    client = CDPClient(host="localhost", port=cfg.remote_debugging_port)
    client.connect()
    try:
        yield launcher, client
    finally:
        client.close()
        launcher.stop()


class ChromeHealth:
    """Probes the CDP HTTP endpoint to detect any Chrome with remote debugging active."""

    def __init__(self, host: str = "localhost", port: int = 9222) -> None:
        self._host = host
        self._port = port

    def is_alive(self) -> bool:
        try:
            url = f"http://{self._host}:{self._port}/json/version"
            with urllib.request.urlopen(url, timeout=2):
                return True
        except Exception:
            return False

    def version_info(self) -> dict | None:
        try:
            url = f"http://{self._host}:{self._port}/json/version"
            with urllib.request.urlopen(url, timeout=2) as resp:
                return json.loads(resp.read())
        except Exception:
            return None

    def verify_running_instance(self, config: "ChromeLaunchConfig") -> bool:
        """Return True if the Chrome listening on port was launched with matching port and user-data-dir."""
        psutil = _get_versholn().install_and_import("psutil")
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr.port == self._port and conn.status == "LISTEN" and conn.pid:
                try:
                    cmdline = psutil.Process(conn.pid).cmdline()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return False
                has_port = any(
                    f"--remote-debugging-port={config.remote_debugging_port}" in a
                    for a in cmdline
                )
                has_udd = any(
                    f"--user-data-dir={config.user_data_dir}" in a
                    for a in cmdline
                )
                return has_port and has_udd
        return False

    @classmethod
    def sim_test(cls) -> None:
        config = ChromeLaunchConfig()
        launcher = ChromeLauncher(config)
        health = cls()

        assert not health.is_alive(), "expected no Chrome before launch"
        print("  before start: not alive (correct)")

        launcher.start()
        time.sleep(1)

        assert health.is_alive(), "expected Chrome alive after start"
        print("  after start:  alive (correct)")

        info = health.version_info()
        assert info is not None, "version_info must return a dict"
        assert "Browser" in info, f"expected 'Browser' key, got: {list(info.keys())}"
        print(f"  version_info: {info['Browser']}")

        assert health.verify_running_instance(config), "cmdline mismatch â€” wrong Chrome instance"
        print("  verify_running_instance: matched port and user-data-dir")

        wrong_config = ChromeLaunchConfig(user_data_dir=r"C:\Temp\wrong_profile")
        assert not health.verify_running_instance(wrong_config), "expected mismatch for wrong config"
        print("  verify_running_instance: correctly rejected wrong config")

        launcher.stop()

        assert not health.is_alive(), "expected Chrome gone after stop"
        print("  after stop:   not alive (correct)")

        print("ChromeHealth.sim_test passed")




class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}

    def subscribe(self, event: str, callback) -> None:
        self._handlers.setdefault(event, []).append(callback)

    def unsubscribe(self, event: str, callback) -> None:
        try:
            self._handlers.get(event, []).remove(callback)
        except ValueError:
            pass

    def dispatch(self, event: str, params: dict) -> None:
        for cb in self._handlers.get(event, []):
            cb(params)


def cdp_evaluate(ws_url: str, js: str, timeout: int = 15) -> str:
    """Evaluate *js* in the tab identified by *ws_url* and return the string result.

    Uses a raw WebSocketApp connection — no CDPClient/CDPSession setup required.
    Ideal for one-shot reads where you already have the webSocketDebuggerUrl from
    the CDP HTTP /json endpoint.

    Returns the raw string value from Runtime.evaluate, or '' on timeout/error.

    Example::

        import urllib.request, json
        targets = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
        page = next(t for t in targets if t.get('type') == 'page')
        html = cdp_evaluate(page['webSocketDebuggerUrl'], 'document.documentElement.outerHTML')
    """
    websocket = _get_versholn().install_and_import("websocket-client", import_as="websocket")
    results: dict = {}
    done = threading.Event()

    def _on_message(ws, msg):
        d = json.loads(msg)
        if d.get("id") == 1:
            results["value"] = d.get("result", {}).get("result", {}).get("value", "")
            done.set()

    def _on_open(ws):
        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": js, "returnByValue": True},
        }))

    wsa = websocket.WebSocketApp(ws_url, on_message=_on_message, on_open=_on_open)
    t = threading.Thread(target=wsa.run_forever, daemon=True)
    t.start()
    done.wait(timeout=timeout)
    wsa.close()
    return results.get("value", "")


class CDPClient:
    def __init__(self, host: str = "localhost", port: int = 9222) -> None:
        self._host = host
        self._port = port
        self.ws = None
        self.event_bus = EventBus()
        self.sessions: dict[str, "CDPSession"] = {}
        self._next_id = 1
        self._pending: dict[int, dict] = {}
        self._send_lock = threading.Lock()
        self._recv_thread: threading.Thread | None = None
        self.closed = threading.Event()  # set when WebSocket connection drops

    def connect(self) -> None:
        url = f"http://{self._host}:{self._port}/json/version"
        with urllib.request.urlopen(url, timeout=5) as resp:
            info = json.loads(resp.read())
        ws_url = info["webSocketDebuggerUrl"]
        websocket = _get_versholn().install_and_import("websocket-client", import_as="websocket")
        self.ws = websocket.WebSocket()
        self.ws.connect(ws_url)
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def close(self) -> None:
        if self.ws:
            if not self.closed.is_set():
                try:
                    self.ws.close()
                except Exception:
                    pass
            self.ws = None

    def send(self, method: str, params: dict | None = None, session_id: str | None = None) -> dict:
        with self._send_lock:
            cmd_id = self._next_id
            self._next_id += 1
            evt = threading.Event()
            self._pending[cmd_id] = {"event": evt, "result": None, "error": None}

        msg: dict = {"id": cmd_id, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        try:
            self.ws.send(json.dumps(msg))
        except Exception:
            self._pending.pop(cmd_id, None)
            raise RuntimeError("connection closed")

        self._pending[cmd_id]["event"].wait(timeout=10)
        entry = self._pending.pop(cmd_id, {})
        if entry.get("error"):
            raise RuntimeError(f"CDP error: {entry['error']}")
        return entry.get("result") or {}

    def subscribe(self, event: str, callback) -> None:
        self.event_bus.subscribe(event, callback)

    def _recv_loop(self) -> None:
        while True:
            try:
                raw = self.ws.recv()
            except Exception as exc:
                print(f"  CDPClient: recv_loop exiting: {exc}")
                break
            if not raw:
                break
            msg = json.loads(raw)
            if "id" in msg:
                cmd_id = msg["id"]
                entry = self._pending.get(cmd_id)
                if entry:
                    entry["result"] = msg.get("result", {})
                    entry["error"] = msg.get("error")
                    entry["event"].set()
            elif "method" in msg:
                session_id = msg.get("sessionId")
                if session_id and session_id in self.sessions:
                    self.sessions[session_id]._dispatch(msg["method"], msg.get("params", {}))
                else:
                    self.event_bus.dispatch(msg["method"], msg.get("params", {}))
        # Wake any commands still waiting so they fail immediately rather than timing out.
        self.closed.set()
        for entry in list(self._pending.values()):
            entry["error"] = {"code": -1, "message": "WebSocket closed"}
            entry["event"].set()

    @classmethod
    def sim_test(cls) -> None:
        with chrome_session(ChromeLaunchConfig(delete_profile=True)) as (_, client):
            # Browser.getVersion via browser-level send
            result = client.send("Browser.getVersion")
            print(f"  Browser product: {result.get('product')}")
            assert result.get("product"), "Browser.getVersion must return product"

            # browser-level event subscription
            received = []
            client.subscribe("Target.targetCreated", lambda p: received.append(p))
            client.send("Target.setDiscoverTargets", {"discover": True})
            time.sleep(0.3)
            print(f"  targetCreated events received: {len(received)}")

            # CDP error path
            try:
                client.send("ThisMethod.DoesNotExist")
                assert False, "expected RuntimeError for unknown method"
            except RuntimeError as e:
                print(f"  error path: caught expected error: {e}")

            # CDPSession basic tests
            CDPSession.sim_test(client)

        print("CDPClient.sim_test passed")


def _wait_for(
    evt: threading.Event,
    timeout: float,
    *,
    abort: threading.Event | None = None,
    interval: float = 0.3,
) -> None:
    """Block until evt is set, checking abort every interval seconds.

    Raises RuntimeError('connection closed') if abort fires.
    Raises TimeoutError if the full timeout elapses without evt being set.
    """
    deadline = time.monotonic() + timeout
    while True:
        if abort and abort.is_set():
            raise RuntimeError("connection closed")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"event did not fire within {timeout:.0f}s")
        if evt.wait(timeout=min(interval, remaining)):
            return


class _EventWaiter:
    """Blocks until a session event matching an optional predicate fires."""

    def __init__(self, session: "CDPSession", event: str, predicate=None,
                 abort: threading.Event | None = None) -> None:
        self._evt = threading.Event()
        self._payload: dict | None = None
        self._predicate = predicate
        self._abort = abort

        self._session = session
        self._event   = event

        def _cb(params: dict) -> None:
            if self._predicate is None or self._predicate(params):
                if not self._evt.is_set():          # capture first match only
                    self._payload = params
                    self._evt.set()

        self._cb = _cb
        session.on_event(event, _cb)

    def wait(self, timeout: float = 10.0) -> dict:
        _wait_for(self._evt, timeout, abort=self._abort)
        self._session.off_event(self._event, self._cb)  # clean up immediately
        return self._payload

    def reset(self) -> None:
        self._evt.clear()
        self._payload = None


class CDPSession:
    def __init__(self, client: CDPClient) -> None:
        self.client = client  # back-reference, not owned
        self._session_id: str | None = None
        self._event_bus = EventBus()

    def attach(self, target_id: str) -> None:
        result = self.client.send(
            "Target.attachToTarget", {"targetId": target_id, "flatten": True}
        )
        self._session_id = result["sessionId"]
        self.client.sessions[self._session_id] = self

    def detach(self) -> None:
        if self._session_id:
            self.client.send(
                "Target.detachFromTarget", {"sessionId": self._session_id}
            )
            self.client.sessions.pop(self._session_id, None)
            self._session_id = None

    def send(self, method: str, params: dict | None = None) -> dict:
        return self.client.send(method, params, session_id=self._session_id)

    def on_event(self, event: str, callback) -> None:
        self._event_bus.subscribe(event, callback)

    def off_event(self, event: str, callback) -> None:
        self._event_bus.unsubscribe(event, callback)

    def _dispatch(self, event: str, params: dict) -> None:
        self._event_bus.dispatch(event, params)

    @classmethod
    def sim_test(cls, client: "CDPClient") -> None:
        """Tests attach, session-scoped send, on_event dispatch, and detach."""
        # find the first available page target
        result = client.send("Target.getTargets")
        targets = result.get("targetInfos", [])
        page = next((t for t in targets if t["type"] == "page"), None)
        assert page is not None, "no page target found to attach to"
        target_id = page["targetId"]
        print(f"  CDPSession: attaching to target {target_id[:16]}...")

        session = cls(client)
        session.attach(target_id)
        assert session._session_id is not None, "session_id must be set after attach"
        assert session._session_id in client.sessions, "session must be registered in client"
        print(f"  CDPSession: attached, session_id={session._session_id[:16]}...")

        # session-scoped send: evaluate JS in the page
        eval_result = session.send("Runtime.evaluate", {"expression": "1 + 1"})
        value = eval_result.get("result", {}).get("value")
        assert value == 2, f"expected 2 from Runtime.evaluate, got {value}"
        print(f"  CDPSession: Runtime.evaluate 1+1 = {value} (correct)")

        # on_event: subscribe to Page.loadEventFired, trigger a navigation
        load_events = []
        session.on_event("Page.loadEventFired", lambda p: load_events.append(p))
        session.send("Page.enable")
        session.send("Page.navigate", {"url": "about:blank"})
        time.sleep(0.5)
        assert len(load_events) > 0, "expected Page.loadEventFired after navigation"
        print(f"  CDPSession: Page.loadEventFired received ({len(load_events)} event(s))")

        # detach
        session.detach()
        assert session._session_id is None, "session_id must be None after detach"
        print("  CDPSession: detached cleanly")

        print("CDPSession.sim_test passed")


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

_DANGEROUS_WORDS = (
    "submit", "complete", "finish", "finalize", "accept",
    "start task", "delete", "discard", "leave page",
)


class BlockedActionError(Exception):
    pass


class SafetyPolicy:
    def is_dangerous_text(self, text: str) -> bool:
        t = text.lower()
        return any(w in t for w in _DANGEROUS_WORDS)

    def assert_safe_click(self, element: dict, allow_dangerous: bool = False) -> None:
        if element.get("dangerous") and not allow_dangerous:
            label = element.get("label") or element.get("text") or element.get("ref")
            raise BlockedActionError(f"Dangerous click text: {label!r}")


# ---------------------------------------------------------------------------
# Element ref store
# ---------------------------------------------------------------------------

class StaleRefError(Exception):
    def __init__(self, ref: str) -> None:
        super().__init__(f"Ref {ref!r} not in current snapshot — take a new snapshot and retry.")
        self.ref = ref


class ElementRefStore:
    def __init__(self) -> None:
        self._refs: dict[str, dict] = {}

    def rebuild(self, elements: list[dict]) -> None:
        self._refs = {e["ref"]: e for e in elements}

    def get(self, ref: str) -> dict | None:
        return self._refs.get(ref)

    def require(self, ref: str) -> dict:
        el = self._refs.get(ref)
        if el is None:
            raise StaleRefError(ref)
        return el

    def all(self) -> list[dict]:
        return list(self._refs.values())


# ---------------------------------------------------------------------------
# Action logger
# ---------------------------------------------------------------------------

class ActionLogger:
    def __init__(self, log_path: str = "browser_states/action_log.jsonl") -> None:
        self._path = pathlib.Path(log_path)

    def log(self, entry: dict) -> None:
        entry.setdefault("ts", datetime.datetime.now().astimezone().isoformat())
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# DOM snapshot JavaScript
# ---------------------------------------------------------------------------

_SNAPSHOT_JS = r"""
(function () {
    document.querySelectorAll('[data-chrome-tools-ref]').forEach(function (el) {
        el.removeAttribute('data-chrome-tools-ref');
    });

    var sel = [
        'button', 'input', 'textarea', 'select', 'a[href]',
        'summary', 'details', '[role="button"]', '[aria-expanded]',
        '[contenteditable="true"]', 'input[type="file"]'
    ].join(',');

    var seen = new Set();
    var elements = Array.from(document.querySelectorAll(sel)).filter(function (el) {
        if (seen.has(el)) return false;
        seen.add(el);
        return true;
    });

    var dangerousWords = [
        'submit', 'complete', 'finish', 'finalize', 'accept',
        'start task', 'delete', 'discard', 'leave page'
    ];

    function getText(el) {
        return (el.innerText || el.textContent || '').trim().slice(0, 200);
    }

    function getLabel(el) {
        var al = el.getAttribute('aria-label');
        if (al) return al.trim();
        var lby = el.getAttribute('aria-labelledby');
        if (lby) {
            var lel = document.getElementById(lby);
            if (lel) return lel.innerText.trim();
        }
        if (el.id) {
            var lfor = document.querySelector('label[for="' + el.id + '"]');
            if (lfor) return lfor.innerText.trim();
        }
        var parent = el.closest('label');
        if (parent) {
            var clone = parent.cloneNode(true);
            clone.querySelectorAll('input,textarea,select,button').forEach(function (i) { i.remove(); });
            return clone.innerText.trim();
        }
        if (el.placeholder) return el.placeholder;
        if (el.title) return el.title;
        return getText(el);
    }

    function isVisible(el) {
        var rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return false;
        var st = window.getComputedStyle(el);
        if (st.display === 'none' || st.visibility === 'hidden' || parseFloat(st.opacity) === 0) return false;
        return true;
    }

    function getKind(el) {
        var tag = el.tagName;
        var type = (el.type || '').toLowerCase();
        var role = (el.getAttribute('role') || '').toLowerCase();
        if (tag === 'INPUT' && type === 'file') return 'upload';
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return 'field';
        if (el.hasAttribute('contenteditable') && el.getAttribute('contenteditable') !== 'false') return 'field';
        if (tag === 'BUTTON' || role === 'button') return 'button';
        if (tag === 'A') return 'link';
        if (tag === 'SUMMARY' || tag === 'DETAILS') return 'expandable';
        if (el.hasAttribute('aria-expanded')) return 'expandable';
        return 'control';
    }

    function isDangerous(el, label) {
        var t = (label + ' ' + getText(el)).toLowerCase();
        return dangerousWords.some(function (w) { return t.indexOf(w) !== -1; });
    }

    var records = [];
    var refNum = 1;

    elements.forEach(function (el) {
        var ref = 'e' + refNum++;
        el.setAttribute('data-chrome-tools-ref', ref);
        var rect = el.getBoundingClientRect();
        var tag = el.tagName;
        var kind = getKind(el);
        var label = getLabel(el);
        var vp = '';
        if (el.value !== undefined) {
            vp = String(el.value).slice(0, 100);
        } else if (kind === 'field') {
            vp = (el.textContent || '').slice(0, 100);
        }
        records.push({
            ref: ref,
            kind: kind,
            tag: tag,
            role: el.getAttribute('role') || '',
            id: el.id || '',
            name: el.name || '',
            type: (el.type || '').toLowerCase(),
            label: label,
            text: getText(el),
            placeholder: el.placeholder || '',
            value_preview: vp,
            aria_label: el.getAttribute('aria-label') || '',
            aria_expanded: el.getAttribute('aria-expanded'),
            visible: isVisible(el),
            enabled: !el.disabled,
            dangerous: isDangerous(el, label),
            rect: {x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)}
        });
    });

    return records;
})()
"""


# ---------------------------------------------------------------------------
# PageController — Phase 1: read-only browser visibility
# ---------------------------------------------------------------------------

class PageController:
    def __init__(self, session: CDPSession, logger: ActionLogger | None = None) -> None:
        self.session = session
        self.safety = SafetyPolicy()
        self.refs = ElementRefStore()
        self.logger = logger or ActionLogger()
        self._snapshot_counter = 0

    @classmethod
    def attach_to_first_page(cls, client: CDPClient, logger: ActionLogger | None = None) -> "PageController":
        result = client.send("Target.getTargets")
        targets = result.get("targetInfos", [])
        page = next((t for t in targets if t["type"] == "page"), None)
        if page is None:
            raise RuntimeError("No page targets found")
        session = CDPSession(client)
        session.attach(page["targetId"])
        session.send("Runtime.enable")
        return cls(session, logger)

    def evaluate(self, expression: str) -> object:
        result = self.session.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
        })
        exc = result.get("exceptionDetails")
        if exc:
            desc = exc.get("exception", {}).get("description", str(exc))
            raise RuntimeError(f"JS exception: {desc}")
        return result.get("result", {}).get("value")

    def _page_meta(self) -> dict:
        return {
            "title": self.evaluate("document.title"),
            "url": self.evaluate("document.location.href"),
            "viewport": {
                "width": self.evaluate("window.innerWidth"),
                "height": self.evaluate("window.innerHeight"),
                "scroll_x": self.evaluate("Math.round(window.scrollX)"),
                "scroll_y": self.evaluate("Math.round(window.scrollY)"),
            },
        }

    def _run_snapshot_js(self) -> list[dict]:
        result = self.session.send("Runtime.evaluate", {
            "expression": _SNAPSHOT_JS,
            "returnByValue": True,
        })
        exc = result.get("exceptionDetails")
        if exc:
            desc = exc.get("exception", {}).get("description", str(exc))
            raise RuntimeError(f"Snapshot JS exception: {desc}")
        return result.get("result", {}).get("value") or []

    def observe_page(self) -> dict:
        self._snapshot_counter += 1
        snapshot_id = f"s{self._snapshot_counter}"
        page = self._page_meta()
        elements = self._run_snapshot_js()
        self.refs.rebuild(elements)

        visible_preview = self.evaluate(
            "(function(){var t=document.body?document.body.innerText:'';return t.slice(0,200);})()"
        )
        full_length = self.evaluate(
            "(function(){var t=document.body?document.body.innerText:'';return t.length;})()"
        )
        active_ref = self.evaluate(
            "(function(){var el=document.activeElement;"
            "return el?el.getAttribute('data-chrome-tools-ref'):null;})()"
        )
        active = self.refs.get(active_ref) if active_ref else None

        controls = [e for e in elements if e["kind"] in ("button", "link", "control")]
        fields = [e for e in elements if e["kind"] == "field"]
        uploads = [e for e in elements if e["kind"] == "upload"]
        expandables = [e for e in elements if e["kind"] == "expandable"]

        return {
            "snapshot_id": snapshot_id,
            "page": page,
            "text": {"visible_preview": visible_preview, "full_length": full_length},
            "active": active,
            "elements": elements,
            "controls": controls,
            "fields": fields,
            "uploads": uploads,
            "expandables": expandables,
        }

    def visible_text(self, max_chars: int = 12000) -> dict:
        url = self.evaluate("document.location.href")
        text = self.evaluate(
            f"(function(){{var t=document.body?document.body.innerText:'';"
            f"return t.slice(0,{max_chars});}})()"
        )
        return {"url": url, "visible_text": text}

    def list_controls(self) -> list[dict]:
        return [e for e in self.refs.all() if e["kind"] in ("button", "link", "control")]

    def list_fields(self) -> list[dict]:
        return [e for e in self.refs.all() if e["kind"] == "field"]

    def list_uploads(self) -> list[dict]:
        return [e for e in self.refs.all() if e["kind"] == "upload"]

    def list_expandables(self) -> list[dict]:
        return [e for e in self.refs.all() if e["kind"] == "expandable"]

    def active_element(self) -> dict | None:
        active_ref = self.evaluate(
            "(function(){var el=document.activeElement;"
            "return el?el.getAttribute('data-chrome-tools-ref'):null;})()"
        )
        return self.refs.get(active_ref) if active_ref else None

    def screenshot(self, path: str | None = None) -> str:
        result = self.session.send("Page.captureScreenshot", {"format": "png"})
        data = result.get("data", "")
        if path is None:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"screenshot_{ts}.png"
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(base64.b64decode(data))
        return str(p)

    def save_state(self, output_dir: str | None = None) -> str:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_dir is None:
            output_dir = str(pathlib.Path("browser_states") / ts)
        d = pathlib.Path(output_dir)
        d.mkdir(parents=True, exist_ok=True)
        snap = self.observe_page()
        (d / "snapshot.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
        vt = self.visible_text(max_chars=50000)
        (d / "visible_text.txt").write_text(vt["visible_text"], encoding="utf-8")
        self.screenshot(str(d / "screenshot.png"))
        return str(d)

    # ------------------------------------------------------------------
    # Phase 2: safe ref actions
    # ------------------------------------------------------------------

    def scroll_to_text(self, text: str) -> dict:
        """Find text in the page and scroll it into view. Returns {found: bool}."""
        expr = (
            "(function(needle) {"
            "  function walk(node) {"
            "    if (node.nodeType === 3) {"
            "      if (node.nodeValue && node.nodeValue.indexOf(needle) !== -1) {"
            "        var p = node.parentElement;"
            "        if (p) { p.scrollIntoView({block:'center',behavior:'instant'}); return p; }"
            "      }"
            "    }"
            "    for (var i=0; i<node.childNodes.length; i++) {"
            "      var r = walk(node.childNodes[i]);"
            "      if (r) return r;"
            "    }"
            "    return null;"
            "  }"
            "  var found = walk(document.body);"
            "  return found ? true : false;"
            "})(" + json.dumps(text) + ")"
        )
        found = self.evaluate(expr)
        self.logger.log({"action": "scroll_to_text", "text": text, "found": found})
        return {"found": bool(found)}

    def scroll_ref_into_view(self, ref: str) -> None:
        """Scroll element ref into view."""
        self.refs.require(ref)
        self.evaluate(
            f"(function(){{"
            f"  var el = document.querySelector('[data-chrome-tools-ref={json.dumps(ref)}]');"
            f"  if (el) el.scrollIntoView({{block:'center',behavior:'instant'}});"
            f"}})()"
        )
        self.logger.log({"action": "scroll_ref_into_view", "ref": ref})

    def click_ref(self, ref: str, allow_dangerous: bool = False) -> dict:
        """Click element by ref. Blocked if element is dangerous (unless allow_dangerous=True)."""
        element = self.refs.require(ref)
        try:
            self.safety.assert_safe_click(element, allow_dangerous=allow_dangerous)
        except BlockedActionError as exc:
            entry = {
                "action": "click_ref", "ref": ref,
                "element": {k: element.get(k) for k in ("ref", "kind", "label", "text", "dangerous")},
                "blocked": True, "reason": str(exc),
            }
            self.logger.log(entry)
            return {"blocked": True, "reason": str(exc)}
        self.scroll_ref_into_view(ref)
        self.evaluate(
            f"(function(){{"
            f"  var el = document.querySelector('[data-chrome-tools-ref={json.dumps(ref)}]');"
            f"  if (el) el.click();"
            f"}})()"
        )
        url = self.evaluate("document.location.href")
        title = self.evaluate("document.title")
        scr_path = self.screenshot()
        entry = {
            "action": "click_ref", "ref": ref,
            "element": {k: element.get(k) for k in ("ref", "kind", "label", "text", "dangerous")},
            "url": url, "title": title, "screenshot": scr_path,
        }
        self.logger.log(entry)
        return {"ok": True, "screenshot": scr_path}

    def focus_ref(self, ref: str) -> None:
        """Focus element by ref."""
        self.refs.require(ref)
        self.evaluate(
            f"(function(){{"
            f"  var el = document.querySelector('[data-chrome-tools-ref={json.dumps(ref)}]');"
            f"  if (el) el.focus();"
            f"}})()"
        )
        self.logger.log({"action": "focus_ref", "ref": ref})

    def fill_ref(self, ref: str, text: str) -> dict:
        """Fill field by ref. If text ends in a known extension, read file contents instead."""
        element = self.refs.require(ref)
        fill_value = text
        # treat as file path if it looks like one
        known_text_exts = (".md", ".txt", ".rst", ".csv", ".json", ".html", ".xml")
        if any(text.lower().endswith(ext) for ext in known_text_exts):
            p = pathlib.Path(text)
            if p.exists():
                fill_value = p.read_text(encoding="utf-8")

        old_preview = element.get("value_preview", "")
        new_preview = fill_value[:100]

        # React-compatible native setter + dispatch input + change events
        js = (
            "(function(ref, val) {"
            "  var el = document.querySelector('[data-chrome-tools-ref=' + JSON.stringify(ref) + ']');"
            "  if (!el) return false;"
            "  if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {"
            "    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');"
            "    var nativeTextAreaSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');"
            "    var setter = el.tagName === 'TEXTAREA' ? (nativeTextAreaSetter && nativeTextAreaSetter.set) : (nativeInputValueSetter && nativeInputValueSetter.set);"
            "    if (setter) { setter.call(el, val); }"
            "    else { el.value = val; }"
            "  } else if (el.isContentEditable) {"
            "    el.textContent = val;"
            "  } else {"
            "    el.value = val;"
            "  }"
            "  el.dispatchEvent(new Event('input', {bubbles: true}));"
            "  el.dispatchEvent(new Event('change', {bubbles: true}));"
            "  return true;"
            "})(" + json.dumps(ref) + ", " + json.dumps(fill_value) + ")"
        )
        ok = self.evaluate(js)
        url = self.evaluate("document.location.href")
        title = self.evaluate("document.title")
        scr_path = self.screenshot()
        entry = {
            "action": "fill_ref", "ref": ref,
            "element": {k: element.get(k) for k in ("ref", "kind", "label", "type")},
            "old_value_preview": old_preview, "new_value_preview": new_preview,
            "url": url, "title": title, "screenshot": scr_path,
        }
        self.logger.log(entry)
        return {"ok": bool(ok), "screenshot": scr_path}

    def paste_text(self, text: str) -> dict:
        """Insert text into the currently active/focused element."""
        js = (
            "(function(val) {"
            "  var el = document.activeElement;"
            "  if (!el) return false;"
            "  if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {"
            "    var start = el.selectionStart; var end = el.selectionEnd;"
            "    var old = el.value;"
            "    el.value = old.slice(0, start) + val + old.slice(end);"
            "    el.selectionStart = el.selectionEnd = start + val.length;"
            "  } else if (el.isContentEditable) {"
            "    document.execCommand('insertText', false, val);"
            "  } else { return false; }"
            "  el.dispatchEvent(new Event('input', {bubbles: true}));"
            "  el.dispatchEvent(new Event('change', {bubbles: true}));"
            "  return true;"
            "})(" + json.dumps(text) + ")"
        )
        ok = self.evaluate(js)
        url = self.evaluate("document.location.href")
        scr_path = self.screenshot()
        self.logger.log({"action": "paste_text", "text_preview": text[:100], "url": url, "screenshot": scr_path})
        return {"ok": bool(ok), "screenshot": scr_path}

    # ------------------------------------------------------------------
    # Phase 3: file upload
    # ------------------------------------------------------------------

    def upload_file_ref(self, ref: str, path: str) -> dict:
        """Upload a file to a file input ref using CDP DOM.setFileInputFiles."""
        element = self.refs.require(ref)
        if element.get("kind") != "upload":
            raise ValueError(f"Ref {ref!r} is not a file input (kind={element.get('kind')!r})")
        p = pathlib.Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Upload file not found: {path!r}")
        abs_path = str(p.resolve())
        # Resolve DOM node id
        expr = (
            "document.querySelector('[data-chrome-tools-ref=' + JSON.stringify("
            + json.dumps(ref) + ") + ']')"
        )
        node_result = self.session.send("DOM.getDocument", {"depth": 0})
        root_id = node_result.get("root", {}).get("nodeId")
        search_result = self.session.send("DOM.querySelector", {
            "nodeId": root_id,
            "selector": f"[data-chrome-tools-ref={json.dumps(ref)}]",
        })
        node_id = search_result.get("nodeId")
        if not node_id:
            raise RuntimeError(f"Could not resolve DOM node for ref {ref!r}")
        self.session.send("DOM.setFileInputFiles", {
            "files": [abs_path],
            "nodeId": node_id,
        })
        snap = self.observe_page()
        scr_path = self.screenshot()
        url = snap["page"]["url"]
        title = snap["page"]["title"]
        entry = {
            "action": "upload_file_ref", "ref": ref,
            "element": {k: element.get(k) for k in ("ref", "kind", "label")},
            "file": abs_path, "url": url, "title": title, "screenshot": scr_path,
        }
        self.logger.log(entry)
        return {"ok": True, "file": abs_path, "screenshot": scr_path}

    @classmethod
    def sim_test(cls) -> None:
        fixture_html = """<!DOCTYPE html>
<html><body>
<h1>Chrome Tools Fixture</h1>
<button id="safe-button" onclick="document.getElementById('click-result').textContent='clicked'">Harmless button</button>
<p id="click-result"></p>
<button id="submit-button">Submit</button>
<label>GitHub URL<input id="repo-url" type="text" placeholder="Repository URL"></label>
<label for="problem">Problem statement</label>
<textarea id="problem"></textarea>
<details><summary>Part 3: Verifier creation</summary>
<p>Verifier instructions inside collapsed section.</p></details>
<input id="upload" type="file" accept=".md">
<div style="height:2000px"></div>
<p id="bottom-text">Bottom marker for scroll test</p>
</body></html>"""
        fixture_b64 = base64.b64encode(fixture_html.encode()).decode()
        fixture_url = f"data:text/html;base64,{fixture_b64}"

        with chrome_session(ChromeLaunchConfig(delete_profile=True)) as (_, client):
            pc = cls.attach_to_first_page(client)
            waiter = _EventWaiter(pc.session, "Page.loadEventFired")
            pc.session.send("Page.enable")
            pc.session.send("Page.navigate", {"url": fixture_url})
            waiter.wait(timeout=5)
            time.sleep(0.3)

            snap = pc.observe_page()
            assert snap["page"]["url"].startswith("data:"), f"unexpected url: {snap['page']['url']}"
            assert snap["text"]["full_length"] > 0, "expected non-empty page text"

            refs_by_text = {e["text"]: e for e in snap["elements"]}

            safe_btn = refs_by_text.get("Harmless button")
            assert safe_btn is not None, "safe button not found"
            assert not safe_btn["dangerous"], "safe button should not be dangerous"
            print(f"  safe button ref={safe_btn['ref']} dangerous={safe_btn['dangerous']} (correct)")

            submit_btn = refs_by_text.get("Submit")
            assert submit_btn is not None, "submit button not found"
            assert submit_btn["dangerous"], "submit button should be dangerous"
            print(f"  submit button ref={submit_btn['ref']} dangerous={submit_btn['dangerous']} (correct)")

            fields = pc.list_fields()
            assert len(fields) >= 2, f"expected at least 2 fields, got {len(fields)}"
            print(f"  fields: {[f['label'] for f in fields]}")

            uploads = pc.list_uploads()
            assert len(uploads) >= 1, f"expected at least 1 upload input, got {len(uploads)}"
            print(f"  uploads: {len(uploads)} (correct)")

            expandables = snap["expandables"]
            assert len(expandables) >= 1, f"expected at least 1 expandable, got {len(expandables)}"
            print(f"  expandables: {len(expandables)} (correct)")

            vt = pc.visible_text()
            assert "Chrome Tools Fixture" in vt["visible_text"], "fixture heading not in visible text"
            print(f"  visible_text length={len(vt['visible_text'])}")

            # Expandables (list_expandables)
            exp = pc.list_expandables()
            assert len(exp) >= 1, f"expected at least 1 expandable, got {len(exp)}"
            print(f"  list_expandables: {len(exp)} (correct)")

            import tempfile, os as _os
            with tempfile.TemporaryDirectory() as tmp:
                # Use ActionLogger pointing into tmp
                pc.logger = ActionLogger(str(pathlib.Path(tmp) / "action_log.jsonl"))

                saved = pc.save_state(tmp)
                assert _os.path.exists(_os.path.join(saved, "snapshot.json")), "snapshot.json missing"
                assert _os.path.exists(_os.path.join(saved, "screenshot.png")), "screenshot.png missing"
                assert _os.path.exists(_os.path.join(saved, "visible_text.txt")), "visible_text.txt missing"
                print(f"  save_state: {saved} (snapshot.json, screenshot.png, visible_text.txt present)")

                # Re-snapshot so refs are fresh
                pc.observe_page()

                # click harmless button
                safe_ref = next(e["ref"] for e in pc.refs.all() if e.get("text") == "Harmless button")
                result = pc.click_ref(safe_ref)
                assert result.get("ok"), f"harmless click failed: {result}"
                time.sleep(0.2)
                click_result_text = pc.evaluate("document.getElementById('click-result').textContent")
                assert click_result_text == "clicked", f"harmless button onclick did not fire, got: {click_result_text!r}"
                print(f"  click_ref (harmless): ok, onclick fired (correct)")

                # blocked Submit click
                submit_ref = next(e["ref"] for e in pc.refs.all() if e.get("text") == "Submit")
                blocked = pc.click_ref(submit_ref)
                assert blocked.get("blocked"), f"expected blocked for Submit, got: {blocked}"
                print(f"  click_ref (Submit): blocked={blocked['blocked']} reason={blocked['reason']!r} (correct)")

                # fill input
                pc.observe_page()
                input_ref = next(e["ref"] for e in pc.refs.all() if e.get("id") == "repo-url" or (e.get("kind") == "field" and e.get("type") == "text"))
                fill_result = pc.fill_ref(input_ref, "https://example.com/repo")
                assert fill_result.get("ok"), f"fill_ref failed: {fill_result}"
                val = pc.evaluate("document.getElementById('repo-url').value")
                assert val == "https://example.com/repo", f"fill_ref value mismatch: {val!r}"
                print(f"  fill_ref (input): ok, value={val!r} (correct)")

                # fill textarea
                ta_ref = next(e["ref"] for e in pc.refs.all() if e.get("tag") == "TEXTAREA")
                fill_ta = pc.fill_ref(ta_ref, "Problem text here.")
                assert fill_ta.get("ok"), f"fill_ref textarea failed: {fill_ta}"
                ta_val = pc.evaluate("document.getElementById('problem').value")
                assert ta_val == "Problem text here.", f"textarea fill mismatch: {ta_val!r}"
                print(f"  fill_ref (textarea): ok, value={ta_val!r} (correct)")

                # scroll_to_text
                scroll_result = pc.scroll_to_text("Bottom marker for scroll test")
                assert scroll_result["found"], "scroll_to_text should find bottom marker"
                print(f"  scroll_to_text: found={scroll_result['found']} (correct)")

                missing_scroll = pc.scroll_to_text("__text_that_does_not_exist_xyz__")
                assert not missing_scroll["found"], "scroll_to_text should not find missing text"
                print(f"  scroll_to_text (missing): found={missing_scroll['found']} (correct)")

                # action_log.jsonl written
                log_path = _os.path.join(tmp, "action_log.jsonl")
                assert _os.path.exists(log_path), f"action_log.jsonl not found at {log_path}"
                with open(log_path, encoding="utf-8") as f:
                    lines = [l for l in f if l.strip()]
                assert len(lines) >= 4, f"expected at least 4 log entries, got {len(lines)}"
                actions = [json.loads(l)["action"] for l in lines]
                print(f"  action_log.jsonl: {len(lines)} entries, actions={actions}")

        print("PageController.sim_test passed")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_PAGE_SNAPSHOT_JS = r"""(function(includeHidden) {
  "use strict";
  var lines = [], hiddenN = 0;
  var SKIP = {SCRIPT:1,STYLE:1,NOSCRIPT:1,SVG:1,CANVAS:1,IFRAME:1,HEAD:1,META:1,LINK:1,OBJECT:1,EMBED:1};
  var INLINE = {SPAN:1,STRONG:1,B:1,EM:1,I:1,SMALL:1,SUP:1,SUB:1,MARK:1,ABBR:1,CITE:1,
                S:1,DEL:1,INS:1,U:1,TIME:1,KBD:1,SAMP:1,VAR:1,BDI:1,BDO:1,WBR:1,LABEL:1};
  function isHid(el) {
    try { var s = window.getComputedStyle(el);
      if (s.display === 'none' || s.visibility === 'hidden') return true;
    } catch(e) {}
    if (el.hidden) return true;
    if (el.getAttribute('aria-hidden') === 'true') return true;
    return false;
  }
  function desc(el) {
    var d = el.tagName.toLowerCase();
    if (el.id) d += '#' + el.id;
    else if (el.className && typeof el.className === 'string') {
      var c = el.className.trim().split(/\s+/).slice(0,2).join('.');
      if (c) d += '.' + c;
    }
    var r = el.getAttribute ? el.getAttribute('role') : null;
    if (r) d += '[role="' + r + '"]';
    return d;
  }
  function getlbl(el) {
    if (el.id) { var lb = document.querySelector('label[for="' + el.id + '"]');
      if (lb) return lb.textContent.trim(); }
    var a = el.getAttribute ? el.getAttribute('aria-label') : null;
    if (a) return a.trim();
    var lid = el.getAttribute ? el.getAttribute('aria-labelledby') : null;
    if (lid) { var le = document.getElementById(lid); if (le) return le.textContent.trim(); }
    return '';
  }
  function gettxt(el, h) {
    try { return h ? (el.textContent||'').trim() : (el.innerText||'').trim(); } catch(e) { return ''; }
  }
  function extractLinks(el, pfx, h) {
    var as = el.querySelectorAll('a[href]');
    for (var i = 0; i < as.length; i++) {
      var a = as[i], t = gettxt(a, h), href = a.href || '';
      if (t && href && href.indexOf('javascript:') !== 0)
        lines.push(pfx + '\u2192 [' + t + '](' + href + ')');
    }
  }
  function blank() { if (lines.length && lines[lines.length-1] !== '') lines.push(''); }
  function walk(node, h) {
    if (!node) return;
    if (node.nodeType === 3) {
      var t = (node.textContent||'').trim();
      if (t) lines.push((h ? '> ' : '') + t);
      return;
    }
    if (node.nodeType !== 1) return;
    var tag = node.tagName;
    if (!tag || SKIP[tag]) return;
    if (INLINE[tag]) {
      for (var i = 0; i < node.childNodes.length; i++) walk(node.childNodes[i], h);
      return;
    }
    var hid = isHid(node);
    if (hid && !includeHidden) return;
    if (hid && !h) {
      hiddenN++;
      var n = hiddenN;
      blank();
      lines.push('<!-- hidden-block:' + n + ' ' + desc(node) + ' -->');
      for (var i = 0; i < node.childNodes.length; i++) walk(node.childNodes[i], true);
      lines.push('<!-- /hidden-block:' + n + ' -->');
      blank();
      return;
    }
    var p = h ? '> ' : '';
    if (/^H[1-6]$/.test(tag)) {
      var t = gettxt(node, h);
      if (t) lines.push(p + Array(parseInt(tag[1])+1).join('#') + ' ' + t);
      extractLinks(node, p, h); return;
    }
    if (tag === 'P') {
      var t = gettxt(node, h);
      if (t) { lines.push(p + t); extractLinks(node, p, h); blank(); } return;
    }
    if (tag === 'A') {
      var t = gettxt(node, h), href = node.href || '';
      if (t && href && href.indexOf('javascript:') !== 0) lines.push(p + '[' + t + '](' + href + ')');
      else if (t) lines.push(p + t);
      return;
    }
    if (tag === 'UL' || tag === 'OL') {
      var ord = tag === 'OL', idx = 0;
      for (var i = 0; i < node.children.length; i++) {
        var li = node.children[i];
        if (li.tagName === 'LI') {
          idx++;
          var t = gettxt(li, h);
          if (t) lines.push(p + (ord ? idx + '. ' : '- ') + t);
          extractLinks(li, p + '  ', h);
        }
      }
      blank(); return;
    }
    if (tag === 'LI') {
      var t = gettxt(node, h);
      if (t) lines.push(p + '- ' + t);
      extractLinks(node, p + '  ', h); return;
    }
    if (tag === 'INPUT') {
      var type = (node.type || 'text').toLowerCase(), lb = getlbl(node);
      if (type === 'checkbox') { lines.push(p + (node.checked ? '[x]' : '[ ]') + (lb ? ' ' + lb : '')); return; }
      if (type === 'radio') { lines.push(p + (node.checked ? '(\u2022)' : '( )') + (lb ? ' ' + lb : '')); return; }
      if (type === 'hidden') return;
      if (type === 'submit' || type === 'button') { lines.push(p + '**[Button: ' + (node.value || lb || type) + ']**'); return; }
      var val = (node.value || '').trim(), ph = node.placeholder || '';
      lines.push(p + '[Input' + (lb ? ':' + lb : '') + (val ? '="' + val + '"' : (ph ? ' placeholder="' + ph + '"' : '')) + ']');
      return;
    }
    if (tag === 'TEXTAREA') {
      var lb = getlbl(node), val = (node.value || '').trim();
      lines.push(p + '[Textarea' + (lb ? ':' + lb : '') + (val ? '="' + val + '"' : '') + ']'); return;
    }
    if (tag === 'SELECT') {
      var lb = getlbl(node), sel = node.options && node.selectedIndex >= 0 ? node.options[node.selectedIndex] : null;
      lines.push(p + '[Select' + (lb ? ':' + lb : '') + (sel ? '="' + sel.text.trim() + '"' : '') + ']'); return;
    }
    if (tag === 'BUTTON') {
      var t = gettxt(node, h); if (t) lines.push(p + '**[Button: ' + t + ']**'); return;
    }
    if (tag === 'IMG') {
      var alt = node.alt || ''; if (alt) lines.push(p + '[Image: ' + alt + ']'); return;
    }
    if (tag === 'TABLE') {
      var rows = node.querySelectorAll('tr'), first = true;
      rows.forEach(function(row) {
        var cells = row.querySelectorAll('td,th');
        if (!cells.length) return;
        var parts = [];
        cells.forEach(function(c) { parts.push(gettxt(c, h).replace(/\|/g, '\\|').replace(/\n/g, ' ')); });
        lines.push(p + '| ' + parts.join(' | ') + ' |');
        if (first) { lines.push(p + '|' + parts.map(function(){return ' --- ';}).join('|') + '|'); first = false; }
      });
      blank(); return;
    }
    if (tag === 'PRE') {
      var t = (node.textContent||'').trim();
      if (t) { lines.push(p + '```'); lines.push(t); lines.push(p + '```'); blank(); } return;
    }
    if (tag === 'CODE') {
      var t = gettxt(node, h); if (t) lines.push(p + '`' + t + '`'); return;
    }
    if (tag === 'BLOCKQUOTE') {
      var t = gettxt(node, h);
      if (t) t.split('\n').forEach(function(l) { lines.push(p + '> ' + l.trim()); });
      blank(); return;
    }
    if (tag === 'HR') { lines.push(p + '---'); return; }
    if (tag === 'BR') { blank(); return; }
    if (tag === 'SUMMARY') { var t = gettxt(node, h); if (t) lines.push(p + '**' + t + '**'); return; }
    for (var i = 0; i < node.childNodes.length; i++) walk(node.childNodes[i], h);
    if (tag==='DIV'||tag==='SECTION'||tag==='ARTICLE'||tag==='MAIN'||tag==='ASIDE'||
        tag==='HEADER'||tag==='FOOTER'||tag==='NAV'||tag==='FORM'||tag==='FIELDSET'||
        tag==='FIGURE'||tag==='DETAILS') blank();
  }
  if (!document.body) return '';
  walk(document.body, false);
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
})"""


class BrowserToolCLI:
    def __init__(self, host: str = "localhost", port: int = 9222,
                 target_id: str | None = None,
                 client: "CDPClient | None" = None) -> None:
        self._host = host
        self._port = port
        self._target_id = target_id
        self._client = client  # pre-connected persistent client (REPL mode); not closed after each command

    def _ok(self, command: str, data: dict | None = None, message: str = "") -> dict:
        return {"ok": True, "command": command, "message": message, "data": data or {}, "warnings": []}

    def _err(self, command: str, reason: str, message: str, data: dict | None = None) -> dict:
        return {"ok": False, "blocked": False, "command": command, "reason": reason,
                "message": message, "data": data or {}, "warnings": []}

    def _connect_pc(self) -> tuple[CDPClient, PageController]:
        client = self._client
        if client is None:
            client = CDPClient(host=self._host, port=self._port)
            client.connect()
        if self._target_id is not None:
            result = client.send("Target.getTargets")
            targets = result.get("targetInfos", [])
            page = next((t for t in targets if t["targetId"] == self._target_id), None)
            if page is None:
                raise RuntimeError(
                    f"Target {self._target_id[:16]}... not found (was the tab closed?)"
                )
            session = CDPSession(client)
            session.attach(page["targetId"])
            session.send("Runtime.enable")
            return client, PageController(session)
        return client, PageController.attach_to_first_page(client)

    def _run_with_pc(self, cmd: str, fn) -> dict:
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err(cmd, "chrome_not_running",
                             f"Chrome CDP endpoint not reachable on {self._host}:{self._port}.")
        try:
            client, pc = self._connect_pc()
            try:
                return fn(pc)
            finally:
                if self._client is None:  # we created it — close it
                    client.close()
        except Exception as exc:
            return self._err(cmd, "error", str(exc))

    def run(self, args: list[str]) -> dict:
        if not args:
            return self._err("help", "no_command", "Provide a command. See README for usage.")
        cmd = args[0]

        if cmd == "status":
            return self._cmd_status()
        if cmd == "pages":
            return self._cmd_pages()
        if cmd == "launch":
            return self._cmd_launch()
        if cmd == "navigate":
            if len(args) < 2:
                return self._err(cmd, "missing_arg", "Usage: navigate <url>")
            return self._cmd_navigate(args[1])
        if cmd == "snapshot":
            return self._run_with_pc(cmd, lambda pc: self._ok(cmd, pc.observe_page(), "Snapshot captured."))
        if cmd == "visible-text":
            max_chars = int(args[1]) if len(args) > 1 else 12000
            return self._run_with_pc(cmd, lambda pc: self._ok(cmd, pc.visible_text(max_chars), "Visible text retrieved."))
        if cmd == "visible-text-md":
            path = args[1] if len(args) > 1 else None
            return self._cmd_visible_text_md(path)
        if cmd == "page-snapshot-md":
            include_hidden = "--include-hidden" in args
            path = next((a for a in args[1:] if not a.startswith("--")), None)
            return self._cmd_page_snapshot_md(include_hidden, path)
        if cmd == "get-page-html":
            path = args[1] if len(args) > 1 else None
            return self._cmd_get_page_html(path)
        if cmd == "get-cookies":
            return self._cmd_get_cookies()
        if cmd == "list-controls":
            return self._run_with_pc(cmd, lambda pc: (pc.observe_page(), self._ok(cmd, {"controls": pc.list_controls()}, f"{len(pc.list_controls())} control(s)."))[1])
        if cmd == "list-fields":
            return self._run_with_pc(cmd, lambda pc: (pc.observe_page(), self._ok(cmd, {"fields": pc.list_fields()}, f"{len(pc.list_fields())} field(s)."))[1])
        if cmd == "list-uploads":
            return self._run_with_pc(cmd, lambda pc: (pc.observe_page(), self._ok(cmd, {"uploads": pc.list_uploads()}, f"{len(pc.list_uploads())} upload(s)."))[1])
        if cmd == "active-element":
            return self._run_with_pc(cmd, lambda pc: (pc.observe_page(), self._ok(cmd, {"active": pc.active_element()}, "Active element retrieved."))[1])
        if cmd == "screenshot":
            path = args[1] if len(args) > 1 else None
            return self._run_with_pc(cmd, lambda pc: self._ok(cmd, {"path": pc.screenshot(path)}, "Screenshot saved."))
        if cmd == "save-state":
            out = args[1] if len(args) > 1 else None
            return self._run_with_pc(cmd, lambda pc: self._ok(cmd, {"output_dir": pc.save_state(out)}, "State saved."))
        if cmd == "list-expandables":
            return self._run_with_pc(cmd, lambda pc: (pc.observe_page(), self._ok(cmd, {"expandables": pc.list_expandables()}, f"{len(pc.list_expandables())} expandable(s)."))[1])
        if cmd == "find-text":
            if len(args) < 2:
                return self._err(cmd, "missing_arg", "Usage: find-text <text>")
            text = args[1]
            return self._run_with_pc(cmd, lambda pc: self._ok(cmd, pc.scroll_to_text(text), f"Find-text completed."))
        if cmd == "scroll-to-text":
            if len(args) < 2:
                return self._err(cmd, "missing_arg", "Usage: scroll-to-text <text>")
            text = args[1]
            return self._run_with_pc(cmd, lambda pc: (pc.observe_page(), self._ok(cmd, pc.scroll_to_text(text), "Scrolled."))[1])
        if cmd == "scroll-ref":
            if len(args) < 2:
                return self._err(cmd, "missing_arg", "Usage: scroll-ref <ref>")
            ref = args[1]
            def _scroll_ref(pc):
                pc.observe_page()
                pc.scroll_ref_into_view(ref)
                return self._ok(cmd, {"ref": ref}, "Scrolled ref into view.")
            return self._run_with_pc(cmd, _scroll_ref)
        if cmd == "click-ref":
            if len(args) < 2:
                return self._err(cmd, "missing_arg", "Usage: click-ref <ref> [--allow-dangerous]")
            ref = args[1]
            allow_dangerous = "--allow-dangerous" in args
            def _click(pc):
                pc.observe_page()
                result = pc.click_ref(ref, allow_dangerous=allow_dangerous)
                if result.get("blocked"):
                    r = self._ok(cmd, result, "Action blocked.")
                    r["blocked"] = True
                    r["reason"] = result.get("reason", "")
                    return r
                return self._ok(cmd, result, "Clicked.")
            return self._run_with_pc(cmd, _click)
        if cmd == "focus-ref":
            if len(args) < 2:
                return self._err(cmd, "missing_arg", "Usage: focus-ref <ref>")
            ref = args[1]
            def _focus(pc):
                pc.observe_page()
                pc.focus_ref(ref)
                return self._ok(cmd, {"ref": ref}, "Focused.")
            return self._run_with_pc(cmd, _focus)
        if cmd == "fill-ref":
            if len(args) < 3:
                return self._err(cmd, "missing_arg", "Usage: fill-ref <ref> <text_or_file>")
            ref = args[1]
            text = args[2]
            def _fill(pc):
                pc.observe_page()
                result = pc.fill_ref(ref, text)
                return self._ok(cmd, result, "Filled.")
            return self._run_with_pc(cmd, _fill)
        if cmd == "paste-text":
            if len(args) < 2:
                return self._err(cmd, "missing_arg", "Usage: paste-text <text>")
            text = args[1]
            def _paste(pc):
                pc.observe_page()
                result = pc.paste_text(text)
                return self._ok(cmd, result, "Pasted.")
            return self._run_with_pc(cmd, _paste)
        if cmd == "upload-file-ref":
            if len(args) < 3:
                return self._err(cmd, "missing_arg", "Usage: upload-file-ref <ref> <path>")
            ref = args[1]
            path = args[2]
            def _upload(pc):
                pc.observe_page()
                result = pc.upload_file_ref(ref, path)
                return self._ok(cmd, result, "Uploaded.")
            return self._run_with_pc(cmd, _upload)

        if cmd == "monitor":
            # monitor --target-id <id> --output <path> [--port N] [--body-url-patterns p1,p2]
            if "--target-id" not in args or "--output" not in args:
                return self._err(cmd, "missing_arg",
                                 "Usage: monitor --target-id <id> --output <path> [--port N] [--body-url-patterns p1,p2]")
            target_id = args[args.index("--target-id") + 1]
            output_path = args[args.index("--output") + 1]
            body_patterns: list[str] = []
            if "--body-url-patterns" in args:
                raw = args[args.index("--body-url-patterns") + 1]
                body_patterns = [p.strip() for p in raw.split(",") if p.strip()]
            return self._cmd_monitor(target_id, output_path, body_patterns)

        return self._err(cmd, "unknown_command", f"Unknown command: {cmd!r}")

    def _cmd_monitor(self, target_id: str, output_path: str,
                      body_url_patterns: list | None = None) -> dict:
        """Run NetworkMonitor for target_id until interrupted. Blocks."""
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err("monitor", "chrome_not_running", "Chrome is not running.")
        _log(f"[monitor] Recording → {output_path}")
        _log(f"[monitor] target {target_id[:16]}...  Press Ctrl+C to stop.")
        if body_url_patterns:
            _log(f"[monitor] Body capture patterns: {body_url_patterns}")
        mon = NetworkMonitor(
            target_id=target_id, output_path=output_path,
            host=self._host, port=self._port,
            body_url_patterns=body_url_patterns or [],
        )
        try:
            mon.run()
        except KeyboardInterrupt:
            pass
        _log(f"[monitor] Stopped. {mon.line_count} event(s) written.")
        return self._ok("monitor", {"lines": mon.line_count, "output": output_path},
                        f"{mon.line_count} network event(s) recorded.")

    def _cmd_status(self) -> dict:
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err("status", "chrome_not_running",
                             f"Chrome CDP endpoint not reachable on {self._host}:{self._port}.")
        info = health.version_info() or {}
        return self._ok("status", {
            "chrome_running": True,
            "cdp_port": self._port,
            "browser": info.get("Browser", ""),
        }, "Chrome is running.")

    def _cmd_pages(self) -> dict:
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err("pages", "chrome_not_running", "Chrome is not running.")
        client = CDPClient(host=self._host, port=self._port)
        client.connect()
        try:
            result = client.send("Target.getTargets")
            targets = result.get("targetInfos", [])
            pages = [
                {"index": i, "target_id": t["targetId"], "type": t["type"],
                 "title": t.get("title", ""), "url": t.get("url", "")}
                for i, t in enumerate(targets) if t["type"] == "page"
            ]
            return self._ok("pages", {"pages": pages}, f"{len(pages)} page(s) found.")
        finally:
            client.close()

    def _cmd_visible_text_md(self, output_path: str | None = None) -> dict:
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err("visible-text-md", "chrome_not_running",
                             f"Chrome is not running on {self._host}:{self._port}.")
        markdownify = _get_versholn().install_and_import("markdownify")
        client = CDPClient(host=self._host, port=self._port)
        client.connect()
        try:
            result = client.send("Target.getTargets")
            targets = result.get("targetInfos", [])
            page = next((t for t in targets if t["type"] == "page"), None)
            if page is None:
                return self._err("visible-text-md", "no_page", "No page targets found.")
            session = CDPSession(client)
            session.attach(page["targetId"])
            session.send("Runtime.enable")
            html = session.send("Runtime.evaluate", {
                "expression": "document.documentElement.outerHTML",
                "returnByValue": True,
            }).get("result", {}).get("value", "")
            url = session.send("Runtime.evaluate", {
                "expression": "document.location.href",
                "returnByValue": True,
            }).get("result", {}).get("value", "")
        finally:
            client.close()
        md = markdownify.markdownify(html, heading_style="ATX", strip=["script", "style"])
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md)
            return self._ok("visible-text-md", {"path": output_path, "url": url, "chars": len(md)},
                            f"Markdown written to {output_path}")
        return self._ok("visible-text-md", {"markdown": md, "url": url, "chars": len(md)},
                        "Markdown retrieved.")

    def _cmd_page_snapshot_md(self, include_hidden: bool = False,
                               output_path: str | None = None) -> dict:
        cmd = "page-snapshot-md"
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err(cmd, "chrome_not_running",
                             f"Chrome is not running on {self._host}:{self._port}.")
        owned = self._client is None
        client = self._client if not owned else CDPClient(host=self._host, port=self._port)
        try:
            if owned:
                client.connect()
            if self._target_id is not None:
                result = client.send("Target.getTargets")
                targets = result.get("targetInfos", [])
                page = next((t for t in targets if t["targetId"] == self._target_id), None)
                if page is None:
                    return self._err(cmd, "no_target",
                                     f"Target {self._target_id[:16]}... not found.")
            else:
                result = client.send("Target.getTargets")
                targets = result.get("targetInfos", [])
                page = next((t for t in targets if t["type"] == "page"), None)
                if page is None:
                    return self._err(cmd, "no_page", "No page targets found.")
            session = CDPSession(client)
            session.attach(page["targetId"])
            session.send("Runtime.enable")
            js = _PAGE_SNAPSHOT_JS + "(" + ("true" if include_hidden else "false") + ")"
            md = session.send("Runtime.evaluate", {
                "expression": js,
                "returnByValue": True,
            }).get("result", {}).get("value", "") or ""
            url = session.send("Runtime.evaluate", {
                "expression": "document.location.href",
                "returnByValue": True,
            }).get("result", {}).get("value", "") or ""
        except Exception as exc:
            return self._err(cmd, "error", str(exc))
        finally:
            if owned:
                client.close()
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md)
            return self._ok(cmd, {"path": output_path, "url": url, "chars": len(md)},
                            f"Page snapshot written to {output_path}")
        return self._ok(cmd, {"markdown": md, "url": url, "chars": len(md)},
                        "Page snapshot captured.")

    def _cmd_get_page_html(self, output_path: str | None = None) -> dict:
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err("get-page-html", "chrome_not_running",
                             f"Chrome is not running on {self._host}:{self._port}.")
        client = CDPClient(host=self._host, port=self._port)
        client.connect()
        try:
            result = client.send("Target.getTargets")
            targets = result.get("targetInfos", [])
            page = next((t for t in targets if t["type"] == "page"), None)
            if page is None:
                return self._err("get-page-html", "no_page", "No page targets found.")
            session = CDPSession(client)
            session.attach(page["targetId"])
            session.send("Runtime.enable")
            html = session.send("Runtime.evaluate", {
                "expression": "document.documentElement.outerHTML",
                "returnByValue": True,
            }).get("result", {}).get("value", "")
            url = session.send("Runtime.evaluate", {
                "expression": "document.location.href",
                "returnByValue": True,
            }).get("result", {}).get("value", "")
        finally:
            client.close()
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            return self._ok("get-page-html", {"path": output_path, "url": url, "chars": len(html)},
                            f"HTML written to {output_path}")
        return self._ok("get-page-html", {"html": html, "url": url, "chars": len(html)},
                        "Page HTML retrieved.")

    def _cmd_get_cookies(self) -> dict:
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err("get-cookies", "chrome_not_running",
                             f"Chrome is not running on {self._host}:{self._port}.")
        client = CDPClient(host=self._host, port=self._port)
        client.connect()
        try:
            result = client.send("Target.getTargets")
            targets = result.get("targetInfos", [])
            page = next((t for t in targets if t["type"] == "page"), None)
            if page is None:
                return self._err("get-cookies", "no_page", "No page targets found.")
            session = CDPSession(client)
            session.attach(page["targetId"])
            session.send("Runtime.enable")
            url = session.send("Runtime.evaluate", {
                "expression": "document.location.href",
                "returnByValue": True,
            }).get("result", {}).get("value", "")
            cookies_result = client.send("Network.getCookies", {"urls": [url]})
            cookies = cookies_result.get("cookies", [])
            return self._ok("get-cookies",
                            {"cookies": cookies, "url": url, "count": len(cookies)},
                            f"{len(cookies)} cookie(s) retrieved.")
        finally:
            client.close()

    def _cmd_launch(self) -> dict:
        health = ChromeHealth(self._host, self._port)
        if health.is_alive():
            return self._ok("launch", {"cdp_port": self._port}, "Chrome is already running.")
        launcher = ChromeLauncher(ChromeLaunchConfig(
            remote_debugging_port=self._port,
            headless=False,
        ))
        launcher.start()
        for _ in range(20):
            time.sleep(0.5)
            if health.is_alive():
                return self._ok("launch", {"cdp_port": self._port}, "Chrome launched.")
        return self._err("launch", "timeout", "Chrome CDP did not become reachable after 10 s.")

    def _cmd_navigate(self, url: str) -> dict:
        health = ChromeHealth(self._host, self._port)
        if not health.is_alive():
            return self._err("navigate", "chrome_not_running",
                             f"Chrome is not running on {self._host}:{self._port}. Run 'launch' first.")
        client = CDPClient(host=self._host, port=self._port)
        client.connect()
        try:
            result = client.send("Target.getTargets")
            targets = result.get("targetInfos", [])
            page = next((t for t in targets if t["type"] == "page"), None)
            if page is None:
                return self._err("navigate", "no_page", "No page targets found.")
            session = CDPSession(client)
            session.attach(page["targetId"])
            session.send("Runtime.enable")
            session.send("Page.navigate", {"url": url})
            time.sleep(3)
            nav_url = session.send("Runtime.evaluate", {
                "expression": "document.location.href", "returnByValue": True,
            }).get("result", {}).get("value", "")
            return self._ok("navigate", {"url": nav_url}, f"Navigated to {nav_url}")
        finally:
            client.close()


# ---------------------------------------------------------------------------
# Network monitor — streams CDP Network events to a JSONL file
# ---------------------------------------------------------------------------

class NetworkMonitor:
    """Stream CDP Network events for a specific tab to a JSONL file.

    Each line written is a JSON object::

        {"_t": "<iso-timestamp>", "_event": "<CDP event name>", ...<event params>...}

    Pass *body_url_patterns* to also capture response bodies for matching URLs.
    When a response whose URL contains any of the patterns finishes loading,
    the monitor fetches the body via ``Network.getResponseBody`` and writes an
    extra record with ``_event`` == ``"Network.responseBody"`` and a ``body``
    field containing the raw text (or base64 if binary).

    Example::

        mon = NetworkMonitor(
            target_id="abc123",
            output_path="/tmp/net.jsonl",
            body_url_patterns=["/graphql", "/api/tasks"],
        )

    Usage (blocking)::

        mon = NetworkMonitor(target_id="abc123", output_path="/tmp/net.jsonl")
        mon.run()   # blocks until Chrome disconnects or KeyboardInterrupt

    Usage (non-blocking context manager)::

        with NetworkMonitor(target_id, output_path) as mon:
            time.sleep(30)
        # thread stopped on __exit__
    """

    EVENTS = [
        "Network.requestWillBeSent",
        "Network.responseReceived",
        "Network.loadingFinished",
        "Network.loadingFailed",
        "Network.requestServedFromCache",
        "Network.webSocketCreated",
        "Network.webSocketFrameSent",
        "Network.webSocketFrameReceived",
        "Network.webSocketClosed",
        "Network.eventSourceMessageReceived",
    ]

    def __init__(self, target_id: str, output_path: str,
                 host: str = "localhost", port: int = 9222,
                 body_url_patterns: list | None = None) -> None:
        self._target_id = target_id
        self._output_path = output_path
        self._host = host
        self._port = port
        self._body_url_patterns = body_url_patterns or []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.line_count = 0

    def run(self) -> None:
        """Block until CDP connection drops, stop() is called, or KeyboardInterrupt."""
        import datetime as _dt
        client = CDPClient(host=self._host, port=self._port)
        client.connect()
        session = CDPSession(client)
        session.attach(self._target_id)
        # Enable network tracking with a generous body buffer so getResponseBody
        # succeeds before Chrome evicts small JSON responses (default buffer is ~1 MB).
        session.send("Network.enable", {
            "maxResourceBufferSize": 10 * 1024 * 1024,   # 10 MB per resource
            "maxTotalBufferSize":    40 * 1024 * 1024,   # 40 MB total
        })

        # requestId -> url for requests whose bodies we want to capture
        _body_pending: dict[str, str] = {}

        os.makedirs(os.path.dirname(os.path.abspath(self._output_path)), exist_ok=True)
        with open(self._output_path, "a", encoding="utf-8", buffering=1) as fh:
            def _write(record: dict) -> None:
                fh.write(json.dumps(record) + "\n")
                self.line_count += 1

            def _make_handler(event_name: str):
                def _handler(params: dict) -> None:
                    record = {
                        "_t": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "_event": event_name,
                    }
                    record.update(params)
                    _write(record)

                    # Capture request (POST) body as soon as the request is registered.
                    # getRequestPostData is available immediately after requestWillBeSent.
                    if event_name == "Network.requestWillBeSent" and self._body_url_patterns:
                        req_url = params.get("request", {}).get("url", "")
                        has_post = params.get("request", {}).get("hasPostData", False)
                        if has_post and any(pat in req_url for pat in self._body_url_patterns):
                            req_id = params.get("requestId", "")
                            def _fetch_request_body(req_id=req_id, url=req_url):
                                try:
                                    result = session.send("Network.getRequestPostData", {"requestId": req_id})
                                    _write({
                                        "_t": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                        "_event": "Network.requestPostData",
                                        "requestId": req_id,
                                        "url": url,
                                        "postData": result.get("postData", ""),
                                    })
                                except Exception as exc:
                                    _write({
                                        "_t": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                        "_event": "Network.requestPostDataError",
                                        "requestId": req_id,
                                        "url": url,
                                        "error": str(exc),
                                    })
                            threading.Thread(target=_fetch_request_body, daemon=True).start()

                    # Track interesting responses for body capture
                    if event_name == "Network.responseReceived" and self._body_url_patterns:
                        url = params.get("response", {}).get("url", "") or params.get("url", "")
                        if any(pat in url for pat in self._body_url_patterns):
                            _body_pending[params["requestId"]] = url

                    # When a tracked request finishes, fetch its body.
                    # Must run in a separate thread: dispatch() is called synchronously
                    # from _recv_loop, so calling session.send() here would deadlock
                    # (send waits for _recv_loop to deliver the response, but _recv_loop
                    # is blocked waiting for this handler to return).
                    if event_name == "Network.loadingFinished" and self._body_url_patterns:
                        req_id = params.get("requestId", "")
                        url = _body_pending.pop(req_id, None)
                        if url:
                            def _fetch_body(req_id=req_id, url=url):
                                try:
                                    result = session.send("Network.getResponseBody", {"requestId": req_id})
                                    body_record = {
                                        "_t": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                        "_event": "Network.responseBody",
                                        "requestId": req_id,
                                        "url": url,
                                        "body": result.get("body", ""),
                                        "base64Encoded": result.get("base64Encoded", False),
                                    }
                                    _write(body_record)
                                except Exception as exc:
                                    _write({
                                        "_t": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                        "_event": "Network.responseBodyError",
                                        "requestId": req_id,
                                        "url": url,
                                        "error": str(exc),
                                    })
                            threading.Thread(target=_fetch_body, daemon=True).start()

                return _handler

            for ev in self.EVENTS:
                session.on_event(ev, _make_handler(ev))

            try:
                while not self._stop_event.is_set() and not client.closed.is_set():
                    client.closed.wait(timeout=1.0)
            except KeyboardInterrupt:
                pass

        client.close()

    def stop(self) -> None:
        """Signal the run() loop to exit cleanly."""
        self._stop_event.set()

    def __enter__(self):
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_):
        self.stop()
        if self._thread:
            self._thread.join(timeout=5)


# ---------------------------------------------------------------------------
# REPL session — persistent Chrome kept alive between runpy re-runs
# ---------------------------------------------------------------------------

class _ReplSession:
    """Singleton class — no instances. All state lives in globals()['_repl_state'].

    Class-level variables would reset on every runpy re-run (the class is
    redefined each time), so state is stored in globals() which persists across
    re-runs in the same process.

    Usage:
        _pc = _ReplSession.get_page_controller()
    """

    _STATE_KEY = "_repl_state"

    @classmethod
    def _state(cls) -> dict:
        """Return the persistent state dict, creating it on first access."""
        if cls._STATE_KEY not in globals():
            globals()[cls._STATE_KEY] = {
                "config": None,
                "launcher": None,
                "client": None,
                "pc": None,
            }
        return globals()[cls._STATE_KEY]

    @classmethod
    def _alive(cls) -> bool:
        """Return True if the current client connection is still healthy."""
        s = cls._state()
        client = s["client"]
        if client is None or client.closed.is_set():
            return False
        # proc.poll() is a free syscall — no HTTP round-trip needed
        return s["launcher"] is not None and s["launcher"].status() == "running"

    @classmethod
    def _teardown(cls) -> None:
        s = cls._state()
        c = s["client"]; s["client"] = None        
        if c is not None:
            try:
                c.close()
            except Exception:
                pass
        if s["launcher"] is not None:
            try:
                s["launcher"].stop()
            except Exception:
                pass
            s["launcher"] = None
        s["pc"] = None

    @classmethod
    def _start(cls) -> None:
        s = cls._state()
        cls._teardown()
        config = s["config"] or ChromeLaunchConfig()
        launcher = ChromeLauncher(config)

        # Try adopting a Chrome that is already listening on the debug port
        # (e.g. the user launched Chrome manually with --remote-debugging-port).
        if launcher.adopt():
            _log(f"REPL: adopted existing Chrome on port {config.remote_debugging_port}")
            s["launcher"] = launcher
        else:
            _log("REPL: starting Chrome...")
            s["launcher"] = launcher
            launcher.start()
            # Poll the CDP endpoint. A 1-second timeout per attempt keeps each
            # poll fast. If our spawned process exits immediately it means Chrome
            # delegated the launch to an existing instance that has no debug port —
            # detect this and give a clear error rather than waiting 30s.
            _log("REPL: waiting for Chrome CDP endpoint...")
            _deadline = time.monotonic() + 30
            while True:
                if launcher.proc is not None and launcher.proc.poll() is not None:
                    raise RuntimeError(
                        f"Chrome process exited immediately (exit code "
                        f"{launcher.proc.poll()}). An existing Chrome window is "
                        f"probably open without --remote-debugging-port. "
                        f"Close all Chrome windows and try again, or use a "
                        f"separate user_data_dir (e.g. C:\\Temp\\chrome_da_profile)."
                    )
                try:
                    urllib.request.urlopen(
                        f"http://localhost:{config.remote_debugging_port}/json/version",
                        timeout=1,
                    ).close()
                    break
                except Exception:
                    if time.monotonic() > _deadline:
                        raise RuntimeError(
                            f"Chrome did not open CDP endpoint on port "
                            f"{config.remote_debugging_port} within 30s"
                        )
                    time.sleep(0.5)

        s["client"] = CDPClient(port=config.remote_debugging_port)
        s["client"].connect()
        s["pc"] = PageController.attach_to_first_page(s["client"])
        _log(f"REPL: Chrome ready on port {config.remote_debugging_port}")

    @classmethod
    def get_page_controller(cls, config: "ChromeLaunchConfig | None" = None) -> "PageController":
        """Return a healthy PageController, restarting Chrome if needed.

        Pass config on first call (or to reconfigure). Subsequent calls reuse
        the running session unless Chrome has died.
        """
        if config is not None:
            cls._state()["config"] = config
        if not cls._alive():
            _log("REPL: Chrome not alive — restarting session...")
            cls._start()
        return cls._state()["pc"]

    @classmethod
    def get_client(cls) -> "CDPClient | None":
        return cls._state()["client"]

    @classmethod
    def teardown(cls) -> None:
        """Explicitly stop Chrome and clean up."""
        cls._teardown()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_log = lambda msg: print(msg, file=sys.stderr)


def safe_local_imports(g: dict) -> None:
    try:
        pass  # all deps loaded via _get_versholn() inside functions
    except Exception:
        import traceback as _tb
        _log(f"FATAL: safe_local_imports failed:\n{_tb.format_exc()}")
        raise


def main() -> int:
    args = sys.argv[1:]
    cli = BrowserToolCLI()
    result = cli.run(args)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    safe_local_imports(globals())

    if len(sys.argv) > 1:
        try:
            raise SystemExit(main())
        except SystemExit:
            raise
        except Exception:
            import traceback
            _log(f"FATAL unhandled exception:\n{traceback.format_exc()}")
            raise
    else:
        # REPL mode — invoked via:
        #   import runpy ; temp = runpy._run_module_as_main("chrome_tools")
        # Chrome stays alive between re-runs. Edit the lines below and re-run.

        # Dedicated profile where Google credentials are saved.
        # On first run, Chrome opens and you log into Google manually.
        # Subsequent runs reuse the same profile — credentials persist.
        _DA_CONFIG = ChromeLaunchConfig(
            #user_data_dir=r"C:\Users\david\AppData\Local\Google\Chrome\User Data", # Doesn't work!
        )

        _pc = _ReplSession.get_page_controller(config=_DA_CONFIG)

        # --- query tools ---
        # Uncomment one block at a time and re-run.

        # Snapshot: page metadata + all interactive elements with refs
        _snap = _pc.observe_page()
        print(f"url   : {_snap['page']['url']}")
        print(f"title : {_snap['page']['title']}")
        print(f"fields: {len(_snap['fields'])}  controls: {len(_snap['controls'])}  uploads: {len(_snap['uploads'])}")

        # Collapsed expandables (dropdowns/details/accordions not yet open)
        _collapsed = [
            e for e in _snap['expandables']
            if e.get('aria_expanded') in (None, 'false', False)
        ]
        if _collapsed:
            print(f"\ncollapsed expandables ({len(_collapsed)}):")
            for _e in _collapsed:
                print(f"  ref={_e['ref']}  tag={_e['tag']}  label={_e.get('label') or _e.get('text') or '(no label)'!r}")
        else:
            print("\nno collapsed expandables found")

        # Full visible text (first 2000 chars)
        #_vt = _pc.visible_text(max_chars=2000)
        #print(_vt["visible_text"])

        # Dump full page HTML to a file
        if True:
            _html = _pc.evaluate("document.documentElement.outerHTML")
            _html_path = pathlib.Path("page_dump.html")
            _html_path.write_text(_html, encoding="utf-8")
            print(f"HTML written to {_html_path.resolve()}  ({len(_html)} chars)")

            # Full snapshot JSON
            #print(json.dumps(_snap, indent=2))
