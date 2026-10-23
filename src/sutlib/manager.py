"""Manage one topology: SUT processes plus the harness observer link."""

from __future__ import annotations

import time

from .config import EnvConfig
from .links.base import Link, LinkUnavailable
from .targets.base import Target
from .targets.local import LocalProcessTarget


class SutTopology:
    """Combines SUT processes (targets) and the observer link of one environment."""

    def __init__(self, name: str, env: EnvConfig) -> None:
        self.name = name
        self._env = env
        self._targets: list[Target] = []
        self.link: Link | None = None

    def start(self, settle: float = 1.5) -> None:
        """Start all SUT subprocesses and open the observer link."""
        for node, cfg in self._env.targets[self.name].items():
            self._targets.append(LocalProcessTarget(node, cfg))
        for target in self._targets:
            target.start()

        try:
            self.link = self._env.create_link(self.name)
        except LinkUnavailable:
            self.stop()
            raise

        # Give the subprocesses time to spin up their transports.
        time.sleep(settle)

    def stop(self) -> None:
        """Close the observer link and stop all SUT subprocesses."""
        if self.link is not None:
            self.link.close()
            self.link = None
        for target in reversed(self._targets):
            target.stop()
        self._targets.clear()