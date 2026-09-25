"""Custom float Dot seeds under every rounding/DAZ/FTZ control combination.

The same independently computed Python outputs and complete flags validate
the pairwise product tree and flattened partial-product CSA construction.
"""
import argparse
from itertools import product
import json
from pathlib import Path
import random
import tempfile

from chialu.modules.common import FLAGS
from chialu.verify.dot_fidelity_selftest import check_vectors, spec
from chialu.verify.formats import parse_format
from chialu.verify.rounding import ROUNDINGS


FORMATS = ("fps1e2m0", "fps1e2m0N", "fps1e2m0I", "fps0e2m1", "fps0e2m1NI",
           "fps1e2m1I", "fps0e2m1I")
SELECTIONS = (("pairwise_tree", {"accum.family": "binary_tree"}),
              ("fused_csa", {"compressor": "3:2"}),
              ("fused_csa", {"compressor": "4:2"}),
              ("pairwise_tree", {"accum.family": "csa_tree", "accum.compressor": "7:3"}))


def stimulus(format_name, n_random=96):
    """Exercise every operand encoding and all control combinations.

    Encoding pairs cover the first multiply; the second term and C include
    cancellation, finite extremes, specials, and independent random words.
    All stochastic words are used whenever SR is selected.
    """
    fmt = parse_format(format_name)
    limit = 1 << fmt.width
    rng = random.Random(181)
    operands = []
    for a, b in product(range(limit), repeat=2):
        operands.append((a | (rng.randrange(limit) << fmt.width),
                         b | (rng.randrange(limit) << fmt.width), rng.randrange(limit)))
    for bits in range(limit):
        other = bits ^ (1 << (fmt.width-1)) if fmt.signed else 0
        operands.append((bits | (other << fmt.width), fmt.round(1) * (1+limit), 0))
        operands.append((bits * (1+limit), bits * (1+limit), bits))
    operands.extend((rng.randrange(limit*limit), rng.randrange(limit*limit), rng.randrange(limit))
                    for _ in range(n_random))
    vectors = []
    for rounding_index, rounding in enumerate(ROUNDINGS):
        for daz, ftz, word in product(range(2), range(2), range(4) if rounding == "SR" else (0,)):
            vectors.extend(dict(a=a, b=b, c=c, rounding_sel=rounding_index,
                                daz_in_sel=daz, ftz_out_sel=ftz, sr_rnd=word) for a, b, c in operands)
    return vectors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formats", default=",".join(FORMATS))
    parser.add_argument("--destination", help="use a distinct output format, including unsigned invalid conversions")
    parser.add_argument("--invalid-result", choices=("saturate", "zero"), default="saturate")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int)
    parser.add_argument("--vectors", type=int, default=96)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    output = Path(args.out or tempfile.mkdtemp(prefix="chialu-dot-custom-format-"))
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for format_index, format_name in enumerate(args.formats.split(",")):
        vectors = stimulus(format_name, args.vectors)
        destination = args.destination or format_name
        target = spec(format_name, format_name, destination, 2, rounding=list(ROUNDINGS), sr_bits=2,
                      daz_in=[False, True], ftz_out=[False, True], flags=list(FLAGS), invalid_result=args.invalid_result)
        controls = {(vector["rounding_sel"], vector["daz_in_sel"], vector["ftz_out_sel"], vector["sr_rnd"])
                    for vector in vectors}
        required = {(i, daz, ftz, word) for i, rounding in enumerate(ROUNDINGS)
                    for daz, ftz, word in product(range(2), range(2), range(4) if rounding == "SR" else (0,))}
        assert controls == required
        for selection_index, selection in enumerate(SELECTIONS):
            index = len(SELECTIONS)*format_index+selection_index
            if index < args.start or args.stop is not None and index >= args.stop:
                continue
            directory = output / str(index)
            try:
                result = check_vectors(target, selection, vectors, directory)
            except (ValueError, AssertionError) as error:
                result = {"pass": False, "phase": "generation", "detail": f"{type(error).__name__}: {error}"}
            row = dict(index=index, format=format_name, destination=destination, invalid_result=args.invalid_result,
                       family=selection[0], pins=selection[1],
                       rounding=list(ROUNDINGS), flags=list(FLAGS), control_combinations=len(controls), **result)
            results.append(row)
            (output / "results.json").write_text(json.dumps(results, indent=2)+"\n")
            print(index, format_name, selection, row["pass"], row.get("detail"), flush=True)
    passed = sum(row["pass"] is True for row in results)
    print(f"{'PASS' if passed == len(results) else 'FAIL'} {passed}/{len(results)} custom-format cases; {output}")
    return int(passed != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
