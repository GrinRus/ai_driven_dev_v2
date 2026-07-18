from __future__ import annotations

import re
from html.parser import HTMLParser
from importlib.resources import files

from aidd.cli.ui_assets import (
    _INDEX_HTML,
    _OPERATOR_CSS,
    _OPERATOR_JS,
    operator_static_asset_for_route,
    operator_static_asset_manifest,
)

_MOBILE_PRIORITY_SELECTOR = (
    '.operator-shell[data-mobile-priority-layout="context-decision-document-drilldown"]'
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


def _next_flow_assets() -> str:
    return "\n".join(
        (
            _asset_text("/operator-next-flow-actions.js"),
            _asset_text("/operator-next-flow-view.js"),
        )
    )


def _dashboard_actions() -> str:
    return _asset_text("/operator-dashboard-actions.js")


def _assert_contains_all(text: str, expected: tuple[str, ...]) -> None:
    missing = [item for item in expected if item not in text]
    assert not missing


def _js_bundle() -> str:
    return "\n".join(
        _asset_text(asset.route)
        for asset in operator_static_asset_manifest()
        if asset.content_type == "text/javascript; charset=utf-8"
    )


def _css_bundle() -> str:
    return "\n".join(
        _asset_text(asset.route)
        for asset in operator_static_asset_manifest()
        if asset.content_type == "text/css; charset=utf-8"
    )


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
    assert {
        "index.html",
        "operator.css",
        "operator-tokens.css",
        "operator-base.css",
        "operator-layout.css",
        "operator-components.css",
        "operator-responsive.css",
        "operator.js",
    }.issubset(filenames)
    assert "operator-api-state.js" in filenames
    assert "operator-presentation.js" not in filenames
    assert "operator-surface-parity.js" in filenames
    assert "operator-dashboard-actions.js" in filenames
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
        if asset.content_type == "text/javascript; charset=utf-8"
        and asset.route.startswith("/operator-")
        and asset.route != "/operator.js"
    ]

    assert module_routes
    for route in module_routes:
        assert f'"{route}"' in loader

    assert loader.index('"/operator-surface-parity.js"') < loader.index(
        '"/operator-api-state.js"'
    )


def test_operator_assets_have_no_legacy_renderer_boundary() -> None:
    bundle = _js_bundle()
    assert "operator-presentation.js" not in _OPERATOR_JS
    for obsolete in (
        "selectSurfaceRenderer",
        "resolveSurfaceRenderer",
        "rollbackRenderer",
        "renderLegacy",
        "aiddPresentation",
        "presentationSelector",
        "presentationEffective",
    ):
        assert obsolete not in bundle


def test_operator_surface_parity_manifest_is_complete_and_policy_free() -> None:
    parity = _asset_text("/operator-surface-parity.js")

    _assert_contains_all(
        parity,
        (
            'new Set(["parity_closed"])',
            "const SURFACE_PARITY_MANIFEST = Object.freeze([",
            'id: "guided-setup"',
            'id: "inbox"',
            'id: "active-studio"',
            'id: "question-recovery"',
            'id: "runtime-validation-recovery"',
            'id: "review-qa"',
            'id: "history"',
            'id: "flow-complete"',
            'journey: "W36-E7-S1-T12"',
            "function validateSurfaceParityManifest(",
        ),
    )
    assert "fetch(" not in parity
    assert "postJson(" not in parity


def test_operator_css_loader_imports_manifested_layers() -> None:
    loader = _asset_text("/operator.css")
    layer_routes = [
        asset.route
        for asset in operator_static_asset_manifest()
        if asset.content_type == "text/css; charset=utf-8" and asset.route != "/operator.css"
    ]

    assert layer_routes == [
        "/operator-tokens.css",
        "/operator-base.css",
        "/operator-layout.css",
        "/operator-components.css",
        "/operator-responsive.css",
    ]
    for route in layer_routes:
        assert f'@import url("{route}")' in loader


def test_operator_html_exposes_four_mode_navigation_without_quick_links() -> None:
    assert _INDEX_HTML.count('role="tab"') == 4
    for mode in ("work", "recovery", "evidence", "history"):
        assert f'data-tab="{mode}"' in _INDEX_HTML
        assert f'id="tab-{mode}"' in _INDEX_HTML
    for legacy_tab in (
        "overview",
        "questions",
        "validation",
        "timeline",
        "artifacts",
        "logs",
        "request",
    ):
        assert f'data-tab="{legacy_tab}"' not in _INDEX_HTML
    assert 'class="quick-link"' not in _INDEX_HTML


def test_operator_responsive_css_prevents_artifact_graph_mobile_overflow() -> None:
    responsive = _asset_text("/operator-responsive.css")

    assert ".evidence-graph-screen," in responsive
    assert ".evidence-artifact-browser," in responsive
    assert ".artifact-inspector {" in responsive
    assert "max-width: 100%;" in responsive
    assert "min-width: 0;" in responsive
    assert ".evidence-table-wrap {" in responsive
    assert "overflow-x: auto;" in responsive


def test_operator_responsive_css_keeps_mobile_topbar_status_readable() -> None:
    responsive = _asset_text("/operator-responsive.css")

    assert ".brand-meta {" in responsive
    assert ".brand-meta code {" in responsive
    assert ".top-status {" in responsive
    assert "flex-wrap: nowrap;" in responsive
    assert ".top-actions {" in responsive
    assert ".runtime-picker {" in responsive
    assert ".runtime-picker select {" in responsive
    assert ".topbar .status-chip," in responsive
    assert ".topbar #runChip," in responsive
    assert ".topbar #workItemChip," in responsive
    assert ".topbar #localStatus {" in responsive
    assert "white-space: normal;" in responsive
    assert "text-overflow: clip;" in responsive
    assert "overflow-wrap: anywhere;" in responsive
    assert ".right-sidebar .maintenance-overflow {" in responsive
    assert "position: fixed;" in responsive
    assert ".path-line {" in responsive


def test_operator_responsive_css_keeps_mobile_stage_rail_inside_viewport() -> None:
    responsive = _asset_text("/operator-responsive.css")
    api_state = _asset_text("/operator-api-state.js")
    shell = _asset_text("/operator-shell-rendering.js")

    assert ".stage-list {" in responsive
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in responsive
    assert "overflow-x: visible;" in responsive
    assert "scroll-snap-type: none;" in responsive
    assert ".stage-card {" in responsive
    assert "min-width: 0;" in responsive
    assert "width: 100%;" in responsive
    assert ".next-action-controls {" in responsive
    assert ".global-next-action-strip .next-button {" in responsive
    assert "function postStageNextActionIsPrimary(" in api_state
    assert "post-stage-next-action-mode" in api_state
    assert _MOBILE_PRIORITY_SELECTOR in responsive
    assert 'document.body.classList.contains("post-stage-next-action-mode")' in shell


def test_operator_workbench_css_wraps_path_lines_without_document_overflow() -> None:
    components = _asset_text("/operator-components.css")

    assert ".artifact-viewer {" in components
    assert ".stage-document-workbench {" in components
    assert ".workbench-main {" in components
    assert ".viewer-header > div:first-child {" in components
    assert ".viewer-header .path-line," in components
    assert ".stage-document-workbench .path-line {" in components
    assert "overflow-wrap: anywhere;" in components
    assert "text-overflow: clip;" in components
    assert "white-space: normal;" in components
    assert "word-break: break-word;" in components


def test_operator_responsive_css_prevents_activity_table_mobile_overflow() -> None:
    responsive = _asset_text("/operator-responsive.css")

    assert "@media (max-width: 1120px)" in responsive
    assert ".request-change-grid," in responsive
    assert ".activity-panel .table-wrap {" in responsive
    assert "overflow-x: hidden;" in responsive
    assert ".activity-panel .activity-table {" in responsive
    assert "table-layout: fixed;" in responsive
    assert ".activity-panel .activity-table th," in responsive
    assert ".activity-panel .activity-table td {" in responsive
    assert "overflow-wrap: anywhere;" in responsive
    assert "word-break: break-word;" in responsive
    assert ".activity-panel .activity-table th:nth-child(1)," in responsive
    assert ".activity-panel .activity-table th:nth-child(2)," in responsive
    assert ".activity-panel .activity-table th:nth-child(3)," in responsive


def test_operator_script_modules_own_static_ui_surfaces() -> None:
    loader = _asset_text("/operator.js")
    api_state = _asset_text("/operator-api-state.js")
    dashboard_actions = _dashboard_actions()
    shell = _asset_text("/operator-shell-rendering.js")
    artifacts = _asset_text("/operator-artifacts-documents.js")
    questions = _asset_text("/operator-questions.js")
    approvals = _asset_text("/operator-approvals-interventions.js")
    logs = _asset_text("/operator-logs-jobs.js")
    next_flow_view = _asset_text("/operator-next-flow-view.js")
    control_center = _asset_text("/operator-control-center.js")
    onboarding = _asset_text("/operator-onboarding.js")
    cockpit = _asset_text("/operator-stage-cockpit.js")
    main = _asset_text("/operator-main.js")

    assert '"/operator-api-state.js"' in loader
    assert "const state = {" in api_state
    assert "function stageRetrySummary(item)" in api_state
    assert "open Recovery for repair and retry history" in api_state
    assert "function secondsLabel(value)" in api_state
    assert "function runtimeOutputFreshnessLabel(job)" in api_state
    assert "function activeJobIsLive(job = state.activeJobStatus)" in api_state
    assert "function activeJobPayloadIsLive(job)" in api_state
    assert "async function recoverActiveJobFromDashboard(job)" in api_state
    assert "function syncLiveJobBodyClass()" in api_state
    assert "function syncExternalRunningBodyClass()" in api_state
    assert "function isNonBlockingValidationNotice(finding)" in api_state
    assert "function actionableValidationFindings(validation)" in api_state
    assert "function nonBlockingValidationNotices(validation)" in api_state
    assert "function primaryValidationFindingForValidation(validation)" in api_state
    assert "async function api(path, options = {})" in api_state
    assert "function renderRuntimeSelector()" in shell
    assert "function renderStageRail()" in shell
    assert "Retry history" in shell
    assert "projectPath.title = projectRoot;" in shell
    assert "workItemChip.title = workItemLabel;" in shell
    assert "runChip.title = runLabel;" in shell
    assert "async function renderArtifacts()" in artifacts
    assert "async function inspectArtifactReference({stage, key, path, kind})" in artifacts
    assert "function focusArtifactWorkbench()" in artifacts
    assert "workbench.scrollIntoView" in artifacts
    assert "workbench.focus({preventScroll: true})" in artifacts
    assert "function questionControlId(prefix, questionId, index)" in questions
    assert "function renderInterviewSummary(view)" in questions
    assert "function renderBlockedStageContext(view)" in questions
    assert "async function answerAndResume(questionId)" in questions
    assert "async function resumeAfterAnswers()" in questions
    assert "async function renderApprovals()" in approvals
    assert "async function submitIntervention()" in approvals
    assert 'kind: "stage-interact"' in approvals
    assert 'operatorMutationKey(\n    "answer"' in questions
    assert "async function renderLogs()" in logs
    assert "async function startJobPolling(job)" in logs
    assert "function renderOnboarding()" in onboarding
    assert "function syncOnboardingCreateActionState()" in onboarding
    assert "async function fetchDashboard()" in dashboard_actions
    assert "async function fetchProjectHome(workItem = \"\")" in dashboard_actions
    assert "async function startWorkflow()" in dashboard_actions
    assert (
        "async function guardedJobLaunch({kind, components, controls, execute})"
        in dashboard_actions
    )
    assert "readWinner: readRunMutationWinner" in dashboard_actions
    assert 'kind: "remediation-rerun"' in dashboard_actions
    assert 'kind: "remediation-launch"' in control_center
    assert "async function handleNextAction()" in dashboard_actions
    assert "function renderStudioFlowCompleteState()" in next_flow_view
    assert "function renderStudioHistory(timeline)" in _asset_text("/operator-history.js")
    assert "async function renderCockpit()" in cockpit
    assert "function renderRecoveryActionBand(diagnostics)" in cockpit
    assert "function renderRepairTimeline(validation)" in cockpit
    assert "function renderResolvedRepairSummary(validation)" in cockpit
    assert "function renderRuntimePartialEvidence(firstFailure)" in cockpit
    assert "return renderActiveStudio();" in cockpit
    assert 'state.activeTab === "history"' in cockpit
    assert "function renderActivityTable()" in cockpit
    assert "revealCockpitOnMobile();" in cockpit
    assert "revealNextFlowWizardOnMobile();" in cockpit
    assert 'document.addEventListener("click"' in main
    assert 'event.target.closest("[data-refresh-dashboard]")' in main
    assert "requestCockpitReveal();" in main
    assert "refresh();" in main


def test_studio_history_uses_typed_frames_without_runtime_mutation() -> None:
    history = _asset_text("/operator-history.js")
    responsive = _asset_text("/operator-responsive.css")
    cockpit = _asset_text("/operator-stage-cockpit.js")
    main = _asset_text("/operator-main.js")

    _assert_contains_all(
        history,
        (
            "async function loadStudioHistoryTimeline()",
            "timeline.frames",
            "function renderStudioHistory(timeline)",
            "function renderStudioRunComparisonPanel()",
            "function renderActiveRunComparisonPanel()",
            'data-studio-history',
            'data-history-frame=',
            'data-history-return-live',
            'data-history-evidence-path=',
            "active runtime is not stopped",
            'data-comparison-evidence-path=',
            "snapshot unavailable",
            "History will not reconstruct it",
            "function renderStudioHistoryLineage()",
            "data-studio-history-lineage",
            'data-operator-route-intent="parent-run"',
            'data-operator-route-intent="child-work-item"',
            "function renderStudioHistoryArchive()",
            "data-studio-history-archive",
            "append-only visibility disposition",
            'data-operator-route-intent="run-artifacts"',
        ),
    )
    assert "postJson(" not in history
    _assert_contains_all(
        responsive,
        (
            ".history-filmstrip-frames",
            "grid-template-columns: minmax(0, 1fr)",
            ".history-frame",
            "overflow: visible",
            "min-height: 44px",
        ),
    )
    assert "return renderStudioHistory(await loadStudioHistoryTimeline());" in cockpit
    assert 'state.historyAutoFollow = false' in main
    assert 'state.historyAutoFollow = true' in main
    assert "renderActiveRunComparisonPanel()" in _asset_text(
        "/operator-next-flow-actions.js"
    )


def test_studio_flow_complete_uses_only_core_recommendation() -> None:
    view = _asset_text("/operator-next-flow-view.js")
    studio = _asset_text("/operator-active-studio.js")
    parity = _asset_text("/operator-surface-parity.js")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        view,
        (
            "function studioFlowCompleteEligibility",
            "terminalHandoffRecommendation(handoff)",
            "function renderStudioFlowCompleteState()",
            "data-studio-flow-complete",
            "data-core-recommended-outcome",
            "Other next actions",
        ),
    )
    assert "return renderStudioFlowCompleteState();" in studio
    assert 'id: "flow-complete"' in parity
    flow_entry = parity.split('id: "flow-complete"', 1)[1].split("},", 1)[0]
    assert 'rollout: "parity_closed"' in flow_entry
    _assert_contains_all(
        responsive,
        (
            ".studio-flow-complete",
            ".studio-flow-complete-other > summary",
            "min-height: 44px",
        ),
    )
    _assert_contains_all(
        view,
        (
            "function renderStudioNextFlowWizard()",
            "renderNextFlowSourceSelection()",
            "data-studio-next-flow-action",
        ),
    )
    assert "state.nextFlowWizard.active" in studio
    assert "renderStudioNextFlowWizard()" in studio
    actions = _asset_text("/operator-next-flow-actions.js")
    _assert_contains_all(
        actions,
        (
            'action === "clone-flow"',
            'postJson("/api/next-flow/clone-draft/create"',
            'fetch("/api/next-flow/preflight"',
            'relationship: wizard.action === "clone-flow" ? "clone" : "follow-up"',
        ),
    )
    _assert_contains_all(
        view,
        (
            "function renderEvalBatchHandoff()",
            "operator-selected local manifest",
            "uv run aidd eval execute <scenario-path> --root .aidd",
            "data-eval-handoff-command",
        ),
    )
    eval_action = actions.split("async function openEvalBatchHandoff()", 1)[1].split(
        "function cloneDraftFromPayload", 1
    )[0]
    assert "postJson(" not in eval_action
    _assert_contains_all(
        actions,
        (
            "async function archiveCompletedRun()",
            'postJson("/api/next-flow/archive"',
            "state.dashboard = payload.dashboard",
        ),
    )
    _assert_contains_all(
        view,
        (
            "function renderArchiveConfirmation()",
            "archive metadata only",
            "The terminal run stays immutable",
            "Confirm Archive Run",
        ),
    )


def test_operator_state_and_dashboard_assets_keep_runtime_and_tab_contracts() -> None:
    api_state = "\n".join((_asset_text("/operator-api-state.js"), _dashboard_actions()))

    _assert_contains_all(
        api_state,
        (
            'const STAGES = ["idea", "research", "plan", "review-spec", "tasklist", '
            '"implement", "review", "qa"];',
            "const NON_BLOCKING_VALIDATION_NOTICE_CODES = new Set(",
            '"STRUCT-OUTPUT-PROMOTED"',
            'activeRunId: ""',
            'selectedEvidenceNodeId: ""',
            'selectedEvidenceEdgeId: ""',
            "nextFlowWizard: {",
            'step: "sources"',
            "sourceFindings: null",
            "followUpDraft: null",
            "selectedSourceIds: []",
            "launchReadinessChecking: false",
            'launchReadinessError: ""',
            "projectHome: null",
            "pendingCockpitReveal: false",
            "pendingNextFlowWizardReveal: false",
            "activeStageExplicit: false",
            "const OPERATOR_MODES",
            "const LEGACY_TAB_TO_MODE",
            "const RECOVERY_NEXT_ACTIONS",
            'activeTab: "work"',
            'workDetail: "overview"',
            'recoveryDetail: "summary"',
            'evidenceDetail: "artifacts"',
            'logViewMode: "summary"',
            "const VALID_TABS",
            "function normalizeOperatorMode(tab)",
            "function setOperatorMode(tab)",
            "function isRecoveryNextAction(action)",
            "function dashboardRuntimeRecoveryAction()",
            'action?.action === "inspect-runtime-log"',
            "action.enabled !== false",
            "function activeModeIsEvidenceLog()",
            "function requestCockpitReveal()",
            "function requestNextFlowWizardReveal()",
            "function scrollCockpitToTopOnMobile()",
            "function revealCockpitOnMobile()",
            "function scrollNextFlowWizardToTopOnMobile()",
            "function revealNextFlowWizardOnMobile()",
            "window.matchMedia(\"(max-width: 760px)\").matches",
            "window.scrollTo({top: Math.max(0, target), behavior: \"auto\"});",
            "window.requestAnimationFrame(scrollCockpitToTopOnMobile);",
            "window.setTimeout(scrollCockpitToTopOnMobile, 80);",
            "function applyOperatorModeBodyClass()",
            "external-running-stage-mode",
            "evidence-log-mode",
            "terminal-handoff-mode",
            "terminal-repair-mode",
            "function initializeStateFromLocation()",
            "decodeOperatorRoute(window.location.search).value",
            "function applyOperatorRoute(route)",
            "STAGES.includes(route.stage)",
            "state.activeStageExplicit = true;",
            "function operatorRouteSnapshot()",
            "function syncLocationState({historyMode = \"replace\"} = {})",
            'window.history[method]({aiddOperatorRoute: true}, "", next);',
            "function sourceFindingsUrl()",
            "function projectHomeUrl(workItem = \"\")",
            "/api/next-flow/source-findings",
            "/api/project-home",
            "readinessLoading: true",
            'readinessError: ""',
            "function escapeHtml(value)",
            "function compactPath(value, maxLength = 56)",
            "function pathLine(value, maxLength = 56)",
            "function renderValidationFindingSummary(finding, {compact = false} = {})",
            "data-finding-code",
            "data-finding-category",
            "data-finding-path",
            "data-finding-line",
            'data-finding-provenance="validator-report"',
            "function primaryValidationFinding()",
            "const occurrenceCount = Number(finding.occurrence_count || 1);",
            "validation-finding-hint",
            "What to do",
            'title="${escapeHtml(text)}"',
            "${escapeHtml(compactPath(text, maxLength))}",
            "async function fetchDashboard()",
            "await recoverActiveJobFromDashboard(payload.active_job);",
            "await pollActiveJob();",
            "state.activeJobCursor = 0;",
            "async function fetchProjectHome(workItem = \"\")",
            "dashboardUrl()",
            "if (state.activeStageExplicit) params.set(\"stage\", state.activeStage);",
            "/api/dashboard",
            (
                "const viewedStage = state.dashboard.active_stage_view?.stage "
                "|| state.dashboard.active_stage;"
            ),
            "if (viewedStage && STAGES.includes(viewedStage)) {",
            "state.activeStage = viewedStage;",
            'state.activeRunId = state.dashboard.run?.run_id || "";',
            'isRecoveryNextAction(nextAction) && state.activeTab === "work"',
            'state.activeTab = "recovery";',
            'state.recoveryDetail = "questions";',
            'state.recoveryDetail = "validation";',
            "state.dashboard.first_failure",
            "dashboardRuntimeRecoveryAction()",
            'state.recoveryDetail = "logs";',
            "requestCockpitReveal();",
            "version.startsWith(\"v\") ? version : `v${version || \"dev\"}`",
            'api("/api/runtime-readiness")',
            'if (element.textContent === message) element.textContent = "";',
            'button.setAttribute("aria-selected", isActive ? "true" : "false");',
            'content.setAttribute("aria-labelledby", `tab-${state.activeTab}`);',
        ),
    )
    assert (
        "&& dashboardRuntimeRecoveryAction()\n"
        "  ) {\n"
        '    state.activeTab = "recovery";\n'
        '    state.recoveryDetail = "summary";'
    ) in api_state


def test_operator_onboarding_static_contract_syncs_create_action_state() -> None:
    onboarding = _asset_text("/operator-onboarding.js")
    main = _asset_text("/operator-main.js")

    _assert_contains_all(
        onboarding,
        (
            "function onboardingCanCreate()",
            "function renderProjectSetEditor()",
            "function renderOnboardingAdvanced()",
            '<details class="onboarding-advanced">',
            "<summary>Advanced configuration</summary>",
            "function updateProjectSetRow(index, field, value)",
            "function addProjectSetRow()",
            "function removeProjectSetRow(index)",
            "function syncOnboardingCreateActionState()",
            "async function resumeProjectHomeWorkItem(workItem, options = {})",
            'state.activeRunId = item?.latest_run?.run_id || "";',
            'state.selectedEvidenceNodeId = "";',
            'state.selectedEvidenceEdgeId = "";',
            'document.getElementById("onboardingCreateForm")',
            'form.querySelector(\'button[type="submit"]\')',
            "button.disabled = !(onboardingCanCreate() && !state.onboarding.creating);",
            'id="onboardingWorkItem"',
            'id="onboardingRequest"',
            'id="onboardingCreateForm"',
            'data-onboarding-work-item-branch="create"',
            'data-onboarding-work-item-branch="resume"',
            'if (action === "create" && !state.selectedRuntime)',
            "runtime selection and launch remain separate actions",
            'data-project-set-field="id"',
            "Duplicate root",
        ),
    )
    _assert_contains_all(
        main,
        (
            'event.target.id === "onboardingWorkItem"',
            "state.onboarding.workItemInput = event.target.value;",
            'event.target.id === "onboardingRequest"',
            "state.onboarding.requestText = event.target.value;",
            "const projectSetField = event.target.dataset?.projectSetField;",
            "syncOnboardingCreateActionState();",
        ),
    )
    assert main.count("syncOnboardingCreateActionState();") == 3


def test_operator_onboarding_distinguishes_deterministic_runner_path() -> None:
    onboarding = _asset_text("/operator-onboarding.js")
    components = _asset_text("/operator-components.css")

    _assert_contains_all(
        onboarding,
        (
            "function onboardingRunnerProfile(runtime)",
            "function onboardingRunnerGuidance(runtimes)",
            'runtimeId === "generic-cli"',
            "deterministic baseline",
            "Best first smoke when a wrapper or fixture runtime is configured.",
            "Native provider runners remain available for real model execution",
            "every launch still requires an explicit runner selection",
            '${profile.recommended ? "recommended" : ""}',
            "runner-card-guidance",
            "runner-card-meta",
        ),
    )
    _assert_contains_all(
        components,
        (
            ".runner-selection-guidance {",
            "border-left: 4px solid var(--amber);",
            ".runner-card.recommended {",
            "box-shadow: inset 3px 0 0 var(--green);",
            ".runner-card.recommended.selected {",
            ".runner-card-meta {",
            ".runner-card-guidance {",
            ".runner-card-guidance strong {",
        ),
    )


def test_operator_shell_asset_keeps_runtime_readiness_navigation_and_markdown_contracts() -> None:
    shell = _asset_text("/operator-shell-rendering.js")

    _assert_contains_all(
        shell,
        (
            "function renderRuntimeSelector()",
            "const runtimes = state.readinessLoading ? [] : (state.readiness?.runtimes || []);",
            "Checking runtimes...",
            "if (state.readinessLoading) return null;",
            "function selectedRuntimeReady()",
            "function runtimeReadinessMessage()",
            "function renderProjectHomeRail()",
            "function currentWorkItemSummary()",
            "function workItemHandoffStatus(item)",
            "function workItemTerminalLabel(item)",
            'if (handoffStatus === "failed") return "bad";',
            'if (handoffStatus === "failed") return "qa not-ready";',
            "QA not ready / ${item.stage_progress_label}",
            "QA risks / ${item.stage_progress_label}",
            "handoff blocked / ${item.stage_progress_label}",
            "function workItemProgressText(item)",
            "flow complete / ${item.stage_progress_label}",
            "workItemTerminalLabel(item)",
            "function updateContextualTabs()",
            "function tabHasQuestions()",
            "function tabHasValidation()",
            "function tabHasRunEvidence()",
            "function tabHasArtifacts()",
            "function tabHasApprovals()",
            "function tabHasRecovery()",
            "function updateTabShortcutVisibility(visible)",
            "const mode = normalizeOperatorMode(shortcut).mode;",
            "const visible = new Set(OPERATOR_MODES);",
            "button.hidden = !visible.has(mode);",
            'state.activeTab = tabHasRecovery() ? "recovery" : "work";',
            "applyOperatorModeBodyClass();",
            "function timeoutSummary(runtime)",
            "function readinessDetail(label, value, maxLength = 72)",
            "function ensureRunnableRuntime()",
            'toast("Selected runtime is not ready.")',
            "function scrollActiveStageIntoView()",
            'window.matchMedia("(max-width: 760px)").matches',
            'rail.querySelector(`[data-stage="${CSS.escape(state.activeStage)}"]`)',
            "rail.scrollWidth <= rail.clientWidth",
            'rail.scrollTo({behavior: "auto", left: Math.max(0, left)});',
            "requestAnimationFrame(scrollActiveStageIntoView);",
            'aria-current="${isActive ? "step" : "false"}"',
            'class="stage-copy"',
            "function renderMarkdown(text)",
        ),
    )


def test_operator_project_rail_uses_distinct_segment_states() -> None:
    shell = _asset_text("/operator-shell-rendering.js")

    assert 'data-tab-shortcut="project-home"' in shell
    assert 'data-tab-shortcut="overview"' in shell
    assert shell.count('data-tab-shortcut="work"') == 0
    assert "projectsActive" in shell
    assert "workItemsActive" in shell
    assert 'aria-pressed="${projectsActive ? "true" : "false"}"' in shell
    assert 'aria-pressed="${workItemsActive ? "true" : "false"}"' in shell


def test_operator_stage_retry_affordance_links_to_recovery_history() -> None:
    api_state = _asset_text("/operator-api-state.js")
    shell = _asset_text("/operator-shell-rendering.js")
    layout = _asset_text("/operator-layout.css")
    components = _asset_text("/operator-components.css")
    cockpit = _asset_text("/operator-stage-cockpit.js")
    main = _asset_text("/operator-main.js")

    _assert_contains_all(
        api_state,
        (
            "function stageRetrySummary(item)",
            "attemptCount <= 1",
            "retryCount",
            "open Recovery for repair and retry history",
        ),
    )
    _assert_contains_all(
        shell,
        (
            "const retry = stageRetrySummary(item);",
            'class="small-badge ${retry ? "retried" : ""}"',
            "retry ${escapeHtml(attemptCount)}x",
            'class="stage-card${active}${retry ? " retried" : ""}"',
            'data-stage-recovery="validation"',
            "Retry history",
        ),
    )
    _assert_contains_all(
        layout,
        (
            ".small-badge.retried",
            ".status-badge.retried",
            ".badge-button.retried",
            ".stage-card.retried",
            ".stage-card.active.retried",
        ),
    )
    _assert_contains_all(
        components,
        (
            ".repair-resolved-summary {",
            "border-left: 4px solid var(--green);",
            ".repair-resolved-summary .small-badge {",
        ),
    )
    _assert_contains_all(
        cockpit,
        (
            "function renderResolvedRepairSummary(validation)",
            "resolved after retry",
            "resolved across",
            "Validation is clear after a retry.",
            "hasRepairAttempts",
            "hasValidationFindings",
            "Resolved retry",
        ),
    )
    _assert_contains_all(
        main,
        (
            'closest("[data-stage-recovery]")',
            'activateTab(stageRecovery.dataset.stageRecovery || "recovery", '
            '{historyMode: "push"});',
        ),
    )


def test_operator_cockpit_asset_keeps_overview_sidebar_and_activity_contracts() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")

    _assert_contains_all(
        cockpit,
        (
            "async function renderCockpit()",
            "renderQuestionCards({showResume: true})",
            'state.recoveryDetail === "questions"',
            "content.innerHTML = renderQuestions();",
            "updateQuestionResumeButtonStates();",
            'state.recoveryDetail === "validation"',
            "content.innerHTML = renderValidation();",
            "Run-global blocker",
            "renderRecoverySummary({",
            'evidence: {label: runtimeFailure ? "Runtime log" : '
            '"Supporting evidence", path: evidencePath}',
            'item.action === "inspect-runtime-log"',
            "Open Recovery Summary",
            "function bottomDockDefaultCollapsed()",
            "function bottomDockIsCollapsed()",
            "data-bottom-dock-toggle",
            "Hide activity",
            "Show activity",
            "No validation evidence for this stage yet",
            "data-blocker-stage",
            "data-evidence-path",
            "Support tier",
            "Command source",
            "Execution mode",
            "Permission policy",
            "Interaction mode",
            "Auto approval",
            "renderRuntimeReadinessDimensions(runtime)",
            "renderProtectedWriteScope()",
            "function liveJobActivityEvents()",
            "function activityEvents()",
            "function summarizeActivityDetails(details)",
            "function renderActivityDetail(details)",
            "function renderActivityTableMarkup(events)",
            "function renderActivityTable()",
            "function renderRecoveryWorkbench()",
            "stage: state.activeStage,",
            "function renderHistoryMode()",
            "renderRuntimeSelector();",
            "await renderCockpit();",
        ),
    )


def test_operator_control_center_asset_surfaces_running_stage_progress() -> None:
    api_state = _asset_text("/operator-api-state.js")
    control_center = _asset_text("/operator-control-center.js")

    _assert_contains_all(
        api_state,
        (
            "function runtimeOutputFreshnessLabel(job)",
            "function runtimeLogChunkCount()",
            "function activeJobLiveLogChunkSummary(job = state.activeJobStatus)",
            "function activeJobHasNoRuntimeOutput(job = state.activeJobStatus)",
            "function runtimeOutputMissingLabel(job = state.activeJobStatus)",
            "function secondsLabel(value)",
            "function externalRunningStageItem(action = state.dashboard?.next_action)",
            "function syncExternalRunningBodyClass()",
            "Last runtime output",
            "No runtime output captured yet",
            (
                "System control messages may exist, but stdout/stderr runtime "
                "evidence has not arrived yet."
            ),
        ),
    )
    _assert_contains_all(
        control_center,
        (
            "function renderRunningStageNotice(job)",
            'class="run-progress-notice" role="status" aria-live="polite"',
            "Runtime is waiting for an operator approval decision.",
            "Stage is still running; live logs are the current evidence stream.",
            "Live log chunks",
            "${renderRunningStageNotice(job)}",
            "${escapeHtml(runtimeOutputFreshnessLabel(job))}",
            "${escapeHtml(logChunkSummary)}",
            "Last runtime output",
            "Last runtime line:",
        ),
    )
    assert "not available ago" not in control_center


def test_operator_global_next_action_surfaces_live_job_progress() -> None:
    next_flow = _next_flow_assets()
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        next_flow,
        (
            "function activeJobLiveMessage(job)",
            "function activeJobProgressNotice(job)",
            "function renderActiveJobProgressNotice(job)",
            "function renderGlobalLiveProgress(job)",
            "function externalRunningStageMessage(action, item)",
            "function renderExternalRunningStageProgress(action)",
            'class="live-progress-strip" role="status" aria-live="polite"',
            'class="live-progress-strip external-running-stage" role="status" aria-live="polite"',
            "Waiting for operator approval",
            "Running now",
            "Waiting for first runtime output",
            "runtimeOutputMissingLabel(job)",
            "runtimeOutputMissingDetail()",
            "Cancel requested",
            "${renderActiveJobProgressNotice(job)}",
            "running outside UI control",
            "Refresh status or inspect saved runtime logs",
            "Runtime is active; live logs are the current evidence stream.",
            "runtimeOutputFreshnessLabel(job)",
            "activeJobLiveLogChunkSummary(job)",
            "Open live logs",
            "Open runtime logs",
            "data-refresh-dashboard",
            "data-cancel-job",
            "syncLiveJobBodyClass();",
            'host.classList.toggle("live-progress-active", Boolean(activeJobState));',
            'host.classList.toggle("external-progress-active", Boolean(externalRunningState));',
            'host.classList.remove("live-progress-active", "external-progress-active");',
        ),
    )
    _assert_contains_all(
        components,
        (
            ".global-next-action-strip.live-progress-active {",
            ".global-next-action-strip.external-progress-active {",
            ".live-progress-strip {",
            ".live-progress-strip.external-running-stage {",
            "grid-template-columns: minmax(0, 1fr);",
            ".live-progress-copy {",
            ".live-progress-meta {",
            ".live-progress-actions {",
            ".live-progress-notice {",
            ".live-progress-notice.info {",
            ".live-progress-notice.warn {",
        ),
    )
    _assert_contains_all(
        responsive,
        (
            ".live-progress-strip {",
            ".live-progress-actions {",
            ".live-progress-actions button {",
            ".live-progress-meta,",
            f"{_MOBILE_PRIORITY_SELECTOR} {{",
            f"{_MOBILE_PRIORITY_SELECTOR} .cockpit {{",
            f"{_MOBILE_PRIORITY_SELECTOR} .stage-rail {{",
            f"{_MOBILE_PRIORITY_SELECTOR} .right-sidebar {{",
            f"{_MOBILE_PRIORITY_SELECTOR} .bottom-dock {{",
        ),
    )


def test_operator_artifact_asset_keeps_document_and_truncation_contracts() -> None:
    artifacts = _asset_text("/operator-artifacts-documents.js")

    _assert_contains_all(
        artifacts,
        (
            "function preferredArtifactKey(documents)",
            '"stage_result"',
            "const MAX_ARTIFACT_READ_BYTES = 262144;",
            "function byteRangeSummary(view)",
            'function renderTruncationNotice(kind, view, mode = "")',
            'class="truncation-notice" role="status"',
            "Runtime log truncated",
            "Artifact view truncated",
            "Switch to Source for a larger bounded read",
            "Source view is bounded. Open the folder for the full file.",
            "Full runtime.log remains on disk",
            "No artifacts for this stage yet",
            "function renderWorkbenchTree(workbench)",
            "function renderWorkbenchViewer(workbench)",
            "function renderWorkbenchDiff(workbench)",
            "function renderWorkbenchTableOfContents(workbench)",
            "function artifactCategoryFor(item = {})",
            "function artifactCategoryLabel(category)",
            "function artifactCategoryDetail(category)",
            "function artifactOwnershipBadge(item = {})",
            "function artifactSupportsDownload(item = {})",
            "function renderArtifactDownloadButton(item = {}, className = \"link-button\")",
            "function renderArtifactOwnershipNote(item = {})",
            "function markdownHeadingSummary(text)",
            "Table of Contents",
            "function renderRequirementList(requirements)",
            "function renderValidationResults(results)",
            "function renderMissingEvidence(requirements)",
            "Artifact categories",
            "Canonical stage documents",
            "Published output mirrors",
            "Source-of-truth stage files for operator review",
            "Downstream handoff copies under output/",
            "canonical source",
            "handoff mirror",
            "\"mirror\": \"MR\"",
            "Canonical source of truth",
            "Published handoff mirror",
            "Canonical stage path:",
            "Runtime inputs",
            "Validation evidence",
            "Runtime evidence",
            "Project evidence",
            "Lineage evidence",
            "Contract requirements",
            "Validation results",
            "Missing evidence",
            "References",
            "Version history",
            "function evidenceEdgeId(edge)",
            "function preferredEvidenceArtifactKey(view)",
            "function selectedEvidenceSelection(view)",
            "function renderEvidenceGraphBrowser(view, selection)",
            "function renderEvidenceGraphCanvas(view, selection)",
            "function renderArtifactInspector(view, selection)",
            "function renderEvidenceArtifactTable(view, selection)",
            "function renderEvidenceWorkbenchShell(selection)",
            "function renderEvidenceWorkbenchUnavailable(view)",
            "function renderEvidenceGraphScreen(view, selection)",
            "async function copyArtifactPath(path)",
            "async function downloadArtifact({stage, key, kind, path})",
            "Artifacts / Evidence Graph",
            "Stage Document Workbench",
            "Flat Table Fallback",
            "Selected Artifact",
            "data-evidence-node",
            "data-evidence-edge",
            "data-download-artifact",
            "data-copy-artifact-path",
            'ref.available === false ? "missing" : "available"',
            "/api/artifacts/evidence-graph?${params.toString()}",
            "/api/artifacts/document?${params.toString()}",
            "/api/stage/workbench?${params.toString()}",
            'params.set("source_limit", String(MAX_ARTIFACT_READ_BYTES));',
            'data-artifact-mode="diff"',
            'renderTruncationNotice("artifact", view, state.artifactViewMode)',
            "${renderMarkdown(view.text)}",
            "async function inspectArtifactReference({stage, key, path, kind})",
            "data-artifact-key",
        ),
    )
    assert (
        "const preferredKey = state.activeArtifactKey || preferredEvidenceArtifactKey(view);"
        in artifacts
    )
    assert (
        'const selectedArtifactKey = selection.node?.kind === "document"'
        in artifacts
    )
    assert "await loadArtifactDocument(selectedArtifactKey);" in artifacts
    assert artifacts.index("${renderEvidenceWorkbenchShell(selection)}") < artifacts.index(
        '<details class="surface evidence-drilldown">'
    )
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")
    _assert_contains_all(
        components,
        (
            ".artifact-category-note {",
            ".artifact-ownership-note {",
            ".artifact-ownership-note.published-stage-output {",
            ".artifact-doc-title {",
            ".markdown-preview code {",
            ".workbench-side-row span {",
        ),
    )
    assert ".artifact-ownership-note," in responsive
    assert ".workbench-sidebar," in responsive


def test_operator_questions_asset_keeps_answer_resolution_and_saved_answer_contracts() -> None:
    questions = _asset_text("/operator-questions.js")
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        questions,
        (
            "function questionControlId(prefix, questionId, index)",
            (
                'const questionTextId = questionControlId("question-text", '
                "question.question_id, index);"
            ),
            'const answerId = questionControlId("answer", question.question_id, index);',
            'const resolutionId = questionControlId("resolution", question.question_id, index);',
            '<p id="${questionTextId}">${escapeHtml(question.text)}</p>',
            (
                '<label class="sr-only" for="${answerId}">Answer for '
                "${escapeHtml(questionLabel)}</label>"
            ),
            '<textarea id="${answerId}" name="${answerId}" aria-describedby="${questionTextId}"',
            '<label class="sr-only" for="${resolutionId}">Resolution for ',
            (
                '<select id="${resolutionId}" name="${resolutionId}" '
                'aria-describedby="${questionTextId}"'
            ),
            "function questionDisplayStatus(question)",
            "function questionRequiresResolvedResume(question)",
            "function updateQuestionResumeButtonState(questionId)",
            "function updateQuestionResumeButtonStates()",
            "function interviewDecisionCounts(view)",
            "function renderInterviewDecisionSpotlight(view)",
            "data-interview-decision-spotlight",
            "No interview questions for this stage",
            "Blocking questions need resolved answers",
            "Interview answers need final resolution",
            "Interview answers saved",
            "Primary action: answer required questions",
            "${renderInterviewDecisionSpotlight(view)}",
            "function renderInterviewSummary(view)",
            "function renderBlockedStageContext(view)",
            "Questions / Interview Loop",
            'data-human-decision-surface="question"',
            "Required answers",
            "Blocked stage",
            'const savedAnswer = question.answer_resolution',
            "const draft = questionDraft(question.question_id)?.value || null;",
            'const answerText = draft?.text ?? question.answer_text ?? "";',
            'const resolutionValue = draft?.resolution || question.answer_resolution || '
            '"resolved";',
            'class="saved-answer"',
            'data-question-id="${escapeHtml(question.question_id)}"',
            'data-question-status="${escapeHtml(displayStatus)}"',
            'data-answer-resolution="${escapeHtml(resolutionValue)}"',
            'data-question-draft-restored="${escapeHtml(question.question_id)}"',
            "Restored unsent session draft.",
            "Saved ${escapeHtml(question.answer_resolution)} answer",
            "Answer recorded in answers.md",
            "${escapeHtml(answerText)}</textarea>",
            'option value="resolved" ${resolutionValue === "resolved" ? "selected" : ""}',
            "Update answer",
            "Update & resume",
            "Select resolved to resume",
            "data-requires-resolved-resume",
            "Blocking questions must be saved as resolved before resume.",
            '<details class="question-history"',
            "data-answer-resume-all",
            'resolution: resolution?.value || "resolved"',
            'option value="partial"',
            'option value="deferred"',
            "async function answerAndResume(questionId)",
            "await fetchReadiness();",
            "async function resumeAfterAnswers()",
        ),
    )
    _assert_contains_all(
        components,
        (
            ".interview-decision-spotlight {",
            "box-shadow: inset 4px 0 0 var(--green);",
            ".interview-decision-spotlight.warn {",
            ".interview-decision-spotlight.bad {",
            ".interview-decision-facts {",
            "grid-template-columns: repeat(5, minmax(0, 1fr));",
        ),
    )
    assert ".interview-decision-spotlight," in responsive
    assert ".interview-decision-facts," in responsive


def test_operator_recovery_assets_keep_repair_center_contracts() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        cockpit,
        (
            "function repairCenterStatus(validation, stopped)",
            "repair-exhausted",
            "explicit-stop",
            "function renderRecoveryActionBand(diagnostics)",
            "renderValidationFindingSummary(finding)",
            (
                "const requestPrimary = status === \"repair-exhausted\" "
                "|| status === \"explicit-stop\";"
            ),
            "Repair exhausted",
            "Validation still fails after repair attempts.",
            "function renderValidationFindingList(validation)",
            "actionableValidationFindings(validation)",
            "function renderOutputMirrorNoticeList(validation)",
            "nonBlockingValidationNotices(validation)",
            "function renderRepairTimeline(validation)",
            "function renderBlockedStageRecovery(diagnostics)",
            "Validation / Repair Center",
            "Repair Available",
            "Run Repair",
            "Stop Run",
            "Request Change",
            'data-recovery-action="request-change"',
            'data-recovery-stage="${escapeHtml(state.activeStage)}"',
            "Validation attempt timeline",
            "Auto-promoted output mirrors",
            "output/ handoff mirrors",
            "canonical stage documents",
            "Actionable validation findings",
            "Blocked questions",
            "Answers path",
            "data-run-repair",
            "data-stop-run",
            'data-tab-shortcut="request"',
        ),
    )
    _assert_contains_all(
        responsive,
        (
            "body.recovery-mode .recovery-summary-failure",
            "body.recovery-mode .recovery-summary-primary",
            "body.recovery-mode .recovery-summary-evidence",
            "min-height: var(--control-height-touch);",
            "overflow: visible;",
        ),
    )


def test_operator_recovery_assets_prioritize_eligible_runtime_retry() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")

    _assert_contains_all(
        cockpit,
        (
            "const RUNTIME_FAILURE_KINDS = new Set([",
            "runtime-exit-metadata-invalid",
            "provider-no-progress",
            "launch_failure",
            "authentication_failure",
            "function isRuntimeFirstFailure(firstFailure)",
            "function runtimeLogEvidencePath(diagnostics)",
            "function runtimeFailureEvidencePath(firstFailure, diagnostics)",
            "function renderRuntimePartialEvidence(firstFailure)",
            "Partial stage evidence",
            "Inspect partial documents, runtime log, and runtime-exit metadata",
            "runtime-partial-evidence",
            'action.action === "resume-stage"',
            'data-recovery-action="resume-stage"',
            "Retry stage",
            "isRuntimeFirstFailure(firstFailure) && retryAction",
            'action: "resume-stage"',
            'label: retryAction.label || "Retry stage"',
            "Runtime failure does not consume validation repair budget.",
            "data-runtime-failure-kind",
            "data-runtime-stopped",
            "data-runtime-last-signal",
            "data-validation-repair-budget-consumed",
            "Runtime log",
        ),
    )
    assert cockpit.index("isRuntimeFirstFailure(firstFailure) && retryAction") < cockpit.index(
        'if (status === "repair-available")'
    )


def test_operator_overview_static_contract_covers_run_accountability_card() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")
    api_state = _asset_text("/operator-api-state.js")

    _assert_contains_all(
        cockpit,
        (
            "function renderRunAccountabilityCard()",
            "async function loadRunAccountabilityCard()",
            "/api/run/accountability",
            "Run provenance",
            "prompt_pack_provenance",
            "repository_git_sha",
            "resource_revision",
            "stage_graph",
        ),
    )
    assert "runAccountability" in api_state
    assert "runAccountabilityError" in api_state


def test_operator_implement_review_static_contract_covers_project_set_grouping() -> None:
    quality_gate = _asset_text("/operator-quality-gates.js")
    control = _asset_text("/operator-control-center.js")

    _assert_contains_all(
        quality_gate + control,
        (
            "async function renderImplementReview()",
            "diffView.project_set_roots",
            "file.scope_status",
            "Project scope:",
        ),
    )


def test_studio_implementation_gate_uses_canonical_task_actions_and_review_guard() -> None:
    quality_gate = _asset_text("/operator-quality-gates.js")
    control = _asset_text("/operator-control-center.js")

    _assert_contains_all(
        quality_gate,
        (
            "function renderStudioImplementationQualityGate(taskView)",
            'data-studio-quality-gate="implement"',
            'data-run-task="${escapeHtml(task.id)}"',
            "task.ready && selectedRuntimeReady()",
            "data-finalize-tasks",
            "taskView.finalization_eligible",
            "data-implementation-review-blocker",
            "taskView.review_blocker",
        ),
    )
    _assert_contains_all(
        control,
        (
            "renderStudioImplementationQualityGate(taskView)",
            "reviewEnabled: context.verificationReady",
        ),
    )


def test_studio_repository_evidence_uses_textual_change_and_scope_contracts() -> None:
    quality_gate = _asset_text("/operator-quality-gates.js")

    _assert_contains_all(
        quality_gate,
        (
            "function renderStudioRepositoryEvidence({",
            'data-document-canvas="implementation-evidence"',
            'return "Added"',
            'return "Removed"',
            'return "Changed"',
            "Allowed scope:",
            "Project scope:",
            "core-owned <code>.aidd/</code> evidence",
            "Claim mismatch:",
            "mentioned but unchanged",
            "absent from implementation-report.md",
            "data-implementation-claims",
        ),
    )


def test_studio_review_qa_gates_render_exact_identity_and_blocker_contracts() -> None:
    quality_gate = _asset_text("/operator-quality-gates.js")
    control = _asset_text("/operator-control-center.js")

    _assert_contains_all(
        quality_gate,
        (
            "function renderStudioReviewQualityGate(view)",
            'data-studio-quality-gate="review"',
            "finding.finding_id",
            "finding.acceptance_ids",
            "finding.evidence",
            "finding.related_paths",
            "function renderStudioQaQualityGate(view, sourceItems)",
            'data-studio-quality-gate="qa"',
            "view?.acceptance_ids",
            "view?.evidence_references",
            "Residual risk ·",
            "Known issue ·",
            "data-quality-gate-blocker",
            "function studioRemediationReadback(sourceStage)",
            'data-remediation-readback=',
            'data-recovery-action="rerun-stale-downstream"',
            "Terminal handoff stays blocked",
        ),
    )
    _assert_contains_all(
        control,
        (
            "renderStudioReviewQualityGate(view)",
            "renderStudioQaQualityGate(view, sourceItems)",
        ),
    )


def test_operator_implement_review_surfaces_missing_verification_evidence() -> None:
    control = _asset_text("/operator-control-center.js")
    quality_gate = _asset_text("/operator-quality-gates.js")

    _assert_contains_all(
        control + quality_gate,
        (
            "function renderImplementationVerificationGap(implementation)",
            "implementation?.verification_commands || []",
            "Implementation verification evidence is missing",
            "No executable command evidence was parsed from implementation-report.md.",
            "Primary action: Rerun implement or request intervention",
            "function implementationSummaryWarnings(implementation)",
            "No executable verification commands",
            "renderWarnings(implementationSummaryWarnings(implementation))",
            "function renderImplementationVerificationItems(implementation)",
            "Skipped: ${escapeHtml(item)}",
            "Verification evidence missing.",
            "${renderImplementationVerificationItems(implementation)}",
            "function implementationVerificationReady(implementation)",
            "function renderImplementationProceedGuard(implementation)",
            (
                "Proceed to review is blocked until implementation records executable "
                "verification evidence."
            ),
            "const verificationReady = implementationVerificationReady(evidence);",
            "reviewEnabled",
            "${renderImplementationProceedGuard(evidence)}",
            'kind: "implementation-verification"',
            'badge: "verification missing"',
            "${renderImplementationVerificationGap(implementation)}",
        ),
    )


def test_operator_stale_downstream_summary_prioritizes_rerun_guidance() -> None:
    api_state = _asset_text("/operator-api-state.js")
    next_flow = _next_flow_assets()
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        api_state,
        (
            "stale-downstream-mode",
            'state.dashboard?.next_action?.action === "rerun-stale-downstream"',
            "(state.dashboard?.stages || []).some((item) => item.stale)",
        ),
    )
    _assert_contains_all(
        next_flow,
        (
            "function staleDownstreamStages()",
            "function staleDownstreamStageLabel(items)",
            "function staleDownstreamRuntimeGate()",
            "function renderStaleDownstreamSummary(action)",
            "data-stale-downstream-summary",
            "Terminal QA handoff stays blocked until stale downstream evidence is refreshed.",
            "Rerun downstream",
            "Select ready runtime",
            "${renderStaleDownstreamSummary(action)}",
        ),
    )
    _assert_contains_all(
        components,
        (
            ".stale-downstream-summary {",
            "box-shadow: inset 4px 0 0 var(--amber);",
            ".stale-downstream-copy {",
            ".stale-downstream-facts {",
            "grid-template-columns: repeat(4, minmax(0, 1fr));",
        ),
    )
    assert _MOBILE_PRIORITY_SELECTOR in responsive
    assert f"{_MOBILE_PRIORITY_SELECTOR} .cockpit" in responsive
    assert ".stale-downstream-summary," in responsive
    assert ".stale-downstream-facts," in responsive


def test_operator_approvals_asset_keeps_request_and_intervention_contracts() -> None:
    approvals = _asset_text("/operator-approvals-interventions.js")
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        approvals,
        (
            "async function renderRequestChange()",
            "async function renderApprovals()",
            "async function submitApproval(requestId, action, {sessionConfirmed = false} = {})",
            "async function submitIntervention()",
            "function requestChangeTargetEntries(documents, context)",
            "function selectedInterventionTargets()",
            "function renderInterventionDiffPreview(requestText, targetDocuments)",
            "function updateInterventionPreview()",
            "function renderRequestChangeAuditLog(context)",
            "function renderApprovalQueueSummary({requests, decisions, pendingIds, diagnostics})",
            "function renderApprovalDiffPreview(request)",
            (
                "function approvalAuditCounts({requests, decisions, pendingIds, "
                "diagnostics, auditHistory})"
            ),
            (
                "function renderApprovalDecisionSpotlight({requests, decisions, pendingIds, "
                "diagnostics, auditHistory})"
            ),
            (
                "function renderApprovalAuditLog(requests, decisions, pendingIds, "
                "diagnostics = null, auditHistory = null)"
            ),
            "function renderApprovalsSurface({view, diagnostics, requests, decisions, pendingIds})",
            "data-approval-decision-spotlight",
            "data-approval-reason",
            "data-approval-session-confirmation",
            "data-approval-request-id",
            "data-approval-status",
            "data-approval-risk",
            "data-approval-scope",
            "data-approval-breadth",
            "data-approval-winner",
            "data-approval-durable-winner",
            "This request only unless session approval is explicitly confirmed",
            "Confirm session-wide approval",
            "all matching requests in the current runtime approval session",
            "function setApprovalRequestPending(requestId, pending)",
            "Runtime approval required",
            "Runtime request blocked by policy",
            "Runtime approval stopped",
            "No runtime approvals are waiting",
            "Request Change / Intervention Composer",
            "Approvals / Runtime Requests",
            "Diff Preview",
            "Approval Audit Log",
            "view?.audit_history",
            (
                "renderApprovalDecisionSpotlight({requests, decisions, pendingIds, "
                "diagnostics, auditHistory})"
            ),
            "policy-blocked",
            "row.runtime_id",
            "row.decision_action",
            "Saved approval ledger",
            'id="operatorRequestText"',
            'id="submitInterventionButton"',
            "data-intervention-eligible",
            'data-human-decision-surface="intervention"',
            'data-human-decision-surface="approval"',
            "data-intervention-stage",
            "data-intervention-run",
            "Request Change requires remediation routing",
            "context.eligible === false",
            "this stage-scoped path will not create an operator request",
            'id="interventionDiffPreview"',
            "data-intervention-target",
            '"validator_report"',
            '"questions.md"',
            "!textPath.includes(\"/operator-requests/\")",
            "function interventionTargetLabel(key)",
            "function updateSubmitInterventionState()",
            "function renderLatestRequestSummary(context)",
            "Latest request",
            "interventionReadinessNote",
            "runtimeReadinessMessage()",
            "/api/jobs/${encodeURIComponent(state.activeJobId)}/operator-requests",
            "target_documents: targetDocuments",
            "request.created_at_utc",
            "escapeHtml(JSON.stringify(payload, null, 2))",
            "if (state.activeRunId) payload.run_id = state.activeRunId;",
            'postJson("/api/stage/interact", payload)',
        ),
    )
    _assert_contains_all(
        components,
        (
            ".approval-decision-spotlight {",
            "box-shadow: inset 4px 0 0 var(--green);",
            ".approval-decision-spotlight.warn {",
            ".approval-decision-spotlight.bad {",
            ".approval-decision-facts {",
            "grid-template-columns: repeat(5, minmax(0, 1fr));",
        ),
    )
    assert ".approval-decision-spotlight," in responsive
    assert ".approval-decision-facts," in responsive
    assert "[data-human-decision-surface] button," in responsive
    assert '[data-human-decision-surface="question"] [data-primary-action]' in responsive
    assert '[data-human-decision-surface="intervention"] #submitInterventionButton' in responsive
    assert (
        '[data-human-decision-surface="approval"] [data-operator-action="allow_once"]'
        in responsive
    )


def test_operator_logs_asset_keeps_filter_raw_cancel_and_polling_contracts() -> None:
    logs = _asset_text("/operator-logs-jobs.js")

    _assert_contains_all(
        logs,
        (
            "function logEntriesFromChunks(chunks)",
            "function logEntriesFromText(text)",
            "rawText.match(/^\\[(stdout|stderr|system)\\]\\s?(.*)$/i)",
            "function logEntryCounts(entries)",
            "function renderLogBoundedNotice(view)",
            "function renderLogSourceStrip(entries, truncation)",
            "function renderLogAuditLog(entries, sourceLabel, truncation)",
            (
                "function renderLogPanel({title, meta, entries, rawText, emptyText, "
                "actions = \"\", truncation = null})"
            ),
            "Runtime Logs / Live Console",
            "Summary",
            "Timeline",
            "Raw Runtime Log",
            "Correlated Events / Audit Log",
            'typeof renderActivityDetail === "function" ? renderActivityDetail(event.details)',
            "bounded-log-notice",
            'renderTruncationNotice("log", view)',
            "No runtime log for this stage yet",
            "Saved runtime.log (pending)",
            "Runtime log is not available yet.",
            "data-log-filter",
            "data-log-view",
            "data-log-raw",
            "state.rawLogMode",
            'state.logFilter === "all" && rawText ? rawText : rawTextFromEntries(filtered)',
            "function renderLiveJobActions()",
            "function activeJobCancelLabel()",
            "async function cancelActiveJob()",
            "function scheduleActiveJobPoll(delayMs = ACTIVE_JOB_POLL_INTERVAL_MS)",
            "function activeJobRetryDelay(failureCount)",
            "function renderActiveJobConnectionSurface()",
            "function reconnectActiveJob()",
            "function clearReconciledActiveJob({preserveConnection = true} = {})",
            "async function reconcileRecoveredActiveJob(jobId, status)",
            "async function reconcileExpiredActiveJob(jobId)",
            "async function reconcileTerminalActiveJob(jobId)",
            'data-connection-state="reconnecting"',
            'data-connection-state="offline"',
            'data-connection-state="expired-job"',
            'data-connection-state="recovered"',
            "data-connection-cursor",
            'data-runtime-terminal-observed="false"',
            'data-durable-log="runtime.log"',
            'recovery: {action: "reconnect-live-job", label: "Reconnect"}',
            "ACTIVE_JOB_RETRY_LIMIT = 5",
            'state: expired || failureCount >= ACTIVE_JOB_RETRY_LIMIT ? "offline" : "reconnecting"',
            "data-cancel-job",
            "Cancel job",
            "Cancelling...",
            "Cancelled",
            "/api/jobs/${encodeURIComponent(state.activeJobId)}/cancel",
            'new Set(["running", "waiting-for-operator", "cancelling"])',
            'state.activeJobStatus?.status === "running"',
            'state.activeJobStatus.kind === "next-flow-launch"',
            "state.activeJobStatus.stage === state.activeStage",
            "state.activeJobLogChunks.length",
            "activeJobLogChunks.push(...(logs.chunks || []));",
            "/api/jobs/${encodeURIComponent(jobId)}/logs?cursor=${state.activeJobCursor}",
            "state.activeJobPollGeneration !== pollGeneration",
            "if (logs.truncated)",
            "Live log tail was truncated before cursor",
            "use the durable runtime log for complete evidence",
            "Number.isFinite(nextCursor)",
            "state.activeJobStatus.status === \"waiting-for-operator\"",
            "async function startJobPolling(job)",
            "message: \"job started\"",
            "renderActiveRunPanel();",
            "renderNextActionPanel();",
            "renderGlobalNextActionStrip();",
            "renderActivityTable();",
        ),
    )
    _assert_contains_all(
        _asset_text("/operator-main.js"),
        (
            'stateRecovery === "reconnect-live-job"',
            "await reconnectActiveJob();",
            'stateRecovery === "refresh-expired-job"',
        ),
    )


def test_operator_next_action_explains_runtime_readiness_blocker_locally() -> None:
    next_flow = _next_flow_assets()
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        next_flow,
        (
            "function nextActionRuntimeBlockerMessage(runtimeBlocked)",
            "runtimeReadinessMessage()",
            "function renderNextActionBlocker(message)",
            'class="next-action-blocker" role="status" aria-live="polite"',
            "const blockerMessage = nextActionRuntimeBlockerMessage(runtimeBlocked);",
            "${renderNextActionBlocker(blockerMessage)}",
            '<div class="next-action-button-stack">',
            "Checking runtime readiness before this action can run.",
            "Runtime readiness unavailable: ${state.readinessError}",
            "Selected runtime is not ready for execution.",
        ),
    )
    _assert_contains_all(
        components,
        (
            ".next-action-button-stack {",
            ".next-action-blocker {",
            "overflow-wrap: anywhere;",
            ".global-next-action-strip .next-action-button-stack {",
            ".global-next-action-strip .next-action-button-stack .next-button {",
        ),
    )
    _assert_contains_all(
        responsive,
        (
            ".global-next-action-strip .next-action-button-stack {",
            "justify-self: stretch;",
            ".next-action-blocker {",
            "max-width: 100%;",
        ),
    )


def test_operator_next_action_sidebar_is_status_mirror_when_global_cta_is_primary() -> None:
    next_flow = _next_flow_assets()
    components = _asset_text("/operator-components.css")

    _assert_contains_all(
        next_flow,
        (
            "function workDetailOwnsPrimarySurface()",
            '["implement-review", "review-findings", "qa-verdict"].includes(state.workDetail)',
            "function globalNextActionStripProvidesPrimary()",
            "state.activeTab === \"recovery\"",
            "workDetailOwnsPrimarySurface()",
            'document.body.classList.contains("evidence-log-mode")',
            "function renderNextActionSidebarMirror({label, statusMessage, tone})",
            '<div class="next-action-sidebar-mirror">',
            "Next Action Status",
            "Primary action is ready in the stage cockpit.",
            "Primary action is not available yet.",
            "renderNextActionSidebarMirror({label, statusMessage, tone})",
            '<button id="nextActionButton" class="next-button"',
        ),
    )
    _assert_contains_all(
        components,
        (
            ".next-action-sidebar-mirror {",
            ".next-action-sidebar-mirror .small-badge {",
            ".next-action-sidebar-mirror strong {",
            ".next-action-sidebar-mirror span:not(.small-badge) {",
        ),
    )


def test_operator_next_flow_wizard_static_contract_covers_controls_and_preflight() -> None:
    next_flow = _next_flow_assets()

    _assert_contains_all(
        next_flow,
        (
            "function renderNextFlowSourceSelection()",
            "function renderFollowUpDefinition()",
            "function renderLaunchConfirmation()",
            "function renderArchiveConfirmation()",
            "function renderSourceSelectionSummary(payload, selectedCount)",
            "renderNextFlowWizardStep()",
            "source findings",
            "Selected sources",
            "Linked artifacts",
            "Select recommended",
            "Clear selection",
            "Supporting evidence",
            "Selection required",
            "data-source-selection-id",
            "data-source-selection-mode",
            "data-close-next-flow-wizard",
            "data-next-flow-continue",
            "Continue to Define Work Item",
            "data-next-flow-back-to-sources",
            "data-next-flow-confirm-preview",
            "data-next-flow-back-to-definition",
            "data-launch-flow-now",
            "Back to handoff",
            "Continue to preflight",
            "Preflight results",
            "Audit preview",
            "Source artifact links",
            "manual-source-row",
            "No source links selected.",
            "Preflight blocked",
            "Definition needs attention",
            "data-follow-up-list-blocker",
            "Required for preflight",
            "Running launch preflight...",
            "Flow Launch Wizard",
            "Independent flow",
            "Confirm Archive Run",
            "renderArchiveHandoffWarning(handoff)",
            "renderTerminalRecoveryWizardAction(handoff)",
            "data-archive-confirm",
        ),
    )


def test_operator_focus_visible_contract_covers_keyboard_reachable_surfaces() -> None:
    html = _asset_text("/")
    css = _css_bundle()

    _assert_contains_all(
        css,
        (
            "button:focus-visible",
            "select:focus-visible",
            "textarea:focus-visible",
            "[tabindex]:focus-visible",
            "box-shadow: var(--focus-shadow)",
            "outline: var(--focus-width) solid var(--color-focus)",
            "outline-offset: var(--focus-offset)",
            "--focus-ring:",
            "--focus-ring-soft:",
        ),
    )
    _assert_contains_all(
        html,
        (
            'id="cockpitContent"',
            'role="tabpanel"',
            'tabindex="0"',
            'id="runtimeSelect"',
            'role="status" aria-live="polite"',
        ),
    )


def test_operator_main_asset_keeps_refresh_order_and_event_routing_contracts() -> None:
    main = _asset_text("/operator-main.js")
    bundle = _js_bundle()

    _assert_contains_all(
        main,
        (
            "await fetchDashboard();",
            "void fetchReadiness().then(renderAll)",
            "/api/open-folder",
            "/api/server/stop",
            "function orderedTabButtons()",
            "VALID_TABS.includes(button.dataset.tab || \"\") && !button.hidden",
            'event.target.closest("[data-first-launch-run]")',
            'event.target.closest("[data-first-launch-stage]")',
            "await startStage(state.activeStage);",
            'closest("[data-next-flow-action]")',
            'action === "start-follow-up-flow"',
            "await openNextFlowWizard(action)",
            "await openNewWorkItemHandoff();",
            "await openCloneFlowDraft();",
            "await openEvalBatchHandoff();",
            'action === "archive-run"',
            "await openArchiveConfirmation();",
            'closest("[data-source-selection-mode]")',
            "selectSourceFindings(sourceSelectionMode);",
            'closest("[data-archive-confirm]")',
            "await archiveCompletedRun();",
            'closest("[data-source-selection-id]")',
            "setSourceFindingSelection",
            'closest("[data-close-next-flow-wizard]")',
            'closest("[data-next-flow-continue]")',
            "await loadFollowUpDraft()",
            'closest("[data-next-flow-back-to-sources]")',
            "requestNextFlowWizardReveal();",
            'closest("[data-next-flow-confirm-preview]")',
            "await loadLaunchConfirmation()",
            'closest("[data-next-flow-back-to-definition]")',
            'closest("[data-launch-flow-now]")',
            "await launchNextFlowNow();",
            'closest("[data-follow-up-field]")',
            'closest("[data-follow-up-list-text]")',
            'closest("[data-follow-up-list]")',
            'closest("[data-inherited-context]")',
            "invalidateFollowUpDraftPreview();",
            'event.target.id === "operatorRequestText"',
            'closest("[data-bottom-dock-toggle]")',
            "state.bottomDockUserCollapsed = !bottomDockIsCollapsed();",
            'closest("[data-intervention-target]")',
            "updateInterventionPreview();",
            'if (state.activeTab === "work") await renderCockpit();',
            'closest("[data-artifact-stage]")',
            'closest("[data-artifact-key]")',
            'closest("[data-evidence-node]")',
            'closest("[data-evidence-edge]")',
            'closest("[data-copy-artifact-path]")',
            'closest("[data-download-artifact]")',
            "await copyArtifactPath(copyArtifact);",
            "await downloadArtifact({",
            "data-log-filter",
            "data-log-raw",
            'closest("[data-answer-resume-all]")',
            'closest("[data-run-repair]")',
            'closest("[data-stop-run]")',
            "Stop Run requires an active UI-started job.",
            "initializeStateFromLocation();",
            "refresh();",
        ),
    )
    assert "queued for the next UI slice" not in main
    assert "queued for the private next-flow API slice" not in main
    assert "Promise.all([fetchDashboard(), fetchReadiness()])" not in main
    assert 'body: JSON.stringify({runtime: "generic-cli"})' not in bundle
    click_handler, change_handler = main.split('document.addEventListener("change"', 1)
    assert 'closest("[data-source-selection-id]")' not in click_handler
    assert 'closest("[data-source-selection-id]")' in change_handler
    assert main.index('closest("[data-artifact-stage]")') < main.index(
        'closest("[data-artifact-key]")'
    )


def test_index_html_exposes_named_operator_landmarks() -> None:
    assert _attrs_for("header", **{"aria-label": "Operator controls"})
    assert _attrs_for("main", **{"aria-label": "Operator workspace"})


def test_index_html_keeps_service_commands_in_labelled_maintenance_overflow() -> None:
    html = _asset_text("/")

    assert html.index('id="cockpitContent"') < html.index('class="maintenance-overflow"')
    _assert_contains_all(
        html,
        (
            '<summary data-aidd-focus-role="maintenance">Maintenance</summary>',
            'role="group" aria-label="Service maintenance commands"',
            'id="refreshButton"',
            'id="openWorkspaceButton"',
            'id="stopServerButton"',
        ),
    )
    top_actions = html.split('<div class="top-actions">', 1)[1].split("</div>", 1)[0]
    assert 'id="refreshButton"' not in top_actions
    assert 'id="openWorkspaceButton"' not in top_actions
    assert 'id="stopServerButton"' not in top_actions


def test_desktop_studio_shell_owns_primary_vertical_scrolling() -> None:
    html = _asset_text("/")
    layout = _asset_text("/operator-layout.css")
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    assert (
        'class="operator-shell" aria-label="Operator workspace" '
        'data-aidd-scroll-owner="studio" data-mobile-priority-layout='
    ) in html
    shell_rule = layout.split(".operator-shell {", 1)[1].split("}", 1)[0]
    assert "max-height: calc(100vh - 52px);" in shell_rule
    assert "overflow-y: auto;" in shell_rule
    stage_rule = layout.split("\n.stage-rail {", 1)[1].split("}", 1)[0]
    cockpit_rule = layout.split("\n.cockpit {", 1)[1].split("}", 1)[0]
    sidebar_rule = components.split("\n.right-sidebar {", 1)[1].split("}", 1)[0]
    assert "overflow: visible;" in stage_rule
    assert "overflow: visible;" in cockpit_rule
    assert "overflow: visible;" in sidebar_rule
    mobile_shell = responsive.split(
        f"  {_MOBILE_PRIORITY_SELECTOR} {{",
        1,
    )[1].split("}", 1)[0]
    assert "max-height: none;" in mobile_shell
    assert "overflow: visible;" in mobile_shell
    assert _attrs_for("aside", **{"aria-label": "Workflow navigation"})
    assert _attrs_for("section", **{"aria-label": "Stage cockpit"})
    assert _attrs_for("aside", **{"aria-label": "Run details"})
    assert _attrs_for("section", **{"aria-label": "Activity and recent artifacts"})
    assert _attrs_for("nav", id="stageRail", **{"aria-label": "Workflow stages"})


def test_index_html_exposes_tab_and_panel_semantics() -> None:
    assert _attrs_for("div", role="tablist", **{"aria-label": "Stage cockpit views"})
    work_tab = _attrs_for("button", id="tab-work", role="tab")
    recovery_tab = _attrs_for("button", id="tab-recovery", role="tab")
    evidence_tab = _attrs_for("button", id="tab-evidence", role="tab")
    history_tab = _attrs_for("button", id="tab-history", role="tab")
    panel = _attrs_for("div", id="cockpitContent", role="tabpanel")

    assert work_tab["aria-selected"] == "true"
    assert work_tab["aria-controls"] == "cockpitContent"
    assert work_tab["tabindex"] == "0"
    assert recovery_tab["aria-selected"] == "false"
    assert recovery_tab["aria-controls"] == "cockpitContent"
    assert recovery_tab["tabindex"] == "-1"
    assert evidence_tab["aria-selected"] == "false"
    assert evidence_tab["aria-controls"] == "cockpitContent"
    assert evidence_tab["tabindex"] == "-1"
    assert history_tab["aria-selected"] == "false"
    assert history_tab["aria-controls"] == "cockpitContent"
    assert history_tab["tabindex"] == "-1"
    assert panel["aria-labelledby"] == "tab-work"
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
    assert 'button.setAttribute("tabindex", isActive ? "0" : "-1");' in _asset_text(
        "/operator-api-state.js"
    )
    operator_main = _asset_text("/operator-main.js")
    assert 'document.addEventListener("keydown"' in operator_main
    assert 'event.key === "ArrowRight"' in operator_main
    assert 'event.key === "ArrowLeft"' in operator_main
    assert 'event.key === "Home"' in operator_main
    assert 'event.key === "End"' in operator_main
    assert "renderTruncationNotice(" in _asset_text("/operator-artifacts-documents.js")
    assert "function scrollActiveStageIntoView()" in _asset_text("/operator-shell-rendering.js")


def test_operator_css_custom_properties_are_resolved() -> None:
    css = _css_bundle()
    defined = set(re.findall(r"(--[a-zA-Z0-9_-]+)\s*:", css))
    referenced = set(re.findall(r"var\((--[a-zA-Z0-9_-]+)", css))

    assert "--ink" in defined
    assert not referenced - defined
