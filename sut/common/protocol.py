"""Generic message protocol shared by the SUT nodes and the test harness.

Two wire formats are supported:
  - CAN 2.0: fixed 8-byte frames  magic(1) | type(1) | seq(2) | ts_ms(4)
  - TCP    : JSON-lines with the same logical fields

Protocol specification is loaded from config/signals.yaml
"""

from __future__ import annotations

import json
import struct
import time
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from sut.common.signal_spec import ProtocolSpec

# Load protocol specification from YAML
_SPEC_PATH = Path(__file__).parent.parent.parent / "config" / "signals.yaml"
_SPEC = ProtocolSpec(_SPEC_PATH)

# Protocol constants derived from YAML specification
CAN_FRAME_SIZE = _SPEC.frame_size
CAN_MAGIC = _SPEC.can_magic

# CAN IDs from specification
CAN_ID_HEARTBEAT = _SPEC.get_message_by_name("heartbeat").can_id
CAN_ID_ACK = _SPEC.get_message_by_name("ack").can_id


class MsgType(IntEnum):
    HEARTBEAT = 0x01
    ACK = 0x02


@dataclass(frozen=True)
class Message:
    """Logical message exchanged between the SUT nodes."""

    msg_type: MsgType
    seq: int
    ts_ms: int
    src: str = "node_a"
    can_id: int = CAN_ID_HEARTBEAT

    # --- encoding -------------------------------------------------------
    def to_can_frame(self) -> bytes:
        return struct.pack(
            ">BBHI", CAN_MAGIC, int(self.msg_type), self.seq & 0xFFFF, self.ts_ms & 0xFFFFFFFF
        )

    def to_json(self) -> str:
        return json.dumps(
            {"type": int(self.msg_type), "seq": self.seq, "ts_ms": self.ts_ms, "src": self.src}
        )

    @classmethod
    def from_can_frame(cls, data: bytes, can_id: int) -> Message:
        if len(data) != CAN_FRAME_SIZE:
            raise ValueError(f"invalid CAN frame length {len(data)}")
        magic, msg_type, seq, ts_ms = struct.unpack(">BBHI", data)
        if magic != CAN_MAGIC:
            raise ValueError(f"invalid CAN magic {magic:#x}")
        # Look up sender from specification based on CAN ID
        src = _SPEC.get_source_by_can_id(can_id)
        return cls(
            msg_type=MsgType(msg_type),
            seq=seq,
            ts_ms=ts_ms,
            src=src,
            can_id=can_id,
        )

    @classmethod
    def from_json(cls, line: str) -> Message:
        data = json.loads(line)
        return cls(
            msg_type=MsgType(data["type"]),
            seq=int(data["seq"]),
            ts_ms=int(data["ts_ms"]),
            src=data.get("src", "node_a"),
        )

    # --- convenience ----------------------------------------------------
    def ack(self) -> Message:
        """Create the ACK message for this message.
        
        Sender and CAN ID are determined from the protocol specification.
        """
        ack_spec = _SPEC.get_message_by_name("ack")
        return Message(
            msg_type=MsgType.ACK,
            seq=self.seq,
            ts_ms=now_ms(),
            src=ack_spec.sender,
            can_id=ack_spec.can_id,
        )


def now_ms() -> int:
    """Current wall-clock time in milliseconds."""
    return int(time.time() * 1000)