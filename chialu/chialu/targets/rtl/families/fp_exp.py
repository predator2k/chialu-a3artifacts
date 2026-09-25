"""Structural rounding to an exponent-only floating format."""
from . import fp
from chialu.targets.rtl.engine import FW, flag_bit
from chialu.verify.formats import NAN


def round_sv(c, g, family, pins, tokens, name=None):
    XW, EW, XT, SB = g.XW, g.EW, g.XT, g.sr_bits
    name = name or f'fam_fp_exp_round_{family}_{c.name}_{g.tag()}{fp._tag(pins)}'
    m = fp.Mod(name, f'{family}: normalize and round to {c.name}, including exponent-field ties to even')
    for direction, port, width in [('input','x',XT),('input','rnd',3),('input','word',SB),('input','ftz',1),('output','fl',FW),('output','bits',c.width)]:
        m.port(direction,port,width)
    fp._x_fields(m,'x',g,'x_')
    m.wire('negative',expr='x_s' if c.signed else "1'b0")
    lf,lp=str(fp._pin(pins,'lzc.family','lzd_cell_tree')),fp._sub(pins,'lzc.')
    sf,sp=str(fp._pin(pins,'shifter.family','barrel_mux_tree')),fp._sub(pins,'shifter.')
    ef,ep=str(fp._pin(pins,'exp_adder.family','ripple_carry')),fp._sub(pins,'exp_adder.')
    xf,xp=str(fp._pin(pins,'exp_incrementer.family','prefix_and_incrementer')),fp._sub(pins,'exp_incrementer.')
    rf=str(fp._pin(pins,'round.family','increment_adder'))
    m.wire('already_rounded',expr="x_sp == 2'd3")
    m.wire('sticky',expr='x_st && !already_rounded')
    m.wire('lone',expr='x_sig == 0 && sticky')
    m.wire('sig_in',XW,expr=f'lone ? {XW}\'d1 : x_sig')
    fp._exp_const(m,ef,ep,EW,'x_e',-XW,'e_lone','weight of a lone sticky value')
    m.wire('e_in',EW,signed=True,expr='lone ? e_lone : x_e')
    fp._lzc(m,lf,lp,'sig_in',XW,'lz','leading bit of the value')
    lw=fp._clog2(XW)
    m.wire('amount',lw,expr=f'sig_in == 0 ? {lw}\'d0 : lz[{lw-1}:0]')
    fp._shift(m,sf,sp,'sig_in',XW,'amount',0,'sig','normalize the leading bit')
    m.wire('lzx',EW,expr=f'{{{{{EW-lw}{{1\'b0}}}}, amount}}')
    fp._exp_sub(m,ef,ep,EW,'e_in','lzx','e','normalization exponent adjustment')
    fp._exp_const(m,ef,ep,EW,'e',XW-1+c.bias,'base','biased exponent field before rounding')
    fp._incr(m,xf,xp,EW,'base',"1'b1",'next_code','','next exponent for the upper-range decision')
    m.wire('frac',XW,expr=f'sig & {XW}\'d{(1<<(XW-1))-1}')
    m.wire('half',XW,expr=f'{XW}\'d{1<<(XW-2)}')
    m.wire('tie',expr='frac == half && !sticky')
    m.wire('inexact',expr='frac != 0 || sticky || already_rounded')
    width=XW+SB+1
    m.wire('fraction_source',width,expr=f'{{1\'b0, frac, {SB}\'d0}}')
    fp._shift(m,sf,sp,'fraction_source',width,str(XW-1),1,'fraction','fraction of one power-of-two interval')
    compare='>=' if tokens.get('SRGE')=='1' else '>'
    m.wire('up',expr=f'already_rounded ? 1\'b0 : rnd == 0 ? (frac > half || (frac == half && (sticky || base[0]))) : rnd == 1 ? 1\'b0 : rnd == 2 ? (negative && inexact) : rnd == 3 ? (!negative && inexact) : rnd == 4 ? (inexact && fraction {compare} word) : inexact')
    if rf in ('increment_adder','compound_adder_select'):
        af,ap=str(fp._pin(pins,'round.incrementer.family','prefix_and_incrementer')),fp._sub(pins,'round.incrementer.')
        fp._incr(m,af,ap,EW,'base','up' if rf=='increment_adder' else "1'b1",'rounded','','the selected rounding incrementer')
        m.wire('code',EW,signed=True,expr='rounded' if rf=='increment_adder' else 'up ? rounded : base')
    elif rf=='flagged_prefix':
        af,ap=str(fp._pin(pins,'round.compound_adder.family','compound_flagged_prefix')),fp._sub(pins,'round.compound_adder.')
        m.wire('rounded',EW)
        m.inst('adder',af,ap,EW,f'.a(base), .b({EW}\'d0), .cin(1\'b0), .s(), .s1(rounded), .cout()', 'parallel next exponent from the flagged prefix')
        m.wire('code',EW,signed=True,expr='up ? rounded : base')
    elif rf=='injection':
        af,ap=str(fp._pin(pins,'round.injection_adder.family','ripple_carry')),fp._sub(pins,'round.injection_adder.')
        m.wire('sigw',XW+1,expr=f'{{1\'b0, sig}} | {{{XW}\'d0, sticky}}')
        m.wire('inject',XW+1,expr=f'rnd == 0 ? {XW+1}\'d{1<<(XW-2)} : (rnd == 3 && !negative) || (rnd == 2 && negative) || rnd == 5 ? {XW+1}\'d{(1<<(XW-1))-1} : 0')
        fp._adder(m,af,ap,XW+1,'sigw','inject','injected','inject below the normalized leading bit')
        m.wire('carry',expr=f'!already_rounded && injected[{XW}] && !(rnd == 0 && tie && !base[0])')
        m.wire('increment',EW,expr=f'{{{EW-1}\'d0, (rnd == 4 ? up : carry)}}')
        fp._adder(m,af,ap,EW,'base','increment','rounded','carry from the injected significand into the exponent field')
        m.wire('code',EW,signed=True,expr='rounded')
    else:
        raise ValueError(f'unknown exponent rounding family {rf}')
    top=c._top()
    m.wire('overflow',expr=f'up ? $signed(next_code) > {fp._slit(EW,top)} : $signed(base) > {fp._slit(EW,top)}')
    ni,ov,ix=flag_bit('nan'),flag_bit('overflow'),flag_bit('inexact')
    nan=c.encode_special(NAN) if c.has_nan else 0
    inf=c.emax_code if c.has_inf else top
    m.wire('zero',expr='x_sig == 0 && !sticky')
    m.wire('finite_flags',FW,expr=f'code < 0 ? (1 << {ix}) : overflow ? ((1 << {ix}) | (1 << {ov})) : (inexact ? (1 << {ix}) : 0) | ((inexact && code == {top}) ? (1 << {ov}) : 0)')
    m.assign('fl',f'x_sp == 1 ? (1 << {ni}) : x_sp == 2 ? {0 if c.has_inf else (1<<ix)|(1<<ov)} : zero ? (1 << {ix}) : finite_flags')
    inf_condition=f'{int(c.has_inf)} && (rnd == 0 || (rnd == 3 && !negative) || (rnd == 2 && negative) || rnd == 4 || rnd == 5)'
    magnitude = lambda value: f"{{negative, {c.exp_bits}'d{value}}}" if c.signed else f"{c.exp_bits}'d{value}"
    code = f"{{negative, code[{c.exp_bits-1}:0]}}" if c.signed else f"code[{c.exp_bits-1}:0]"
    m.assign('bits',f'x_sp == 1 ? {c.width}\'d{nan} : x_sp == 2 ? {magnitude(inf)} : zero ? 0 : code < 0 ? {magnitude(0)} : overflow ? ({inf_condition} ? {magnitude(inf)} : {magnitude(top)}) : {code}')
    return name,m.render()
