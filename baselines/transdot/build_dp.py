"""TransDot's dot-product mode as one SystemVerilog text behind chiALU's
`dot_core`, read by yosys-slang and by Verilator.

    PYTHONPATH=<chialu tree>:<chialu tree>/third_party/adir \\
        python3 baselines/transdot/build_dp.py --row fp16 fp8 --out runs/tableb/transdot_dp

`--row mixed` joins transdot_dot_core.sv (the two-mode wrapper of
vec_dot_acc_cmp.yaml), `--row fp16` transdot_dot_core_fp16.sv and `--row fp8`
transdot_dot_core_fp8.sv (the one-mode wrappers of Table B's two rows). The
joined text is written beside the results, so the conformance run and the
tables read the same file; `--no-synth` writes the texts alone. The fork's
fma is register-free under `COMBINATIONAL` once tdot_comb.py has run."""
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
DEFINES = ("TRANSDOT_ENABLE", "USE_TRANSDOT_MULTIPLIER", "USE_TRANSDOT_EXPONENT_DATAPATH",
           "USE_TRANSDOT_ADDEND_DATAPATH", "USE_TRANSDOT_NORMALIZE_DATAPATH",
           "FP4_INCLUDED", "FP8_INCLUDED", "COMBINATIONAL")
ROWS = {"mixed": ("dot_core", "transdot_dot_core.sv"),
        "fp16": ("dot_core_fp16", "transdot_dot_core_fp16.sv"),
        "fp8": ("dot_core_fp8", "transdot_dot_core_fp8.sv")}


def sources() -> list:
    out = []
    for line in (HERE / "dp_files.txt").read_text().splitlines():
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
    parts = ["".join(f"`define {d}\n" for d in DEFINES)]
    for f in sources() + [HERE / top_file]:
        parts.append(f"// ---- {f.relative_to(ROOT)}\n"
                     + _strip_translate_off(_inline_includes(f.read_text())) + "\n")
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", nargs="*", default=None, choices=sorted(ROWS))
    ap.add_argument("--fp16", action="store_true", help="the one-mode fp16 wrapper (same as --row fp16)")
    ap.add_argument("--clocks", nargs="*", type=int, default=[])
    ap.add_argument("--tight", type=int, default=300)
    ap.add_argument("--pdk", default="nangate45")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--out", default="runs/transdot_dp")
    ap.add_argument("--no-synth", action="store_true")
    a = ap.parse_args()
    rows = a.row or (["fp16"] if a.fp16 else ["mixed"])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    results: dict = {}
    for row in rows:
        name, top_file = ROWS[row]
        text = joined(top_file)
        f = out / f"transdot_dp_{name}.sv"
        f.write_text(text)
        results[name] = {"file": str(f), "chars": len(text), "at": {}}
        print(f"[{name}] {len(text)} chars -> {f}", flush=True)
        if a.no_synth:
            continue
        from chialu.eda import synth_ppa
        for clock in ([a.tight] + list(a.clocks)):
            t0 = time.time()
            r = synth_ppa(text, "dot_core", a.pdk, clock, timeout_s=3600, effort=a.effort, repeats=a.repeats)
            results[name]["at"][str(clock)] = dict(r)
            print(f"[{name}] {clock} ps: {r.get('area_um2')} um2, {r.get('abc_delay_ps')} ps, "
                  f"{r.get('cells')} cells, {round(time.time() - t0)} s"
                  + ("" if r.get("ok") else f" FAILED {str(r.get('detail'))[:400]}"), flush=True)
        (out / "transdot_dp_synth.json").write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
