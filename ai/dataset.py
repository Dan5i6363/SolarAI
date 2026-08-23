"""Reproducible, engineering-oriented synthetic PV condition dataset."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from simulation.pv_model import find_mpp, pv_model

CLASSES = ["Normal", "Low Irradiance", "Partial Shading", "Soiling/Dust", "Possible Fault"]
FEATURES = ["irradiance", "voltage", "current", "power", "temperature", "mppt_reference_voltage", "efficiency", "power_deviation"]


def _ranges(label: str, rng: np.random.Generator) -> tuple[float, float, float, float]:
    """Return irradiance, voltage, current, and loss factors with intentional overlap."""
    if label == "Normal": return rng.uniform(450, 1050), rng.normal(1.0, .035), rng.normal(1.0, .055), rng.uniform(.90, 1.04)
    if label == "Low Irradiance": return rng.uniform(70, 560), rng.normal(1.0, .05), rng.normal(1.0, .07), rng.uniform(.82, 1.02)
    if label == "Partial Shading": return rng.uniform(420, 1050), rng.uniform(.78, 1.02), rng.uniform(.52, .94), rng.uniform(.52, .90)
    if label == "Soiling/Dust": return rng.uniform(420, 1050), rng.uniform(.88, 1.04), rng.uniform(.70, .98), rng.uniform(.68, .94)
    return rng.uniform(180, 1050), rng.uniform(.52, 1.08), rng.uniform(.18, .82), rng.uniform(.15, .78)


def generate_dataset(samples_per_class: int = 600, seed: int = 42) -> pd.DataFrame:
    """Generate seeded, noisy synthetic data; it is not a physical benchmark."""
    rng = np.random.default_rng(seed); rows: list[dict] = []
    for label in CLASSES:
        for _ in range(samples_per_class):
            irradiance, voltage_factor, current_factor, loss_factor = _ranges(label, rng)
            temperature = rng.uniform(12, 65)
            voltage, current, power = pv_model(irradiance, temperature)
            vmp, imp, pmp = find_mpp(voltage, current, power)
            measured_voltage = max(.05, vmp * voltage_factor * (1 + rng.normal(0, .018)))
            measured_current = max(0.0, imp * current_factor * (1 + rng.normal(0, .035)))
            measured_power = max(0.0, measured_voltage * measured_current * loss_factor * (1 + rng.normal(0, .025)))
            rows.append({"irradiance": round(float(irradiance), 3), "voltage": round(float(measured_voltage), 4),
                         "current": round(float(measured_current), 4), "power": round(float(measured_power), 4),
                         "temperature": round(float(temperature), 3), "mppt_reference_voltage": round(float(vmp), 4),
                         "efficiency": round(float(measured_power / max(pmp, .01)), 4),
                         "power_deviation": round(float(1 - measured_power / max(pmp, .01)), 4),
                         "condition": label, "data_origin": "synthetic PV simulation; not hardware measurement"})
    return pd.DataFrame(rows)


def save_dataset(path: str | Path, samples_per_class: int = 600, seed: int = 42) -> Path:
    output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
    generate_dataset(samples_per_class, seed).to_csv(output, index=False)
    return output
