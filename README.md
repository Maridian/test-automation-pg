# test-automation-pg

Modular pytest test framework for embedded devices that communicate over
**CAN** or **Ethernet** — fully virtual today, hardware-ready tomorrow.

Two software elements (a "sensor" and a "controller") act as system-under-test
(SUT). They talk to each other over a pluggable link and the tests verify the
communication end-to-end. Both SUTs currently run as local subprocesses
(virtual devices); swapping in real Raspberry Pis later only requires a new
environment configuration, **not** changes to the tests.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Linux with SocketCAN for CAN tests (`vcan0`). Ethernet tests run on any host.
- Optional: [Allure commandline](https://allurereport.org/docs/install/) to open the HTML report (`allure serve`). Java 17+ is required.

## Setup

```bash
uv sync --all-groups
```

Bring up a virtual CAN interface (Linux, required for CAN tests):

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

If `vcan0` is missing, CAN tests are skipped automatically.

## Run tests

```bash
uv run pytest
```

Useful variants:

```bash
# Ethernet only (works on Windows / macOS)
uv run pytest -m transport_eth

# CAN only (needs vcan0)
uv run pytest -m transport_can

# Skip hardware-marked tests (CI default)
uv run pytest -m "not hardware"

# See SUT stdout/stderr
SUT_VERBOSE=1 uv run pytest
```

Every run writes Allure results to `reports/allure-results` (gitignored).
Open them locally with the Allure CLI:

```bash
allure serve reports/allure-results
```

Or build a static HTML report (what CI uploads as an artifact):

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

Select an environment with `SUT_ENV` (default: `virtual`):

```bash
SUT_ENV=virtual uv run pytest
```

CI (GitHub Actions) installs uv, lints with Ruff, and runs
`pytest -m "not hardware"` with JUnit, coverage, and Allure reports. It tries
to create `vcan0`; GitHub-hosted Ubuntu runners currently use an Azure kernel
without the `vcan` module, so CAN tests are skipped there and Ethernet
tests still run. Download the `test-reports` artifact and open
`allure-report/index.html`.

## Structure

```
config/environments/   Environment TOML (links + how SUTs are launched)
src/sutlib/            Host-side harness: config, process manager, observer links
sut/                   Devices under test (same code later on real hardware)
  common/              Shared protocol (CAN 2.0 frames / JSON-lines over TCP)
  node_a/              Sensor: periodic heartbeats
  node_b/              Controller: ACK every heartbeat
tests/                 pytest fixtures and end-to-end checks
```

| Path | Role |
| --- | --- |
| `src/sutlib/config.py` | Load and validate `config/environments/<name>.toml` |
| `src/sutlib/manager.py` | Start/stop a topology (SUT processes + observer link) |
| `src/sutlib/targets/` | Launch abstraction (`subprocess` today, `ssh` later) |
| `src/sutlib/links/` | Observer links: SocketCAN (`vcan`) and TCP (`tcpip`) |
| `tests/conftest.py` | Session fixtures `env_config`, `sut_can`, `sut_eth` |

## How a test run works

1. pytest loads `config/environments/$SUT_ENV.toml` (default `virtual`).
2. The `sut_can` / `sut_eth` fixture starts node A and node B as local
   subprocesses and opens an observer link on the same bus or TCP port.
3. Node A sends heartbeats. Node B ACKs them with the same sequence number.
   On Ethernet, node B also re-emits traffic so the harness sees both
   directions on one connection.
4. Tests wait for matching messages via `wait_for_message`.
5. The fixture stops the subprocesses after the session.

Tests assert behaviour, not launch details. Changing *where* a node runs
means changing the environment file, not the test.

## Protocol

Logical fields are identical on both transports: type, sequence, timestamp, source.

- **CAN 2.0**: 8-byte frames `magic(1) | type(1) | seq(2) | ts_ms(4)`
  - heartbeat: CAN ID `0x100` (node A → node B)
  - ACK: CAN ID `0x200` (node B → node A)
- **Ethernet**: JSON-lines over TCP (`127.0.0.1:41002` in the virtual env)

## Environments

`config/environments/virtual.toml` launches both nodes as `python -m …`
subprocesses. CAN uses `vcan0`; Ethernet uses localhost TCP.

`config/environments/rpi.toml.example` is the intended hardware layout
(SSH launch, real `can0` / device IPs). Copy it to `rpi.toml`, fill in
addresses, and run with `SUT_ENV=rpi`. The `ssh` launch type is not
implemented yet; that is the extension point for real Raspberry Pis.

## Markers

| Marker | Meaning |
| --- | --- |
| `transport_can` | Needs a CAN / vcan link |
| `transport_eth` | Needs an Ethernet / TCP link |
| `hardware` | Needs real hardware (skipped in CI) |

## License

MIT. See [LICENSE](LICENSE).
