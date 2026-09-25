"""Every conformance mismatch of a dot wrapper, classified.

The target's bundle is simulated on the wrapper through chiALU's own
bench in dump mode, the dump is compared with the expected words, and
each mismatch is decoded into (mode, the operand lanes, expected d, got
d) and put in a class:

* `nan_expected`: the reference's d is a NaN and the design's is a number
* `inf_expected`: the reference's d is an infinity and the design's is not
* `value`: both are numbers and they differ
* `nan_got`: the design's d is a NaN and the reference's is not

    PYTHONPATH=3rdparty/chialu python3 baselines/classify_dot.py \\
        --target targets/eval/vec_dot_acc_cmp.yaml --rtl <design>.sv --n-random 500
"""
from __future__ import annotations

import argparse
import os, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHIALU = Path(os.environ.get("CHIALU") or (ROOT / "3rdparty" / "chialu"))
sys.path.insert(0, str(CHIALU))
sys.path.insert(0, str(CHIALU / "third_party" / "adir"))
sys.path.insert(0, str(ROOT / "baselines"))
from conform import instance_with  # noqa: E402

ELEM = {0: (16, 5, 10, 2), 1: (8, 5, 2, 4)}   # mode -> (width, exp bits, man bits, lanes)


def special(x: int, e: int, m: int) -> str:
    if ((x >> m) & ((1 << e) - 1)) != (1 << e) - 1:
        return ""
    return "nan" if (x & ((1 << m) - 1)) else "inf"


def f32(x: int) -> str:
    return special(x, 8, 23) or "num"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--rtl", required=True)
    ap.add_argument("--n-random", type=int, default=500)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from chialu.eda import _candidate_build, _run_campaign, _spec_of, rtl_of
    inst = instance_with((CHIALU / a.target) if not Path(a.target).is_absolute() else Path(a.target),
                         a.n_random, None)
    arts = {art.path: art for art in inst.artifacts.values()}
    files = arts["verify_bundle"].texts
    rtl = rtl_of(Path(a.rtl).read_text())
    t0 = time.time()
    b, meta = _candidate_build(rtl, None, _spec_of(files), files)
    if not b.ok:
        print("build failed:", b.phase, str(b.detail)[:800]); return 2
    vectors = files["vectors.hex"].split()
    expected = files["expected.hex"].split()
    err, out, dump = _run_campaign(b, files, ["+campaign=0", "+vectors=vectors.hex",
                                              f"+n={len(vectors)}"], "dump.hex", a.timeout)
    if err:
        print("simulation failed:", err); return 2
    got = dump.split()
    print(f"{len(vectors)} vectors, {len(got)} dumped, {round(time.time() - t0)} s", flush=True)

    classes, by_mode, samples = Counter(), Counter(), {}
    for i, (hv, he, hg) in enumerate(zip(vectors, expected, got)):
        e, g = int(he, 16) & 0xFFFFFFFF, int(hg, 16) & 0xFFFFFFFF
        if e == g:
            continue
        w = int(hv, 16)
        mode = w & 1
        c = (w >> 1) & 0xFFFFFFFF
        bb = (w >> 33) & 0xFFFFFFFF
        aa = (w >> 65) & 0xFFFFFFFF
        ew, eb, mb, n = ELEM[mode]
        la = [(aa >> (k * ew)) & ((1 << ew) - 1) for k in range(n)]
        lb = [(bb >> (k * ew)) & ((1 << ew) - 1) for k in range(n)]
        sp = [special(x, eb, mb) for x in la + lb] + [special(c, 8, 23)]
        kind = f32(e)
        cls = {"nan": "nan_expected", "inf": "inf_expected"}.get(kind, "value")
        if f32(g) == "nan" and kind == "num":
            cls = "nan_got"
        key = f"{cls}/operand_special={'yes' if any(sp) else 'no'}"
        classes[key] += 1
        by_mode[f"mode{mode}/{cls}"] += 1
        samples.setdefault(key, []).append(
            f"mode {mode} a={la} b={lb} c={c:08x} expected {e:08x} got {g:08x} specials={[x for x in sp if x]}")
    print("mismatches", sum(classes.values()), "of", len(vectors))
    for k, v in sorted(classes.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    for k, v in sorted(by_mode.items()):
        print(f"  {k}: {v}")
    for k, rows in samples.items():
        print("==", k)
        for r in rows[:4]:
            print("  ", r)
    if a.out:
        Path(a.out).write_text(json.dumps({"classes": classes, "by_mode": by_mode,
                                           "samples": {k: v[:20] for k, v in samples.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
