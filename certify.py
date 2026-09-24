#!/usr/bin/env python3
"""Produce a bounded inert-web-bundle certificate without rendering content."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.producer_core import make_certificate


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("left", type=Path)
    p.add_argument("right", type=Path)
    p.add_argument("-o", "--output", type=Path)
    args = p.parse_args()
    cert = make_certificate(args.left, args.right)
    text = json.dumps(cert, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with args.output.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        except FileExistsError as exc:
            raise SystemExit(f"refusing to overwrite existing output: {args.output}") from exc
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
