"""Validated telemetry packet used by the simulated offline communication layer."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class TelemetryPacket:
    timestamp: str; voltage: float; current: float; power: float; temperature: float; irradiance: float; mppt_reference: float; panel_angle: float=0.0; health_score: float=100.0; fault_code: str="NONE"
    def validate(self) -> None:
        if not 0<=self.voltage<=100 and self.voltage>=0: raise ValueError("voltage out of range")
        if self.current<0 or self.power<0 or self.irradiance<0: raise ValueError("negative telemetry value")
        if not 0<=self.health_score<=100: raise ValueError("health_score must be 0–100")
    def telemetry_dict(self, source: str="Communication simulation") -> dict:
        d=asdict(self); d.update({"mppt_reference_voltage":d.pop("mppt_reference"),"source":source}); return d
    @classmethod
    def from_measurement(cls, measurement: dict) -> "TelemetryPacket":
        return cls(datetime.now(timezone.utc).isoformat(),float(measurement["voltage"]),float(measurement["current"]),float(measurement["power"]),float(measurement.get("temperature",25)),float(measurement["irradiance"]),float(measurement["mppt_reference_voltage"]))
