"""Native truncated multipliers: exact algorithm and separate numerical budget.

Algorithm conformance is required for every canonical point. A point that
exceeds its existing mathematical tolerance remains a failed candidate;
the integration test checks that this failure is reported independently.
"""
import argparse
import hashlib
from dataclasses import asdict, replace
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import re
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families.alu_contracts import alu_family_requirements
from chialu.targets.rtl.families.mul_ext import truncated_sv
from chialu.targets.rtl.families.selftest import run_python_case, run_case
from chialu.verify.dot_component_selftest import cases
from chialu.verify.elaboration import elaborate
from chialu.verify.family_ref import golden, no_golden_reason, NO_GOLDEN
from chialu.verify.family_tb import emit
from chialu.verify.truncated_multiplier_ref import SCHEMES, OUTPUT_ROUNDING, calibration_units


def _words(path):
    lines = path.read_text().split()
    assert lines and all(re.fullmatch(r"[0-9a-fA-F]+", word) for word in lines), path
    return [int(word, 16) for word in lines]


def _budget(expected, actual, width, signed, tolerance, corners):
    def value(word):
        return word-(1 << (2*width)) if signed and word >> (2*width-1) else word
    errors = [abs(value(got)-value(want)) for want, got in zip(expected, actual)]
    maximum = Fraction(max(errors), tolerance.scale)
    mean = Fraction(sum(errors[corners:]), (len(errors)-corners)*tolerance.scale)
    passed = maximum <= Fraction(str(tolerance.max_err)) and mean <= Fraction(str(tolerance.mean_err))
    return passed, dict(max_abs=max(errors), mean_abs=float(mean*tolerance.scale),
                        max_scaled=str(maximum), mean_scaled=str(mean), samples=len(actual))


def check(width, signed, pins, directory, vectors):
    bound = dict(pins, _signed=signed)
    adapter = golden("multiplier", "truncated_fixed_width", bound, width)
    assert adapter is not None and adapter.algorithm is not None and adapter.tolerance is not None
    module = FAM.mul_module("truncated_fixed_width", pins, width, signed)
    assert module is not None, pins
    bench = emit(module.name, module.params, adapter, vectors, 269)
    status = run_python_case("", directory.name, bench, directory.parent, module.text)
    actual = _words(directory / "actual.hex")
    algorithm = _words(directory / "algorithm.hex")
    expected = _words(directory / "expected.hex")
    assert len(actual) == len(algorithm) == len(expected)
    assert actual == algorithm, status
    budget_pass, metrics = _budget(expected, actual, width, signed, adapter.tolerance, len(adapter.stimulus(0, 269)))
    assert status.endswith(": PASS") == budget_pass, (status, budget_pass, metrics)
    if not budget_pass:
        assert "BOUND" in status or "MEAN" in status, status
    result = dict(width=width, signed=signed, pins=pins, algorithm_pass=True,
                  budget_pass=budget_pass, pass_both=budget_pass, pass_candidate=budget_pass,
                  tolerance=asdict(adapter.tolerance), mathematical_metrics=metrics, detail=status)
    result.update(source_sha256=hashlib.sha256(module.text.encode()).hexdigest(),
                  mathematical_expected_sha256=hashlib.sha256((directory / "expected.hex").read_bytes()).hexdigest(),
                  algorithm_expected_sha256=hashlib.sha256((directory / "algorithm.hex").read_bytes()).hexdigest())
    (directory / "result.json").write_text(json.dumps(result, indent=2))
    return result


def rejected(callback, text):
    try:
        callback()
    except ValueError as error:
        assert text in str(error), error
    else:
        raise AssertionError(f"invalid native point accepted: {text}")


def checks(root):
    pins = dict(extra_columns_kept=4, correction_scheme="constant", output_rounding="truncate")
    rejected(lambda: truncated_sv(0, False, {}, "bad_width"), "width")
    rejected(lambda: truncated_sv(2, False, pins, "bad_geometry"), "extra_columns_kept=4")
    assert FAM.mul_module("truncated_fixed_width", pins, 2, False) is None
    rejected(lambda: golden("multiplier", "truncated_fixed_width", pins, 2), "extra_columns_kept=4")
    for invalid in (-1, 5, True, 1.5, "not-an-integer"):
        rejected(lambda: truncated_sv(7, False, dict(pins, extra_columns_kept=invalid), "bad_pin"), "extra_columns_kept")
    # Omitted values retain the width-dependent native default; explicit
    # values are never silently clipped to make a small target compile.
    assert FAM.mul_module("truncated_fixed_width", {}, 1, False) is not None
    for keep in range(5):
        for scheme in SCHEMES:
            geometry = alu_family_requirements("multiplier", "truncated_fixed_width", dict(extra_columns_kept=keep, correction_scheme=scheme))
            assert geometry["minimum_width"] >= max(2, keep)
            if scheme in ("constant", "variable_mmse"):
                assert geometry["minimum_width"] >= keep+3
    for supplied in ({"correction": "none"}, {"kept_tree.cpa.adder.family": "approximate_truncated"},
                     {"kept_tree.cpa.adder.family": "end_around_carry"}):
        reason = no_golden_reason("multiplier", "truncated_fixed_width", supplied, 7)
        assert reason in NO_GOLDEN.values() and golden("multiplier", "truncated_fixed_width", supplied, 7) is None
    adapter = golden("multiplier", "truncated_fixed_width", dict(pins, _signed=False), 7)
    assert adapter.expect(dict(a=8, b=15)) == {"p": 120}
    assert adapter.algorithm_expect(dict(a=8, b=15)) == {"p": 128}
    mutable = dict(pins, _signed=False)
    frozen = golden("multiplier", "truncated_fixed_width", mutable, 7)
    mutable["correction_scheme"] = "none"
    assert frozen.algorithm_expect(dict(a=8, b=15)) == {"p": 128}
    # A correct algorithm cannot pass an impossible numerical budget.
    adapter.tolerance = replace(adapter.tolerance, max_err=0, mean_err=0)
    module = FAM.mul_module("truncated_fixed_width", pins, 7, False)
    status = run_python_case("", "tight", emit(module.name, {}, adapter, 1500, 271), root, module.text)
    assert not status.endswith(": PASS") and ("BOUND" in status or "MEAN" in status), status
    assert _words(root / "tight" / "actual.hex") == _words(root / "tight" / "algorithm.hex")
    # A wrong algorithm cannot pass a permissive numerical budget.
    adapter.tolerance = replace(adapter.tolerance, max_err=1e12, mean_err=1e12)
    source = module.text + f"\nmodule corrupt(input [6:0] a,b,output [13:0] p); wire [13:0] correct; " \
             f"{module.name} original(.a(a),.b(b),.p(correct)); assign p=correct ^ 14'd1; endmodule\n"
    status = run_python_case("", "corrupt", emit("corrupt", {}, adapter, 1500, 271), root, source)
    assert not status.endswith(": PASS") and "ALGORITHM" in status, status
    bench = emit(module.name, {}, adapter, 1500, 271)
    bench.write(root / "missing_algorithm")
    (root / "missing_algorithm" / "algorithm.hex").write_text("")
    status = run_case("", "missing_algorithm", bench, root, module.text)
    assert not status.endswith(": PASS") and "ALGORITHM" in status, status
    print("PASS native geometry, uncovered contracts, exact-vs-algorithm data, and independent budget/algorithm gates", flush=True)


def budget_literals(root):
    from chialu.verify.family_ref import Adapter, Port, Tolerance
    for bits in (32, 64):
        step = 1 << bits
        width = bits+1
        ports = (Port("a", "input", width), Port("p", "output", width))
        adapter = Adapter(ports, lambda row: {"p": row["a"]}, Tolerance(1, 1, ("p",), scale=step),
                          domains={"a": step}, algorithm=lambda row, step=step: {"p": row["a"]+step})
        name = f"scale_{bits}"
        source = f"module {name}(input [{width-1}:0] a,output [{width-1}:0] p); assign p=a+{width}'d{step}; endmodule\n"
        result = run_python_case("", name, emit(name, {}, adapter, 1500, 277), root, source)
        assert result.endswith(": PASS"), result
    ports = (Port("a", "input", 1), Port("p", "output", 1))
    adapter = Adapter(ports, lambda row: {"p": 1}, Tolerance(0, 0, ("p",), relative=True, minimum=1 << 200),
                      algorithm=lambda row: {"p": 1})
    source = "module minimum_limit(input a,output p); assign p=1'b1; endmodule\n"
    result = run_python_case("", "minimum_limit", emit("minimum_limit", {}, adapter, 1500, 277), root, source)
    assert not result.endswith(": PASS") and "measured=0" in result, result
    adapter = Adapter(ports, lambda row: {"p": 0}, Tolerance(0, 0, ("p",), slack=1 << 200),
                      algorithm=lambda row: {"p": 1})
    source = "module slack_limit(input a,output p); assign p=1'b1; endmodule\n"
    result = run_python_case("", "slack_limit", emit("slack_limit", {}, adapter, 1500, 277), root, source)
    assert result.endswith(": PASS"), result
    print("PASS 32/64-bit budget scales and 201-bit minimum/slack limits", flush=True)


def half_boundaries(root, vectors):
    results = []
    for first, signed in product((49, 50, 51, 52, 53, 55, 59), (False, True)):
        width = first+2
        pins = dict(extra_columns_kept=2, correction_scheme="constant", output_rounding="truncate")
        directory = root / f"half_{first}_{int(signed)}"
        result = check(width, signed, pins, directory, vectors)
        expected_units = round(Fraction((first-1)*(1 << first)+1, 4*(1 << first)))
        match = re.search(r"correction_constant_units=(\d+); first_kept_column=(\d+)", (directory / "lib.sv").read_text())
        assert match and int(match[1]) == expected_units and int(match[2]) == first, (first, match)
        result.update(first_kept_column=first, calibration_units=expected_units,
                      independent_mean=str(Fraction((first-1)*(1 << first)+1, 4*(1 << first))))
        (directory / "result.json").write_text(json.dumps(result, indent=2))
        results.append(dict(index=directory.name, **result))
        print(width, signed, "PASS half-boundary constant", expected_units, "budget", result["budget_pass"], flush=True)
    # Both operands carry a real FP64 hidden bit. There are no partial
    # products below column 51 and the kept units end in binary 11, so
    # units 12 -> 13 crosses the retained 2**53 output boundary.
    from chialu.targets.derive import seed_for
    from chialu.verify import dot_ref as D
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.tb_gen import write_hex
    a_sig, b_sig = (1 << 52)+(1 << 50), (1 << 52)+6
    assert a_sig >> 52 == b_sig >> 52 == 1
    assert ((a_sig*b_sig) >> 51) & 3 == 3
    assert ((a_sig & -a_sig).bit_length()-1) + ((b_sig & -b_sig).bit_length()-1) == 51
    pins = {"mul.family": "truncated_fixed_width", "mul.extra_columns_kept": 2,
            "mul.correction_scheme": "constant", "mul.output_rounding": "truncate", "per_level_truncation": True}
    target = D.normalize_dot_spec(dict(unit="vec_dot_acc", dut_name="dot_core", modes=[dict(elements=2,
        format_ab="fp64", format_c="fp64", format_d="fp64")], dot_contract="architecture",
        dot_architecture={"family": "pairwise_tree", "pins": pins},
        flags=["invalid", "overflow", "underflow", "inexact", "denormal"]))
    a, b = (1023 << 52) | (1 << 50), (1023 << 52) | 6
    layout = D.dot_layout(target)
    wanted = D.dot_outputs(target, layout, 0, a, b, 0, {"rounding": "RNE"}, [0])
    assert wanted == {"d": 0x3ff400000000000e, "flags": 8}, wanted
    ports = tuple(Port(port.name, "input" if port.direction == "in" else "output", port.width)
                  for port in layout["core_in"]+layout["core_out"])
    inputs = tuple(port for port in ports if port.direction == "input")
    outputs = tuple(port for port in ports if port.direction == "output")
    directory = root / "fp64_normal_significands"
    directory.mkdir(parents=True, exist_ok=True)
    write_hex(directory / "vectors.hex", [pack_ports(dict(a=a, b=b, c=0), inputs)], sum(port.width for port in inputs))
    write_hex(directory / "expected.hex", [pack_ports(wanted, outputs)], sum(port.width for port in outputs))
    source = str(seed_for(target, family=("pairwise_tree", pins)))
    status = run_case("", directory.name, emit_text("dot_core", {}, ports, 1), root, source)
    assert status.endswith(": PASS"), status
    (directory / "result.json").write_text(json.dumps(dict(pass_algorithm=True, a=hex(a), b=hex(b),
        a_significand=a_sig, b_significand=b_sig, expected_d=hex(wanted["d"]), expected_flags=wanted["flags"],
        first_kept_column=51, correction_units=13, source_sha256=hashlib.sha256(source.encode()).hexdigest(), detail=status), indent=2))
    print("PASS FP64 normal-significand units12->13 witness, result 0x3ff400000000000e", flush=True)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=60)
    parser.add_argument("--vectors", type=int, default=1500)
    parser.add_argument("--one-bit", action="store_true")
    parser.add_argument("--checks", action="store_true")
    parser.add_argument("--wide", action="store_true")
    parser.add_argument("--half-boundaries", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-native-truncated-"))
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for index, pins, _ in cases():
        if not args.start <= index < args.stop:
            continue
        for signed in (False, True):
            result = check(7, signed, pins, root / f"{index}_{int(signed)}", args.vectors)
            results.append(dict(index=index, **result))
            (root / "report.json").write_text(json.dumps(results, indent=2))
            print(index, signed, "algorithm PASS; mathematical budget", result["budget_pass"], flush=True)
    if args.one_bit:
        for index, (kept, scheme, rounding, signed) in enumerate(product((0, 1), SCHEMES, OUTPUT_ROUNDING, (False, True))):
            pins = dict(extra_columns_kept=kept, correction_scheme=scheme, output_rounding=rounding)
            result = check(1, signed, pins, root / f"w1_{index}", args.vectors)
            results.append(dict(index=f"w1_{index}", **result))
            if scheme == "none" and kept == 0:
                module = FAM.mul_module("truncated_fixed_width", pins, 1, signed)
                hierarchy = elaborate(module.text, module.name, root / f"w1_{index}" / "elaborated")
                selected = [row for row in hierarchy if row["module"] == module.name]
                assert selected and all(row["ports"]["a"]["width"] == 1 and row["ports"]["b"]["width"] == 1 and row["ports"]["p"]["width"] == 2 for row in selected), selected
            (root / "report.json").write_text(json.dumps(results, indent=2))
        print("PASS 48 W1 canonical algorithm points and actual 1/1/2-bit ports", flush=True)
    if args.checks:
        checks(root)
        budget_literals(root)
    if args.wide:
        for width, kept, signed in product((16, 32, 64), (0, 4), (False, True)):
            pins = dict(extra_columns_kept=kept, correction_scheme="variable_mmse", output_rounding="truncate",
                        **{"kept_tree.family": "csa_reduction_tree", "kept_tree.cpa.family": "uniform",
                           "kept_tree.cpa.adder.family": "parallel_prefix", "kept_tree.cpa.adder.topology": "brent_kung"})
            directory = root / f"wide_{width}_{kept}_{int(signed)}"
            result = check(width, signed, pins, directory, args.vectors)
            source = (directory / "lib.sv").read_text()
            constant = re.search(r"correction_constant_units=(\d+); first_kept_column=(\d+)", source)
            assert constant and int(constant[2]) == width-kept, source[:300]
            assert int(constant[1]) == calibration_units(width, width-kept), (width, kept, constant[1])
            result.update(calibration_units=int(constant[1]), independent_calibration="exact Fraction residual over 4096 seed-1 pairs")
            results.append(dict(index=directory.name, **result))
            (root / "report.json").write_text(json.dumps(results, indent=2))
            print(width, kept, signed, "PASS algorithm and calibration; budget", result["budget_pass"], flush=True)
    if args.half_boundaries:
        results.extend(half_boundaries(root, args.vectors))
        (root / "report.json").write_text(json.dumps(results, indent=2))
    budget_failures = sum(not row["budget_pass"] for row in results)
    print(f"PASS integration: {len(results)} exact algorithms; {budget_failures} mathematical-budget failures retained; {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
