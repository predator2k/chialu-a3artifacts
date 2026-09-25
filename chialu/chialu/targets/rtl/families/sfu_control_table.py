"""Generate value tables with rounding controls from independent function values."""
from fractions import Fraction
from math import floor, isqrt
import hashlib
import json

import mpmath

from chialu.verify.formats import FloatFormat, PositFormat, Special, NAN, NAR, PINF, NINF, _floor_log2
from chialu.verify.rounding import Rounder
from chialu.targets.rtl.engine import FLAG_ORDER, FW


def function_value(fn, fmt, bits, precision, sr_bits):
    """Evaluate a named function independently of verify.ops and verify.sfu_ref."""
    x = fmt.decode(bits)
    posit = isinstance(fmt, PositFormat)
    sign = int(not posit and getattr(fmt, "signed", True) and bits >> (fmt.width - 1))
    zero_sign = sign if fn in ("sin", "tanh", "erf", "gelu", "silu", "sqrt") else 0
    if x in (NAN, NAR):
        return NAN, {"invalid"}, zero_sign, False
    if x in (PINF, NINF):
        positive = x is PINF
        if fn in ("sin", "cos") or (not positive and fn in ("log", "log2", "sqrt", "rsqrt")):
            return NAN, {"invalid"}, zero_sign, False
        if fn in ("tanh", "erf"):
            return Fraction(1 if positive else -1), set(), zero_sign, False
        if fn == "sigmoid":
            return Fraction(int(positive)), set(), zero_sign, False
        if fn in ("recip", "rsqrt") or not positive:
            # IEEE 754-2019 section 6.3 gives a quotient the exclusive or of the operand signs,
            # so 1/(-inf) is -0. rsqrt reaches this with +inf alone, since a negative operand is
            # invalid above, and the other functions keep the zero sign they were given.
            zs = sign if fn == "recip" else zero_sign
            return Fraction(0), set(), zs, False
        return PINF, set(), zero_sign, False
    if fn in ("log", "log2", "recip", "rsqrt") and x == 0:
        # IEEE 754-2019 section 9.2.1: rSqrt(-0) is -inf, as sqrt(-0) is -0 and 1/(-0) is -inf,
        # so the sign of the zero carries into the infinity for recip and rsqrt alike.
        special = NAR if posit else (NINF if (fn in ("log", "log2") or sign) else PINF)
        return special, {"div_zero"}, zero_sign, False
    if fn in ("log", "log2", "sqrt", "rsqrt") and x < 0:
        return NAN, {"invalid"}, zero_sign, False
    if x == 0 and fn != "softplus":
        value = 1 if fn in ("exp", "exp2", "cos") else Fraction(1, 2) if fn == "sigmoid" else 0
        return Fraction(value), set(), zero_sign, False
    if fn == "recip":
        return 1 / x, set(), zero_sign, False
    if fn in ("sqrt", "rsqrt"):
        numerator, denominator = isqrt(x.numerator), isqrt(x.denominator)
        if numerator * numerator == x.numerator and denominator * denominator == x.denominator:
            root = Fraction(numerator, denominator)
            return root if fn == "sqrt" else 1 / root, set(), zero_sign, False
    if fn == "log" and x == 1:
        return Fraction(0), set(), zero_sign, False
    if fn == "log2" and not (x.numerator & (x.numerator - 1)) and not (x.denominator & (x.denominator - 1)):
        return Fraction(x.numerator.bit_length() - x.denominator.bit_length()), set(), zero_sign, False
    maximum = fmt.decode((1 << (fmt.width - 1)) - 1) if posit else fmt.max_finite()
    minimum = fmt.decode(1) if posit else fmt.min_positive()
    margin = abs(_floor_log2(minimum)) + abs(_floor_log2(maximum)) + sr_bits + 128
    epsilon = Fraction(2) ** -margin
    value = None
    if fn in ("exp", "exp2"):
        if x > margin:
            value = 4 * maximum
        elif x < -margin:
            value = minimum * epsilon
    elif fn == "softplus":
        if x > margin:
            value = x + epsilon
        elif x < -margin:
            value = minimum * epsilon
    elif fn == "sigmoid":
        if x > margin:
            value = 1 - epsilon
        elif x < -margin:
            value = minimum * epsilon
    elif fn in ("tanh", "erf") and abs(x) > margin:
        value = (1 - epsilon) * (1 if x > 0 else -1)
    elif fn in ("gelu", "silu"):
        if x > 2 * margin:
            value = x * (1 - epsilon)
        elif x < -2 * margin:
            value = -minimum * epsilon
    if value is not None:
        return value, set(), zero_sign, True
    if fn == "exp2" and x.denominator == 1:
        return Fraction(2) ** int(x), set(), zero_sign, False
    mp = mpmath.mp.clone()
    mp.prec = precision
    argument = mp.mpf(x.numerator) / x.denominator
    if fn == "exp2":
        result = mp.power(2, argument)
    elif fn == "log2":
        result = mp.log(argument, 2)
    elif fn == "rsqrt":
        result = 1 / mp.sqrt(argument)
    elif fn in ("sigmoid", "silu"):
        probability = mp.exp(argument) / (1 + mp.exp(argument)) if argument < 0 else 1 / (1 + mp.exp(-argument))
        result = probability if fn == "sigmoid" else argument * probability
    elif fn == "gelu":
        result = argument * mp.erfc(-argument / mp.sqrt(2)) / 2
    elif fn == "softplus":
        result = max(argument, 0) + mp.log1p(mp.exp(-abs(argument)))
    elif fn in ("exp", "log", "sin", "cos", "tanh", "sqrt", "erf"):
        result = getattr(mp, fn)(argument)
    else:
        raise ValueError(f"no scalar value-table function {fn!r}")
    # Values near an exact limit retain the side of every directed boundary.
    # This also prevents finite working precision from turning a tail exact.
    if result == 1 and fn in ("sigmoid", "tanh", "erf"):
        value = 1 - epsilon
    elif result == -1 and fn in ("tanh", "erf"):
        value = -1 + epsilon
    elif result == argument and fn in ("gelu", "silu", "softplus"):
        value = x + epsilon if fn == "softplus" else x * (1 - epsilon)
    else:
        negative, mantissa, exponent, _ = result._mpf_
        value = Fraction(int(mantissa)) * Fraction(2) ** int(exponent)
        if negative:
            value = -value
    return value, set(), zero_sign, True


def _cut(fmt, value, spec):
    if not isinstance(fmt, FloatFormat) or isinstance(value, Special) or value == 0 or (value < 0 and not fmt.signed):
        return None
    toward = fmt.round(value, "RTZ")
    away = fmt.round(value, "RUP" if value > 0 else "RDN")
    low, high = fmt.decode(toward), fmt.decode(away)
    if toward == away or isinstance(low, Special):
        return None
    spacing = abs(high) - abs(low) if not isinstance(high, Special) else fmt.ulp_at(toward)
    threshold = floor((abs(value) - abs(low)) * (1 << spec["sr_bits"]) / spacing)
    if spec.get("sr_compare", "gt") == "ge":
        threshold += 1
    return max(0, min(1 << spec["sr_bits"], threshold))


def _record(fn, fmt, bits, spec, precision):
    from chialu.verify.alu_ref import _nan_result
    value, initial_flags, sign, irrational = function_value(fn, fmt, bits, precision, spec["sr_bits"])
    def rounded(mode, word=0):
        rounder = Rounder(mode, spec["sr_bits"], spec.get("sr_compare", "gt"), spec.get("tininess", "after"))
        if isinstance(fmt, PositFormat):
            result, flags = rounder.posit(fmt, value)
        elif value in (NAN, NAR):
            operands = [bits] if fmt.decode(bits) is NAN else []
            result, flags = _nan_result(fmt, spec, operands)
        elif not fmt.signed and (value is NINF or (not isinstance(value, Special) and value < 0)):
            result, flags = _nan_result(fmt, spec, [], invalid_sign=1)
            flags.add("invalid")
        else:
            result, flags = rounder.float(fmt, value, word, sign)
        flags |= initial_flags
        if irrational:
            flags.add("inexact")
        return result | (sum(1 << index for index, name in enumerate(FLAG_ORDER) if name in flags) << fmt.width)
    limit = 1 << spec["sr_bits"]
    cuts = {0, limit}
    candidates = [fmt]
    if isinstance(fmt, FloatFormat) and not fmt.exp_only:
        candidates.append(FloatFormat("table_wide", fmt.exp_bits + 8, fmt.man_bits, True, True, fmt.signed))
    for candidate in candidates:
        cut = _cut(candidate, value, spec)
        if cut is not None:
            cuts.add(cut)
    cuts = sorted(cuts)
    outputs = [rounded(mode) for mode in ("RNE", "RTZ", "RDN", "RUP")]
    segments = [rounded("SR", first) for first in cuts[:-1]]
    for first, last, output in zip(cuts, cuts[1:], segments):
        if rounded("SR", last - 1) != output:
            raise ValueError("stochastic value-table interval has more than one output")
    if len(segments) > 3:
        raise ValueError("more stochastic output intervals than the table contract admits")
    boundaries = cuts[1:-1]
    while len(segments) < 3:
        segments.append(segments[-1])
        boundaries.append(limit)
    result = 0
    word_width = fmt.width + FW
    for index, output in enumerate(outputs + segments):
        result |= output << (index * word_width)
    for index, boundary in enumerate(boundaries):
        result |= boundary << (7 * word_width + index * (spec["sr_bits"] + 1))
    return result


def controlled_table(functions, fmt, family, spec):
    """One direct or base/delta table with live rounding and operand controls."""
    from chialu.targets.rtl.families import Module
    from chialu.targets.rtl.families.sfu import Net, PATTERN_MAX_BITS
    from chialu.targets.rtl.families.selection import register_origin
    from chialu.targets.rtl.families.fidelity import shared
    name, pins = family
    if fmt.width > PATTERN_MAX_BITS:
        raise ValueError(f"a value table needs a format of at most {PATTERN_MAX_BITS} bits")
    strategy = pins.get("sharing", "datapath_per_fn")
    if len(functions) > 1 and strategy == "shared_range_reduction":
        raise ValueError("pattern value tables have no range-reduction circuit to share")
    sb, width = int(spec["sr_bits"]), fmt.width
    minimum = fmt.decode(1) if isinstance(fmt, PositFormat) else fmt.min_positive()
    precision = int(pins.get("_table_precision", max(128, 2 * abs(_floor_log2(minimum)) + 4 * width + sb + 64)))
    signature = [functions, fmt.name, name, dict(pins), sb, spec.get("sr_compare"), spec.get("tininess"),
                 spec.get("invalid_result"), spec.get("nan_payload")]
    module = "fam_sfu_control_table_" + hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()[:16]
    row_width = 7 * (width + FW) + 2 * (sb + 1)
    function_bits = max(1, (len(functions) - 1).bit_length()) if len(functions) > 1 else 0
    rows = []
    for function in functions:
        for bits in range(1 << width):
            first = _record(function, fmt, bits, spec, precision)
            second = _record(function, fmt, bits, spec, 2 * precision)
            if first != second:
                raise ValueError(f"value-table output is undecided at {precision}/{2*precision} working bits: {function}/{fmt.name}/0x{bits:x}")
            rows.append(second)
    rows.extend([0] * ((1 << (width + function_bits)) - len(rows)))
    net = Net(module + "_data", f"{name} independently evaluated control records at {precision}/{2*precision} working bits")
    address = net.port_in("address", width + function_bits)
    if name == "direct_lut":
        data = net.rom(rows, address, row_width)
    elif name == "compressed_lut":
        low_bits = min(3, width - 1)
        high = net.bits(address, width + function_bits - 1, low_bits)
        bases = rows[::1 << low_bits]
        deltas = [value - bases[index >> low_bits] for index, value in enumerate(rows)]
        delta_width = max(2, max(abs(value) for value in deltas).bit_length() + 1)
        base = net.rom(bases, high, row_width)
        delta = net.rom(deltas, address, delta_width, True)
        data = net.bits(net.uns(net.add(net.sgn(base), net.ext(delta, row_width + 1))), row_width - 1, 0)
    else:
        raise ValueError(f"not a value-table family: {name}")
    net.port_out("data", data)
    is_float = isinstance(fmt, FloatFormat)
    denormal = (f"(x[{fmt.man_bits} +: {fmt.exp_bits}] == 0 && x[{fmt.man_bits-1}:0] != 0)"
                if is_float and not fmt.exp_only and fmt.man_bits else "1'b0")
    sign_zero = f"{{x[{width-1}], {{{width-1}{{1'b0}}}}}}" if is_float and fmt.signed else f"{width}'d0"
    subnormal_result = (f"(result[{fmt.man_bits} +: {fmt.exp_bits}] == 0 && result[{fmt.man_bits-1}:0] != 0)"
                        if is_float and not fmt.exp_only and fmt.man_bits else "1'b0")
    input_ports = f", input [{function_bits-1}:0] fn_sel" if function_bits else ""
    lookup_address = "{fn_sel, operand}" if function_bits else "operand"
    output_zero = f"{{result[{width-1}], {{{width-1}{{1'b0}}}}}}" if is_float and fmt.signed else f"{width}'d0"
    denormal_flag = 1 << FLAG_ORDER.index("denormal")
    flush_flags = (1 << FLAG_ORDER.index("inexact")) | (1 << FLAG_ORDER.index("underflow"))
    word_width = width + FW
    cutoff_offset = 7 * word_width
    text = net.render() + f"""
module {module}(input [{width-1}:0] x, input [2:0] rnd, input daz, ftz,
    input [{sb-1}:0] word{input_ports}, output [{width-1}:0] y, output [{FW-1}:0] flags);
  wire denormal = {denormal};
  wire [{width-1}:0] operand = daz && denormal ? {sign_zero} : x;
  wire [{row_width-1}:0] data;
  {net.name} table_data(.address({lookup_address}), .data(data));
  reg [{word_width-1}:0] result;
  always @* begin
    case (rnd)
      3'd0: result = data[0 +: {word_width}];
      3'd1: result = data[{word_width} +: {word_width}];
      3'd2: result = data[{2*word_width} +: {word_width}];
      3'd3: result = data[{3*word_width} +: {word_width}];
      default: begin
        if ({{1'b0,word}} < data[{cutoff_offset} +: {sb+1}]) result = data[{4*word_width} +: {word_width}];
        else if ({{1'b0,word}} < data[{cutoff_offset+sb+1} +: {sb+1}]) result = data[{5*word_width} +: {word_width}];
        else result = data[{6*word_width} +: {word_width}];
      end
    endcase
  end
  wire flush = ftz && {subnormal_result};
  assign y = flush ? {output_zero} : result[{width-1}:0];
  assign flags = result[{width} +: {FW}] | (denormal ? {FW}'d{denormal_flag} : {FW}'d0) | (flush ? {FW}'d{flush_flags} : {FW}'d0);
endmodule
"""
    register_origin(getattr(pins, "owner", "core"), name, pins, module, text)
    if function_bits:
        shared("core", strategy, [module], ["core"] + ["core.fn." + fn for fn in functions],
               detail="one physical table read port selected by fn_sel", origin_modules=[net.name])
    return Module(module, {}, text)
