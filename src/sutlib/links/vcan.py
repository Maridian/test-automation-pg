"""Observer/sender on a SocketCAN bus (vcan0 virtual or can0 real)."""

from __future__ import annotations

from sut.common.protocol import Message

from .base import Link, LinkUnavailable


class VcanLink(Link):
    """Watches a CAN interface via python-can.

    Opening the bus also verifies that the interface actually exists, which
    makes this link unusable where no (virtual) CAN interface is present.
    """

    def __init__(self, interface: str = "vcan0") -> None:
        try:
            import can
        except ImportError as exc:  # pragma: no cover
            raise LinkUnavailable("python-can is not installed") from exc

        try:
            self._bus = can.Bus(interface="socketcan", channel=interface)
        except (OSError, ModuleNotFoundError) as exc:
            raise LinkUnavailable(
                f"Cannot open SocketCAN interface '{interface}': {exc}"
            ) from exc
        self._interface = interface

    def send(self, msg: Message) -> None:
        import can

        frame = can.Message(arbitration_id=msg.can_id, data=msg.to_can_frame())
        self._bus.send(frame)

    def recv(self, timeout: float) -> Message | None:
        frame = self._bus.recv(timeout=timeout)
        if frame is None:
            return None
        return Message.from_can_frame(bytes(frame.data), frame.arbitration_id)

    def close(self) -> None:
        self._bus.shutdown()