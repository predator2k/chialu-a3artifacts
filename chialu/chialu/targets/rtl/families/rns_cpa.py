"""Decode selected EAC outputs for an ordinary unsigned binary CPA port.

The original end-around-carry module remains on the data path. Only its
modular encoding is removed; this does not recompute a+b in another CPA.
Generic-p conversion reconstructs the quotient from the original inputs
and uses the selected module's remainder and binary carry. Approximate
children still need a composed algorithm contract and an output error gate.
"""
from __future__ import annotations


MODULI = ('mod_2n_minus_1', 'mod_2n_plus_1_diminished_one')
RECIRCULATIONS = ('two_pass_prefix', 'cyclic_prefix_level', 'select_based')


def generic_modulus(pins, width):
    """Validate the generic-p geometry and its active choice domain."""
    from .fidelity import inactive
    if type(width) is not int or width < 2:
        raise ValueError('generic-p EAC needs at least two bits for p >= 3')
    value = pins.get('modulus_value', (1 << width) - 1)
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            raise ValueError('generic-p modulus_value must be an integer') from None
    if type(value) is not int or not 3 <= value < (1 << width):
        raise ValueError(f'generic-p modulus_value must satisfy 3 <= p < 2^{width}')
    if 'modulus_value' in pins and value > 4095:
        raise ValueError('explicit generic-p modulus_value is outside its declared Range(3, 4095)')
    inactive(pins, 'recirculation', 'generic-p uses complete conditional subtraction')
    for key in pins:
        if key.startswith('incrementer.'):
            inactive(pins, key, 'generic-p uses complete conditional subtraction')
    return value


def _bit(signal, width, index):
    return signal if width == 1 else f'{signal}[{index}]'


def _decrement(m, value, width, enable, out):
    """Conditional decrement as XOR/borrow decode of the selected result."""
    m.wire(out, width)
    for bit in range(width):
        borrow = enable if bit == 0 else f'({enable} & ~(|{value}[{bit-1}:0]))'
        m.assign(_bit(out, width, bit), f'{_bit(value, width, bit)} ^ {borrow}')
    return out


def raw_binary(m, family, pins, width, a, b, cin, s, cout, comment='', *, module=None):
    """Append a selected EAC plus its binary decode; return whether handled.

    Non-EAC families return False for the caller's ordinary installation
    path. The native generic-p module accepts the complete input range.
    """
    if family != 'end_around_carry':
        return False
    if type(width) is not int or width < 1:
        raise ValueError('RNS binary CPA adapter requires a positive integer width')
    pins = {} if pins is None else pins
    modulus = pins.get('modulus', 'mod_2n_minus_1')
    recirculation = pins.get('recirculation', 'cyclic_prefix_level')
    pmod = generic_modulus(pins, width) if modulus == 'generic_p_correction' else None
    if modulus not in (*MODULI, 'generic_p_correction') or recirculation not in RECIRCULATIONS:
        raise ValueError(f'unsupported EAC binary decode {modulus!r}/{recirculation!r}')
    from chialu.targets.rtl import families as FAM
    selected = module if module is not None else FAM.adder_module(family, pins, width)
    if selected is None:
        raise ValueError(f'selected EAC rejected the requested {width}-bit geometry')
    # Install directly rather than calling m.adder, which invokes this
    # adapter at every raw-binary call site after RNS integration.
    m.n += 1
    tag = f'rns_eac{m.n}'
    aw, bw = m.wire(tag + '_a', width, a), m.wire(tag + '_b', width, b)
    ci = m.wire(tag + '_cin', 1, cin)
    encoded = m.wire(tag + '_encoded_sum', width)
    encoded_carry = m.wire(tag + '_encoded_carry', 1)
    if selected.text:
        m.extra.append(selected.text)
    m.controls(selected.ctrl)
    params = ', '.join(f'.{key}({value})' for key, value in selected.params.items())
    controls = ''.join(f', .{port}({port})' for port, _ in selected.ctrl)
    instance = f'u{m.n}'
    m.raw(f'  // {comment}: selected EAC followed by binary encoding decode')
    m.raw(f'  {selected.name} ' + (f'#({params}) ' if params else '') +
          f'{instance} (.a({aw}), .b({bw}), .cin({ci}), .s({encoded}), .cout({encoded_carry}){controls});')
    if pmod is not None:
        # a=qa*p+ra, b=qb*p+rb and ra+rb+cin=k*p+r, k in {0,1}.
        # Therefore t=(qa+qb+k)*p+selected_r. These are explicit
        # quotient/remainder conversion operations, not another a+b CPA.
        qw = (((1 << width) - 1) // pmod).bit_length()
        rw = (pmod - 1).bit_length()
        partial_width = (2 * pmod - 1).bit_length()
        qsum_width = (2 * (((1 << width) - 1) // pmod) + 1).bit_length()
        qa = m.wire(tag + '_qa', qw, f"{aw} / {width}'d{pmod}")
        qb = m.wire(tag + '_qb', qw, f"{bw} / {width}'d{pmod}")
        ra = m.wire(tag + '_ra', rw, f"{aw} % {width}'d{pmod}")
        rb = m.wire(tag + '_rb', rw, f"{bw} % {width}'d{pmod}")
        partial = m.wire(tag + '_partial', partial_width, f'{ra} + {rb} + {ci}')
        quotient_carry = m.wire(tag + '_quotient_carry', 1, f"{partial} >= {partial_width}'d{pmod}")
        quotient = m.wire(tag + '_quotient', qsum_width, f'{qa} + {qb} + {quotient_carry}')
        coarse = m.wire(tag + '_coarse', width + 1, f"{quotient} * {width+1}'d{pmod}")
        decoded = m.wire(tag + '_decoded_sum', width + 1, f'{coarse} + {encoded}')
        raw_carry = m.wire(tag + '_raw_carry', 1, encoded_carry)
        m.assign(s, f'{decoded}[{width-1}:0]')
    elif modulus == 'mod_2n_minus_1':
        all_max = m.wire(tag + '_all_max', 1, f'(&{aw}) & (&{bw}) & {ci}')
        raw_carry = m.wire(tag + '_raw_carry', 1,
                           f'{encoded_carry} | ({ci} & (&({aw} ^ {bw})))')
        decoded = _decrement(m, encoded, width, raw_carry, tag + '_decoded_sum')
        # t=2**(W+1)-1 aliases t=2**W at the EAC output; original
        # input boundary information disambiguates this double wrap.
        m.assign(s, f'{all_max} ? {{{width}{{1\'b1}}}} : {decoded}')
    else:
        all_max = m.wire(tag + '_all_max', 1, f'(&{aw}) & (&{bw}) & {ci}')
        if recirculation == 'cyclic_prefix_level':
            inverse_a = m.wire(tag + '_inverse_a', width, f'~{aw}')
            complement = _decrement(m, inverse_a, width, ci, tag + '_complement')
            at_low_max = m.wire(tag + '_at_low_max', 1, f'({bw} == {complement}) & ~{all_max}')
            # Native cyclic cout names (t+1)[W], not t[W]. It rises
            # one code early and wraps at the all-ones input boundary.
            raw_carry = m.wire(tag + '_raw_carry', 1,
                               f'({encoded_carry} & ~{at_low_max}) | {all_max}')
        else:
            raw_carry = m.wire(tag + '_raw_carry', 1, encoded_carry)
        decrement = m.wire(tag + '_decrement', 1, f'~{raw_carry}')
        decoded = _decrement(m, encoded, width, decrement, tag + '_decoded_sum')
        m.assign(s, decoded)
    m.assign(cout, raw_carry)
    if not hasattr(m, 'cpa_contract_stats'):
        m.cpa_contract_stats = []
    m.cpa_contract_stats.append({'adapter': 'eac_to_binary', 'width': width,
                                'modulus': modulus, 'recirculation': recirculation,
                                'selected_module': selected.name, 'selected_instance': instance,
                                'encoded_sum': encoded, 'encoded_carry': encoded_carry,
                                'decoded_sum': decoded, 'raw_carry': raw_carry})
    if pmod is not None:
        m.cpa_contract_stats[-1].update(modulus_value=pmod, recirculation=None, quotient_width=qw,
                                      remainder_width=rw, conversion='quotient_remainder')
    return True
