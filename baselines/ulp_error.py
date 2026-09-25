"""The accuracy column of Table B: a dot design's conformance run measured in ulp.

The target's bundle (its corner and random vectors) is simulated on the design
through chiALU's own bench in dump mode, and every vector's packed `format_d`
result is compared with the reference under the fused contract, which is the
exact dot product rounded once (docs/formats-and-options.md, section 6), and
with the reference under the sequential contract (every product rounded to
format_d, then c and the products added one at a time with a rounding each).

The error of one vector, in ulp of the reference's binade:

* `ref` is the fused reference's packed d decoded as a rational; `got` is the
  design's d decoded the same way
* the ulp of a normal reference is 2^(e - (p - 1)), where e is the exponent of
  the reference's binade (floor(log2 |ref|)) and p the format's precision
  (24 for fp32)
* the ulp of a zero or subnormal reference is the format's smallest subnormal,
  2^(emin - (p - 1)) (2^-149 for fp32): the spacing of the subnormal binade
* the error is |got - ref| / ulp; a correctly rounded design scores 0 on every
  vector, and one that returns the other of two equal-distance candidates
  scores 1
* `ulp_vs_exact` is the same quotient against the exact rational dot product in
  the ulp of the exact value's binade (a correctly rounded design scores at most
  0.5 there); it is reported beside the column rather than in it
* a special result stays out of the ulp statistics and goes to a class:
  `special_agree` is not a class (it is `exact`: reference and design both NaN,
  or the same infinity); `nan_expected` / `inf_expected` (the reference is a
  NaN / an infinity and the design is not that special), `nan_got` / `inf_got`
  (the design is a NaN / an infinity where the reference is a number);
  `zero_sign` (both zero, signs differ) is a class of its own with error 0
* `exact` is the fraction of vectors whose packed d equals the fused
  reference's bit for bit (a NaN counts when both are NaN)

The report gives the maximum and the mean over the numeric vectors (the exact
ones count as 0), the fraction exact, a histogram of the error, the classes
with samples, and the same comparison against the sequential reference, which
is the contract statement of an FMA cascade.

    CHIALU=<chialu tree> PYTHONPATH=<chialu tree>:<chialu tree>/third_party/adir \\
        python3 baselines/ulp_error.py --target targets/eval/vec_dot_acc_cmp_fp16.yaml \\
        --rtl runs/tableb/transdot_dp/transdot_dp_dot_core_fp16.sv --n-random 3000 --out <json>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHIALU = Path(os.environ.get("CHIALU") or (ROOT / "3rdparty" / "chialu"))
for p in (str(CHIALU / "third_party" / "adir"), str(CHIALU), str(ROOT / "baselines")):
    if p not in sys.path:
        sys.path.insert(0, p)

from classify import ports_of, unpack  # noqa: E402
from conform import instance_with  # noqa: E402

BINS = [(0, 0.5), (0.5, 1), (1, 2), (2, 4), (4, 8), (8, 16), (16, 64), (64, 1024), (1024, float("inf"))]
BIN_NAMES = ["0"] + [f"({lo}, {hi}]" for lo, hi in BINS]


def bin_of(e: float) -> str:
    if e == 0:
        return "0"
    for lo, hi in BINS:
        if lo < e <= hi:
            return f"({lo}, {hi}]"
    return "?"


def floor_log2(x: Fraction) -> int:
    """floor(log2 x) of a positive rational, exactly."""
    n, d = x.numerator, x.denominator
    e = n.bit_length() - d.bit_length()
    if e >= 0:
        if n < (d << e):
            e -= 1
    else:
        if (n << -e) < d:
            e -= 1
    return e


def ulp_of(x: Fraction, fmt) -> Fraction:
    """The spacing of the binade of |x| in the float format (docstring above)."""
    p = fmt.man_bits + 1
    emin = 2 - fmt.bias
    ax = abs(x)
    if ax == 0 or ax < Fraction(2) ** emin:
        return Fraction(2) ** (emin - (p - 1))
    return Fraction(2) ** (floor_log2(ax) - (p - 1))


def special(fmt, bits: int) -> str:
    e = (bits >> fmt.man_bits) & ((1 << fmt.exp_bits) - 1)
    if e != (1 << fmt.exp_bits) - 1:
        return ""
    return "nan" if bits & ((1 << fmt.man_bits) - 1) else ("-inf" if bits >> (fmt.exp_bits + fmt.man_bits) else "+inf")


def _stats(errs: list) -> dict:
    return {"max_ulp": max(errs) if errs else None,
            "mean_ulp": (sum(errs) / len(errs)) if errs else None}


def measure(target: Path, rtl: str, n_random: int = 3000, seed=None, timeout: int = 3600, samples: int = 6) -> dict:
    """The report of the docstring for one design on one target's bundle."""
    from chialu.eda import _candidate_build, _run_campaign, _spec_of, rtl_of
    from chialu.verify import dot_ref as D
    from chialu.verify.formats import FloatFormat

    inst = instance_with(target, n_random, seed)
    arts = {art.path: art for art in inst.artifacts.values()}
    files = arts["verify_bundle"].texts
    ins, outs = ports_of(inst)
    spec = D.normalize_dot_spec(_spec_of(files))
    lay = D.dot_layout(spec)
    fused = dict(spec, dot_contract="fused")
    seq = dict(spec, dot_contract="sequential")
    lay_seq = D.dot_layout(seq)
    ctrl = D.vector_ctrl(spec, {})
    rtl = rtl_of(rtl)
    t0 = time.time()
    b, _meta = _candidate_build(rtl, None, spec, files)
    if b is None or not b.ok:
        return {"error": f"build failed: {getattr(b, 'phase', '?')}: {str(getattr(b, 'detail', 'no universal bench'))[:1500]}"}
    vectors = files["vectors.hex"].split()
    err, out, dump = _run_campaign(b, files, ["+campaign=0", "+vectors=vectors.hex", f"+n={len(vectors)}"],
                                   "dump.hex", timeout)
    if err:
        return {"error": f"simulation failed: {err}"}
    got_words = dump.split()
    if len(got_words) != len(vectors):
        return {"error": f"dump has {len(got_words)} words for {len(vectors)} vectors"}

    classes, samples_by, hist, hist_seq = Counter(), {}, Counter(), Counter()
    errs, errs_exact, errs_seq = [], [], []
    exact_bits = seq_exact_bits = 0
    seq_classes = Counter()
    worst = (-1.0, "")          # the vector of the largest error against the fused reference
    for i, (vw, gw) in enumerate(zip(vectors, got_words)):
        v = unpack(int(vw, 16), ins)
        g = unpack(int(gw, 16), outs)["d"]
        mi = v.get("mode", 0)
        m = lay["modes"][mi]
        fd = m["fd"]
        if not isinstance(fd, FloatFormat):
            raise SystemExit("the ulp column is defined for a float format_d alone")
        a_bits, b_bits, c_bits = v["a"], v["b"], v.get("c", 0)
        w = fd.width
        ref_d = D.dot_expected(fused, lay, mi, a_bits, b_bits, c_bits, ctrl, None)[0] & ((1 << w) - 1)
        seq_d = D.dot_expected(seq, lay_seq, mi, a_bits, b_bits, c_bits, ctrl, None)[0] & ((1 << w) - 1)
        g &= (1 << w) - 1
        sr, sg = special(fd, ref_d), special(fd, g)
        if g == ref_d or (sr == "nan" and sg == "nan"):
            cls = "exact"
        elif sr == "nan":
            cls = "nan_expected"
        elif sr:
            cls = "inf_expected"
        elif sg == "nan":
            cls = "nan_got"
        elif sg:
            cls = "inf_got"
        else:
            rv, gv = fd.decode(ref_d), fd.decode(g)
            cls = "zero_sign" if (rv == 0 and gv == 0) else "value"
        if cls == "exact":
            exact_bits += 1
            errs.append(0.0)
            errs_exact.append(0.0)
            hist["0"] += 1
        elif cls in ("zero_sign", "value"):
            rv, gv = fd.decode(ref_d), fd.decode(g)
            e = float(abs(gv - rv) / ulp_of(rv, fd))
            errs.append(e)
            hist[bin_of(e)] += 1
            n = D.n_products(m)
            av = D._values_of(m["fab"], a_bits, n, False)
            bv = D._values_of(m["fab"], b_bits, n, False)
            cv = D._values_of(m["fc"], c_bits, 1, False)[0][0] if lay["accumulate"] else Fraction(0)
            exact = sum((x[0] * y[0] for x, y in zip(av, bv)), Fraction(0)) + cv
            errs_exact.append(float(abs(gv - exact) / ulp_of(exact, fd)))
        if cls != "exact":
            classes[cls] += 1
            n = D.n_products(m)
            fab = m["fab"]
            la = [(a_bits >> (k * fab.width)) & ((1 << fab.width) - 1) for k in range(n)]
            lb = [(b_bits >> (k * fab.width)) & ((1 << fab.width) - 1) for k in range(n)]
            sp = [special(fab, x) for x in la + lb] + ([special(m["fc"], c_bits)] if lay["accumulate"] else [])
            key = f"{cls}/operand_special={'yes' if any(sp) else 'no'}"
            classes[key] += 1
            line = (f"i={i} mode {mi} a={la} b={lb} c={c_bits:0{(lay['c_w'] + 3) // 4}x} "
                    f"fused {ref_d:08x} sequential {seq_d:08x} got {g:08x} specials={[x for x in sp if x]}")
            if len(samples_by.setdefault(key, [])) < samples:
                samples_by[key].append(line)
            if cls in ("zero_sign", "value") and errs[-1] > worst[0]:
                worst = (errs[-1], f"{errs[-1]} ulp: {line}")
        ss = special(fd, seq_d)
        if g == seq_d or (ss == "nan" and sg == "nan"):
            seq_exact_bits += 1
            hist_seq["0"] += 1
            errs_seq.append(0.0)
        elif ss or sg:
            seq_classes["special" if ss else sg + "_got"] += 1
        else:
            sv, gv = fd.decode(seq_d), fd.decode(g)
            if sv == 0 and gv == 0:
                seq_classes["zero_sign"] += 1
                errs_seq.append(0.0)
                hist_seq["0"] += 1
            else:
                seq_classes["value"] += 1
                e = float(abs(gv - sv) / ulp_of(sv, fd))
                errs_seq.append(e)
                hist_seq[bin_of(e)] += 1

    n_vec = len(vectors)
    return {
        "target": str(target), "n_random": n_random, "vectors": n_vec,
        "definition": "error = |got - ref| / ulp(ref binade); ref is the fused reference's packed d; "
                      "zero or subnormal ref: ulp = 2^(emin - p + 1); specials are classes rather than errors",
        "vs_fused": {
            "exact_fraction": round(exact_bits / n_vec, 6), "exact": exact_bits, "numeric_vectors": len(errs),
            **_stats(errs),
            "max_ulp_vs_exact": max(errs_exact) if errs_exact else None,
            "mean_ulp_vs_exact": (sum(errs_exact) / len(errs_exact)) if errs_exact else None,
            "histogram": {k: hist[k] for k in BIN_NAMES if hist[k]},
            "classes": dict(sorted(classes.items())),
            "worst": worst[1],
        },
        "vs_sequential": {
            "exact_fraction": round(seq_exact_bits / n_vec, 6), "exact": seq_exact_bits,
            **_stats(errs_seq),
            "histogram": {k: hist_seq[k] for k in BIN_NAMES if hist_seq[k]},
            "classes": dict(sorted(seq_classes.items())),
        },
        "samples": samples_by,
        "seconds": round(time.time() - t0),
    }


def summary(report: dict) -> str:
    if "error" in report:
        return report["error"]
    f, s, n = report["vs_fused"], report["vs_sequential"], report["vectors"]
    r6 = lambda x: None if x is None else round(x, 6)  # noqa: E731
    lines = [f"vs fused: exact {f['exact']}/{n} ({100 * f['exact_fraction']:.2f}%), numeric {f['numeric_vectors']}, "
             f"max {f['max_ulp']} ulp, mean {r6(f['mean_ulp'])} ulp (vs the exact value: max {f['max_ulp_vs_exact']}, "
             f"mean {r6(f['mean_ulp_vs_exact'])})",
             f"  histogram: {f['histogram']}", f"  classes: {f['classes']}",
             f"  worst: {f.get('worst') or '-'}",
             f"vs sequential: exact {s['exact']}/{n} ({100 * s['exact_fraction']:.2f}%), max {s['max_ulp']} ulp, "
             f"mean {r6(s['mean_ulp'])} ulp; classes {s['classes']}"]
    for k, rows in report["samples"].items():
        lines.append(f"== {k}")
        lines += ["   " + r for r in rows]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="the run file whose bundle judges the design")
    ap.add_argument("--rtl", required=True, help="the design (SystemVerilog; the top is dot_core)")
    ap.add_argument("--n-random", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--out", default=None)
    ap.add_argument("--samples", type=int, default=6)
    a = ap.parse_args()
    target = (CHIALU / a.target) if not Path(a.target).is_absolute() else Path(a.target)
    report = measure(target, Path(a.rtl).read_text(), a.n_random, a.seed, a.timeout, a.samples)
    report["rtl"] = a.rtl
    print(summary(report))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(report, indent=1))
    return 0 if "error" not in report else 2


if __name__ == "__main__":
    sys.exit(main())
