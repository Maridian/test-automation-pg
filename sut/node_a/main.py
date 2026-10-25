"""Node A - sensor device under test.

Sends periodic heartbeat/telemetry messages to node B over the selected
link. In the virtual environment it runs as a local subprocess; on real
hardware the same module is started on the device itself.

Usage: python -m sut.node_a.main --transport can --interface vcan0
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from sut.common.protocol import Message, MsgType, now_ms
from sut.common.signal_spec import ProtocolSpec
from sut.common.transport import CanTransport, TcpClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Node A - sensor simulator")
    parser.add_argument("--transport", choices=("can", "eth"), required=True)
    parser.add_argument("--interface", default="vcan0", help="SocketCAN interface (CAN only)")
    parser.add_argument("--host", default="127.0.0.1", help="Node B host (Ethernet only)")
    parser.add_argument("--port", type=int, default=41002, help="Node B port (Ethernet only)")
    parser.add_argument("--interval", type=float, default=0.5, help="Heartbeat period (seconds)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    
    # Load protocol specification
    spec_path = Path(__file__).parent.parent.parent / "config" / "signals.yaml"
    spec = ProtocolSpec(spec_path)
    hb_spec = spec.get_message_by_name("heartbeat")
    
    if args.transport == "can":
        transport: CanTransport | TcpClient = CanTransport(interface=args.interface)
    else:
        transport = TcpClient(host=args.host, port=args.port)
        transport.connect()

    seq = 0
    try:
        while True:
            seq += 1
            msg = Message(
                msg_type=MsgType.HEARTBEAT,
                seq=seq,
                ts_ms=now_ms(),
                src=hb_spec.sender,
                can_id=hb_spec.can_id,
            )
            transport.send(msg)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        transport.close()


if __name__ == "__main__":
    main()