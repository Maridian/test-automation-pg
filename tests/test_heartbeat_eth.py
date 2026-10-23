"""End-to-end checks over Ethernet: node A sends heartbeats, node B ACKs them.

Runs over localhost TCP and therefore works on every development host.
"""

from __future__ import annotations

import pytest
from helpers import wait_for_message

from sut.common.protocol import MsgType

pytestmark = pytest.mark.transport_eth


def test_heartbeat_from_node_a(sut_eth) -> None:
    """Node A heartbeats must be observable via node B's re-emission."""
    wait_for_message(sut_eth.link, timeout=10.0, msg_type=MsgType.HEARTBEAT, src="node_a")


def test_node_b_acks_same_sequence(sut_eth) -> None:
    """Node B must ACK the heartbeat with the identical sequence number."""
    heartbeat = wait_for_message(
        sut_eth.link, timeout=10.0, msg_type=MsgType.HEARTBEAT, src="node_a"
    )
    ack = wait_for_message(sut_eth.link, timeout=10.0, msg_type=MsgType.ACK, seq=heartbeat.seq)
    assert ack.src == "node_b"