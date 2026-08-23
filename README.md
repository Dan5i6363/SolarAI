# SolarAI: AI-enabled MPPT solar monitoring

The existing OpenModelica PV + MPPT models remain intact. The demo uses the existing Python PV model as its electrical simulation source. Generated data, classifier results, and dashboard values are **synthetic simulation data**, not hardware measurements.

Includes reproducible synthetic PV data and PyTorch training, heuristic OpenCV monitoring, OpenModelica CSV/MAT import, replay sources, CRC telemetry protocol simulation, and a Streamlit dashboard. OpenModelica models are preserved.

## Exact Windows commands

From PowerShell in `C:\SolarAI`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m ai.train --epochs 180 --seed 42
python -m pytest -q
streamlit run dashboard\app.py
```

One-command demo: `powershell -ExecutionPolicy Bypass -File scripts\run_demo.ps1`.

For Community Cloud, push source plus `models/`, `data/`, and `requirements.txt`; use `dashboard/app.py`. Cloud supports demo mode only—no local serial, webcam, LoRa, or OpenModelica access.

## Before physical deployment

Validate/retrain with labelled real panel measurements, map actual OpenModelica CSV and sensor variable names to the eight model features, calibrate CV for the camera position, and have a qualified PV technician validate any fault rules. ESP32/SX1278 sketches are future-integration examples, not tested RF performance.
