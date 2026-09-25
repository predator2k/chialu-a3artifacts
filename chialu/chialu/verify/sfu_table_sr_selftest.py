"""Simulate every stochastic-word width at table decision boundaries."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import tempfile


def check(case):
    from chialu.targets.rtl.engine import FLAG_ORDER, FW
    from chialu.targets.rtl.families.sfu_control_table import _record, controlled_table
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.elaboration import hierarchy_of_files
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.formats import parse_format
    from chialu.verify.sfu_ref import normalize_sfu_spec, sfu_layout, sfu_expected
    from chialu.verify.tb_gen import write_hex
    family, compare, width, root = case
    spec = normalize_sfu_spec({"unit": "vec_sfu", "modes": [{"count": 1, "format": "fp4e2m1"}],
        "functions": ["exp2"], "rounding": ["SR"], "sr_bits": width, "sr_compare": compare,
        "flags": list(FLAG_ORDER), "daz_in": [False, True], "ftz_out": [False, True]})
    fmt, layout = parse_format("fp4e2m1"), sfu_layout(spec)
    module = controlled_table(["exp2"], fmt, (family, {}), spec)
    tag = f"{family}_{compare}_{width}"
    directory = Path(root) / tag
    directory.mkdir(parents=True, exist_ok=True)
    ports = [Port("x", "input", 4), Port("rnd", "input", 3), Port("daz", "input", 1),
             Port("ftz", "input", 1), Port("word", "input", width), Port("y", "output", 4), Port("flags", "output", FW)]
    inputs = [port for port in ports if port.direction == "input"]
    outputs = [port for port in ports if port.direction == "output"]
    vectors, expected = [], []
    for bits in range(16):
        # Generated boundaries select test inputs only. The expected results
        # come from the independent mathematical SFU reference.
        record = _record("exp2", fmt, bits, spec, 2 * max(128, 16 + width + 64))
        cuts = [(record >> (7 * (4 + FW) + i * (width + 1))) & ((1 << (width + 1)) - 1) for i in range(2)]
        words = {0, (1 << width) - 1, 1 << (width - 1)}
        words.update(word for cut in cuts for word in (cut - 1, cut, cut + 1) if 0 <= word < 1 << width)
        for daz in (False, True):
            for ftz in (False, True):
                for word in sorted(words):
                    vector = {"x": bits, "rnd": 4, "daz": int(daz), "ftz": int(ftz), "word": word}
                    y, flags = sfu_expected(spec, layout, 0, 0, bits,
                                           {"rounding": "SR", "daz_in": daz, "ftz_out": ftz}, [word], [])
                    vectors.append(pack_ports(vector, inputs))
                    expected.append(pack_ports({"y": y, "flags": flags}, outputs))
    write_hex(directory / "vectors.hex", vectors, sum(port.width for port in inputs))
    write_hex(directory / "expected.hex", expected, 4 + FW)
    bench = emit_text(module.name, {}, ports, len(vectors))
    verdict = run_case("", tag, bench, Path(root), module.text)
    instances = (hierarchy_of_files(["tb.sv", "lib.sv"], directory, "tb")
                 if (directory / "tb.sv").exists() else [])
    actual = [instance for instance in instances if instance["module"] == module.name]
    faithful = len(actual) == 1 and actual[0]["ports"]["word"]["width"] == width
    result = {"family": family, "sr_compare": compare, "sr_bits": width, "vectors": len(vectors),
              "pass": verdict.endswith(": PASS") and faithful, "simulation": verdict, "word_port_fidelity": faithful,
              "source_sha256": hashlib.sha256(module.text.encode()).hexdigest(),
              "vectors_sha256": hashlib.sha256((directory / "vectors.hex").read_bytes()).hexdigest(),
              "expected_sha256": hashlib.sha256((directory / "expected.hex").read_bytes()).hexdigest()}
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--widths", default=",".join(str(width) for width in range(1, 33)))
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-sfu-table-sr-"))
    root.mkdir(parents=True, exist_ok=True)
    widths = list(map(int, args.widths.split(",")))
    if args.jobs < 1 or any(not 1 <= width <= 32 for width in widths):
        parser.error("jobs must be positive and stochastic widths must be in 1..32")
    cases = [(family, compare, width, str(root)) for family in ("direct_lut", "compressed_lut")
             for compare in ("gt", "ge") for width in widths]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(check, cases):
            results.append(result)
            print(json.dumps({key: result[key] for key in ("family", "sr_compare", "sr_bits", "vectors", "pass")}), flush=True)
            (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0 if results and all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
