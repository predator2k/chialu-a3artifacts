"""Simulate the complex BKM pair and its reached sine/cosine family states."""
import argparse
from copy import deepcopy
from fractions import Fraction
import itertools
import json
from pathlib import Path
import re
import tempfile

from chialu.verify.bkm_ref import BkmContract, mathematical_pair
from chialu.verify.digit_recurrence_ref import _signed


def pins_for(normalization, termination, index_advance="sequential", radix=2):
    return dict(state_domain="complex_bkm", radix=radix, digit_set="signed_redundant", selection="table_lookup",
                index_advance=index_advance, normalization=normalization, termination=termination)


def check_series():
    import mpmath
    with mpmath.workprec(256):
        for value in range(256):
            truths = mathematical_pair(value, 8, 40)
            for name in ("sin", "cos"):
                answer = getattr(mpmath, name)(mpmath.pi * value / 512)
                sign, mantissa, exponent, _ = answer._mpf_
                exact_working_value = Fraction(int(mantissa)) * Fraction(2) ** int(exponent) * (-1 if sign else 1)
                if not truths[name][0] <= exact_working_value <= truths[name][1]:
                    raise AssertionError("rational trigonometric bounds failed their high-precision cross-check")


def trace_ports(net, definition):
    from chialu.targets.rtl.families.sfu import Ref
    ports = []
    for index, state in enumerate(definition["states"]):
        for coordinate, (signal, width) in enumerate(zip(state["signals"], state["widths"])):
            name = f"q{index}_{coordinate}"
            net.port_out(name, Ref(signal, width, True)); ports.append((name, width))
    for index, digit in enumerate(definition["digits"]):
        for coordinate, signal in enumerate(digit["signals"]):
            name = f"d{index}_{coordinate}"
            width = definition.get("digit_width", 2)
            net.port_out(name, Ref(signal, width, True)); ports.append((name, width))
    for index, stage in enumerate(definition.get("schedule", [])):
        for field, (signal, width) in enumerate(zip(stage["signals"], stage["widths"])):
            name = f"probe_sched_{index}_{field}"
            net.port_out(name, Ref(signal, width, False)); ports.append((name, width))
    return ports


def execution_trace(execution):
    return ([v for state in execution["states"] for v in state] + [v for digit in execution["digits"] for v in digit]
            + [v for row in execution.get("schedule", []) for v in row])


def check_skip_execution(reference, value, execution):
    baseline = reference.sequential_execution(value)
    if execution["outputs"] != baseline["outputs"]:
        raise AssertionError("BKM skipping changed the sequential output")
    expanded = [(0, 0)] * reference.iterations
    active = set()
    for physical, (index, pair) in enumerate(zip(execution["indices"], execution["digits"]), 1):
        if index <= reference.iterations:
            if pair == (0, 0):
                raise AssertionError("an active BKM skip stage retained a zero pair")
            expanded[index - 1] = pair; active.add(pair)
        if execution["states"][physical] != baseline["states"][min(index, reference.iterations)]:
            raise AssertionError("a physical BKM state does not match its logical sequential index")
    if expanded != baseline["digits"] or execution["states"][reference.iterations:] != baseline["states"][reference.iterations:]:
        raise AssertionError("BKM skip expansion or unchanged reconstruction differs from sequential")
    for item in execution["omitted"]:
        if item["digits"] != [0, 0] or baseline["digits"][item["index"] - 1] != (0, 0):
            raise AssertionError("BKM skipped a nonzero digit pair")
    return active


def activity(execution, value, previous=None):
    found = dict(previous or {})
    for index, state in enumerate(execution["states"]):
        if state[1] and "imaginary_state" not in found:
            found["imaginary_state"] = {"input": value, "state_index": index, "imaginary": state[1]}
    for index, digit in enumerate(execution["digits"]):
        if digit[0] < 0 and "negative_real_correction" not in found:
            found["negative_real_correction"] = {"input": value, "iteration": index + 1, "digit": list(digit)}
    return found


def one_case(normalization, termination, directory, source_fraction=8, output_fraction=8, index_advance="sequential", radix=2, inputs=None):
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    name = f"bkm_{normalization}_{termination}_f{output_fraction}_u{source_fraction}" + ("_skip" if index_advance == "leading_bit_skip" else "")
    name += "_r4" if radix == 4 else ""
    net = SF.Net(name, "independent complex BKM fixture")
    argument = net.port_in("u", source_fraction)
    sine, cosine = SF.DigitRecEngine("digit_recurrence_exp_log", pins_for(normalization, termination, index_advance, radix))(
        net, SF.core_of("sinc"), argument, source_fraction, output_fraction, "sincos")
    net.port_out("sin_out", sine); net.port_out("cos_out", cosine)
    definition = net.algorithm_contracts[-1]
    reference = BkmContract(definition)
    values = range(1 << source_fraction) if inputs is None else sorted(set(inputs))
    if not values or any(not 0 <= value < 1 << source_fraction for value in values):
        raise ValueError("the BKM fixture needs valid input words")
    ports = trace_ports(net, definition)
    lines = [f"module tb; logic [{source_fraction-1}:0] u; logic [{output_fraction}:0] sin_out,cos_out; integer errors;"]
    lines += [f"logic [{width-1}:0] {name};" for name, width in ports]
    connections = [".u(u)", ".sin_out(sin_out)", ".cos_out(cos_out)"] + [f".{name}({name})" for name, _ in ports]
    lines += [f"{name} dut({','.join(connections)}); initial begin errors=0;"]
    witnesses, digit_witnesses = {}, {}
    active_pairs, omitted_pairs, visited_indices, first_indices = set(), set(), set(), set()
    omitted_count = 0
    if index_advance == "leading_bit_skip":
        if len(net.memory_banks) != 8 or net.lib_uses.get("lzc") != 2 * reference.iterations:
            raise AssertionError("the BKM core changed its bank count or independent physical LZC instances")
        rom_events = [event for event in net.events if event[0] == "rom"]
        if len(rom_events) != 16 * reference.iterations or any(event[3][2] is None for event in rom_events):
            raise AssertionError("the BKM banked implementation lost an independent read port")
        expressions = {event[2].name: event[3] for event in net.events if event[0] == "wire"}
        addresses = [event[3][1].name for event in net.events if event[0] == "rom"]
        for stage in definition["schedule"]:
            index, shift = stage["signals"][4], stage["signals"][6]
            if not any(expressions.get(address, "").startswith("{" + index + ", ") for address in addresses):
                raise AssertionError("the live BKM index does not drive a complex factor ROM")
            if not any((">>> " + shift) in expression for expression in expressions.values()) or not any(("<<< " + shift) in expression for expression in expressions.values()):
                raise AssertionError("the live BKM index does not drive both prefix and complex-product shifts")
    ordinary = BkmContract(dict(definition, normalization="multiplicative")) if normalization == "additive" else None
    for value in values:
        expected = reference.evaluate(value)
        if index_advance == "leading_bit_skip":
            active_pairs |= check_skip_execution(reference, value, expected)
            omitted_count += len(expected["omitted"])
            omitted_pairs |= {tuple(item["digits"]) for item in expected["omitted"]}
            visited_indices |= {i for i in expected["indices"] if i <= reference.iterations}
            first_indices.add(expected["indices"][0])
        else:
            active_pairs.update(expected["digits"])
        for stage, (index, pair) in enumerate(zip(expected["indices"], expected["digits"]), 1):
            if index <= reference.iterations:
                digit_witnesses.setdefault(str(pair), dict(input=value, physical_stage=stage, index=index,
                    shift=reference.rb * index, residual_before=list(expected["states"][stage - 1][2:])))
        if ordinary is not None:
            other = ordinary.evaluate(value)
            if expected["outputs"] != other["outputs"] or expected["digits"] != other["digits"]:
                raise AssertionError("the exact-child complex coordinate identity failed")
            for index, (first, second) in enumerate(zip(expected["states"], other["states"])):
                shifted = (first[0] + (1 << reference.fraction), *first[1:]) if index <= reference.iterations + 1 else first
                if shifted != second:
                    raise AssertionError("a complex delta state violates the exact-child coordinate identity")
        witnesses = activity(expected, value, witnesses)
        conditions = [f"sin_out !== {sine.w}'d{expected['outputs']['sin']}", f"cos_out !== {cosine.w}'d{expected['outputs']['cos']}"]
        trace = execution_trace(expected)
        conditions += [f"{name} !== {width}'d{value & ((1<<width)-1)}" for (name, width), value in zip(ports, trace)]
        lines.append(f"u={source_fraction}'d{value}; #1; if ({' || '.join(conditions)}) begin errors=errors+1; "
                     f'$display("FAIL input={value} sin=%h cos=%h",sin_out,cos_out); end')
    lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
    status = run_case("", name, "\n".join(lines), directory, net.render())
    if set(witnesses) != {"imaginary_state", "negative_real_correction"}:
        raise AssertionError("the fixture did not activate the complex state and gain correction")
    if index_advance == "leading_bit_skip":
        wanted = set(itertools.product(range(-reference.alpha, reference.alpha + 1), repeat=2)) - {(0, 0)}
        if active_pairs != wanted or omitted_pairs != {(0, 0)} or not omitted_count:
            raise AssertionError("the BKM fixture did not activate all nonzero pairs and truly omit the zero pair")
        if visited_indices != set(range(2 if radix == 2 else 1, reference.iterations + 1)) or len(first_indices) < 2:
            raise AssertionError("the BKM fixture did not activate every eligible index and data-dependent skipping")
        certificate = reference.skip_certificate()
        (directory / name / "skip-certificate.json").write_text(json.dumps(certificate, indent=2) + "\n")
    if index_advance == "leading_bit_skip":
        damaged = deepcopy(definition); damaged.pop("schedule_version")
        try:
            BkmContract(damaged)
        except ValueError:
            pass
        else:
            raise AssertionError("an unversioned BKM skip manifest was accepted as a legacy schedule")
        damaged = deepcopy(definition)
        if radix == 2:
            damaged["schedule"][0]["signals"][6] = "unrelated_shift"
        else:
            damaged["schedule"][0]["widths"][6] = damaged["schedule"][0]["widths"][4]
        try:
            BkmContract(damaged)
        except ValueError:
            pass
        else:
            raise AssertionError("the BKM manifest detached the shift from its selected index")
    for field in ("real_log_factors", "imag_log_factors"):
        damaged = deepcopy(definition); damaged[field][0][1] += 1
        try:
            BkmContract(damaged)
        except ValueError:
            pass
        else:
            raise AssertionError("the independent constant contract accepted a corrupted complex factor")
    if radix == 4 and index_advance == "sequential" and active_pairs != set(itertools.product(range(-2, 3), repeat=2)):
        raise AssertionError("the radix-4 fixture did not activate all 25 actual complex pairs")
    analytic = None
    if radix == 4:
        certificate = reference.convergence_certificate()
        (directory / name / "convergence-certificate.json").write_text(json.dumps(certificate, indent=2) + "\n")
        analytic = reference.analytic_error_enclosure()
        for value in values:
            expected = reference.sequential_execution(value)
            for state, stage in zip(expected["states"][1:], certificate["stages"]):
                a, b, c, d = stage["rectangle"]
                if not (a <= state[2] <= b and c <= state[3] <= d):
                    raise AssertionError("an actual residual escaped the complete rectangle certificate")
    error = reference.error_enclosure()
    if analytic is not None and error["complete"]:
        for output, bounds in error["maximum_absolute_error"].items():
            bound = analytic["maximum_absolute_error_upper"][output]
            if Fraction(int(bounds[1]["numerator"]), int(bounds[1]["denominator"])) > Fraction(int(bound["numerator"]), int(bound["denominator"])):
                raise AssertionError("the complete analytic bound missed a finite-domain mathematical error")
    if reference.error_enclosure(max_inputs=1)["complete"]:
        raise AssertionError("BKM reported a partial input domain as complete")
    (directory / name / "contract.json").write_text(json.dumps(definition, indent=2) + "\n")
    result = {"name": name, "pass": status.endswith(": PASS"), "detail": status, "vectors": len(values),
              "inputs_exhaustive": len(values) == 1 << source_fraction,
              "witnesses": witnesses, "radix": radix, "error_enclosure": error, "analytic_error_enclosure": analytic, "contract_sha256": reference.sha256,
              "index_advance": index_advance, "rom_banks": len(net.memory_banks), "rom_storage_bits": net.rom_bits,
              "lzc_instances": net.lib_uses.get("lzc", 0), "active_pairs": sorted(active_pairs), "omitted_pairs": sorted(omitted_pairs),
              "digit_witnesses": digit_witnesses,
              "zero_pairs_omitted": omitted_count, "visited_indices": sorted(visited_indices), "first_indices": sorted(first_indices)}
    (directory / name / "reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def family_case(function, normalization, termination, directory, format_name="fp8e4m3", index_advance="sequential", radix=2):
    """Check every reached core state, plus a separate full-format numerical report."""
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.targets.rtl.engine import Conventions, Engine
    from chialu.verify.formats import parse_format, PINF, NINF
    from chialu.verify.errors import ErrorReport
    fmt = parse_format(format_name)
    geometry = SF.Geom.of_engine(Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions()))
    pins = pins_for(normalization, termination, index_advance, radix)
    name, text, net = SF.sfu_sv(function, fmt, geometry, "digit_recurrence_exp_log", pins)
    definition = net.algorithm_contracts[-1]; reference = BkmContract(definition)
    sin_signal, cos_signal = (definition["outputs"][name]["signal"] for name in ("sin", "cos"))
    selector = next((match.group(1) for event in net.events if event[0] == "wire"
                     if (match := re.fullmatch(r"(\w+) \? " + cos_signal + " : " + sin_signal, event[3]))), None)
    if selector is None:
        raise AssertionError("both BKM results do not feed the live quadrant selector")
    observed = [(definition["input"], definition["input_width"], False), (sin_signal, definition["outputs"]["sin"]["width"], False),
                (cos_signal, definition["outputs"]["cos"]["width"], False), (selector, 1, False)]
    observed += [(signal, width, True) for state in definition["states"] for signal, width in zip(state["signals"], state["widths"])]
    observed += [(signal, definition.get("digit_width", 2), True) for digit in definition["digits"] for signal in digit["signals"]]
    observed += [(signal, width, False) for row in definition.get("schedule", []) for signal, width in zip(row["signals"], row["widths"])]
    width = geometry.XT
    lines = [f"module tb; logic [{width-1}:0] x,y; logic inv,dz; integer file_id;",
             f"{name} dut(.x(x),.y(y),.inv(inv),.dz(dz)); initial begin file_id=$fopen(\"trace.txt\",\"w\");"]
    fields = ",".join([f"dut.{signal}" for signal, _, _ in observed] + ["y", "inv", "dz"])
    template = " ".join(["%h"] * (len(observed) + 3))
    for bits in range(1 << fmt.width):
        lines.append(f"x={width}'d{SF.x_of_bits(fmt,bits,geometry)}; #1; $fdisplay(file_id,\"{bits} {template}\",{fields});")
    lines += ['$fclose(file_id); $display("PASS"); $finish; end endmodule']
    status = run_case("", name, "\n".join(lines), directory, text)
    if not status.endswith(": PASS"):
        raise AssertionError(status)
    rows = (directory / name / "trace.txt").read_text().splitlines()
    if len(rows) != 1 << fmt.width:
        raise AssertionError("family capture did not cover the entire input format")
    numerical = ErrorReport(); witnesses = {}; branches = set()
    active_pairs = set(); omitted_count = 0
    for row in rows:
        fields = row.split(); bits = int(fields[0]); values = [int(word, 16) for word in fields[1:]]
        argument, sine, cosine, branch = values[:4]
        expected = reference.evaluate(argument)
        if index_advance == "leading_bit_skip":
            active_pairs |= check_skip_execution(reference, argument, expected)
            omitted_count += len(expected["omitted"])
        else:
            active_pairs.update(expected["digits"])
        trace = execution_trace(expected)
        actual = [_signed(value, width) if signed else value for value, (_, width, signed) in zip(values[4:len(observed)], observed[4:])]
        if (sine, cosine) != (expected["outputs"]["sin"], expected["outputs"]["cos"]) or actual != trace:
            raise AssertionError((function, bits, "reached BKM state differs from independent integer contract"))
        witnesses = activity(expected, bits, witnesses); branches.add(branch)
        packed, _ = SF.bits_of_x(fmt, values[-3], geometry, inv=values[-2], dz=values[-1])
        if values[-2] != int(fmt.decode(bits) in (PINF, NINF)) or values[-1] != 0:
            raise AssertionError((function, bits, "unit-level domain flags differ from the sine/cosine contract"))
        numerical.add(fmt, SF.reference_bits(function, fmt, bits), packed, str(bits))
    if branches != {0, 1} or len(witnesses) != 2:
        raise AssertionError("full-family inputs did not activate both quadrant outputs and complex corrections")
    if index_advance == "leading_bit_skip" and (len(active_pairs) != (2 * reference.alpha + 1) ** 2 - 1 or not omitted_count):
        raise AssertionError("the full family input domain did not activate all nonzero complex pairs and true omissions")
    if radix == 4 and index_advance == "sequential" and len(active_pairs) != 25:
        raise AssertionError("the full family input domain did not activate all 25 complex pairs")
    result = {"name": name, "pass": True, "vectors": len(rows), "witnesses": witnesses, "quadrant_branches": sorted(branches),
              "scope": "independent BKM contract at every reached core input; surrounding range/reconstruction checked numerically",
              "mathematical_max_ulp": numerical.max_ulp, "mathematical_wrong": numerical.n_wrong,
              "mathematical_special_mismatches": numerical.n_special_mismatch, "mathematical_worst": numerical.worst,
              "mathematical_special_pass": numerical.n_special_mismatch == 0,
              "domain_flags_checked": True, "flags_checked": False, "index_advance": index_advance,
              "active_pairs": sorted(active_pairs), "zero_pairs_omitted": omitted_count}
    (directory / name / "contract.json").write_text(json.dumps(definition, indent=2) + "\n")
    (directory / name / "reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def seed_special_case(family, pins, directory, invalid_result="saturate", nan_payload="canonical",
                      format_name="fp8e5m2", functions=("sin", "cos"), finite_inputs=(), tininess="after", special_inputs=None):
    """Compare complete VecSFU output words and flags on specials and exact zeros."""
    from chialu.targets.derive import seed_for
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.sfu_ref import normalize_sfu_spec, sfu_layout, sfu_expected, _read
    from chialu.verify.formats import Special
    from chialu.verify.errors import compare
    spec = normalize_sfu_spec({"unit": "vec_sfu", "dut_name": "sfu_core", "modes": [{"count": 1, "format": format_name}],
        "functions": list(functions), "rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "sr_bits": 1,
        "daz_in": [False, True], "ftz_out": [False, True],
        "flags": ["invalid", "div_zero", "overflow", "underflow", "inexact", "nan", "denormal"],
        "invalid_result": invalid_result, "nan_payload": nan_payload, "tininess": tininess})
    layout = sfu_layout(spec)
    source = str(seed_for(spec, family=(family, pins)))
    name = f"seed_special_{family}_{format_name}_{'_'.join(functions)}_{invalid_result}_{nan_payload}"
    if finite_inputs:
        name += f"_finite_{tininess}"
    ports = layout["core_in"] + layout["core_out"]
    lines = ["module tb; integer errors;"] + [f"logic [{port.width-1}:0] {port.name};" for port in ports]
    lines += ["sfu_core dut(" + ",".join(f".{port.name}({port.name})" for port in ports) + "); initial begin errors=0;"]
    vectors = 0
    fmt = layout["modes"][0][1]
    patterns = list(special_inputs) if special_inputs is not None else \
        [bits for bits in range(1 << fmt.width) if isinstance(fmt.decode(bits), Special) or fmt.decode(bits) == 0]
    patterns = sorted(set(patterns) | set(finite_inputs))
    for bits, function, rounding, daz, ftz in itertools.product(patterns, range(len(functions)), range(5), range(2), range(2)):
        mode = spec["rounding"][rounding]
        for word in ((0, 1) if mode == "SR" else (0,)):
            ctrl = {"rounding": mode, "daz_in": bool(daz), "ftz_out": bool(ftz)}
            expected, flags = sfu_expected(spec, layout, 0, function, bits, ctrl, [word], [])
            allowed = [(expected, flags)]
            value = _read(fmt, bits, bool(daz))[0] if bits in finite_inputs else None
            if bits in finite_inputs and not isinstance(value, Special) and value != 0 and flags & (1 << 4) and not flags & 1 \
                    and not isinstance(fmt.decode(expected), Special):
                allowed = []
                for candidate in range(max(0, expected - 2), min(1 << fmt.width, expected + 3)):
                    score = compare(fmt, expected, candidate)
                    if score.special_mismatch or score.ulp > 1 or (getattr(fmt, "signed", True) and (candidate >> (fmt.width-1)) != (expected >> (fmt.width-1))):
                        continue
                    candidate_flags = flags
                    if tininess == "after" and functions[function] in ("sin", "cos"):
                        tiny = abs(fmt.decode(candidate)) < Fraction(2) ** (1 - fmt.bias)
                        candidate_flags = (candidate_flags | (1 << 3)) if tiny else (candidate_flags & ~(1 << 3))
                    allowed.append((candidate, candidate_flags))
            comparison = " || ".join(f"(y === {fmt.width}'d{candidate} && flags === 7'd{candidate_flags})" for candidate, candidate_flags in allowed)
            lines.append(f"x={fmt.width}'d{bits}; fn_sel=1'd{function}; rounding_sel=3'd{rounding}; daz_in_sel=1'd{daz}; "
                         f"ftz_out_sel=1'd{ftz}; sr_rnd=1'd{word}; #1; if(!({comparison})) "
                         f'begin errors=errors+1; $display("FAIL x={bits} fn={function} rnd={mode} y=%h flags=%h expected={expected:x}/{flags:x}",y,flags); end')
            vectors += 1
    lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
    status = run_case("", name, "\n".join(lines), directory, source)
    result = {"name": name, "family": family, "format": format_name, "functions": list(functions),
              "invalid_result": invalid_result, "nan_payload": nan_payload,
              "finite_inputs": list(finite_inputs), "tininess": tininess, "finite_numeric_ulp_budget": 1 if finite_inputs else 0,
              "vectors": vectors, "pass": status.endswith(": PASS"), "detail": status,
              "scope": "complete VecSFU specials/zeros/exact identities are bit-exact; selected inexact finite values use one ULP, with exact flags and delivered-result after-tininess"}
    (directory / name / "reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def existing_engine_domain_case(function, directory):
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.targets.rtl.engine import Conventions, Engine
    from chialu.verify.formats import parse_format, Special, PINF, NINF
    fmt = parse_format("fp8e5m2")
    geometry = SF.Geom.of_engine(Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions()))
    name, text, _ = SF.sfu_sv(function, fmt, geometry, "cordic", {"coordinate_set": "circular", "iterations": 12})
    width = geometry.XT
    lines = [f"module tb; logic [{width-1}:0] x,y; logic inv,dz; integer errors;",
             f"{name} dut(.x(x),.y(y),.inv(inv),.dz(dz)); initial begin errors=0;"]
    for bits in range(1 << fmt.width):
        value = fmt.decode(bits)
        special = int(isinstance(value, Special))
        invalid = int(value in (PINF, NINF))
        lines.append(f"x={width}'d{SF.x_of_bits(fmt,bits,geometry)}; #1; if(y[{width-1}:{width-2}] !== 2'd{special} || inv !== 1'd{invalid} || dz !== 1'b0) "
                     f'begin errors=errors+1; $display("FAIL bits={bits} sp=%h inv=%b dz=%b",y[{width-1}:{width-2}],inv,dz); end')
    lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
    status = run_case("", name, "\n".join(lines), directory, text)
    return {"name": name, "pass": status.endswith(": PASS"), "detail": status, "vectors": 1 << fmt.width,
            "scope": "existing CORDIC X-level domain result and inv/dz flags over the entire format"}


def seed_flag_cases(directory, index_advance="sequential", radix=2):
    from chialu.verify.formats import parse_format, NAN, PINF, NINF
    from chialu.verify.bkm_ref import pi_bounds
    results = []
    for family, pins in (("digit_recurrence_exp_log", pins_for("multiplicative", "iterate_to_full_precision", index_advance, radix)),
                         ("cordic", {"coordinate_set": "circular", "iterations": 12})):
        for payload in ("canonical", "propagate"):
            results.append(seed_special_case(family, pins, directory, nan_payload=payload))
        for invalid in ("saturate", "zero"):
            results.append(seed_special_case(family, pins, directory, invalid_result=invalid, format_name="fps1e3m2I"))
        for tininess in ("before", "after"):
            results.append(seed_special_case(family, pins, directory, tininess=tininess,
                                             finite_inputs=(1, 2, 3, 4, 129, 130, 131, 132)))
    for payload in ("canonical", "propagate"):
        results.append(seed_special_case("digit_recurrence_exp_log", {"state_domain": "real", "radix": 2}, directory,
                                         nan_payload=payload, functions=("exp2", "log2")))
    fmt = parse_format("fp8e5m2")
    exact_inputs = tuple(sorted({fmt.round(v) for v in (-16, -2, -1, Fraction(1, 2), 1, 2, 4)}))
    results.append(seed_special_case("digit_recurrence_exp_log", {"state_domain": "real", "radix": 2}, directory,
                                     functions=("exp2", "log2"), finite_inputs=exact_inputs))
    fmt = parse_format("fps1e3m2I")
    for invalid in ("zero", "saturate"):
        results.append(seed_special_case("digit_recurrence_exp_log", {"state_domain": "real", "radix": 2}, directory,
                                         functions=("exp2", "log2"), format_name=fmt.name, invalid_result=invalid,
                                         finite_inputs=tuple(fmt.round(v) for v in (-1, 1, 2))))
    fmt = parse_format("fps1e2m8NI")
    sign = 1 << (fmt.width - 1)
    low, high = pi_bounds(64)
    near = fmt.round(low / 2)
    if fmt.round(high / 2) != near:
        raise AssertionError("the nearest pi/2 input was not established by rational bounds")
    special = (0, sign, fmt.encode_special(NAN), sign | fmt.encode_special(NAN),
               fmt.encode_special(PINF), fmt.encode_special(NINF))
    for family, pins in (("digit_recurrence_exp_log", pins_for("multiplicative", "iterate_to_full_precision", index_advance, radix)),
                         ("cordic", {"coordinate_set": "circular", "iterations": 12})):
        results.append(seed_special_case(family, pins, directory, format_name=fmt.name,
                                         finite_inputs=(1, sign | 1, near, sign | near), tininess="before", special_inputs=special))
    return results


def sharing_cases(directory, radix=2):
    """Multi-lane/mode sharing must preserve the verified separate-function seed."""
    from chialu.targets.derive import seed_for
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.targets.rtl.families.mul import dedupe_modules
    from chialu.verify.sfu_ref import normalize_sfu_spec, sfu_layout
    base = {"unit": "vec_sfu", "dut_name": "bkm_separate", "modes": [{"count": 2, "format": "fp4e2m1"}, {"count": 1, "format": "fps1e2m2NI"}],
            "functions": ["sin", "cos"], "rounding": ["RNE"],
            "flags": ["invalid", "div_zero", "overflow", "underflow", "inexact", "nan", "denormal"]}
    spec = normalize_sfu_spec(base); layout = sfu_layout(spec)
    pins = pins_for("multiplicative", "iterate_to_full_precision", "leading_bit_skip", radix)
    separate = str(seed_for(spec, family=("digit_recurrence_exp_log", dict(pins, sharing="datapath_per_fn"))))
    rows = []
    for sharing in ("shared_evaluator", "shared_range_reduction", "fully_shared_rom_evaluator"):
        shared_spec = normalize_sfu_spec(dict(base, dut_name="bkm_shared"))
        shared = str(seed_for(shared_spec, family=("digit_recurrence_exp_log", dict(pins, sharing=sharing))))
        lines = ["module tb; integer errors;"]
        lines += [f"logic [{port.width-1}:0] {port.name};" for port in layout["core_in"]]
        for port in layout["core_out"]:
            lines.append(f"logic [{port.width-1}:0] a_{port.name},b_{port.name};")
        common = [f".{port.name}({port.name})" for port in layout["core_in"]]
        for module, prefix in (("bkm_separate", "a"), ("bkm_shared", "b")):
            connections = common + [f".{port.name}({prefix}_{port.name})" for port in layout["core_out"]]
            lines.append(f"{module} {prefix}({','.join(connections)});")
        lines.append("initial begin errors=0;")
        for port in layout["core_in"]:
            lines.append(f"{port.name}=0;")
        comparisons = " || ".join(f"a_{port.name} !== b_{port.name}" for port in layout["core_out"])
        vectors = 0
        for mode, (count, fmt) in enumerate(layout["modes"]):
            for function, bits in itertools.product(range(2), range(1 << fmt.width)):
                packed = bits | ((bits ^ (0xa5 & ((1 << fmt.width) - 1))) << fmt.width) if count == 2 else bits
                lines.append(f"mode=1'd{mode}; fn_sel=1'd{function}; x=8'd{packed}; #1; if({comparisons}) "
                             f'begin errors=errors+1; $display("FAIL mode={mode} fn={function} x={packed}"); end')
                vectors += 1
        lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
        status = run_case("", "bkm_" + sharing, "\n".join(lines), directory, dedupe_modules(separate + "\n" + shared))
        rows.append(dict(sharing=sharing, pass_sim=status.endswith(": PASS"), detail=status, vectors=vectors,
                         scope="full-domain fp4/fp5, multi-mode/two-lane bit and flag equivalence to the separately verified per-function seed"))
        print(status, flush=True)
        (directory / "sharing-report.json").write_text(json.dumps(rows, indent=2) + "\n")
    if not all(row["pass_sim"] for row in rows):
        raise AssertionError("BKM sharing changed the selected datapath behavior")
    return rows


def skip_mutation_cases(directory, radix=2):
    from chialu.targets.rtl.families.selftest import run_case
    row = one_case("multiplicative", "iterate_to_full_precision", directory / "baseline", index_advance="leading_bit_skip", radix=radix)
    if not row["pass"]:
        raise AssertionError("BKM mutation baseline failed")
    folder = directory / "baseline" / row["name"]
    definition = json.loads((folder / "contract.json").read_text())
    original = (folder / "lib.sv").read_text()
    results = []
    mutations = [("max_components_instead_of_min", 2), ("following_skips_an_unchecked_index", 5)]
    if radix == 4:
        mutations.append(("binary_shift_in_radix4_stage", 6))
    for mutation, field in mutations:
        signal = definition["schedule"][0]["signals"][field]
        line = next(line for line in original.splitlines() if re.search(r"\b" + re.escape(signal) + r"\s*=", line))
        if field == 6:
            index = definition["schedule"][0]["signals"][4]
            altered = re.sub(r" = .*;", f" = {index};", line)
            text = original.replace(line, altered, 1)
            status = run_case("", row["name"], (folder / "tb.sv").read_text(), directory / mutation, text)
            if ": FAIL " not in status:
                raise AssertionError(f"radix-4 shift mutation was not detected: {status}")
            results.append(dict(mutation=mutation, detected=True, detail=status, vectors=row["vectors"]))
            continue
        match = re.search(r" = (\w+) \? (\w+) : (\w+);", line)
        if not match:
            raise AssertionError("cannot locate the live BKM scheduling mux")
        condition, first, second = match.groups()
        if field == 2:
            replacement = f" = {condition} ? {second} : {first};"
        else:
            index = definition["schedule"][0]["signals"][4]
            width = definition["schedule"][0]["widths"][4]
            replacement = f" = {condition} ? ({index} + {width}'d2) : {second};"
        altered = line[:match.start()] + replacement
        text = original.replace(line, altered, 1)
        status = run_case("", row["name"], (folder / "tb.sv").read_text(), directory / mutation, text)
        if ": FAIL " not in status:
            raise AssertionError(f"BKM scheduling mutation was not detected by a valid simulation: {status}")
        results.append(dict(mutation=mutation, detected=True, detail=status, vectors=row["vectors"]))
    (directory / "mutation-report.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


def index_binding_cases(directory, radix=2):
    """The compact default tree must retain descendant bindings and explicit LZC selection."""
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.bkm_ref import component_cells, first_component_digit
    bindings = {
        "parent_adder": {"adder": ("ripple_carry", {"full_adder_logic": "xor_majority", "chunk_width_bits": 1})},
        "explicit_lzc": {"lzc": ("priority_encoder", {"lookahead_group": 4, "levels": 2, "output_form": "one_hot_then_encode"})},
    }
    rows = []
    for label, bind in bindings.items():
        net = SF.Net("bkm_binding_" + label, "BKM leading primitive binding", bind=bind)
        value = net.port_in("value", 22, True)
        result = SF._bkm_first_nonzero(net, value, 18, 18 if radix == 2 else 9, "real", radix=radix)
        net.port_out("index", result)
        if label == "parent_adder" and (not net.lib_uses.get("adder") or "fam_adder_ripple_carry" not in net.render()):
            raise AssertionError("the wrapped native LZC lost its selected parent adder")
        if label == "explicit_lzc" and ("bkm_native_lzc" in net.render() or "fam_count_priority_encoder_g4_l2_one_hot_then_encode" not in net.render()):
            raise AssertionError("an explicit LZC family/pins were replaced by the compact native tree")
        patterns = set()
        for negative in (False, True):
            for low, stop in component_cells(18, 18 if radix == 2 else 9, "real", negative, radix):
                patterns |= {-x if negative else x for x in (low, stop - 1)}
        lines = [f"module tb; logic signed [21:0] value; logic [{result.w-1}:0] index; integer errors;",
                 f"{net.name} dut(.value(value),.index(index)); initial begin errors=0;"]
        for word in sorted(patterns):
            expected = first_component_digit(18, 18 if radix == 2 else 9, word, "real", radix)
            lines.append(f"value=22'd{word & ((1<<22)-1)}; #1; if(index !== {result.w}'d{expected}) "
                         f'begin errors=errors+1; $display("FAIL value={word} index=%h",index); end')
        lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
        status = run_case("", net.name, "\n".join(lines), directory, net.render())
        rows.append(dict(name=label, pass_sim=status.endswith(": PASS"), detail=status, vectors=len(patterns), library_uses=net.lib_uses))
    invalid = SF.Net("bad_bkm_lzc", "explicit invalid LZC", bind={"lzc": ("priority_encoder", {"output_form": "unknown"})})
    try:
        SF._bkm_first_nonzero(invalid, invalid.port_in("value", 22, True), 18, 18 if radix == 2 else 9, "real", radix=radix)
    except ValueError:
        pass
    else:
        raise AssertionError("an invalid explicit LZC silently fell back to the native tree")
    if not all(row["pass_sim"] for row in rows):
        raise AssertionError("BKM primitive binding simulation failed")
    (directory / "binding-report.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows


def component_index_cases(directory, radix=2, fractions=None):
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.bkm_ref import component_cells, first_component_digit, component_digit, zero_threshold, skip_certificate, radix4_convergence_certificate
    rows = []
    if fractions is None:
        fractions = (10, 12, 18, 28, 60, 74) if radix == 2 else (10, 11, 12, 18, 19, 28, 60, 74, 75)
    for fraction, linear, coordinate in itertools.product(fractions, (False, True), ("real", "imag")):
        full = (fraction + (radix.bit_length() - 2)) // (radix.bit_length() - 1)
        iterations = (full + 1) // 2 + 1 if linear else full
        width = fraction + 4
        name = f"bkm_index_{coordinate}_f{fraction}_n{iterations}"
        net = SF.Net(name, "complete BKM index/prefix cell endpoints")
        residual = net.port_in("residual", width, True)
        index = net.port_in("index", (iterations + 3).bit_length())
        first = SF._bkm_first_nonzero(net, residual, fraction, iterations, coordinate, radix=radix)
        digit = SF._bkm_prefix_digit(net, residual, index, fraction, iterations, coordinate, radix=radix)
        net.port_out("first", first); net.port_out("digit", digit)
        vectors = set()
        low, high = -(1 << (width - 1)), (1 << (width - 1)) - 1
        for negative in (False, True):
            for start, stop in component_cells(fraction, iterations, coordinate, negative, radix):
                for magnitude in {start, stop - 1}:
                    value = -magnitude if negative else magnitude
                    chosen = first_component_digit(fraction, iterations, value, coordinate, radix)
                    vectors.add((value, chosen))
        for shift in range(1, iterations + 2):
            positive = zero_threshold(fraction, shift, coordinate, False, radix)
            negative = zero_threshold(fraction, shift, coordinate, True, radix)
            for value in (low, high, 0, positive - 1, positive, positive + 1, -negative - 1, -negative, -negative + 1):
                if low <= value <= high:
                    vectors.add((value, shift))
            if radix == 4:
                for half_digit in (-3, -1, 1, 3):
                    boundary = -(-(half_digit * (1 << fraction)) // (2 * radix ** shift))
                    vectors |= {(value, shift) for value in (boundary - 1, boundary, boundary + 1) if low <= value <= high}
        lines = [f"module tb; logic signed [{width-1}:0] residual; logic [{index.w-1}:0] index;",
                 f"logic [{first.w-1}:0] first; logic [{digit.w-1}:0] digit; integer errors;",
                 f"{name} dut(.residual(residual),.index(index),.first(first),.digit(digit)); initial begin errors=0;"]
        for value, shift in sorted(vectors):
            expected_index = first_component_digit(fraction, iterations, value, coordinate, radix)
            expected_digit = component_digit(fraction, shift, value, coordinate, radix)
            lines.append(f"residual={width}'d{value & ((1<<width)-1)}; index={index.w}'d{shift}; #1; "
                         f"if(first !== {first.w}'d{expected_index} || digit !== {digit.w}'d{expected_digit & ((1 << digit.w) - 1)}) "
                         f'begin errors=errors+1; $display("FAIL residual={value} index={shift} first=%h digit=%h",first,digit); end')
        lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
        status = run_case("", name, "\n".join(lines), directory, net.render())
        rows.append(dict(name=name, pass_sim=status.endswith(": PASS"), detail=status, vectors=len(vectors),
                         fraction_bits=fraction, iterations=iterations, coordinate=coordinate,
                         complete_predicate_cells=True, state_signed_minimum=low))
        print(status, flush=True)
        (directory / "component-report.json").write_text(json.dumps(rows, indent=2) + "\n")
    proof_cells, convergence = 0, []
    for fraction, linear in itertools.product(range(10, 91), (False, True)):
        full = (fraction + (radix.bit_length() - 2)) // (radix.bit_length() - 1)
        iterations = (full + 1) // 2 + 1 if linear else full
        proof = skip_certificate(fraction, iterations, radix)
        if not proof["complete"]:
            raise AssertionError("BKM zero-cell proof is incomplete")
        proof_cells += sum(row["cells"] for row in proof["component_cells"])
        if radix == 4:
            certificate = radix4_convergence_certificate(fraction, iterations)
            convergence.append(dict(fraction_bits=fraction, iterations=iterations, complete=certificate["complete"],
                                    final_rectangle=certificate["stages"][-1]["rectangle"]))
    if not all(row["pass_sim"] for row in rows):
        raise AssertionError("actual BKM index/prefix helper differs from its full-state predicate cells")
    (directory / "component-proof.json").write_text(json.dumps(dict(geometries=162, component_geometries=648,
        signed_state_cells=proof_cells, input_words_enumerated=0), indent=2) + "\n")
    if convergence:
        (directory / "convergence-proof.json").write_text(json.dumps(convergence, indent=2) + "\n")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radix", type=int, choices=(2, 4), default=2)
    parser.add_argument("--skip", action="store_true", help="exercise the simultaneous-zero leading-bit schedule")
    parser.add_argument("--work"); parser.add_argument("--wide", action="store_true")
    parser.add_argument("--family", action="store_true", help="also check full fp8 sine/cosine family entries")
    parser.add_argument("--seed-flags", action="store_true", help="also check complete seed special/small-value flags and an existing CORDIC engine")
    args = parser.parse_args(argv)
    directory = Path(args.work or tempfile.mkdtemp(prefix="chialu-bkm-")); directory.mkdir(parents=True, exist_ok=True)
    check_series()
    if args.skip:
        component_index_cases(directory / "component_cells", args.radix)
        index_binding_cases(directory / "bindings", args.radix)
        skip_mutation_cases(directory / "mutations", args.radix)
    results = []
    for normalization, termination in itertools.product(("multiplicative", "additive"), ("iterate_to_full_precision", "linear_extrapolation")):
        for fraction in ((8, 64) if args.wide else (8,)):
            result = one_case(normalization, termination, directory, source_fraction=(4 if args.skip else 6) if fraction == 64 else 8, output_fraction=fraction,
                              index_advance="leading_bit_skip" if args.skip else "sequential", radix=args.radix)
            results.append(result); print(result["detail"], flush=True)
    families = []
    if args.family:
        for function, normalization, termination in itertools.product(("sin", "cos"), ("multiplicative", "additive"), ("iterate_to_full_precision", "linear_extrapolation")):
            result = family_case(function, normalization, termination, directory, index_advance="leading_bit_skip" if args.skip else "sequential", radix=args.radix)
            families.append(result); print(f"{result['name']}: algorithm PASS max_ulp={result['mathematical_max_ulp']} special_mismatches={result['mathematical_special_mismatches']}", flush=True)
    sharings = sharing_cases(directory / "sharing", args.radix) if args.skip and args.family else []
    seeds, domains = [], []
    if args.seed_flags:
        seeds = seed_flag_cases(directory, "leading_bit_skip" if args.skip else "sequential", args.radix)
        domains = [existing_engine_domain_case(function, directory) for function in ("sin", "cos")]
        for result in seeds + domains:
            print(result["detail"], flush=True)
    (directory / "report.json").write_text(json.dumps({"cores": results, "families": families, "seeds": seeds, "existing_domains": domains, "sharing": sharings}, indent=2) + "\n")
    print(f"{sum(x['pass'] for x in results)}/{len(results)} core contracts; {len(families)} family contracts; {directory}")
    return 0 if all(x["pass"] for x in results + seeds + domains) and all(x["mathematical_special_pass"] for x in families) and all(x["pass_sim"] for x in sharings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
