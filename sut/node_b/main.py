"""Node B - controller device under test.

Receives messages on the selected link and replies with an ACK for every
heartbeat. On Ethernet it additionally re-emits the observed traffic to all
connected observer clients so the test harness can watch both directions
over a single connection.

Usage: python -m sut.node_b.main --transport can --interface vcan0
"""

from __future__ import annotations

import argparse
import time

from sut.common.protocol import Message, MsgType
from sut.common.transport import CanTransport, TcpServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Node B - controller simulator")
    parser.add_argument("--transport", choices=("can", "eth"), required=True)
    parser.add_argument("--interface", default="vcan0", help="SocketCAN interface (CAN only)")
    parser.add_argument("--host", default="127.0.0.1", help="Listen host (Ethernet only)")
    parser.add_argument("--port", type=int, default=41002, help="Listen port (Ethernet only)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.transport == "can":
            _run_can(interface=args.interface)
        else:
            _run_eth(host=args.host, port=args.port)
    except KeyboardInterrupt:
        pass


def _run_can(interface: str) -> None:
    transport = CanTransport(interface=interface)
    try:
        while True:
            msg = transport.recv(timeout=0.5)
            if msg is not None and msg.msg_type == MsgType.HEARTBEAT:
                transport.send(msg.ack())
    finally:
        transport.close()


def _run_eth(host: str, port: int) -> None:
    def handle(msg: Message, server: TcpServer) -> None:
        # Re-emit what we received so observers see node A's traffic too.
        server.broadcast(msg)
        if msg.msg_type == MsgType.HEARTBEAT:
            server.broadcast(msg.ack())

    server = TcpServer(host=host, port=port, on_message=handle)

    try:
        server.start()
        while True:
            time.sleep(3600.0)
    finally:
        server.close()


if __name__ == "__main__":
    main()
