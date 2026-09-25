"""Verify RNS ROM multiplication and its physical lookup-bank geometry."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import re
import subprocess
import tempfile

from chialu.targets.rtl.families import redundant as R
from chialu.targets.rtl.families import library_closure
from chialu.verify.alu_ref import normalize_spec
from chialu.verify.elaboration import elaborate
from chialu.verify.variant_selftest import check_seed


def banks(modulus):
    width = (modulus - 1).bit_length()
    chunk = width if width <= 5 else 4
    return [(min(chunk, width - a), min(chunk, width - b), width, a + b, modulus)
            for a in range(0, width, chunk) for b in range(0, width, chunk)
            if pow(2, a + b, modulus)]


def inspect(source, top, directory, moduli):
    rows = elaborate(source, top, directory)
    actual = []
    checked = set()
    for row in rows:
        if not row['module'].startswith('fam_rns_product_rom_'):
            continue
        p = row['parameters']
        key = tuple(p[name] for name in ('A_BITS', 'B_BITS', 'OUT_BITS', 'SHIFT', 'MODULUS'))
        assert tuple(row['ports'][name]['width'] for name in ('a', 'b', 'y')) == key[:3], row
        table = p['T_value']
        if key not in checked:
            aw, bw, ow, shift, modulus = key
            for b in range(1 << bw):
                for a in range(1 << aw):
                    address = (b << aw) | a
                    got = (table >> (address * ow)) & ((1 << ow) - 1)
                    assert got == (a * b * (1 << shift)) % modulus, (key, a, b, got)
            checked.add(key)
        actual.append(key)
    expected = [bank for modulus in moduli for bank in banks(modulus)]
    assert Counter(actual) == Counter(expected), (actual, expected)
    additions = re.findall(r'// channel (\d+|native) ROM bank tree[^\n]*\n\s+(\w+)\s+(?:#\([^\n]*\)\s+)?(u\d+)\s*\(', source)
    counts = Counter(channel for channel, _, _ in additions)
    for channel, modulus in enumerate(moduli):
        tag = 'native' if top == 'rom_dut' else str(channel)
        assert counts[tag] == len(banks(modulus)) - 1, (tag, counts, modulus)
    for channel, name, instance in additions:
        width = (moduli[0 if channel == 'native' else int(channel)] - 1).bit_length()
        cp = [row for row in rows if row['module'] == name and row['instance'] == instance]
        assert len(cp) == 1 and cp[0]['ports']['a']['width'] == width, (channel, name, instance, cp)
        assert (name == 'fam_adder_ripple_carry' and cp[0]['parameters']['CHUNK'] == 3 or
                name == f'fam_prefix_brent_kung_w{width}'), cp
    (Path(directory) / 'banks.json').write_text(json.dumps(actual, indent=2))
    return len(actual)


def native(modulus, directory, vectors):
    """Independent integer oracle, exhaustive on short canonical residues."""
    width = (modulus - 1).bit_length()
    module = R.Mod('rom_dut', f'input [{width-1}:0] a, b, output [{width-1}:0] y', 'ROM regression')
    cfg = {'mul_red': 'rom', 'adder_family': 'ripple_carry', 'adder_pins': {'chunk_width_bits': 3}}
    R._mod_mul(module, 'a', 'b', modulus, 'product', cfg, 'native')
    module.assign('y', 'product')
    source = module.render()
    source += library_closure(source)
    assert 'stands in' not in source
    count = inspect(source, 'rom_dut', directory / 'elaboration', [modulus])
    rng = random.Random(192)
    pairs = ([(a, b) for a in range(modulus) for b in range(modulus)] if width <= 6 else
             [(a, b) for a in (0, 1, 2, modulus // 2, modulus - 2, modulus - 1)
              for b in (0, 1, 2, modulus // 2, modulus - 2, modulus - 1)] +
             [(rng.randrange(modulus), rng.randrange(modulus)) for _ in range(vectors)])
    tb = [f'module tb; reg [{width-1}:0] a, b; wire [{width-1}:0] y; rom_dut dut(a,b,y); initial begin']
    for a, b in pairs:
        tb.append(f"a={width}'d{a}; b={width}'d{b}; #1; if(y !== {width}'d{a*b%modulus}) $fatal(1, \"ROM {modulus} a={a} b={b}: %d\", y);")
    tb += ['$display("PASS ROM arithmetic"); $finish; end endmodule']
    (directory / 'tb.sv').write_text('\n'.join(tb))
    from chialu.verify import simulate as SIM
    compiled = subprocess.run(['verilator', *SIM.VERILATOR_FLAGS, '-j', str(SIM.VERILATOR_JOBS),
                               '--top-module', 'tb', '-Mdir', 'obj_sim', '-o', 'sim',
                               'tb.sv', str(directory / 'elaboration' / 'design.sv')],
                              cwd=directory, capture_output=True, text=True, timeout=SIM.scaled(600))
    compiled.check_returncode()
    result = subprocess.run(['./obj_sim/sim'], cwd=directory, capture_output=True, text=True, timeout=SIM.scaled(60))
    (directory / 'simulation.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    print('native', modulus, f'PASS {len(pairs)} pairs, {count} actual ROM banks', flush=True)


def signed_seed(root, vectors):
    pins = {'channel_width_n': 6, 'modulus_form': 'pow2', 'multiplier_reduction': 'rom',
            'modular_adder.family': 'ripple_carry', 'modular_adder.chunk_width_bits': 3}
    spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                           'modes': [{'format': 'int7', 'count': 1}],
                           'ops': ['mul', 'mul_high', 'mul_wide', 'mul_sat'],
                           'flags': ['overflow', 'int_overflow']})
    directory = root / 'pow2_n6_w7_signed'
    result = check_seed(spec, {'core': ('rns_internal', {}),
                               'core.channels': ('rns_channel_arithmetic', pins)}, directory, vectors, 29)
    assert result['pass'], {key: value for key, value in result.items() if key != 'fidelity'}
    count = inspect((directory / 'seed.sv').read_text(), 'alu_core', directory / 'elaboration', (63, 64, 65))
    print('pow2 6 PASS int7 signed golden,', count, 'actual ROM banks', flush=True)


def invalid_selection():
    try:
        R.rns_sv('multiplier', 5, 'rns_channel_arithmetic', {'multiplier_reduction': 'not_a_reduction'})
    except ValueError as error:
        assert 'multiplier_reduction' in str(error), error
    else:
        raise AssertionError('invalid RNS multiplier reduction was replaced by a default')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--vectors', type=int, default=128)
    parser.add_argument('--section', choices=('all', 'native', 'seeds'), default='all')
    parser.add_argument('--forms', nargs='+', choices=('pow2', 'pow2_plus_1', 'pow2_minus_1', 'generic'),
                        default=('pow2', 'pow2_plus_1', 'pow2_minus_1', 'generic'))
    parser.add_argument('--width-pins', type=int, nargs='+', choices=range(4, 33), default=(4, 6, 32))
    args = parser.parse_args()
    invalid_selection()
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-rom-'))
    # Widths 4, 5 and 6 straddle the old replacement threshold; the wide
    # moduli exercise all full tiles and a one-bit tail, not a clipped pin.
    if args.section != 'seeds':
        for modulus in (15, 17, 31, 33, (1 << 32) - 1, 1 << 32, (1 << 32) + 1):
            native(modulus, root / f'native_{modulus}', args.vectors)
    if args.section == 'native':
        return
    for form in args.forms:
        for n in args.width_pins:
            pins = {'channel_width_n': n, 'modulus_form': form, 'multiplier_reduction': 'rom',
                    'modular_adder.family': 'ripple_carry', 'modular_adder.chunk_width_bits': 3}
            if n == 32:
                # The native wide-bank tests above select ripple. These whole
                # ALUs select a prefix CPA to bound entry/CRT conversion depth.
                pins.pop('modular_adder.chunk_width_bits')
                pins.update({'modular_adder.family': 'parallel_prefix', 'modular_adder.topology': 'brent_kung'})
            preview = R.rns_cfg('rns_channel_arithmetic', pins, 1, 'multiplier')
            width = max((m - 1).bit_length() for m in preview['moduli'])
            cfg = R.rns_cfg('rns_channel_arithmetic', pins, width, 'multiplier')
            assert cfg['n'] == n, cfg
            # These largest heterogeneous CRT boundaries dominate simulation
            # cost. One wide-product op observes every product bit; the small
            # targets above independently exercise all four result/flag paths.
            wide_only = n == 32 and form in ('pow2_minus_1', 'generic')
            spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                                   'modes': [{'format': f'uint{width}', 'count': 1}],
                                   'ops': ['mul_wide'] if wide_only else ['mul', 'mul_high', 'mul_wide', 'mul_sat'],
                                   'flags': [] if wide_only else ['overflow', 'int_overflow']})
            directory = root / f'{form}_n{n}_w{width}'
            result = check_seed(spec, {'core': ('rns_internal', {}),
                                       'core.channels': ('rns_channel_arithmetic', pins)},
                                directory, args.vectors, 29)
            assert result['pass'], {key: value for key, value in result.items() if key != 'fidelity'}
            source = (directory / 'seed.sv').read_text()
            count = inspect(source, 'alu_core', directory / 'elaboration', cfg['moduli'])
            print(form, n, f'PASS uint{width} golden, {count} actual ROM banks', flush=True)
    signed_seed(root, args.vectors)


if __name__ == '__main__':
    main()
