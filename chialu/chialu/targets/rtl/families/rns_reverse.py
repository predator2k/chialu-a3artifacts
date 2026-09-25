"""Exact RNS reconstruction with distinct ROM and arithmetic paths.

CRT-I uses adjacent differences whose coefficients telescope modulo each
channel. CRT-II reconstructs two actual subgroups, including a 1+2 split
for three channels, and joins them by an inverse modulo the second group.
Inputs are canonical residues; all intermediate bounds follow that domain.
"""
from __future__ import annotations

import math

from . import redundant as R
from .selection import copy_pins

ALGORITHMS = ('crt', 'mixed_radix', 'new_crt_i', 'new_crt_ii')
IMPLEMENTATIONS = ('rom', 'adder_based')


def _configuration(cfg):
    result = dict(cfg or {})
    result.setdefault('adder_family', 'ripple_carry')
    result['adder_pins'] = copy_pins(result.get('adder_pins'))
    result.setdefault('rev_impl', 'adder_based')
    if result['rev_impl'] not in IMPLEMENTATIONS:
        raise ValueError(f"unsupported RNS reverse implementation {result['rev_impl']!r}")
    if not isinstance(result['adder_family'], str) or not result['adder_family']:
        raise ValueError('RNS reverse conversion requires a concrete modular_adder family')
    return result


def _moduli(ms):
    moduli = tuple(ms)
    if not moduli or any(type(value) is not int or value < 2 for value in moduli):
        raise ValueError('RNS moduli must be integers greater than one')
    if any(math.gcd(a, b) != 1 for index, a in enumerate(moduli) for b in moduli[index + 1:]):
        raise ValueError('RNS reconstruction requires pairwise-coprime moduli')
    return moduli


def _record(m, **entry):
    if not hasattr(m, 'reverse_stats'):
        m.reverse_stats = []
    m.reverse_stats.append(entry)
    return entry


def _resize(signal, width, target):
    if width == target:
        return signal
    if width < target:
        return f"{{{{{target-width}{{1'b0}}}}, {signal}}}"
    return f'{signal}[{target-1}:0]'


def _slice(signal, width, low, bits):
    return signal if width == 1 else f'{signal}[{low+bits-1}:{low}]'


def _install(m, child, inputs, out, width):
    m.extra.append(child.render())
    m.controls(child.control_ports.items())
    m.reduction_stats.extend(dict(entry, scope=f'{m.name}.u_{out}',
                                  child_scope=entry.get('scope', child.name))
                             for entry in child.reduction_stats)
    for entry in getattr(child, 'reverse_stats', ()):
        _record(m, **dict(entry, scope=f'{m.name}.u_{out}',
                         child_scope=entry.get('scope', child.name)))
    m.wire(out, width)
    connections = [f'.{name}({value})' for name, value in inputs.items()]
    connections.append(f'.y({out})')
    connections += [f'.{name}({name})' for name in child.control_ports]
    m.raw(f"  {child.name} u_{out} ({', '.join(connections)});")
    return out


def _add(m, a, b, width, out, cfg, *, carry="1'b0"):
    value, cout = m.wire(out, width), m.wire(out + '_carry', 1)
    m.adder(cfg['adder_family'], cfg['adder_pins'], width, a, b, carry, value, cout,
            'RNS reverse conversion through the selected CPA')
    return value


def _difference(m, a, aw, a_max, b, bw, b_max, modulus, out, cfg):
    # One target modulus need not exceed the source digit. Add enough
    # multiples to make every canonical subtraction nonnegative.
    pad = ((b_max + modulus - 1) // modulus) * modulus
    maximum = a_max + pad
    minimum = pad - b_max
    width = max(1, maximum.bit_length(), aw, bw)
    positive = _add(m, _resize(a, aw, width), f"{width}'d{pad}", width, out + '_positive', cfg)
    inverse_b = m.wire(out + '_inverse_b', width, f'~{_resize(b, bw, width)}')
    value = _add(m, positive, inverse_b, width, out, cfg, carry="1'b1")
    _record(m, kind='nonnegative_difference', stage=out, modulus=modulus, pad=pad,
            minuend_maximum=a_max, subtrahend_maximum=b_max, minimum=minimum, maximum=maximum, width=width)
    return value, width, minimum, maximum


def _rom_bank(m, x, width, coefficient, modulus, shift, out, minimum, maximum):
    result_bits = (modulus - 1).bit_length()
    weight = (coefficient * (1 << shift)) % modulus
    name = f'fam_rns_reverse_rom_m{modulus}_c{coefficient}_s{shift}_w{width}'
    bank = R.Mod(name, f'input logic [{width-1}:0] x, output logic [{result_bits-1}:0] y',
                 f'ROM: (digit * {coefficient} * 2^{shift}) mod {modulus}')
    bank.raw(f'  localparam integer INPUT_BITS = {width}, RESULT_BITS = {result_bits}, SHIFT = {shift};')
    bank.raw(f"  localparam [{result_bits}:0] MODULUS = {result_bits+1}'d{modulus};")
    bank.raw(f"  localparam [{result_bits-1}:0] COEFFICIENT = {result_bits}'d{coefficient};")
    bank.raw('  always_comb begin\n    case (x)')
    values = [(digit * weight) % modulus for digit in range(1 << width)]
    for digit, value in enumerate(values):
        bank.raw(f"      {width}'d{digit}: y = {result_bits}'d{value};")
    bank.raw("      default: y = 'x;\n    endcase\n  end")
    _install(m, bank, {'x': x}, out, result_bits)
    first, last = minimum >> shift, maximum >> shift
    addresses = (list(range(1 << width)) if last - first + 1 >= (1 << width) else
                 sorted({value & ((1 << width) - 1) for value in range(first, last + 1)}))
    return _record(m, kind='rom_bank', stage=out, module=name, instance='u_' + out,
                   input_bits=width, result_bits=result_bits, coefficient=coefficient,
                   modulus=modulus, shift=shift, reachable_addresses=addresses,
                   variable=any(values[digit] != values[addresses[0]] for digit in addresses),
                   nonidentity=any(values[digit] != digit for digit in addresses))


def _mod_sum(m, terms, modulus, out, cfg):
    rows, level = list(terms), 0
    while len(rows) > 1:
        following = [R._mod_add(m, rows[index], rows[index + 1], "1'b0", modulus,
                                f'{out}_level{level}_{index//2}', cfg,
                                f'reverse modular sum {out}, level {level}')
                     for index in range(0, len(rows) - 1, 2)]
        if len(rows) % 2:
            following.append(rows[-1])
        rows = following
        level += 1
    return m.wire(out, (modulus - 1).bit_length(), rows[0] if rows else "'0")


def const_mod_product(m, x, xw, coefficient, modulus, out, cfg, *, minimum=0, maximum=None):
    """x*C mod modulus: complete <=8-bit ROM banks or arithmetic CPAs."""
    cfg = _configuration(cfg)
    if type(xw) is not int or xw < 1 or type(modulus) is not int or modulus < 2:
        raise ValueError('invalid constant-product geometry')
    if type(coefficient) is not int:
        raise ValueError('RNS constant-product coefficient must be an integer')
    maximum = (1 << xw) - 1 if maximum is None else maximum
    if type(maximum) is not int or type(minimum) is not int or not 0 <= minimum <= maximum < (1 << xw):
        raise ValueError('constant-product range does not fit its input width')
    coefficient %= modulus
    width = (modulus - 1).bit_length()
    argument = m.wire(out + '_input', xw, x)
    stats = dict(kind='constant_mod_product', stage=out, implementation=cfg['rev_impl'],
                 input_bits=xw, input_minimum=minimum, input_maximum=maximum, result_bits=width,
                 coefficient=coefficient, modulus=modulus)
    if coefficient == 0 or maximum == 0:
        _record(m, **stats, bypass='zero', banks=0)
        return m.wire(out, width, f"{width}'d0")
    if coefficient == 1 and maximum < modulus:
        _record(m, **stats, bypass='identity', banks=0)
        return m.wire(out, width, _resize(argument, xw, width))
    if cfg['rev_impl'] == 'rom':
        rows, records, zero_banks = [], [], 0
        for low in range(0, xw, 8):
            bits = min(8, xw - low)
            weight = (coefficient * (1 << low)) % modulus
            if not weight or not (maximum >> low):
                zero_banks += 1
                continue
            name = f'{out}_bank{low//8}'
            records.append(_rom_bank(m, _slice(argument, xw, low, bits), bits, coefficient,
                                     modulus, low, name, minimum, maximum))
            rows.append(name)
        _record(m, **stats, bypass=None, banks=len(records), omitted_zero_banks=zero_banks,
                nonidentity_banks=sum(r['nonidentity'] and r['variable'] for r in records))
        return _mod_sum(m, rows, modulus, out, cfg)
    product_maximum = maximum * coefficient
    product_width = max(xw, product_maximum.bit_length(), 1)
    if xw == 1:
        product = m.wire(out + '_product', product_width,
                         f"{argument} ? {product_width}'d{coefficient} : {product_width}'d0")
    else:
        product = R._const_mul(m, argument, xw, coefficient, out + '_product', product_width,
                               'csd', out, cfg)
    _record(m, **stats, bypass=None, banks=0, product_bits=product_width,
            product_maximum=product_maximum)
    return R._binary_mod_reduce(m, product, product_width, modulus, out, cfg,
                                maximum=product_maximum)


def mixed_radix_digits(m, xs, ms, tag, rom_steps, cfg=None):
    """Canonical mixed-radix digits, honoring ROM/arithmetic at every step."""
    moduli = _moduli(ms)
    if len(xs) != len(moduli) or type(rom_steps) is not bool:
        raise ValueError('invalid mixed-radix input list or implementation')
    cfg = _configuration(dict(cfg or {}, rev_impl='rom' if rom_steps else 'adder_based'))
    widths = [(value - 1).bit_length() for value in moduli]
    digits = []
    for index, modulus in enumerate(moduli):
        value, width = xs[index], widths[index]
        for previous in range(index):
            inverse = pow(moduli[previous], -1, modulus)
            difference, dw, minimum, maximum = _difference(
                m, value, width, modulus - 1, digits[previous], widths[previous], moduli[previous] - 1,
                modulus, f'{tag}_difference{index}_{previous}', cfg)
            value = const_mod_product(m, difference, dw, inverse, modulus,
                                      f'{tag}_digit{index}_{previous}', cfg, minimum=minimum, maximum=maximum)
            _record(m, kind='mixed_radix_step', stage=value, digit=index, previous=previous,
                    modulus=modulus, inverse=inverse, implementation=cfg['rev_impl'])
        digits.append(value)
    return digits


def _crt(m, xs, ms, out, cfg):
    product = math.prod(ms)
    if len(ms) == 1:
        _record(m, kind='singleton_crt', stage=out, modulus=product,
                implementation=cfg['rev_impl'])
        return m.wire(out, (product - 1).bit_length(), xs[0])
    terms = []
    for index, modulus in enumerate(ms):
        factor = product // modulus
        coefficient = factor * pow(factor, -1, modulus)
        terms.append(const_mod_product(m, xs[index], (modulus - 1).bit_length(), coefficient,
                                       product, f'{out}_term{index}', cfg, maximum=modulus - 1))
    return _mod_sum(m, terms, product, out, cfg)


def _group(m, xs, ms, out, cfg):
    product, width = math.prod(ms), (math.prod(ms) - 1).bit_length()
    signature = {'moduli': tuple(ms), 'implementation': cfg['rev_impl'],
                 'adder_family': cfg['adder_family'], 'adder_pins': dict(cfg['adder_pins']),
                 'diminished_one': bool(cfg.get('dim1', False)),
                 'column_family': cfg.get('col_family'), 'column_pins': dict(cfg.get('col_pins') or {})}
    name = f'fam_rns_reverse_crt_group_k{len(ms)}_m{product}{R._ptag(signature)}'
    ports = ', '.join(f'input logic [{(modulus-1).bit_length()-1}:0] r{i}' for i, modulus in enumerate(ms))
    child = R.Mod(name, ports + f', output logic [{width-1}:0] y', 'CRT-II subgroup reconstruction')
    child.raw(f'  localparam integer GROUP_SIZE = {len(ms)}, RESULT_BITS = {width};')
    child.raw(f"  localparam [{width}:0] MODULUS_PRODUCT = {width+1}'d{product};")
    value = _crt(child, [f'r{i}' for i in range(len(ms))], ms, 'value', cfg)
    child.assign('y', value)
    _install(m, child, {f'r{i}': value for i, value in enumerate(xs)}, out, width)
    _record(m, kind='crt_group', stage=out, module=name, instance='u_' + out,
            group_size=len(ms), moduli=tuple(ms), product=product, width=width,
            implementation=cfg['rev_impl'])
    return out, width, product


def reverse(m, xs, ms, out, ow, cfg):
    """Append an exact reconstruction over canonical residues to m."""
    moduli = _moduli(ms)
    if len(xs) != len(moduli):
        raise ValueError('residue and modulus counts differ')
    cfg = _configuration(cfg)
    algorithm = cfg.get('rev', 'crt')
    if algorithm not in ALGORITHMS:
        raise ValueError(f'unsupported RNS reverse algorithm {algorithm!r}')
    if cfg.get('family') == 'rns_reverse_converter' and len(moduli) not in (3, 4, 5):
        raise ValueError('rns_reverse_converter declares 3..5 channels')
    product = math.prod(moduli)
    width = (product - 1).bit_length()
    if type(ow) is not int or ow < width:
        raise ValueError(f'RNS reverse output needs {width} bits for product {product}; got {ow}')
    _record(m, kind='reverse', stage=out, algorithm=algorithm, implementation=cfg['rev_impl'],
            moduli=moduli, channel_widths=[(v - 1).bit_length() for v in moduli], output_bits=ow)
    m.raw(f'  // reverse algorithm {algorithm}, implementation {cfg["rev_impl"]}, {len(moduli)} channels')
    if algorithm == 'crt':
        value = _crt(m, xs, moduli, out + '_crt', cfg)
    elif algorithm == 'mixed_radix':
        digits = mixed_radix_digits(m, xs, moduli, out, cfg['rev_impl'] == 'rom', cfg)
        terms, factor = [], 1
        for index, (digit, modulus) in enumerate(zip(digits, moduli)):
            terms.append(const_mod_product(m, digit, (modulus - 1).bit_length(), factor,
                                           product, f'{out}_weighted{index}', cfg, maximum=modulus - 1))
            factor *= modulus
        value = R._sum_terms(m, terms, width, out + '_reconstructed', cfg,
                             'mixed-radix weighted digits')
    elif algorithm == 'new_crt_i':
        if len(moduli) < 2:
            raise ValueError('new_crt_i needs at least two channels')
        reduced_modulus = product // moduli[0]
        reduced_width = (reduced_modulus - 1).bit_length()
        terms = []
        for index in range(1, len(moduli)):
            prefix, suffix = math.prod(moduli[:index]), math.prod(moduli[index:])
            coefficient = (pow(prefix, -1, suffix) * math.prod(moduli[1:index])) % reduced_modulus
            difference, dw, minimum, maximum = _difference(
                m, xs[index], (moduli[index]-1).bit_length(), moduli[index]-1,
                xs[index-1], (moduli[index-1]-1).bit_length(), moduli[index-1]-1,
                reduced_modulus, f'{out}_adjacent{index}', cfg)
            terms.append(const_mod_product(m, difference, dw, coefficient, reduced_modulus,
                                           f'{out}_adjacent_term{index}', cfg, minimum=minimum, maximum=maximum))
            _record(m, kind='new_crt_i_term', stage=terms[-1], index=index, modulus=reduced_modulus,
                    coefficient=coefficient, implementation=cfg['rev_impl'])
        residue = _mod_sum(m, terms, reduced_modulus, out + '_reduced', cfg)
        scaled = const_mod_product(m, residue, reduced_width, moduli[0], product,
                                   out + '_scaled', cfg, maximum=reduced_modulus - 1)
        value = _add(m, scaled, _resize(xs[0], (moduli[0]-1).bit_length(), width),
                     width, out + '_joined', cfg)
    else:
        if len(moduli) < 2:
            raise ValueError('new_crt_ii needs two nonempty subgroups')
        split = len(moduli) // 2
        left, left_width, left_product = _group(m, xs[:split], moduli[:split], out + '_left', cfg)
        right, right_width, right_product = _group(m, xs[split:], moduli[split:], out + '_right', cfg)
        difference, dw, minimum, maximum = _difference(
            m, right, right_width, right_product - 1, left, left_width, left_product - 1,
            right_product, out + '_group_difference', cfg)
        inverse = pow(left_product, -1, right_product)
        residue = const_mod_product(m, difference, dw, inverse, right_product,
                                    out + '_join_residue', cfg, minimum=minimum, maximum=maximum)
        scaled = const_mod_product(m, residue, right_width, left_product, product,
                                   out + '_group_scaled', cfg, maximum=right_product - 1)
        value = _add(m, scaled, _resize(left, left_width, width), width, out + '_joined', cfg)
        _record(m, kind='new_crt_ii_join', stage=value, split=(split, len(moduli)-split),
                left_product=left_product, right_product=right_product, inverse=inverse,
                implementation=cfg['rev_impl'])
    return m.wire(out, ow, _resize(value, width, ow))
