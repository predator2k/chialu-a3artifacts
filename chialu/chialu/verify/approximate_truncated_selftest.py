"""Simulate every legal own-pin binding with an independent algorithm contract."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import tempfile

from chialu.active_variants import ActiveProduct
from chialu.variant_contracts import family_schemas
from chialu.variants import FamilyProduct
from chialu.verify.approximate_adder_algorithm import TruncatedAdder


def check(width, pins, index, root):
    from chialu.targets.rtl.families import adder_ext
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.tb_gen import write_hex
    contract = TruncatedAdder.from_pins(width, pins)
    k = contract.lower_width
    name = f"truncated_{index}"
    source = adder_ext.approximate_truncated_sv(width, pins, name)
    assert f"logic [{k-1}:0] al" in source and f"the upper {width-k} bits exact" in source
    if contract.scheme == "speculative_segments":
        window = contract.window
        assert f"al[{k-1}:{k-window}]" in source
    if contract.correction:
        assert "the correction stage through the incrementer" in source
    mask, low_mask = (1 << width) - 1, (1 << k) - 1
    values = sorted({0, 1, mask, mask - 1, low_mask, low_mask - 1, 1 << k, 1 << (k - 1), mask ^ low_mask})
    vectors = [dict(a=a, b=b, cin=cin) for a in values for b in values for cin in (0, 1)]
    rng = random.Random(181 + index)
    vectors += [dict(a=rng.getrandbits(width), b=rng.getrandbits(width), cin=rng.getrandbits(1)) for _ in range(96)]
    ports = [Port("a", "input", width), Port("b", "input", width), Port("cin", "input", 1),
             Port("s", "output", width), Port("cout", "output", 1)]
    expected = [contract.evaluate(**vector) for vector in vectors]
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    write_hex(directory / "vectors.hex", [pack_ports(v, ports[:3]) for v in vectors], 2 * width + 1)
    write_hex(directory / "expected.hex", [pack_ports(v, ports[3:]) for v in expected], width + 1)
    status = run_case("", name, emit_text(name, {}, ports, len(vectors)), root, source)
    assert status.endswith(": PASS"), status
    errors = [(result["s"] + (result["cout"] << width)) - sum(vector.values()) for vector, result in zip(vectors, expected)]
    return {"index": index, "width": width, "pins": pins, "pass": True, "vectors": len(vectors), "detail": status,
            "algorithm": "independent integer lower-scheme/carry contract with exact child assumptions",
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "sample_mathematical_error": {"min": min(errors), "max": max(errors), "complete_range": False}}


def main(argv=None):
    from chialu.targets.rtl.families.adder_ext import approximate_truncated_sv
    from chialu.variant_legality import own_reason
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-approximate-truncated-"))
    root.mkdir(parents=True, exist_ok=True)
    schema, = family_schemas("adder", "approximate_truncated")
    own = ActiveProduct(FamilyProduct(schema.name, schema.axes, ()), {})
    width = max(axis.at(axis.count - 1) for axis in schema.axes if axis.name == "lower_part_width") + 8
    results, excluded = [], []
    for index in range(own.count):
        pins = own.at(index)
        if pins.get("speculation_window", 0) > pins["lower_part_width"]:
            try:
                approximate_truncated_sv(width, pins, "invalid_window")
            except ValueError as error:
                assert "does not fit" in str(error), error
                reason = own_reason(schema.name, pins, width)
                assert reason is not None
                excluded.append({"index": index, "pins": pins, "reason": reason, "generation_error": str(error)})
                continue
            raise AssertionError("oversized speculation window was silently clipped")
        result = check(width, pins, index, root)
        results.append(result)
        print(json.dumps(result), flush=True)
        (root / "report.json").write_text(json.dumps({"scope": "own pins only, exact default child; not complete ALU composition",
            "active_own_count": own.count, "width": width, "passed": results, "geometry_excluded": excluded}, indent=2) + "\n")
    for invalid_width in (4, 16, 32):
        try:
            approximate_truncated_sv(invalid_width, {"lower_part_width": 32}, "invalid_lower")
        except ValueError:
            pass
        else:
            raise AssertionError("lower part was silently clipped")
    print(f"PASS {len(results)} own-pin bindings; {len(excluded)} rejected oversized windows; width={width}; {root}")


if __name__ == "__main__":
    main()
