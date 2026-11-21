"""Regression tests for cx against a fake `codex`: python3 test_cx.py"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

CX = Path(__file__).with_name("cx")

# Behaves like `codex exec --json`; FAKE_MODE picks the outcome.
FAKE_CODEX = r'''#!/bin/sh
out=""; prev=""
for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done
echo '{"type":"thread.started","thread_id":"fake-thread"}'
echo '{"type":"item.started","item":{"type":"command_execution","command":"/usr/bin/zsh -lc '"'"'ls'"'"'"}}'
case "$FAKE_MODE" in
  ok) echo "$*" > "$out.args"; echo DONE > "$out"; echo '{"type":"turn.completed"}';;
  fail) echo '{"type":"turn.failed","error":{"message":"usage limit reached"}}'; exit 1;;
  hang) sleep 300 & wait;;
esac
'''


class Cx(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "bin").mkdir()
        fake = self.tmp / "bin" / "codex"
        fake.write_text(FAKE_CODEX)
        fake.chmod(0o755)
        (self.tmp / "brief.md").write_text("do it")
        self.env = {**os.environ, "CX_HOME": str(self.tmp / "threads"),
                    "PATH": f"{self.tmp / 'bin'}:{os.environ['PATH']}"}

    def cx(self, *args, mode="ok", **kwargs):
        return subprocess.run([sys.executable, CX, *args], env={**self.env, "FAKE_MODE": mode},
                              capture_output=True, text=True, **kwargs)

    def start(self, name, mode, *extra):
        return subprocess.Popen([sys.executable, CX, "run", name, "--brief", self.tmp / "brief.md",
                                 "--cd", self.tmp, *extra],
                                env={**self.env, "FAKE_MODE": mode}, stdout=subprocess.PIPE, text=True)

    def state(self, name):
        return json.loads((self.tmp / "threads" / name / "state.json").read_text())

    def test_success_records_result_thread_and_progress(self):
        result = self.cx("run", "a", "--brief", self.tmp / "brief.md", "--cd", self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.state("a")["state"], "done")
        self.assertEqual(self.state("a")["thread_id"], "fake-thread")
        self.assertEqual(self.cx("result", "a").stdout.strip(), "DONE")
        progress = (self.tmp / "threads" / "a" / "progress.log").read_text()
        self.assertIn("$ ls", progress)
        args = (self.tmp / "threads" / "a" / "result.md.args").read_text()
        self.assertIn('approval_policy="never"', args)

    def test_failure_is_reported_with_its_reason(self):
        result = self.cx("run", "b", "--brief", self.tmp / "brief.md", "--cd", self.tmp, mode="fail")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.state("b")["state"], "failed")
        self.assertIn("usage limit reached", self.cx("status", "b").stdout
                      + (self.tmp / "threads" / "b" / "progress.log").read_text())

    def test_silent_hang_times_out_and_leaves_no_process(self):
        started = time.time()
        result = self.cx("run", "c", "--brief", self.tmp / "brief.md", "--cd", self.tmp,
                         "--timeout", "0.05", mode="hang", timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertLess(time.time() - started, 15)
        self.assertEqual(self.state("c")["state"], "timeout")
        leftover = subprocess.run(["pgrep", "-f", f"{self.tmp}/bin/codex"], capture_output=True)
        self.assertEqual(leftover.stdout, b"")

    def test_killed_wrapper_is_detected_and_codex_stops(self):
        process = self.start("d", "hang")
        time.sleep(1.5)
        process.kill()
        process.wait()
        time.sleep(0.5)
        self.assertIn("killed", self.cx("status", "d").stdout)
        leftover = subprocess.run(["pgrep", "-f", f"{self.tmp}/bin/codex"], capture_output=True)
        self.assertEqual(leftover.stdout, b"")

    def test_second_run_of_a_running_thread_is_refused(self):
        process = self.start("e", "hang")
        time.sleep(1.5)
        second = self.cx("run", "e", "--brief", self.tmp / "brief.md", "--cd", self.tmp)
        process.kill()
        process.wait()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("already running", second.stderr)

    def test_resume_keeps_the_previous_result(self):
        self.cx("run", "f", "--brief", self.tmp / "brief.md", "--cd", self.tmp)
        result = self.cx("resume", "f", "and now this")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "threads" / "f" / "result.previous.md").exists())
        args = (self.tmp / "threads" / "f" / "result.md.args").read_text()
        self.assertIn("resume fake-thread", args)

    def test_watch_ends_when_threads_end_and_can_give_up_its_window(self):
        process = self.start("g", "hang", "--timeout", "0.05")
        watch = self.cx("watch", "g", timeout=60)
        process.wait()
        self.assertIn("g: timeout", watch.stdout)
        slow = self.start("h", "hang")
        time.sleep(1)
        window = self.cx("watch", "h", "--for", "0.02", timeout=60)
        slow.kill()
        slow.wait()
        self.assertIn("re-arm", window.stdout)


if __name__ == "__main__":
    unittest.main()
