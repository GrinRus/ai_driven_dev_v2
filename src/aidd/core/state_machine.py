from __future__ import annotations

from enum import StrEnum


class StageState(StrEnum):
    PENDING = "pending"
    PREPARING = "preparing"
    EXECUTING = "executing"
    VALIDATING = "validating"
    REPAIR_NEEDED = "repair-needed"
    BLOCKED = "blocked"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[StageState, frozenset[StageState]] = {
    StageState.PENDING: frozenset({StageState.PREPARING}),
    StageState.PREPARING: frozenset(
        {
            StageState.EXECUTING,
            StageState.BLOCKED,
            StageState.FAILED,
        }
    ),
    StageState.EXECUTING: frozenset(
        {
            StageState.VALIDATING,
            StageState.BLOCKED,
            StageState.FAILED,
        }
    ),
    StageState.VALIDATING: frozenset(
        {
            StageState.SUCCEEDED,
            StageState.REPAIR_NEEDED,
            StageState.BLOCKED,
            StageState.FAILED,
        }
    ),
    StageState.REPAIR_NEEDED: frozenset({StageState.PREPARING, StageState.FAILED}),
    StageState.BLOCKED: frozenset({StageState.PREPARING, StageState.FAILED}),
    StageState.SUCCEEDED: frozenset(),
    StageState.FAILED: frozenset(),
}

_TERMINAL_STATES = frozenset({StageState.SUCCEEDED, StageState.FAILED})


def all_stage_states() -> tuple[StageState, ...]:
    return tuple(StageState)


def allowed_transitions(from_state: StageState) -> frozenset[StageState]:
    return _ALLOWED_TRANSITIONS[from_state]


def is_valid_transition(from_state: StageState, to_state: StageState) -> bool:
    return to_state in allowed_transitions(from_state)


def is_terminal_state(state: StageState) -> bool:
    return state in _TERMINAL_STATES


def transition_stage_state(from_state: StageState, to_state: StageState) -> StageState:
    if not is_valid_transition(from_state=from_state, to_state=to_state):
        raise ValueError(f"Illegal stage transition: {from_state} -> {to_state}")
    return to_state
