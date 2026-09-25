"""chiALU's fp16 unit against the Berkeley TestFloat vectors (the plan's
section 3): `f16_add`, `f16_sub`, `f16_mul`, `f16_eq`, `f16_lt` and
`f16_le` under the four rounding modes, level-1 vectors from
`testfloat_gen`, through Verilator on the target's rendered seed.

    python3 harness/testfloat_harness.py --rtl /tmp/pipe_fpc4/seeds/baseline/program.sv \\
        --testfloat 3rdparty/berkeley-hardfloat/berkeley-testfloat-3/build/Linux-x86_64-GCC \\
        --out runs/testfloat

The comparisons are judged on their flags too, against SoftFloat's quiet
predicates; a NaN result matches any NaN, as TestFloat itself judges
without -checkNaNs. The report per (function, rounding mode): vectors,
mismatches, the first twenty."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# chiALU's `fcmp` is one quiet comparison returning {gt, eq, lt}: it raises invalid for a signalling
# NaN operand alone. SoftFloat's `f16_eq` is that predicate; its `f16_lt` and `f16_le` are the
# signalling ones, so the quiet variants are the comparable pair.
FUNCS = {"add": "f16_add", "sub": "f16_sub", "mul": "f16_mul", "eq": "f16_eq",
         "lt": "f16_lt_quiet", "le": "f16_le_quiet"}
RND = {0: "-rnear_even", 1: "-rminMag", 2: "-rmin", 3: "-rmax"}


def gen(testfloat: Path, func: str, rnd: int, level: int, out: Path) -> int:
    cmd = [str(testfloat / "testfloat_gen"), f"-level{level}", RND[rnd], func]
    with out.open("w") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, timeout=600)
    if r.returncode:
        raise RuntimeError(f"{' '.join(cmd)}: {r.stderr[-500:]}")
    return sum(1 for _ in out.open())


def build(rtl: Path, work: Path) -> Path:
    """The Verilator binary of the bench over the design (sv2v first, as
    chiALU's own flow does)."""
    design = work / "design.v"
    r = subprocess.run(["sv2v", str(rtl)], capture_output=True, text=True, timeout=900)
    if r.returncode:
        raise RuntimeError("sv2v: " + r.stderr[-800:])
    design.write_text(r.stdout)
    shutil.copy(HERE / "tb_testfloat.sv", work / "tb_testfloat.sv")
    r = subprocess.run(["verilator", "--binary", "-j", "4", "-Wno-fatal", "-Wno-lint", "-Wno-style", "--top-module", "tb",
                        "-Mdir", str(work / "obj"), "--x-assign", "fast", "-O2", str(work / "tb_testfloat.sv"), str(design)],
                       capture_output=True, text=True, timeout=3600, cwd=work)
    if r.returncode:
        raise RuntimeError("verilator: " + (r.stderr or r.stdout)[-1500:])
    return work / "obj" / "Vtb"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtl", required=True, help="the fp16-capable alu_core design (chiALU's fp_alu_cmp seed)")
    ap.add_argument("--testfloat", required=True, help="the directory holding testfloat_gen")
    ap.add_argument("--level", type=int, default=1)
    ap.add_argument("--funcs", nargs="*", default=list(FUNCS))
    ap.add_argument("--rnd", nargs="*", type=int, default=[0, 1, 2, 3])
    ap.add_argument("--out", default="runs/testfloat")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    report: dict = {"rtl": a.rtl, "level": a.level, "cases": {}}
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        t0 = time.time()
        binary = build(Path(a.rtl), work)
        print(f"built in {round(time.time() - t0)} s", flush=True)
        for kind in a.funcs:
            for rnd in (a.rnd if kind in ("add", "sub", "mul") else [0]):
                vec = work / f"{kind}_{rnd}.txt"
                n = gen(Path(a.testfloat), FUNCS[kind], rnd, a.level, vec)
                r = subprocess.run([str(binary), f"+vectors={vec}", f"+kind={kind}", f"+rnd={rnd}"],
                                   capture_output=True, text=True, timeout=3600)
                lines = r.stdout.splitlines()
                summary = next((l for l in lines if l.startswith("TESTFLOAT")), "")
                m = re.search(r"vectors=(\d+) mismatches=(\d+)", summary)
                classes = dict(re.findall(r"(qnan_invalid|nan_other|subnormal|other)=(\d+)", summary))
                case = {"function": FUNCS[kind], "rounding": RND[rnd], "vectors": int(m.group(1)) if m else n,
                        "mismatches": int(m.group(2)) if m else None, "pass": "PASS" in summary,
                        "classes": {k: int(v) for k, v in classes.items()},
                        "first": [l for l in lines if l.startswith("MISMATCH")][:20]}
                report["cases"][f"{kind}/{rnd}"] = case
                print(summary or f"{kind}/{rnd}: no summary ({r.stdout[-300:]} {r.stderr[-300:]})", flush=True)
    (out / "testfloat.json").write_text(json.dumps(report, indent=1))
    (out / "testfloat.md").write_text(table(report))
    return 0 if all(c["pass"] for c in report["cases"].values()) else 1


def table(report: dict) -> str:
    L = [f"# TestFloat level {report['level']} against `{report['rtl']}`", "",
         "Mismatch classes: `qnan_invalid` is a quiet-NaN operand where the flags differ in the invalid bit alone "
         "(chiALU's reference raises invalid on any NaN operand, IEEE 754 and TestFloat on a signalling one); "
         "`nan_other` another NaN-operand case; `subnormal` a subnormal operand or result; `other` the rest.", "",
         "| function | rounding | vectors | mismatches | qnan_invalid | nan_other | subnormal | other |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in report["cases"].values():
        k = c.get("classes", {})
        L.append(f"| `{c['function']}` | `{c['rounding']}` | {c['vectors']} | {c['mismatches']} | {k.get('qnan_invalid', 0)} | "
                 f"{k.get('nan_other', 0)} | {k.get('subnormal', 0)} | {k.get('other', 0)} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
