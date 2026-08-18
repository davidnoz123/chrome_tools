"""Tests for CDPClient's reply timeout.

    & "<venv>\Scripts\python.exe" -m unittest chrome_tools_test

No Chrome and no WebSocket: the transport is replaced by a fake, so these
exercise the waiting and raising alone. That is the whole of what changed.
"""

import json
import threading
import time
import unittest

import chrome_tools


class FakeWS:
    """A WebSocket that never answers, unless a reply is scheduled for it."""

    def __init__(self, reply=None, delay=0.0):
        self.reply = reply          # dict to answer with, or None to go silent
        self.delay = delay
        self.sent = []

    def send(self, raw):
        self.sent.append(json.loads(raw))
        if self.reply is None:
            return
        msg = dict(self.reply, id=json.loads(raw)["id"])
        threading.Timer(self.delay, self._deliver, args=(msg,)).start()

    def _deliver(self, msg):
        entry = self.client._pending.get(msg["id"])
        if entry:
            entry["result"] = msg.get("result", {})
            entry["error"] = msg.get("error")
            entry["event"].set()


def client_with(ws, **kw):
    c = chrome_tools.CDPClient(**kw)
    c.ws = ws
    ws.client = c
    return c


class SilenceIsNotAnEmptyAnswer(unittest.TestCase):
    """The bug: a command that never answered returned {} and looked fine."""

    def test_timeout_raises_rather_than_returning_empty(self):
        c = client_with(FakeWS(reply=None), timeout=0.05)
        with self.assertRaises(chrome_tools.CDPTimeout):
            c.send("Runtime.evaluate", {})

    def test_the_message_names_the_method_and_the_wait(self):
        c = client_with(FakeWS(reply=None), timeout=0.05)
        try:
            c.send("Runtime.evaluate", {})
        except chrome_tools.CDPTimeout as exc:
            self.assertIn("Runtime.evaluate", str(exc))
            self.assertIn("0.05s", str(exc))
        else:
            self.fail("expected CDPTimeout")

    def test_an_answer_of_no_payload_still_returns_empty(self):
        """A genuine empty result must stay empty -- that is not a failure."""
        c = client_with(FakeWS(reply={"result": {}}), timeout=5)
        self.assertEqual(c.send("Network.enable", {}), {})

    def test_a_real_result_comes_back(self):
        c = client_with(FakeWS(reply={"result": {"value": 7}}), timeout=5)
        self.assertEqual(c.send("Runtime.evaluate", {}), {"value": 7})


class TheCeilingIsNowRaisable(unittest.TestCase):
    """9 MB at 1.1 s/MB exceeded the old hard-coded ten seconds."""

    def test_default_is_the_historical_ten_seconds(self):
        self.assertEqual(chrome_tools.CDPClient.DEFAULT_TIMEOUT, 10.0)
        self.assertEqual(chrome_tools.CDPClient()._timeout, 10.0)

    def test_a_slow_reply_survives_a_longer_timeout(self):
        c = client_with(FakeWS(reply={"result": {"ok": 1}}, delay=0.2), timeout=0.05)
        with self.assertRaises(chrome_tools.CDPTimeout):
            c.send("Runtime.evaluate", {})          # instance default too short
        c2 = client_with(FakeWS(reply={"result": {"ok": 1}}, delay=0.2), timeout=0.05)
        self.assertEqual(c2.send("Runtime.evaluate", {}, timeout=5), {"ok": 1})

    def test_a_session_passes_the_timeout_through(self):
        """Otherwise the option is unreachable from where photographs are read."""
        seen = {}

        class Recorder(chrome_tools.CDPClient):
            def send(self, method, params=None, session_id=None, timeout=None):
                seen["timeout"] = timeout
                return {}

        session = chrome_tools.CDPSession.__new__(chrome_tools.CDPSession)
        session.client = Recorder()
        session._session_id = "s1"
        session.send("Runtime.evaluate", {}, timeout=45)
        self.assertEqual(seen["timeout"], 45)


if __name__ == "__main__":
    unittest.main()
