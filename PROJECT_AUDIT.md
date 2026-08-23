# SolarAI project audit

Audit date: 2026-08-24. This audit was completed before implementation changes.
The existing OpenModelica files were read only and must remain unchanged.

## Current architecture

`SolarAI_PV_MPPT.mo` and `modelica/SolarAI_MPPT.mo` contain the working
OpenModelica PV + MPPT simulations. The existing Python empirical PV model in
`simulation/pv_model.py` provides a separate validation/demo source. The
software layer currently has a generated synthetic dataset, a compact PyTorch
classifier, an OpenCV quadrilateral/brightness heuristic, an integration module,
and a small Streamlit dashboard.

## Completed components

- OpenModelica PV/MPPT models (preserved).
- Python PV curve and P&O MPPT validation scripts.
- Synthetic five-class condition dataset and saved PyTorch model.
- Basic classifier inference with six electrical features.
- Image/demo panel-region heuristic and webcam capture helper.
- Demo integration and Streamlit scenario selector.

## Incomplete components

- No central configuration or source abstraction.
- Synthetic classes are unrealistically easy to separate; current 100% synthetic
  accuracy is not suitable as a field-performance claim.
- No persisted model metadata, preprocessing artifact, or confusion-matrix plot.
- CSV reader lacks feature-name mapping; no MAT reader.
- No OpenModelica replay, serial ingestion, LoRa protocol/simulation, ESP32
  examples, deterministic replay controls, or decision explanation/severity.
- Dashboard has no architecture/about views, trends, source status, or model info.
- Tests cover only three basic paths and did not complete under `pytest -q` in
  the previous session despite direct integration checks succeeding.
- README, ignore rules, deployment guide, scripts, and status documentation are
  incomplete for a professional demonstration.

## Dependencies

Declared dependencies: NumPy, pandas, scikit-learn, PyTorch, OpenCV, Streamlit,
and pytest. Matplotlib is used by existing simulation scripts but is not listed.
The environment also contains the installed dependencies needed by the current
demo. No credentials or network services are required for demo mode.

## Entry points

- `simulation/pv_model.py`: existing PV model/plot script.
- `simulation/mppt.py`: existing P&O MPPT validation/plot script.
- `ai/train.py`: synthetic training and model save.
- `dashboard/app.py`: Streamlit dashboard.
- `integration.py`: application-level demo assessment.
- `gpu_test.py`: standalone GPU stress utility; not part of the application.

## Risks

- Synthetic labels are generated from strong, fixed class effects, creating
  leakage-like separability and misleadingly high test metrics.
- Current CV is a heuristic panel locator, not a trained visual-fault classifier.
- Model paths are relative to process working directory, limiting portability.
- Existing scripts use non-package imports and plotting side effects; preserve
  them, but avoid using them as production interfaces.
- Hardware sensor, serial, LoRa, and camera accuracy have not been validated.

## Recommended execution order

1. Add central configuration, common telemetry schema, and data-source classes.
2. Improve synthetic variation and make the AI training/evaluation artifacts
   reproducible and transparent.
3. Add robust OpenModelica CSV/MAT mapping and replay.
4. Improve CV return schema and add deterministic hybrid decision logic.
5. Add communication protocol/simulator and optional ESP32 examples.
6. Upgrade dashboard, tests, documentation, and one-command scripts.
7. Run full validation while preserving Modelica hashes.
