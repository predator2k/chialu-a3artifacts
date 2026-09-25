"""Fuse product rounding with an exact fractional block-scale remainder."""
from . import fp
from chialu.verify.formats import FloatFormat


def mul_sv(g, pins, scale_format, target_format, name=None, tokens=None):
    XW, EW, XT, SW, SB = g.XW, g.EW, g.XT, g.SW, g.sr_bits
    PW, SM = 2 * SW, scale_format.man_bits + 1
    floating = isinstance(target_format, FloatFormat)
    M = target_format.man_bits if floating else target_format.width
    bias = target_format.bias if floating else 0
    DW = PW + SM + M + SB + 6
    name = name or f'fam_block_fused_{target_format.name}_{scale_format.name}_{g.tag()}{fp._tag(pins)}'
    m = fp.Mod(name, 'selected product and injection CPA with an exact block-scale quotient/remainder')
    for direction, port, width in [('input', 'xa', XT), ('input', 'xb', XT), ('input', 'rnd', 3),
                                   ('input', 'word', SB), ('input', 'scale_exp', EW), ('input', 'scale_sig', SM),
                                   ('input', 'scale_sp', 2), ('output', 'y', XT), ('output', 'raw_y', XT)]:
        m.port(direction, port, width)
    raw_pins = {key: value for key, value in pins.items() if key.startswith(('sig_mul.', 'exp_adder.'))}
    raw_name, raw_text = fp.mul_sv(g, 'sig_mul_then_round', raw_pins, name=name + '_product')
    m.extra.append(raw_text)
    m.raw(f'  {raw_name} product (.xa(xa), .xb(xb), .y(raw_y));')
    fp._x_fields(m, 'raw_y', g, 'r_')
    m.wire('p', PW, expr=f'r_sig[{PW-1}:0]')
    lf, lp = str(fp._pin(pins, 'lzc.family', 'lzd_cell_tree')), fp._sub(pins, 'lzc.')
    ef, ep = str(fp._pin(pins, 'exp_adder.family', 'ripple_carry')), fp._sub(pins, 'exp_adder.')
    af, ap = str(fp._pin(pins, 'injection_adder.family', 'ripple_carry')), fp._sub(pins, 'injection_adder.')
    fp._lzc(m, lf, lp, 'p', PW, 'plz', 'leading position of the exact product')
    fp._lzc(m, lf, lp, 'scale_sig', SM, 'slz', 'leading position of the selected scale significand')
    m.wire('plead', EW, signed=True, expr=f'{EW}\'sd{PW-1} - $signed({{1\'b0, plz}})')
    m.wire('slead', EW, signed=True, expr=f'{EW}\'sd{SM-1} - $signed({{1\'b0, slz}})')
    fp._exp_sub(m, ef, ep, EW, 'plead', 'slead', 'lead0', 'leading exponent estimate of product/scale')
    m.wire('pwide', DW, expr=f'{{{{{DW-PW}{{1\'b0}}}}, p}}')
    m.wire('swide', DW, expr=f'{{{{{DW-SM}{{1\'b0}}}}, scale_sig}}')
    m.wire('lead_below', expr='lead0[$high(lead0)] ? (pwide << (-$signed(lead0))) < swide : pwide < (swide << lead0)')
    m.wire('adjust', EW, expr=f'{{{EW-1}\'d0, lead_below}}')
    fp._exp_sub(m, ef, ep, EW, 'lead0', 'adjust', 'lead', 'exact leading exponent of the rational significand')
    fp._exp_sub(m, ef, ep, EW, 'r_e', 'scale_exp', 'weight', 'product exponent relative to the scale')
    fp._exp_add(m, ef, ep, EW, 'weight', 'lead', 'eu', 'exponent of the scaled product')
    if floating:
        m.wire('unit_e', EW, signed=True, expr=f'$signed(eu) < {fp._slit(EW, 1-bias)} ? {fp._slit(EW, 1-bias-M)} : $signed(eu) - {EW}\'sd{M}')
    else:
        m.wire('unit_e', EW, signed=True, expr=fp._slit(EW, -getattr(target_format, 'frac_bits', 0)))
    fp._exp_sub(m, ef, ep, EW, 'weight', 'unit_e', 'shift', 'numerator/denominator alignment at the rounding bit')
    m.wire('negative_shift', expr=f'shift[{EW-1}]')
    m.wire('distance', EW, expr='negative_shift ? -$signed(shift) : shift')
    m.wire('below', expr=f'negative_shift && distance >= {EW}\'d{DW-1}')
    m.wire('n0', DW, expr=f'negative_shift ? pwide : distance >= {EW}\'d{DW-PW} ? ({DW}\'d1 << {DW-1}) : pwide << distance')
    m.wire('d0', DW, expr=f'below ? ({DW}\'d1 << {DW-1}) : negative_shift ? swide << distance : swide')
    if pins.get('sticky_method', 'post_cpa_or_tree') == 'input_trailing_zero_count':
        tf, tp = str(fp._pin(pins, 'tzc.family', 'trailing_zero')), fp._sub(pins, 'tzc.')
        for port, value, width in [('a', f'xa[{SW}:1]', SW), ('b', f'xb[{SW}:1]', SW), ('s', 'scale_sig', SM)]:
            m.wire(f'tz{port}', width.bit_length())
            m.inst('tzc', tf, tp, width, f'.a({value}), .n(tz{port})', f'{port}: remove common powers of two before scale division')
        m.wire('ntz', EW, expr='tza + tzb + (negative_shift ? 0 : distance)')
        m.wire('dtz', EW, expr='tzs + (negative_shift ? distance : 0)')
        m.wire('common', EW, expr='below ? 0 : ntz < dtz ? ntz : dtz')
        m.wire('n', DW, expr='n0 >> common')
        m.wire('d', DW, expr='d0 >> common')
    else:
        m.wire('n', DW, expr='n0')
        m.wire('d', DW, expr='d0')
    m.wire('q', DW, expr='d == 0 ? 0 : n / d')
    m.wire('rem', DW, expr='d == 0 ? 0 : n % d')
    m.wire('inexact', expr='rem != 0 || r_st')
    m.wire('twice', DW + 1, expr="{rem, 1'b0}")
    m.wire('tie', expr="twice == {1'b0, d} && d != 0")
    m.wire('inject', DW, expr="rnd == 0 ? d >> 1 : (rnd == 2 && r_s) || (rnd == 3 && !r_s) ? d - 1'b1 : 0")
    m.wire('nx', DW + 1, expr="{1'b0, n}")
    m.wire('ix', DW + 1, expr="{1'b0, inject}")
    fp._adder(m, af, ap, DW + 1, 'nx', 'ix', 'injected', 'inject the rounding interval into the exact numerator')
    m.wire('qi', DW + 1, expr='d == 0 ? 0 : injected / d')
    m.wire('nearest', DW + 1, expr=f'rnd == 0 && tie ? {{qi[{DW}:1], 1\'b0}} : qi')
    m.wire('fraction_n', DW + SB, expr=f'{{rem, {SB}\'d0}}')
    m.wire('fraction', DW + SB, expr='d == 0 ? 0 : fraction_n / d')
    compare = '>=' if (tokens or {}).get('SRGE') == '1' else '>'
    m.wire('sr_up', expr=f'inexact && fraction {compare} word')
    m.wire('qwide', DW + 1, expr="{1'b0, q}")
    m.wire('upwide', DW + 1, expr=f'{{{DW}\'d0, sr_up}}')
    fp._adder(m, af, ap, DW + 1, 'qwide', 'upwide', 'stochastic', 'stochastic injection from the exact rational remainder')
    m.wire('rounded', DW + 1, expr='rnd == 4 ? stochastic : nearest')
    if floating:
        m.wire('reconstructed', XW, expr='rounded * scale_sig')
    else:
        maximum = 1 << (M + 1)
        m.wire('bounded', M + 2, expr=f'$signed(eu) >= {fp._slit(EW, M+1-getattr(target_format, "frac_bits", 0))} || rounded > {DW+1}\'d{maximum} ? {M+2}\'d{maximum} : rounded[{M+1}:0]')
        m.wire('reconstructed', XW, expr='bounded * scale_sig')
    fp._exp_add(m, ef, ep, EW, 'unit_e', 'scale_exp', 'result_e', 'restore the block-scale exponent after rounding')
    finite = fp._mkx(g, 'inexact ? 2\'d3 : 2\'d0', 'r_s', 'result_e', 'reconstructed', "1'b0")
    zero = fp._mkx(g, "2'd0", 'r_s', "0", "0", "1'b0")
    if floating and target_format.has_inf and not target_format.has_nan and M:
        boundary = target_format.emax_code - target_format.bias - M
        m.wire('hole_result', expr=f'(unit_e == {fp._slit(EW,boundary)} && rounded == {DW+1}\'d{1<<M}) || '
                                  f'(unit_e == {fp._slit(EW,boundary-1)} && rounded == {DW+1}\'d{1<<(M+1)})')
        finite = f'hole_result ? raw_y : {finite}'
    m.assign('y', f'r_sp != 0 ? raw_y : scale_sp != 0 || p == 0 ? {zero} : {finite}')
    return name, m.render()
