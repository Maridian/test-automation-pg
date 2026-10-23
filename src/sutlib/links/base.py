"""Link abstraction used by the tests to observe and inject messages."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sut.common.protocol import Message


class LinkError(Exception):
    """Base error for link problems."""


class LinkUnavailable(LinkError):
    """Raised when a link cannot be established (tests should skip)."""


class Link(ABC):
    """A connection used by the test harness to watch and talk to the SUTs.

    Implementations:
      - VcanLink : SocketCAN bus (virtual vcan0 or real can0)
      - TcpLink  : JSON-lines client connected to node B's observer port
    """

    def send(self, msg: Message) -> None:
        """Inject a message into the link (not supported by every backend)."""
        raise NotImplementedError("This link does not support sending")

    @abstractmethod
    def recv(self, timeout: float) -> Message | None:
        """Return the next message, or None if the timeout expires."""

    def close(self) -> None:
        """Release any resources held by the link."""