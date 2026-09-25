"""Round across the finite-value gap around an infinity-only encoding."""


def correction(module, fmt, geom, srge, code_width):
    width, mantissa = geom.XW, fmt.man_bits
    fractional = width - mantissa - 1
    if fractional < max(1, geom.sr_bits):
        raise ValueError("infinity-only rounding needs enough retained fraction bits for the stochastic word")
    hole = fmt.emax_code << mantissa
    module.wire("hole_hit", expr=f"code == {code_width}'d{hole}")
    high_exponent = fmt.emax_code - fmt.bias - width + 1
    module.wire("hole_above", expr=f"e == {geom.EW}'sd{high_exponent}" if high_exponent >= 0 else
                f"e == -{geom.EW}'sd{-high_exponent}")
    lower = f"sig[{fractional-2}:0], 1'b0" if fractional > 1 else "1'b0"
    above = f"{{sig[{fractional-1}], ~sig[{fractional-1}], {lower}}}"
    module.wire("hole_delta", fractional + 2, expr=f"hole_above ? {above} : {{2'b0, sig[{fractional-1}:0]}}")
    numerator_width = geom.sr_bits + 2
    module.wire("hole_numerator", numerator_width, expr=f"hole_delta >> {fractional-geom.sr_bits}")
    module.wire("hole_quotient", numerator_width)
    module.wire("hole_remainder0", 2, expr="2'd0")
    for step, bit in enumerate(reversed(range(numerator_width))):
        remainder = f"hole_remainder{step}"
        digit = f"hole_numerator[{bit}]"
        module.assign(f"hole_quotient[{bit}]", f"{remainder}[1] || ({remainder}[0] && {digit})")
        module.wire(f"hole_remainder{step+1}", 2,
                    expr=f"{remainder}[1] ? {{{digit}, ~{digit}}} : {remainder}[0] ? {{~{digit}, 1'b0}} : {{1'b0, {digit}}}")
    module.wire("hole_up", expr=f"rnd == 0 ? (hole_delta >= {fractional+2}'d{3 << (fractional-1)}) : "
                f"rnd == 1 ? 1'b0 : rnd == 2 ? s : rnd == 3 ? !s : rnd == 4 ? "
                f"({srge} ? hole_quotient >= word : hole_quotient > word) : 1'b1")
    magnitude_width = fmt.exp_bits + mantissa
    magnitude = f"(hole_up ? {magnitude_width}'d{hole+1} : {magnitude_width}'d{hole-1})"
    result = f"{{s, {magnitude}}}" if fmt.signed else magnitude
    module.wire("hole_bits", fmt.width, expr=result)
    return "hole_hit", "hole_bits"
