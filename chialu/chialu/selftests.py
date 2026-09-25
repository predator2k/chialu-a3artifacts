"""Discovery for chiALU's selftests, and a runner over them.

`pytest` is the runner the suite uses, through `tests/test_selftests.py`,
which takes `discover()` and `SLOW` from here so the module list has one
definition:

    pytest -n 8 -m "not slow"     # the fast set
    pytest -n 2 -m slow           # the modules that drive a simulator or a synthesis

This module's own command line stays for a run without pytest:

    python3 -m chialu.selftests                 # the fast set
    python3 -m chialu.selftests --slow          # every module, the slow ones included
    python3 -m chialu.selftests --only fault    # the modules whose name holds a substring
    python3 -m chialu.selftests --list          # the modules and their group

A module exits 0 when it passes, so the runner's own exit code is 0 when
every module it ran passed and 1 otherwise. A module that times out or
crashes counts as a failure and its last output lines are printed.

`SLOW` names the modules that reach the EDA tools (yosys, Verilator,
or synthesize, which take minutes rather than seconds. They
stay out of the default set so the fast set is runnable on every change,
and `--slow` adds them back.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# the modules that drive a simulator or a synthesis, measured 2026-09-17; the rest finish in
# seconds on pure Python
SLOW = {
    "chialu.verify.domain_selftest",
    "chialu.verify.check_rules_selftest",
    "chialu.verify.combinational_sim_selftest",
    "chialu.verify.combinational_sim_check_selftest",
    "chialu.verify.checkers_selftest",
    "chialu.verify.simulate_selftest",
    "chialu.verify.fp_sharing_selftest",
    "chialu.verify.prompt_selftest",
    "chialu.targets.rtl.families.selftest",
    # measured alone on <host>, 2026-09-23: past the fast set's 600 s
    "chialu.verify.composition_selftest",        # 465 s: formal proofs of every composed adder's children
    "chialu.verify.dot_window_selftest",         # 733 s
    "chialu.verify.dot_arch_selftest",           # 526 s under load
    "chialu.verify.dot_exp_only_selftest",       # 407 s under load
    "chialu.verify.rns_rom_selftest",            # 665 s
    "chialu.verify.rns_chunk_selftest",          # 1748 s
    "chialu.verify.rns_cpa_range_selftest",      # 3019 s
    "chialu.verify.rns_geometry_selftest",       # RNS ALU seeds through Verilator, past 900 s under load
    "chialu.verify.dot_kulisch_selftest",        # 40 accumulator bindings up to 4288 bits, sharded
    "chialu.verify.cordic_rotation_selftest",    # sharded
}

# coverage campaigns over whole family products: hours of work, resumable and sharded from their own
# command lines, rather than a check a suite run completes. The suite runs them only when asked
# (CHIALU_CAMPAIGNS=1); each one's own `python3 -m <module>` is the full run.
CAMPAIGNS = {
    "chialu.verify.variant_selftest",            # every pin of every family at every dense width
}


def _ranges(module: str, size: int, *cases_args) -> list:
    """`--start/--stop` slices of `size` cases over the module's own case list,
    counted when the suite is collected, so a case added later lands in a slice."""
    import importlib
    total = len(list(importlib.import_module(module).cases(*cases_args)))
    return [(f"{i}-{min(i + size, total)}", ["--start", str(i), "--stop", str(min(i + size, total))])
            for i in range(0, total, size)]


def shards(module: str) -> list:
    """[(label, argv)]: how one module is split across workers. A module
    that runs for minutes is cut along its own command line (a case range,
    a section, a parameter list) into slices of a few minutes each, so
    `pytest -n auto` spreads it over the cores instead of one worker
    carrying it alone. Every other module is one run with no arguments.
    Each slice's exit status covers the cases it ran; the slices together
    run what the module's default run does.

    A slice's own pool is cut to one job (two for composition's proofs):
    the cores go to the suite's workers, and the load is workers times a
    slice's jobs times Verilator's `-j` (CHIALU_VERILATOR_JOBS). On <host>
    the suite runs `CHIALU_VERILATOR_JOBS=1 pytest -n 80`, which leaves room
    for the other users of the host."""
    if module == "chialu.verify.dot_kulisch_selftest":        # 40 bindings at 5 widths up to 4288 bits
        return _ranges(module, 4)
    if module == "chialu.verify.cordic_rotation_selftest":    # 11 iteration counts
        return [(label, argv + ["--jobs", "1"]) for label, argv in _ranges(module, 16)]
    if module == "chialu.verify.dot_window_selftest":         # 7 window widths and the multi-term contracts
        return _ranges(module, 64)
    if module == "chialu.verify.dot_arch_selftest":           # 62 contracts, about 8 s each
        return _ranges(module, 4)
    if module == "chialu.verify.dot_exp_only_selftest":       # 104 cases, about 4 s each
        return _ranges(module, 8)
    if module == "chialu.verify.rns_cpa_range_selftest":      # about 100 representative p in two batches
        return [("", ["--jobs", "2"])]
    if module == "chialu.verify.rns_chunk_selftest":
        chunks = [1, 2, 3, 4, 8, 9, 16, 31, 32, 33, 63, 64]     # the module's representative widths
        return ([(s, ["--section", s, "--jobs", "1"]) for s in ("geometry", "native", "alu")]
                + [(f"component-c{'-'.join(map(str, chunks[i:i + 3]))}",
                    ["--section", "component", "--jobs", "1", "--chunks", *map(str, chunks[i:i + 3])])
                   for i in range(0, len(chunks), 3)])
    if module == "chialu.verify.rns_rom_selftest":
        return [("native", ["--section", "native"])] + [
            (f"seeds-{f}", ["--section", "seeds", "--forms", f]) for f in ("pow2", "pow2_plus_1", "pow2_minus_1", "generic")]
    if module == "chialu.verify.rns_geometry_selftest":
        return [("boundaries", ["--section", "boundaries"])] + [
            (f"counts-{c}", ["--section", "counts", "--counts", str(c)]) for c in (3, 5, 6)]
    if module == "chialu.targets.rtl.families.selftest":
        # the representative space: every family's baseline and one sampled point per kind at 8, 16 and 32
        # bits (598 points, about 5 CPU-s each on <host>). The default run (14 widths to 512 bits, 8 samples,
        # 4,326 points at up to minutes each) was the suite's long tail; it stays the command-line default.
        return [(f"s{k}", ["--widths", "8,16,32", "--sample", "1", "--shard", f"{k}/10", "--jobs", "1"])
                for k in range(10)]
    if module == "chialu.verify.composition_selftest":
        return [(f"{f}-w{w}", ["--families", f, "--widths", w, "--jobs", "2"])
                for f in ("carry_skip", "carry_select", "carry_increment", "sparse_prefix_hybrid") for w in ("8", "16")]
    return [("", [])]


SELF = ".".join(pathlib.Path(__file__).resolve().relative_to(ROOT).with_suffix("").parts)
GUARD = "CHIALU_SELFTESTS_RUNNING"


def discover() -> list:
    """Every selftest module under the package, as an importable name.

    This module's own name is excluded. Its file is `selftests.py`, which
    a `*selftest*.py` glob matches, so a runner that discovered itself
    would spawn a copy of itself per module and fork without bound. The
    glob is anchored on `_selftest.py` for the same reason, and `main`
    refuses to run at all when it is already inside a run.
    """
    out = []
    for p in sorted(ROOT.joinpath("chialu").rglob("*.py")):
        if p.name.startswith("_"):
            continue
        if not (p.name.endswith("_selftest.py") or p.name == "selftest.py"):
            continue
        name = ".".join(p.relative_to(ROOT).with_suffix("").parts)
        if name != SELF:
            out.append(name)
    return out


def run_one(module: str, timeout_s: int, argv=()) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-m", module, *argv], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=timeout_s)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        rc = 124
        out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        out += f"\n[timeout after {timeout_s}s]"
    return {"module": module + (f"[{' '.join(argv)}]" if argv else ""), "rc": rc, "out": out,
            "seconds": round(time.time() - t0, 1)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--slow", action="store_true", help="run the slow modules too")
    ap.add_argument("--only", default="", help="run the modules whose name holds this substring")
    ap.add_argument("--list", action="store_true", help="list the modules and their group")
    ap.add_argument("--jobs", type=int, default=4, help="modules run at once")
    ap.add_argument("--timeout", type=int, default=1800, help="one module's wall limit")
    ap.add_argument("--lines", type=int, default=12, help="output lines printed for a failure")
    args = ap.parse_args(argv)
    if os.environ.get(GUARD):
        print(f"[selftests] refusing to run inside a run ({GUARD} is set)")
        return 1
    os.environ[GUARD] = "1"

    mods = discover()
    if args.only:
        mods = [m for m in mods if args.only in m]
    if args.list:
        for m in mods:
            print(f"{'slow' if m in SLOW else 'fast'}  {m}")
        print(f"[selftests] {len(mods)} modules, {sum(1 for m in mods if m in SLOW)} slow")
        return 0
    if not args.slow:
        mods = [m for m in mods if m not in SLOW]
    if not mods:
        print("[selftests] no module selected")
        return 1

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        jobs = [(m, argv) for m in mods if m not in CAMPAIGNS or args.slow for _label, argv in shards(m)]
        results = list(pool.map(lambda job: run_one(job[0], args.timeout, job[1]), jobs))
    failed = [r for r in results if r["rc"] != 0]
    for r in sorted(results, key=lambda r: -r["seconds"])[:5]:
        print(f"  {r['seconds']:7.1f}s  {r['module']}")
    for r in failed:
        print(f"\n=== FAIL rc={r['rc']} {r['module']} ({r['seconds']}s)")
        for line in r["out"].strip().splitlines()[-args.lines:]:
            print("    " + line[:200])
    print(f"\n[selftests] {len(results) - len(failed)} of {len(results)} passed in "
          f"{round(time.time() - t0)}s" + (f"; failed: {', '.join(r['module'] for r in failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
