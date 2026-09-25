"""Map family ports to Python reference operations and explicit error bounds."""
from __future__ import annotations

from dataclasses import dataclass, field
import random
from fractions import Fraction
from typing import Callable, NamedTuple

from chialu.verify import ops
from chialu.verify.formats import (BCDFormat, FloatFormat, IntFormat, PositFormat, Special,
                                   NAN, NAR, PINF, NINF, _floor_log2, parse_format)


class Port(NamedTuple):
    name: str
    direction: str
    width: int


@dataclass(frozen=True)
class Tolerance:
    """Bound the maximum and mean error in the stated units."""
    max_err: float
    mean_err: float
    ports: tuple[str, ...]
    scale: int = 1
    relative: bool = False
    signed: bool = False
    minimum: int = 0
    slack: int = 0
    unchecked_ports: tuple[str, ...] = ()


# These gaps concern output representations or contracts absent from ops.py.
NO_GOLDEN = {
    "truncated_multiplier_legacy": "The legacy correction pin selects a different multiplier algorithm; the canonical correction_scheme contract does not cover it.",
    "approximate_divider": "The approximate divider bounds its quotient but declares no remainder bound; ops.py does not express that output-pair contract.",
    "nonbinary_slot": "A binary arithmetic slot binds modular arithmetic; ops.py has no contract for that composition.",
    "approximate_slot": "An arithmetic slot binds an approximate component without a bound for the composed error.",
    "fp_adder": "X significand, exponent and sticky outputs have no unique format-level encoding; fptest checks their packed values.",
    "fp_multiplier": "X outputs and fused rounding flags require the internal arithmetic contract; fptest checks their packed values.",
    "fp_fma": "X sum and product outputs of the fused datapath have no unique format-level encoding; fptest checks their packed values in both roles.",
    "fp_comparator": "The comparator accepts X values rather than format patterns; fptest supplies the internal representation.",
    "fp_divider": "X quotient and sticky outputs require the internal arithmetic contract; fptest checks their packed values.",
    "fp_sqrt": "X root and sticky outputs require the internal arithmetic contract; fptest checks their packed values.",
    "rounder": "X sticky inputs and exception flags are outside fp_ref's pattern result; fptest checks the rounder contract.",
    "posit_unit": "V/X conversion ports and exception flags are outside the format-level result; posittest checks the unit contract.",
    "dot": "Accumulator and X outputs include family-specific intermediate precision; dottest checks the accumulation contract.",
    "dot_operation": "This pin selects an operation that the dot-product unit does not express; its current generator substitutes products.",
    "sfu": "Internal X outputs and family error contracts are outside the scalar pattern result; sfutest reports their error.",
    "sfu_pattern": "The table's signed-zero or tail conventions differ from the scalar ops.py contract; sfu_table_selftest checks the independent entries.",
    "checker": "A concurrent checker's contract is detection under its rule table, not a function of its operands; checkers_selftest and the fault campaign check it.",
}


PATTERN_SFU_FUNCTIONS = frozenset(("exp2", "exp", "log2", "log", "cos", "sigmoid", "recip", "rsqrt"))

def no_golden_reason(kind: str, family: str, pins: dict, width: int) -> str | None:
    """Return the declared gap for a point, if its kind has one."""
    if kind == "multiplier" and family == "truncated_fixed_width" and "correction" in pins:
        return NO_GOLDEN["truncated_multiplier_legacy"]
    if kind == "divider" and family in ("approximate_recurrence", "approximate_functional"):
        return NO_GOLDEN["approximate_divider"]
    if kind == "dot" and ((family == "integer_mac" and pins.get("element_op", "product") != "product") or
                          (family == "multi_term_fused_dot" and pins.get("term_source", "products") != "products") or
                          (family == "fused_two_term_dot" and pins.get("second_op", "dot2") != "dot2")):
        return NO_GOLDEN["dot_operation"]
    if kind == "sfu" and family in ("direct_lut", "compressed_lut"):
        supported = pins.get("_fn") in PATTERN_SFU_FUNCTIONS or (
            str(pins.get("_fmt", "")).startswith("posit") and pins.get("_fn") in ops.SFU_UNARY and pins.get("_fn") != "softplus")
        return None if supported else NO_GOLDEN["sfu_pattern"]
    for name, value in pins.items():
        if not name.endswith(".family"):
            continue
        if value == "end_around_carry":
            return NO_GOLDEN["nonbinary_slot"]
        if value in {"approximate_truncated", "segmented_carry_speculative", "lower_part_approximate", "accuracy_configurable",
                     "truncated_fixed_width", "logarithmic_mitchell", "approximate_compressor", "dynamic_segment", "operand_rounding",
                     "logarithmic", "pp_perforation", "approximate_compressor_tree", "approximate_booth"}:
            return NO_GOLDEN["approximate_slot"]
    if kind == "dot" and width == 8:
        return None
    return NO_GOLDEN.get(kind)


def _integer(pins, key, default):
    try:
        return int(pins.get(key, default))
    except (ValueError, TypeError):
        return default


def flagged_sum(a, b, width, minus=False):
    """Return the prefix flag output under cin == 0."""
    fmt = IntFormat(width, "unsigned")
    total = ops.int_ref("add", fmt, a, b)
    return ops.int_ref("sub" if minus else "add", fmt, total, 1)


def modular_sum(a, b, cin, width, pins):
    """Return the end-around sum and the carry named by its recirculation."""
    mask = (1 << width) - 1
    total = ops.int_ref("adc" if cin else "add", IntFormat(width, "unsigned"),
                        a, b, IntFormat(width + 2, "unsigned"))
    modulus = pins.get("modulus", "mod_2n_minus_1")
    cyclic = pins.get("recirculation", "cyclic_prefix_level") == "cyclic_prefix_level"
    if modulus == "generic_p_correction":
        return {"s": total % _integer(pins, "modulus_value", mask), "cout": total >> width}
    if modulus == "mod_2n_plus_1_diminished_one":
        return {"s": ((total + 1) % (mask + 2)) & mask,
                "cout": ((total + 1 if cyclic else total) >> width) & 1}
    return {"s": (total % mask or mask) if total else 0,
            "cout": ((a + b if cyclic else total) >> width) & 1}


def representation_value(positive, negative, width, carry_save=False):
    """Decode a carry-save or borrow-save pair into a binary word."""
    return ops.int_ref("add" if carry_save else "sub", IntFormat(width, "unsigned"), positive, negative)


def residue_value(residues, moduli):
    """Decode coprime residue channels by the Chinese remainder theorem."""
    from math import prod
    modulus = prod(moduli)
    return sum(r * (modulus // m) * pow(modulus // m, -1, m)
               for r, m in zip(residues, moduli, strict=True)) % modulus


@dataclass
class Adapter:
    ports: tuple[Port, ...]
    reference: Callable[[dict], dict] = field(repr=False)
    tolerance: Tolerance | None = None
    domains: dict[str, int] = field(default_factory=dict)
    constants: dict[str, int] = field(default_factory=dict)
    decimal: bool = False
    equal_operands: bool = False
    nonzero_divisor: bool = False
    normalize: Callable[[dict], dict] | None = field(default=None, repr=False)
    algorithm: Callable[[dict], dict] | None = field(default=None, repr=False)

    def stimulus(self, n, seed):
        """Return corner patterns followed by n seeded random patterns."""
        if n < 0:
            raise ValueError("n must be nonnegative")
        rng = random.Random(seed)
        inputs = [p for p in self.ports if p.direction == "input"]

        def limit(p):
            return self.domains.get(p.name, 1 << p.width)

        def clean(values):
            values = {p.name: values.get(p.name, 0) % limit(p) for p in inputs}
            values.update(self.constants)
            if self.nonzero_divisor and values.get("b") == 0:
                values["b"] = 1
            if self.decimal:
                for p in inputs:
                    if p.name in ("a", "b"):
                        values[p.name] = BCDFormat(p.width).encode(values[p.name])
            if self.equal_operands:
                values["b"] = values["a"]
            return self.normalize(values) if self.normalize else values

        patterns = [{p.name: v % limit(p) for p in inputs} for v in (0, 1, -1)]
        for p in inputs:
            for bit in range(p.width):
                for v in (1 << bit, (1 << bit) - 1, (limit(p) - 1) ^ (1 << bit)):
                    patterns.append({q.name: v if q == p else limit(q) - 1 for q in inputs})
        controls = [p for p in inputs if p.width <= 3 or p.name == "amt"]
        for p in controls:
            for v in range(min(limit(p), 512)):
                for a in (0, 1, -1):
                    pattern = {q.name: a % limit(q) for q in inputs}
                    pattern[p.name] = v
                    patterns.append(pattern)
        corners = list({tuple(clean(v).items()): clean(v) for v in patterns}.values())
        return corners + [clean({p.name: rng.randrange(limit(p)) for p in inputs}) for _ in range(n)]

    def expect(self, inputs):
        """Return every output pattern from the Python contract."""
        return self._checked(self.reference(inputs))

    def algorithm_expect(self, inputs):
        """Return exact algorithm outputs independently of the mathematical budget."""
        if self.algorithm is None:
            raise ValueError("this adapter has no independent algorithm contract")
        return self._checked(self.algorithm(inputs))

    def _checked(self, result):
        outputs = {p.name: p for p in self.ports if p.direction == "output"}
        if result.keys() != outputs.keys():
            raise ValueError(f"reference outputs {result.keys()} differ from ports {outputs.keys()}")
        for name, value in result.items():
            if not isinstance(value, int) or not 0 <= value < 1 << outputs[name].width:
                raise ValueError(f"{name}={value} exceeds {outputs[name].width} bits")
        return result


def _ports(inputs, outputs):
    return tuple(Port(n, d, w) for d, ps in (("input", inputs), ("output", outputs)) for n, w in ps)


def _mul_tolerance(family, pins, width, signed):
    bound = None
    relative = False
    minimum = 0
    scale = 1 << width
    if family in ("truncated_fixed_width", "approximate_booth"):
        bound = (2.5, 0.6) if family == "truncated_fixed_width" else (2.0, 0.5)
        if family == "truncated_fixed_width" and "correction" not in pins:
            kept = max(0, min(width, _integer(pins, "extra_columns_kept", 2)))
            # The omitted triangle has c + 1 terms of weight 2**c in column c.
            omitted = sum((c + 1) * (1 << c) for c in range(width - kept)) / (1 << width)
            bound = (max(2.5, omitted + 2), bound[1])
            if kept != 2 or pins.get("correction_scheme") == "none":
                bound = (bound[0], max(0.6, omitted / 4 + 1))
    elif family in ("logarithmic_mitchell", "logarithmic"):
        relative = True
        bound = (0.12, 0.05)
        correction = pins.get("correction", pins.get("correction_scheme"))
        if correction in ("combet_error_terms", "operand_decomposition"):
            bound = (0.12, 0.03)
        if correction == "nearest_one_rounding":
            bound = (0.15, 0.05)
        if correction == "iterative_residual":
            bound = (0.12, 0.02)
        if pins.get("base") == "mitchell_unbiased" or correction == "near_zero_bias_coefficients":
            bound = (0.2, 0.06)
        if pins.get("mantissa_adder") in ("truncated", "set_one_soa"):
            bound, minimum = (0.15, 0.05), 1 << (width + 2)
    elif family == "dynamic_segment" or (family == "approximate_compressor" and pins.get("technique") == "dynamic_segment"):
        relative, bound = True, (0.07, 0.02)
        if pins.get("segment_select") == "dynamic_leading_one_rounded":
            bound = (0.1, 0.03)
        if pins.get("segment_select") == "static_msb_or_lsb":
            kept = max(2, min(width, _integer(pins, "segment_width", 6)))
            scale = 1 << (2 * width - kept)
            relative, bound = False, (2.0, 0.5)
        if family == "dynamic_segment" and relative:
            kept = max(2, min(width, _integer(pins, "segment_width", 6)))
            operand_error = 2.0 ** (1 - kept)
            bound = (max(bound[0], 2 * operand_error + operand_error ** 2),
                     max(bound[1], operand_error))
    elif family == "operand_rounding":
        relative, bound = True, (0.13, 0.04)
        if pins.get("bias_correction") in (True, "True", 1):
            bound = (0.25, 0.12)
        if pins.get("rounding") == "nearest_pow2":
            bound = (1.0, 0.35)
    elif family == "pp_perforation":
        rows = max(0, min(width - 1, _integer(pins, "perforated_rows", 2)))
        bound = (max(3.5, float(1 << rows)), max(2.0, 2.0 ** (rows - 1) + 1))
        if pins.get("cell") == "kulkarni_2x2_inaccurate":
            cell_error = sum(2 << (i + j) for i in range(rows, width - 1, 2)
                             for j in range(0, width - 1, 2)) / scale
            bound = (bound[0] + cell_error, bound[1] + cell_error / 16)
        if pins.get("cell") == "awtm_band_forced_block":
            # The low band can carry at most half its partial-product count into the upper half.
            bound = (bound[0] + width / 2, bound[1] + width / 4)
    elif family == "approximate_compressor_tree":
        columns = max(0, min(2 * width - 1, _integer(pins, "approximate_columns", width)))
        scale = 1 << max(width, columns)
        # The affected columns contain at most width partial-product bits each.
        bound = (max(6.0, width + 1.0), 2.0)
    elif family == "approximate_compressor":
        bound = (1.0, 0.2) if pins.get("technique") in ("approximate_compressor", "configurable_error_recovery") else (4.0, 0.5)
    if family == "approximate_booth":
        columns = max(0, min(2 * width - 1, _integer(pins, "approx_encoder_columns", width // 2)))
        scale = 1 << max(width, columns)
        if columns > width // 2:
            bound = (max(2.0, width / 2), max(0.5, width / 8))
    return Tolerance(*bound, ("p",), scale, relative, signed, minimum) if bound else None


ROUNDING = ("RNE", "RTZ", "RDN", "RUP", "SR", "RAZ")


@dataclass(frozen=True)
class ValueFormat:
    """Supply an exact value to cvt_ref without rounding it into an intermediate format."""
    value: object

    def decode(self, bits):
        return self.value


def _fields(sp, sign, exponent, significand, sw, ew):
    return (((sp << 1 | sign) << ew | (exponent & ((1 << ew) - 1))) << sw) | significand


def round_ref(fmt, value, mode, word=0, sr_bits=8, ftz=False):
    """Round through cvt_ref, with the engine's finite-word stochastic decision for floats."""
    source = ValueFormat(value)
    if isinstance(fmt, PositFormat) or mode in ROUNDING[:4] or isinstance(value, Special):
        bits = ops.cvt_ref(source, 0, fmt, mode)
    elif mode == "RAZ":
        bits = ops.cvt_ref(source, 0, fmt, "RDN" if value < 0 else "RUP")
    else:
        low = ops.cvt_ref(source, 0, fmt, "RTZ")
        high = ops.cvt_ref(source, 0, fmt, "RDN" if value < 0 else "RUP")
        if low == high:
            bits = low
        else:
            lower = abs(fmt.decode(low))
            upper = fmt.decode(high)
            if isinstance(upper, Special):
                upper = Fraction(2) ** (fmt._top() - fmt.bias + 1)
            else:
                upper = abs(upper)
            probability = max(Fraction(0), min(Fraction(1), (abs(value) - lower) / (upper - lower)))
            threshold = int(probability * (1 << sr_bits))
            bits = high if threshold > word else low
    if ftz and isinstance(fmt, FloatFormat):
        magnitude = bits & ((1 << (fmt.width - 1)) - 1)
        if 0 < magnitude < 1 << fmt.man_bits:
            bits &= 1 << (fmt.width - 1)
    return bits



def unpack_ref(fmt, bits, sw, ew, daz=False, normalize=False):
    """Reference the V fields and denormal flag from the format's decoded value."""
    value = fmt.decode(bits)
    if value in (NAN, NAR):
        return _fields(1, 0, 0, 0, sw, ew)
    if value in (PINF, NINF):
        return _fields(2, int(value is NINF), 0, 0, sw, ew)
    if isinstance(fmt, PositFormat):
        if value == 0:
            return 0
        exponent = _floor_log2(abs(value)) - (fmt.width - 1)
        significand = int(abs(value) / Fraction(2) ** exponent)
        return _fields(0, int(value < 0), exponent, significand, sw, ew)
    exponent_field = (bits >> fmt.man_bits) & ((1 << fmt.exp_bits) - 1)
    mantissa = bits & ((1 << fmt.man_bits) - 1)
    denormal = exponent_field == 0 and mantissa != 0
    exponent = max(1, exponent_field) - fmt.bias - fmt.man_bits
    significand = mantissa + ((1 << fmt.man_bits) if exponent_field else 0)
    if daz and denormal:
        significand = 0
    if normalize:
        shift = ops.int_ref("clz", IntFormat(sw, "unsigned"), significand, 0)
        significand = ops.int_ref("shl", IntFormat(sw, "unsigned"), significand, shift)
        exponent -= shift
    sign = (bits >> (fmt.width - 1)) if fmt.signed else 0
    return (int(denormal) << (3 + ew + sw)) | _fields(0, sign, exponent, significand, sw, ew)



def pattern_sfu_ref(fn, fmt, bits):
    """Map the reciprocal's signed-zero input through the frozen SFU and negation ops."""
    result = ops.sfu_ref(fn, fmt, bits)
    if fn == "recip" and isinstance(fmt, FloatFormat) and fmt.signed and bits == 1 << (fmt.width - 1):
        result = ops.fp_ref("fneg", fmt, result, 0)
    return result


def golden(kind: str, family: str, pins: dict, width: int) -> Adapter | None:
    """Return a port adapter or a reason declared in NO_GOLDEN."""
    if no_golden_reason(kind, family, pins, width):
        return None
    if kind == "dot":
        from chialu.characterize import dot_geom
        geometry = dot_geom(width)
        element = IntFormat(geometry.intg[0])
        addend = IntFormat(geometry.intg[3])
        accumulator = IntFormat(geometry.AW)
        def dot(v):
            mask = (1 << element.width) - 1
            a = [(v["a"] >> (lane * element.width)) & mask for lane in range(geometry.n)]
            b = [(v["b"] >> (lane * element.width)) & mask for lane in range(geometry.n)]
            c = ops.cvt_ref(addend, v["c"], accumulator)
            return {"acc": ops.dot_ref(element, accumulator, a, b, c)}
        return Adapter(_ports([("a", geometry.n * element.width), ("b", geometry.n * element.width),
                               ("c", addend.width)], [("acc", geometry.AW)]), dot)
    if kind == "unpacker":
        from chialu.characterize import fp_geom
        fmt, _, geometry = fp_geom(width)
        return Adapter(_ports([("b", fmt.width), ("daz", 1)], [("u", geometry.VW + 1)]),
                       lambda v: {"u": unpack_ref(fmt, v["b"], geometry.SW, geometry.EW, bool(v["daz"]),
                                                 pins.get("denormal_handling", "in_unpack") == "in_unpack")})
    if kind == "sfu":
        fmt = parse_format(pins["_fmt"])
        return Adapter(_ports([("x", fmt.width)], [("y", fmt.width)]),
                       lambda v: {"y": pattern_sfu_ref(pins["_fn"], fmt, v["x"])})
    original_kind = kind
    if kind == "sd_adder":
        kind = "adder"
    elif kind.startswith("rns_"):
        kind = kind[4:]
    u = IntFormat(width, "unsigned")
    signed = bool(pins.get("_signed", True))
    fmt = IntFormat(width) if signed else u
    binary = [("a", width), ("b", width)]
    mask = (1 << width) - 1
    if kind in ("adder", "incrementer"):
        inputs = (binary if kind == "adder" else binary[:1]) + [("cin", 1)]
        outputs = [("s", width), ("cout", 1)]
        flagged = family == "compound_flagged_prefix"
        if flagged:
            outputs += [("s1", width)]
            if pins.get("outputs") == "sum_sum1_summinus1":
                outputs += [("sm1", width)]
        def add(v):
            a, b, cin = v["a"], v.get("b", 0), v["cin"]
            if family == "end_around_carry":
                return modular_sum(a, b, cin, width, pins)
            total = ops.int_ref("adc" if cin else "add", u, a, b, IntFormat(width + 1, "unsigned"))
            result = {"s": total & mask, "cout": total >> width}
            if flagged:
                result["s1"] = flagged_sum(a, b, width)
                if len(outputs) == 4:
                    result["sm1"] = flagged_sum(a, b, width, True)
            return result
        adapter = Adapter(_ports(inputs, outputs), add)
        if flagged:
            adapter.constants["cin"] = 0
        if family in ("approximate_truncated", "segmented_carry_speculative", "lower_part_approximate", "accuracy_configurable"):
            k = max(1, min(width - 1, _integer(pins, "lower_part_width", width // 2)))
            scale, bound = 1 << k, (2.0, 0.6)
            if family == "lower_part_approximate":
                k = max(1, min(width - 1, _integer(pins, "lower_width", 4)))
                scale, bound = 1 << k, (2.0, 1.0)
            if family == "segmented_carry_speculative":
                k = max(2, min(width, _integer(pins, "sub_adder_width", 4)))
                # Each omitted carry contributes at most one unit at its block boundary.
                scale = max(1, sum(1 << lo for lo in range(k, width, k)))
                bound = (1.0, 0.6)
            if family == "accuracy_configurable":
                modes = max(2, min(8, _integer(pins, "mode_count", 2)))
                k = max(2, (width + modes - 1) // modes)
                scale = max(1, sum(1 << lo for lo in range(k, width, k)))
                bound = (1.0, 0.6)
                if pins.get("reconfig_grain") == "truncation_width":
                    mode = max(0, min(modes - 1, _integer(pins, "operating_mode", modes // 2)))
                    scale = 1 << min(width, k * (modes - 1 - mode))
                    bound = (2.0, 1.0)
            adapter.tolerance = Tolerance(*bound, ("cout", "s"), scale)
            if family == "approximate_truncated":
                from chialu.verify.approximate_adder_algorithm import TruncatedAdder
                contract = TruncatedAdder.from_pins(width, pins)
                adapter.algorithm = lambda values: contract.evaluate(**values)
        return adapter
    if kind == "multiplier":
        def multiply(v):
            return {"p": ops.int_ref("mul_wide", fmt, v["a"], v["b"], IntFormat(2 * width, fmt.encoding))}
        adapter = Adapter(_ports(binary, [("p", 2 * width)]), multiply,
                          _mul_tolerance(family, pins, width, signed))
        if family == "truncated_fixed_width":
            from chialu.verify.truncated_multiplier_ref import configuration, product
            algorithm_pins = dict(pins)
            configuration(width, algorithm_pins)
            adapter.algorithm = lambda values: {"p": product(width, signed, algorithm_pins, values["a"], values["b"])}
        return adapter
    if kind == "divider":
        def divide(v):
            return {"q": ops.int_ref("div", u, v["a"], v["b"]), "r": ops.int_ref("rem", u, v["a"], v["b"])}
        return Adapter(_ports(binary, [("q", width), ("r", width)]), divide, nonzero_divisor=True)
    if kind == "comparator":
        def compare(v):
            bits = ops.int_ref("cmp", fmt, v["a"], v["b"])
            return {"lt": bits & 1, "eq": (bits >> 1) & 1}
        return Adapter(_ports(binary, [("lt", 1), ("eq", 1)]), compare)
    if kind in ("shifter", "rotator"):
        def shift(v):
            a, amt, op = v["a"], v["amt"], v["op"]
            operation = ("shl", "shr_logical", "shr_arith", "rol", "ror")[op]
            lost = (a >> (width - amt) if op == 0 else a & ((1 << amt) - 1)) if amt and op < 3 else 0
            return {"y": ops.int_ref(operation, u, a, amt),
                    "sticky": int(bool(lost) and pins.get("sticky_collect") in (True, "True", 1))}
        return Adapter(_ports([("a", width), ("amt", max(1, (width - 1).bit_length())), ("op", 3)],
                              [("y", width), ("sticky", 1)]), shift, domains={"amt": width, "op": 5})
    if kind in ("lzc", "bitcount"):
        operation = "popcount" if family == "popcount_counter_tree" else "ctz" if family == "trailing_zero" else "clz"
        return Adapter(_ports([("a", width)], [("n", width.bit_length())]),
                       lambda v: {"n": ops.int_ref(operation, u, v["a"], 0)})
    if kind == "logic":
        return Adapter(_ports(binary + [("op", 2)], [("y", width)]),
                       lambda v: {"y": ops.int_ref(("and", "or", "xor", "not")[v["op"]], u, v["a"], v["b"])})
    if kind.startswith("bcd_"):
        fmt = BCDFormat(width)
        operation = kind[4:]
        def decimal(v):
            a, b = v["a"], v["b"]
            if operation == "adder":
                sub, cin = v["sub"], v["cin"]
                op = ("sbb" if cin else "sub") if sub else ("adc" if cin else "add")
                total = fmt.decode(a) + (-fmt.decode(b) - cin if sub else fmt.decode(b) + cin)
                return {"s": ops.int_ref(op, fmt, a, b), "cout": int(total >= 0 if sub else total > fmt.max_int)}
            if operation == "multiplier":
                return {"p": ops.int_ref("mul_wide", fmt, a, b, BCDFormat(2 * width))}
            return {"q": ops.int_ref("div", fmt, a, b), "r": ops.int_ref("rem", fmt, a, b)}
        inputs = binary + ([("sub", 1), ("cin", 1)] if operation == "adder" else [])
        outputs = {"adder": [("s", width), ("cout", 1)], "multiplier": [("p", 2 * width)],
                   "divider": [("q", width), ("r", width)]}[operation]
        return Adapter(_ports(inputs, outputs), decimal, domains={"a": fmt.max_int + 1, "b": fmt.max_int + 1},
                       decimal=True, nonzero_divisor=operation == "divider")
    raise ValueError(f"undeclared golden kind: {original_kind}/{family}")


def divider_adapter(n, d, q, shift=0):
    """Reference the unsigned divider's domain of nonzero divisors and fitting quotients."""
    source = IntFormat(n + shift, "unsigned")
    def normalize(v):
        b = max(v["b"], 1 << max(0, shift - q + 1))
        v["b"] = min(b, (1 << d) - 1)
        v["a"] %= max(1, min(1 << n, (v["b"] << q) >> shift))
        return v
    def reference(v):
        a = v["a"] << shift
        return {"q": ops.int_ref("div", source, a, v["b"], IntFormat(q, "unsigned")),
                "r": ops.int_ref("rem", source, a, v["b"], IntFormat(d, "unsigned"))}
    return Adapter(_ports([("a", n), ("b", d)], [("q", q), ("r", d)]), reference,
                   nonzero_divisor=True, normalize=normalize)


def sqrt_adapter(width, normalized=False):
    """Reference an integer square root and its nonnegative remainder."""
    from math import isqrt
    def reference(v):
        root = isqrt(v["x"])
        return {"root": root, "rem": v["x"] - root * root}
    return Adapter(_ports([("x", 2 * width)], [("root", width), ("rem", width + 2)]), reference,
                   normalize=(lambda v: {"x": v["x"] | (1 << (2 * width - 2))}) if normalized else None)


def subword_adapter(width, lane_widths, signed=None):
    """Reference each selected lane and every carry at a finest-lane boundary."""
    selection_width = max(1, (max(2, len(lane_widths)) - 1).bit_length())
    fine = min(lane_widths)
    inputs = [("a", width), ("b", width)]
    if signed is None:
        inputs += [("cin", width // fine)]
    inputs += [("sel", selection_width)]
    outputs = [("p", 2 * width)] if signed is not None else [("s", width), ("cout", width // fine)]
    def reference(v):
        lw = lane_widths[v["sel"]]
        result = carries = carry = 0
        if signed is not None:
            fmt = IntFormat(lw, "twos_complement" if signed[v["sel"]] else "unsigned")
            for lo in range(0, width, lw):
                mask = (1 << lw) - 1
                product = ops.int_ref("mul_wide", fmt, (v["a"] >> lo) & mask, (v["b"] >> lo) & mask,
                                      IntFormat(2 * lw, fmt.encoding))
                result |= product << (2 * lo)
            return {"p": result}
        fmt = IntFormat(fine, "unsigned")
        for lo in range(0, width, fine):
            if lo % lw == 0:
                carry = (v["cin"] >> (lo // fine)) & 1
            mask = (1 << fine) - 1
            total = ops.int_ref("adc" if carry else "add", fmt, (v["a"] >> lo) & mask, (v["b"] >> lo) & mask,
                                IntFormat(fine + 1, "unsigned"))
            result |= (total & mask) << lo
            carry = total >> fine
            carries |= carry << (lo // fine)
        return {"s": result, "cout": carries}
    return Adapter(_ports(inputs, outputs), reference, domains={"sel": len(lane_widths)})
