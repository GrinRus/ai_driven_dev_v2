from __future__ import annotations

from html.parser import HTMLParser
from importlib.resources import files

from aidd.cli.ui_assets import (
    _INDEX_HTML,
    _OPERATOR_CSS,
    _OPERATOR_JS,
    operator_static_asset_for_route,
    operator_static_asset_manifest,
)


class _StartTagCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


def _html_tags() -> list[tuple[str, dict[str, str | None]]]:
    collector = _StartTagCollector()
    collector.feed(_INDEX_HTML)
    return collector.tags


def _attrs_for(tag: str, **required: str) -> dict[str, str | None]:
    for candidate_tag, attrs in _html_tags():
        if candidate_tag != tag:
            continue
        if all(attrs.get(key) == value for key, value in required.items()):
            return attrs
    raise AssertionError(f"missing <{tag}> with attrs {required}")


def _asset_text(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_operator_assets_are_loaded_from_packaged_static_resources() -> None:
    static_files = files("aidd.cli.static")

    for asset in operator_static_asset_manifest():
        assert static_files.joinpath(asset.filename).read_text(encoding="utf-8") == _asset_text(
            asset.route
        )


def test_operator_static_asset_manifest_preserves_compatibility_routes() -> None:
    manifest = operator_static_asset_manifest()
    routes = {asset.route: asset for asset in manifest}
    filenames = {asset.filename for asset in manifest}

    assert len(routes) == len(manifest)
    assert {"index.html", "operator.css", "operator.js"}.issubset(filenames)
    assert "operator-api-state.js" in filenames
    assert "operator-main.js" in filenames
    assert routes["/"].filename == "index.html"
    assert routes["/operator.js"].content_type == "text/javascript; charset=utf-8"
    assert routes["/operator.css"].content_type == "text/css; charset=utf-8"
    assert _asset_text("/") == _INDEX_HTML
    assert _asset_text("/operator.js") == _OPERATOR_JS
    assert _asset_text("/operator.css") == _OPERATOR_CSS
    assert operator_static_asset_for_route("/missing.js") is None


def test_operator_js_bootstrap_loads_manifested_browser_modules() -> None:
    loader = _asset_text("/operator.js")
    module_routes = [
        asset.route
        for asset in operator_static_asset_manifest()
        if asset.route.startswith("/operator-") and asset.route != "/operator.js"
    ]

    assert module_routes
    for route in module_routes:
        assert f'"{route}"' in loader


def test_operator_script_modules_own_static_ui_surfaces() -> None:
    loader = _asset_text("/operator.js")
    api_state = _asset_text("/operator-api-state.js")
    shell = _asset_text("/operator-shell-rendering.js")
    artifacts = _asset_text("/operator-artifacts-documents.js")
    questions = _asset_text("/operator-questions.js")
    approvals = _asset_text("/operator-approvals-interventions.js")
    logs = _asset_text("/operator-logs-jobs.js")
    next_flow = _asset_text("/operator-next-flow-actions.js")
    cockpit = _asset_text("/operator-stage-cockpit.js")
    main = _asset_text("/operator-main.js")

    assert '"/operator-api-state.js"' in loader
    assert "const state = {" in api_state
    assert "async function api(path, options = {})" in api_state
    assert "function renderRuntimeSelector()" in shell
    assert "function renderStageRail()" in shell
    assert "async function renderArtifacts()" in artifacts
    assert "async function inspectArtifactReference({stage, key, path, kind})" in artifacts
    assert "function questionControlId(prefix, questionId, index)" in questions
    assert "async function answerAndResume(questionId)" in questions
    assert "async function renderApprovals()" in approvals
    assert "async function submitIntervention()" in approvals
    assert "async function renderLogs()" in logs
    assert "async function startJobPolling(job)" in logs
    assert "async function startWorkflow()" in next_flow
    assert "async function handleNextAction()" in next_flow
    assert "async function renderCockpit()" in cockpit
    assert "function renderActivityTable()" in cockpit
    assert 'document.addEventListener("click"' in main
    assert "refresh();" in main


def test_index_html_exposes_named_operator_landmarks() -> None:
    assert _attrs_for("header", **{"aria-label": "Operator controls"})
    assert _attrs_for("main", **{"aria-label": "Operator workspace"})
    assert _attrs_for("aside", **{"aria-label": "Workflow navigation"})
    assert _attrs_for("section", **{"aria-label": "Stage cockpit"})
    assert _attrs_for("aside", **{"aria-label": "Run details"})
    assert _attrs_for("section", **{"aria-label": "Activity and recent artifacts"})
    assert _attrs_for("nav", id="stageRail", **{"aria-label": "Workflow stages"})


def test_index_html_exposes_tab_and_panel_semantics() -> None:
    assert _attrs_for("div", role="tablist", **{"aria-label": "Stage cockpit views"})
    overview_tab = _attrs_for("button", id="tab-overview", role="tab")
    questions_tab = _attrs_for("button", id="tab-questions", role="tab")
    panel = _attrs_for("div", id="cockpitContent", role="tabpanel")

    assert overview_tab["aria-selected"] == "true"
    assert overview_tab["aria-controls"] == "cockpitContent"
    assert questions_tab["aria-selected"] == "false"
    assert questions_tab["aria-controls"] == "cockpitContent"
    assert panel["aria-labelledby"] == "tab-overview"
    assert panel["tabindex"] == "0"


def test_index_html_exposes_runtime_and_loading_contracts() -> None:
    runtime_label = _attrs_for("label", **{"class": "runtime-picker", "for": "runtimeSelect"})
    runtime_select = _attrs_for("select", id="runtimeSelect")
    loading_state = _attrs_for("div", **{"class": "empty-state loading-state"})

    assert runtime_label["for"] == runtime_select["id"]
    assert loading_state["class"] == "empty-state loading-state"


def test_operator_script_keeps_dynamic_accessibility_contracts() -> None:
    assert "function questionControlId(prefix, questionId, index)" in _asset_text(
        "/operator-questions.js"
    )
    assert 'aria-describedby="${questionTextId}"' in _asset_text("/operator-questions.js")
    assert 'aria-current="${isActive ? "step" : "false"}' in _asset_text(
        "/operator-shell-rendering.js"
    )
    assert 'button.setAttribute("aria-selected", isActive ? "true" : "false");' in _asset_text(
        "/operator-api-state.js"
    )
    assert "renderTruncationNotice(" in _asset_text("/operator-artifacts-documents.js")
    assert "function scrollActiveStageIntoView()" in _asset_text("/operator-shell-rendering.js")


def test_operator_css_keeps_focus_and_screen_reader_contracts() -> None:
    assert ".sr-only" in _OPERATOR_CSS
    assert "button:focus-visible" in _OPERATOR_CSS
    assert "outline: 3px solid var(--focus-ring)" in _OPERATOR_CSS
    assert ".truncation-notice" in _OPERATOR_CSS
    assert ".saved-answer" in _OPERATOR_CSS
