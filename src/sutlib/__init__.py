"""Test harness for the test-automation-pg framework.

Host-side helpers: environment configuration, SUT process management and
link (CAN / Ethernet) abstractions used by the pytest tests.
"""

from .config import EnvConfig, LinkConfig, TargetConfig, load_env
from .manager import SutTopology

__all__ = [
    "EnvConfig",
    "LinkConfig",
    "SutTopology",
    "TargetConfig",
    "load_env",
]