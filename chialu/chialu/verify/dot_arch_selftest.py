"""Simulate explicit dot architecture contracts, including partial flags.

This is an architectural regression matrix, not a certificate for every
recursive component pin product. Every PE-width Range member is included.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.dot import dot_family_requirements
from chialu.verify.variant_selftest import check_seed


def cases():
    family = "tensor_core_mixed_precision_mac"
    for width, rounding, align in product(range(4, 33, 4), ("rne", "truncate_toward_zero"),
                                          ("largest_exponent", "pairwise_sequential")):
        yield family, dict(dot_width_per_pe=width, partial_sum_rounding=rounding, alignment_target=align)
    family = "bf16_fma_datapath"
    for shape, flush in product(("scalar_fma", "dot2_accumulate", "dot4_accumulate"), (False, True)):
        yield family, dict(op_shape=shape, rounding_mode="round_to_odd", flush_subnormals=flush)
    family = "fp8_training_datapath"
    for precision, policy, stochastic in product(("fp16", "bf16", "fp32"), ("single_e4m3", "single_e5m2"), (False, True)):
        yield family, dict(op_shape="dot2_accumulate", chunk_based_accumulation=True,
                           accumulate_precision=precision, format_policy=policy, stochastic_rounding=stochastic)
    family = "mixed_precision_cascade_fma"
    for preserve, normalization, operators in product((False, True), ("dedicated", "on_demand_copy"),
                                                       ("addition", "multiplication", "both")):
        yield family, dict(exact_product_preserved=preserve, two_term_expansion_output=True,
                           error_term_normalization=normalization, error_term_ops=operators)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vectors", type=int, default=128)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--stop", type=int)
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="chialu-dot-arch-"))
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for index, (family, pins) in enumerate(cases()):
        if index < args.start or (args.stop is not None and index >= args.stop):
            continue
        target = dot_family_requirements(family, pins)["spec"]
        target["flags"] = ["invalid", "overflow", "underflow", "inexact", "denormal"]
        try:
            result = check_seed(target, (family, pins), out / str(index), args.vectors, 71)
        except Exception as exc:
            result = {"pass": False, "phase": "generation", "detail": f"{type(exc).__name__}: {exc}"}
        item = dict(index=index, family=family, pins=pins, **result)
        results.append(item)
        (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(item), flush=True)
    failed = [r for r in results if not r["pass"]]
    print(f"{'FAIL' if failed else 'PASS'} {len(results)-len(failed)}/{len(results)} architecture contracts; {out}")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
