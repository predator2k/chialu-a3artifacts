"""TransDot's no-DP SIMD FMA as a cascade of fused multiply-adds behind chiALU's
`dot_core` (Table B's sequential-contract reference row from TransDot), one
SystemVerilog text per row, read by yosys-slang and by Verilator.

    PYTHONPATH=<chialu tree>:<chialu tree>/third_party/adir \\
        python3 baselines/transdot_no_dp/build.py --row fp16 fp8 --out runs/tableb/transdot_no_dp

`--row fp16` joins transdot_no_dp_dot_core_fp16.sv (two stages), `--row fp8`
transdot_no_dp_dot_core_fp8.sv (four stages). The joined text is written
beside the results, so the conformance run and the tables read the same
file; `--no-synth` writes the texts alone."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

os.environ.setdefault("CHIALU_SYNTH_REPORT", "0")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TRANSDOT = ROOT / "3rdparty" / "transdot"
INCLUDE_DIRS = (TRANSDOT / "src" / "common_cells" / "include", TRANSDOT / "src")
# the defines of the fork's no-DP build (baselines/transdot/build.py), so the FMA's text
# elaborates as it does under the fork's fpnew_top
DEFINES = ("SIMD_ENABLE", "TRANSDOT_NO_DP", "FP8_INCLUDED", "COMBINATIONAL")
# The suppression the reference design needs, recorded here rather than in it (the plan's
# section 8): the FMA's fp8 and 16-bit SIMD lanes iterate every enabled format, and a
# format wider than the lane selects a range outside its signal in branches the scalar
# path never takes (`fpnew_round_classify_stage` of the fp8 lanes with FP32 enabled).
# slang refuses those selects by default; the flow's `read_slang` carries no -Wno flags,
# so the joined text turns the two diagnostics off itself. Those lanes' results are unused
# under simd_enable 0 and synthesis removes them.
PRAGMAS = ('`pragma diagnostic ignore="-Wrange-oob"', '`pragma diagnostic ignore="-Windex-oob"')
ROWS = {"fp16": "transdot_no_dp_dot_core_fp16.sv", "fp8": "transdot_no_dp_dot_core_fp8.sv"}


def sources() -> list:
    out = []
    for line in (HERE / "files.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(TRANSDOT / line)
    return out


def _inline_includes(text: str) -> str:
    """`include lines replaced by the file's text (the design is one joined
    file with no include path); a file not found stays as is."""
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
    return re.sub(r"//\s*pragma\s+translate_off.*?//\s*pragma\s+translate_on[^\n]*",
                  "// (translate_off block removed)", text, flags=re.S)


def joined(top_file: str) -> str:
    parts = ["".join(f"{p}\n" for p in PRAGMAS) + "".join(f"`define {d}\n" for d in DEFINES)]
    for f in sources() + [HERE / top_file]:
        parts.append(f"// ---- {f.relative_to(ROOT)}\n"
                     + _strip_translate_off(_inline_includes(f.read_text())) + "\n")
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", nargs="*", default=["fp16", "fp8"], choices=sorted(ROWS))
    ap.add_argument("--clocks", nargs="*", type=int, default=[40000])
    ap.add_argument("--pdk", default="nangate45")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--out", default="runs/tableb/transdot_no_dp")
    ap.add_argument("--no-synth", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    results: dict = {}
    for row in a.row:
        text = joined(ROWS[row])
        f = out / f"transdot_no_dp_dot_core_{row}.sv"
        f.write_text(text)
        results[row] = {"file": str(f), "chars": len(text), "at": {}}
        print(f"[{row}] {len(text)} chars -> {f}", flush=True)
        if a.no_synth:
            continue
        from chialu.eda import synth_ppa
        for clock in a.clocks:
            t0 = time.time()
            r = synth_ppa(text, "dot_core", a.pdk, clock, timeout_s=3600, effort=a.effort, repeats=a.repeats)
            results[row]["at"][str(clock)] = dict(r)
            print(f"[{row}] {clock} ps: {r.get('area_um2')} um2, {r.get('abc_delay_ps')} ps, "
                  f"{r.get('cells')} cells, {round(time.time() - t0)} s"
                  + ("" if r.get("ok") else f" FAILED {str(r.get('detail'))[:400]}"), flush=True)
        (out / "transdot_no_dp_synth.json").write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
