"""A reference design's wrapper through chiALU's conformance gate: the
target's verify bundle (the run file's spec, vectors and expected results,
with `verify.n_random` raised) simulated against the given RTL, the verdict
and the first mismatches explained in the reference model's terms.

    PYTHONPATH=3rdparty/chialu python3 baselines/conform.py --target targets/eval/fp_alu_cmp.yaml \\
        --rtl runs/fpnew/fpnew_merged_alu_core.sv --n-random 20000 --out runs/fpnew/conformance_merged.json

Runs on the EDA host (Verilator)."""
from __future__ import annotations

import argparse
import os
import json
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHIALU = Path(os.environ.get("CHIALU") or (ROOT / "3rdparty" / "chialu"))


def instance_with(target: Path, n_random: int, seed: int | None):
    """The target's instance with the verify knobs overridden, loaded from
    a copy of the run file beside the original (paths stay relative)."""
    from adir.instance import load
    text = target.read_text()
    text = re.sub(r"(verify\.n_random:[^\n]*\n\s*fixed:\s*)\d+", rf"\g<1>{n_random}", text)
    if seed is not None:
        text = re.sub(r"(verify\.seed:[^\n]*\n\s*fixed:\s*)\d+", rf"\g<1>{seed}", text)
    import os
    copy = target.with_name(target.stem + f".conform{n_random}.{os.getpid()}.yaml")   # one copy per process
    copy.write_text(text)
    try:
        return load(str(copy))
    finally:
        copy.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="the run file whose bundle judges the design")
    ap.add_argument("--rtl", required=True, help="the design (SystemVerilog; the top is alu_core)")
    ap.add_argument("--n-random", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    # chiALU and its own ADIR first: the host's environment may name another checkout
    sys.path.insert(0, str(CHIALU))
    sys.path.insert(0, str(CHIALU / "third_party" / "adir"))
    from adir.registry import underlying
    from chialu.eda import conformance, lint
    # the plain functions, run in this process: a CHIA node called directly joins a running Ray cluster
    conformance, lint = underlying(conformance), underlying(lint)
    inst = instance_with((CHIALU / a.target) if not Path(a.target).is_absolute() else Path(a.target), a.n_random, a.seed)
    files = inst.artifacts["verify_bundle"].texts
    rtl = Path(a.rtl).read_text()
    t0 = time.time()
    li = lint(rtl)
    print(f"lint: {'ok' if li.get('ok') else 'FAILED'} ({li.get('seconds')} s)" + ("" if li.get("ok") else f"\n{str(li.get('detail'))[:1500]}"), flush=True)
    r = conformance(rtl, files, a.timeout)
    r["lint"] = {k: li.get(k) for k in ("ok", "detail", "seconds")}
    r["n_random"] = a.n_random
    r["vectors"] = len(files["vectors.hex"].split()) if "vectors.hex" in files else None
    print(f"conformance: {'PASS' if r.get('pass') else 'FAIL'} over {r['vectors']} vectors in {round(time.time() - t0)} s")
    print(str(r.get("detail"))[:3000])
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(r, indent=1, default=str))
    return 0 if r.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
