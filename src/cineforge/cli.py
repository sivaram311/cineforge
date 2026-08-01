"""cineforge CLI — thin entrypoint over the RunPod client.

Usage::

    cineforge generate --prompt "a sunset over the ocean"

Requires ``RUNPOD_API_KEY`` and ``RUNPOD_ENDPOINT_ID`` in the environment
(or a local ``.env`` file). See ``.env.example``.
"""

from __future__ import annotations

import argparse
import json
import sys

from cineforge import __version__
from cineforge.runpod_client import (
    RunPodAPIError,
    RunPodConfigError,
    generate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cineforge",
        description="Orchestrate RunPod Serverless video/image generation.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    generate_cmd = sub.add_parser(
        "generate",
        help="Submit a text prompt to the configured RunPod Serverless endpoint.",
    )
    generate_cmd.add_argument(
        "--prompt",
        required=True,
        help="Text prompt for generation (T2V / T2I / etc. depending on endpoint).",
    )
    generate_cmd.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between status polls (default: 2.0).",
    )
    generate_cmd.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Max seconds to wait for job completion (default: 600).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        try:
            # TODO(bolt): enrich params (duration, resolution, I2V image URL, etc.)
            result = generate(
                args.prompt,
                poll_interval=args.poll_interval,
                timeout=args.timeout,
            )
        except RunPodConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except RunPodAPIError as exc:
            print(f"error: RunPod API failure: {exc}", file=sys.stderr)
            return 1

        print(json.dumps(result, indent=2, default=str))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
