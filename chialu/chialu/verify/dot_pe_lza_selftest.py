"""PE anticipators act on product sums even with one PE and no C input."""
import argparse
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.dot import dot_family_requirements
from chialu.verify.dot_lza_selftest import cases as lza_cases
from chialu.verify.variant_selftest import check_seed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int)
    parser.add_argument("--out")
    parser.add_argument("--vectors", type=int, default=96)
    args = parser.parse_args()
    output = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="chialu-dot-pe-lza-"))
    output.mkdir(parents=True, exist_ok=True)
    family = "tensor_core_mixed_precision_mac"
    results = []
    cases = [(alignment, pins) for alignment in ("largest_exponent", "pairwise_sequential")
             for context, pins in lza_cases() if context == "classic_fma"]
    for index, (alignment, pins) in enumerate(cases):
        if index < args.start or args.stop is not None and index >= args.stop:
            continue
        pins = dict(pins, alignment_target=alignment, dot_width_per_pe=4)
        target = dot_family_requirements(family, pins)["spec"]
        target.update(accumulate=False, rounding=["RNE", "RTZ", "RDN", "RUP"],
                      flags=["invalid", "overflow", "underflow", "inexact", "denormal"])
        result = check_seed(target, (family, pins), output / str(index), args.vectors, 113)
        row = dict(index=index, pins=pins, **result)
        results.append(row)
        (output / "results.json").write_text(json.dumps(results, indent=2))
        print(index, "PASS" if result["pass"] else result, flush=True)
    passed = sum(row["pass"] is True for row in results)
    print(f"{'PASS' if passed == len(results) else 'FAIL'} {passed}/{len(results)} PE LZA; {output}")
    return int(passed != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
