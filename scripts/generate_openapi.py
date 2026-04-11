#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _build_spec() -> dict:
    try:
        from app.main import app
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "unknown"
        raise SystemExit(
            "❌ Unable to import FastAPI app dependencies while generating OpenAPI. "
            f"Missing module: {missing_module}. "
            "Run 'bash scripts/bootstrap.sh' in a Python 3.12+ environment first."
        ) from exc

    return app.openapi()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify the pinned OpenAPI artifact.")
    parser.add_argument(
        "--output",
        default="docs/api/openapi-v1.json",
        help="Path to write/read the OpenAPI artifact.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the generated OpenAPI spec differs from the committed artifact.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "apps" / "api"))
    sys.path.insert(0, str(root / "packages" / "core" / "src"))
    sys.path.insert(0, str(root / "packages" / "mcp-server" / "src"))

    output_path = root / args.output
    rendered = json.dumps(_build_spec(), indent=2, sort_keys=True) + "\n"

    if args.check:
        if not output_path.exists():
            print(f"❌ Missing OpenAPI artifact: {output_path}")
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            print(
                "❌ OpenAPI artifact is out of date. "
                "Run '.venv/bin/python scripts/generate_openapi.py' and commit the result."
            )
            return 1
        print(f"✅ OpenAPI artifact is up to date: {output_path}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"✅ OpenAPI artifact written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
