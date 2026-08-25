"""OpenModelica CLI automation runner for SolarAI.

Executes Modelica simulations via the OpenModelica Compiler (omc) CLI,
exports time-series telemetry to CSV, and feeds results into the
existing SolarAI reading and assessment pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
import glob
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

from config import PROJECT_ROOT, settings
from simulation.data_sources import OpenModelicaSource
from integration import assess


class OpenModelicaError(Exception):
    """Base exception for OpenModelica automation errors."""


class OpenModelicaUnavailableError(OpenModelicaError):
    """Raised when OpenModelica compiler (omc) is not found or not executable."""


class OpenModelicaSimulationError(OpenModelicaError):
    """Raised when OpenModelica simulation compilation or execution fails."""


@dataclass
class SimulationResult:
    """Container for simulation execution artifacts."""
    success: bool
    csv_path: Path | None
    stdout: str
    stderr: str
    model_name: str
    stop_time: float


def find_omc_executable(custom_path: str | Path | None = None) -> Path | None:
    """Locate the OpenModelica Compiler (omc) executable.

    Checks:
    1. Explicit custom path (returns None immediately if provided path does not exist)
    2. OPENMODELICAHOME environment variable
    3. System PATH
    4. Standard Windows install locations
    """
    if custom_path is not None:
        p = Path(custom_path)
        if p.is_file() and os.access(p, os.X_OK):
            return p
        if p.is_dir():
            candidate = p / "bin" / ("omc.exe" if os.name == "nt" else "omc")
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate
        return None

    om_home = os.getenv("OPENMODELICAHOME")
    if om_home:
        candidate = Path(om_home) / "bin" / ("omc.exe" if os.name == "nt" else "omc")
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    which_omc = shutil.which("omc")
    if which_omc:
        return Path(which_omc)

    if os.name == "nt":
        search_patterns = [
            r"C:\Program Files\OpenModelica*\bin\omc.exe",
            r"C:\Program Files (x86)\OpenModelica*\bin\omc.exe",
            r"C:\OpenModelica*\bin\omc.exe",
        ]
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                matches.sort(reverse=True)
                return Path(matches[0])

    return None


def get_omc_environment(omc_path: Path) -> dict[str, str]:
    """Prepare environment variables needed by OpenModelica on Windows."""
    env = os.environ.copy()
    om_home = omc_path.resolve().parents[1]
    env["OPENMODELICAHOME"] = str(om_home)

    bin_dir = str(om_home / "bin")
    lib_dir = str(om_home / "lib" / "omc")
    ucrt_bin = str(om_home / "tools" / "msys" / "ucrt64" / "bin")
    usr_bin = str(om_home / "tools" / "msys" / "usr" / "bin")

    additional_paths = [bin_dir, lib_dir, ucrt_bin, usr_bin]
    existing_path = env.get("PATH", "")
    env["PATH"] = ";".join(additional_paths) + ";" + existing_path
    return env


def generate_mos_script(
    model_file: Path | str,
    model_name: str = "SolarAI_MPPT.SolarAI",
    stop_time: float = 86400.0,
    intervals: int = 500,
    output_format: str = "csv",
    libraries: list[tuple[str, str | None]] | None = None,
) -> str:
    """Generate a clean OpenModelica (.mos) script for headless execution."""
    if libraries is None:
        libraries = [("Modelica", None), ("PhotoVoltaics", "2.1.0")]

    abs_model_path = Path(model_file).resolve().as_posix()

    lines: list[str] = [
        "// Auto-generated SolarAI OpenModelica Simulation Script",
    ]
    for lib, ver in libraries:
        if ver:
            lines.append(f'loadModel({lib}, {{"{ver}"}});')
        else:
            lines.append(f"loadModel({lib});")

    lines.append(f'loadFile("{abs_model_path}");')
    lines.append("getErrorString();")
    lines.append(
        f'simulate({model_name}, stopTime={stop_time}, numberOfIntervals={intervals}, outputFormat="{output_format}");'
    )
    lines.append("getErrorString();")
    return "\n".join(lines) + "\n"


def cleanup_build_artifacts(
    build_dir: Path | str,
    keep_csv: bool = True,
    model_name: str | None = None,
) -> list[Path]:
    """Clean up compiler intermediate files from the build directory.

    Retains CSV result files so that simulations remain inspectable and replayable.
    Returns list of deleted file paths.
    """
    b_dir = Path(build_dir)
    if not b_dir.exists() or not b_dir.is_dir():
        return []

    deleted: list[Path] = []
    build_extensions = {
        ".c", ".o", ".h", ".makefile", ".bat", ".libs",
        ".bin", ".intdata", ".realdata", ".xml", ".json",
        ".log", ".mos", ".exe"
    }

    for item in b_dir.iterdir():
        if not item.is_file():
            continue
        if keep_csv and item.suffix.lower() == ".csv":
            continue
        if item.suffix.lower() in build_extensions:
            try:
                item.unlink()
                deleted.append(item)
            except OSError:
                pass
    return deleted


def run_modelica_simulation(
    model_file: Path | str = "modelica/SolarAI_MPPT.mo",
    model_name: str = "SolarAI_MPPT.SolarAI",
    stop_time: float = 86400.0,
    intervals: int = 500,
    output_dir: Path | str = "data",
    custom_omc_path: Path | str | None = None,
    build_dir: Path | str | None = None,
    timeout_seconds: int = 180,
    cleanup_build: bool = True,
) -> Path:
    """Execute OpenModelica simulation via CLI and return the generated CSV path.

    Uses a project-local working directory (e.g. build/openmodelica) instead of
    Windows %TEMP% to prevent Windows Device Guard/execution policy blocks.

    Raises:
        OpenModelicaUnavailableError: If omc is not installed or accessible.
        OpenModelicaSimulationError: If omc fails to compile or simulate the model.
    """
    model_path = Path(model_file).resolve()
    if not model_path.exists():
        raise FileNotFoundError(f"Modelica model file not found: {model_path}")

    omc_exe = find_omc_executable(custom_path=custom_omc_path)
    if omc_exe is None:
        raise OpenModelicaUnavailableError(
            "OpenModelica compiler (omc) executable was not found. "
            "Please ensure OpenModelica is installed and omc is in PATH or OPENMODELICAHOME is set."
        )

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if build_dir is not None:
        build_path = Path(build_dir).resolve()
    else:
        build_path = Path(getattr(settings, "omc_build_dir", PROJECT_ROOT / "build" / "openmodelica")).resolve()

    build_path.mkdir(parents=True, exist_ok=True)

    mos_content = generate_mos_script(
        model_file=model_path,
        model_name=model_name,
        stop_time=stop_time,
        intervals=intervals,
        output_format="csv",
    )

    mos_file = build_path / "run_simulation.mos"
    mos_file.write_text(mos_content, encoding="utf-8")

    env = get_omc_environment(omc_exe)

    try:
        process = subprocess.run(
            [str(omc_exe), mos_file.name],
            cwd=str(build_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise OpenModelicaSimulationError(
            f"OpenModelica simulation timed out after {timeout_seconds} seconds."
        ) from exc
    except Exception as exc:
        raise OpenModelicaSimulationError(
            f"Failed to execute OpenModelica compiler: {exc}"
        ) from exc

    # Check for generated CSV in build_path
    csv_candidates = list(build_path.glob("*.csv"))
    if not csv_candidates:
        stdout_snippet = process.stdout[:1000]
        stderr_snippet = process.stderr[:1000]
        raise OpenModelicaSimulationError(
            f"OpenModelica simulation did not produce a CSV result file.\n"
            f"Exit code: {process.returncode}\n"
            f"Stdout: {stdout_snippet}\n"
            f"Stderr: {stderr_snippet}"
        )

    # Prefer file containing 'res' or the model name, sorted by newest
    csv_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    target_csv_file = csv_candidates[0]
    for c in csv_candidates:
        if "res" in c.name.lower():
            target_csv_file = c
            break

    dest_csv = out_dir / f"{Path(model_name).stem}_simulation_res.csv"
    shutil.copy2(target_csv_file, dest_csv)

    if cleanup_build:
        cleanup_build_artifacts(build_path, keep_csv=True, model_name=model_name)

    return dest_csv


def evaluate_simulation_csv(
    csv_path: Path | str,
    max_samples: int = 10,
) -> list[dict[str, Any]]:
    """Load OpenModelica CSV via OpenModelicaSource and evaluate through assess().

    Returns a list of diagnostic assessment dictionaries.
    """
    source = OpenModelicaSource(csv_path)
    assessments: list[dict[str, Any]] = []

    count = 0
    while count < max_samples:
        try:
            telemetry_row = source.read()
            evaluation = assess(telemetry_row)
            assessments.append(evaluation)
            count += 1
        except (IndexError, StopIteration):
            break

    return assessments
