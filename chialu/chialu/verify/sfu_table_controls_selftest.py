"""Check value-table seed controls over complete small input domains."""
import argparse
import json
from pathlib import Path
import tempfile

from chialu.verify.sfu_ref import FUNCTIONS, VECTOR_FNS, normalize_sfu_spec
from chialu.verify.variant_selftest import check_seed


def cases():
    scalar = [fn for fn in FUNCTIONS if fn != "none" and fn not in VECTOR_FNS]
    for family, compare in (("direct_lut", "gt"), ("compressed_lut", "ge")):
        yield family, "fp4e2m1", scalar, {"sr_compare": compare, "invalid_result": "zero"}, {}
        yield family, "fp8e5m2", ["exp2", "log2", "recip", "softplus"], {"sr_compare": compare}, {"sharing": "fully_shared_rom_evaluator"}
    yield "compressed_lut", "posit8_0", ["gelu", "silu"], {}, {"sharing": "shared_evaluator"}
    yield "direct_lut", "fps0e2m1N", ["sin", "cos", "log2"], {"invalid_result": "zero"}, {}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int)
    args = parser.parse_args(argv)
    directory = Path(args.out or tempfile.mkdtemp(prefix="chialu-sfu-table-controls-"))
    directory.mkdir(parents=True, exist_ok=True)
    results = []
    selected = list(enumerate(cases()))[args.start:args.stop]
    for index, (family, fmt, functions, options, pins) in selected:
        spec = normalize_sfu_spec({"unit": "vec_sfu", "dut_name": "sfu_core",
            "modes": [{"count": 1, "format": fmt}], "functions": functions,
            "rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "sr_bits": 1,
            "daz_in": [False, True], "ftz_out": [False, True],
            "flags": ["invalid", "div_zero", "overflow", "underflow", "inexact", "nan", "denormal"],
            "budget": {"max_ulp": 0}, "sfu_accuracy": {"mode": "report_error", "family": family}, **options})
        case = {"index": index, "family": family, "format": fmt, "functions": functions, "pins": pins, "options": options}
        try:
            result = check_seed(spec, (family, pins), directory / str(index), 4, 1)
            case.update(result)
        except (ValueError, AssertionError) as error:
            case.update({"pass": False, "detail": f"{type(error).__name__}: {error}"})
        results.append(case)
        print(json.dumps({key: case.get(key) for key in ("index", "family", "format", "pass", "algorithm_pass", "detail", "first_mismatches")}), flush=True)
        (directory / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0 if results and all(case.get("pass") and case.get("algorithm_pass") and case.get("error_range_complete") for case in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
