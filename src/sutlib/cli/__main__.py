"""Allow running the monitor via python -m sutlib.cli."""

from .monitor import monitor

if __name__ == "__main__":
    monitor()
