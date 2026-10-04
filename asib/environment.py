from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OrbitalEnvironment:
    """Deterministic orbital context used by the Earth-based digital twin."""

    phase_deg: float = 0.0
    angular_rate_deg_per_tick: float = 30.0
    eclipse_start_deg: float = 90.0
    eclipse_end_deg: float = 270.0
    sunlit_generation_pct: float = 1.8
    eclipse_generation_pct: float = 0.2
    sunlit_cooling_bias_c: float = -0.2
    eclipse_cooling_bias_c: float = 0.6

    def advance(self):
        self.phase_deg = (self.phase_deg + self.angular_rate_deg_per_tick) % 360.0

    @property
    def in_eclipse(self) -> bool:
        return self.eclipse_start_deg <= self.phase_deg < self.eclipse_end_deg

    @property
    def solar_generation_pct(self) -> float:
        return self.eclipse_generation_pct if self.in_eclipse else self.sunlit_generation_pct

    @property
    def cooling_bias_c(self) -> float:
        return self.eclipse_cooling_bias_c if self.in_eclipse else self.sunlit_cooling_bias_c

    @property
    def ground_contact_window(self) -> bool:
        """Potential high-bandwidth Earth contact window; not a command authority."""
        phase = self.phase_deg
        return phase <= 30.0 or phase >= 330.0

    def snapshot(self) -> dict:
        return {
            "phase_deg": round(self.phase_deg, 2),
            "in_eclipse": self.in_eclipse,
            "solar_generation_pct": round(self.solar_generation_pct, 2),
            "cooling_bias_c": round(self.cooling_bias_c, 2),
            "ground_contact_window": self.ground_contact_window,
        }
