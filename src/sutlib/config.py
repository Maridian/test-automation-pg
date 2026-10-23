"""Environment configuration handling.

A configuration file (config/environments/<name>.toml) describes the links
(CAN / Ethernet) and the SUT targets for one environment. The environment is
selected with the SUT_ENV environment variable (default: "virtual").
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

from .links.base import Link, LinkUnavailable
from .links.tcpip import TcpLink
from .links.vcan import VcanLink

if TYPE_CHECKING:
        from .manager import SutTopology


class LinkConfig(BaseModel):
    """Description of a single transport link (CAN or Ethernet)."""

    type: Literal["vcan", "tcpip"] = "tcpip"
    # CAN
    interface: str = "vcan0"
    # Ethernet
    host: str = "127.0.0.1"
    port: int = Field(default=41002, ge=1, le=65535)


class TargetConfig(BaseModel):
    """Description of how a single SUT is launched."""

    launch: Literal["subprocess", "ssh"] = "subprocess"
    module: str = ""
    command: str = ""
    args: list[str] = []


class EnvConfig(BaseModel):
    """Root object of an environment file."""

    name: str
    links: dict[str, LinkConfig]
    targets: dict[str, dict[str, TargetConfig]]

    def create_link(self, name: str) -> Link:
        """Instantiate the observer link for the given link name."""
        cfg = self.links[name]
        if cfg.type == "vcan":
            return VcanLink(interface=cfg.interface)
        if cfg.type == "tcpip":
            return TcpLink(host=cfg.host, port=cfg.port)
        raise LinkUnavailable(f"Unknown link type '{cfg.type}'")

    def topology(self, name: str) -> SutTopology:
        """Build a runnable topology (SUT processes + observer link)."""
        from .manager import SutTopology

        return SutTopology(name=name, env=self)


def load_env(path: str | Path) -> EnvConfig:
    """Load and validate an environment TOML file."""
    with open(path, "rb") as handle:
        data = tomllib.load(handle)
    return EnvConfig.model_validate(data)