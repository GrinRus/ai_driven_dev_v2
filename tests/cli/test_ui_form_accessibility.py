from __future__ import annotations

from aidd.cli.ui_assets import operator_static_asset_for_route


def _asset(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_dynamic_remediation_and_intervention_fields_have_stable_form_identity() -> None:
    control = _asset("/operator-control-center.js")
    intervention = _asset("/operator-approvals-interventions.js")

    for expected in (
        'id="review-remediation-${index}" name="review_remediation"',
        'for="review-remediation-${index}"',
        'id="reviewRemediationNote" name="review_remediation_note"',
        'for="reviewRemediationNote"',
        'id="qa-remediation-${index}" name="qa_remediation"',
        'for="qa-remediation-${index}"',
        'id="qaRemediationNote" name="qa_remediation_note"',
        'for="qaRemediationNote"',
    ):
        assert expected in control
    for expected in (
        'id="intervention-target-${index}" name="intervention_target"',
        'for="intervention-target-${index}"',
        'id="operatorRequestText" name="operator_request"',
        'for="operatorRequestText"',
    ):
        assert expected in intervention


def test_onboarding_and_follow_up_fields_have_id_name_and_associated_labels() -> None:
    onboarding = _asset("/operator-onboarding.js")
    follow_up = _asset("/operator-next-flow-view.js")

    for field_id, name in (
        ("onboardingProjectRoot", "project_root"),
        ("onboardingWorkItem", "work_item"),
        ("onboardingRequest", "request"),
        ("onboardingForceContext", "force_context"),
    ):
        assert f'id="{field_id}" name="{name}"' in onboarding
        assert f'for="{field_id}"' in onboarding
    for field_id, name in (
        ("runComparisonBaseline", "comparison_baseline_run"),
        ("followUpWorkItem", "new_work_item"),
        ("followUpTitle", "title"),
        ("followUpInputPreview", "first_stage_input_preview"),
    ):
        assert f'id="{field_id}" name="{name}"' in follow_up
        assert f'for="{field_id}"' in follow_up
    assert 'name="source_selection"' in follow_up
    assert 'name="inherited_context"' in follow_up
    assert 'class="sr-only" for="${escapeHtml(textId)}"' in follow_up
