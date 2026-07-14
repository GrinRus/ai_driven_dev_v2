# Document & Evidence Studio reference prompts

These project-bound references were generated with the built-in image generation path and
the `ui-mockup` use case. They communicate hierarchy, density, and interaction intent. The
written contract in `../../operator-frontend.md` wins when generated text or controls drift.

## Shared prompt

Use `00-style-anchor-document-studio.png` as a visual-system reference only, not as an edit
target. Generate a new shippable product UI screenshot with the same calm editorial character:

- warm off-white application canvas and white working surfaces;
- compact deep-teal brand/context bar;
- charcoal text, restrained teal actions, cool-gray dividers;
- amber, red, green, and blue only as status signals;
- Inter-like sans-serif UI text and monospace paths/ids;
- 6-8px corners, almost no shadow, no gradients, glow, glass, or decorative illustration;
- strong whitespace and typographic hierarchy instead of a card grid;
- one visually primary action per state;
- direct, straight-on application screenshot with no browser chrome or device frame;
- no fake percentages, generic analytics charts, graph wallpaper, marketing copy, or lorem ipsum.

Desktop screens use a 3:2 landscape canvas. The common top bar contains `AIDD`, stable
destinations `Inbox`, `Studio`, and `History`, project/run context, runtime readiness, and one
labelled overflow. Studio screens retain the canonical eight-stage strip and keep the selected
Markdown document dominant.

## 01 — Inbox desktop

Create the decision-first project entry. Select `Inbox` in the top navigation. Show the heading
`Needs your decision` with three ordered rows:

1. `Plan is waiting for one answer`, question `Should rollback require zero downtime?`, primary
   action `Answer question`, secondary action `View evidence`.
2. `Implement requested permission`, primary action `Review request`.
3. `QA is stale after remediation`, primary action `Rerun stale downstream`.

Below, show `Running now` with `Research · Attempt 1 · Last output 18s ago` and `Open live
output`. Keep `Flow complete` collapsed below. Do not show the stage rail, an analytics
dashboard, or equal-weight cards.

## 02 — Guided Setup desktop

Create Guided Delivery setup at step `3 of 4 · Runtime`. Show a narrow centered workflow with
the step labels `Project`, `Work Item`, `Runtime`, and `Review & Launch`. Summarize completed
choices `Local Project` and `WI-042`. In the active Runtime step show one selected runtime:
`codex`, `Ready`, command available, authentication evidence available, permission policy
`brokered`, and last launch evidence. Keep capabilities under `View capabilities`. Primary
action: `Review & Launch`. Secondary action: `Back`. Put `Project set and advanced options`
behind a collapsed disclosure. Do not show multiple competing setup panels.

## 03 — Active Studio desktop

Create the default live Studio at `Research`. The Decision Bar says `Research is running`,
`Attempt 1 · Elapsed 08:42 · Last output 18s ago`, with primary action `Open live output` and a
secondary overflow containing cancellation. The center document is `research-notes.md` with
readable sections `Repository context`, `Product constraints`, `Observed facts`, and `Open
questions`. Its final copy uses actual repository facts: Python 3.12 with `uv`, runtime-agnostic
orchestration under `src/aidd/core`, runtime-specific launch behavior under
`src/aidd/adapters`, one shared `.aidd/` workspace for CLI and UI, canonical Markdown stage
artifacts, validation before progression, repair or explicit stop after invalid output, raw
runtime-log visibility, the eight-stage Idea-to-QA flow, durable questions and answers, and
built-in harness/eval evidence. The left rail lists stage artifacts. The Evidence Inspector
shows `Live evidence`, three real milestones, and `No decision required`. Keep `Logs and
attempts` collapsed at the bottom. Do not invent progress percentages.

## 04 — Validation Repair desktop

Create Studio at `Plan` after validation failure. The Decision Bar says `Validation needs
repair`, `1 finding · Repair attempt 0 of 2`, with primary action `Run Repair` and secondary
`Request Change`. Center `plan.md`; highlight only the Rollback sentence related to the
finding. The Evidence Inspector says `Rollback criteria are incomplete`, references
`plan.md:28`, rule `plan.rollback.criteria`, and links `Open finding`, `View validator report`,
and `View repair brief` where available. Keep raw logs collapsed and secondary.

## 05 — Quality Gate desktop

Create the evidence-heavy `Review` Studio. The Decision Bar says `Review rejected two
findings` and uses primary action `Send selected to implement`. The center uses a restrained
split diff for the real repository change with file rows `src/aidd/cli/ui.py` and
`tests/cli/test_ui.py`; label additions and removals in text as well as color. A compact
`Implementation report` panel flags one claim-to-evidence mismatch. The Evidence Inspector
lists two selectable findings with ids `REV-01` and `REV-02`, evidence links, and a notice
`Review and QA will become stale after remediation`. Avoid a generic code-editor clone.

## 06 — History Filmstrip desktop

Create light-theme `History` for `WI-042 / Run 07`. Across the top, show the canonical stage
sequence with real outcomes: `Idea complete`, `Research complete`, `Plan repaired`,
`Review Spec complete`, `Tasklist complete`, `Implement complete`, `Review rejected`, `QA
stale`. The main timeline contains `Attempt 1 started`, `Runtime completed`, `Validation failed
· 3 findings`, `Repair brief created`, `Attempt 2 started`, and `Validation passed`. Select the
validation failure. The right inspector shows first decisive failure, exact artifacts
`validator-report.md` and `repair-brief.md`, actions `Open evidence` and `Open logs`, and the
message `Raw history is immutable`. Include `Return to live` only as a secondary control.

## 07 — Flow Complete desktop

Create the terminal Studio state only after fresh QA. The Decision Bar says `Flow complete`,
`QA passed with no blockers`, and promotes one action `Create New Work Item`. Show a concise
immutable handoff with final artifacts, QA verdict, repair count, approvals, answered
questions, source run, baseline, and lineage. Place `Start Follow-up Flow`, `Clone This Flow`,
`Run Eval / Scenario Batch`, and `Archive Run` inside a collapsed `Other next actions`
disclosure instead of a five-card grid. Keep `Open final evidence` secondary.

## 08 — Question mobile

Create a 9:16 mobile application screenshot at 390px logical width. Use a compact context bar
under 80px with `AIDD`, `WI-042 · Plan`, and overflow. Put the current decision in the first
viewport: `Plan needs your answer`, the blocking question `Should rollback require zero
downtime?`, a multiline answer field, resolution choices `Resolved`, `Partial`, and `Deferred`
with `Resolved` selected, and one sticky primary action `Save answer & resume`. Show `What will
happen` and `View evidence` as collapsed disclosures. The next content preview is `plan.md`.
Use 44px touch targets, no horizontal overflow, no desktop sidebars, and no tiny stage grid.
