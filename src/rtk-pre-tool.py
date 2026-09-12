#!/usr/bin/python3
"""Fail-closed Codex adapter for the existing RTK Claude hook."""

import json
from pathlib import Path
import shutil
import subprocess
import sys


GUARD = str(Path(__file__).resolve().with_name("3d3d-guard.sh"))
RTK = str(Path.home() / ".local/bin/rtk")
TIMEOUT_SECONDS = 5


class AdapterError(RuntimeError):
    pass


class Denied(AdapterError):
    pass


def run_guard(payload):
    try:
        result = subprocess.run(
            [GUARD], input=payload, text=True, capture_output=True,
            timeout=TIMEOUT_SECONDS, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AdapterError(f"guard failed: {exc}") from exc
    if result.returncode == 2:
        raise Denied(result.stderr.strip() or "guard denied the command")
    if result.returncode != 0:
        raise AdapterError(f"guard exited {result.returncode}")


def run_rtk(payload):
    try:
        result = subprocess.run(
            [RTK, "hook", "claude"], input=payload, text=True,
            capture_output=True, timeout=TIMEOUT_SECONDS, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AdapterError(f"RTK processor failed: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip()
        raise AdapterError(f"RTK processor exited {result.returncode}: {detail}")
    return result.stdout


def parse_event(raw):
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(event, dict):
        raise AdapterError("hook input must be a JSON object")
    tool_name = event.get("tool_name")
    if not isinstance(tool_name, str):
        raise AdapterError("tool_name must be a string")
    if tool_name != "Bash":
        return None
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        raise AdapterError("Bash tool_input must be an object")
    if not isinstance(tool_input.get("command"), str):
        raise AdapterError("Bash tool_input.command must be a string")
    return event


def adapt(raw):
    event = parse_event(raw)
    if event is None:
        return None

    run_guard(raw)
    processor_output = run_rtk(raw)
    if not processor_output.strip():
        return None

    try:
        response = json.loads(processor_output)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"RTK returned invalid JSON: {exc.msg}") from exc
    if not isinstance(response, dict):
        raise AdapterError("RTK response must be a JSON object")
    specific = response.get("hookSpecificOutput")
    if not isinstance(specific, dict) or specific.get("hookEventName") != "PreToolUse":
        raise AdapterError("RTK response is not a PreToolUse result")
    updated_input = specific.get("updatedInput")
    if not isinstance(updated_input, dict):
        raise AdapterError("RTK response lacks updatedInput")
    command = updated_input.get("command")
    if not isinstance(command, str) or not command.strip():
        raise AdapterError("RTK rewrite lacks a command")
    if shutil.which("rtk") != RTK:
        raise AdapterError(f"rewritten rtk does not resolve to {RTK}")

    merged_input = dict(event["tool_input"])
    merged_input["command"] = command
    rewritten_event = dict(event)
    rewritten_event["tool_input"] = merged_input
    run_guard(json.dumps(rewritten_event, separators=(",", ":")))

    output_specific = dict(specific)
    output_specific["permissionDecision"] = "allow"
    output_specific["updatedInput"] = merged_input
    output = dict(response)
    output["hookSpecificOutput"] = output_specific
    return json.dumps(output, separators=(",", ":"))


def main():
    try:
        output = adapt(sys.stdin.read())
    except AdapterError as exc:
        print(f"RTK adapter BLOCKED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"RTK adapter BLOCKED: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if output is not None:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
