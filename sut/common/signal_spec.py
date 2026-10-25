"""Signal specification loader for CAN and Ethernet protocol.

Loads and parses the YAML signal specification file that defines:
  - Message types and their CAN IDs
  - Signal layouts within messages
  - Node roles and message routing
  - Protocol configuration
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Signal:
    """Individual signal within a message."""

    name: str
    start_bit: int
    length: int
    value_type: str
    default: int = 0
    unit: Optional[str] = None


@dataclass
class MessageSpec:
    """Complete message specification."""

    name: str
    can_id: int
    msg_type: int
    dlc: int
    sender: str
    receiver: str
    signals: List[Signal]
    cycle_time_ms: Optional[int] = None
    description: str = ""


@dataclass
class NodeSpec:
    """Node configuration."""

    name: str
    role: str
    sends: List[str]
    receives: List[str]


class ProtocolSpec:
    """Load and query protocol specification from YAML."""

    def __init__(self, yaml_path: str | Path):
        self.path = Path(yaml_path)
        with open(self.path) as f:
            self.data = yaml.safe_load(f)

        self.version = self.data["protocol"]["version"]
        self.can_magic = self.data["can_config"]["magic"]
        self.frame_size = self.data["can_config"]["frame_size"]

        self.messages: Dict[str, MessageSpec] = self._parse_messages()
        self.nodes: Dict[str, NodeSpec] = self._parse_nodes()

        # Quick lookups
        self._msg_by_type: Dict[int, MessageSpec] = {
            msg.msg_type: msg for msg in self.messages.values()
        }
        self._msg_by_can_id: Dict[int, MessageSpec] = {
            msg.can_id: msg for msg in self.messages.values()
        }

    def _parse_messages(self) -> Dict[str, MessageSpec]:
        result = {}
        for msg_data in self.data["messages"]:
            signals = [
                Signal(
                    name=sig["name"],
                    start_bit=sig["start_bit"],
                    length=sig["length"],
                    value_type=sig["value_type"],
                    default=sig.get("default", 0),
                    unit=sig.get("unit"),
                )
                for sig in msg_data["signals"]
            ]

            result[msg_data["name"]] = MessageSpec(
                name=msg_data["name"],
                can_id=msg_data["can_id"],
                msg_type=msg_data["msg_type"],
                dlc=msg_data["dlc"],
                sender=msg_data["sender"],
                receiver=msg_data["receiver"],
                signals=signals,
                cycle_time_ms=msg_data.get("cycle_time_ms"),
                description=msg_data.get("description", ""),
            )
        return result

    def _parse_nodes(self) -> Dict[str, NodeSpec]:
        result = {}
        for node_name, node_data in self.data["nodes"].items():
            result[node_name] = NodeSpec(
                name=node_name,
                role=node_data["role"],
                sends=node_data["sends"],
                receives=node_data["receives"],
            )
        return result

    def get_message_by_name(self, name: str) -> MessageSpec:
        """Get message spec by name."""
        return self.messages[name]

    def get_message_by_type(self, msg_type: int) -> MessageSpec:
        """Get message spec by type ID."""
        return self._msg_by_type[msg_type]

    def get_message_by_can_id(self, can_id: int) -> MessageSpec:
        """Get message spec by CAN ID."""
        return self._msg_by_can_id[can_id]

    def get_sender(self, msg_type: int) -> str:
        """Get sender node name for a message type."""
        return self._msg_by_type[msg_type].sender

    def get_receiver(self, msg_type: int) -> str:
        """Get receiver node name for a message type."""
        return self._msg_by_type[msg_type].receiver

    def get_can_id_for_message(self, msg_name: str) -> int:
        """Get CAN ID for a message name."""
        return self.messages[msg_name].can_id

    def get_source_by_can_id(self, can_id: int) -> str:
        """Get the sender node name for a given CAN ID."""
        try:
            msg_spec = self.get_message_by_can_id(can_id)
            return msg_spec.sender
        except KeyError:
            return "unknown"
