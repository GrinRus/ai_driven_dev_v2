from __future__ import annotations

import pytest

from aidd.core.state_machine import (
    StageState,
    all_stage_states,
    allowed_transitions,
    is_terminal_state,
    is_valid_transition,
    transition_stage_state,
)


def test_all_stage_states_exposes_canonical_sequence() -> None:
    assert all_stage_states() == (
        StageState.PENDING,
        StageState.PREPARING,
        StageState.EXECUTING,
        StageState.VALIDATING,
        StageState.REPAIR_NEEDED,
        StageState.BLOCKED,
        StageState.SUCCEEDED,
        StageState.FAILED,
    )


def test_state_machine_accepts_primary_happy_path_transitions() -> None:
    state = StageState.PENDING
    state = transition_stage_state(state, StageState.PREPARING)
    state = transition_stage_state(state, StageState.EXECUTING)
    state = transition_stage_state(state, StageState.VALIDATING)
    state = transition_stage_state(state, StageState.SUCCEEDED)

    assert state == StageState.SUCCEEDED
    assert is_terminal_state(state) is True


def test_state_machine_allows_block_and_repair_loops() -> None:
    assert is_valid_transition(StageState.EXECUTING, StageState.BLOCKED) is True
    assert is_valid_transition(StageState.BLOCKED, StageState.PREPARING) is True
    assert is_valid_transition(StageState.VALIDATING, StageState.REPAIR_NEEDED) is True
    assert is_valid_transition(StageState.REPAIR_NEEDED, StageState.PREPARING) is True


def test_state_machine_rejects_illegal_transition() -> None:
    with pytest.raises(ValueError, match="Illegal stage transition"):
        transition_stage_state(StageState.PENDING, StageState.VALIDATING)


def test_terminal_states_have_no_allowed_transitions() -> None:
    assert allowed_transitions(StageState.SUCCEEDED) == frozenset()
    assert allowed_transitions(StageState.FAILED) == frozenset()
