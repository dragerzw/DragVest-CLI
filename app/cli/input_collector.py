# app/cli/input_collector.py
from typing import Any, Optional, Union
from rich.prompt import Prompt
from rich.console import Console
from app.cli.constants import APP_NAME
from decimal import Decimal, InvalidOperation

console = Console()

def get_string(prompt: str = f"{APP_NAME} Input") -> str:
    """
    Prompt the user for a non-empty string. Returns empty string on cancel (Ctrl-C/Ctrl-D).
    """
    while True:
        try:
            value = console.input(f"[bold]{prompt}[/bold] > ")
            if value is None:
                return ""
            value = value.strip()
            if value == "":
                console.print("[red]Input cannot be empty. Please try again.[/red]")
                continue
            return value
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Input cancelled.[/red]")
            return ""

def get_int(prompt: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """
    Prompt the user for an integer. Returns 0 on cancel/invalid flow (caller should handle).
    """
    while True:
        try:
            raw = console.input(f"[bold]{prompt}[/bold] > ")
            if raw is None:
                return 0
            raw = raw.strip()
            if raw == "":
                console.print("[red]Please enter a number.[/red]")
                continue
            try:
                val = int(raw)
            except ValueError:
                console.print("[red]Invalid integer. Try again.[/red]")
                continue
            if (min_value is not None and val < min_value) or (max_value is not None and val > max_value):
                rmin = f"{min_value}" if min_value is not None else ""
                rmax = f"{max_value}" if max_value is not None else ""
                console.print(f"[red]Please enter a number between {rmin} and {rmax}.[/red]")
                continue
            return val
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Input cancelled.[/red]")
            return 0

def get_float(prompt: str, min_value: Optional[Union[float, Decimal]] = None, max_value: Optional[Union[float, Decimal]] = None) -> Decimal:
    """
    Prompt the user for a numeric value and return a Decimal.

    Returns Decimal('0.00') on cancel to preserve previous behavior where callers
    expected a numeric return. `min_value` and `max_value` may be provided as
    float or Decimal and are converted to Decimal for comparison.
    """
    # Normalize min/max to Decimal if provided
    min_dec = Decimal(str(min_value)) if min_value is not None else None
    max_dec = Decimal(str(max_value)) if max_value is not None else None
    while True:
        try:
            raw = console.input(f"[bold]{prompt}[/bold] > ")
            if raw is None:
                return Decimal('0.00')
            raw = raw.strip()
            if raw == "":
                console.print("[red]Please enter a number.[/red]")
                continue
            try:
                val = Decimal(raw)
            except (InvalidOperation, ValueError):
                console.print("[red]Invalid number. Try again.[/red]")
                continue
            if (min_dec is not None and val < min_dec) or (max_dec is not None and val > max_dec):
                rmin = f"{min_value}" if min_value is not None else ""
                rmax = f"{max_value}" if max_value is not None else ""
                console.print(f"[red]Please enter a number between {rmin} and {rmax}.[/red]")
                continue
            return val
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Input cancelled.[/red]")
            return Decimal('0.00')
