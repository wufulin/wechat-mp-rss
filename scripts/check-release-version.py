#!/usr/bin/env python3
"""Validate that all user-visible WeRSS version declarations agree."""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def core_version() -> str:
    tree = ast.parse((ROOT / "core/ver.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError("core/ver.py does not define a string VERSION")


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def frontend_version() -> str:
    package = json.loads((ROOT / "web_ui/package.json").read_text(encoding="utf-8"))
    return str(package["version"])


def readme_version() -> str:
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"shields\.io/badge/version-([0-9]+\.[0-9]+\.[0-9]+)-", content)
    if not match:
        raise ValueError("README.md does not contain the version badge")
    return match.group(1)


def main() -> int:
    expected = sys.argv[1].removeprefix("v") if len(sys.argv) > 1 else None
    versions = {
        "core/ver.py": core_version(),
        "pyproject.toml": project_version(),
        "web_ui/package.json": frontend_version(),
        "README.md": readme_version(),
    }

    canonical = expected or next(iter(versions.values()))
    if not SEMVER.fullmatch(canonical):
        print(f"Invalid release version: {canonical}", file=sys.stderr)
        return 1

    mismatches = {path: value for path, value in versions.items() if value != canonical}
    if mismatches:
        print(f"Expected release version {canonical}, found:", file=sys.stderr)
        for path, value in mismatches.items():
            print(f"  {path}: {value}", file=sys.stderr)
        return 1

    print(f"Release version validated: {canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
