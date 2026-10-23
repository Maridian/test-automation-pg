"""Small helpers shared by the tests."""

from __future__ import annotations

import time

from sut.common.protocol import Message
from sutlib.links.base import Link


def wait_for_message(link: Link, timeout: float, **filters: object) -> Message | None:
    """Wait for a message matching all given filters.

    Example: wait_for_message(link, 5.0, msg_type=MsgType.HEARTBEAT, src="node_a")
    Returns the first matching message, or None if the timeout expires.
    """
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        msg = link.recv(timeout=min(0.25, remaining))
        if msg is None:
            continue
        if all(getattr(msg, key, None) == value for key, value in filters.items()):
            return msg