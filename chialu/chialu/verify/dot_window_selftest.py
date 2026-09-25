"""Exercise every declared window and guard value against independent arithmetic."""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.dot import dot_family_requirements
from chialu.verify.variant_selftest import check_seed


# the window widths a default run binds: the Range's ends (33, 256) and each side of a power of two, where
# the window's word boundary moves; --full walks every width of 33..256
REPRESENTATIVE_WINDOWS = (33, 63, 64, 65, 128, 129, 256)


def cases(full=False):
    for width, approach, normalize in product(range(33, 257) if full else REPRESENTATIVE_WINDOWS,
            ("shifted_fixed_point_window", "tree_reduce_with_refinement"), (False, True)):
        yield "streaming_accurate_accumulator", dict(window_bits=width, approach=approach,
                                                    in_loop_normalization=normalize)
    for guard, contract, alignment in product(range(9), ("faithful", "truncated_with_guard"),
            ("per_level", "single_wide_window", "two_stage_coarse_fine", "max_exponent_tree",
             "pairwise_difference_reuse", "exponent_sorted_realignment_lines")):
        yield "multi_term_fused_dot", dict(guard_bits_per_level=guard, rounding_contract=contract,
                                          alignment_strategy=alignment)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--stop", type=int)
    ap.add_argument("--vectors", type=int, default=64)
    ap.add_argument("--out")
    ap.add_argument("--full", action="store_true", help="every window width of 33..256, not the representative ones")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="chialu-dot-window-"))
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (family, pins) in enumerate(cases(args.full)):
        if index < args.start or (args.stop is not None and index >= args.stop):
            continue
        target = dot_family_requirements(family, pins)["spec"]
        # BF16's exponent range permits discarded terms even at window=256;
        # its narrow product also fits the smallest 33-bit window.
        target["modes"] = [dict(elements=4, format_ab="bf16", format_c="fp32", format_d="fp32")]
        target["flags"] = ["invalid", "overflow", "underflow", "inexact", "denormal"]
        try:
            result = check_seed(target, (family, pins), out / str(index), args.vectors, 83)
        except Exception as exc:
            result = {"pass": False, "phase": "generation", "detail": f"{type(exc).__name__}: {exc}"}
        row = dict(index=index, family=family, pins=pins, **result)
        rows.append(row)
        (out / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(json.dumps({k: v for k, v in row.items() if k != "fidelity"}), flush=True)
    passed = sum(row.get("pass") is True for row in rows)
    print(f"{'PASS' if passed == len(rows) else 'FAIL'} {passed}/{len(rows)} window contracts; {out}")
    return int(passed != len(rows))


if __name__ == "__main__":
    raise SystemExit(main())
