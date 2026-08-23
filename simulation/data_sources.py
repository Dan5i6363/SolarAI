"""Common telemetry sources for demo, replay, model results, and future serial."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator
import pandas as pd

from simulation.openmodelica_reader import load_result, map_features
from simulation.source import PVMeasurement, simulate_measurement


class DataSource(ABC):
    """A source that yields canonical PV telemetry dictionaries."""
    name: str

    @abstractmethod
    def read(self) -> dict:
        raise NotImplementedError


class DemoSource(DataSource):
    name = "Demo / synthetic source"

    def __init__(self, condition: str = "Normal", seed: int = 42) -> None:
        self.condition, self.seed = condition, seed

    def read(self) -> dict:
        return simulate_measurement(self.condition, self.seed).to_dict()


class CSVSource(DataSource):
    name = "CSV replay source"

    def __init__(self, path: str | Path) -> None:
        self.path, self.index = Path(path), 0
        self.frame, self.mapping, _ = map_features(load_result(self.path))

    def read(self) -> dict:
        if self.frame.empty:
            raise ValueError("Replay file has no usable telemetry rows.")
        row = self.frame.iloc[self.index % len(self.frame)].to_dict(); self.index += 1
        row["source"] = f"CSV replay (simulation/file data): {self.path.name}"
        return row

    def reset(self) -> None:
        self.index = 0


class OpenModelicaSource(CSVSource):
    name = "OpenModelica result source"


class SerialSource(DataSource):
    """Future serial source. It parses newline-delimited protocol packets when supplied."""
    name = "Hardware serial source (placeholder)"

    def __init__(self, port: str = "", baudrate: int = 115200) -> None:
        self.port, self.baudrate = port, baudrate

    def parse_line(self, line: str) -> dict:
        from communication.protocol import decode_packet
        packet = decode_packet(line.strip())
        return packet.telemetry_dict(source="Serial telemetry; hardware unverified")

    def read(self) -> dict:
        if not self.port:
            raise RuntimeError("No serial port configured. Set SOLARAI_SERIAL_PORT for hardware mode.")
        try:
            import serial
        except ImportError as error:
            raise RuntimeError("pyserial is required for live serial input.") from error
        with serial.Serial(self.port, self.baudrate, timeout=2) as connection:
            return self.parse_line(connection.readline().decode("utf-8", errors="replace"))
