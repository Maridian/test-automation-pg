"""Launch a SUT as a local subprocess (the virtual device)."""

from __future__ import annotations

import os
import subprocess
import sys

from ..config import TargetConfig
from .base import Target


class LocalProcessTarget(Target):
    """Runs `python -m <module> <args>` in a subprocess on the test host.

    This stands in for a real device today. The exact same SUT modules are
    meant to run on actual hardware later (see rpi.toml.example); only this
    launcher would be exchanged for an SSH-based one.
    """

    def __init__(self, name: str, config: TargetConfig) -> None:
        super().__init__(name)
        self._config = config
        self._process: subprocess.Popen | None = None

    def start(self) -> None:
        if not self._config.module:
            raise ValueError(f"Target '{self.name}' has no module configured")
        env = dict(os.environ)
        verbose = env.get("SUT_VERBOSE") == "1"
        self._process = subprocess.Popen(
            [sys.executable, "-m", self._config.module, *self._config.args],
            env=env,
            stdout=None if verbose else subprocess.DEVNULL,
            stderr=None if verbose else subprocess.DEVNULL,
        )

    def stop(self) -> None:
        if self._process is None or self._process.poll() is not None:
            self._process = None
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=3.0)
        self._process = None