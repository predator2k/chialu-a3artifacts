"""Simulate each real digit-recurrence choice against an independent integer contract."""
from __future__ import annotations

import argparse
from copy import deepcopy
from fractions import Fraction
import itertools
import json
from pathlib import Path
import tempfile

from chialu.verify.digit_recurrence_ref import DigitRecurrenceContract


def check_mathematical_enclosures():
    import mpmath
    from fractions import Fraction
    from chialu.verify.digit_recurrence_ref import mathematical_bounds
    with mpmath.workprec(256):
        for core in ("exp2c", "log2c"):
            for value in range(256):
                x = mpmath.mpf(value) / 256
                truth = mpmath.power(2, x) if core == "exp2c" else mpmath.log(mpmath.mpf(3) / 4 + x, 2)
                sign, mantissa, exponent, _ = truth._mpf_
                exact_working_value = Fraction(int(mantissa)) * Fraction(2) ** int(exponent) * (-1 if sign else 1)
                low, high = mathematical_bounds(core, value, 8, 32)
                if not low <= exact_working_value <= high:
                    raise AssertionError((core, value, "rational mathematical enclosure failed direct high-precision check"))


def check_exp_startup_rules():
    """Legacy replay, mandatory startup, selector geometry and all-width proof."""
    from chialu.targets.rtl.families import sfu as SF
    from chialu.verify.digit_recurrence_ref import logarithm_constant
    required = SF.sfu_requirements('digit_recurrence_exp_log',
                                  {'radix': 16, 'selection': 'rounding_of_scaled_residual',
                                   'termination': 'linear_extrapolation'})
    assert required['minimum_significand_bits'] == 4, 'core Fo=7 includes three engine guard bits'
    def build(fraction, selection="table_lookup", termination="iterate_to_full_precision", radix=16,
              digits="signed_redundant", advance="sequential", normalization="multiplicative"):
        net = SF.Net("exp_startup_rule", "versioned exponential startup")
        SF.DigitRecEngine("digit_recurrence_exp_log", dict(radix=radix, digit_set=digits, selection=selection, termination=termination,
                                                        index_advance=advance, normalization=normalization))(
            net, SF.core_of("exp2c"), net.port_in("u", 8), 8, fraction, "exp2c")
        return net.algorithm_contracts[-1]
    modern = build(8)
    reference = DigitRecurrenceContract(modern)
    legacy = {key: value for key, value in modern.items() if key not in (
        "initial_range_convention", "bootstrap_indices", "startup_table_through_index", "main_stages",
        "sequential_indices", "initial_product", "state_signals", "residual_signals")}
    legacy["stages"] -= 1
    old = DigitRecurrenceContract(legacy)
    witnesses = {0: 256, 127: 361, 128: 362, 134: 367, 255: 396}
    if any(old.evaluate(value) != result for value, result in witnesses.items()):
        raise AssertionError("historical manifests no longer reproduce the legacy exp result")
    if old.convergence_certificate()["complete"] or reference.evaluate(255) != 510:
        raise AssertionError("the known upper-half convergence failure was not corrected")
    for damaged in (dict(modern, bootstrap_indices=[]), dict(modern, sequential_indices=list(range(1, 6))),
                    dict(modern, startup_table_through_index=0), dict(modern, initial_product="one")):
        try:
            DigitRecurrenceContract(damaged)
        except ValueError:
            pass
        else:
            raise AssertionError("the independent contract accepted a damaged exp startup schedule")
    for output_fraction in (0, 1, 2):
        try:
            build(output_fraction, "rounding_of_scaled_residual")
        except ValueError as exc:
            if "three main indices" not in str(exc):
                raise
        else:
            raise AssertionError("rounded selection silently became an all-table recurrence")
    DigitRecurrenceContract(build(3, "rounding_of_scaled_residual"))
    for output_fraction, selection in itertools.product(range(3, 7), ("table_lookup", "rounding_of_scaled_residual")):
        try:
            build(output_fraction, selection, "linear_extrapolation")
        except ValueError as exc:
            if "identically zero tail" not in str(exc):
                raise
        else:
            raise AssertionError("a static zero tail was accepted as an active linear termination")
    DigitRecurrenceContract(build(7, "rounding_of_scaled_residual", "linear_extrapolation"))
    count = zero_tail_geometries = zero_tail_rejections = 0
    for fraction, radix, signed, lookup, linear in itertools.product(range(6, 81), (2, 4, 16), (False, True), (False, True), (False, True)):
        rb = radix.bit_length() - 1
        full = (fraction + rb - 1) // rb
        main = (full + 1) // 2 + 1 if linear else full
        if not lookup and main < 3:
            continue
        alpha = max(1, radix // 2) if signed else radix - 1
        digits = range(-alpha if signed else 0, alpha + 1)
        bootstrap = int(signed and radix == 16)
        data = dict(modern, radix=radix, output_fraction_bits=fraction - 6, working_fraction_bits=fraction,
                    input_width=128, input_fraction_bits=128, domain_hi_exclusive=1 << 128,
                    digit_set="signed_redundant" if signed else "nonredundant", digit_min=digits.start, digit_max=alpha,
                    selection="table_lookup" if lookup else "rounding_of_scaled_residual",
                    termination="linear_extrapolation" if linear else "iterate_to_full_precision",
                    main_stages=main, stages=main + bootstrap, bootstrap_indices=[1] if bootstrap else [],
                    sequential_indices=([1] if bootstrap else []) + list(range(1, main + 1)),
                    initial_product="upper_half_two_lower_half_one" if signed else "one",
                    ln2=logarithm_constant(Fraction(2), fraction + 2),
                    inv_ln2=logarithm_constant(Fraction(2), fraction + 2, reciprocal=True),
                    log_factors=[[logarithm_constant(Fraction(1) + Fraction(d, radix ** i), fraction) for d in digits]
                                 for i in range(1, main + 1)])
        for key in ("state_signals", "residual_signals"):
            data.pop(key, None)
        contract = DigitRecurrenceContract(data)
        if not contract.convergence_certificate()["complete"] or not contract.analytic_error_enclosure()["complete"]:
            raise AssertionError("all-input core bound became a sampled result")
        if linear and main == full and contract.convergence_certificate()["stages"][-1]["output_interval"] == [0, 0]:
            zero_tail_geometries += 1
            for advance, normalization in itertools.product(("sequential", "leading_bit_skip"), ("multiplicative", "additive")):
                try:
                    build(fraction - 6, data["selection"], data["termination"], radix, data["digit_set"], advance, normalization)
                except ValueError as exc:
                    if "identically zero tail" not in str(exc):
                        raise
                    zero_tail_rejections += 1
                else:
                    raise AssertionError("a proved inactive termination geometry generated")
        count += 1
    return {"interval_geometries": count, "zero_tail_geometries": zero_tail_geometries,
            "zero_tail_generation_rejections": zero_tail_rejections, "working_fraction_range": [6, 80], "inputs_per_geometry": str(1 << 128),
            "input_words_enumerated": 0, "legacy_upper_half_result": 396, "new_upper_half_result": 510}


def check_log_startup_rules():
    from chialu.targets.rtl.families import sfu as SF
    from chialu.verify.digit_recurrence_ref import logarithm_constant
    def build(fo, radix=16, digits="signed_redundant", selection="table_lookup", term="iterate_to_full_precision",
              advance="sequential", normalization="multiplicative"):
        net = SF.Net("log_startup_rule", "versioned logarithm startup")
        SF.DigitRecEngine("digit_recurrence_exp_log", dict(radix=radix, digit_set=digits, selection=selection,
            termination=term, index_advance=advance, normalization=normalization))(
            net, SF.core_of("log2c"), net.port_in("u", 8), 8, fo, "log2c")
        return net.algorithm_contracts[-1]
    modern = build(8)
    current = DigitRecurrenceContract(modern)
    legacy = {key: value for key, value in modern.items() if key not in (
        "initial_range_convention", "bootstrap_indices", "startup_table_through_index", "main_stages",
        "sequential_indices", "initial_product", "state_signals", "residual_signals", "accumulator_signals")}
    legacy["stages"] -= 1
    old = DigitRecurrenceContract(legacy)
    for value, result in {0: -107, 64: 0, 128: 82, 160: 117, 166: 126, 177: 134, 191: 148}.items():
        if old.evaluate(value) != result:
            raise AssertionError("legacy logarithm manifest replay changed")
    if old.convergence_certificate()["complete"] or current.evaluate(166) != 123:
        raise AssertionError("known signed radix16 logarithm convergence failure persists")
    for damaged in (dict(modern, bootstrap_indices=[]), dict(modern, initial_product="one"),
                    dict(modern, startup_table_through_index=0), dict(modern, sequential_indices=list(range(1, 6)))):
        try:
            DigitRecurrenceContract(damaged)
        except ValueError:
            pass
        else:
            raise AssertionError("independent log reference accepted a damaged startup convention")
    rejected = 0
    for fo, digits, term, advance, normalization in itertools.product(range(3), ("nonredundant", "signed_redundant"),
            ("iterate_to_full_precision", "linear_extrapolation"), ("sequential", "leading_bit_skip"), ("multiplicative", "additive")):
        try:
            build(fo, 16, digits, "rounding_of_scaled_residual", term, advance, normalization)
        except ValueError as exc:
            if "three main indices" not in str(exc):
                raise
            rejected += 1
        else:
            raise AssertionError("log rounded selector silently became all-table")
    witnesses = 0
    for digits, selection, advance, normalization in itertools.product(("nonredundant", "signed_redundant"),
            ("table_lookup", "rounding_of_scaled_residual"), ("sequential", "leading_bit_skip"), ("multiplicative", "additive")):
        manifest = build(3, 16, digits, selection, "linear_extrapolation", advance, normalization)
        witness = manifest["termination_activity_witness"]
        execution = DigitRecurrenceContract(manifest).log_execution(witness["input"])
        if not witness["terminal_centered_state"] or execution["residuals"][-1] != witness["terminal_centered_state"]:
            raise AssertionError("log linear tail has no independently confirmed activity witness")
        witnesses += 1
    count = 0
    for fraction, radix, signed, lookup, linear in itertools.product(range(6, 81), (2, 4, 16), (False, True), (False, True), (False, True)):
        rb = radix.bit_length() - 1
        full = (fraction + rb - 1) // rb
        main = (full + 1) // 2 + 1 if linear else full
        if not lookup and main < 3:
            continue
        alpha = max(1, radix // 2) if signed else radix - 1
        digits = range(-alpha if signed else 0, alpha + 1)
        bootstrap = int(signed and radix == 16)
        data = dict(modern, radix=radix, output_fraction_bits=fraction - 6, working_fraction_bits=fraction,
                    input_width=128, input_fraction_bits=128, domain_hi_exclusive=3 << 126,
                    digit_set="signed_redundant" if signed else "nonredundant", digit_min=digits.start, digit_max=alpha,
                    selection="table_lookup" if lookup else "rounding_of_scaled_residual",
                    termination="linear_extrapolation" if linear else "iterate_to_full_precision",
                    main_stages=main, stages=main + bootstrap, bootstrap_indices=[1] if bootstrap else [],
                    sequential_indices=([1] if bootstrap else []) + list(range(1, main + 1)),
                    initial_product="centered_significand" if signed else "centered_significand_fold_above_one",
                    ln2=logarithm_constant(Fraction(2), fraction + 2),
                    inv_ln2=logarithm_constant(Fraction(2), fraction + 2, reciprocal=True),
                    log_factors=[[logarithm_constant(Fraction(1) + Fraction(d, radix ** i), fraction, base2=True) for d in digits]
                                 for i in range(1, main + 1)])
        for key in ("state_signals", "residual_signals", "accumulator_signals"):
            data.pop(key, None)
        contract = DigitRecurrenceContract(data)
        if not contract.convergence_certificate()["complete"] or not contract.analytic_error_enclosure()["complete"] or not contract.log_skip_certificate()["complete"]:
            raise AssertionError("log all-input proof was replaced with a sampled result")
        count += 1
    return dict(interval_geometries=count, leading_zero_threshold_cell_certificates=count, working_fraction_range=[6, 80], inputs_per_geometry=str(3 << 126),
                input_words_enumerated=0, inactive_rounded_generation_rejections=rejected,
                same_length_linear_activity_witnesses=witnesses, legacy_witness_result=126, new_witness_result=123)


def check_skip_entry(directory, selections=("table_lookup", "rounding_of_scaled_residual"), digit_set="nonredundant",
                     normalization="multiplicative", index_advance="leading_bit_skip"):
    """Full family entry equivalence; the independent golden claim is the core test.

    This confirms validation accepts only the implemented subset and that
    actual range/reconstruction paths retain the selected skip core.
    """
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.targets.rtl.engine import Conventions, Engine
    from chialu.verify.formats import parse_format
    fmt = parse_format("fp8e4m3")
    geometry = SF.Geom.of_engine(Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions()))
    pins = dict(radix=2, digit_set=digit_set, selection=selections[0], index_advance=index_advance, normalization=normalization)
    invalid = [dict(pins, **{key: value}) for key, value in (("radix", 8), ("selection", "unknown"),
               ("state_domain", "complex_bkm"), ("normalization", "unknown"))]
    for rejected in invalid:
        try:
            SF.sfu_sv("exp2", fmt, geometry, "digit_recurrence_exp_log", rejected)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unimplemented leading-bit combination {rejected} silently generated")
    results = []
    for fn, term, radix, selection in itertools.product(("exp2", "exp", "log2", "log"),
                                     ("iterate_to_full_precision", "linear_extrapolation"), (2, 4, 16), selections):
        selected = dict(pins, termination=term, radix=radix, selection=selection)
        name, text, net = SF.sfu_sv(fn, fmt, geometry, "digit_recurrence_exp_log", selected)
        baseline_name, baseline_text, _ = SF.sfu_sv(fn, fmt, geometry, "digit_recurrence_exp_log",
                                                  dict(selected, index_advance="sequential", normalization="multiplicative"))
        if not net.algorithm_contracts or any(c.get("index_advance") != index_advance or c["digit_set"] != digit_set
                                             or c["selection"] != selection or c["normalization"] != normalization for c in net.algorithm_contracts):
            raise AssertionError("family entry substituted a different recurrence core")
        width = geometry.XT
        lines = [f"module tb; logic [{width-1}:0] x,y,baseline; logic inv,dz,binv,bdz; integer errors;",
                 f"{name} dut(.x(x),.y(y),.inv(inv),.dz(dz));",
                 f"{baseline_name} seq(.x(x),.y(baseline),.inv(binv),.dz(bdz)); initial begin errors=0;"]
        for bits in range(1 << fmt.width):
            argument = SF.x_of_bits(fmt, bits, geometry)
            lines.append(f"x={width}'d{argument}; #1; if (y !== baseline || inv !== binv || dz !== bdz) "
                         f'begin errors=errors+1; $display("FAIL bits={bits} y=%h sequential=%h",y,baseline); end')
        lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
        status = run_case("", name, "\n".join(lines), directory, text + "\n" + baseline_text)
        results.append({"function": fn, "termination": term, "radix": radix, "selection": selection, "digit_set": digit_set,
                        "normalization": normalization, "index_advance": index_advance,
                        "pass": status.endswith(": PASS"), "detail": status,
                        "vectors": 1 << fmt.width, "scope": "family entry coordinate/schedule RTL equivalence with exact primitives; not independent whole-seed golden"})
        print(status, flush=True)
    (directory / "entry-equivalence.json").write_text(json.dumps(results, indent=2) + "\n")
    if not all(result["pass"] for result in results):
        raise AssertionError("family entry skip equivalence failed")
    return results


def one_case(core, radix, digit_set, selection, termination, directory, fraction=8, output_fraction=8, error_bounds=False,
             index_advance="sequential", normalization="multiplicative"):
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    pins = dict(radix=radix, digit_set=digit_set, selection=selection, termination=termination, index_advance=index_advance,
                normalization=normalization)
    name = f"digit_{core}_r{radix}_{digit_set}_{selection}_{termination}_f{output_fraction}"
    if index_advance != "sequential":
        name += "_skip"
    if normalization != "multiplicative":
        name += "_additive"
    net = SF.Net(name, "real digit-recurrence contract fixture")
    argument = net.port_in("u", fraction)
    result = SF.DigitRecEngine("digit_recurrence_exp_log", pins)(
        net, SF.core_of(core), argument, fraction, output_fraction, core)
    net.port_out("y", result)
    definition = net.algorithm_contracts[-1]
    reference = DigitRecurrenceContract(definition)
    versioned = reference.convergent_start or reference.log_start
    input_values = range(definition["domain_lo"], definition["domain_hi_exclusive"]) if reference.log_start else range(1 << fraction)
    for i, (signal, width, signed) in enumerate(zip(definition["digit_signals"], definition["digit_widths"], definition["digit_signed"])):
        net.port_out(f"d{i}", SF.Ref(signal, width, signed))
    for i, (signal, width) in enumerate(zip(definition["index_signals"], definition["index_widths"])):
        net.port_out(f"idx{i}", SF.Ref(signal, width, False))
    for i, (signal, width) in enumerate(zip(definition["shift_signals"], definition["shift_widths"])):
        net.port_out(f"sh{i}", SF.Ref(signal, width, False))
    for i, (signal, width, signed) in enumerate(zip(definition["state_signals"], definition["state_widths"], definition["state_signed"])):
        net.port_out(f"q{i}", SF.Ref(signal, width, signed))
    for i, (signal, width, signed) in enumerate(zip(definition.get("residual_signals", []), definition.get("residual_widths", []), definition.get("residual_signed", []))):
        net.port_out(f"r{i}", SF.Ref(signal, width, signed))
    for i, (signal, width, signed) in enumerate(zip(definition.get("accumulator_signals", []), definition.get("accumulator_widths", []), definition.get("accumulator_signed", []))):
        net.port_out(f"probe_acc_{i}", SF.Ref(signal, width, signed))
    if "initial_halve_signal" in definition:
        net.port_out("halve", SF.Ref(definition["initial_halve_signal"], definition["initial_halve_width"], False))
    if "initial_upper_signal" in definition:
        net.port_out("upper", SF.Ref(definition["initial_upper_signal"], definition["initial_upper_width"], False))
    if "termination_activity_witness" in definition:
        witness = definition["termination_activity_witness"]
        if reference.log_execution(witness["input"])["residuals"][-1] != witness["terminal_centered_state"] or not witness["terminal_centered_state"]:
            raise AssertionError("the generator's log tail activity witness is false")
    certificate = reference.convergence_certificate() if versioned else None
    lines = [f"module tb; logic [{fraction-1}:0] u; logic [{result.w-1}:0] y;"]
    lines += [f"logic [{width-1}:0] d{i};" for i, width in enumerate(definition["digit_widths"])]
    lines += [f"logic [{width-1}:0] idx{i};" for i, width in enumerate(definition["index_widths"])]
    lines += [f"logic [{width-1}:0] sh{i};" for i, width in enumerate(definition["shift_widths"])]
    lines += [f"logic [{width-1}:0] q{i};" for i, width in enumerate(definition["state_widths"])]
    lines += [f"logic [{width-1}:0] r{i};" for i, width in enumerate(definition.get("residual_widths", []))]
    lines += [f"logic [{width-1}:0] probe_acc_{i};" for i, width in enumerate(definition.get("accumulator_widths", []))]
    if "initial_halve_signal" in definition:
        lines.append("logic halve;")
    if "initial_upper_signal" in definition:
        lines.append("logic upper;")
    conns = ", ".join([".u(u)", ".y(y)"] + [f".d{i}(d{i})" for i in range(reference.stages)] +
                      [f".idx{i}(idx{i})" for i in range(len(definition["index_signals"]))] +
                      [f".sh{i}(sh{i})" for i in range(len(definition["shift_signals"]))] +
                      [f".q{i}(q{i})" for i in range(len(definition["state_signals"]))] +
                      [f".r{i}(r{i})" for i in range(len(definition.get("residual_signals", [])))] +
                      [f".probe_acc_{i}(probe_acc_{i})" for i in range(len(definition.get("accumulator_signals", [])))] +
                      ([".halve(halve)"] if "initial_halve_signal" in definition else []) +
                      ([".upper(upper)"] if "initial_upper_signal" in definition else []))
    lines += [f"{name} dut({conns}); integer errors; initial begin errors=0;"]
    observed = [set() for _ in range(reference.stages)]
    observed_indices = [set() for _ in definition["index_signals"]]
    skipped_count = 0
    zero_factor_digits = 0
    odd_midpoint_floor_hits = 0
    initial_states = set()
    tail_residuals = set()
    rounded_active = 0
    if normalization == "additive":
        normal_coordinates = DigitRecurrenceContract(dict(definition, normalization="multiplicative", state_origin="one_centered_value"))
        products = definition["correction_products"]
        expressions = {event[2].name: event[3] for event in net.events if event[0] == "wire"}
        if len(products) != reference.stages:
            raise AssertionError("the additive recurrence does not have one digit correction per stage")
        for stage, product in enumerate(products):
            if product["state"] != definition["state_signals"][stage]:
                raise AssertionError("an additive multiplier bypasses the stored delta")
            expression = expressions.get(product["product"], "")
            if not expression.startswith(product["state"] + " * "):
                raise AssertionError("an additive multiplier consumes a reconstructed one-centered value")
            if expressions.get(product["correction"]) != product["product"] + " + " + product["bias"]:
                raise AssertionError("the additive digit bias is not a separate correction operand")
    if index_advance == "leading_bit_skip":
        baseline = dict(definition, index_advance="sequential")
        sequential = DigitRecurrenceContract(baseline)
        addresses = [event[3][1].name for event in net.events if event[0] == "rom"]
        expressions = {event[2].name: event[3] for event in net.events if event[0] == "wire"}
        for signal in definition["index_signals"][reference.bootstrap:]:
            if not any(address == signal or expressions.get(address, "").startswith("{" + signal + ", ") for address in addresses):
                raise AssertionError("a skip index does not drive a factor ROM address")
        if not any((">>> " + signal) in text or (">> " + signal) in text
                   for signal in definition["shift_signals"] for text in net.decls):
            raise AssertionError("skip indices do not drive any variable shift")
        if selection == "rounding_of_scaled_residual":
            for signal in definition["shift_signals"][reference.bootstrap:]:
                if not any(("<<< " + signal) in expression for expression in expressions.values()):
                    raise AssertionError("rounded digit selection does not use the live radix scale")
    for value in input_values:
        expected, digits = reference.evaluate(value, trace=True)
        condition = [f"y !== {result.w}'d{expected & ((1 << result.w)-1)}"]
        states = reference.normalization_states(value)
        initial_states.add(states[0])
        if versioned:
            execution = reference.log_execution(value) if reference.log_start else reference.exp_execution(value)
            for i, accumulator in enumerate(execution.get("accumulators", [])):
                width = definition["accumulator_widths"][i]
                condition.append(f"probe_acc_{i} !== {width}'d{accumulator & ((1 << width)-1)}")
            if "initial_halve_signal" in definition:
                condition.append(f"halve !== 1'd{int(execution['initial_halve'])}")
            tail_residuals.add(execution["residuals"][-1])
            for i, residual in enumerate(execution["residuals"]):
                width = definition["residual_widths"][i]
                condition.append(f"r{i} !== {width}'d{residual & ((1 << width)-1)}")
            low, high = certificate["initial_interval"]
            if not low <= execution["residuals"][0] <= high:
                raise AssertionError("folded initial residual escaped the all-input interval")
            for i, decision in enumerate(execution["decisions"]):
                if decision["active"]:
                    logical = 0 if decision["role"] == "bootstrap" else reference.bootstrap + decision["index"] - 1
                else:
                    logical = reference.stages - 1
                low, high = certificate["stages"][logical]["output_interval"]
                if not low <= execution["residuals"][i + 1] <= high:
                    raise AssertionError("observed physical residual escaped the independently propagated interval")
                rounded_active += int(selection == "rounding_of_scaled_residual" and decision["active"] and decision["index"] >= 3 and decision["digit"] != 0 and decision["residual"] != 0)
            if "initial_upper_signal" in definition:
                condition.append(f"upper !== 1'd{int(execution['initial_upper'])}")
        if normalization == "additive":
            ordinary, ordinary_digits = normal_coordinates.evaluate(value, trace=True)
            ordinary_states = normal_coordinates.normalization_states(value)
            if expected != ordinary or digits != ordinary_digits or [state + (1 << reference.fraction) for state in states] != ordinary_states:
                raise AssertionError("the exact-child normalization coordinate identity failed")
        for i, state in enumerate(states):
            width = definition["state_widths"][i]
            condition.append(f"q{i} !== {width}'d{state & ((1 << width)-1)}")
        for i, digit in enumerate(digits):
            width = definition["digit_widths"][i]
            observed[i].add(digit)
            condition.append(f"d{i} !== {width}'d{digit & ((1 << width)-1)}")
        if index_advance == "leading_bit_skip":
            _, _, indices, skipped, decisions = reference.skip_execution(value, detail=True)
            if digit_set == "signed_redundant" and selection == "table_lookup" and core == "exp2c":
                for decision in decisions:
                    if not decision["active"]:
                        continue
                    index, residual = decision["index"], decision["residual"]
                    for upper_digit in reference.digits[1:]:
                        factor_sum = reference.factors[index, upper_digit - 1] + reference.factors[index, upper_digit]
                        if factor_sum % 2 and 2 * residual == factor_sum - 1:
                            odd_midpoint_floor_hits += 1
                            if decision["digit"] >= upper_digit:
                                raise AssertionError("signed lookup used floor instead of ceil at an odd midpoint")
            if selection == "rounding_of_scaled_residual" and ((core == "exp2c" and value == 0) or
                    (core == "log2c" and value == 1 << (fraction - 2))):
                if any(digits) or any(index != reference.main_stages + 1 for index in indices[reference.bootstrap:]):
                    raise AssertionError("a zero rounded residual selected a nonzero tail digit")
            if digit_set == "signed_redundant" and selection == "rounding_of_scaled_residual" and core == "log2c" and not reference.log_start:
                half_step = 1 << (fraction - reference.radix_bits - 1)
                middle = 1 << (fraction - 2)
                if value == middle - half_step and (indices[0] != 1 or digits[0] != 1):
                    raise AssertionError("positive half-step did not round to +1 at index 1")
                if value == middle + half_step and (indices[0] != 2 or digits[0] >= 0):
                    raise AssertionError("negative half-step did not skip its zero digit at index 1")
            sequential_result, sequential_digits = sequential.evaluate(value, trace=True)
            if expected != sequential_result or any(sequential_digits[reference.bootstrap + index - 1] != 0 for _, index in skipped):
                raise AssertionError((core, value, "skip changed sequential state or skipped a nonzero digit"))
            reconstructed = digits[:reference.bootstrap] + [0] * reference.main_stages
            for index, digit in zip(indices[reference.bootstrap:], digits[reference.bootstrap:]):
                if index <= reference.main_stages:
                    reconstructed[reference.bootstrap + index - 1] = digit
                    zero_factor_digits += int(digit != 0 and reference.factors[index, digit] == 0)
            if reconstructed != sequential_digits:
                raise AssertionError("the physical skip schedule does not reconstruct the sequential digits")
            skipped_count += len(skipped)
            for i, index in enumerate(indices):
                observed_indices[i].add(index)
                condition.append(f"idx{i} !== {definition['index_widths'][i]}'d{index}")
                condition.append(f"sh{i} !== {definition['shift_widths'][i]}'d{index * reference.radix_bits}")
        lines.append(f"u={fraction}'d{value}; #1; if ({' || '.join(condition)}) begin errors=errors+1; "
                     f'$display("FAIL input={value} result=%h",y); end')
    lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
    status = run_case("", name, "\n".join(lines), directory, net.render())
    case_dir = directory / name
    (case_dir / "contract.json").write_text(json.dumps(definition, indent=2) + "\n")
    (case_dir / "reference.json").write_text(json.dumps({"sha256": reference.sha256,
        "constant_reference": "Fraction atanh-series enclosures", "state_reference": "independent integer recurrence",
        "observed_digits": [sorted(values) for values in observed],
        "observed_indices": [sorted(values) for values in observed_indices], "zero_digits_skipped": skipped_count,
        "nonzero_digits_with_zero_factors": zero_factor_digits,
        "odd_midpoint_floor_hits": odd_midpoint_floor_hits, "initial_states": sorted(initial_states),
        "rounded_active_stages": rounded_active, "tail_residuals": sorted(tail_residuals)}, indent=2) + "\n")
    if index_advance == "leading_bit_skip" and (skipped_count == 0 or len(observed_indices[reference.bootstrap]) < 2):
        raise AssertionError("fixture did not activate data-dependent index skipping")
    if index_advance == "leading_bit_skip" and selection == "table_lookup" and core == "exp2c" and termination == "iterate_to_full_precision" \
            and reference.fraction % reference.radix_bits and zero_factor_digits == 0:
        raise AssertionError("fixture did not exercise positive digits with quantized-zero partial-stage factors")
    if versioned:
        if reference.convergent_start and digit_set == "signed_redundant" and initial_states != {(1 << reference.fraction) * (1 - int(normalization == "additive")),
                                                               (1 << reference.fraction) * (2 - int(normalization == "additive"))}:
            raise AssertionError("the target did not exercise both physical initial product values")
        if termination == "linear_extrapolation" and tail_residuals == {0}:
            raise AssertionError("the fixture did not activate a nonzero linear tail")
        if selection == "rounding_of_scaled_residual" and not rounded_active:
            raise AssertionError("table startup hid the requested rounded selector")
        (case_dir / "convergence.json").write_text(json.dumps(certificate, indent=2) + "\n")
    # The constant check must reject the old negative-rounding bias.
    if digit_set == "signed_redundant":
        damaged = deepcopy(definition)
        damaged["log_factors"][0][0] += 1
        try:
            DigitRecurrenceContract(damaged)
        except ValueError:
            pass
        else:
            raise AssertionError("the independent reference accepted a corrupted negative log factor")
    analytic = reference.analytic_error_enclosure() if versioned else None
    if analytic is not None:
        (case_dir / "analytic-error-enclosure.json").write_text(json.dumps(analytic, indent=2) + "\n")
    error = reference.error_enclosure() if error_bounds else None
    if error is not None:
        if reference.error_enclosure(max_inputs=1)["complete"]:
            raise AssertionError("the error reporter called a partial domain complete")
        if analytic is not None:
            def rational(record):
                return Fraction(int(record["numerator"]), int(record["denominator"]))
            if rational(error["maximum_absolute_error"][1]) > rational(analytic["maximum_absolute_error"][1]):
                raise AssertionError("analytic core bound does not contain the exhaustive mathematical envelope")
        (case_dir / "error-enclosure.json").write_text(json.dumps(error, indent=2) + "\n")
    return {"name": name, "pass": status.endswith(": PASS"), "detail": status, "pins": pins,
            "core": core, "vectors": len(input_values), "contract_sha256": reference.sha256,
            "observed_digits": [sorted(values) for values in observed], "error_enclosure": error,
            "observed_indices": [sorted(values) for values in observed_indices], "zero_digits_skipped": skipped_count,
            "nonzero_digits_with_zero_factors": zero_factor_digits, "odd_midpoint_floor_hits": odd_midpoint_floor_hits,
            "convergence_certificate": certificate, "analytic_error_enclosure": analytic, "initial_states": sorted(initial_states), "rounded_active_stages": rounded_active, "tail_residuals": sorted(tail_residuals)}


def check_log_wide_digit_extrema(directory):
    """A six-bit input is needed to activate both extreme digits in the short r16 tail."""
    rows = []
    for digits, selection, advance, normalization in itertools.product(("nonredundant", "signed_redundant"),
            ("table_lookup", "rounding_of_scaled_residual"), ("sequential", "leading_bit_skip"), ("multiplicative", "additive")):
        row = one_case("log2c", 16, digits, selection, "linear_extrapolation", directory, fraction=6,
                       output_fraction=64, error_bounds=True, index_advance=advance, normalization=normalization)
        observed = set().union(*(set(stage) for stage in row["observed_digits"]))
        endpoints = (0, 15) if digits == "nonredundant" else (-8, 8)
        if not set(endpoints) <= observed:
            raise AssertionError("the wide log target did not activate both digit extremes")
        row["extreme_digits_activated"] = endpoints
        rows.append(row)
        print(row["detail"], flush=True)
        (directory / "wide-extrema-report.json").write_text(json.dumps(rows, indent=2) + "\n")
    if not all(row["pass"] for row in rows):
        raise AssertionError("wide extreme-digit simulation failed")
    return rows


def check_log_startup_mutations(directory):
    import re
    from chialu.targets.rtl.families.selftest import run_case
    rows = []
    for mode, digits, selection in (("bootstrap_bypass", "signed_redundant", "table_lookup"),
                                    ("premature_rounded_selector", "nonredundant", "rounding_of_scaled_residual")):
        baseline = directory / "baseline"
        row = one_case("log2c", 16, digits, selection, "iterate_to_full_precision", baseline,
                       index_advance="leading_bit_skip")
        if not row["pass"]:
            raise AssertionError("mutation baseline failed")
        case = baseline / row["name"]
        definition = json.loads((case / "contract.json").read_text())
        text = (case / "lib.sv").read_text()
        def assignment(signal):
            return next(line for line in text.splitlines() if re.search(r"\b" + re.escape(signal) + r"\s*=", line))
        if mode == "bootstrap_bypass":
            for field in ("state_signals", "accumulator_signals"):
                previous, signal = definition[field][:2]
                line = assignment(signal)
                changed = re.sub(r"assign " + re.escape(signal) + r" = .*;", f"assign {signal} = {previous};", line)
                if changed == line:
                    raise AssertionError("bootstrap mutation did not change RTL")
                text = text.replace(line, changed, 1)
        else:
            line = assignment(definition["digit_signals"][0])
            match = re.search(r" = (\w+) \? ", line)
            if not match:
                raise AssertionError("cannot locate the live startup selector mux")
            signal = match[1]
            line = assignment(signal)
            changed = re.sub(r"assign " + re.escape(signal) + r" = .*;", f"assign {signal} = 1'b0;", line)
            if changed == line:
                raise AssertionError("selector mutation did not change RTL")
            text = text.replace(line, changed, 1)
        status = run_case("", row["name"], (case / "tb.sv").read_text(), directory / mode, text)
        if ": FAIL " not in status:
            raise AssertionError(f"mutation was not detected by valid simulation: {status}")
        rows.append(dict(mutation=mode, detected=True, detail=status, vectors=row["vectors"]))
    (directory / "mutation-report.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work")
    parser.add_argument("--log-startup", action="store_true", help="all real logarithm startup combinations and interval/legacy proofs")
    parser.add_argument("--exp-startup", action="store_true", help="all real exponential startup combinations and interval/legacy proofs")
    parser.add_argument("--entry", action="store_true", help="include full family-entry schedule/coordinate RTL equivalence")
    parser.add_argument("--wide", action="store_true", help="also exercise log-factor precision beyond binary64")
    parser.add_argument("--error-bounds", action="store_true", help="enclose error over each complete contracted core domain")
    parser.add_argument("--skip-only", action="store_true", help="test leading-bit advancement")
    parser.add_argument("--skip-selection", choices=("table_lookup", "rounding_of_scaled_residual"),
                        help="limit a skip run to one digit selection")
    parser.add_argument("--skip-digit-set", choices=("nonredundant", "signed_redundant"), default="nonredundant",
                        help="digit set for a leading-bit skip run")
    parser.add_argument("--normalization", choices=("multiplicative", "additive"), default="multiplicative")
    args = parser.parse_args(argv)
    if args.exp_startup and args.log_startup:
        parser.error("choose one startup core per run")
    if args.entry and not (args.exp_startup or args.log_startup):
        parser.error("--entry requires --exp-startup or --log-startup")
    if args.skip_selection and not args.skip_only:
        parser.error("--skip-selection requires --skip-only")
    selections = (args.skip_selection,) if args.skip_selection else ("table_lookup", "rounding_of_scaled_residual")
    directory = Path(args.work or tempfile.mkdtemp(prefix="chialu-digit-recurrence-"))
    directory.mkdir(parents=True, exist_ok=True)
    results = []
    if args.exp_startup or args.log_startup:
        proof = check_log_startup_rules() if args.log_startup else check_exp_startup_rules()
        (directory / "startup-rules.json").write_text(json.dumps(proof, indent=2) + "\n")
        if args.error_bounds:
            check_mathematical_enclosures()
        if args.log_startup:
            check_log_startup_mutations(directory / "mutations")
        for output_fraction, radix, digits, selection, term, advance, normalization in itertools.product(
                (8, 3, 7, 9, 64) if args.wide else (8,), (2, 4, 16), ("nonredundant", "signed_redundant"),
                ("table_lookup", "rounding_of_scaled_residual"), ("iterate_to_full_precision", "linear_extrapolation"),
                ("sequential", "leading_bit_skip"), ("multiplicative", "additive")):
            if args.exp_startup and output_fraction == 3 and radix == 16 and term == "linear_extrapolation":
                continue  # Proven zero-tail geometry is explicitly rejected by check_exp_startup_rules.
            result = one_case("log2c" if args.log_startup else "exp2c", radix, digits, selection, term, directory,
                              fraction=8 if output_fraction == 8 else 4 if args.log_startup and output_fraction == 64 else 6,
                              output_fraction=output_fraction,
                              index_advance=advance, normalization=normalization, error_bounds=args.error_bounds)
            results.append(result)
            print(result["detail"], flush=True)
            (directory / "report.json").write_text(json.dumps(results, indent=2) + "\n")
        if args.log_startup and args.wide:
            check_log_wide_digit_extrema(directory / "wide_digit_extrema")
        if args.entry:
            for digits, normalization in itertools.product(("nonredundant", "signed_redundant"), ("multiplicative", "additive")):
                entry_dir = directory / f"entry_{digits}_{normalization}"
                entry_dir.mkdir(exist_ok=True)
                check_skip_entry(entry_dir, digit_set=digits, normalization=normalization)
        print(f"{sum(r['pass'] for r in results)}/{len(results)} contracts; {sum(r['vectors'] for r in results)} vectors; {directory}")
        return 0 if all(r["pass"] for r in results) else 1
    if args.error_bounds:
        check_mathematical_enclosures()
    for values in itertools.product(("exp2c", "log2c"), (2, 4, 16),
                                    (args.skip_digit_set,) if args.skip_only else ("nonredundant", "signed_redundant"),
                                    selections,
                                    ("iterate_to_full_precision", "linear_extrapolation")):
        result = one_case(*values, directory, error_bounds=args.error_bounds,
                          index_advance="leading_bit_skip" if args.skip_only else "sequential", normalization=args.normalization)
        results.append(result)
        print(f"{'PASS' if result['pass'] else 'FAIL'} {result['name']}: {result['detail']}", flush=True)
    if args.wide:
        for core, radix, selection, termination in itertools.product(("exp2c", "log2c"), (2, 4, 16) if args.skip_only else (16,),
                                                       selections if args.skip_only else ("table_lookup",),
                                                       ("iterate_to_full_precision", "linear_extrapolation") if args.skip_only else ("iterate_to_full_precision",)):
            result = one_case(core, radix, args.skip_digit_set if args.skip_only else "signed_redundant",
                              selection, termination, directory, fraction=6, output_fraction=64,
                              error_bounds=args.error_bounds, index_advance="leading_bit_skip" if args.skip_only else "sequential",
                              normalization=args.normalization)
            results.append(result)
            print(f"{'PASS' if result['pass'] else 'FAIL'} {result['name']}: {result['detail']}", flush=True)
        if args.skip_only:
            for core, radix, output_fraction, selection, termination in itertools.product(("exp2c", "log2c"), (4, 16), (7, 9), selections,
                                                                                        ("iterate_to_full_precision", "linear_extrapolation")):
                result = one_case(core, radix, args.skip_digit_set, selection, termination, directory,
                                  fraction=6, output_fraction=output_fraction, error_bounds=args.error_bounds,
                                  index_advance="leading_bit_skip", normalization=args.normalization)
                results.append(result)
                print(f"{'PASS' if result['pass'] else 'FAIL'} {result['name']}: {result['detail']}", flush=True)
    if args.skip_only:
        check_skip_entry(directory, selections, args.skip_digit_set, args.normalization)
        if args.skip_digit_set == "signed_redundant" and "table_lookup" in selections and not sum(r["odd_midpoint_floor_hits"] for r in results):
            raise AssertionError("no vector exercised the distinction between floor and ceil at a signed odd midpoint")
    (directory / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"{sum(r['pass'] for r in results)}/{len(results)} contracts; {sum(r['vectors'] for r in results)} vectors; {directory}")
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
