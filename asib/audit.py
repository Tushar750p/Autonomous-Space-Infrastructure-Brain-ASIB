from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class AuditEntry:
    trace_id: str
    tick: int
    digest: str
    previous_digest: str
    payload: dict[str, Any]


class DecisionLedger:
    """Tamper-evident append-only ledger for autonomous decision traces."""

    ALGORITHM = "sha256"

    def __init__(self):
        self.entries: list[AuditEntry] = []

    @staticmethod
    def _canonical(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)

    def append(self, payload: dict[str, Any]) -> AuditEntry:
        previous = self.entries[-1].digest if self.entries else "0" * 64
        body = {"previous_digest": previous, "payload": payload}
        digest = hashlib.sha256(self._canonical(body).encode("utf-8")).hexdigest()
        entry = AuditEntry(
            trace_id=str(payload["trace_id"]),
            tick=int(payload["tick"]),
            digest=digest,
            previous_digest=previous,
            payload=payload,
        )
        self.entries.append(entry)
        return entry

    def verify(self) -> bool:
        previous = "0" * 64
        for entry in self.entries:
            if entry.previous_digest != previous:
                return False
            body = {"previous_digest": previous, "payload": entry.payload}
            expected = hashlib.sha256(self._canonical(body).encode("utf-8")).hexdigest()
            if entry.digest != expected:
                return False
            previous = entry.digest
        return True

    def export(self) -> list[dict[str, Any]]:
        return [
            {
                "trace_id": entry.trace_id,
                "tick": entry.tick,
                "digest": entry.digest,
                "previous_digest": entry.previous_digest,
                "payload": entry.payload,
            }
            for entry in self.entries
        ]

    @classmethod
    def from_export(cls, records: list[dict[str, Any]]) -> "DecisionLedger":
        ledger = cls()
        for record in records:
            ledger.entries.append(AuditEntry(
                trace_id=str(record["trace_id"]),
                tick=int(record["tick"]),
                digest=str(record["digest"]),
                previous_digest=str(record["previous_digest"]),
                payload=dict(record["payload"]),
            ))
        return ledger
