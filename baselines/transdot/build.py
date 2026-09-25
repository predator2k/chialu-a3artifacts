"""The TransDot reference design (the no-DP SIMD FMA point) as one SystemVerilog
text per design point, read by yosys-slang and synthesized with chiALU's flow.

read_slang needs `-Wno-range-oob -Wno-index-oob` on this design: its
multi-format code selects a wider format's range from a narrower
format's signal in branches a generate condition never takes, and slang
is stricter about that than sv2v was.

    PYTHONPATH=3rdparty/chialu python3 baselines/transdot/build.py --point MERGED --clocks 5500 6800 8200 13700 --out runs/transdot

For each point (MERGED, PARALLEL) the `alu_core` text (the wrapper with
its decode, the number that enters the tables). The joined text is
written beside the results, so the conformance run and the tables read
the same file."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("CHIALU_SYNTH_REPORT", "0")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CVFPU = ROOT / "3rdparty" / "transdot"


def sources() -> list:
    out = []
    for line in (HERE / "files.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(CVFPU / line)
    return out


INCLUDE_DIRS = (CVFPU / "src" / "common_cells" / "include",)


def _inline_includes(text: str) -> str:
    """`include lines replaced by the file's text (the design is one
    joined file with no include path); a file not found stays as is."""
    import re

    def sub(m):
        name = m.group(1)
        for d in INCLUDE_DIRS:
            f = d / name
            if f.is_file():
                return f"// ---- `include \"{name}\"\n" + f.read_text() + "\n"
        return m.group(0)
    return re.sub(r'^\s*`include\s+"([^"]+)"\s*$', sub, text, flags=re.M)


def _strip_translate_off(text: str) -> str:
    """The simulation-only text between `pragma translate_off` and
    `pragma translate_on` removed (the assertions of the reference design
    are not part of the compared circuit)."""
    import re
    return re.sub(r"//\s*pragma\s+translate_off.*?//\s*pragma\s+translate_on[^\n]*", "// (translate_off block removed)", text, flags=re.S)


def joined(point: str, top_file: str) -> str:
    # slang: the multi-format code selects out of range in branches a generate condition never takes (see the module docstring)
    parts = ["`pragma diagnostic ignore=\"-Wrange-oob\"\n`pragma diagnostic ignore=\"-Windex-oob\"\n"
             f"`define FPNEW_ADDMUL {point}\n`define SIMD_ENABLE\n`define TRANSDOT_NO_DP\n`define FP8_INCLUDED\n`define COMBINATIONAL\n"]
    for f in sources() + [HERE / top_file]:
        parts.append(f"// ---- {f.relative_to(ROOT)}\n" + _strip_translate_off(_inline_includes(f.read_text())) + "\n")
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--point", nargs="*", default=["MERGED"])
    ap.add_argument("--clocks", nargs="*", type=int, default=[])
    ap.add_argument("--tight", type=int, default=300)
    ap.add_argument("--pdk", default="nangate45")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--out", default="runs/fpnew")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    results: dict = {}
    for point in a.point:
        for name, top_file, top in (("alu_core", "transdot_alu_core.sv", "alu_core"),):
            text = joined(point, top_file)
            f = out / f"transdot_{point.lower()}_{name}.sv"
            f.write_text(text)
            key = f"{point}/{name}"
            results[key] = {"file": str(f), "chars": len(text), "at": {}}
            print(f"[{key}] {len(text)} chars", flush=True)
            from chialu.eda import synth_ppa
            for clock in ([a.tight] + list(a.clocks)):
                t0 = time.time()
                r = synth_ppa(text, top, a.pdk, clock, timeout_s=3600, effort=a.effort, repeats=a.repeats)
                results[key]["at"][str(clock)] = dict(r)
                print(f"[{key}] {clock} ps: {r.get('area_um2')} um2, {r.get('abc_delay_ps')} ps, {r.get('cells')} cells, "
                      f"{round(time.time() - t0)} s" + ("" if r.get("ok") else f" FAILED {str(r.get('detail'))[:300]}"), flush=True)
    (out / "transdot_synth.json").write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
