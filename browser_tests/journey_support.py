from __future__ import annotations

import sys
from pathlib import Path


def configure_sleeping_fixture_runtime(
    project_root: Path,
    *,
    sleep_seconds: int = 30,
) -> None:
    fixture_runtime = (
        Path(__file__).parents[1]
        / "harness/fixtures/minimal-python/aidd_fixture_runtime.py"
    ).resolve()
    wrapper = project_root / "browser_fixture_runtime.py"
    wrapper.write_text(
        "import runpy\n"
        "import time\n"
        "try:\n"
        f"    runpy.run_path({fixture_runtime.as_posix()!r}, run_name='__main__')\n"
        "except SystemExit as error:\n"
        "    if error.code not in (None, 0):\n"
        "        raise\n"
        f"time.sleep({sleep_seconds})\n",
        encoding="utf-8",
    )
    project_root.joinpath("aidd.example.toml").write_text(
        "[workspace]\n"
        'root = ".aidd"\n\n'
        "[runtime.generic_cli]\n"
        f'command = "{sys.executable} {wrapper.as_posix()}"\n'
        'mode = "adapter-flags"\n'
        'permission_policy = "full-access"\n\n'
        "[logging]\n"
        'mode = "both"\n\n'
        "[repair]\n"
        "max_attempts = 2\n",
        encoding="utf-8",
    )
