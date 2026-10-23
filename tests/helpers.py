"""Small helpers shared by the tests."""

from __future__ import annotations

import time

import pytest

from sut.common.protocol import Message
from sutlib.links.base import Link

_TRACE_LIMIT = 20


def wait_for_message(link: Link, timeout: float, **filters: object) -> Message:
    """Wait for a message matching all given filters.

    Example: wait_for_message(link, 5.0, msg_type=MsgType.HEARTBEAT, src="node_a")
    Fails the test on timeout and dumps the messages seen on the link.
    """
    seen: list[Message] = []
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            pytest.fail(_timeout_dump(timeout, filters, seen))
        msg = link.recv(timeout=min(0.25, remaining))
        if msg is None:
            continue
        seen.append(msg)
        if all(getattr(msg, key, None) == value for key, value in filters.items()):
            return msg


def _timeout_dump(timeout: float, filters: dict[str, object], seen: list[Message]) -> str:
    wanted = " ".join(f"{key}={value!r}" for key, value in filters.items()) or "(any)"
    lines = [
        f"timeout after {timeout:.1f}s waiting for {wanted}",
        f"received {len(seen)} message(s)",
    ]
    if seen:
        lines.append(f"last {min(len(seen), _TRACE_LIMIT)}:")
        for msg in seen[-_TRACE_LIMIT:]:
            lines.append(
                f"  type={msg.msg_type.name} seq={msg.seq} src={msg.src} ts_ms={msg.ts_ms}"
            )
    return "\n".join(lines)
