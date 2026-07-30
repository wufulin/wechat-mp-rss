from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DockerBuildConfigurationTests(unittest.TestCase):
    def test_full_stack_uses_docker_api_compatible_traefik(self):
        content = (REPOSITORY_ROOT / "docker-compose.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("image: traefik:v3.6.16", content)
        self.assertNotIn("image: traefik:v3.3\n", content)

    def test_dockerfiles_keep_expensive_browser_layer_before_application_code(self):
        for name in ("Dockerfile", "Dockerfile.cn"):
            with self.subTest(dockerfile=name):
                content = (REPOSITORY_ROOT / name).read_text(encoding="utf-8")
                self.assertLess(
                    content.index("python3 -m playwright install"),
                    content.index("COPY config.example.yaml config.yaml"),
                )
                self.assertIn("PLAYWRIGHT_BROWSERS_PATH=/ms-playwright", content)
                self.assertNotIn("浏览器安装失败，将在运行时安装", content)
                self.assertNotIn("浏览器仍未安装成功，启动时 install.sh 会再试", content)

    def test_china_dockerfile_uses_buildkit_dependency_caches_and_lockfile(self):
        content = (REPOSITORY_ROOT / "Dockerfile.cn").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("# syntax=docker/dockerfile:1.4\n"))
        self.assertIn(
            "--mount=type=cache,target=/root/.local/share/pnpm/store", content
        )
        self.assertIn("pnpm install --frozen-lockfile", content)
        self.assertIn("--mount=type=cache,target=/root/.cache/uv", content)

    def test_release_dockerfile_pins_multiarch_build_inputs(self):
        content = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "node:24.8.0-slim@sha256:"
            "cadbfafeb6baf87eaaffa40b3640209c4b7fd38cebde65059d15bc39cd636b85",
            content,
        )
        self.assertIn(
            "ghcr.io/astral-sh/uv:0.11.32@sha256:"
            "df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c",
            content,
        )
        self.assertIn(
            "python:3.11-slim@sha256:"
            "db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93",
            content,
        )

    def test_release_and_ci_caches_do_not_share_the_default_gha_scope(self):
        pull_request_workflow = (
            REPOSITORY_ROOT / ".github/workflows/pr-checks.yaml"
        ).read_text(encoding="utf-8")
        release_workflow = (
            REPOSITORY_ROOT / ".github/workflows/release-deploy.yaml"
        ).read_text(encoding="utf-8")

        scoped_cache = "type=gha,scope=werss-ci-amd64"
        self.assertIn(f"cache-from: {scoped_cache}", pull_request_workflow)
        self.assertIn(
            f"cache-to: {scoped_cache},mode=max", pull_request_workflow
        )
        self.assertIn(
            "type=registry,ref=docker.io/${{ vars.DOCKERHUB_USERNAME }}"
            "/werss:latest",
            release_workflow,
        )
        self.assertIn("cache-to: type=inline", release_workflow)
        self.assertNotIn("cache-to: type=gha,mode=max", release_workflow)


if __name__ == "__main__":
    unittest.main()
