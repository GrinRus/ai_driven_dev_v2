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
    assert "operator-presentation.js" in filenames
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
        '"/operator-presentation.js"'
    )
    assert loader.index('"/operator-presentation.js"') < loader.index(
        '"/operator-api-state.js"'
    )


def test_operator_presentation_selector_is_browser_only_and_fail_closed() -> None:
    presentation = _asset_text("/operator-presentation.js")
    api_state = _asset_text("/operator-api-state.js")

    _assert_contains_all(
        presentation,
        (
            'new Set(["studio", "legacy"])',
            'new URLSearchParams(search).get("ui")',
            'return PRESENTATION_SELECTORS.has(requested) ? requested : "legacy";',
            "function resolveSurfaceRendererFor(entry, selector)",
            'presentation === "studio" ? `studio:${entry.id}` : entry.rollbackRenderer',
            "function resolveSurfaceRenderer(surfaceId",
            "function selectSurfaceRenderer(surfaceId, renderers)",
            'const effective = presentations.size === 1 ? [...presentations][0] : "mixed";',
            "SURFACE_PARITY_MANIFEST.map((entry)",
            "document.documentElement.dataset.presentationRequested",
            "document.documentElement.dataset.presentationEffective",
        ),
    )
    assert 'presentationSelector: window.aiddPresentation?.requested || "legacy"' in api_state
    assert 'presentationEffective: window.aiddPresentation?.effective || "legacy"' in api_state
    assert "fetch(" not in presentation
    assert "postJson(" not in presentation


def test_operator_surface_parity_manifest_is_complete_and_policy_free() -> None:
    parity = _asset_text("/operator-surface-parity.js")

    _assert_contains_all(
        parity,
        (
            'new Set(["legacy_only", "candidate", "parity_closed"])',
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
            "function surfaceParityEntry(surfaceId)",
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


def test_operator_css_layers_own_static_ui_surfaces() -> None:
    tokens = _asset_text("/operator-tokens.css")
    base = _asset_text("/operator-base.css")
    layout = _asset_text("/operator-layout.css")
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    assert ":root {" in tokens
    assert "--focus-ring:" in tokens
    assert "button:focus-visible" in base
    assert ".sr-only" in base
    assert "textarea {" in base
    assert ".operator-shell" in layout
    assert ".stage-rail" in layout
    assert ".cockpit" in layout
    assert ".brand-title" in layout
    assert "min-width: 0;" in layout
    assert ".topbar #runChip" in layout
    assert ".topbar #workItemChip" in layout
    assert "text-overflow: ellipsis;" in layout
    assert "body.evidence-log-mode .global-next-action-strip" in layout
    assert ".truncation-notice" in components
    assert ".definition-list-warning" in components
    assert ".truncation-notice ul" in components
    assert ".saved-answer" in components
    assert ".activity-detail" in components
    assert ".artifact-row" in components
    assert ".stage-document-workbench" in components
    assert ".workbench-side-row" in components
    assert ".project-home-rail" in components
    assert ".project-work-item-card" in components
    assert ".project-set-row" in components
    assert ".global-next-action-strip" in components
    assert ".global-next-action-strip.live-progress-active" in components
    assert ".live-progress-strip" in components
    assert ".live-progress-actions" in components
    assert ".run-progress-notice" in components
    assert ".run-progress-meta" in components
    assert ".recovery-card" in components
    assert ".recovery-workbench" in components
    assert ".recovery-hero" in components
    assert ".repair-resolved-summary" in components
    assert ".output-mirror-notice-list" in components
    assert ".validation-finding-summary.notice" in components
    assert ".evidence-drilldown" in components
    assert ".interview-loop-screen" in components
    assert ".validation-repair-center" in components
    assert ".repair-action-band" in components
    assert ".project-setup-grid" in components
    assert ".setup-readiness-checklist" in components
    assert ".flow-complete-state" in components
    assert ".flow-complete-mark" in components
    assert ".next-flow-action-card.recommended" in components
    assert ".terminal-summary-grid" in components
    assert ".run-history-state" in components
    assert ".lineage-node.current" in components
    assert ".next-flow-wizard" in components
    assert ".next-flow-wizard-frame" in components
    assert ".next-flow-stepper" in components
    assert ".source-finding-groups" in components
    assert ".source-selection-summary" in components
    assert ".source-finding-supporting" in components
    assert ".archive-confirmation" in components
    assert ".evidence-screen-stack" in components
    assert ".evidence-workbench-grid" in components
    assert ".workbench-toc" in components
    assert ".follow-up-definition-grid" in components
    assert '.editable-list-row input[type="text"]' in components
    assert ".inherited-context-toggle" in components
    assert ".launch-confirmation-grid" in components
    assert ".preflight-check" in components
    assert ".preflight-blocker-summary" in components
    assert ".launch-readiness-summary" in components
    assert ".clone-launch-summary" in components
    assert ".clone-draft-error-summary" in components
    assert ".launch-failure-summary" in components
    assert ".wizard-action-guard" in components
    assert ".log-panel" in components
    assert "@media (max-width: 760px)" in responsive
    assert ".workbench-main" in responsive
    assert ".global-next-action-strip" in responsive
    assert ".live-progress-strip" in responsive
    assert ".live-progress-actions" in responsive
    assert ".live-progress-meta" in responsive
    assert ".run-progress-meta" in responsive
    assert ".project-home-grid" in responsive
    assert ".handoff-metric-grid" in responsive
    assert ".lineage-flow" in responsive
    assert ".next-flow-wizard-frame" in responsive
    assert ".source-finding-groups" in responsive
    assert ".follow-up-definition-grid" in responsive
    assert ".launch-confirmation-grid" in responsive
    assert ".interview-loop-screen" in responsive
    assert ".validation-repair-center" in responsive
    assert "body.recovery-mode .cockpit" in responsive
    assert "body.evidence-log-mode .operator-shell" in responsive
    assert "body.evidence-log-mode .cockpit" in responsive
    assert "body.evidence-log-mode .stage-rail" in responsive
    assert "body.live-job-mode .operator-shell" in responsive
    assert "body.live-job-mode .cockpit" in responsive
    assert "body.live-job-mode .stage-rail" in responsive
    assert ".recovery-hero," in responsive
    assert ".workbench-toc-list" in responsive
    assert "scroll-padding-inline: 10px" in responsive


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
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in responsive
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
    assert "grid-column: 1 / -1;" in responsive
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
    assert "body.post-stage-next-action-mode .operator-shell" in responsive
    assert "body.post-stage-next-action-mode .cockpit" in responsive
    assert "body.post-stage-next-action-mode .stage-rail" in responsive
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
    assert "function renderFlowCompleteState()" in next_flow_view
    assert "function renderRunHistory()" in next_flow_view
    assert "async function renderCockpit()" in cockpit
    assert "function renderRecoveryActionBand(diagnostics)" in cockpit
    assert "function renderRepairTimeline(validation)" in cockpit
    assert "function renderResolvedRepairSummary(validation)" in cockpit
    assert "function renderRuntimePartialEvidence(firstFailure)" in cockpit
    assert "return renderFlowCompleteState();" in cockpit
    assert 'state.activeTab === "history"' in cockpit
    assert "function renderActivityTable()" in cockpit
    assert "revealCockpitOnMobile();" in cockpit
    assert "revealNextFlowWizardOnMobile();" in cockpit
    assert 'document.addEventListener("click"' in main
    assert 'event.target.closest("[data-refresh-dashboard]")' in main
    assert "requestCockpitReveal();" in main
    assert "refresh();" in main


def test_operator_next_flow_controller_and_view_keep_separate_boundaries() -> None:
    controller = _asset_text("/operator-next-flow-actions.js")
    dashboard_actions = _dashboard_actions()
    view = _asset_text("/operator-next-flow-view.js")
    loader = _asset_text("/operator.js")

    assert controller.count("return `") <= 1
    assert "innerHTML =" not in controller
    assert "function renderFlowCompleteState()" not in controller
    assert "function renderNextFlowWizardShell(" not in controller
    assert "async function startWorkflow()" not in controller
    assert "async function handleNextAction()" not in controller
    assert "async function startWorkflow()" in dashboard_actions
    assert "async function handleNextAction()" in dashboard_actions

    assert "function renderFlowCompleteState()" in view
    assert "function renderRunHistory()" in view
    assert "function renderNextFlowWizardShell(" in view
    assert "function renderLaunchConfirmation()" in view
    assert "function renderNextActionPanel()" in view
    assert "fetch(" not in view
    assert "postJson(" not in view

    assert loader.index('"/operator-dashboard-actions.js"') < loader.index(
        '"/operator-next-flow-actions.js"'
    )
    assert loader.index('"/operator-next-flow-actions.js"') < loader.index(
        '"/operator-next-flow-view.js"'
    )
    assert loader.index('"/operator-next-flow-view.js"') < loader.index(
        '"/operator-control-center.js"'
    )
    assert loader.index('"/operator-control-center.js"') < loader.index(
        '"/operator-stage-cockpit.js"'
    )
    assert loader.index('"/operator-stage-cockpit.js"') < loader.index(
        '"/operator-main.js"'
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
            'active?.scrollIntoView({behavior: "auto", block: "nearest", inline: "center"});',
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
            "renderFirstLaunchState();",
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
            "Provider version",
            "Provider command",
            "function liveJobActivityEvents()",
            "function activityEvents()",
            "function summarizeActivityDetails(details)",
            "function renderActivityDetail(details)",
            "function renderActivityTableMarkup(events)",
            "function renderActivityTable()",
            "function renderRecoveryWorkbench()",
            "primaryAction: {action: primary.action, label: primary.label",
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
            "body.live-job-mode .operator-shell {",
            "body.external-running-stage-mode .operator-shell {",
            "body.live-job-mode .cockpit {",
            "body.external-running-stage-mode .cockpit {",
            "body.live-job-mode .stage-rail {",
            "body.external-running-stage-mode .stage-rail {",
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
            "Required answers",
            "Blocked stage",
            'const savedAnswer = question.answer_resolution',
            "const draft = questionDraft(question.question_id)?.value || null;",
            'const answerText = draft?.text ?? question.answer_text ?? "";',
            'const resolutionValue = draft?.resolution || question.answer_resolution || '
            '"resolved";',
            'class="saved-answer"',
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


def test_operator_recovery_assets_prioritize_runtime_log_recovery() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")

    _assert_contains_all(
        cockpit,
        (
            "const RUNTIME_FAILURE_KINDS = new Set([",
            "runtime-exit-metadata-invalid",
            "provider-no-progress",
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
            'action: "inspect-runtime-log"',
            "isRuntimeFirstFailure(firstFailure) && runtimeAction",
            'label: runtimeAction.label || "Open logs"',
            "Runtime log",
        ),
    )
    assert cockpit.index("isRuntimeFirstFailure(firstFailure) && runtimeAction") < cockpit.index(
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
            'id="runAccountabilityCard"',
        ),
    )
    assert "runAccountability" in api_state
    assert "runAccountabilityError" in api_state


def test_operator_run_history_static_contract_covers_run_comparison_panel() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")
    next_flow = _next_flow_assets()
    api_state = _asset_text("/operator-api-state.js")

    _assert_contains_all(
        next_flow,
        (
            "function renderRunComparisonPanel()",
            "async function loadRunComparisonPanel()",
            "/api/run/comparison",
            "baseline_run_id",
            "target_run_id",
            "Run comparison",
            "Prompt hash deltas",
            "Stage status deltas",
            "Artifact hash deltas",
            "Validator outcome deltas",
            'id="runComparisonBaseline"',
            "data-run-comparison-refresh",
        ),
    )
    assert "void loadRunComparisonPanel()" in cockpit
    assert "runComparison" in api_state
    assert "runComparisonBaselineInput" in api_state


def test_operator_implement_review_static_contract_covers_project_set_grouping() -> None:
    control = _asset_text("/operator-control-center.js")

    _assert_contains_all(
        control,
        (
            "async function renderImplementReview()",
            "diffView.project_set_roots",
            "file.scope_status",
            "outside-project-set",
            "outside project set",
            "file.root_id",
            "file.root_label",
            "file.root_relative_root",
        ),
    )


def test_operator_implement_review_surfaces_missing_verification_evidence() -> None:
    control = _asset_text("/operator-control-center.js")

    _assert_contains_all(
        control,
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
            'verificationReady && selectedRuntimeReady() ? "" : "disabled"',
            "${renderImplementationProceedGuard(evidence)}",
            'kind: "implementation-verification"',
            'badge: "verification missing"',
            "${renderImplementationVerificationGap(implementation)}",
        ),
    )


def test_operator_review_and_qa_decision_summaries_prioritize_next_actions() -> None:
    api_state = _asset_text("/operator-api-state.js")
    control = _asset_text("/operator-control-center.js")
    next_flow = _next_flow_assets()
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        api_state,
        (
            "reviewFindingsView: null",
            "reviewFindingsRunId: \"\"",
            "qaVerdictView: null",
            "qaVerdictRunId: \"\"",
            "decision-detail-mode",
            "[\"review-findings\", \"qa-verdict\"].includes(state.workDetail)",
        ),
    )
    _assert_contains_all(
        control,
        (
            "function renderDecisionSummary({kind, tone, badge, title, body, primary, metrics})",
            "function renderReviewDecisionSummary(view, findings)",
            "Review rejected: fix blocking findings before QA",
            "Review approved: QA can start",
            "Primary action: Send selected to implement",
            "function renderRemediationRuntimeGuard(sourceStage, hasRemediationItems)",
            "Runtime readiness is required before sending ${escapeHtml(label)} back to implement.",
            "${renderRemediationRuntimeGuard(\"review\", Boolean(findings.length))}",
            "function renderQaCompletionGuard(view, hasRemediationItems)",
            "Accept complete is disabled while QA is not-ready.",
            "Send selected QA risks or issues back to implement, then rerun verification and QA.",
            "${renderQaCompletionGuard(view, Boolean(sourceItems.length))}",
            "return renderDecisionBar({",
            "renderReviewDecisionSummary(view, findings)",
            "function renderQaDecisionSummary(view, risks, issues)",
            "QA not ready: send selected items back to implement",
            "QA ready: run can be accepted",
            "QA ready with follow-up context",
            "renderQaDecisionSummary(view, risks, issues)",
            "${renderRemediationRuntimeGuard(\"qa\", Boolean(sourceItems.length))}",
            "state.reviewFindingsView = view",
            "state.qaVerdictView = view",
        ),
    )
    _assert_contains_all(
        next_flow,
        (
            "function activeModeDecisionPeek()",
            "function renderModeDecisionPeek()",
            "Review approved",
            "Review rejected",
            "QA ready",
            "QA not ready",
            "${renderModeDecisionPeek()}",
            "mode-decision-peek",
        ),
    )
    _assert_contains_all(
        components,
        (
            ".decision-summary {",
            "grid-template-columns: minmax(0, 1.1fr) minmax(260px, 0.9fr);",
            ".decision-summary.good {",
            ".decision-summary.warn {",
            ".decision-summary.bad {",
            ".decision-summary-metrics {",
            "grid-template-columns: repeat(4, minmax(0, 1fr));",
            ".decision-metric strong {",
            ".mode-decision-peek {",
            "display: none;",
        ),
    )
    assert ".decision-summary," in responsive
    assert ".decision-summary-metrics," in responsive
    assert ".mode-decision-peek {" in responsive
    assert "body.decision-detail-mode .operator-shell" in responsive
    assert "body.decision-detail-mode .cockpit" in responsive
    assert "body.decision-detail-mode .stage-rail" in responsive


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
    assert "body.stale-downstream-mode .operator-shell" in responsive
    assert "body.stale-downstream-mode .cockpit" in responsive
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


def test_operator_next_flow_asset_keeps_launch_resume_and_runtime_guard_contracts() -> None:
    next_flow = "\n".join((_dashboard_actions(), _next_flow_assets()))

    _assert_contains_all(
        next_flow,
        (
            "function renderFirstLaunchState()",
            "function setupPreviousRunContext()",
            "function renderPreviousRunContext(context)",
            "function renderSetupReadinessChecklist({ready, context})",
            "Readiness Checklist",
            "function renderFlowCompleteState()",
            "function renderNextFlowActions(handoff)",
            "function renderTerminalArtifacts(artifacts)",
            "function renderTerminalBlockers(blockers)",
            "function renderFollowUpCandidates(handoff)",
            "function renderBaselineSnapshot()",
            "Follow-up candidates",
            "Baseline snapshot",
            "function renderRunHistory()",
            "function renderLineageRows({run, lineage, candidates})",
            "function renderLineageCandidates(candidates)",
            "async function openNextFlowWizard(action)",
            "async function renderNextFlowWizardStep()",
            "requestNextFlowWizardReveal();",
            "async function archiveCompletedRun()",
            "function renderNextFlowSourceSelection()",
            "function renderFollowUpDefinition()",
            "function renderLaunchConfirmation()",
            "function renderNextFlowWizardProgress()",
            (
                "return state.dashboard?.work_item || "
                'state.dashboard?.run?.lineage?.source_work_item_id || "";'
            ),
            (
                "function renderNextFlowWizardShell({sectionClass = "
                "\"next-flow-wizard\", title, badge, badgeTone = \"\", body})"
            ),
            "Flow Launch Wizard",
            "Choose Flow Type",
            "Select Source Findings",
            "Define Work Item",
            "Review Clone Draft",
            "Confirm Launch",
            "function renderPreflightChecks(preflight)",
            "function blockingPreflightChecks(preflight)",
            "function renderPreflightBlockedSummary(wizard, preflight, backLabel)",
            "function renderLaunchFailureSummary(wizard, draft, backLabel)",
            "function renderLaunchReadinessSummary(wizard)",
            "function renderCloneLaunchSafetySummary(wizard)",
            "function renderCloneDraftCreationError(wizard)",
            "function cloneDraftCreationMessage(error, targetWorkItem)",
            (
                "function renderLaunchConfirmationActions({backPrimary, backLabel, "
                "launchLabel, blocked, launchBusy})"
            ),
            "function renderLaunchConfirmationGuards({blocked, readinessBlocked, backLabel})",
            "function renderAuditPreview(draft, preflight)",
            "async function loadLaunchConfirmation()",
            "async function launchNextFlowNow()",
            "async function createFollowUpDraftForLaunch(draft)",
            "async function refreshRuntimeReadinessForLaunch()",
            "function resetLaunchReadiness(wizard = state.nextFlowWizard)",
            "function nextFlowBrowserDraftIdentity(action = state.nextFlowWizard.action)",
            "function mergeNextFlowBrowserDraft(serverDraft, action = state.nextFlowWizard.action)",
            "function persistNextFlowBrowserDraft()",
            "clearOperatorDraft(nextFlowBrowserDraftIdentity());",
            "function invalidateFollowUpDraftPreview()",
            (
                'document.querySelectorAll("[data-follow-up-definition-error], '
                '[data-follow-up-list-blocker]")'
            ),
            "data-follow-up-definition-error",
            "definitionErrors",
            "function followUpDraftValidationErrors(draft)",
            "At least one acceptance criterion is required before preflight.",
            "At least one required evidence item is required before preflight.",
            "Fix these required launch inputs, then retry Continue to preflight.",
            "data-follow-up-list-blocker",
            "Required for preflight",
            "async function openCloneFlowDraft()",
            "function renderNewWorkItemHandoff()",
            "function renderEvalBatchHandoff()",
            "function selectedFollowUpListValues(name, fallbackItems = [])",
            "function allFollowUpListValues(name, fallbackItems = [])",
            "acceptance_criteria_all",
            "required_evidence_all",
            "selectedItems.map((item) => String(item))",
            'document.querySelectorAll("[data-follow-up-list-text]")',
            "textControl ? textControl.value : fallbackItems[index]",
            "function inheritedContextLinesFromItems(items = [])",
            "function selectedInheritedContextLines(items = [], fallbackLines = null)",
            "function followUpDraftValidationError(draft)",
            "function renderLaunchSourceLink(item)",
            'result.status === "blocked"',
            "wizard.preflightError = result.error",
            "wizard.preflightError = definitionError",
            "async function loadFollowUpDraft()",
            "Define Follow-up Work Item",
            "Definition needs attention",
            "Confirm and Launch Next Flow",
            "Preflight results",
            "data-clone-launch-summary",
            "Clone does not remediate this handoff",
            "Clone creates a separate run identity",
            "Clone reuses configuration in a new run identity",
            "Clone reuses configuration and baseline; it does not select source findings.",
            "not selected for clone",
            "configuration only",
            "Clone-only flow",
            "without clearing QA status",
            "data-clone-draft-error-summary",
            "Clone Draft Needs Attention",
            "Clone target is already in use",
            "A clone draft or work item already exists",
            "Open the existing work item from Active work items",
            "Clone still does not remediate QA.",
            "Preflight blocked before launch",
            "Launch is disabled until blocking checks pass.",
            "data-preflight-blocker-summary",
            "Launch Flow Now is disabled because preflight returned blocking checks.",
            "data-launch-readiness-summary",
            "Checking runtime readiness before launch",
            "Runtime readiness changed before launch",
            "Launch was not started. Resolve runtime readiness",
            "Checking Runtime...",
            "Launch will re-check runtime readiness before starting.",
            "data-launch-failure-summary",
            "Launch did not start",
            "Retry Launch",
            "The source run remains unchanged.",
            "Audit preview",
            "Launch Flow Now",
            "data-follow-up-field",
            "newWorkItemField.value.trim()",
            "titleField.value.trim()",
            "data-follow-up-list-text",
            "data-inherited-context",
            "data-next-flow-back-to-sources",
            "data-next-flow-confirm-preview",
            "data-next-flow-back-to-definition",
            "data-launch-flow-now",
            "function renderSourceFindingGroup(group)",
            "function renderSourceFindingItem(group, item)",
            "data-source-selection-id",
            "selectedSourceIds",
            "first-launch-state",
            "project-setup-state",
            "flow-complete-state",
            "run-history-state",
            "Run History / Lineage",
            "data-lineage-run-id",
            "data-lineage-work-item",
            "archive.archived",
            'data-lineage-run-id="${escapeHtml(sourceRun)}"',
            "${escapeHtml(candidate.label || candidate.work_item_id)}",
            "Review &amp; Launch",
            "Flow Complete",
            "Start Next Flow",
            "Final artifacts",
            "Blockers / safety",
            "Runtime fallback",
            "Previous-run context",
            "data-next-flow-action",
            "Select a runtime to start the first governed workflow run.",
            "Create or resume a work item before starting the governed workflow.",
            "const hasWorkItemContext = Boolean(state.dashboard?.work_item);",
            "const canRun = hasWorkItemContext && ready && runtime;",
            "data-first-launch-run",
            "data-first-launch-stage",
            "Run selected stage",
            "function activeJobBlocksNextAction(action)",
            "function activeJobNextActionState(action)",
            "function renderNextActionPanel()",
            "function renderGlobalNextActionStrip()",
            "state.onboarding?.setupRequired",
            "Run Next Action",
            "next-action-controls",
            "primaryValidationFinding()",
            "renderValidationFindingSummary(finding)",
            "Resume workflow",
            "Runtime selected and ready to start the governed workflow.",
            "Runtime selected. Resolve readiness before starting the governed workflow.",
            "Runtime selected. Start the workflow from the current work item.",
            "Runtime selected. Resolve readiness before starting the workflow.",
            "Continue with ${stageTitle(action.stage || state.activeStage)}",
            "Checking runtime readiness.",
            "Selected runtime is not ready.",
            "Current job is still running. Inspect logs before starting another action.",
            "Open Runtime Logs / Live Console for live output before starting another action.",
            "async function startWorkflow()",
            "Create or resume a work item before starting the workflow.",
            "async function handleNextAction()",
            "const payload = {runtime: state.selectedRuntime, log_follow: true};",
            "const payload = {stage, runtime: state.selectedRuntime, log_follow: true};",
            "if (state.activeRunId) payload.run_id = state.activeRunId;",
            'postJson("/api/workflow/run", payload)',
            'postJson("/api/stage/run", payload)',
            'postJson("/api/next-flow/follow-up-draft/create", {',
            'postJson("/api/next-flow/clone-draft/create", {',
            'postJson("/api/next-flow/launch", {',
            'postJson("/api/next-flow/archive", {',
            "first_stage_input: draft.first_stage_input_preview",
            "acceptance_criteria: draft.acceptance_criteria || []",
            "required_evidence: draft.required_evidence || []",
            "inherited_context: draft.inherited_context_lines",
            "Run archived for operator navigation.",
        ),
    )
    assert next_flow.index("${backPrimary ? actionRow : \"\"}") < next_flow.index(
        '<div class="launch-confirmation-grid">'
    )
    assert next_flow.index("${backPrimary ? actionGuards : \"\"}") < next_flow.index(
        '<div class="launch-confirmation-grid">'
    )
    assert next_flow.index('<div class="launch-confirmation-grid">') < next_flow.index(
        "${backPrimary ? \"\" : actionRow}"
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


def test_operator_static_screen_landmarks_cover_accepted_mission_control_surfaces() -> None:
    html = _asset_text("/")
    next_flow = _next_flow_assets()
    artifacts = _asset_text("/operator-artifacts-documents.js")
    cockpit = _asset_text("/operator-stage-cockpit.js")
    questions = _asset_text("/operator-questions.js")
    logs = _asset_text("/operator-logs-jobs.js")
    approvals = _asset_text("/operator-approvals-interventions.js")

    _assert_contains_all(
        html,
        (
            'aria-label="Operator controls"',
            'aria-label="Operator workspace"',
            'aria-label="Workflow navigation"',
            'aria-label="Stage cockpit"',
            'aria-label="Run details"',
            'aria-label="Activity and recent artifacts"',
            'role="tablist" aria-label="Stage cockpit views"',
            'role="tabpanel" aria-labelledby="tab-work" tabindex="0"',
        ),
    )
    _assert_contains_all(
        next_flow,
        (
            '<section class="surface flow-complete-state">',
            '<section class="surface run-history-state hierarchy-primary history-filmstrip">',
            '<section class="surface next-flow-wizard">',
            'sectionClass: "next-flow-wizard follow-up-definition"',
            'sectionClass: "next-flow-wizard launch-confirmation"',
            '<aside class="next-flow-stepper" aria-label="Flow Launch Wizard">',
            '<div class="source-finding-groups">',
            '<div class="lineage-flow">',
        ),
    )
    _assert_contains_all(
        artifacts + cockpit + questions + logs + approvals,
        (
            "Artifacts / Evidence Graph",
            "Stage Document Workbench",
            "Questions / Interview Loop",
            "Validation / Repair Center",
            "Runtime Logs / Live Console",
            "Approvals / Runtime Requests",
            "Request Change / Intervention Composer",
        ),
    )


def test_operator_flow_complete_static_contract_covers_terminal_handoff_actions() -> None:
    shell = _asset_text("/operator-shell-rendering.js")
    next_flow = _next_flow_assets()
    components = _asset_text("/operator-components.css")
    responsive = _asset_text("/operator-responsive.css")

    _assert_contains_all(
        next_flow,
        (
            "function renderFlowCompleteState()",
            "terminalHandoffTitle(handoff)",
            "terminalHandoffTone(handoff.status)",
            "terminalHandoffMark(handoff)",
            "terminalHandoffMessage(handoff)",
            "handoff.final_qa_status",
            "QA terminal handoff is ready for operator review",
            "QA did not clear this run",
            "The terminal handoff is blocked",
            "QA completed with recorded risks",
            "flow-complete-mark",
            "Start Next Flow",
            "terminal handoff",
            "function recommendedNextFlowDecision(handoff)",
            "function renderRecommendedNextFlowDecision(handoff)",
            "function renderTerminalRepairHighlights(highlights)",
            "function renderTerminalEvidenceSpotlight(handoff)",
            "function renderTerminalAttentionSpotlight(handoff)",
            "const TERMINAL_EVIDENCE_REQUIREMENTS",
            "function terminalEvidenceArtifacts(artifacts)",
            "function terminalEvidenceRequirement(key)",
            "function terminalMissingEvidence(artifacts)",
            "function handoffMissingTerminalEvidence(handoff)",
            "function renderTerminalMissingEvidence(missing)",
            "function renderGlobalTerminalEvidenceActions()",
            "function terminalEvidenceActionLabel(artifact)",
            "function terminalRepairDecisionPeek()",
            "repair resolved",
            "QA Did Not Clear",
            "Recorded QA Risks",
            "Terminal handoff blockers",
            "Evidence First",
            "Missing Evidence",
            "Missing Terminal Evidence",
            "Missing terminal evidence",
            "Missing ${escapeHtml(item.label)}",
            (
                "Required terminal evidence is missing; restore artifacts before "
                "starting any next flow."
            ),
            "Restore the required terminal evidence before choosing a next-flow action.",
            "before next-flow",
            "Terminal evidence shortcuts",
            "Runtime log",
            "QA report",
            "Raw runtime output for the terminal QA attempt.",
            "Final QA readiness and release recommendation.",
            "Document validation result for the terminal QA stage.",
            "Terminal stage status and handoff summary.",
            "runtime_log",
            "qa_report",
            "validator_report",
            "stage_result",
            "recommended next decision",
            "next decision blocked",
            "Resolved Repairs",
            "These validation issues were retried and resolved before QA handoff.",
            "handoff.repair_highlights",
            "renderTerminalAttentionSpotlight(handoff)",
            "renderTerminalEvidenceSpotlight(handoff)",
            "renderGlobalTerminalEvidenceActions()",
            "data-open-artifact",
            "QA is ready and no open blockers are recorded",
            "Terminal QA failed; carry failed evidence into a follow-up",
            "carry the current findings into follow-up work first",
            "renderRecommendedNextFlowDecision(handoff)",
            "function terminalHandoffNeedsRecovery(handoff)",
            "function terminalNextFlowSafetyNote(handoff, action)",
            "function separateScopeHandoffMessage(handoff)",
            "function evalBatchHandoffMessage(handoff)",
            "Recovery path: carries QA findings, blockers, or manual notes into new scoped work.",
            "Navigation only: does not resolve QA blockers or carry findings into remediation.",
            "Separate scope: does not inherit this failed QA evidence.",
            "Comparison only: does not repair or complete this terminal handoff.",
            "Separate scope only",
            "This starts unrelated work only.",
            "Use Start Follow-up Flow for remediation.",
            "This uses terminal handoff evidence for review",
            'blocker${blockerCount === 1 ? " remains" : "s remain"}',
            "next-flow-safety-note",
            "function renderArchiveHandoffWarning(handoff)",
            "function renderTerminalRecoveryWizardAction(handoff)",
            'data-next-flow-action="start-follow-up-flow"',
            "Archive does not resolve this handoff",
            "Use Start Follow-up Flow when QA evidence still needs remediation",
            "Archive is navigation metadata only; remediation starts with Start Follow-up Flow.",
            "History is review-only; remediation starts with Start Follow-up Flow.",
            'const historyActionClass = needsRecovery ? \' class="secondary"\' : "";',
            (
                '<button data-tab-shortcut="history" type="button"${historyActionClass}>'
                "Open Run History</button>"
            ),
            "renderTerminalRepairHighlights(handoff.repair_highlights || [])",
            "renderNextFlowActions(handoff)",
            "activeModeDecisionPeek() || terminalRepairDecisionPeek()",
            "next-flow-action-card",
            "recommended",
            "recommended after restore",
            "Final artifacts",
            "Blockers / safety",
            "Follow-up candidates",
            "Baseline snapshot",
            "Source run policy",
            "Runtime fallback",
            "No final artifacts recorded.",
            "No blockers detected in the final QA handoff.",
            'data-next-flow-action="${escapeHtml(action.action)}"',
        ),
    )
    _assert_contains_all(
        components,
        (
            ".next-flow-decision-spotlight {",
            "grid-template-columns: minmax(0, 1fr) auto;",
            ".next-flow-decision-spotlight .small-badge {",
            "justify-self: start;",
            "width: fit-content;",
            ".next-flow-decision-spotlight button {",
            "min-width: 156px;",
            ".next-flow-safety-note {",
            "font-weight: 800;",
            ".repair-highlight-spotlight {",
            "border-left: 4px solid var(--green);",
            ".repair-highlight-card {",
            "grid-template-columns: minmax(0, 1fr) auto;",
            ".repair-highlight-evidence button {",
            "white-space: nowrap;",
            ".terminal-attention-spotlight {",
            "border-left: 4px solid var(--red);",
            ".terminal-missing-evidence {",
            ".terminal-missing-row {",
            ".archive-risk-notice {",
            ".next-action-evidence-actions {",
            "flex-wrap: wrap;",
        ),
    )
    assert ".next-flow-decision-spotlight," in responsive
    assert ".terminal-attention-spotlight," in responsive
    assert ".repair-highlight-card," in responsive
    assert ".repair-highlight-evidence," in responsive
    assert ".next-action-evidence-actions," in responsive
    assert "body.terminal-handoff-mode .operator-shell" in responsive
    assert "body.terminal-handoff-mode .cockpit" in responsive
    assert "body.terminal-handoff-mode .stage-rail" in responsive
    assert "body.terminal-handoff-mode .project-home-rail" in responsive
    assert "body.terminal-repair-mode .operator-shell" in responsive
    assert "body.terminal-repair-mode .cockpit" in responsive
    assert "body.terminal-repair-mode .stage-rail" in responsive
    assert "body.terminal-repair-mode .project-home-rail" in responsive
    assert 'document.body.classList.contains("terminal-handoff-mode")' in shell
    assert 'document.body.classList.contains("terminal-repair-mode")' in shell


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


def test_operator_run_history_static_contract_covers_lineage_and_archive_labels() -> None:
    next_flow = _next_flow_assets()

    _assert_contains_all(
        next_flow,
        (
            "function renderRunHistory()",
            "Run History / Lineage",
            "parent run",
            (
                "const hasParentRun = Boolean(lineage.source_run_id "
                "&& lineage.source_run_id !== run.run_id);"
            ),
            "current run",
            "next work item",
            "not created",
            "Lineage rows",
            "Run actions",
            "Linked artifacts",
            "Relationship",
            "Run / work item",
            "Next action",
            "Source",
            "Baseline",
            "Archive",
            "archived",
            "data-lineage-run-id",
            "data-lineage-work-item",
            "renderLineageActions(handoff)",
            "renderLineageArtifactRefs()",
            "renderLineageRows({run, lineage, candidates})",
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


def test_operator_css_keeps_focus_and_screen_reader_contracts() -> None:
    css = _css_bundle()

    assert ".sr-only" in css
    assert "clip-path: inset(50%)" in css
    assert "position: absolute" in css
    assert "button:focus-visible" in css
    assert "--focus-ring:" in css
    assert "outline: var(--focus-width) solid var(--color-focus)" in css
    assert "box-shadow: var(--focus-shadow)" in css
    assert ".status-badge.cancelled" in css
    assert ".small-badge.running" in css
    assert ".small-badge.cancelling" in css
    assert ".small-badge.waiting-for-operator" in css
    assert ".run-progress-notice" in css
    assert ".run-progress-meta" in css
    assert ".activity-detail" in css
    assert ".log-actions" in css
    assert ".truncation-notice" in css
    assert ".stage-document-workbench" in css
    assert ".workbench-main" in css
    assert ".workbench-side-row" in css
    assert ".interview-loop-screen" in css
    assert ".validation-repair-center" in css
    assert ".repair-action-band" in css
    assert ".request-change-screen" in css
    assert ".request-change-grid" in css
    assert ".latest-request-summary" in css
    assert ".form-readiness-note" in css
    assert ".intervention-diff-preview" in css
    assert ".approval-console-screen" in css
    assert ".approval-summary-grid" in css
    assert ".approval-meta-grid" in css
    assert ".approval-audit-wrap" in css
    assert ".log-console-screen" in css
    assert ".log-source-strip" in css
    assert ".bounded-log-notice" in css
    assert ".audit-log-panel" in css
    assert ".evidence-graph-screen" in css
    assert ".evidence-artifact-browser" in css
    assert ".evidence-graph-canvas" in css
    assert ".evidence-node.selected" in css
    assert ".evidence-edge.selected" in css
    assert ".artifact-inspector" in css
    assert ".artifact-action-row" in css
    assert ".evidence-artifact-table" in css
    assert ".saved-answer" in css
    assert ".saved-answer-text" in css
    assert ".previous-run-context" in css
    assert ".flow-complete-state" in css
    assert ".terminal-attention-spotlight" in css
    assert ".terminal-evidence-spotlight" in css
    assert ".terminal-missing-evidence" in css
    assert ".next-flow-action-card" in css
    assert ".next-flow-wizard" in css
    assert ".source-selection-summary" in css
    assert ".source-finding-card" in css
    assert ".source-finding-supporting" in css
    assert ".bottom-dock.collapsed" in css
    assert ".bottom-dock-toggle-row" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "overflow-wrap: normal" in css
    assert ".archive-confirmation" in css
    assert ".follow-up-definition-grid" in css
    assert ".inherited-context-toggle" in css
    assert ".launch-confirmation-grid" in css
    assert ".preflight-check" in css
    assert ".loading-state" in css
    assert "scroll-padding-inline: 10px" in css


def test_operator_css_custom_properties_are_resolved() -> None:
    css = _css_bundle()
    defined = set(re.findall(r"(--[a-zA-Z0-9_-]+)\s*:", css))
    referenced = set(re.findall(r"var\((--[a-zA-Z0-9_-]+)", css))

    assert "--ink" in defined
    assert not referenced - defined
