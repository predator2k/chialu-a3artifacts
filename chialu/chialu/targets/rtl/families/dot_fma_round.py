"""Post-normalization dual-sum rounding for the reduced-latency FMA.

The first CPA establishes the magnitude and its leading position. A bank
of compound CPAs receives the original aligned operands at every useful
rounding boundary. Normalization selects a bank; carry and GRS select its
sum or incremented sum. This trades area for keeping operand normalization
after the arithmetic, without replacing the dual sum by an add of zero.
"""
from .fp import ROUNDED, _clog2, _mkx, _slit


def post_normalization_dual_sum(m, dg, window_bits, exponent, magnitude, sign, negative,
                                left, right, subtraction, leading_zeros, unrounded,
                                *, topology='kogge_stone'):
    g, fmt = dg.g, dg.fd
    iw, xw, ew, ewx = window_bits+1, g.XW, g.EW, g.EW+3
    precision = fmt.man_bits+1
    padding = xw-precision
    maximum_cut = iw-precision
    if padding < 0 or maximum_cut < 2:
        raise ValueError('post-normalization dual sum requires an X word with target precision and guard bits')
    # a+b+subtraction is the magnitude computed by the first CPA. A
    # negative difference swaps its real operands before complementing.
    a = m.wire('pd_a', iw, expr=f'{negative} ? {right} : {left}')
    b = m.wire('pd_b', iw, expr=f'{subtraction} ? ~({negative} ? {left} : {right}) : {right}')
    cw = _clog2(iw)+1
    m.wire('pd_cut', cw, expr=f"{cw}'d{window_bits-fmt.man_bits} - {leading_zeros}")
    m.wire('pd_exp', ewx, signed=True,
           expr=f'{exponent} + {_slit(ewx, window_bits-xw)} - $signed({{1\'b0, {leading_zeros}}})')
    m.wire('pd_biased', ewx, signed=True,
           expr=f'pd_exp + {_slit(ewx, xw-1+fmt.bias)}')
    first_code = 0 if fmt.exp_only else 1
    last_code = fmt._top() if fmt.exp_only else (1 << fmt.exp_bits)-2
    m.wire('pd_eligible', expr=f"(|{magnitude}[{iw-1}:1]) && (pd_cut >= 2) && (pd_cut <= {cw}'d{maximum_cut}) "
           f"&& (pd_biased >= {first_code}) && (pd_biased <= {_slit(ewx, last_code)}) && (rnd != 3'd4)")
    outputs, increments, carries, low_carries = [], [], [], []
    for cut in range(2, maximum_cut+1):
        tag, high = f'pd_k{cut}', precision
        # Only the target P bits participate in the retained word modulo
        # 2**P. Higher operand bits cannot affect them; the final rounding
        # carry is recovered explicitly below. Do not construct a growing
        # full-width CPA at each otherwise equivalent boundary.
        ah = m.wire(tag+'_a', high, expr=f'{a}[{cut+precision-1}:{cut}]')
        bh = m.wire(tag+'_b', high, expr=f'{b}[{cut+precision-1}:{cut}]')
        low_carry = m.wire(tag+'_cin', expr=f'{a}[{cut}] ^ {b}[{cut}] ^ {magnitude}[{cut}]')
        # sum_i = a_i XOR b_i XOR carry_i recovers the true low carry.
        # Every compound candidate below still adds the two real operands.
        for suffix in ('s0', 's1', 's2'):
            m.wire(tag+'_'+suffix, high)
        m.wire(tag+'_cout')
        m.wire(tag+'_cout2')
        m.inst('adder', 'compound_flagged_prefix', {'topology': topology}, high,
               f'.a({ah}), .b({bh}), .cin(1\'b0), .s({tag}_s0), .cout({tag}_cout), .s1({tag}_s1)',
               f'post-normalization compound CPA at rounding cut {cut}')
        m.inst('incr', 'prefix_and_incrementer', {}, high,
               f'.a({tag}_s1), .cin(1\'b1), .s({tag}_s2), .cout({tag}_cout2)',
               f'cut {cut}: candidate for simultaneous low carry and rounding increment')
        m.wire(tag+'_down', high, expr=f'{low_carry} ? {tag}_s1 : {tag}_s0')
        m.wire(tag+'_up', high, expr=f'{low_carry} ? {tag}_s2 : {tag}_s1')
        m.wire(tag+'_guard', expr=f'{magnitude}[{cut-1}]')
        m.wire(tag+'_sticky', expr=f'|{magnitude}[{cut-2}:0]')
        m.wire(tag+'_inexact', expr=f'{tag}_guard | {tag}_sticky')
        kept_lsb = tag+'_down' if precision == 1 else tag+'_down[0]'
        tie_lsb = 'pd_biased[0]' if fmt.exp_only else kept_lsb
        # the engine's codes: 0 nearest even, 1 toward zero, 2 toward negative infinity, 3 toward positive infinity,
        # 5 away from zero (the checker's window copy); 4 is the stochastic mode, which leaves unrounded
        m.wire(tag+'_increment', expr=
               f"(rnd == 3'd0) ? ({tag}_guard && ({tag}_sticky || {tie_lsb})) : "
               f"(rnd == 3'd2) ? ({tag}_inexact && {sign}) : (rnd == 3'd3) ? ({tag}_inexact && !{sign}) : "
               f"(rnd == 3'd5) ? {tag}_inexact : 1'b0")
        m.wire(tag+'_keep', high, expr=f'{tag}_increment ? {tag}_up : {tag}_down')
        # For P=1 the incremented compound candidate wraps 1 to 0.
        # Consume that real output in the exponent-carry decision; the
        # output is not a dummy significand discarded by the packer.
        m.wire(tag+'_carry', expr=(f'{tag}_increment && {tag}_down && !{tag}_up' if precision == 1 else
                                  f"{tag}_increment && (&{tag}_down[{precision-1}:0])"))
        kept_word = tag+'_keep' if precision == 1 else f'{tag}_keep[{precision-1}:0]'
        kept = f"{{{kept_word}, {padding}'d0}}" if padding else kept_word
        m.wire(tag+'_sig', xw, expr=f"{tag}_carry ? ({xw}'d1 << {xw-1}) : {kept}")
        m.wire(tag+'_ewide', ewx, signed=True,
               expr=f"pd_exp + ({tag}_carry ? {ewx}'sd1 : {ewx}'sd0)")
        m.wire(tag+'_e', ew, signed=True, expr=f'{tag}_ewide[{ew-1}:0]')
        m.wire(tag+'_special', 2, expr=f"{tag}_inexact ? {ROUNDED} : 2'd0")
        outputs.append(m.wire(tag+'_y', g.XT,
                             expr=_mkx(g, tag+'_special', sign, tag+'_e', tag+'_sig', "1'b0")))
        increments.append(tag+'_increment')
        carries.append(tag+'_carry')
        low_carries.append(low_carry)
    def choose(values, default):
        return ' : '.join(f"(pd_cut == {cw}'d{cut}) ? {value}" for cut, value in enumerate(values, 2))+' : '+default
    m.wire('pd_increment', expr=choose(increments, "1'b0"))
    m.wire('pd_carry', expr=choose(carries, "1'b0"))
    m.wire('pd_low_carry', expr=choose(low_carries, "1'b0"))
    m.wire('pd_candidate', g.XT, expr=choose(outputs, unrounded))
    return m.wire('y_pd', g.XT, expr=f'pd_eligible ? pd_candidate : {unrounded}')
