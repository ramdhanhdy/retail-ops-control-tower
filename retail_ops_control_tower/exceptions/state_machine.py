"""Exception lifecycle state machine.

Valid transitions:
    RAISED -> OPEN
    OPEN -> IN_PROGRESS
    IN_PROGRESS -> RESOLVED
    RESOLVED -> CLOSED
    IN_PROGRESS -> PAUSED -> IN_PROGRESS
    IN_PROGRESS -> ESCALATED -> IN_PROGRESS
    IN_PROGRESS -> WAIVED -> CLOSED
    RESOLVED -> OPEN (reopen, creates new exception_id linked to parent)
"""

from __future__ import annotations


class InvalidTransition(Exception):
    """Raised when an invalid state transition is attempted."""


VALID_TRANSITIONS: dict[str, set[str]] = {
    "raised": {"open"},
    "open": {"in_progress"},
    "in_progress": {"resolved", "paused", "escalated", "waived"},
    "paused": {"in_progress"},
    "escalated": {"in_progress"},
    "resolved": {"closed", "open"},
    "closed": set(),
    "waived": {"closed"},
}


def can_transition(from_status: str, to_status: str) -> bool:
    """Check if a state transition is valid."""
    return to_status in VALID_TRANSITIONS.get(from_status, set())


def transition(from_status: str, to_status: str) -> str:
    """Execute a state transition, raising InvalidTransition if invalid."""
    if not can_transition(from_status, to_status):
        raise InvalidTransition(
            f"Cannot transition from '{from_status}' to '{to_status}'"
        )
    return to_status
