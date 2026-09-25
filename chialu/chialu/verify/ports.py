"""A port of a generated unit's interface: name, direction, width."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Port:
    name: str
    direction: str  # "in" | "out"
    width: int
