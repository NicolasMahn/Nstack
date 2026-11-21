#!/usr/bin/env python3
"""Show OpenRouter status, ask a paid model for a consultation, or generate an image.

Examples:
  python3 scripts/openrouter.py status
  python3 scripts/openrouter.py consult \
    --model "provider/model-name" \
    --prompt-file /tmp/review-prompt.md
  python3 scripts/openrouter.py image \
    --model "provider/image-model" \
    --prompt "A flat app icon of a paper boat" \
    --output /tmp/boat.png
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


API_BASE = "https://openrouter.ai/api/v1"
KEY_NAME = "OPENROUTER_API_KEY"
SCRIPT_PATH = Path(__file__).resolve()
# Model versions change quickly, so status finds current IDs in the live
# catalogue by family name instead of pinning them here.
IMAGE_SUFFIXES = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}
TEXT_BACKUP_FAMILIES = ("-sol",)


@dataclass
class ApiResult:
    status: int
    payload: dict[str, Any]


def request(
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
) -> ApiResult:
    key = os.environ.get(KEY_NAME)
    if not key:
        raise RuntimeError(f"{KEY_NAME} is not set in the environment.")

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            return ApiResult(
                status=response.status,
                payload=json.loads(response.read().decode("utf-8")),
            )
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter returned HTTP {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach OpenRouter: {error.reason}") from error


def money(value: Any) -> str:
    try:
        return f"${Decimal(str(value)):,.4f}"
    except (InvalidOperation, ValueError):
        return "unknown"


def model_price(model: dict[str, Any]) -> tuple[Decimal, Decimal] | None:
    pricing = model.get("pricing", {})
    try:
        return (
            Decimal(str(pricing["prompt"])) * Decimal(1_000_000),
            Decimal(str(pricing["completion"])) * Decimal(1_000_000),
        )
    except (KeyError, InvalidOperation, ValueError):
        return None


def print_price(model: dict[str, Any]) -> None:
    price = model_price(model)
    if price is None:
        print(f"  {model['id']}: price unavailable")
        return
    prompt_per_million, completion_per_million = price
    print(
        f"  {model['id']}: {money(prompt_per_million)} input / "
        f"{money(completion_per_million)} output per million tokens"
    )


def status() -> int:
    # An agent reads this output before it decides to use OpenRouter, so a
    # missing key or a network failure is reported as text, not as a failure.
    try:
        return print_status()
    except Exception as error:
        print(f"OpenRouter unavailable: {error}")
        return 0


def print_status() -> int:
    models = request("/models").payload.get("data", [])

    print("OpenRouter status")
    print("=================")
    print(f"API key: available ({KEY_NAME})")

    try:
        credits = request("/credits").payload.get("data", {})
        limit = credits.get("total_credits")
        used = credits.get("total_usage")
        if limit is not None and used is not None:
            remaining = Decimal(str(limit)) - Decimal(str(used))
            print(f"Balance: {money(remaining)} remaining")
        else:
            print("Balance: unavailable from this key")
    except RuntimeError:
        print("Balance: unavailable (a management key is required for credits)")

    print(f"Live model catalogue: {len(models)} models")
    print("\nImage models")
    for model in models:
        outputs = model.get("architecture", {}).get("output_modalities", [])
        model_id = model.get("id", "")
        if "image" in outputs and not model_id.startswith("openrouter/"):
            print_price(model)

    print("\nText backup models")
    for model in models:
        model_id = model.get("id", "")
        if model_id.startswith("openai/") and model_id.endswith(TEXT_BACKUP_FAMILIES):
            print_price(model)

    print("\nNext step")
    print(
        "For a paid consultation, use:\n"
        f"  python3 {SCRIPT_PATH} consult "
        '--model "provider/model-name" --prompt-file /path/to/prompt.md'
    )
    print(
        "For an image, use:\n"
        f"  python3 {SCRIPT_PATH} image "
        '--model "provider/image-model" --prompt "..." --output /path/to/image.png'
    )
    print(
        "\nBoth commands check the model against the live catalogue, "
        "call it, and report the returned cost."
    )
    return 0


def consult(
    model_id: str,
    prompt: str,
    max_tokens: int | None,
    context_file: str | None = None,
    reasoning_effort: str = "low",
    max_continuations: int | None = None,
    timeout_seconds: int = 30,
) -> int:
    if context_file:
        with open(context_file, encoding="utf-8") as file:
            reference = file.read().strip()
        if not reference:
            raise RuntimeError("The context file is empty.")
        prompt = f"{prompt.strip()}\n\n---\n\nReference document:\n{reference}"


    if not prompt:
        raise RuntimeError("The prompt file is empty.")

    models = request("/models", timeout_seconds=timeout_seconds).payload.get("data", [])
    model = next((item for item in models if item.get("id") == model_id), None)
    if model is None:
        raise RuntimeError(
            f'No live OpenRouter model matches "{model_id}". '
            "Run `status` and choose an ID from the current catalogue."
        )

    price = model_price(model)
    if price:
        prompt_per_million, completion_per_million = price
        print(
            "Live list price: "
            f"{money(prompt_per_million)} input / "
            f"{money(completion_per_million)} output per million tokens"
        )
        if max_tokens is None:
            print("Output cap: provider default (no client-side limit requested)")
        else:
            print(
                "Maximum output-only estimate per call: "
                f"{money(completion_per_million * Decimal(max_tokens) / Decimal(1_000_000))}"
            )
        print(
            "A length-truncated response is continued automatically until it finishes"
            if max_continuations is None
            else "Automatic continuations are capped at "
            f"{max_continuations}."
        )
    else:
        print("Live list price: unavailable")

    messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
    segments: list[str] = []
    total_cost = Decimal(0)
    total_cost_available = True
    finish_reason = ""

    call_number = 0
    while True:
        call_number += 1
        body: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "reasoning": {
                "effort": reasoning_effort,
                "exclude": True,
            },
        }
        if max_tokens is not None:
            body["max_completion_tokens"] = max_tokens

        result = request(
            "/chat/completions",
            method="POST",
            body=body,
            timeout_seconds=timeout_seconds,
        )
        choices = result.payload.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter returned no completion.")

        choice = choices[0]
        assistant_message = choice.get("message", {})
        message = assistant_message.get("content")
        reasoning = assistant_message.get("reasoning")
        finish_reason = choice.get("finish_reason") or "unknown"
        usage = result.payload.get("usage", {})
        actual_cost = usage.get("cost")
        try:
            total_cost += Decimal(str(actual_cost))
        except (InvalidOperation, ValueError):
            total_cost_available = False

        if isinstance(message, str) and message.strip():
            segment = message
            segments.append(segment)
            messages.append({"role": "assistant", "content": segment})
        elif isinstance(reasoning, str) and reasoning.strip():
            raise RuntimeError(
                "The model returned reasoning but no final text. "
                "Try a lower reasoning effort or a larger token limit."
            )
        else:
            raise RuntimeError("The model returned no final response text.")

        if finish_reason != "length":
            break
        if max_continuations is not None and call_number > max_continuations:
            break
        messages.append(
            {
                "role": "user",
                "content": "Continue exactly where your prior response stopped. Do not repeat it.",
            }
        )

    print("\nConsultation")
    print("============")
    print("".join(segments).strip())
    if finish_reason == "length":
        print("\n[Output remained truncated after the continuation limit.]", file=sys.stderr)
    print("\nCost")
    print("====")
    print(f"Model: {model_id}")
    print(f"Actual cost: {money(total_cost) if total_cost_available else 'unavailable'}")
    return 0


def write_new_file(path: Path, data: bytes) -> Path:
    """Write without overwriting. The image is already paid for, so a taken
    name gets a numbered sibling instead of an error."""
    candidate = path
    number = 1
    while True:
        try:
            with open(candidate, "xb") as file:
                file.write(data)
            return candidate
        except FileExistsError:
            number += 1
            candidate = path.with_name(f"{path.stem}-{number}{path.suffix}")


def generate_image(
    model_id: str,
    prompt: str,
    output: Path,
    input_images: list[Path],
    timeout_seconds: int,
) -> int:
    if not prompt.strip():
        raise RuntimeError("The prompt is empty.")
    if not output.parent.is_dir():
        raise RuntimeError(f"{output.parent} is not a directory.")

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for path in input_images:
        mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}
        )

    result = request(
        "/chat/completions",
        method="POST",
        body={
            "model": model_id,
            "messages": [{"role": "user", "content": content}],
            "modalities": ["image", "text"],
        },
        timeout_seconds=timeout_seconds,
    )
    choices = result.payload.get("choices", [])
    images = choices[0].get("message", {}).get("images", []) if choices else []
    if not images:
        raise RuntimeError("The model returned no image. Check that it supports image output.")

    # Images arrive as data URLs. The model decides the format, so the suffix
    # follows the returned MIME type rather than the requested file name.
    saved: list[Path] = []
    for image in images:
        header, _, encoded = image["image_url"]["url"].partition(",")
        mime_subtype = header.partition("/")[2].partition(";")[0]
        suffix = IMAGE_SUFFIXES.get(mime_subtype, ".png")
        saved.append(write_new_file(output.with_suffix(suffix), base64.b64decode(encoded)))

    for path in saved:
        print(f"Saved: {path}")
    print(f"Model: {model_id}")
    print(f"Actual cost: {money(result.payload.get('usage', {}).get('cost'))}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("status", help="Show balance availability and live model status.")

    consult_parser = commands.add_parser(
        "consult",
        help="Run one bounded paid consultation.",
    )
    consult_parser.add_argument(
        "--model",
        required=True,
        help="Exact OpenRouter model ID from the live catalogue.",
    )
    prompt_source = consult_parser.add_mutually_exclusive_group(required=True)
    prompt_source.add_argument(
        "--prompt",
        help="Consultation prompt provided directly on the command line.",
    )
    prompt_source.add_argument(
        "--prompt-file",
        help="UTF-8 text file containing the consultation prompt.",
    )
    consult_parser.add_argument(
        "--context-file",
        help="Optional UTF-8 document supplied as reference context.",
    )
    consult_parser.add_argument(
        "--max-tokens",
        type=int,
        help="Optional maximum completion tokens. Omit to use the provider default.",
    )
    consult_parser.add_argument(
        "--reasoning-effort",
        default="low",
        help="Reasoning effort for models that support it (default: low).",
    )
    consult_parser.add_argument(
        "--max-continuations",
        type=int,
        help="Optional cap on continuations after a length-truncated answer (default: no cap).",
    )
    consult_parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Seconds to wait for each OpenRouter request (default: 30).",
    )

    image_parser = commands.add_parser("image", help="Generate or edit one image.")
    image_parser.add_argument(
        "--model",
        required=True,
        help="Exact OpenRouter image model ID from the live catalogue.",
    )
    image_parser.add_argument("--prompt", required=True, help="What to draw or change.")
    image_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Where to save the image. Existing files are never overwritten.",
    )
    image_parser.add_argument(
        "--input-image",
        type=Path,
        action="append",
        default=[],
        help="Optional PNG or JPEG to edit or use as reference (repeatable).",
    )
    image_parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Seconds to wait for the image (default: 180).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "status":
        return status()
    if args.timeout <= 0:
        raise RuntimeError("--timeout must be greater than zero.")
    if args.command == "image":
        return generate_image(
            args.model, args.prompt, args.output, args.input_image, args.timeout
        )
    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as file:
            prompt = file.read()
    return consult(
        args.model,
        prompt,
        args.max_tokens,
        args.context_file,
        args.reasoning_effort,
        args.max_continuations,
        args.timeout,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
