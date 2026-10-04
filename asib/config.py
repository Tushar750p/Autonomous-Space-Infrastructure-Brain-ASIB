from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ASIBConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    tick_interval_s: float = 1.0

    @classmethod
    def from_env(cls) -> "ASIBConfig":
        port = int(os.getenv("ASIB_PORT", "8080"))
        interval = float(os.getenv("ASIB_TICK_INTERVAL_S", "1.0"))
        return cls(
            host=os.getenv("ASIB_HOST", "0.0.0.0"),
            port=max(1, min(65535, port)),
            tick_interval_s=max(0.05, min(60.0, interval)),
        )
