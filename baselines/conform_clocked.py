"""A reference design with a pipeline stage through chiALU's conformance
gate: the target's bundle rebuilt with `latency_cycles`, so the bench
drives clk and rst_n and samples the result after L edges.

    PYTHONPATH=3rdparty/chialu python3 baselines/conform_clocked.py \\
        --target targets/eval/vec_dot_acc_cmp.yaml --rtl <design>.sv --latency 1 --n-random 2000
"""
from __future__ import annotations

import argparse
import os
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHIALU = Path(os.environ.get("CHIALU") or (ROOT / "3rdparty" / "chialu"))
sys.path.insert(0, str(CHIALU))
sys.path.insert(0, str(CHIALU / "third_party" / "adir"))

from conform import instance_with  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--rtl", required=True)
    ap.add_argument("--latency", type=int, default=1)
    ap.add_argument("--n-random", type=int, default=2000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from adir.registry import underlying
    from chialu.eda import conformance, lint
    from chialu.verify.harness import build_verification

    target = (CHIALU / a.target) if not Path(a.target).is_absolute() else Path(a.target)
    inst = instance_with(target, a.n_random, None)
    arts = {art.path: art for art in inst.artifacts.values()}
    files = dict(arts["verify_bundle"].texts)
    spec = json.loads(files["spec.json"])
    spec["latency_cycles"] = a.latency
    with tempfile.TemporaryDirectory() as td:
        build_verification(spec, Path(td))
        for name in ("tb.sv", "vectors.hex", "expected.hex", "freeze.json"):
            f = Path(td) / name
            if f.is_file():
                files[name] = f.read_text()
    files["spec.json"] = json.dumps(spec)

    rtl = Path(a.rtl).read_text()
    r = underlying(lint)(rtl)
    print(f"lint: {'ok' if r['ok'] else 'FAIL'}" + ("" if r["ok"] else "\n" + r["detail"][-1500:]))
    c = underlying(conformance)(rtl, files)
    print(f"conformance at latency {a.latency}: {'PASS' if c.get('pass') else 'FAIL'}; "
          f"{c.get('mismatch_count')} of {len(files['vectors.hex'].split())} vectors, {c.get('seconds')} s")
    for line in (c.get("first_mismatches") or [])[:8]:
        print("  " + str(line)[:200])
    print(str(c.get("detail"))[:1500])
    if a.out:
        Path(a.out).write_text(json.dumps({k: v for k, v in c.items()}, default=str, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
