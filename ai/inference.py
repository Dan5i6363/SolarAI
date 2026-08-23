"""Inference wrapper for the trained PV condition classifier."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import torch
from ai.train import PVConditionNet


def predict(measurement: dict, model_path: str | Path = "models/pv_condition_classifier.pt") -> dict:
    bundle = torch.load(Path(model_path), map_location="cpu", weights_only=False)
    model = PVConditionNet(len(bundle["features"]), len(bundle["classes"]))
    model.load_state_dict(bundle["state_dict"]); model.eval()
    data = dict(measurement)
    if "efficiency" not in data or "power_deviation" not in data:
        # Conservative estimate from nominal 20 W panel, retained as derived input.
        efficiency = float(data["power"]) / 20.0
        data.setdefault("efficiency", efficiency); data.setdefault("power_deviation", 1 - efficiency)
    vector = np.array([data[name] for name in bundle["features"]], dtype=np.float32)
    vector = (vector - bundle["feature_mean"]) / bundle["feature_std"]
    with torch.no_grad():
        probabilities = torch.softmax(model(torch.tensor(vector).unsqueeze(0)), dim=1)[0].numpy()
    index = int(probabilities.argmax())
    return {"condition": bundle["classes"][index], "confidence": float(probabilities[index]),
            "probabilities": dict(zip(bundle["classes"], map(float, probabilities)))}
