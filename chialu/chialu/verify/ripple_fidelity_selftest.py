"""Simulate every ripple-carry binding on its minimum target for complete size coverage."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import tempfile

from chialu.variant_contracts import family_schemas
from chialu.verify.alu_ref import normalize_spec
from chialu.verify.variant_selftest import check_seed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--vectors", type=int, default=64)
    args = parser.parse_args()
    out = Path(args.out or tempfile.mkdtemp(prefix="chialu-ripple-fidelity-"))
    out.mkdir(parents=True, exist_ok=True)
    product, = family_schemas("adder", "ripple_carry")
    sizes = next(axis for axis in product.axes if axis.name == "chunk_width_bits")
    width = max(sizes.at(index) for index in range(sizes.count))
    target = normalize_spec({"unit": "alu", "dut_name": "alu_core", "check_en": False,
                             "modes": [{"format": f"int{width}", "count": 1}],
                             "ops": ["add", "sub", "adc", "sbb", "neg", "abs", "add_sat", "sub_sat"],
                             "flags": ["carry", "overflow", "int_overflow"]})
    selections = [{"core.adder.m0": (product.name, product.at(index))} for index in range(product.count)]
    from chialu.targets.rtl.alu_seed import alu_seed
    for choice in selections:
        generated = alu_seed(target, families=choice)
        effect = next(effect for effect in generated.fidelity["effects"] if effect["pin"] == "chunk_width_bits")
        assert effect["geometry"]["width"] == width and effect["requested"] == effect["effective"]
    smaller = dict(target, modes=[{"format": f"int{width-1}", "count": 1}])
    try:
        alu_seed(smaller, families={"core.adder.m0": (product.name, {"chunk_width_bits": width})})
    except ValueError:
        pass
    else:
        raise AssertionError("a target narrower than the maximum chunk was admitted")
    report = {"family": product.name, "schema": product.fingerprint, "total": product.count,
              "target": target, "minimum_width": width,
              "minimum_reason": "The declared largest chunk requires at least this width, and every declared binding fits it.",
              "scope": "all own pins of ripple_carry at this integer ALU geometry; no nested slots",
              "formal": "deferred", "cases": {}}
    def run(index):
        directory = out / str(index)
        result = check_seed(target, selections[index], directory, args.vectors, 23)
        from chialu.verify.elaboration import elaborate
        instances = elaborate((directory / "seed.sv").read_text(), "alu_core", directory / "elaboration")
        chunks = [instance for instance in instances if instance["module"] == "fam_adder_ripple_chunk"]
        size = product.at(index)["chunk_width_bits"]
        expected = sorted([min(size, width - lo) for lo in range(0, width, size)])
        actual = sorted(instance["parameters"].get("W") for instance in chunks)
        assert actual == expected, (index, actual, expected)
        forms = {"generate_propagate": 0, "two_half_adders_or": 1, "xor_majority": 2, "half_sum_mux_carry": 3}
        requested_form = forms[product.at(index)["full_adder_logic"]]
        assert all(instance["parameters"].get("FORM") == requested_form for instance in chunks)
        assert all(instance["ports"]["a"]["width"] == instance["parameters"]["W"] for instance in chunks)
        result["elaborated_chunk_widths"] = actual
        result["fidelity_status"] = "pass"
        return index, result
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for future in as_completed([pool.submit(run, index) for index in range(product.count)]):
            index, result = future.result()
            report["cases"][str(index)] = dict(pins=product.at(index), **result)
            (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            print(index, "PASS" if result.get("pass") else result.get("detail"), flush=True)
    report["complete"] = len(report["cases"]) == product.count and all(case.get("pass") and case.get("fidelity_status") == "pass"
                                                                     for case in report["cases"].values())
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    assert report["complete"], out
    print(f"PASS {product.count} complete bindings; minimum target width {width}: {out}")


if __name__ == "__main__":
    main()
