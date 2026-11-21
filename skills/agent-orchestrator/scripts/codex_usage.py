#!/usr/bin/env python3
"""Show how much of Nicolas's Codex plan usage is left, and the current model slugs.

Asks the local Codex app-server, which is the same source the Codex UI uses.

An agent reads this output to decide whether Codex can take work, so the script
always exits 0 and reports a problem as text: "unavailable" is an answer too.
"""

from __future__ import annotations

import json
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODELS_CACHE = Path.home() / ".codex" / "models_cache.json"

TIMEOUT_SECONDS = 20
RATE_LIMITS_REQUEST_ID = 2


def rpc(method: str, request_id: int | None = None, params: dict[str, Any] | None = None) -> str:
    message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if request_id is not None:
        message["id"] = request_id
    if params is not None:
        message["params"] = params
    return json.dumps(message) + "\n"


def read_rate_limits() -> dict[str, Any]:
    server = subprocess.Popen(
        ["codex", "app-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if server.stdin is None or server.stdout is None:
        raise RuntimeError("could not open pipes to the Codex app-server")
    try:
        client = {"clientInfo": {"name": "codex-usage", "version": "1.0"}}
        server.stdin.write(rpc("initialize", 1, client))
        server.stdin.write(rpc("initialized"))
        server.stdin.write(rpc("account/rateLimits/read", RATE_LIMITS_REQUEST_ID))
        server.stdin.flush()

        # The server also sends notifications, so skip lines until our reply.
        for line in server.stdout:
            reply = json.loads(line)
            if reply.get("id") != RATE_LIMITS_REQUEST_ID:
                continue
            if "error" in reply:
                raise RuntimeError(f"Codex returned an error: {reply['error']}")
            return reply["result"]
        raise RuntimeError("Codex closed the connection without answering.")
    finally:
        server.kill()
        server.wait()


def describe_window(label: str, window: dict[str, Any] | None) -> None:
    if not window:
        return
    remaining = 100 - window["usedPercent"]
    resets = datetime.fromtimestamp(window["resetsAt"], tz=timezone.utc).astimezone()
    days = window["windowDurationMins"] / 1440
    print(
        f"{label} ({days:g}-day window): {remaining:g}% remaining, "
        f"resets {resets.isoformat(timespec='minutes')}"
    )


def print_models() -> None:
    """List current model slugs, so callers never need a pinned version."""
    try:
        models = json.loads(MODELS_CACHE.read_text(encoding="utf-8"))["models"]
    except (OSError, KeyError, json.JSONDecodeError):
        print("Models: unavailable (no Codex model cache)")
        return
    # Codex marks internal models as hidden; they are not meant to be picked.
    slugs = [model["slug"] for model in models if model.get("visibility") == "list"]
    print("Models: " + ", ".join(slugs))


def main() -> None:
    result = read_rate_limits()
    limits = result["rateLimits"]
    allowed = result.get("ordinaryUsageAllowed", True)

    print(f"Codex usable now: {'yes' if allowed else 'no'}")
    describe_window("Primary limit", limits.get("primary"))
    describe_window("Secondary limit", limits.get("secondary"))
    credits = limits.get("credits") or {}
    if credits.get("unlimited"):
        print("Credits: unlimited")
    elif credits.get("hasCredits"):
        print(f"Credits: {credits.get('balance')}")
    print_models()


def on_timeout(signum: int, frame: Any) -> None:
    raise RuntimeError(f"no answer within {TIMEOUT_SECONDS} seconds")


if __name__ == "__main__":
    try:
        # A hung app-server must not stall the orchestrator.
        signal.signal(signal.SIGALRM, on_timeout)
        signal.alarm(TIMEOUT_SECONDS)
        main()
    except Exception as error:  # Any failure must still exit 0; see the module docstring.
        print(f"Codex usage unavailable: {error}. Treat Codex as unusable.")
