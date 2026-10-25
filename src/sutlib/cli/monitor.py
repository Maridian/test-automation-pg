"""Interactive monitoring tool for live signal analysis during test development."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure imports work
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))
if str(_PROJECT_ROOT / "sut") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "sut"))

from sutlib import load_env
from sutlib.links.base import LinkUnavailable
from sut.common.protocol import MsgType


@click.command()
@click.option(
    "--env",
    default="virtual",
    help="Environment config name (e.g., 'virtual', 'hardware')",
)
@click.option(
    "--topology",
    default="can",
    help="Topology to monitor (e.g., 'can', 'eth')",
)
@click.option(
    "--count",
    type=int,
    default=None,
    help="Stop after N messages (default: run until Ctrl+C)",
)
@click.option(
    "--filter-src",
    help="Only show messages from this source (e.g., 'node_a')",
)
@click.option(
    "--filter-type",
    type=click.Choice(["HEARTBEAT", "ACK"], case_sensitive=False),
    help="Only show messages of this type",
)
def monitor(
    env: str,
    topology: str,
    count: int | None,
    filter_src: str | None,
    filter_type: str | None,
):
    """Live monitor for SUT signals - useful for test development and debugging.

    Examples:

        sutlib-monitor                          # Monitor CAN with defaults

        sutlib-monitor --topology eth           # Monitor Ethernet

        sutlib-monitor --filter-src node_a      # Only node_a messages

        sutlib-monitor --count 50               # Stop after 50 messages
    """
    console = Console()

    # Header
    console.print(
        Panel.fit(
            f"[bold cyan]SUT Signal Monitor[/bold cyan]\n"
            f"Environment: [yellow]{env}[/yellow] | "
            f"Topology: [yellow]{topology}[/yellow]",
            border_style="cyan",
        )
    )

    # Load environment and topology
    config_path = _PROJECT_ROOT / "config" / "environments" / f"{env}.toml"
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Environment config not found: {config_path}")
        sys.exit(1)

    try:
        env_config = load_env(config_path)
        sut = env_config.topology(topology)
    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        sys.exit(1)

    # Start topology
    try:
        console.print("[green]Starting topology...[/green]")
        sut.start()
    except LinkUnavailable as e:
        console.print(f"[red]Link unavailable:[/red] {e}")
        console.print("[yellow]Hint:[/yellow] For CAN, make sure vcan0 is up:")
        console.print("  sudo modprobe vcan")
        console.print("  sudo ip link add dev vcan0 type vcan")
        console.print("  sudo ip link set up vcan0")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error starting topology:[/red] {e}")
        sys.exit(1)

    # Show active filters
    if filter_src or filter_type:
        filters = []
        if filter_src:
            filters.append(f"source={filter_src}")
        if filter_type:
            filters.append(f"type={filter_type}")
        console.print(f"[yellow]Filters active:[/yellow] {', '.join(filters)}")

    console.print("[green]Monitoring...[/green] (press Ctrl+C to stop)\n")

    # Message counters
    msg_count = 0
    total_count = 0
    msg_stats = {}

    try:
        while True:
            if count and msg_count >= count:
                break

            msg = sut.link.recv(timeout=1.0)
            if not msg:
                continue

            total_count += 1

            # Apply filters
            if filter_src and msg.src != filter_src:
                continue
            if filter_type and msg.msg_type.name != filter_type.upper():
                continue

            msg_count += 1

            # Update statistics
            key = (msg.src, msg.msg_type.name)
            msg_stats[key] = msg_stats.get(key, 0) + 1

            # Format message type with color
            type_color = "magenta" if msg.msg_type == MsgType.HEARTBEAT else "green"

            # Display message
            console.print(
                f"[dim]{msg_count:4d}[/dim] "
                f"[cyan]{msg.ts_ms/1000:8.3f}s[/cyan] "
                f"[yellow]{msg.src:10s}[/yellow] → "
                f"[{type_color}]{msg.msg_type.name:12s}[/{type_color}] "
                f"seq=[bold]{msg.seq:5d}[/bold] "
                f"can_id=[dim]0x{msg.can_id:03x}[/dim]"
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped by user[/yellow]")

    finally:
        # Show statistics
        console.print("\n" + "─" * 60)
        console.print("[bold]Statistics:[/bold]")
        console.print(f"  Total messages received: {total_count}")
        console.print(f"  Messages displayed: {msg_count}")

        if msg_stats:
            console.print("\n[bold]Message breakdown:[/bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("Source", style="yellow")
            table.add_column("Type", style="cyan")
            table.add_column("Count", justify="right", style="green")

            for (src, msg_type), count in sorted(msg_stats.items()):
                table.add_row(src, msg_type, str(count))

            console.print(table)

        console.print("\n[green]Stopping topology...[/green]")
        sut.stop()
        console.print("[green]Done.[/green]")


if __name__ == "__main__":
    monitor()
