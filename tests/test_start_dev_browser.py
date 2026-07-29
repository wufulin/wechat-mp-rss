import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class StartDevBrowserTests(unittest.TestCase):
    def test_edge_uses_chromium_install_and_preserves_configured_value(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            virtual_environment = temporary_path / "venv"
            fake_python = virtual_environment / "bin" / "python"
            fake_browser = temporary_path / "chromium"
            install_log = temporary_path / "install.log"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text(
                """#!/bin/bash
if [[ "$1" == "-" ]]; then
    printf '%s\\n' "$FAKE_BROWSER_PATH"
    exit 0
fi
if [[ "$1" == "-m" && "$2" == "playwright" && "$3" == "install" ]]; then
    printf '%s\\n' "$4" > "$FAKE_INSTALL_LOG"
    touch "$FAKE_BROWSER_PATH"
    chmod +x "$FAKE_BROWSER_PATH"
    exit 0
fi
exit 2
""",
                encoding="utf-8",
            )
            fake_python.chmod(fake_python.stat().st_mode | stat.S_IXUSR)

            environment = os.environ.copy()
            environment.update(
                {
                    "BROWSER_TYPE": "edge",
                    "FAKE_BROWSER_PATH": str(fake_browser),
                    "FAKE_INSTALL_LOG": str(install_log),
                }
            )
            completed = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; ensure_playwright_browser "$2"; '
                    'printf "CONFIGURED_BROWSER=%s\\n" "$BROWSER_TYPE"',
                    "bash",
                    str(REPOSITORY_ROOT / "start_dev.sh"),
                    str(virtual_environment),
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(install_log.read_text(encoding="utf-8").strip(), "chromium")
            self.assertIn("CONFIGURED_BROWSER=edge", completed.stdout)


if __name__ == "__main__":
    unittest.main()
