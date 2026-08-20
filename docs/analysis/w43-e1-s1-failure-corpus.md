# Wave 43 Failure Corpus

This note records the evidence-only corpus for `W43-E1-S1-T1`.  It is a sanitized,
provider-free replay bundle for the ownership and repair work that follows; it does not
change runtime behavior or claim that a provider was launched in CI.

## Provenance and sanitization

- Corpus: `w43-e1-s1-failure-corpus-v1`.
- Source reference: retained `IUIT-1203` evidence, reduced to the failure shapes required by
  the Wave 43 ownership and repair contracts.
- Runtime identity is retained only as a categorical `qwen` value. Provider payloads,
  credentials, target-repository paths, timestamps, and other identifying material are
  removed or fixed for deterministic replay.
- The corpus contains no network or provider invocation. Fixtures are read-only inputs to
  existing parsers and repair-budget arithmetic.
- The manifest is
  [`failure-corpus.json`](../../tests/fixtures/w43-e1-s1-failure-corpus/failure-corpus.json).

## Retained cases

| Case | Runtime | Stage | Attempt mode | First decisive boundary | Automatic repair consumed | Related findings |
| --- | --- | --- | --- | --- | ---: | --- |
| `malformed-question-resume` | `qwen` | `research` | `resume` | `INTERVIEW-MALFORMED-DOCUMENT` in `questions.md` | `0/2` | `CROSS-BLOCKING-UNANSWERED` |
| `service-document-placeholder` | `qwen` | `plan` | `initial` | `STRUCT-STALE-STAGE-RESULT-PLACEHOLDER` in `stage-result.md` | `0/2` | `SEM-INCOMPLETE-SECTION` |
| `malformed-rich-tasklist` | `qwen` | `tasklist` | `repair` | `RICH-TASKLIST-PARSE-ERROR` in `tasklist.md` | `1/2` | `CROSS-TASKLIST-PLAN-DEPENDENCY` |
| `cascade-finding` | `qwen` | `plan` | `repair` | `SEM-PLACEHOLDER-CONTENT` in `plan.md` | `1/2` | `SEM-INCOMPLETE-SECTION` |
| `repair-exhaustion` | `qwen` | `implement` | `repair` | `CROSS-REPAIR-BUDGET-EXHAUSTED` in `repair-history.md` | `2/2` | `SEM-PLACEHOLDER-CONTENT` |

The first boundary is the primary cause used for diagnosis. Related findings remain in the
manifest so later root-cause and severity work can collapse cascades without deleting the
original evidence.

## Replay contract

`aidd.evals.failure_corpus.load_failure_corpus()` validates schema, case identity, safe
relative fixture paths, and the sanitization flags.  `replay_failure_case()` then uses:

- the existing interview Markdown parsers for malformed question/answer input;
- the existing placeholder vocabulary for the service-document placeholder;
- the existing rich task-plan parser for malformed task cards;
- the canonical validator-report parser for cascade findings; and
- the existing repair-attempt arithmetic for exhaustion.

The focused eval test asserts that all five cases replay to their declared primary signal,
that the cascade retains its related finding, and that exhaustion consumes exactly the
declared budget.  A missing signal, unsafe path, credential-like fixture content, or budget
drift fails closed.

## Scope boundary

This artifact deliberately does not define the ownership matrix, alter stage output
resolution, normalize candidate documents, or add a repair extension. Those are later Wave
43 tasks and must consume this retained corpus as evidence rather than mutate it.
