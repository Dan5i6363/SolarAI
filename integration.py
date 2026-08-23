"""Combines electrical inputs, AI inference, CV status, and recommendations."""
from __future__ import annotations
from ai.inference import predict
from camera.panel_monitor import analyze_panel
from simulation.source import PVMeasurement, simulate_measurement

_ACTIONS = {"Normal": "Continue normal monitoring.", "Low Irradiance": "Confirm weather/time conditions; no electrical intervention needed.", "Partial Shading": "Inspect for shadows and remove obstructions where safe.", "Soiling/Dust": "Inspect and clean the panel using approved safe procedures.", "Possible Fault": "Inspect wiring and connectors; consult a qualified technician if persistent."}
_STATUS = {"Normal": "NORMAL", "Low Irradiance": "LOW IRRADIANCE", "Partial Shading": "PARTIAL SHADING", "Soiling/Dust": "SOILING / DUST", "Possible Fault": "POSSIBLE FAULT"}


def assess(measurement: PVMeasurement | dict, image=None, image_path=None) -> dict:
    data = measurement.to_dict() if isinstance(measurement, PVMeasurement) else dict(measurement)
    result = predict(data); cv = analyze_panel(image=image, image_path=image_path)
    condition = result["condition"]
    severity = "HIGH" if condition == "Possible Fault" else "MEDIUM" if condition in {"Partial Shading", "Soiling/Dust"} else "LOW"
    evidence = {"electrical": {"irradiance_w_m2": data["irradiance"], "power_w": data["power"], "voltage_v": data["voltage"]}, "ai_prediction": condition, "cv_status": cv["visual_condition"]}
    return {"measurement": data, "status": _STATUS[condition], "condition": condition, "severity": severity, "evidence": evidence,
            "confidence": result["confidence"], "recommended_action": _ACTIONS[condition],
            "probabilities": result["probabilities"], "cv": cv}


def run_demo(condition: str = "Normal", seed: int = 42) -> dict:
    return assess(simulate_measurement(condition, seed))
