"""Bit-exact composition of a truncated multiplier with a Dot reduction.

All 60 algorithm-choice combinations are retained. Recursive approximate
arithmetic without an independent contract is reported as uncovered.
"""
import argparse
from itertools import product as cartesian
import json
from pathlib import Path
import re
import tempfile

from chialu.verify.truncated_multiplier_ref import product, SCHEMES, OUTPUT_ROUNDING, output_equivalence
from chialu.targets.rtl.families.dot import dot_family_requirements
from chialu.verify.variant_selftest import check_seed
from chialu.modules.common import FLAGS


def cases():
    for index, (columns, correction, rounding) in enumerate(cartesian(range(5), SCHEMES, OUTPUT_ROUNDING)):
        child = dict(extra_columns_kept=columns, correction_scheme=correction, output_rounding=rounding)
        if index % 3 == 0:
            child.update({"kept_tree.family": "csa_reduction_tree", "kept_tree.geometry": "dadda", "kept_tree.counter_kind": "3_2",
                          "kept_tree.cpa.family": "uniform", "kept_tree.cpa.adder.family": "parallel_prefix", "kept_tree.cpa.adder.topology": "brent_kung"})
            reduction = {"accum.family": "binary_tree", "accum.cpa.family": "parallel_prefix", "accum.cpa.topology": "brent_kung"}
        elif index % 3 == 1:
            child.update({"kept_tree.family": "compressor_4_2_tree", "kept_tree.compressor_kind": "stacking_6_3",
                          "kept_tree.cpa.family": "uniform", "kept_tree.cpa.adder.family": "ripple_carry", "kept_tree.cpa.adder.chunk_width_bits": 2})
            reduction = {"accum.family": "linear_chain"}
        else:
            child.update({"kept_tree.family": "tiled_cpa_reduction_tree", "kept_tree.adder_width": 2,
                          "kept_tree.carry_assimilation": "terminal_compressor", "kept_tree.terminal_reduction": "3_2_counter",
                          "kept_tree.tile_adder.family": "ripple_carry", "kept_tree.cpa.family": "uniform",
                          "kept_tree.cpa.adder.family": "parallel_prefix", "kept_tree.cpa.adder.topology": "sklansky"})
            reduction = {"accum.family": "csa_tree", "accum.compressor": "3:2", "accum.final_cpa.family": "ripple_carry"}
        yield index, child, {"mul.family": "truncated_fixed_width", **{"mul."+key: value for key, value in child.items()}, **reduction}


def leaf_case(child, signed, directory, vectors):
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.selftest import run_python_case
    from chialu.verify.family_ref import Adapter, Port
    from chialu.verify.family_tb import emit
    width = 7
    module = FAM.mul_module("truncated_fixed_width", child, width, signed)
    assert module is not None, child
    adapter = Adapter((Port("a", "input", width), Port("b", "input", width), Port("p", "output", 2*width)),
                      lambda row: {"p": product(width, signed, child, row["a"], row["b"])})
    result = run_python_case("", "signed" if signed else "unsigned", emit(module.name, module.params, adapter, vectors, 223), directory, module.text)
    assert result.endswith(": PASS"), result


def rejection_checks(output):
    from chialu.targets.derive import seed_for, verify_files
    from chialu.eda import conformance
    _, _, pins = next(cases())
    target = dot_family_requirements("pairwise_tree", pins)["spec"]
    exact = dict(target, dot_contract="fused")
    try:
        seed_for(exact, family=("pairwise_tree", pins))
    except ValueError as error:
        assert "architecture contract" in str(error), error
    else:
        raise AssertionError("a truncated child silently retained the fused mathematical contract")
    small = dict(target, modes=[dict(target["modes"][0], format_ab="fp4e2m1")])
    too_wide = dict(pins, **{"mul.extra_columns_kept": 4})
    small["dot_architecture"] = {"family": "pairwise_tree", "pins": too_wide}
    try:
        seed_for(small, family=("pairwise_tree", too_wide))
    except ValueError as error:
        assert "extra_columns_kept" in str(error), error
    else:
        raise AssertionError("k=4 silently became a two-column construction")
    missing = dict(pins, **{"mul.kept_tree.cpa.adder.family": "approximate_truncated"})
    uncovered = dict(target, dot_architecture={"family": "pairwise_tree", "pins": missing})
    try:
        verify_files(uncovered, output / "uncovered")
    except ValueError as error:
        assert "uncovered component contract" in str(error), error
    else:
        raise AssertionError("an unmodeled approximate CPA received an exact-sum oracle")
    target.update(n_random=96, seed=227, budget={"max_abs": 0})
    result = check_seed(target, ("pairwise_tree", pins), output / "zero_budget", 96, 227)
    assert result["algorithm_pass"] is True and result["budget_pass"] is False and result["pass"] is False, result
    target["budget"] = {"max_abs": 1e12}
    source = seed_for(target, family=("pairwise_tree", pins))
    source = re.sub(r"\bmodule\s+dot_core\b", "module original_dot", str(source), count=1)
    from chialu.verify.dot_ref import dot_layout
    ports = dot_layout(target)
    declarations = [f"{'input' if port.direction == 'in' else 'output'} wire [{port.width-1}:0] {port.name}" for port in ports["core_in"]+ports["core_out"]]
    conns = [f".{port.name}({('original_d' if port.name == 'd' else port.name)})" for port in ports["core_in"]+ports["core_out"]]
    source += "\nmodule dot_core("+", ".join(declarations)+");\n"
    source += f"wire [{ports['d_w']-1}:0] original_d; original_dot dut({', '.join(conns)}); assign d=original_d ^ 1'b1; endmodule\n"
    result = conformance(source, verify_files(target, output / "mutation"))
    assert result["algorithm_pass"] is False and result["pass"] is False, result


def zero_sign_checks(output):
    """Approximation zero and true cancellation have different IEEE signs."""
    from chialu.targets.derive import seed_for
    from chialu.verify import dot_ref as D
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.tb_gen import write_hex
    from chialu.targets.rtl.families.selftest import run_case
    for raw in (False, True):
        index = 3 if raw else 48
        _, _, pins = list(cases())[index]
        target = dot_family_requirements("pairwise_tree", pins)["spec"]
        if raw:
            target["modes"][0].update(format_ab="int7", format_c="int10", format_d="fp16")
        target.update(rounding=["RNE", "RDN"], flags=list(FLAGS))
        layout = D.dot_layout(target)
        ports = tuple(Port(port.name, "input" if port.direction == "in" else "output", port.width)
                      for port in layout["core_in"]+layout["core_out"])
        inputs = tuple(port for port in ports if port.direction == "input")
        outputs = tuple(port for port in ports if port.direction == "output")
        rows = [dict(a=0, b=127 | (127 << 7), c=768, rounding_sel=i) if raw else
                dict(a=1, b=1, c=0, rounding_sel=i) for i in range(2)]
        expected = []
        for index, row in enumerate(rows):
            ctrl = D.vector_ctrl(target, {"rounding": target["rounding"][index]})
            result = D.dot_outputs(target, layout, 0, row["a"], row["b"], row["c"], ctrl, [0])
            assert result["d"] == (0x8000 if raw and index == 1 else 0), (raw, index, result)
            expected.append(pack_ports(result, outputs))
        source = str(seed_for(target, family=("pairwise_tree", pins)))
        label = "zero_raw" if raw else "zero_truncated"
        def run(label, source):
            directory = output / label
            directory.mkdir(parents=True, exist_ok=True)
            write_hex(directory / "vectors.hex", [pack_ports({port.name: row.get(port.name, 0) for port in inputs}, inputs) for row in rows], sum(port.width for port in inputs))
            write_hex(directory / "expected.hex", expected, sum(port.width for port in outputs))
            return run_case("", label, emit_text("dot_core", {}, ports, len(rows)), output, source)
        assert run(label, source).endswith(": PASS")
        field = "products_negative" if raw else "product_nonzero"
        changed, count = re.subn(r"assign " + field + r" = [^;]+;", "assign " + field + " = 1'b1;", source)
        assert count == 1
        rejected = run(label+"_mutant", changed)
        assert "FAIL" in rejected and not rejected.endswith(": PASS"), rejected
    print("PASS actual-product zero/sign classification and two sensitized mutations")


def activity_checks(output):
    """Find numerical witnesses and check all 60 physical child circuits."""
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.tb_gen import write_hex
    width = 7
    witnesses, points = [], {(0, 0), (127, 127)}
    comparisons = []
    for keep, rounding in cartesian(range(5), OUTPUT_ROUNDING):
        for scheme, previous in (("constant", "none"), ("data_dependent", "none"), ("variable_mmse", "data_dependent")):
            left = dict(extra_columns_kept=keep, correction_scheme=previous, output_rounding=rounding)
            comparisons.append((left, dict(left, correction_scheme=scheme)))
    for keep, scheme in cartesian(range(5), SCHEMES):
        left = dict(extra_columns_kept=keep, correction_scheme=scheme, output_rounding="truncate")
        for rounding in OUTPUT_ROUNDING[1:]:
            right = dict(left, output_rounding=rounding)
            if not output_equivalence(right):
                comparisons.append((left, right))
    for left, right in comparisons:
        found = next(((a, b) for a, b in cartesian(range(1 << width), repeat=2)
                      if product(width, False, left, a, b) != product(width, False, right, a, b)), None)
        assert found is not None, (left, right, "target did not activate this algorithm choice")
        points.add(found)
        witnesses.append(dict(left=left, right=right, a=found[0], b=found[1]))
    selections = list(cases())
    ports = (Port("a", "input", width), Port("b", "input", width),
             *(Port(f"p{index}", "output", 2*width) for index, _, _ in selections))
    source = "module activity_dut("+", ".join(f"{port.direction} wire [{port.width-1}:0] {port.name}" for port in ports)+");\n"
    modules = {}
    for index, child, _ in selections:
        module = FAM.mul_module("truncated_fixed_width", child, width, False)
        assert module is not None
        source += f"{module.name} u{index}(.a(a), .b(b), .p(p{index}));\n"
        modules.update(FAM.module_texts(module.name, module.text))
    source += "endmodule\n"+"\n".join(modules.values())
    directory = output / "activity"
    directory.mkdir(parents=True, exist_ok=True)
    vectors = [dict(a=a, b=b) for a, b in sorted(points)]
    expected = [{f"p{index}": product(width, False, child, row["a"], row["b"]) for index, child, _ in selections} for row in vectors]
    write_hex(directory / "vectors.hex", [pack_ports(row, ports[:2]) for row in vectors], 2*width)
    write_hex(directory / "expected.hex", [pack_ports(row, ports[2:]) for row in expected], 2*width*len(selections))
    (directory / "witnesses.json").write_text(json.dumps(witnesses, indent=2))
    result = run_case("", "activity", emit_text("activity_dut", {}, ports, len(vectors)), output, source)
    assert result.endswith(": PASS"), result
    print(f"PASS {len(witnesses)} algorithm-choice witnesses across 60 child circuits; k=0 RN/truncate equivalence retained")


def extra_contexts(output, vectors):
    from chialu.verify.dot_ref import normalize_dot_spec
    _, _, pins = list(cases())[59]
    for fmt in ("int7", "uint7", "fxs1i2f4"):
        fd = "fxs1i7f8" if fmt.startswith("fxs") else "int16"
        target = normalize_dot_spec(dict(unit="vec_dot_acc", dut_name="dot_core", modes=[dict(elements=2,
            format_ab=fmt, format_c=fmt, format_d=fd)], dot_contract="architecture",
            dot_architecture={"family": "pairwise_tree", "pins": pins}, flags=list(FLAGS)))
        result = check_seed(target, ("pairwise_tree", pins), output / fmt, vectors, 233)
        assert result["algorithm_pass"] is True and result["pass"] is True, result
        print(fmt, "PASS raw child sign and fixed-point scaling", flush=True)
    pins = dict(pins, per_level_truncation=True)
    target = dot_family_requirements("pairwise_tree", pins)["spec"]
    target.update(rounding=["RNE", "RTZ", "RDN", "RUP", "SR"], sr_bits=2, flags=list(FLAGS))
    result = check_seed(target, ("pairwise_tree", pins), output / "per_level", vectors, 239)
    assert result["algorithm_pass"] is True and result["pass"] is True, result
    print("PASS approximate products composed with per-level windows", flush=True)
    target = normalize_dot_spec(dict(unit="vec_dot_acc", dut_name="dot_core", modes=[dict(elements=2,
        format_ab="fps1e2m0N", format_c="fps1e2m0N", format_d="fps1e2m0N")], dot_contract="architecture",
        dot_architecture={"family": "streaming_accurate_accumulator", "pins": {"window_bits": 33}},
        rounding=["RNE", "RTZ", "RDN", "RUP", "SR"], sr_bits=2, flags=list(FLAGS)))
    result = check_seed(target, ("streaming_accurate_accumulator", {"window_bits": 33}), output / "signed_exp_only", vectors, 241)
    assert result["algorithm_pass"] is True and result["pass"] is True, result
    print("PASS signed exponent-only stored-sign regression", flush=True)
    from adir.instance import _bind_variables
    from chialu.verify.dot_binding_selftest import bindings_for
    from chialu.modules import generators
    architecture = {"family": "pairwise_tree", "pins": {"mul.family": "truncated_fixed_width"}}
    instance, specifications = bindings_for(architecture)
    specifications["modes"] = {"fixed": {"elements": 2, "format_ab": "fps1e2m6", "format_c": "fp16", "format_d": "fp16"}}
    _bind_variables(instance, specifications)
    target = generators.spec_of(instance.ctx())
    assert target["dot_architecture"]["pins"]["mul.extra_columns_kept"] == 2
    assert target["dot_architecture"]["pins"]["mul.correction_scheme"] == "constant"
    selected = generators.core_family_of(instance.ctx())
    result = check_seed(target, selected, output / "adir", vectors, 251)
    assert result["algorithm_pass"] is True and result["pass"] is True, result
    print("PASS ADIR frozen child algorithm defaults and real seed", flush=True)


def one_bit_checks(output):
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.selftest import run_python_case
    from chialu.verify.family_ref import Adapter, Port
    from chialu.verify.family_tb import emit
    from chialu.verify.dot_ref import normalize_dot_spec
    for kept, scheme, signed in cartesian((0, 1), SCHEMES, (False, True)):
        child = dict(extra_columns_kept=kept, correction_scheme=scheme, output_rounding="force_lsb_one_jamming")
        module = FAM.mul_module("truncated_fixed_width", child, 1, signed)
        assert module is not None
        assert "full[1:2]" not in module.text
        adapter = Adapter((Port("a", "input", 1), Port("b", "input", 1), Port("p", "output", 2)),
                          lambda row: {"p": product(1, signed, child, row["a"], row["b"])})
        result = run_python_case("", f"w1_{kept}_{scheme}_{signed}", emit(module.name, module.params, adapter, 4, 257), output, module.text)
        assert result.endswith(": PASS"), result
    pins = {"mul.family": "truncated_fixed_width", "mul.extra_columns_kept": 0,
            "mul.correction_scheme": "none", "mul.output_rounding": "force_lsb_one_jamming"}
    target = normalize_dot_spec(dict(unit="vec_dot_acc", dut_name="dot_core", modes=[dict(elements=2,
        format_ab="fps1e2m0N", format_c="fps1e2m0N", format_d="fps1e2m0N")], dot_contract="architecture",
        dot_architecture={"family": "pairwise_tree", "pins": pins}, rounding=["RNE", "RTZ", "RDN", "RUP", "SR"],
        sr_bits=2, flags=list(FLAGS)))
    result = check_seed(target, ("pairwise_tree", pins), output / "w1_dot", 96, 263)
    assert result["algorithm_pass"] is True and result["pass"] is True, result
    print("PASS 16 one-bit native jam cases and signed M=0 Dot composition", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=60)
    parser.add_argument("--vectors", type=int, default=96)
    parser.add_argument("--out")
    parser.add_argument("--skip-leaves", action="store_true")
    parser.add_argument("--checks", action="store_true")
    parser.add_argument("--activity", action="store_true")
    parser.add_argument("--extra-contexts", action="store_true")
    parser.add_argument("--one-bit", action="store_true")
    args = parser.parse_args(argv)
    output = Path(args.out or tempfile.mkdtemp(prefix="chialu-dot-component-"))
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for index, child, pins in cases():
        if not args.start <= index < args.stop:
            continue
        if not args.skip_leaves:
            for signed in (False, True):
                leaf_case(child, signed, output / str(index) / "leaf", args.vectors)
        target = dot_family_requirements("pairwise_tree", pins)["spec"]
        target.update(rounding=["RNE", "RTZ", "RDN", "RUP", "SR"], sr_bits=2,
                      daz_in=[False, True], ftz_out=[False, True],
                      flags=list(FLAGS))
        result = check_seed(target, ("pairwise_tree", pins), output / str(index) / "dot", args.vectors, 229)
        assert result["algorithm_pass"] is True and result["pass"] is True, result
        effects = [effect for effect in result["fidelity"]["effects"] if effect["pin"] == "extra_columns_kept"]
        assert len(effects) == 2 and all(effect["effective"] == child["extra_columns_kept"] and effect["geometry"]["width"] == 7 for effect in effects), effects
        if index % 12 == 0:
            from chialu.verify.elaboration import elaborate
            source = (output / str(index) / "dot" / "seed.sv").read_text()
            instances = elaborate(source, "dot_core", output / str(index) / "elaborated")
            multipliers = [row for row in instances if row["module"].startswith("fam_mul_truncated_fixed_width")]
            assert len(multipliers) == 2 and all(row["ports"]["a"]["width"] == 7 and row["ports"]["p"]["width"] == 14 for row in multipliers), multipliers
        results.append(dict(index=index, pins=pins, algebraic_equivalence=output_equivalence(child), **result))
        (output / "results.json").write_text(json.dumps(results, indent=2))
        print(index, child["extra_columns_kept"], child["correction_scheme"], child["output_rounding"], "PASS algorithm; max_abs", result["mathematical_metrics"]["max_abs"], flush=True)
    if args.checks:
        rejection_checks(output)
        zero_sign_checks(output)
        print("PASS fused/width/uncovered-contract rejections and independent algorithm/budget gates")
    if args.activity:
        activity_checks(output)
    if args.extra_contexts:
        extra_contexts(output, args.vectors)
    if args.one_bit:
        one_bit_checks(output)
    print(f"PASS {len(results)} composed Dot cases; {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
