from __future__ import annotations

import pytest

try:
    import can
except ImportError as exc:
    pytest.skip(f"python-can is not installed: {exc}")


def test_vcan0_interface_available() -> None:
    """A minimal SocketCAN bus on vcan0 must be openable and sendable."""
    try:
        bus = can.Bus(interface="socketcan", channel="vcan0")
    except (OSError, can.CanError) as exc:
        pytest.skip(f"vcan0 is not available: {exc}")

    try:
        frame = can.Message(arbitration_id=0x100, data=b"\xAA\x01\x00\x01\x00\x00\x00\x01")
        bus.send(frame)
    finally:
        bus.shutdown()