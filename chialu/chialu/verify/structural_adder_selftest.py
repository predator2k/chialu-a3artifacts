"""Simulate complete pin domains at geometries that instantiate their selected structures."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import tempfile

from chialu.variant_contracts import family_schemas
from chialu.targets.rtl.families.alu_contracts import alu_family_requirements
from chialu.verify.alu_ref import normalize_spec
from chialu.verify.elaboration import elaborate
from chialu.verify.variant_selftest import check_seed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--vectors", type=int, default=32)
    parser.add_argument("--families", default="carry_lookahead,conditional_sum,fpga_carry_chain,manchester_carry_chain")
    args = parser.parse_args()
    out = Path(args.out or tempfile.mkdtemp(prefix="chialu-structural-adders-"))
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    for family in args.families.split(","):
        product, = family_schemas("adder", family)
        if product.slots:
            raise ValueError(f"{family}: this runner does not discharge nested component domains")
        for index in range(product.count):
            pins = product.at(index)
            width = alu_family_requirements("adder", family, pins)["minimum_width"]
            if family == "fpga_carry_chain" and pins["prefix_over_chain"]:
                width = max(width, pins["chain_segment_length"] + 1)
            cases.append((family, index, pins, width))
    report = {"scope": "complete own-pin products of the selected families at recorded effective geometries",
              "total": len(cases), "complete": False, "formal": "deferred", "cases": {}}
    def run(case):
        family, index, pins, width = case
        key = f"{family}/{index}"
        directory = out / key
        target = normalize_spec({"unit": "alu", "dut_name": "alu_core", "check_en": False,
                                 "modes": [{"format": f"int{width}", "count": 1}],
                                 "ops": ["add", "sub", "adc", "sbb"], "flags": ["carry", "overflow", "int_overflow"]})
        result = check_seed(target, {"core.adder.m0": (family, pins)}, directory, args.vectors, 29)
        instances = elaborate((directory / "seed.sv").read_text(), "alu_core", directory / "elaboration")
        if family == "carry_lookahead":
            levels = [instance["parameters"] for instance in instances if instance["module"] == "fam_adder_cla_level"]
            assert sorted(level["LEVELS"] for level in levels) == list(range(1, pins["levels"] + 1))
            assert all(level["N"] >= 2 for level in levels)
            assert all(level["INTER"] == {"ripple": 0, "lookahead": 1, "select": 2}[pins["intergroup_carry"]] for level in levels)
        if family == "fpga_carry_chain":
            if pins["prefix_over_chain"]:
                sizes = sorted(instance["parameters"]["W"] for instance in instances if instance["module"] == "fam_adder_ripple_carry")
            else:
                sizes = sorted(instance["parameters"]["W"] for instance in instances if instance["module"] == "fam_adder_ripple_chunk")
            segment = pins["chain_segment_length"]
            assert sizes == sorted(min(segment, width - lo) for lo in range(0, width, segment))
        if family == "conditional_sum":
            selected = next(instance for instance in instances if instance["module"] == "fam_adder_conditional_sum")
            assert selected["parameters"]["BASE"] == pins["base_block_width"]
            assert selected["parameters"]["RADIX"] == pins["selection_radix"]
            assert (width + pins["base_block_width"] - 1) // pins["base_block_width"] >= pins["selection_radix"]
        if family == "manchester_carry_chain":
            selected = next(instance for instance in instances if instance["module"] == "fam_adder_manchester_carry_chain")
            assert selected["parameters"]["SEG"] == pins["chain_segment_length"]
            assert selected["parameters"]["VARSKIP"] == int(pins["variable_skip"])
        return key, dict(pins=pins, width=width, **result, elaborated_instances=instances)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for future in as_completed([pool.submit(run, case) for case in cases]):
            key, result = future.result()
            report["cases"][key] = result
            (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            print(key, result["width"], "PASS" if result.get("pass") else result.get("detail"), flush=True)
    report["complete"] = len(report["cases"]) == len(cases) and all(case.get("pass") for case in report["cases"].values())
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    assert report["complete"], out
    print(f"PASS {len(cases)} complete structural adder bindings: {out}")


if __name__ == "__main__":
    main()
