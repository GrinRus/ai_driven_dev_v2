from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.evals.failure_corpus import (
    FailureCorpusError,
    load_failure_corpus,
    replay_failure_case,
)


def test_failure_corpus_loads_all_sanitized_cases() -> None:
    corpus = load_failure_corpus()

    assert corpus.schema_version == 1
    assert corpus.corpus_id == "w43-e1-s1-failure-corpus-v1"
    assert [case.case_id for case in corpus.cases] == [
        "malformed-question-resume",
        "service-document-placeholder",
        "malformed-rich-tasklist",
        "cascade-finding",
        "repair-exhaustion",
    ]
    assert corpus.source["credentials_removed"] is True


def test_every_failure_case_replays_to_its_primary_boundary() -> None:
    corpus = load_failure_corpus()

    replays = [replay_failure_case(corpus, case) for case in corpus.cases]

    assert all(replay.primary_signal for replay in replays)
    assert replays[0].primary_signal == "INTERVIEW-MALFORMED-DOCUMENT"
    assert replays[1].primary_signal == "STRUCT-STALE-STAGE-RESULT-PLACEHOLDER"
    assert replays[2].primary_signal == "RICH-TASKLIST-PARSE-ERROR"
    assert replays[3].observed_signals == (
        "SEM-PLACEHOLDER-CONTENT",
        "SEM-INCOMPLETE-SECTION",
    )
    assert replays[4].budget_exhausted is True
    assert replays[4].repair_attempts_used == 2
    assert replays[4].remaining_repair_attempts == 0


def test_corpus_retains_related_findings_without_replacing_primary_cause() -> None:
    corpus = load_failure_corpus()
    case = next(item for item in corpus.cases if item.case_id == "cascade-finding")

    replay = replay_failure_case(corpus, case)

    assert replay.primary_signal == "SEM-PLACEHOLDER-CONTENT"
    assert replay.related_signals == ("SEM-INCOMPLETE-SECTION",)
    assert case.related_findings == ("SEM-INCOMPLETE-SECTION",)


def test_corpus_rejects_fixture_path_escape(tmp_path: Path) -> None:
    source_root = load_failure_corpus().root
    destination = tmp_path / "corpus"
    for source in source_root.rglob("*"):
        if source.is_file():
            target = destination / source.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

    manifest_path = destination / "failure-corpus.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["cases"][0]["fixtures"]["questions"] = "../outside.md"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(FailureCorpusError, match="corpus-relative"):
        load_failure_corpus(destination)
