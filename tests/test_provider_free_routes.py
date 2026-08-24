from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from browser_tests.state_fixtures import BROWSER_FIXTURE_STATES, build_browser_state_fixture

_PROVIDER_FREE_FIXTURES = set(BROWSER_FIXTURE_STATES) | {
    "history",
    "implementation-task-failed",
    "implementation-finalization-failed",
    "implementation-finalized",
    "review-qa-rejected",
}


def _provider_free_manifest(repository_root: Path) -> list[dict[str, object]]:
    manifest_path = repository_root / "src/aidd/cli/static/operator-surface-parity.js"
    script = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const context = vm.createContext({console});
const payload = new vm.Script(
  `${source}\n;JSON.stringify(PROVIDER_FREE_ROUTE_MANIFEST);`,
).runInContext(context);
process.stdout.write(payload);
"""
    completed = subprocess.run(
        ("node", "-e", script, manifest_path.as_posix()),
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_provider_free_manifest_maps_target_files_to_loadable_local_fixtures(
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    entries = _provider_free_manifest(repository_root)

    assert len(entries) == 13
    assert [str(entry["target"]) for entry in entries] == [
        f"{index:02d}-{name}.png"
        for index, name in enumerate(
            (
                "project-work-items",
                "create-work-item",
                "work-item-launch",
                "task-workspace",
                "active-task-run",
                "decision-workbench",
                "validation-repair",
                "markdown-workspace",
                "implementation-review",
                "review-qa-remediation",
                "run-history",
                "flow-complete",
                "mobile-decision",
            ),
            start=1,
        )
    ]

    for entry in entries:
        assert entry["provider"] == "local"
        assert entry["requiresLiveProvider"] is False
        assert entry["credentialMode"] == "none"
        assert entry["clockMode"] == "fixed"
        assert entry["idMode"] == "deterministic"
        route = str(entry["route"])
        assert route.startswith("?")
        parsed = urlsplit(route)
        assert parsed.scheme == ""
        assert parsed.netloc == ""
        query = parse_qs(parsed.query)
        route_intent = str(entry["routeIntent"])
        if route_intent == "setup":
            assert query == {"ui": ["studio"]}
        else:
            assert query.get("mode") == [route_intent]

        context = entry["context"]
        assert isinstance(context, dict)
        work_item = str(context.get("work_item", "WI-BROWSER"))
        run_id = str(context.get("run", "run-browser"))
        fixture_name = str(entry["fixture"])
        assert fixture_name in _PROVIDER_FREE_FIXTURES
        fixture = build_browser_state_fixture(
            tmp_path / str(entry["id"]),
            fixture_name,
            work_item=work_item,
            run_id=run_id,
            route_intent_override=route_intent,
        )
        assert fixture.project_root.is_relative_to(tmp_path)
        assert fixture.expected_route_intent == route_intent
        assert fixture.api_path.startswith("/api/")
        assert all(token not in route for token in ("Date", "Math", "random", "timestamp"))
