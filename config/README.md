# Configuration Files

This directory contains configuration files for the test automation framework.

## Signal Specification (`signals.yaml`)

The `signals.yaml` file defines the complete protocol specification for CAN and Ethernet communication between SUT nodes.

### Structure

#### Protocol Configuration
- **version**: Protocol specification version
- **transports**: Supported transport layers (can, ethernet)

#### CAN Configuration
- **magic**: Magic byte for frame validation (0xAA)
- **frame_size**: CAN frame size in bytes (8)
- **byte_order**: Byte order for multi-byte values (big_endian)

#### Messages
Each message defines:
- **name**: Unique message identifier
- **can_id**: CAN arbitration ID (hex)
- **msg_type**: Message type ID (hex)
- **dlc**: Data Length Code (8 bytes)
- **sender**: Node that sends this message
- **receiver**: Node that receives this message
- **cycle_time_ms**: Optional periodic sending interval
- **description**: Human-readable description
- **signals**: List of signals within the message

#### Signal Definition
Each signal defines:
- **name**: Signal name
- **start_bit**: Starting bit position in frame
- **length**: Length in bits
- **value_type**: Data type (unsigned, signed)
- **default**: Optional default value
- **unit**: Optional unit of measurement

#### Nodes
Each node defines:
- **role**: Node role (primary, secondary)
- **sends**: List of message names this node sends
- **receives**: List of message names this node receives

### Example

```yaml
messages:
  - name: heartbeat
    can_id: 0x100
    msg_type: 0x01
    dlc: 8
    sender: node_a
    receiver: node_b
    cycle_time_ms: 100
    description: "Periodic heartbeat from primary node"
    signals:
      - name: magic
        start_bit: 0
        length: 8
        value_type: unsigned
        default: 0xAA
      - name: seq
        start_bit: 16
        length: 16
        value_type: unsigned
```

### Usage in Code

```python
from sut.common.signal_spec import ProtocolSpec

# Load specification
spec = ProtocolSpec("config/signals.yaml")

# Get message details
hb_spec = spec.get_message_by_name("heartbeat")
print(f"Heartbeat CAN ID: {hb_spec.can_id:#x}")
print(f"Sender: {hb_spec.sender}")

# Lookup by CAN ID
msg_spec = spec.get_message_by_can_id(0x100)
print(f"Message name: {msg_spec.name}")

# Get sender for a message type
sender = spec.get_sender(0x01)
print(f"Heartbeat sender: {sender}")
```

### Benefits

1. **Central Configuration**: All protocol definitions in one place
2. **No Hardcoding**: Message routing and IDs are configurable
3. **Version Control**: Protocol changes are tracked in git
4. **Documentation**: YAML is self-documenting
5. **Validation**: Can be validated with schema tools
6. **Extensibility**: Easy to add new messages and signals

### Modifying the Protocol

To add a new message:

1. Add the message definition to the `messages` list
2. Add corresponding entries to node `sends` and `receives` lists
3. Update the `MsgType` enum in `sut/common/protocol.py` if needed
4. No code changes required in most cases!

## Environment Configuration (`environments/`)

Environment-specific configuration files:
- `virtual.toml`: Local subprocess-based virtual environment
- `rpi.toml.example`: Example for Raspberry Pi hardware setup
