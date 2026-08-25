"""Tests for the OpenModelica CLI automation runner and end-to-end integration."""
from __future__ import annotations

import io
from pathlib import Path
import pytest
import pandas as pd

from simulation.omc_runner import (
    OpenModelicaUnavailableError,
    OpenModelicaSimulationError,
    evaluate_simulation_csv,
    find_omc_executable,
    generate_mos_script,
    run_modelica_simulation,
)
from simulation.data_sources import OpenModelicaSource
from simulation.openmodelica_reader import load_result, map_features
from integration import assess


def test_generate_mos_script():
    """Verify that the generated .mos script contains all necessary commands."""
    model_file = Path("modelica/SolarAI_MPPT.mo")
    script = generate_mos_script(
        model_file=model_file,
        model_name="SolarAI_MPPT.SolarAI",
        stop_time=86400.0,
        intervals=500,
        output_format="csv",
    )
    assert "loadModel(Modelica);" in script
    assert 'loadModel(PhotoVoltaics, {"2.1.0"});' in script
    assert "loadFile(" in script
    assert "SolarAI_MPPT.mo" in script
    assert "simulate(SolarAI_MPPT.SolarAI, stopTime=86400.0, numberOfIntervals=500, outputFormat=\"csv\");" in script


def test_omc_unavailable_graceful_handling():
    """Verify that OpenModelicaUnavailableError is raised when omc cannot be found."""
    with pytest.raises(OpenModelicaUnavailableError) as exc_info:
        run_modelica_simulation(
            model_file="modelica/SolarAI_MPPT.mo",
            custom_omc_path=Path("non_existent_directory/non_existent_omc.exe"),
        )
    assert "not found" in str(exc_info.value).lower()


def test_openmodelica_csv_pipeline_integration(tmp_path):
    """Verify that OpenModelica-formatted CSV data flows through reader, source, and assess()."""
    # Create sample CSV with authentic OpenModelica hierarchical column names
    sample_data = pd.DataFrame({
        "time": [0.0, 10.0, 20.0],
        "irradiance.irradiance": [800.0, 850.0, 900.0],
        "module.v": [18.1, 18.2, 18.3],
        "module.i": [1.05, 1.08, 1.10],
        "powerSensor.power": [19.0, 19.65, 20.13],
        "mpTracker.vRef": [18.2, 18.2, 18.2],
        "module.T": [298.15, 298.15, 298.15],
    })
    csv_file = tmp_path / "omc_test_res.csv"
    sample_data.to_csv(csv_file, index=False)

    # 1. Test load_result and map_features
    df = load_result(csv_file)
    mapped_df, mapping, unused = map_features(df)
    assert "irradiance" in mapped_df.columns
    assert "voltage" in mapped_df.columns
    assert "current" in mapped_df.columns
    assert "power" in mapped_df.columns
    assert "mppt_reference_voltage" in mapped_df.columns

    # 2. Test OpenModelicaSource reading
    source = OpenModelicaSource(csv_file)
    row = source.read()
    assert row["voltage"] == 18.1
    assert row["power"] == 19.0
    assert "OpenModelica result source" in source.name

    # 3. Test assess() integration
    evaluation = assess(row)
    assert "condition" in evaluation
    assert "severity" in evaluation
    assert "recommended_action" in evaluation
    assert evaluation["severity"] in {"LOW", "MEDIUM", "HIGH"}

    # 4. Test evaluate_simulation_csv helper
    assessments = evaluate_simulation_csv(csv_file, max_samples=3)
    assert len(assessments) == 3
    for a in assessments:
        assert 0 <= a["confidence"] <= 1.0


def test_omc_executable_finder():
    """Verify that find_omc_executable returns a Path or None cleanly."""
    found = find_omc_executable()
    if found is not None:
        assert isinstance(found, Path)
        assert found.name.startswith("omc")


def test_cleanup_build_artifacts(tmp_path):
    """Verify that cleanup_build_artifacts removes intermediate compiler files and keeps CSVs."""
    from simulation.omc_runner import cleanup_build_artifacts

    build_dir = tmp_path / "omc_build"
    build_dir.mkdir()

    # Create dummy artifacts
    (build_dir / "model.c").write_text("dummy C code", encoding="utf-8")
    (build_dir / "model.o").write_bytes(b"\x00\x01")
    (build_dir / "model.exe").write_bytes(b"MZ\x90")
    (build_dir / "model.makefile").write_text("all:", encoding="utf-8")
    (build_dir / "model.log").write_text("log info", encoding="utf-8")
    (build_dir / "model.mos").write_text("simulate();", encoding="utf-8")
    (build_dir / "model_res.csv").write_text("time,val\n0,1\n", encoding="utf-8")

    deleted = cleanup_build_artifacts(build_dir, keep_csv=True)
    assert len(deleted) == 6
    assert (build_dir / "model_res.csv").exists()
    assert not (build_dir / "model.c").exists()
    assert not (build_dir / "model.exe").exists()
    assert not (build_dir / "model.o").exists()


def test_run_modelica_simulation_with_custom_build_dir(tmp_path, monkeypatch):
    """Verify that run_modelica_simulation executes in the configured build directory."""
    import subprocess
    from simulation.omc_runner import run_modelica_simulation

    custom_build = tmp_path / "custom_build_dir"
    custom_output = tmp_path / "custom_output"
    fake_omc = tmp_path / "bin" / "omc.exe"
    fake_omc.parent.mkdir(parents=True)
    fake_omc.write_text("dummy", encoding="utf-8")

    model_file = tmp_path / "DummyModel.mo"
    model_file.write_text("model DummyModel end DummyModel;", encoding="utf-8")

    executed_cwd = []

    def mock_subprocess_run(cmd, cwd, env, capture_output, text, timeout):
        executed_cwd.append(cwd)
        # Simulate creating a result CSV in the build dir
        res_csv = Path(cwd) / "DummyModel_res.csv"
        res_csv.write_text("time,module.v,module.i,module.power,irradiance.irradiance,mpTracker.vRef\n0,18,1,18,800,18\n", encoding="utf-8")
        class Result:
            returncode = 0
            stdout = "Simulation finished"
            stderr = ""
        return Result()

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    result_csv = run_modelica_simulation(
        model_file=model_file,
        model_name="DummyModel",
        output_dir=custom_output,
        custom_omc_path=fake_omc,
        build_dir=custom_build,
        cleanup_build=True,
    )

    assert str(custom_build) in executed_cwd
    assert result_csv.exists()
    assert result_csv.parent == custom_output
    assert (custom_build / "DummyModel_res.csv").exists()
