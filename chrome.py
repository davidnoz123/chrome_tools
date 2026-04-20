
r"""

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-allow-origins=* --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\ChromeDebugProfile"

"""

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, field

import versholn


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
        psutil = versholn.install_and_import("psutil")
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
        psutil = versholn.install_and_import("psutil")
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
        websocket = versholn.install_and_import("websocket-client", import_as="websocket")
        self.ws = websocket.WebSocket()
        self.ws.connect(ws_url)
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def close(self) -> None:
        if self.ws:
            self.ws.close()
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
        launcher = ChromeLauncher(ChromeLaunchConfig(delete_profile=True))
        launcher.start()
        time.sleep(1)

        client = CDPClient()
        client.connect()

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
        cls_session = CDPSession
        cls_session.sim_test(client)

        client.close()
        launcher.stop()
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
