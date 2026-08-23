"""JSON + CRC32 protocol; simulates packets only, not LoRa RF transmission."""
from __future__ import annotations
import json, zlib
from dataclasses import asdict
from communication.packet import TelemetryPacket

def encode_packet(packet: TelemetryPacket) -> str:
    packet.validate(); payload=json.dumps(asdict(packet),sort_keys=True,separators=(",",":"))
    return json.dumps({"payload":payload,"crc32":f"{zlib.crc32(payload.encode()):08x}"},separators=(",",":"))

def decode_packet(encoded: str) -> TelemetryPacket:
    outer=json.loads(encoded); payload=outer["payload"]
    if outer.get("crc32") != f"{zlib.crc32(payload.encode()):08x}": raise ValueError("Telemetry CRC mismatch")
    packet=TelemetryPacket(**json.loads(payload)); packet.validate(); return packet
