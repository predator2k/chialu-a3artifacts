"""PDK descriptors (pdk/<name>.yaml): the liberty files, the ABC
mapping script and the default clock the loop's synthesis step uses.
`resolve(name)` accepts the descriptor's name, one of its aliases, or the
legacy `<name>_yosys` form."""
from __future__ import annotations

from pathlib import Path

import yaml

PDK_DIR = Path(__file__).resolve().parent


def available() -> dict[str, dict]:
    out = {}
    for f in sorted(PDK_DIR.glob("*.yaml")):
        d = yaml.safe_load(f.read_text()) or {}
        out[d["name"]] = d
    return out


def resolve(name: str) -> dict:
    pdks = available()
    if name.endswith("_yosys"):
        name = name[: -len("_yosys")]
    for d in pdks.values():
        if name == d["name"] or name in (d.get("aliases") or []):
            return d
    names = sorted(f"{n} (aliases: {', '.join(d.get('aliases') or []) or '-'})"
                   for n, d in pdks.items())
    raise KeyError(f"no PDK descriptor for {name!r}; pdk/ has: {names}")
