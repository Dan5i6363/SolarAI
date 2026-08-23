"""Central, relative-path configuration for SolarAI."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    mode: str = _env("SOLARAI_MODE", "demo")
    model_path: Path = PROJECT_ROOT / _env("SOLARAI_MODEL_PATH", "models/pv_condition_classifier.pt")
    dataset_path: Path = PROJECT_ROOT / _env("SOLARAI_DATASET_PATH", "data/synthetic_pv_dataset.csv")
    camera_source: str = _env("SOLARAI_CAMERA_SOURCE", "demo")
    serial_port: str = _env("SOLARAI_SERIAL_PORT", "")
    serial_baudrate: int = int(_env("SOLARAI_SERIAL_BAUDRATE", "115200"))
    lora_frequency_mhz: float = float(_env("SOLARAI_LORA_FREQUENCY_MHZ", "433.0"))
    dashboard_port: int = int(_env("SOLARAI_DASHBOARD_PORT", "8501"))
    pv_rated_power_w: float = float(_env("SOLARAI_PV_RATED_POWER_W", "20.0"))
    pv_vmp_ref_v: float = float(_env("SOLARAI_PV_VMP_REF_V", "18.2"))

    def is_demo(self) -> bool:
        return self.mode.lower() in {"demo", "simulation"}


settings = Settings()
