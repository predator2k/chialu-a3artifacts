"""Exercise every active LZA own-choice combination on real dot operand pairs."""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.dot import dot_family_requirements
from chialu.verify.variant_selftest import check_seed


def cases():
    contexts = (("classic_fma", {}), ("multi_term_fused_dot", {"alignment_strategy": "single_wide_window"}),
                ("fused_csa", {}), ("streaming_accurate_accumulator", {
                    "window_bits": 33, "approach": "tree_reduce_with_refinement", "in_loop_normalization": True}))
    for family, own in contexts:
        for correction, form, restriction, zero in product(
                ("post_norm_fine_shift", "compensation_in_rounding"), ("single_indicator", "dual_pos_neg_strings"),
                ("general", "positive_result_only"), ("indicator_or", "operand_function_or")):
            selectors = (None,) if form == "single_indicator" else ("true_sign", "maximum_count")
            for select in selectors:
                pins = dict(own, **{"lza.family": "lza", "lza.correction_scheme": correction,
                                   "lza.string_form": form, "lza.indicator_restriction": restriction,
                                   "lza.zero_result_detect": zero})
                if select is not None:
                    pins["lza.split_string_select"] = select
                yield family, pins


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--stop", type=int)
    ap.add_argument("--vectors", type=int, default=96)
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="chialu-dot-lza-"))
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for index, (family, pins) in enumerate(cases()):
        if index < args.start or (args.stop is not None and index >= args.stop):
            continue
        target = dot_family_requirements(family, pins)["spec"]
        target["rounding"] = ["RNE", "RTZ", "RDN", "RUP", "SR"]
        target["sr_bits"] = 4
        target["flags"] = ["invalid", "overflow", "underflow", "inexact", "denormal"]
        try:
            result = check_seed(target, (family, pins), out / str(index), args.vectors, 73)
        except Exception as exc:
            result = {"pass": False, "phase": "generation", "detail": f"{type(exc).__name__}: {exc}"}
        row = dict(index=index, family=family, pins=pins, **result)
        results.append(row)
        (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(row), flush=True)
    passed = sum(row.get("pass") is True for row in results)
    print(f"{'PASS' if passed == len(results) else 'FAIL'} {passed}/{len(results)} LZA contracts; {out}")
    return int(passed != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
