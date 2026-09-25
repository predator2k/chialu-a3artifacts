"""Simulation witnesses for effective Dot reduction and bounded-alignment choices."""
import argparse
from itertools import product
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.dot import dot_family_requirements
from chialu.targets.derive import seed_for
from chialu.verify.variant_selftest import check_seed


LZA = {"lza.family": "lza", "lza.correction_scheme": "compensation_in_rounding",
       "lza.string_form": "dual_pos_neg_strings", "lza.split_string_select": "maximum_count",
       "lza.zero_result_detect": "operand_function_or"}


def cases():
    for sign, contract in product(("post_add_complement", "dual_reduction_positive_pair_select"),
                                  ("correctly_rounded", "faithful", "truncated_with_guard")):
        pins = dict(LZA, alignment_strategy="per_level", sign_handling=sign, rounding_contract=contract,
                    **{"reduction.family": "binary_tree"})
        if sign == "post_add_complement":
            pins["cancellation_handling"] = "detect_and_bypass_smallest_operand"
        if contract != "correctly_rounded":
            pins["guard_bits_per_level"] = 0
        yield "multi_term_fused_dot", pins, False
    for family, bound in product(("pairwise_tree", "integer_mac", "kulisch_long_accumulator"), range(2, 9)):
        pins = dict(LZA, **{"align.family": "bounded_align", "align.bound": bound})
        if family != "pairwise_tree":
            pins["accumulator_width_bits"] = 16 if family == "integer_mac" else 64
        yield family, pins, False
    for raw, organization, carry in product((False, True), ("segmented_lazy_carry", "banked_sub_adders", "two_speed"),
                                            ("immediate", "carry_save_deferred")):
        yield "kulisch_long_accumulator", dict(LZA, accumulator_width_bits=64,
                                               organization=organization, carry_resolution=carry), raw
    for alignment in ("full_align", "bounded_align"):
        pins = dict(LZA, accumulator_width_bits=16, accumulation_mode="sum_apart", **{"align.family": alignment})
        if alignment == "bounded_align":
            pins["align.bound"] = 8
        yield "integer_mac", pins, False


def reject_inactive():
    for family, own in (("bf16_fma_datapath", {}), ("fp8_training_datapath", {"accumulate_precision": "fp16"}),
                         ("pairwise_tree", {})):
        pins = dict(own, **{"align.family": "bounded_align", "align.bound": 8})
        spec = dot_family_requirements(family, pins)["spec"]
        if family == "pairwise_tree":
            spec["modes"][0]["format_c"] = "fp4e2m1"
        try:
            seed_for(spec, family=(family, pins))
        except ValueError as error:
            assert "align.bound" in str(error), error
        else:
            raise AssertionError(f"{family}: ineffective guard was accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int)
    parser.add_argument("--out")
    parser.add_argument("--vectors", type=int, default=96)
    args = parser.parse_args()
    output = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="chialu-dot-structural-"))
    output.mkdir(parents=True, exist_ok=True)
    reject_inactive()
    results = []
    for index, (family, pins, raw) in enumerate(cases()):
        if index < args.start or args.stop is not None and index >= args.stop:
            continue
        spec = dot_family_requirements(family, pins)["spec"]
        spec.update(rounding=["RNE", "RTZ", "RDN", "RUP"],
                    flags=["invalid", "overflow", "underflow", "inexact", "denormal"])
        if raw:
            spec["modes"][0].update(format_ab="int8", format_c="int8")
        result = check_seed(spec, (family, pins), output / str(index), args.vectors, 163)
        row = dict(index=index, family=family, pins=pins, raw=raw, **result)
        results.append(row)
        (output / "results.json").write_text(json.dumps(results, indent=2))
        print(index, family, "PASS" if result["pass"] else result, flush=True)
    passed = sum(row["pass"] is True for row in results)
    print(f"{'PASS' if passed == len(results) else 'FAIL'} {passed}/{len(results)} structural cases, 3 inactive rejections; {output}")
    return int(passed != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
