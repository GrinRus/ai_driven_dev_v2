# Prod-like Live Provider Acceptance

This contract defines the manual live-provider acceptance gate for Wave 36. It extends the
general live E2E catalog without creating another workflow, adapter, or UI execution path.

## Candidate and scenario

- Build the candidate wheel from a clean tracked `HEAD` snapshot created with `git archive`.
- Install the wheel into the harness-owned isolated tool home.
- Use `AIDD-LIVE-007`, whose `feature_size` is `medium`, and the pinned Hono revision
  `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`.
- Run the complete public `idea -> qa` stage graph through native `codex` and `claude-code`.
- Keep the canonical Codex `gpt-5.5` / `xhigh` live profile. Claude Code uses its native default
  model selection.

This is a local production-like audit, not a claim that the public target or provider service is
controlled production infrastructure.

## External execution roots

The launching operator must set `AIDD_LIVE_E2E_ROOT` to an existing directory outside the AIDD
source checkout. Each provider gets a fresh subtree with independent `work`, `reports`, and
`browser` directories. The black-box evaluator receives those paths through `--work-root`,
`--report-root`, and `--manual-frontend-evidence`.

The two providers must not reuse a target clone, `.aidd` workspace, install home, cache, run id,
answers, task attempts, patch, or evidence bundle. Provider authentication may be inherited from
the launching operator as documented by the live runner, but credentials are never copied into
the candidate, target, report, browser, or tracked documentation trees.

Run the provider-neutral gate before `aidd eval doctor` or any live command:

```bash
uv run --extra dev python -m aidd.harness.live_acceptance_preflight \
  harness/scenarios/live/hono-non-error-throw-handling.yaml \
  --runtime codex \
  --source-checkout "$PWD" \
  --external-root "$AIDD_LIVE_E2E_ROOT"
```

Repeat it with `--runtime claude-code`. The JSON result supplies the exact independent work,
report, and browser roots for the black-box command. A failed preflight must not allocate a live
run.

## Product and evaluator boundary

- The evaluator drives only supported CLI, loopback UI/API, operator-answer, quality-audit, and
  remediation surfaces.
- Core, adapters, validators, prompts, and Studio must not branch on a live scenario id, Hono task
  id, target repository, evidence root, or evaluator-only environment variable.
- Runtime-specific behavior remains adapter-owned and generic across scenarios.
- The explicit `aidd eval` facade may invoke harness code. Other product runtime and UI modules
  must not import live orchestration.
- The authored Hono request, repository pin, verification recipe, and task-specific rubric remain
  in the scenario manifest and live documentation.
- The target runtime may modify the target product checkout within the authored task. It must not
  write to the AIDD source checkout or another provider's roots.
- Harness metadata, config, and `.aidd` evidence must not be presented as target product changes.

The tracked AIDD tree is hashed before and after every live run. Any tracked change makes the run
invalid. Raw logs, screenshots, target patches, generated workspaces, absolute local paths,
credentials, and prompt contents remain outside Git.

## Execution and quality checkpoints

Run providers sequentially. After every completed product-evaluation stage, inspect the stage
output, runtime evidence, target diff, validator report, and runner audit, then write the required
`stage-quality-audits/<stage-run-id>.md`. Questions, approvals, repair, and review/QA remediation
use their normal durable paths; the operator must not replace model output to force progression.

Use the installed loopback `aidd ui` and Chromium to inspect actual run state. At minimum capture
bounded notes or screenshots for active execution, Implement task/finalization evidence,
Review/QA, and fresh terminal Flow Complete. Conditional recovery or approval states are recorded
only when they occur naturally. Record console, page, failed-request, overflow, and artifact/log
reachability observations. Imported browser evidence is manual and does not change the runner
verdict.

After terminal QA, run the manifest verification commands and write `flow-quality-report.md`,
`code-quality-report.md`, and `quality-report.md`. A run is counted clean only when execution
passes, every required stage audit exists, target verification passes, terminal QA is fresh, the
manual reports have no unresolved must-fix issue, and isolation checks remain clean.

## Failure handling

Classify the first decisive signal as environment/auth/network, provider CLI, adapter, core
orchestration, contract/validator/prompt, harness/eval, target setup, or model-authored artifact
quality.

An AIDD-owned defect blocks the active live task. Create one reviewable roadmap task in the owning
slice, add a provider-free regression test, fix the general contract, merge it, and start a fresh
run of the same manifest/runtime. Do not add provider- or scenario-specific product branches.
Provider quota/auth/network blockers are recorded and retried after the environment is restored;
they are not product defects. Model artifact misses use normal repair, interview, or remediation
before any prompt or validator change is considered.

If a fix changes the candidate SHA, previous provider acceptance is historical. Final acceptance
requires fresh Codex and Claude runs against the same clean AIDD SHA and target revision.

## Tracked acceptance summary

The final tracked summary records only the AIDD SHA, scenario/runtime/run ids, target revision,
tool versions, terminal outcomes, repair counts, verification results, artifact-manifest digests,
browser checkpoint summary, and classified findings. It must not contain raw runtime output,
target source, prompt bodies, credentials, participant data, or absolute paths.

Live execution remains manual-only. It must not be added to CI or release preflight.
