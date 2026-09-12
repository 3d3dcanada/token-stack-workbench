import importlib.util
import io
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


ADAPTER_PATH = Path(__file__).resolve().parents[1] / "src/rtk-pre-tool.py"
spec = importlib.util.spec_from_file_location("rtk_pre_tool", ADAPTER_PATH)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def payload(command="git status", tool_name="Bash", **extra):
    return json.dumps({
        "session_id": "test",
        "tool_name": tool_name,
        "tool_input": {"command": command, **extra},
    })


def invoke(raw):
    return subprocess.run(
        ["/usr/bin/python3", str(ADAPTER_PATH)], input=raw, text=True,
        capture_output=True, timeout=10, check=False,
    )


class AdapterTests(unittest.TestCase):
    def call_main(self, raw=None):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(adapter.sys, "stdin", io.StringIO(raw or payload())), \
             patch.object(adapter.sys, "stdout", stdout), \
             patch.object(adapter.sys, "stderr", stderr):
            return adapter.main(), stdout.getvalue(), stderr.getvalue()

    def test_benign_rewrite_with_actual_hooks(self):
        result = invoke(payload(description="keep me"))
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        specific = output["hookSpecificOutput"]
        self.assertEqual(specific["permissionDecision"], "allow")
        self.assertEqual(specific["updatedInput"]["command"], "rtk git status")
        self.assertEqual(specific["updatedInput"]["description"], "keep me")

    def test_already_prefixed_is_noop_with_actual_hooks(self):
        result = invoke(payload("rtk git status"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_irrelevant_event_is_noop(self):
        result = invoke(json.dumps({"tool_name": "Read", "tool_input": []}))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_malformed_bash_input_is_blocked(self):
        result = invoke(json.dumps({"tool_name": "Bash", "tool_input": {"command": 7}}))
        self.assertEqual(result.returncode, 2)
        self.assertIn("command must be a string", result.stderr)

    def test_deeply_nested_json_is_blocked(self):
        raw = '{"tool_name":"Bash","tool_input":{"command":"git status","x":' + "[" * 10000 + "0" + "]" * 10000 + "}}"
        result = invoke(raw)
        self.assertEqual(result.returncode, 2)
        self.assertIn("RecursionError", result.stderr)

    def test_guard_failures_are_blocked(self):
        cases = (
            ("exit", {"return_value": subprocess.CompletedProcess([], 9, "", "guard error")}),
            ("timeout", {"side_effect": subprocess.TimeoutExpired([adapter.GUARD], adapter.TIMEOUT_SECONDS)}),
        )
        for name, mock_args in cases:
            with self.subTest(failure=name), \
                 patch.object(adapter.subprocess, "run", **mock_args):
                code, stdout, stderr = self.call_main()
                self.assertEqual(code, 2)
                self.assertEqual(stdout, "")
                self.assertIn("guard", stderr)

    def test_processor_failure_is_blocked(self):
        ok = subprocess.CompletedProcess([], 0, "", "")
        failed = subprocess.CompletedProcess([], 9, "", "processor error")
        with patch.object(adapter.subprocess, "run", side_effect=[ok, failed]):
            with self.assertRaisesRegex(adapter.AdapterError, "processor exited 9"):
                adapter.adapt(payload())

    def test_processor_timeout_is_blocked(self):
        ok = subprocess.CompletedProcess([], 0, "", "")
        timeout = subprocess.TimeoutExpired([adapter.RTK], adapter.TIMEOUT_SECONDS)
        with patch.object(adapter.subprocess, "run", side_effect=[ok, timeout]):
            with self.assertRaisesRegex(adapter.AdapterError, "processor failed"):
                adapter.adapt(payload())

    def test_unexpected_subprocess_decode_error_is_blocked(self):
        decode_error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte")
        with patch.object(adapter.subprocess, "run", side_effect=decode_error):
            code, stdout, stderr = self.call_main()
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertIn("UnicodeDecodeError", stderr)

    def test_malformed_processor_output_is_blocked(self):
        ok = subprocess.CompletedProcess([], 0, "", "")
        malformed = subprocess.CompletedProcess([], 0, "{", "")
        with patch.object(adapter.subprocess, "run", side_effect=[ok, malformed]):
            code, stdout, stderr = self.call_main()
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertIn("invalid JSON", stderr)

    def test_path_mismatch_is_blocked(self):
        rewrite = json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": {"command": "rtk git status"},
            }
        })
        with patch.object(adapter, "run_guard"), \
             patch.object(adapter, "run_rtk", return_value=rewrite), \
             patch.object(adapter.shutil, "which", return_value="/wrong/rtk"):
            code, stdout, stderr = self.call_main()
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertIn("does not resolve", stderr)

    def test_original_guard_denial_uses_payload_only(self):
        result = invoke(payload("git push --force origin test-only-payload"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("3D3D guard BLOCKED: force/mirror push", result.stderr)

    def test_rewritten_guard_denial_uses_payload_only(self):
        rewrite = json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": {"command": "rtk git push --force origin test-only-payload"},
            }
        })
        with patch.object(adapter, "run_rtk", return_value=rewrite):
            with self.assertRaisesRegex(adapter.Denied, "3D3D guard BLOCKED"):
                adapter.adapt(payload())

    def test_outer_code_mode_shape_is_not_the_canonical_hook_event(self):
        # Host round trips are tested by ../tools/host_probe.py.
        # An invented outer event cannot establish whether the nested hook fires.
        for name in ('exec', 'shell'):
            result = invoke(json.dumps({'tool_name': name, 'tool_input': {'code': 'text("git status")'}}))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')

    def test_canonical_multi_command_and_heredoc_denials(self):
        for command in ('git status; git push --force origin test-only-payload',
                        "python3 - <<'PY'\nprint('git push --force')\nPY",
                        "printf '%s\\n' 'git push --force TOKEN_STACK_INERT_CANARY'",
                        'rtk git push --force origin test-only-payload'):
            result = invoke(payload(command))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('3D3D guard BLOCKED', result.stderr)

    def test_canonical_missing_empty_whitespace_and_malformed(self):
        for value in ({}, {'command': None}, {'command': []}):
            result = invoke(json.dumps({'tool_name': 'Bash', 'tool_input': value}))
            self.assertEqual(result.returncode, 2)
        for command in ('', '  \n'):
            result = invoke(payload(command))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')


if __name__ == "__main__":
    unittest.main()
