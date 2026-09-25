"""Canonical RNS encoding after a selected binary adder algorithm.

The first sum is computed by the requested family. Fixed representation
normalization then reduces that family's actual output, including an
approximate output. It does not replace that output with exact a+b.
"""
from __future__ import annotations


def _record(m, **record):
    if not hasattr(m, 'modular_add_stats'):
        m.modular_add_stats = []
    m.modular_add_stats.append(record)


def _resize(signal, width, target):
    if width == target:
        return signal
    if width < target:
        return f"{{{{{target-width}{{1'b0}}}}, {signal}}}"
    return f'{signal}[{target-1}:0]'


def _form(modulus):
    if modulus & (modulus - 1) == 0:
        return 'pow2'
    if (modulus + 1) & modulus == 0:
        return 'minus_one'
    if (modulus - 1) & (modulus - 2) == 0:
        return 'plus_one'
    return 'generic'


def _approximate_geometry(pins, width):
    """Reject invalid primitive geometry and inactive explicit controls."""
    from .fidelity import inactive
    lower = pins.get('lower_part_width', 4)
    scheme = pins.get('lower_scheme', 'truncate_constant')
    if type(lower) is not int or not 1 <= lower < width:
        raise ValueError('approximate lower_part_width must leave real lower and upper regions')
    if scheme not in ('truncate_constant', 'or_gates', 'segmented_subadders', 'speculative_segments'):
        raise ValueError(f'unknown approximate lower_scheme {scheme!r}')
    if scheme != 'speculative_segments':
        for key in pins:
            if key in ('speculation_window', 'correction') or key.startswith('correction_incrementer.'):
                inactive(pins, key, 'only speculative_segments has speculation/correction hardware')
        return
    window = pins.get('speculation_window', 4)
    correction = pins.get('correction', 'none')
    if type(window) is not int or not 1 <= window <= lower:
        raise ValueError('the entire speculation_window must fit the lower region')
    if correction not in ('none', 'configurable_stages'):
        raise ValueError(f'unknown approximate correction {correction!r}')
    if correction == 'none':
        for key in pins:
            if key.startswith('correction_incrementer.'):
                inactive(pins, key, 'correction=none has no correction incrementer')


def normalize(m, value, bits, modulus, out, *, maximum=None):
    """Fixed exact remainder for every word in the declared input bound."""
    if type(bits) is not int or bits < 1 or type(modulus) is not int or modulus < 2:
        raise ValueError('invalid RNS normalization geometry')
    limit = (1 << bits) - 1 if maximum is None else maximum
    if type(limit) is not int or not 0 <= limit < (1 << bits):
        raise ValueError('normalization bound does not fit its input word')
    width = (modulus - 1).bit_length()
    current = m.wire(out + '_input', bits, value)
    stages = []
    # Before shift j, current < 2**(j+1)*m. One conditional subtraction
    # makes current < 2**j*m. The final stage therefore leaves <m.
    for shift in reversed(range((limit // modulus).bit_length())):
        constant = modulus << shift
        take = m.wire(f'{out}_take{shift}', 1, f"{current} >= {bits}'d{constant}")
        current = m.wire(f'{out}_remainder{shift}', bits,
                         f"{take} ? ({current} - {bits}'d{constant}) : {current}")
        stages.append({'shift': shift, 'constant': constant, 'take': take, 'result': current})
    _record(m, kind='normalization', output=out, input_bits=bits, input_maximum=limit,
            modulus=modulus, output_bits=width, stages=stages)
    return m.wire(out, width, _resize(current, bits, width))


def normalize_sum(m, total, child_width, modulus, out, *, diminished=False):
    """Canonical residue from every possible selected {cout,sum} word."""
    if type(child_width) is not int or child_width < 1 or type(modulus) is not int or modulus < 2:
        raise ValueError('invalid modular-adder geometry')
    bits = child_width + 1
    raw = m.wire(out + '_selected_total', bits, total)
    if diminished:
        if modulus != (1 << child_width) + 1:
            raise ValueError('diminished-one requires m=2**child_width+1')
        decoded = m.wire(out + '_plus_two', bits + 1, f"{{1'b0, {raw}}} + {bits+1}'d2")
        return normalize(m, decoded, bits + 1, modulus, out, maximum=(1 << bits) + 1)
    if (modulus - 1).bit_length() != child_width:
        raise ValueError('normal modular addition requires the full residue width')
    if modulus == (1 << child_width):
        _record(m, kind='power_two_slice', output=out, modulus=modulus, child_width=child_width)
        return m.wire(out, child_width, f'{raw}[{child_width-1}:0]')
    if modulus == (1 << child_width) - 1:
        # Keep the carry of this fold: S may itself be all ones while
        # cout=1, including outputs of approximate child algorithms.
        folded = m.wire(out + '_folded', bits,
                        f"{{1'b0, {raw}[{child_width-1}:0]}} + {raw}[{child_width}]")
        return normalize(m, folded, bits, modulus, out, maximum=1 << child_width)
    return normalize(m, raw, bits, modulus, out)


def mod_add(m, a, b, cin, mod, out, cfg, tag):
    """Use the selected first sum, then restore a canonical residue code."""
    if type(mod) is not int or mod < 2:
        raise ValueError('RNS modulus must be an integer greater than one')
    family = cfg.get('adder_family')
    if not isinstance(family, str) or not family:
        raise ValueError('modular addition requires a concrete selected adder family')
    pins = cfg.get('adder_pins', {})
    width = (mod - 1).bit_length()
    diminished = _form(mod) == 'plus_one' and bool(cfg.get('dim1'))
    child_width = width - 1 if diminished else width
    if family == 'approximate_truncated':
        _approximate_geometry(pins, child_width)
    aw, bw = m.wire(out + '_a', width, a), m.wire(out + '_b', width, b)
    ci = m.wire(out + '_cin', 1, cin)
    if diminished:
        za = m.wire(out + '_zero_a', 1, f"{aw} == {width}'d0")
        zb = m.wire(out + '_zero_b', 1, f"{bw} == {width}'d0")
        aa = m.wire(out + '_encoded_a', child_width, f"{aw}[{child_width-1}:0] - {child_width}'d1")
        bb = m.wire(out + '_encoded_b', child_width, f"{bw}[{child_width-1}:0] - {child_width}'d1")
    else:
        aa, bb = aw, bw
    summed, carry = m.wire(out + '_child_sum', child_width), m.wire(out + '_child_carry', 1)
    m.adder(family, pins, child_width, aa, bb, ci, summed, carry,
            f'channel {tag}: selected first addition before fixed canonical normalization')
    total = m.wire(out + '_child_total', child_width + 1, f'{{{carry}, {summed}}}')
    canonical = normalize_sum(m, total, child_width, mod, out + '_canonical', diminished=diminished)
    if diminished:
        alternate = m.wire(out + '_zero_total', width + 1, f'({za} ? {bw} : {aw}) + {ci}')
        zero_result = normalize(m, alternate, width + 1, mod, out + '_zero_canonical', maximum=mod)
        result = f'({za} | {zb}) ? {zero_result} : {canonical}'
    else:
        result = canonical
    _record(m, kind='modular_add', output=out, modulus=mod, width=width, family=family,
            pins=dict(pins), child_width=child_width, diminished=diminished,
            selected_sum=summed, selected_carry=carry, selected_total=total,
            zero_a=za if diminished else None, zero_b=zb if diminished else None)
    return m.wire(out, width, result)
