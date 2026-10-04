from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable


class EventStore:
    """Optional local SQLite journal for persistent simulation and decision history."""

    def __init__(self, path: str):
        if not path:
            raise ValueError("EventStore path must not be empty")
        self.path = str(Path(path).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                node_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                action TEXT,
                trace_id TEXT,
                message TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                trace_id TEXT PRIMARY KEY,
                tick INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def append_events(self, events: Iterable[object]) -> int:
        rows = []
        for event in events:
            rows.append(
                (
                    int(event.tick),
                    str(event.event_type),
                    str(event.node_id),
                    str(event.severity),
                    event.action,
                    event.trace_id,
                    str(event.message),
                    json.dumps(event.__dict__, sort_keys=True, default=str),
                )
            )
        if not rows:
            return 0
        self.connection.executemany(
            """
            INSERT INTO events
            (tick, event_type, node_id, severity, action, trace_id, message, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()
        return len(rows)

    def append_decision(self, decision: dict) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO decisions(trace_id, tick, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                str(decision["trace_id"]),
                int(decision["tick"]),
                json.dumps(decision, sort_keys=True, default=str),
            ),
        )
        self.connection.commit()

    def counts(self) -> dict:
        events = self.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        decisions = self.connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        return {"events": int(events), "decisions": int(decisions), "path": self.path}

    def close(self) -> None:
        self.connection.close()
