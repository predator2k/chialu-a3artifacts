"""Runs a candidate hint generator in its own process.

The generator is code the search wrote, so it runs behind a timeout and
its output is validated before anything downstream sees it. Called as:

    python -m pfllm.harness <generator.py> <binary> <ensemble-csv> <fields> <out.json>
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from .disasm import disassemble, window

CONTEXT_LINES = 128
MAX_DEGREE = 3


def load_generator(path: str):
    spec = importlib.util.spec_from_file_location("candidate_hintgen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "emit_hints"):
        raise RuntimeError("the generator defines no emit_hints(disasm, loads, ensemble, fields)")
    return mod


def build_inputs(binary: str, context_lines: int = CONTEXT_LINES):
    disasm = disassemble(binary)
    loads = []
    for r in disasm:
        if not r["is_load"]:
            continue
        rec = dict(r)
        rec["context"] = window(disasm, r["pc"], context_lines)
        loads.append(rec)
    return disasm, loads


def validate(raw, loads, ensemble) -> dict:
    """Keep what is well formed, drop the rest; the caller turns the
    coverage that survives into a hard constraint."""
    want = {r["pc"] for r in loads}
    members = set(ensemble)
    out = {}
    for pc, h in (raw or {}).items():
        try:
            pc = int(pc)
        except (TypeError, ValueError):
            continue
        if pc not in want or not isinstance(h, dict):
            continue
        sel = h.get("select")
        if sel is None or sel == "none" or sel not in members:
            sel = "none"
        deg = h.get("degree", 2)
        deg = deg if isinstance(deg, int) and 1 <= deg <= MAX_DEGREE else 2
        flt = h.get("filter")
        flt = flt if (isinstance(flt, str) and flt in members and flt != "none") else None
        out[pc] = {"select": sel, "degree": deg, "filter": flt}
    return out


def main(argv) -> int:
    gen_path, binary, ensemble_csv, fields, out_path = argv[1:6]
    ensemble = [x for x in ensemble_csv.split(",") if x]
    disasm, loads = build_inputs(binary)
    mod = load_generator(gen_path)
    raw = mod.emit_hints(disasm, loads, ensemble, fields)
    hints = validate(raw, loads, ensemble)
    Path(out_path).write_text(json.dumps(
        {"binary": binary, "n_loads": len(loads), "hints": {str(k): v for k, v in hints.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
