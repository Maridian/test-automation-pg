"""Abstraction over how a SUT is started and stopped."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Target(ABC):
    """A single system-under-test node that runs somewhere."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def start(self) -> None:
        """Bring the SUT up."""

    @abstractmethod
    def stop(self) -> None:
        """Take the SUT down (must be idempotent)."""