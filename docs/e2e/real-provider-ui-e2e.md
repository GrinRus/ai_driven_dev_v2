# Real-Provider UI E2E Lane

This lane proves that the UI-first local operator path works with authenticated native
provider runtimes, not only the deterministic `generic-cli` fixture. It is manual local
evidence only. It must not run in CI/CD or release automation.

## Acceptance Matrix

Each provider smoke starts from a disposable local project root, runs `aidd ui` without
`--work-item`, completes setup mode, selects the runtime explicitly, and runs bounded
selected-stage execution through `idea -> research`.

| Runtime | Priority | Prerequisites | Smoke target | Evidence |
| --- | --- | --- | --- | --- |
| `codex` | first | `codex` binary available, provider auth active, configured native command ready | clean UI onboarding, work item creation, selected `codex`, `idea -> research` | UI URL, work item id, run id, job ids, logs, timeline, artifacts, terminal status |
| `claude-code` | second | `claude` binary available, provider auth active, configured native command ready | clean UI onboarding, work item creation, selected `claude-code`, `idea -> research` | UI URL, work item id, run id, job ids, logs, timeline, artifacts, terminal status |
| `opencode` | third | `opencode` binary available, provider auth active, configured native command ready | clean UI onboarding, work item creation, selected `opencode`, `idea -> research` | UI URL, work item id, run id, job ids, logs, timeline, artifacts, terminal status |
| `qwen` | optional | `qwen` binary available, provider auth active, experimental command ready | clean UI onboarding, work item creation, selected `qwen`, `idea -> research` | UI URL, work item id, run id, job ids, logs, timeline, artifacts, terminal status |

`generic-cli` remains the deterministic baseline and is not counted as real-provider
evidence for this lane.

## Provider Readiness Preflight

Run the preflight from the disposable project root before opening the browser:

1. Confirm `aidd --version` or `uv run aidd --version` names the artifact under test.
2. Run `aidd doctor --config <config>` and record the selected runtime readiness row.
3. Confirm the provider binary is in `PATH` or the config command is executable.
4. Confirm provider auth using the provider's own local command or an already-known
   authenticated session.
5. Confirm the smoke config keeps `.aidd/` project-local and does not point at the AIDD
   source checkout unless that source checkout is the target project.
6. Confirm the UI launch will use loopback, for example `--host 127.0.0.1 --port 0`.
7. Confirm runtime launch payloads include the explicit runtime id. A missing runtime
   must fail with `runtime is required`.

If a preflight step fails, record it as an environment blocker instead of substituting a
deterministic runtime.

## Smoke Procedure

For each provider:

1. Create a disposable audit root under `/tmp`.
2. Copy or create a small local target project under that audit root.
3. Start `aidd ui --config <config> --host 127.0.0.1 --port 0` from the target project.
4. Before setup, verify `/api/onboarding/state` returns setup mode and `/api/dashboard`
   requires project setup.
5. In the browser, validate the absolute project root.
6. Create work item `WI-W29-<RUNTIME>-UI-SMOKE` with a bounded request.
7. Select the provider runtime card explicitly.
8. Run `idea` with **Run selected stage** and wait for `/api/jobs/<job_id>` status
   `completed`.
9. Run `research` with **Run selected stage** or the next-action path and wait for
   `/api/jobs/<job_id>` status `completed`.
10. Verify the stage rail reports `idea` and `research` as `succeeded`.
11. Inspect live and persisted logs, timeline milestones, and Markdown artifacts.
12. Stop the UI server and remove the disposable project unless evidence must be retained
    outside Git.

## Evidence Template

Record only non-sensitive evidence in roadmap notes or an external evidence bundle:

- Runtime id: `<codex | claude-code | opencode | qwen>`
- AIDD artifact: `<source checkout | installed package version>`
- Project root: `<disposable path or redacted external bundle id>`
- UI URL: `<loopback URL>`
- Work item: `<work item id>`
- Run id: `<run id>`
- Jobs: `<idea job id, research job id>`
- Stage status: `<idea status, research status>`
- Logs: `<live stdout/stderr observed, persisted runtime.log observed>`
- Timeline: `<created/runtime/first-output/artifact/validation/completed observed>`
- Artifacts: `<idea-brief.md, research-notes.md, stage-result.md, validator-report.md>`
- Runtime selection: `<explicit runtime selected, missing-runtime launch rejected>`
- Cleanup: `<removed | retained outside Git with reason>`
- Blocker: `<none or blocker classification>`

## Blocker Taxonomy

Classify every failed smoke before opening implementation work:

- `auth/env` - missing binary, missing auth, missing local config, provider quota, or
  disposable project setup failure.
- `provider` - provider command starts but returns a provider-owned service or API error.
- `adapter` - provider output is valid enough to observe but AIDD's adapter maps,
  streams, exits, approvals, or errors incorrectly.
- `model-output` - runtime completes but writes incomplete or invalid stage Markdown.
- `AIDD bug` - AIDD UI/API/core behavior violates the acceptance matrix with valid
  environment and provider behavior.
- `docs mismatch` - product docs describe a behavior different from the observed shipped
  behavior.
- `deferred scope` - requested behavior is intentionally outside the current product
  boundary, such as unrelated multi-project execution.

Only `AIDD bug`, `adapter`, and confirmed `docs mismatch` findings become immediate
Wave 29 fix tasks. Provider auth, quota, and local environment blockers are recorded as
evidence blockers.
