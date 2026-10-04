from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryScorecard:
    first_detection_tick: int | None
    recovery_tick: int | None
    detection_latency_ticks: int | None
    recovery_latency_ticks: int | None
    autonomous_actions: int
    blocked_or_unverified_actions: int
    human_review_events: int

    def as_dict(self) -> dict:
        return self.__dict__


class RecoveryScorecardBuilder:
    """Deterministic operational metrics for a benchmark run."""

    @staticmethod
    def build(reports, recovery_tick: int | None) -> RecoveryScorecard:
        detection = None
        actions = 0
        blocked = 0
        human_review = 0

        for report in reports:
            for event in report.events:
                event_type = event.get("event_type")
                severity = event.get("severity")
                if detection is None and (
                    event_type in {"critical", "degradation"}
                    or severity == "critical"
                ):
                    detection = report.tick
                if event_type == "action":
                    actions += 1
                if event_type in {"blocked_action", "verification"} and (
                    event_type == "blocked_action"
                    or "not verified" in event.get("message", "")
                    or "not_verified" in event.get("message", "")
                ):
                    blocked += 1
                if event_type == "human_review":
                    human_review += 1

        return RecoveryScorecard(
            first_detection_tick=detection,
            recovery_tick=recovery_tick,
            detection_latency_ticks=detection,
            recovery_latency_ticks=(
                recovery_tick - detection
                if detection is not None and recovery_tick is not None
                else None
            ),
            autonomous_actions=actions,
            blocked_or_unverified_actions=blocked,
            human_review_events=human_review,
        )
