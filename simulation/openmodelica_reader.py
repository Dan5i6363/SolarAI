"""Import OpenModelica CSV/MAT results without modifying Modelica models.

The mapper uses normalized names and aliases because exported variable names vary
between model/package versions. Inspect ``unmapped_columns`` before relying on a
new export.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import numpy as np
import pandas as pd

FEATURE_ALIASES = {
    "irradiance": ("irradiance", "solarirradiance", "g", "gpoa"),
    "voltage": ("pvvoltage", "voltage", "modulev", "vdc", "v"),
    "current": ("pvcurrent", "current", "modulei", "i"),
    "power": ("pvpower", "power", "modulepower", "p"),
    "mppt_reference_voltage": ("mpptreferencevoltage", "vref", "mpptvref", "vdcRef".lower()),
    "temperature": ("temperature", "moduletemperature", "celltemperature", "t"),
}


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def load_result(path: str | Path) -> pd.DataFrame:
    """Load a CSV or a practical numeric MAT-file export into a table."""
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    if input_path.suffix.lower() == ".csv":
        return pd.read_csv(input_path)
    if input_path.suffix.lower() != ".mat":
        raise ValueError("Supported result formats are .csv and .mat")
    try:
        from scipy.io import loadmat
    except ImportError as error:
        raise RuntimeError("MAT import requires scipy; install scipy to use this optional feature.") from error
    contents: dict[str, Any] = loadmat(input_path, squeeze_me=True)
    numeric = {key: value for key, value in contents.items() if not key.startswith("__") and np.asarray(value).ndim == 1}
    if not numeric:
        raise ValueError("No one-dimensional numeric signals found in MAT file.")
    return pd.DataFrame(numeric)


def map_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    """Return canonical PV features, selected source columns, and unused columns."""
    normalized = {_normalize(column): column for column in frame.columns}
    mapping: dict[str, str] = {}
    for feature, aliases in FEATURE_ALIASES.items():
        match = next((normalized[alias] for alias in aliases if alias in normalized), None)
        if match is None:
            match = next((column for norm, column in normalized.items() if any(alias in norm for alias in aliases)), None)
        if match is not None:
            mapping[feature] = match
    required = {"irradiance", "voltage", "current", "power", "mppt_reference_voltage"}
    missing = required - mapping.keys()
    if missing:
        raise ValueError(f"Could not map required OpenModelica features: {sorted(missing)}. Available columns: {list(frame.columns)}")
    result = pd.DataFrame({feature: pd.to_numeric(frame[column], errors="coerce") for feature, column in mapping.items()})
    if "temperature" not in result:
        result["temperature"] = 25.0
    result = result.dropna().reset_index(drop=True)
    return result, mapping, [column for column in frame.columns if column not in mapping.values()]
