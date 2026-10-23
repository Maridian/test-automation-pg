"""Observer client that connects to node B's Ethernet observer port."""

from __future__ import annotations

from sut.common.protocol import Message
from sut.common.transport import TcpClient

from .base import Link, LinkUnavailable


class TcpLink(Link):
    """JSON-lines client connected to node B's server port.

    Node B re-emits incoming heartbeats and broadcasts its ACKs to all
    connected clients, so this single connection observes both directions.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 41002) -> None:
        self._client = TcpClient(host=host, port=port, connect_timeout=3.0)
        try:
            self._client.connect()
        except (OSError, ConnectionError) as exc:
            self._client.close()
            raise LinkUnavailable(
                f"Cannot connect to observer port '{host}:{port}': {exc}"
            ) from exc

    def send(self, msg: Message) -> None:
        self._client.send(msg)

    def recv(self, timeout: float) -> Message | None:
        return self._client.recv(timeout)

    def close(self) -> None:
        self._client.close()