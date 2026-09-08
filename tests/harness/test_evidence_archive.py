from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
from pathlib import Path

import pytest

from aidd.harness.evidence_archive import (
    EvidenceArchiveError,
    export_evidence_archive,
    extract_evidence_archive,
    read_evidence_archive,
    retention_sidecar_path,
)
from aidd.harness.evidence_archive_contract import EvidenceRedaction
from aidd.harness.result_bundle_contract import (
    ResultBundleArtifact,
    ResultBundleIdentity,
    ResultBundleInventory,
    dump_result_bundle_inventory,
    validate_result_bundle_inventory,
)


def _sealed_bundle(tmp_path: Path) -> tuple[Path, ResultBundleIdentity]:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    files = {
        "verdict.md": "# Pass\n",
        "secret.txt": "provider payload should not leave the workspace\n",
    }
    artifacts = []
    for name, content in files.items():
        path = bundle / name
        path.write_text(content, encoding="utf-8")
        artifacts.append(
            ResultBundleArtifact(
                path=name,
                sha256=hashlib.sha256(content.encode()).hexdigest(),
                size_bytes=len(content.encode()),
            )
        )
    identity = ResultBundleIdentity(
        evaluation_run_id="eval-archive-001",
        product_run_id=None,
        scenario_id="AIDD-ARCHIVE-001",
        runtime_id="generic-cli",
        work_item="WI-ARCHIVE",
    )
    inventory = ResultBundleInventory(
        identity=identity,
        status="pass",
        artifacts=tuple(artifacts),
    )
    (bundle / "result-bundle-inventory.json").write_text(
        dump_result_bundle_inventory(inventory),
        encoding="utf-8",
    )
    return bundle, identity


def _redaction() -> EvidenceRedaction:
    return EvidenceRedaction(
        credentials_removed=True,
        provider_payloads_removed=True,
        target_paths_redacted=True,
        redacted_paths=("secret.txt",),
    )


def test_export_and_readback_survive_source_bundle_deletion(tmp_path: Path) -> None:
    bundle, identity = _sealed_bundle(tmp_path)
    archive = tmp_path / "retained" / "eval-archive-001.tar"

    retention = export_evidence_archive(
        bundle_root=bundle,
        archive_path=archive,
        source_revision="abcdef1234567",
        target_pin="1234567890abc",
        redaction=_redaction(),
    )
    shutil.rmtree(bundle)

    snapshot = read_evidence_archive(archive_path=archive)
    assert snapshot.archive_path == archive.resolve()
    assert snapshot.identity == identity
    assert snapshot.status == "pass"
    assert [item.path for item in snapshot.files] == [
        "artifact-digests.json",
        "result-bundle-inventory.json",
        "verdict.md",
    ]
    assert snapshot.excluded_paths == ("secret.txt",)
    assert snapshot.retention == retention

    extracted = tmp_path / "fresh-checkout" / "evidence"
    extract_evidence_archive(archive_path=archive, destination=extracted)
    assert (extracted / "verdict.md").read_text(encoding="utf-8") == "# Pass\n"
    assert (extracted / "result-bundle-inventory.json").is_file()
    assert not (extracted / "secret.txt").exists()
    restored_inventory = ResultBundleInventory.from_dict(
        json.loads((extracted / "result-bundle-inventory.json").read_text(encoding="utf-8"))
    )
    validate_result_bundle_inventory(inventory=restored_inventory, bundle_root=extracted)


def test_exports_are_deterministic_except_for_locator_metadata(tmp_path: Path) -> None:
    bundle, _identity = _sealed_bundle(tmp_path)
    first = tmp_path / "first.tar"
    second = tmp_path / "second.tar"
    kwargs = {
        "bundle_root": bundle,
        "source_revision": "abcdef1234567",
        "target_pin": "1234567890abc",
        "redaction": _redaction(),
    }
    first_retention = export_evidence_archive(archive_path=first, **kwargs)
    second_retention = export_evidence_archive(archive_path=second, **kwargs)

    assert first.read_bytes() == second.read_bytes()
    assert first_retention.sha256 == second_retention.sha256
    assert first_retention.locator != second_retention.locator


def test_tampered_archive_fails_digest_verification(tmp_path: Path) -> None:
    bundle, _identity = _sealed_bundle(tmp_path)
    archive = tmp_path / "archive.tar"
    export_evidence_archive(
        bundle_root=bundle,
        archive_path=archive,
        source_revision="abcdef1234567",
        target_pin="1234567890abc",
        redaction=_redaction(),
    )
    archive.write_bytes(archive.read_bytes() + b"tamper")

    with pytest.raises(EvidenceArchiveError, match="size|digest"):
        read_evidence_archive(archive_path=archive)


def test_tampered_retention_metadata_fails_provenance_verification(tmp_path: Path) -> None:
    bundle, _identity = _sealed_bundle(tmp_path)
    archive = tmp_path / "archive.tar"
    export_evidence_archive(
        bundle_root=bundle,
        archive_path=archive,
        source_revision="abcdef1234567",
        target_pin="1234567890abc",
        redaction=_redaction(),
    )
    sidecar = retention_sidecar_path(archive)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["target_pin"] = "fedcba9876543"
    sidecar.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(EvidenceArchiveError, match="target pin"):
        read_evidence_archive(archive_path=archive)


def test_read_requires_retention_sidecar(tmp_path: Path) -> None:
    bundle, _identity = _sealed_bundle(tmp_path)
    archive = tmp_path / "archive.tar"
    export_evidence_archive(
        bundle_root=bundle,
        archive_path=archive,
        source_revision="abcdef1234567",
        target_pin="1234567890abc",
        redaction=_redaction(),
    )
    retention_sidecar_path(archive).unlink()

    with pytest.raises(EvidenceArchiveError, match="sidecar"):
        read_evidence_archive(archive_path=archive)


def test_extract_rejects_existing_targets(tmp_path: Path) -> None:
    bundle, _identity = _sealed_bundle(tmp_path)
    archive = tmp_path / "archive.tar"
    export_evidence_archive(
        bundle_root=bundle,
        archive_path=archive,
        source_revision="abcdef1234567",
        target_pin="1234567890abc",
        redaction=_redaction(),
    )
    destination = tmp_path / "destination"
    (destination / "verdict.md").parent.mkdir(parents=True)
    (destination / "verdict.md").write_text("existing\n", encoding="utf-8")

    with pytest.raises(EvidenceArchiveError, match="already exists"):
        extract_evidence_archive(archive_path=archive, destination=destination)


def test_export_rejects_mutable_or_existing_destinations(tmp_path: Path) -> None:
    bundle, _identity = _sealed_bundle(tmp_path)
    with pytest.raises(EvidenceArchiveError, match="outside"):
        export_evidence_archive(
            bundle_root=bundle,
            archive_path=bundle / "archive.tar",
            source_revision="abcdef1234567",
            target_pin="1234567890abc",
            redaction=_redaction(),
        )

    archive = tmp_path / "archive.tar"
    archive.write_bytes(b"existing")
    with pytest.raises(EvidenceArchiveError, match="already present"):
        export_evidence_archive(
            bundle_root=bundle,
            archive_path=archive,
            source_revision="abcdef1234567",
            target_pin="1234567890abc",
            redaction=_redaction(),
        )


def test_read_rejects_duplicate_tar_members_even_with_updated_digest(tmp_path: Path) -> None:
    bundle, _identity = _sealed_bundle(tmp_path)
    archive = tmp_path / "archive.tar"
    export_evidence_archive(
        bundle_root=bundle,
        archive_path=archive,
        source_revision="abcdef1234567",
        target_pin="1234567890abc",
        redaction=_redaction(),
    )
    duplicate = tmp_path / "duplicate.tar"
    with tarfile.open(archive, "r:") as source, tarfile.open(duplicate, "w") as target:
        members = source.getmembers()
        for member in members + [members[-1]]:
            stream = source.extractfile(member)
            target.addfile(member, stream)
    sidecar = retention_sidecar_path(archive)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["locator"] = duplicate.resolve().as_posix()
    payload["sha256"] = hashlib.sha256(duplicate.read_bytes()).hexdigest()
    payload["size_bytes"] = duplicate.stat().st_size
    duplicate_sidecar = retention_sidecar_path(duplicate)
    duplicate_sidecar.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(EvidenceArchiveError, match="duplicate"):
        read_evidence_archive(archive_path=duplicate)
