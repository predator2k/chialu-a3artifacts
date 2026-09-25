"""Verify RNS channel CPA selection through ALU generation and elaboration."""
import argparse
from pathlib import Path
import re
import tempfile
from unittest.mock import patch

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.alu_seed import alu_seed
from chialu.targets.rtl.families import redundant
from chialu.verify.alu_ref import normalize_spec
from chialu.verify.elaboration import elaborate
from chialu.verify.variant_selftest import check_seed


def request():
    return normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                           'modes': [{'format': 'int8', 'count': 1}],
                           'ops': ['add', 'sub', 'adc', 'sbb', 'neg', 'abs', 'add_sat', 'sub_sat'],
                           'unary_dual': [False, True], 'flags': ['carry', 'int_overflow', 'overflow']})


def selections(form, family, pins):
    return {'core': ('rns_internal', {}),
            'core.channels': ('rns_channel_arithmetic', {'channel_width_n': 4, 'modulus_form': form}),
            'core.adder.m0': (family, dict(pins))}


def rejected(function, needle):
    try:
        function()
    except ValueError as error:
        assert needle in str(error), error
    else:
        raise AssertionError(f'RNS selection unexpectedly accepted: {needle}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--vectors', type=int, default=128)
    args = parser.parse_args()
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-channel-cpa-'))
    spec = request()
    expected_widths = {'pow2': [4, 4, 5], 'pow2_plus_1': [4, 4, 5],
                       'pow2_minus_1': [4, 5, 7], 'generic': [4, 4, 4]}
    for form, widths in expected_widths.items():
        for family, pins in [('ripple_carry', {'chunk_width_bits': 3, 'full_adder_logic': 'xor_majority'}),
                             ('parallel_prefix', {'topology': 'brent_kung', 'valency': 2})]:
            chosen = selections(form, family, pins)
            directory = root / form / family
            result = check_seed(spec, chosen, directory, args.vectors, 21)
            assert result['pass'], result
            source = (directory / 'seed.sv').read_text()
            rows = elaborate(source, 'alu_core', directory / 'elaboration')
            # Identify the actual channel additions, rather than accepting an
            # unrelated matching CPA in an entry or exit converter.
            for channel, width in enumerate(widths):
                match = re.search(r'// channel ' + str(channel) + r':[^\n]*\n\s+(\w+)\s+(?:#\([^\n]*\)\s+)?(u\d+)\s*\(', source)
                assert match, (form, family, channel)
                module, instance = match.groups()
                copies = [row for row in rows if row['module'] == module and row['instance'] == instance]
                assert len(copies) == 2, (form, channel, copies)
                assert all(row['ports']['a']['width'] == width for row in copies), copies
                if family == 'ripple_carry':
                    assert module == 'fam_adder_ripple_carry'
                    assert all(row['parameters']['CHUNK'] == 3 and row['parameters']['FORM'] == 2 for row in copies)
                else:
                    assert module == f'fam_prefix_brent_kung_w{width}', module
            print(form, family, 'PASS Python golden and selected CPA in all three channels', flush=True)
    chosen = selections('pow2', 'ripple_carry', {'chunk_width_bits': 3, 'full_adder_logic': 'xor_majority'})
    chosen['core.channels'][1].update({'modular_adder.family': 'ripple_carry',
                                      'modular_adder.chunk_width_bits': 3,
                                      'modular_adder.full_adder_logic': 'xor_majority'})
    assert alu_seed(spec, families=chosen).text == (root / 'pow2' / 'ripple_carry' / 'seed.sv').read_text()
    names = []
    for family, pins in [('ripple_carry', {'chunk_width_bits': 3}), ('parallel_prefix', {'topology': 'brent_kung'})]:
        name, _ = redundant.rns_sv('adder', 8, 'rns_channel_arithmetic', {'channel_width_n': 4},
                                   adder_selection=(family, pins))
        names.append(name)
    assert len(set(names)) == 2, 'different selected channel CPAs reused one module name'
    chosen = selections('pow2', 'ripple_carry', {})
    del chosen['core.adder.m0']
    result = check_seed(spec, chosen, root / 'channels_only', args.vectors, 21)
    assert result['pass'], result
    for override, needle in (({'modular_adder.family': 'parallel_prefix'}, 'different families'),
                             ({'modular_adder.chunk_width_bits': 2}, 'disagree on chunk_width_bits')):
        chosen = selections('pow2', 'ripple_carry', {'chunk_width_bits': 3})
        chosen['core.channels'][1].update(override)
        rejected(lambda: alu_seed(spec, families=chosen), needle)
    chosen = selections('pow2', 'ripple_carry', {'chunk_width_bits': 3})
    with patch.object(FAM, 'adder_module', return_value=None):
        rejected(lambda: alu_seed(spec, families=chosen), 'selected adder')
        rejected(lambda: redundant.rns_sv('adder', 8, 'rns_channel_arithmetic', {}), 'selected adder')
    rejected(lambda: redundant.rns_sv('adder', 8, 'rns_channel_arithmetic', {'modular_adder.family': 'parallel_prefix'},
                                       adder_selection=('ripple_carry', {})), 'disagrees on modular_adder.family')
    print('PASS RNS defaults, alias conflicts and rejected-adder propagation', flush=True)


if __name__ == '__main__':
    main()
