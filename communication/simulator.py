"""Deterministic communication-layer transmitter/receiver demonstration."""
from communication.packet import TelemetryPacket
from communication.protocol import decode_packet, encode_packet
def transmit(measurement: dict) -> dict:
    return decode_packet(encode_packet(TelemetryPacket.from_measurement(measurement))).telemetry_dict("LoRa protocol simulation; no RF hardware connected")
