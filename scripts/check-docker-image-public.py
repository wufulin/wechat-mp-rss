#!/usr/bin/env python3
"""Verify that a Docker Hub image can be pulled anonymously."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from typing import Any


REPOSITORY = re.compile(
    r"^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)+$"
)
TAG = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]{0,127}$")
PLATFORM = re.compile(r"^[a-z0-9]+/[a-z0-9_]+(?:/[A-Za-z0-9._-]+)?$")
MANIFEST_ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)


class VerificationError(RuntimeError):
    """The image did not satisfy the anonymous-pull contract."""


def _request_json(
    request: urllib.request.Request,
    *,
    opener: Callable[..., Any],
    sleeper: Callable[[float], None],
    attempts: int,
    delay_seconds: float,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with opener(request, timeout=30) as response:
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise VerificationError(f"Expected a JSON object from {request.full_url}")
            return payload
        except (
            json.JSONDecodeError,
            TimeoutError,
            urllib.error.HTTPError,
            urllib.error.URLError,
        ) as error:
            last_error = error
            if attempt < attempts:
                sleeper(delay_seconds)

    raise VerificationError(
        f"Request failed after {attempts} attempt(s): {request.full_url}: {last_error}"
    )


def verify_public_image(
    repository: str,
    tag: str,
    required_platforms: Iterable[str],
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
    attempts: int = 10,
    delay_seconds: float = 3,
) -> set[str]:
    if not REPOSITORY.fullmatch(repository):
        raise VerificationError(f"Invalid Docker repository: {repository}")
    if not TAG.fullmatch(tag):
        raise VerificationError(f"Invalid Docker tag: {tag}")

    required = set(required_platforms)
    invalid_platforms = sorted(platform for platform in required if not PLATFORM.fullmatch(platform))
    if invalid_platforms:
        raise VerificationError(f"Invalid platform(s): {', '.join(invalid_platforms)}")
    if not required:
        raise VerificationError("At least one required platform must be specified")

    token_query = urllib.parse.urlencode(
        {
            "service": "registry.docker.io",
            "scope": f"repository:{repository}:pull",
        }
    )
    token_request = urllib.request.Request(
        f"https://auth.docker.io/token?{token_query}",
        headers={"User-Agent": "WeRSS-release-check/1"},
    )
    token_payload = _request_json(
        token_request,
        opener=opener,
        sleeper=sleeper,
        attempts=attempts,
        delay_seconds=delay_seconds,
    )
    token = token_payload.get("token") or token_payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise VerificationError("Docker Hub did not issue an anonymous pull token")

    manifest_request = urllib.request.Request(
        f"https://registry-1.docker.io/v2/{repository}/manifests/{tag}",
        headers={
            "Accept": MANIFEST_ACCEPT,
            "Authorization": f"Bearer {token}",
            "User-Agent": "WeRSS-release-check/1",
        },
    )
    manifest = _request_json(
        manifest_request,
        opener=opener,
        sleeper=sleeper,
        attempts=attempts,
        delay_seconds=delay_seconds,
    )
    available = {
        f"{platform['os']}/{platform['architecture']}"
        + (f"/{platform['variant']}" if platform.get("variant") else "")
        for descriptor in manifest.get("manifests", [])
        if isinstance(descriptor, dict)
        and isinstance((platform := descriptor.get("platform")), dict)
        and isinstance(platform.get("os"), str)
        and isinstance(platform.get("architecture"), str)
    }

    missing = sorted(required - available)
    if missing:
        raise VerificationError(
            "Anonymous manifest is missing required platform(s): " + ", ".join(missing)
        )
    return available


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Docker Hub repository, for example franklin888/werss")
    parser.add_argument("tag", help="Image tag to verify")
    parser.add_argument("platform", nargs="+", help="Required platform, for example linux/amd64")
    args = parser.parse_args()

    try:
        available = verify_public_image(args.repository, args.tag, args.platform)
    except VerificationError as error:
        print(f"Anonymous image verification failed: {error}", file=sys.stderr)
        return 1

    verified = ", ".join(sorted(set(args.platform)))
    print(f"Anonymous pull verified: docker.io/{args.repository}:{args.tag} ({verified})")
    print(f"Manifest platforms: {', '.join(sorted(available))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
