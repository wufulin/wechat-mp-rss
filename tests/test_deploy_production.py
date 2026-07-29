import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = ROOT / "scripts/deploy-production.sh"


class DeployProductionScriptTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.deploy_dir = self.root / "deploy"
        self.bin_dir = self.root / "bin"
        self.deploy_dir.mkdir()
        self.bin_dir.mkdir()
        (self.deploy_dir / ".env").write_text("POSTGRES_DB=werss\n", encoding="utf-8")
        self.compose_candidate = self.root / "docker-compose.yml"
        self.compose_candidate.write_text("services: {}\n", encoding="utf-8")
        self.docker_log = self.root / "docker.log"

        fake_docker = self.bin_dir / "docker"
        fake_docker.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                set -euo pipefail
                printf '%s\n' "$*" >> "$FAKE_DOCKER_LOG"
                case "$*" in
                  *" ps --status running --quiet postgres")
                    exit 0
                    ;;
                  *" exec -T werss python3 -c "*)
                    printf '%s\n' "$FAKE_APP_VERSION"
                    ;;
                esac
                """
            ),
            encoding="utf-8",
        )
        fake_docker.chmod(0o755)

    def tearDown(self):
        self.tempdir.cleanup()

    def run_deploy(self, app_version="1.1.6"):
        env = os.environ.copy()
        env.update(
            {
                "COMPOSE_PROJECT_NAME": "werss-test",
                "DEPLOY_DIR": str(self.deploy_dir),
                "FAKE_APP_VERSION": app_version,
                "FAKE_DOCKER_LOG": str(self.docker_log),
                "PATH": f"{self.bin_dir}:{env['PATH']}",
            }
        )
        return subprocess.run(
            ["bash", str(DEPLOY_SCRIPT), "1.1.6", str(self.compose_candidate)],
            check=False,
            capture_output=True,
            env=env,
            text=True,
        )

    def test_success_installs_compose_and_release_version(self):
        result = self.run_deploy()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.deploy_dir / ".release.env").read_text(encoding="utf-8"),
            "WERSS_IMAGE_TAG=1.1.6\n",
        )
        self.assertEqual(
            (self.deploy_dir / "docker-compose.yml").read_text(encoding="utf-8"),
            "services: {}\n",
        )
        self.assertIn("--no-build --wait", self.docker_log.read_text(encoding="utf-8"))

    def test_version_mismatch_uses_previous_release_for_rollback(self):
        (self.deploy_dir / "docker-compose.yml").write_text(
            "services:\n  werss: {}\n",
            encoding="utf-8",
        )
        (self.deploy_dir / ".release.env").write_text(
            "WERSS_IMAGE_TAG=1.1.5\n",
            encoding="utf-8",
        )

        result = self.run_deploy(app_version="9.9.9")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Version check failed", result.stderr)
        log = self.docker_log.read_text(encoding="utf-8")
        self.assertIn(".rollback/docker-compose.yml", log)
        self.assertIn(".rollback/.release.env", log)


if __name__ == "__main__":
    unittest.main()
