"""End-to-end checks over CAN: node A sends heartbeats, node B ACKs them.

Skipped automatically when vcan0 is not available on the test host.
"""

from __future__ import annotations

import pytest
from helpers import wait_for_message

from sut.common.protocol import MsgType

pytestmark = pytest.mark.transport_can


def test_heartbeat_from_node_a(sut_can) -> None:
    """Node A must publish heartbeats on the CAN bus."""
    msg = wait_for_message(sut_can.link, timeout=10.0, msg_type=MsgType.HEARTBEAT, src="node_a")
    assert msg.seq > 0


def test_node_b_acks_same_sequence(sut_can) -> None:
    """Node B must ACK the heartbeat with the identical sequence number."""
    heartbeat = wait_for_message(
        sut_can.link, timeout=10.0, msg_type=MsgType.HEARTBEAT, src="node_a"
    )
    ack = wait_for_message(sut_can.link, timeout=10.0, msg_type=MsgType.ACK, seq=heartbeat.seq)
    assert ack.src == "node_b"