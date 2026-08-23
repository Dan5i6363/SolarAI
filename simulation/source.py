"""Simulation-source adapter used by the software demo.

This module deliberately labels its output as simulated.  It uses the existing
empirical PV model in :mod:`simulation.pv_model`; it does not modify or replace
the OpenModelica model.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional
import csv
import numpy as np

from .pv_model import find_mpp, pv_model


@dataclass
class PVMeasurement:
    irradiance: float
    voltage: float
    current: float
    power: float
    temperature: float
    mppt_reference_voltage: float
    source: str = "SIMULATED (existing Python PV model)"

    def to_dict(self) -> dict:
        return asdict(self)


_EFFECTS = {
    "Normal": (1.0, 1.0),
    "Low Irradiance": (1.0, 1.0),
    "Partial Shading": (0.88, 0.60),
    "Soiling/Dust": (0.95, 0.78),
    "Possible Fault": (0.65, 0.35),
}


def simulate_measurement(condition: str = "Normal", seed: Optional[int] = None) -> PVMeasurement:
    """Create one *simulated* operating-point measurement for a condition."""
    if condition not in _EFFECTS:
        raise ValueError(f"Unknown condition: {condition}")
    rng = np.random.default_rng(seed)
    irradiance = rng.uniform(80, 440) if condition == "Low Irradiance" else rng.uniform(650, 1050)
    temperature = rng.uniform(18, 55)
    voltage, current, power = pv_model(irradiance, temperature)
    vmp, imp, _ = find_mpp(voltage, current, power)
    voltage_scale, current_scale = _EFFECTS[condition]
    measured_voltage = max(0.1, vmp * voltage_scale * (1 + rng.normal(0, 0.012)))
    measured_current = max(0.0, imp * current_scale * (1 + rng.normal(0, 0.018)))
    return PVMeasurement(
        irradiance=round(float(irradiance), 2), voltage=round(float(measured_voltage), 3),
        current=round(float(measured_current), 3), power=round(float(measured_voltage * measured_current), 3),
        temperature=round(float(temperature), 2), mppt_reference_voltage=round(float(vmp), 3),
    )


def read_openmodelica_csv(path: str | Path) -> list[dict[str, str]]:
    """Read an exported OpenModelica CSV without making assumptions about names.

    Map its columns to ``PVMeasurement`` in hardware-specific code once the
    actual result variable names are known.
    """
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
