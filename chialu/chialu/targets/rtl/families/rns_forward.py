"""RNS forward conversion with explicit word chunks and bounded ROM banks."""
from __future__ import annotations

from . import redundant as R


def chunk_layout(width, chunk):
    if not 1 <= chunk <= 64:
        raise ValueError(f"chunk_bits must be in 1..64, got {chunk}")
    if width < chunk:
        raise ValueError(f"chunk_bits={chunk} needs at least one full chunk; input width is {width}")
    return tuple((lo, min(chunk, width - lo)) for lo in range(0, width, chunk))


def _slice(value, width, low, bits):
    # Mod.wire declares a one-bit intermediate as a scalar.
    return value if width == 1 else f'{value}[{low+bits-1}:{low}]'


def _tag(cfg, *, columns=False):
    pins = {'adder.family': cfg['adder_family'], **{'adder.' + k: v for k, v in cfg['adder_pins'].items()}}
    if columns:
        pins.update({'column.family': cfg.get('col_family'), **{'column.' + k: v for k, v in cfg.get('col_pins', {}).items()}})
    return R._ptag(pins)


def _install(parent, child, inputs, output, bits):
    parent.extra.append(child.render())
    parent.controls(child.control_ports.items())
    parent.reduction_stats.extend(dict(record, scope=f'{parent.name}.u_{output}',
                                       child_scope=record.get('scope', child.name)) for record in child.reduction_stats)
    parent.wire(output, bits)
    conns = [f'.{port}({value})' for port, value in inputs.items()]
    conns += [f'.y({output})'] + [f'.{port}({port})' for port in child.control_ports]
    parent.raw(f"  {child.name} u_{output} ({', '.join(conns)});")
    return output


def _bank(parent, x, width, modulus, shift, output):
    bits = (modulus - 1).bit_length()
    name = f'fam_rns_forward_bank_m{modulus}_w{width}_s{shift}'
    bank = R.Mod(name, f'input logic [{width-1}:0] x, output logic [{bits-1}:0] y',
                 f'ROM of (x * 2^{shift}) mod {modulus}')
    bank.raw(f'  localparam integer INPUT_BITS = {width}, RESULT_BITS = {bits}, SHIFT = {shift};')
    bank.raw(f"  localparam [{bits}:0] MODULUS = {bits+1}'d{modulus};")
    # Address the complete words directly. A packed bit-select first
    # creates a barrel over 2**width * bits positions in some frontends.
    bank.raw('  always_comb begin\n    case (x)')
    for value in range(1 << width):
        bank.raw(f"      {width}'d{value}: y = {bits}'d{(value << shift) % modulus};")
    bank.raw("      default: y = 'x;\n    endcase\n  end")
    return _install(parent, bank, {'x': x}, output, bits)


def _mod_tree(m, rows, modulus, output, cfg):
    level = 0
    while len(rows) > 1:
        following = [R._mod_add(m, rows[i], rows[i + 1], "1'b0", modulus,
                                f'{output}_l{level}_{i//2}', cfg, f'{output} bank tree {level}:{i//2}')
                     for i in range(0, len(rows) - 1, 2)]
        if len(rows) % 2:
            following.append(rows[-1])
        rows = following
        level += 1
    return m.wire(output, (modulus - 1).bit_length(), rows[0] if rows else "'0")


def _rom_value(m, x, width, modulus, shift, output, cfg):
    rows = []
    for lo in range(0, width, 8):
        bits = min(8, width - lo)
        if pow(2, shift + lo, modulus):
            rows.append(_bank(m, _slice(x, width, lo, bits), bits, modulus, shift + lo, f'{output}_bank{lo//8}'))
    return _mod_tree(m, rows, modulus, output, cfg)


def _chunk(parent, x, bits, modulus, shift, nominal, output, cfg, periodic=False):
    residue_bits = (modulus - 1).bit_length()
    weights = [pow(2, shift + i, modulus) for i in range(bits)]
    maximum = sum(weights) if periodic else modulus - 1
    result_bits = max(1, maximum.bit_length())
    mode = 'periodic' if periodic else 'rom'
    name = f'fam_rns_forward_chunk_{mode}_c{nominal}_w{bits}_m{modulus}_s{shift}{_tag(cfg, columns=periodic)}'
    chunk = R.Mod(name, f'input logic [{bits-1}:0] x, output logic [{result_bits-1}:0] y',
                  f'{mode} chunk: {bits} actual input bits of a nominal {nominal}-bit chunk')
    chunk.raw(f'  localparam integer CHUNK_BITS = {nominal}, INPUT_BITS = {bits}, RESULT_BITS = {result_bits}, SHIFT = {shift};')
    chunk.raw(f"  localparam [{residue_bits}:0] MODULUS = {residue_bits+1}'d{modulus};")
    if periodic:
        rows = [chunk.wire(f'row{i}', result_bits, f"x[{i}] ? {result_bits}'d{weight} : {result_bits}'d0")
                for i, weight in enumerate(weights) if weight]
        value = R._sum_terms(chunk, rows, result_bits, 'value', cfg, 'periodic weighted columns within a chunk')
    else:
        value = _rom_value(chunk, 'x', bits, modulus, shift, 'value', cfg)
    chunk.assign('y', value)
    return _install(parent, chunk, {'x': x}, output, result_bits), result_bits, maximum


def _final_rom(m, x, width, modulus, output, cfg):
    name = f'fam_rns_forward_final_rom_w{width}_m{modulus}{_tag(cfg)}'
    bits = (modulus - 1).bit_length()
    final = R.Mod(name, f'input logic [{width-1}:0] x, output logic [{bits-1}:0] y', 'final banked residue ROM')
    final.raw(f'  localparam integer INPUT_BITS = {width}, RESULT_BITS = {bits};')
    value = _rom_value(final, 'x', width, modulus, 0, 'value', cfg)
    final.assign('y', value)
    return _install(m, final, {'x': x}, output, bits)


def _finish(m, rows, widths, maximum, modulus, output, cfg):
    width = max(1, maximum.bit_length())
    terms = [f"{{{{{width-bits}{{1'b0}}}}, {row}}}" if width > bits else row for row, bits in zip(rows, widths)]
    total = R._sum_terms(m, terms, width, f'{output}_sum', cfg, 'the chunks combined before final reduction')
    if cfg['fwd_final'] == 'rom':
        return _final_rom(m, total, width, modulus, output, cfg)
    if cfg['fwd_final'] != 'modular_adder':
        raise ValueError(f"RNS final_reduction {cfg['fwd_final']!r} is not implemented")
    return R._binary_mod_reduce(m, total, width, modulus, output, cfg, maximum=maximum)


def _mac(parent, x, width, modulus, output, cfg, layout):
    residue_bits = (modulus - 1).bit_length()
    current, current_max = f"{residue_bits}'d0", 0
    for index, (lo, bits) in reversed(list(enumerate(layout))):
        input_max = (current_max << bits) + (1 << bits) - 1
        final_rom = index == 0 and cfg['fwd_final'] == 'rom'
        name = (f'fam_rns_forward_mac_c{cfg["chunk_bits"]}_w{bits}_m{modulus}_b{current_max}'
                + ('_rom' if final_rom else '') + _tag(cfg))
        step = R.Mod(name, f'input logic [{residue_bits-1}:0] r, input logic [{bits-1}:0] digit, output logic [{residue_bits-1}:0] y',
                     f'unrolled radix-2^{bits} modular multiply-add')
        step.raw(f'  localparam integer CHUNK_BITS = {cfg["chunk_bits"]}, INPUT_BITS = {bits}, RADIX_BITS = {bits};')
        combined = step.wire('combined', residue_bits + bits, '{r, digit}')
        if final_rom:
            live_width = max(1, input_max.bit_length())
            value = _final_rom(step, f'{combined}[{live_width-1}:0]', live_width, modulus, 'value', cfg)
        else:
            value = R._binary_mod_reduce(step, combined, residue_bits + bits, modulus, 'value', cfg, maximum=input_max)
        step.assign('y', value)
        current = _install(parent, step, {'r': current, 'digit': _slice(x, width, lo, bits)}, f'{output}_step{index}', residue_bits)
        current_max = min(modulus - 1, input_max)
    return parent.wire(output, residue_bits, current)


def forward(m, x, width, modulus, output, cfg, tag):
    implementation = cfg['fwd']
    if implementation not in ('rom_per_chunk', 'segmented_rom_modular_add', 'periodic_csa_moma', 'channel_modular_mac'):
        raise ValueError(f'RNS forward implementation {implementation!r} is not implemented')
    if cfg['fwd_final'] not in ('rom', 'modular_adder'):
        raise ValueError(f"RNS final_reduction {cfg['fwd_final']!r} is not implemented")
    layout = chunk_layout(width, cfg['chunk_bits'])
    # Geometry requirements concern the selected construction, not the
    # mathematical converter. Keep a short tail, but do not accept a
    # selection whose feedback or segment-combination stage disappears.
    chunk = cfg['chunk_bits']
    if implementation == 'segmented_rom_modular_add' and len(layout) < 4:
        raise ValueError(f'segmented_rom_modular_add with chunk_bits={chunk} needs two actual '
                         f'two-chunk segments; input width must be at least {3 * chunk + 1}, got {width}')
    if implementation == 'channel_modular_mac' and len(layout) < 2:
        raise ValueError(f'channel_modular_mac with chunk_bits={chunk} needs actual residue feedback; '
                         f'input width must be at least {chunk + 1}, got {width}')
    if implementation in ('rom_per_chunk', 'segmented_rom_modular_add') and cfg['fwd_final'] == 'rom' and len(layout) < 2:
        raise ValueError(f'final_reduction=rom with chunk_bits={chunk} needs two residue chunks; '
                         f'input width must be at least {chunk + 1}, got {width}')
    if implementation == 'channel_modular_mac':
        return _mac(m, x, width, modulus, output, cfg, layout)
    periodic = implementation == 'periodic_csa_moma'
    if periodic and not cfg.get('col_family'):
        from .selection import copy_pins
        columns = copy_pins(cfg.get('col_pins'))
        columns.setdefault('final_cpa.family', 'ripple_carry')
        cfg = dict(cfg, col_family='csa_tree',
                   col_pins=columns)
    chunks = [_chunk(m, _slice(x, width, lo, bits), bits, modulus, lo, cfg['chunk_bits'],
                     f'{output}_chunk{i}', cfg, periodic)
              for i, (lo, bits) in enumerate(layout)]
    rows, widths, maxima = map(list, zip(*chunks))
    if periodic:
        nonzero = [(row, bits) for row, bits, maximum in zip(rows, widths, maxima) if maximum]
        return _finish(m, [row for row, _ in nonzero], [bits for _, bits in nonzero], sum(maxima), modulus, output, cfg)
    if implementation == 'segmented_rom_modular_add':
        rows = [R._mod_add(m, rows[i], rows[i + 1], "1'b0", modulus, f'{output}_segment{i//2}', cfg,
                           f'{tag} segment {i//2}') if i + 1 < len(rows) else rows[i]
                for i in range(0, len(rows), 2)]
    if cfg['fwd_final'] == 'rom':
        return _finish(m, rows, [(modulus - 1).bit_length()] * len(rows), len(rows) * (modulus - 1), modulus, output, cfg)
    if cfg['fwd_final'] != 'modular_adder':
        raise ValueError(f"RNS final_reduction {cfg['fwd_final']!r} is not implemented")
    current = rows[0]
    for index, row in enumerate(rows[1:]):
        current = R._mod_add(m, current, row, "1'b0", modulus, f'{output}_combine{index}', cfg, f'{tag} chunk sum {index}')
    return m.wire(output, (modulus - 1).bit_length(), current)
