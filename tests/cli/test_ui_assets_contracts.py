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
    assert ".truncation-notice" in components
    assert ".saved-answer" in components
    assert ".artifact-row" in components
    assert ".stage-document-workbench" in components
    assert ".workbench-side-row" in components
    assert ".interview-loop-screen" in components
    assert ".validation-repair-center" in components
    assert ".repair-action-band" in components
    assert ".project-setup-grid" in components
    assert ".setup-mode-card.selected" in components
    assert ".flow-complete-state" in components
    assert ".next-flow-action-card.recommended" in components
    assert ".terminal-summary-grid" in components
    assert ".run-history-state" in components
    assert ".lineage-node.current" in components
    assert ".next-flow-wizard" in components
    assert ".source-finding-groups" in components
    assert ".follow-up-definition-grid" in components
    assert ".inherited-context-toggle" in components
    assert ".launch-confirmation-grid" in components
    assert ".preflight-check" in components
    assert ".log-panel" in components
    assert "@media (max-width: 760px)" in responsive
    assert ".workbench-main" in responsive
    assert ".setup-mode-grid" in responsive
    assert ".handoff-metric-grid" in responsive
    assert ".lineage-flow" in responsive
    assert ".source-finding-groups" in responsive
    assert ".follow-up-definition-grid" in responsive
    assert ".launch-confirmation-grid" in responsive
    assert ".interview-loop-screen" in responsive
    assert ".validation-repair-center" in responsive
    assert "scroll-padding-inline: 10px" in responsive


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
    assert "function renderInterviewSummary(view)" in questions
    assert "function renderBlockedStageContext(view)" in questions
    assert "async function answerAndResume(questionId)" in questions
    assert "async function resumeAfterAnswers()" in questions
    assert "async function renderApprovals()" in approvals
    assert "async function submitIntervention()" in approvals
    assert "async function renderLogs()" in logs
    assert "async function startJobPolling(job)" in logs
    assert "async function startWorkflow()" in next_flow
    assert "async function handleNextAction()" in next_flow
    assert "function renderFlowCompleteState()" in next_flow
    assert "function renderRunHistory()" in next_flow
    assert "async function renderCockpit()" in cockpit
    assert "function renderRecoveryActionBand(diagnostics)" in cockpit
    assert "function renderRepairTimeline(validation)" in cockpit
    assert "return renderFlowCompleteState();" in cockpit
    assert 'state.activeTab === "history"' in cockpit
    assert "function renderActivityTable()" in cockpit
    assert 'document.addEventListener("click"' in main
    assert "refresh();" in main


def test_operator_api_state_asset_keeps_dashboard_runtime_and_tab_contracts() -> None:
    api_state = _asset_text("/operator-api-state.js")

    _assert_contains_all(
        api_state,
        (
            'const STAGES = ["idea", "research", "plan", "review-spec", "tasklist", '
            '"implement", "review", "qa"];',
            "const SETUP_MODES = [",
            'id: "new-work-item"',
            'label: "New Work Item"',
            'id: "follow-up-flow"',
            'label: "Follow-up Flow"',
            'id: "clone-previous-flow"',
            'label: "Clone Previous Flow"',
            'id: "eval-scenario-batch"',
            'label: "Eval / Scenario Batch"',
            'activeRunId: ""',
            'setupMode: "new-work-item"',
            "nextFlowWizard: {",
            'step: "sources"',
            "sourceFindings: null",
            "followUpDraft: null",
            "selectedSourceIds: []",
            "function sourceFindingsUrl()",
            "/api/next-flow/source-findings",
            "readinessLoading: true",
            'readinessError: ""',
            "function escapeHtml(value)",
            "function compactPath(value, maxLength = 56)",
            "function pathLine(value, maxLength = 56)",
            'title="${escapeHtml(text)}"',
            "${escapeHtml(compactPath(text, maxLength))}",
            "async function fetchDashboard()",
            "dashboardUrl()",
            "/api/dashboard",
            'state.activeRunId = state.dashboard.run?.run_id || "";',
            "version.startsWith(\"v\") ? version : `v${version || \"dev\"}`",
            'api("/api/runtime-readiness")',
            'if (element.textContent === message) element.textContent = "";',
            'button.setAttribute("aria-selected", isActive ? "true" : "false");',
            'content.setAttribute("aria-labelledby", `tab-${tab}`);',
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


def test_operator_cockpit_asset_keeps_overview_sidebar_and_activity_contracts() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")

    _assert_contains_all(
        cockpit,
        (
            "async function renderCockpit()",
            "renderFirstLaunchState();",
            "renderQuestionCards({showResume: true})",
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
            "function renderActivityTable()",
            "renderRuntimeSelector();",
            "await renderCockpit();",
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
            "function renderRequirementList(requirements)",
            "function renderValidationResults(results)",
            "function renderMissingEvidence(requirements)",
            "Artifact tree",
            "Contract requirements",
            "Validation results",
            "Missing evidence",
            "References",
            "Version history",
            "/api/stage/workbench?${params.toString()}",
            'params.set("source_limit", String(MAX_ARTIFACT_READ_BYTES));',
            'data-artifact-mode="diff"',
            'renderTruncationNotice("artifact", view, state.artifactViewMode)',
            "${renderMarkdown(view.text)}",
            "async function inspectArtifactReference({stage, key, path, kind})",
            "data-artifact-key",
        ),
    )


def test_operator_questions_asset_keeps_answer_resolution_and_saved_answer_contracts() -> None:
    questions = _asset_text("/operator-questions.js")

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
            "function renderInterviewSummary(view)",
            "function renderBlockedStageContext(view)",
            "Questions / Interview Loop",
            "Required answers",
            "Blocked stage",
            'const savedAnswer = question.answer_resolution',
            'class="saved-answer"',
            "Saved ${escapeHtml(question.answer_resolution)} answer",
            "Answer recorded in answers.md",
            "data-answer-resume-all",
            'resolution: resolution?.value || "resolved"',
            'option value="partial"',
            'option value="deferred"',
            "async function answerAndResume(questionId)",
            "async function resumeAfterAnswers()",
        ),
    )


def test_operator_recovery_assets_keep_repair_center_contracts() -> None:
    cockpit = _asset_text("/operator-stage-cockpit.js")

    _assert_contains_all(
        cockpit,
        (
            "function repairCenterStatus(validation, stopped)",
            "repair-exhausted",
            "explicit-stop",
            "function renderRecoveryActionBand(diagnostics)",
            "function renderRepairTimeline(validation)",
            "function renderBlockedStageRecovery(diagnostics)",
            "Validation / Repair Center",
            "Repair Available",
            "Run Repair",
            "Stop Run",
            "Request Change",
            "Validation attempt timeline",
            "Blocked questions",
            "Answers path",
            "data-run-repair",
            "data-stop-run",
            'data-tab-shortcut="request"',
        ),
    )


def test_operator_approvals_asset_keeps_request_and_intervention_contracts() -> None:
    approvals = _asset_text("/operator-approvals-interventions.js")

    _assert_contains_all(
        approvals,
        (
            "async function renderRequestChange()",
            "async function renderApprovals()",
            "async function submitApproval(requestId, action)",
            "async function submitIntervention()",
            "function requestChangeTargetEntries(documents, context)",
            "function selectedInterventionTargets()",
            "function renderInterventionDiffPreview(requestText, targetDocuments)",
            "function updateInterventionPreview()",
            "function renderRequestChangeAuditLog(context)",
            "function renderApprovalQueueSummary({requests, decisions, pendingIds, diagnostics})",
            "function renderApprovalDiffPreview(request)",
            "function renderApprovalAuditLog(requests, decisions, pendingIds, diagnostics = null)",
            "function renderApprovalsSurface({view, diagnostics, requests, decisions, pendingIds})",
            "Request Change / Intervention Composer",
            "Approvals / Runtime Requests",
            "Diff Preview",
            "Approval Audit Log",
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
            "/api/jobs/${encodeURIComponent(state.activeJobId)}/operator-requests",
            "target_documents: targetDocuments",
            "request.created_at_utc",
            "escapeHtml(JSON.stringify(payload, null, 2))",
            "if (state.activeRunId) payload.run_id = state.activeRunId;",
            'postJson("/api/stage/interact", payload)',
        ),
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
            "Correlated Events / Audit Log",
            "bounded-log-notice",
            'renderTruncationNotice("log", view)',
            "No runtime log for this stage yet",
            "data-log-filter",
            "data-log-raw",
            "state.rawLogMode",
            'state.logFilter === "all" && rawText ? rawText : rawTextFromEntries(filtered)',
            "function renderLiveJobActions()",
            "function activeJobCancelLabel()",
            "async function cancelActiveJob()",
            "data-cancel-job",
            "Cancel job",
            "Cancelling...",
            "Cancelled",
            "/api/jobs/${encodeURIComponent(state.activeJobId)}/cancel",
            'new Set(["running", "waiting-for-operator", "cancelling"])',
            'state.activeJobStatus?.status === "running"',
            "state.activeJobStatus.stage === state.activeStage",
            "state.activeJobLogChunks.length",
            "activeJobLogChunks.push(...(logs.chunks || []));",
            "/api/jobs/${encodeURIComponent(state.activeJobId)}/logs?cursor=${state.activeJobCursor}",
            "state.activeJobStatus.status === \"waiting-for-operator\"",
            "async function startJobPolling(job)",
            "renderActivityTable();",
        ),
    )


def test_operator_next_flow_asset_keeps_launch_resume_and_runtime_guard_contracts() -> None:
    next_flow = _asset_text("/operator-next-flow-actions.js")

    _assert_contains_all(
        next_flow,
        (
            "function renderFirstLaunchState()",
            "function setupPreviousRunContext()",
            "function renderSetupModeSelector(context)",
            "function renderPreviousRunContext(context)",
            'aria-disabled="true" disabled',
            "function renderFlowCompleteState()",
            "function renderNextFlowActions(handoff)",
            "function renderTerminalArtifacts(artifacts)",
            "function renderTerminalBlockers(blockers)",
            "function renderRunHistory()",
            "function renderLineageRows({run, lineage, candidates})",
            "function renderLineageCandidates(candidates)",
            "async function openNextFlowWizard(action)",
            "function renderNextFlowSourceSelection()",
            "function renderFollowUpDefinition()",
            "function renderLaunchConfirmation()",
            "function renderPreflightChecks(preflight)",
            "function renderAuditPreview(draft, preflight)",
            "async function loadLaunchConfirmation()",
            'result.status === "blocked"',
            "wizard.preflightError = result.error",
            "async function loadFollowUpDraft()",
            "Define Follow-up Work Item",
            "Confirm and Launch Next Flow",
            "Preflight results",
            "Audit preview",
            "Launch Flow Now",
            "data-follow-up-field",
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
            'data-lineage-run-id="${escapeHtml(sourceRun)}"',
            "${escapeHtml(candidate.label || candidate.work_item_id)}",
            "Project Setup",
            "Flow Complete",
            "Start Next Flow",
            "Final artifacts",
            "Blockers / safety",
            "Runtime fallback",
            "Previous-run context",
            "data-setup-mode",
            "data-next-flow-action",
            "Select a runtime to start the first governed workflow run.",
            "data-first-launch-run",
            "function renderNextActionPanel()",
            "Resume workflow",
            "Continue with ${stageTitle(action.stage || state.activeStage)}",
            "Checking runtime readiness.",
            "Selected runtime is not ready.",
            "async function startWorkflow()",
            "async function handleNextAction()",
            "const payload = {runtime: state.selectedRuntime, log_follow: true};",
            "const payload = {stage, runtime: state.selectedRuntime, log_follow: true};",
            "if (state.activeRunId) payload.run_id = state.activeRunId;",
            'postJson("/api/workflow/run", payload)',
            'postJson("/api/stage/run", payload)',
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
            'event.target.closest("[data-first-launch-run]")',
            'closest("[data-setup-mode]")',
            "requestedMode.requiresPreviousRun",
            "setupPreviousRunContext().available",
            'closest("[data-next-flow-action]")',
            'nextFlowAction.dataset.nextFlowAction === "start-follow-up-flow"',
            "await openNextFlowWizard(nextFlowAction.dataset.nextFlowAction)",
            'closest("[data-source-selection-id]")',
            "setSourceFindingSelection",
            'closest("[data-close-next-flow-wizard]")',
            'closest("[data-next-flow-continue]")',
            "await loadFollowUpDraft()",
            'closest("[data-next-flow-back-to-sources]")',
            'closest("[data-next-flow-confirm-preview]")',
            "await loadLaunchConfirmation()",
            'closest("[data-next-flow-back-to-definition]")',
            'closest("[data-launch-flow-now]")',
            "Launch endpoint is queued for the private next-flow API slice.",
            "Start Next Flow wizard is queued for the next UI slice.",
            'event.target.id === "operatorRequestText"',
            'closest("[data-intervention-target]")',
            "updateInterventionPreview();",
            'if (state.activeTab === "overview") await renderCockpit();',
            'closest("[data-artifact-stage]")',
            'closest("[data-artifact-key]")',
            "data-log-filter",
            "data-log-raw",
            'closest("[data-answer-resume-all]")',
            'closest("[data-run-repair]")',
            'closest("[data-stop-run]")',
            "Stop Run requires an active UI-started job.",
            "refresh();",
        ),
    )
    assert "Promise.all([fetchDashboard(), fetchReadiness()])" not in main
    assert 'body: JSON.stringify({runtime: "generic-cli"})' not in bundle
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
    overview_tab = _attrs_for("button", id="tab-overview", role="tab")
    questions_tab = _attrs_for("button", id="tab-questions", role="tab")
    history_tab = _attrs_for("button", id="tab-history", role="tab")
    panel = _attrs_for("div", id="cockpitContent", role="tabpanel")

    assert overview_tab["aria-selected"] == "true"
    assert overview_tab["aria-controls"] == "cockpitContent"
    assert questions_tab["aria-selected"] == "false"
    assert questions_tab["aria-controls"] == "cockpitContent"
    assert history_tab["aria-selected"] == "false"
    assert history_tab["aria-controls"] == "cockpitContent"
    assert panel["aria-labelledby"] == "tab-overview"
    assert panel["tabindex"] == "0"
    assert 'data-tab-shortcut="history"' in _asset_text("/")


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
    css = _css_bundle()

    assert ".sr-only" in css
    assert "clip-path: inset(50%)" in css
    assert "position: absolute" in css
    assert "button:focus-visible" in css
    assert "--focus-ring:" in css
    assert "outline: 3px solid var(--focus-ring)" in css
    assert "box-shadow: 0 0 0 4px var(--focus-ring-soft)" in css
    assert ".status-badge.cancelled" in css
    assert ".small-badge.running" in css
    assert ".small-badge.cancelling" in css
    assert ".small-badge.waiting-for-operator" in css
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
    assert ".intervention-diff-preview" in css
    assert ".approval-console-screen" in css
    assert ".approval-summary-grid" in css
    assert ".approval-meta-grid" in css
    assert ".approval-audit-wrap" in css
    assert ".log-console-screen" in css
    assert ".log-source-strip" in css
    assert ".bounded-log-notice" in css
    assert ".audit-log-panel" in css
    assert ".saved-answer" in css
    assert ".saved-answer-text" in css
    assert ".setup-mode-card" in css
    assert ".previous-run-context" in css
    assert ".flow-complete-state" in css
    assert ".next-flow-action-card" in css
    assert ".next-flow-wizard" in css
    assert ".source-finding-card" in css
    assert ".follow-up-definition-grid" in css
    assert ".inherited-context-toggle" in css
    assert ".launch-confirmation-grid" in css
    assert ".preflight-check" in css
    assert ".loading-state" in css
    assert "scroll-padding-inline: 10px" in css
