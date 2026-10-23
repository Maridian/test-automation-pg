"""Shared pytest fixtures: environment config, SUT topologies and observer links."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

# Make the project root (for `sut`) and the "src" directory (for the `sutlib`
# test harness) importable from anywhere pytest runs (local, CI).
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _entry in (".", "src", "sut"):
    _path = str((_PROJECT_ROOT / _entry).resolve())
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pytest

from sutlib import EnvConfig, SutTopology, load_env
from sutlib.links.base import LinkUnavailable

DEFAULT_SUT_ENV = "virtual"
@pytest.fixture(scope="session")
def env_config() -> EnvConfig:
    """Load the environment file selected via SUT_ENV (default: virtual)."""
    env_name = os.getenv("SUT_ENV", DEFAULT_SUT_ENV)
    path = Path(__file__).resolve().parents[1] / "config" / "environments" / f"{env_name}.toml"
    if not path.exists():
        pytest.fail(f"Environment config not found: {path}")
    return load_env(path)


@pytest.fixture(scope="session")
def sut_can(env_config: EnvConfig) -> Iterator[SutTopology]:
    """CAN topology: node A + node B as subprocesses on vcan0."""
    topology = env_config.topology("can")
    try:
        topology.start()
    except LinkUnavailable as exc:
        pytest.skip(f"CAN link not available: {exc}")
    yield topology
    topology.stop()


@pytest.fixture(scope="session")
def sut_eth(env_config: EnvConfig) -> Iterator[SutTopology]:
    """Ethernet topology: node A + node B as subprocesses over localhost TCP."""
    topology = env_config.topology("eth")
    try:
        topology.start()
    except LinkUnavailable as exc:
        pytest.skip(f"Ethernet link not available: {exc}")
    yield topology
    topology.stop()

