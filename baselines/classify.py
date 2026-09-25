"""Every conformance mismatch of a reference wrapper, classified: the
target's verify bundle is simulated on the wrapper through chiALU's own
bench (the universal testbench in dump mode), the dump is compared with
the expected words, and each mismatch is decoded into (mode, op,
rounding, a, b, expected y and flags, got y and flags) and put in a
class:

* `qnan_invalid`: a quiet-NaN operand, the result agrees (NaN against
  NaN, or equal), the flags differ in the invalid bit alone (chiALU's
  reference raises invalid on any NaN operand, IEEE 754 on a signalling one)
* `snan_flags`: a signalling-NaN operand, flags differ
* `nan_result`: a NaN operand and the results disagree beyond NaN-ness
* `lane_flags`: a two-lane mode where the results agree and the flags
  differ between lanes (a reference that reports one status for both)
* `flags_only`: the results agree, other flag differences
* `value`: the results disagree without a NaN operand

    PYTHONPATH=3rdparty/chialu/third_party/adir:3rdparty/chialu python3 baselines/classify.py \\
        --target targets/eval/fp_alu_cmp.yaml --rtl runs/fpnew/fpnew_merged_alu_core.sv --n-random 20000 --out runs/fpnew/classes_merged.json
"""
from __future__ import annotations

import argparse
import os
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHIALU = Path(os.environ.get("CHIALU") or (ROOT / "3rdparty" / "chialu"))
sys.path.insert(0, str(CHIALU))
sys.path.insert(0, str(CHIALU / "third_party" / "adir"))

from conform import instance_with  # noqa: E402  (beside this file)


def ports_of(inst) -> tuple:
    """([(name, width)] inputs, [(name, width)] outputs) in the bench's
    packing order: the first port is the word's top slice."""
    ins, outs = [], []
    for line in inst.elaboration.info.get("interface") or []:
        m = re.match(r"\* `(\w+)`: (in|out)put, (\d+) bits", line)
        if m:
            (ins if m.group(2) == "in" else outs).append((m.group(1), int(m.group(3))))
    return ins, outs


def unpack(word: int, ports: list) -> dict:
    out = {}
    hi = sum(w for _, w in ports)
    for name, w in ports:
        out[name] = (word >> (hi - w)) & ((1 << w) - 1)
        hi -= w
    return out


FMT = {0: ("fp16", 16, 5, 10), 1: ("bf16", 16, 8, 7), 2: ("fp8e5m2", 8, 5, 2)}
OPS = ["fadd", "fsub", "fmul", "fmin", "fmax", "fcmp"]
RND = ["RNE", "RTZ", "RDN", "RUP"]


def lanes(mode: int, word: int) -> list:
    name, w, e, m = FMT[mode]
    n = 16 // w
    return [(word >> (i * w)) & ((1 << w) - 1) for i in range(n)]


def nan_kind(x: int, mode: int) -> str:
    name, w, e, m = FMT[mode]
    exp = (x >> m) & ((1 << e) - 1)
    man = x & ((1 << m) - 1)
    if exp == (1 << e) - 1 and man:
        return "qnan" if man >> (m - 1) else "snan"
    return ""


def classify(v: dict, exp: dict, got: dict) -> str:
    mode, op = v["mode"], v["op"]
    n = len(lanes(mode, v["a"]))
    a_l, b_l = lanes(mode, v["a"]), lanes(mode, v["b"])
    ey_l, gy_l = lanes(mode, exp["y"]), lanes(mode, got["y"])
    ef, gf = exp["flags"], got["flags"]
    nan_ops = [nan_kind(x, mode) for x in a_l + b_l]
    any_nan = any(nan_ops)
    y_same = all(ey == gy or (nan_kind(ey, mode) and nan_kind(gy, mode)) for ey, gy in zip(ey_l, gy_l))
    if y_same and ef == gf:
        return "none"
    if y_same:
        if any_nan and "snan" not in nan_ops and (ef ^ gf) & ~0x11 == 0 and (ef ^ gf):
            return "qnan_invalid"
        if "snan" in nan_ops:
            return "snan_flags"
        if n == 2:
            l0e, l1e, l0g, l1g = ef & 0xF, ef >> 4, gf & 0xF, gf >> 4
            if (l0g | l1g) == (l0e | l1e) or l0g == l1g:
                return "lane_flags"
        return "flags_only"
    if any_nan:
        return "nan_result"
    return "value"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--rtl", required=True)
    ap.add_argument("--n-random", type=int, default=20000)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from chialu.eda import _candidate_build, _run_campaign, _spec_of, rtl_of
    inst = instance_with((CHIALU / a.target) if not Path(a.target).is_absolute() else Path(a.target), a.n_random, None)
    files = inst.artifacts["verify_bundle"].texts
    ins, outs = ports_of(inst)
    rtl = rtl_of(Path(a.rtl).read_text())
    t0 = time.time()
    b, meta = _candidate_build(rtl, None, _spec_of(files), files)
    if not b.ok:
        print("build failed:", b.phase, str(b.detail)[:1000])
        return 2
    vectors = files["vectors.hex"].split()
    expected = files["expected.hex"].split()
    err, out, dump = _run_campaign(b, files, ["+campaign=0", "+vectors=vectors.hex", f"+n={len(vectors)}"], "dump.hex", a.timeout)
    if err:
        print("simulation failed:", err)
        return 2
    got_words = dump.split()
    print(f"{len(vectors)} vectors, {len(got_words)} dumped, {round(time.time() - t0)} s", flush=True)
    by_class: Counter = Counter()
    by_mode_op_class: Counter = Counter()
    examples: dict = {}
    mism = 0
    for i, (vw, ew, gw) in enumerate(zip(vectors, expected, got_words)):
        v = unpack(int(vw, 16), ins)
        e = unpack(int(ew, 16), outs)
        g = unpack(int(gw, 16), outs)
        c = classify(v, e, g)
        if c == "none":
            continue
        mism += 1
        by_class[c] += 1
        key = f"{FMT[v['mode']][0]}/{OPS[v['op']]}/{c}"
        by_mode_op_class[key] += 1
        if len(examples.setdefault(c, [])) < 6:
            examples[c].append(f"mode {FMT[v['mode']][0]} op {OPS[v['op']]} rnd {RND[v.get('rounding_sel', 0)]}: a={v['a']:04x} b={v['b']:04x} "
                               f"expected y={e['y']:04x} flags={e['flags']:02x} got y={g['y']:04x} flags={g['flags']:02x}")
    report = {"rtl": a.rtl, "vectors": len(vectors), "mismatches": mism, "by_class": dict(by_class),
              "by_mode_op_class": dict(sorted(by_mode_op_class.items())), "examples": examples, "seconds": round(time.time() - t0)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=1))
    print(f"mismatches {mism} of {len(vectors)}: {dict(by_class)}")
    for k, n in sorted(by_mode_op_class.items()):
        print(f"  {k}: {n}")
    for c, ex in examples.items():
        print(f"== {c}")
        for l in ex:
            print("  ", l)
    return 0


if __name__ == "__main__":
    sys.exit(main())
