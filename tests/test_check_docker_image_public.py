import importlib.util
import io
import json
import unittest
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-docker-image-public.py"
SPEC = importlib.util.spec_from_file_location("check_docker_image_public", SCRIPT)
assert SPEC and SPEC.loader
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def json_response(payload):
    return FakeResponse(json.dumps(payload).encode())


class DockerImagePublicCheckTests(unittest.TestCase):
    def test_accepts_anonymous_multi_platform_manifest(self):
        responses = iter(
            (
                json_response({"token": "anonymous-token"}),
                json_response(
                    {
                        "mediaType": "application/vnd.oci.image.index.v1+json",
                        "manifests": [
                            {"platform": {"os": "linux", "architecture": "amd64"}},
                            {"platform": {"os": "linux", "architecture": "arm64"}},
                            {"platform": {"os": "unknown", "architecture": "unknown"}},
                        ],
                    }
                ),
            )
        )
        requests = []

        def opener(request, timeout):
            requests.append((request, timeout))
            return next(responses)

        platforms = CHECK.verify_public_image(
            "franklin888/werss",
            "1.1.6",
            ("linux/amd64", "linux/arm64"),
            opener=opener,
            attempts=1,
        )

        self.assertIn("linux/amd64", platforms)
        self.assertIn("linux/arm64", platforms)
        self.assertNotIn("Authorization", dict(requests[0][0].header_items()))
        self.assertEqual(
            dict(requests[1][0].header_items())["Authorization"],
            "Bearer anonymous-token",
        )

    def test_rejects_manifest_without_required_platform(self):
        responses = iter(
            (
                json_response({"token": "anonymous-token"}),
                json_response(
                    {
                        "manifests": [
                            {"platform": {"os": "linux", "architecture": "amd64"}}
                        ]
                    }
                ),
            )
        )

        with self.assertRaisesRegex(CHECK.VerificationError, "linux/arm64"):
            CHECK.verify_public_image(
                "franklin888/werss",
                "1.1.6",
                ("linux/amd64", "linux/arm64"),
                opener=lambda request, timeout: next(responses),
                attempts=1,
            )

    def test_rejects_registry_denial_for_anonymous_token(self):
        responses = iter(
            (
                json_response({"token": "anonymous-token"}),
                urllib.error.HTTPError(
                    "https://registry-1.docker.io/v2/franklin888/werss/manifests/1.1.6",
                    401,
                    "Unauthorized",
                    {},
                    io.BytesIO(b""),
                ),
            )
        )

        def opener(request, timeout):
            response = next(responses)
            if isinstance(response, Exception):
                raise response
            return response

        with self.assertRaisesRegex(CHECK.VerificationError, "401"):
            CHECK.verify_public_image(
                "franklin888/werss",
                "1.1.6",
                ("linux/amd64", "linux/arm64"),
                opener=opener,
                attempts=1,
            )


if __name__ == "__main__":
    unittest.main()
