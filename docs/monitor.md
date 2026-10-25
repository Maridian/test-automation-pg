# SUT Signal Monitor

The **SUT Signal Monitor** is an interactive development tool for live signal analysis during test development. It enables real-time monitoring of messages across various topologies (CAN, Ethernet, etc.).

## Features

- 🔴 **Live monitoring** of SUT signals in real-time
- 🎯 **Flexible filtering** by source and message type
- 📊 **Statistics overview** at the end of monitoring sessions
- 🎨 **Colorized console output** for better readability
- ⚙️ **Configurable** via environments and topologies

## Installation

The monitor tool is automatically installed with sutlib:

```bash
uv sync
```

## Usage

### Basic Usage

Simple monitoring with default settings (CAN, virtual environment):

```bash
sutlib-monitor
```

### Examples

Monitor Ethernet topology:

```bash
sutlib-monitor --topology eth
```

Show only messages from a specific source:

```bash
sutlib-monitor --filter-src node_a
```

Show only HEARTBEAT messages:

```bash
sutlib-monitor --filter-type HEARTBEAT
```

Automatically stop after 50 messages:

```bash
sutlib-monitor --count 50
```

Monitor hardware environment with CAN:

```bash
sutlib-monitor --env hardware --topology can
```

Combined filters:

```bash
sutlib-monitor --filter-src node_b --filter-type ACK --count 100
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--env` | `virtual` | Environment configuration (e.g., 'virtual', 'hardware') |
| `--topology` | `can` | Topology to monitor (e.g., 'can', 'eth') |
| `--count` | `None` | Stop after N messages (default: run until Ctrl+C) |
| `--filter-src` | `None` | Only show messages from this source |
| `--filter-type` | `None` | Only show messages of this type (HEARTBEAT, ACK) |

## Output Format

Each message is displayed in the following format:

```
No   Timestamp    Source      → Type         seq=##### can_id=0x###
   1    0.123s    node_a      → HEARTBEAT   seq=    1 can_id=0x100
   2    0.234s    node_b      → ACK         seq=   42 can_id=0x201
```

### Color Coding

- **Cyan**: Timestamps and headers
- **Yellow**: Source nodes and filters
- **Magenta**: HEARTBEAT messages
- **Green**: ACK messages and success notifications
- **Red**: Error messages

## Statistics

At the end of a monitoring session, a summary is displayed:

- Total number of messages received
- Number of messages displayed (after filtering)
- Breakdown by source and message type

Example:

```
Statistics:
  Total messages received: 250
  Messages displayed: 100

Message breakdown:
┏━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┓
┃ Source ┃ Type      ┃ Count ┃
┡━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━┩
│ node_a │ HEARTBEAT │    45 │
│ node_a │ ACK       │    30 │
│ node_b │ HEARTBEAT │    25 │
└────────┴───────────┴───────┘
```

## Error Handling

### CAN Interface Unavailable

For virtual CAN (vcan0), helpful setup commands are displayed:

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

### Environment Configuration Not Found

Make sure the corresponding configuration file exists:

```
config/environments/virtual.toml
config/environments/hardware.toml
```

## Use Cases

### Test Development

Observe SUT behavior during test development:

```bash
# Terminal 1: Start monitor
sutlib-monitor --filter-src node_a

# Terminal 2: Run tests
pytest tests/test_can.py -v
```

### Debugging

Analyze specific message types when troubleshooting:

```bash
sutlib-monitor --filter-type HEARTBEAT --count 200
```

### System Verification

Check if all nodes are active:

```bash
sutlib-monitor --count 100
# Review the message breakdown table
```

### Performance Analysis

Monitor message timing and frequency:

```bash
sutlib-monitor --topology can
# Watch timestamps and sequence numbers
```

## Integration with Other Tools

The monitor tool can be used in parallel with other sutlib tools:

```bash
# Terminal 1: Monitor
sutlib-monitor

# Terminal 2: Tests
pytest tests/

# Terminal 3: Interactive console
sutlib-console
```

## Tips & Tricks

1. **Quick Testing**: Use `--count 10` for rapid checks
2. **Log Files**: Combine with shell redirection for logs:
   ```bash
   sutlib-monitor --count 1000 > monitor.log 2>&1
   ```
3. **Combine Filters**: Use multiple filters simultaneously for precise analysis
4. **Timing Analysis**: Watch the timestamp column for timing issues

## See Also

- [Main README](../README.md) - Project overview
- [CAN Tests](../tests/test_can.py) - Example tests
- [Topology Configuration](../config/environments/) - Environment setup
