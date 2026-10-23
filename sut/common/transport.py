"""Transport backends used by the SUT nodes and the observer links.

Common interface where applicable: send(Message) / recv(timeout) / close().

  CanTransport - SocketCAN bus via python-can (vcan0 virtual / can0 real)
  TcpClient    - JSON-lines client (node A sender, test observer)
  TcpServer    - JSON-lines multi-client server (node B, broadcasts replies)
"""

from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Callable

from .protocol import Message

# A smaller connect timeout so CI fails fast, but retry inside the window.
_CONNECT_TIMEOUT = 10.0
_RECV_CHUNK = 4096


class CanTransport:
    """SocketCAN bus transport (python-can)."""

    def __init__(self, interface: str) -> None:
        import can  # deferred so CLI help works without a CAN driver

        self._bus = can.Bus(interface="socketcan", channel=interface)

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


class TcpClient:
    """JSON-lines TCP client with reconnection during startup.

    Used by node A to talk to node B and by the test observer to connect
    to node B's observer port.
    """

    def __init__(self, host: str, port: int, connect_timeout: float = _CONNECT_TIMEOUT) -> None:
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._sock: socket.socket | None = None
        self._buf = b""

    def connect(self) -> None:
        """Connect with retry until the deadline; raise OSError afterwards."""
        deadline = time.monotonic() + self._connect_timeout
        while True:
            try:
                self._sock = socket.create_connection((self._host, self._port), timeout=2.0)
                return
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.2)

    def send(self, msg: Message) -> None:
        if self._sock is None:
            raise RuntimeError("client is not connected")
        self._sock.sendall((msg.to_json() + "\n").encode("utf-8"))

    def recv(self, timeout: float) -> Message | None:
        if self._sock is None:
            raise RuntimeError("client is not connected")
        deadline = time.monotonic() + timeout
        while b"\n" not in self._buf:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            self._sock.settimeout(remaining)
            try:
                chunk = self._sock.recv(_RECV_CHUNK)
            except TimeoutError:
                return None
            except OSError:
                return None
            if not chunk:
                return None
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return Message.from_json(line.decode("utf-8"))

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None


class TcpServer:
    """Multi-client JSON-lines TCP server.

    Every received message is handed to `on_message(msg, server)`; the
    callback can reply via `server.broadcast(msg)` to all connected clients.
    """

    def __init__(
        self, host: str, port: int, on_message: Callable[[Message, TcpServer], None]
    ) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((host, port))
        self._server.listen(16)
        self._on_message = on_message
        self._clients: set[socket.socket] = set()
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def broadcast(self, msg: Message) -> None:
        line = (msg.to_json() + "\n").encode("utf-8")
        with self._lock:
            clients = list(self._clients)
        for client in clients:
            try:
                client.sendall(line)
            except OSError:
                self._drop(client)

    def _drop(self, client: socket.socket) -> None:
        with self._lock:
            self._clients.discard(client)
        try:
            client.close()
        except OSError:
            pass

    def _accept_loop(self) -> None:
        while self._running:
            try:
                conn, _ = self._server.accept()
            except OSError:
                return
            with self._lock:
                self._clients.add(conn)
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn: socket.socket) -> None:
        buf = b""
        conn.settimeout(1.0)
        try:
            while self._running:
                try:
                    chunk = conn.recv(_RECV_CHUNK)
                except TimeoutError:
                    continue
                except OSError:
                    break
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = Message.from_json(line.decode("utf-8"))
                    except (ValueError, json.JSONDecodeError):
                        continue
                    self._on_message(msg, self)
        finally:
            self._drop(conn)

    def close(self) -> None:
        self._running = False
        try:
            self._server.close()
        except OSError:
            pass


def create_transport(
    kind: str,
    role: str,
    *,
    interface: str | None = None,
    host: str | None = None,
    port: int | None = None,
    on_message: Callable[[Message, TcpServer], None] | None = None,
) -> CanTransport | TcpClient | TcpServer:
    """Factory for SUT-side transports."""
    if kind == "can":
        if interface is None:
            raise ValueError("interface is required for CAN transports")
        return CanTransport(interface=interface)
    if kind == "eth":
        if host is None or port is None:
            raise ValueError("host and port are required for Ethernet transports")
        if role == "server":
            if on_message is None:
                raise ValueError("on_message is required for Ethernet server role")
            return TcpServer(host=host, port=port, on_message=on_message)
        return TcpClient(host=host, port=port)
    raise ValueError(f"unknown transport kind '{kind}'")