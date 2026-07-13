"""Machine-checkable transition tables for separate LAOS aggregates."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import StateConflict


@dataclass(frozen=True, slots=True)
class TransitionTable:
    aggregate: str
    version: str
    transitions: dict[str, frozenset[str]]

    def require(self, current: str, target: str) -> None:
        if target not in self.transitions.get(current, frozenset()):
            raise StateConflict(
                f"illegal {self.aggregate} transition: {current} -> {target}",
                code="ILLEGAL_STATE_TRANSITION",
                context={"aggregate": self.aggregate, "current": current, "target": target},
            )


def _table(aggregate: str, transitions: dict[str, set[str]]) -> TransitionTable:
    return TransitionTable(aggregate, "1.0.0", {key: frozenset(value) for key, value in transitions.items()})


TRANSITION_TABLES: dict[str, TransitionTable] = {
    "engagement": _table(
        "engagement",
        {
            "draft": {"active", "cancelled"},
            "active": {"blocked", "accepted", "cancelled"},
            "blocked": {"active", "cancelled"},
        },
    ),
    "task": _table(
        "task",
        {
            "planned": {"ready", "cancelled"},
            "ready": {"active", "cancelled"},
            "active": {"blocked", "review", "cancelled"},
            "blocked": {"ready", "cancelled"},
            "review": {"accepted", "ready"},
        },
    ),
    "action_attempt": _table(
        "action_attempt",
        {
            "created": {"active", "aborted"},
            "active": {"submitted", "aborted"},
            "submitted": {"verified", "rejected"},
            "rejected": {"aborted"},
        },
    ),
    "criterion": _table(
        "criterion",
        {
            "open": {"proven", "rejected"},
            "proven": {"reviewed", "open", "rejected"},
            "reviewed": {"accepted", "open", "rejected"},
        },
    ),
    "side_effect": _table(
        "side_effect",
        {
            "proposed": {"approved", "failed"},
            "approved": {"dispatched", "failed"},
            "dispatched": {"verified", "failed", "outcome_unknown"},
            "outcome_unknown": {"reconciled", "failed"},
        },
    ),
    "promotion_intent": _table(
        "promotion_intent",
        {
            "prepared": {"locked", "aborted"},
            "locked": {"promoted", "conflict", "aborted"},
            "conflict": {"reconciled", "aborted"},
        },
    ),
    "release": _table(
        "release",
        {
            "planned": {"built"},
            "built": {"hashed"},
            "hashed": {"extracted"},
            "extracted": {"retested"},
            "retested": {"attested"},
            "attested": {"frozen"},
            "frozen": {"published"},
        },
    ),
}


def serialized_transition_tables() -> dict[str, object]:
    return {
        "format_version": "1.0.0",
        "aggregates": {
            name: {
                "version": table.version,
                "transitions": {state: sorted(targets) for state, targets in sorted(table.transitions.items())},
            }
            for name, table in sorted(TRANSITION_TABLES.items())
        },
    }
