"""Check that a carry-save ALU uses its selected exit adder and rejects conflicts."""
from pathlib import Path
from unittest.mock import patch
import argparse
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.alu_seed import alu_seed
from chialu.targets.rtl.families import redundant
from chialu.verify.alu_ref import normalize_spec
from chialu.verify.elaboration import elaborate
from chialu.verify.variant_selftest import check_seed


def spec():
    return normalize_spec({
        'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
        'modes': [{'format': 'int8', 'count': 1}],
        'ops': ['add', 'adc', 'sub', 'sbb', 'neg', 'abs', 'add_sat', 'sub_sat'],
        'unary_dual': [False, True], 'flags': ['carry', 'int_overflow', 'overflow'],
    })


def selections(compressor='3_2', correction=False):
    return {'core': ('redundant_internal', {}),
            'core.representation': ('carry_save_datapath', {
                'compressor': compressor, 'carry_overflow_correction': correction}),
            'core.adder.m0': ('ripple_carry', {
                'chunk_width_bits': 3, 'full_adder_logic': 'xor_majority'})}


def rejected(callback, reason):
    try:
        callback()
    except ValueError as error:
        assert reason in str(error), str(error)
    else:
        raise AssertionError('invalid or unrealized exit selection was accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--vectors', type=int, default=128)
    args = parser.parse_args()
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-carry-save-exit-'))
    request = spec()
    for compressor in ('3_2', '4_2', '5_3', '7_3'):
        for correction in (False, True):
            directory = root / (compressor + ('_corrected' if correction else ''))
            result = check_seed(request, selections(compressor, correction), directory, args.vectors, 17)
            assert result['pass'], result
            instances = elaborate((directory / 'seed.sv').read_text(), 'alu_core', directory / 'elaboration')
            adders = [row for row in instances if row['module'] == 'fam_adder_ripple_carry']
            assert len(adders) == 2, adders
            assert all(row['parameters']['W'] == 9 and row['parameters']['CHUNK'] == 3
                       and row['parameters']['FORM'] == 2 and row['ports']['a']['width'] == 9 for row in adders), adders
            chunks = [row for row in instances if row['module'] == 'fam_adder_ripple_chunk']
            assert len(chunks) == 6 and all(row['ports']['a']['width'] == 3 for row in chunks), chunks
            print(compressor, correction, 'PASS golden and actual 9-bit assimilator with three 3-bit chunks', flush=True)
    defaults = selections()
    del defaults['core.adder.m0']
    result = check_seed(request, defaults, root / 'representation_only', args.vectors, 17)
    assert result['pass'], result
    text = (root / 'representation_only' / 'seed.sv').read_text()
    assert 'fam_csd_adder_' in text and 'fam_adder_ripple_carry' in text
    for override, message in (({'assimilator.family': 'parallel_prefix'}, 'different families'),
                              ({'assimilator.chunk_width_bits': 2}, 'disagree on chunk_width_bits')):
        chosen = selections()
        chosen['core.representation'][1].update(override)
        rejected(lambda: alu_seed(request, families=chosen), message)
    original = FAM.adder_module
    with patch.object(FAM, 'adder_module', lambda family, pins, width: None if family == 'ripple_carry' else original(family, pins, width)):
        rejected(lambda: alu_seed(request, families=selections()), 'selected exit adder')
        rejected(lambda: redundant.representation_adder_sv(8, 'carry_save_datapath', {}), 'assimilator')
    # A controlled leaf makes dropped control connections observable. Its
    # separate test contract adds amode, so an unconnected control produces X.
    from chialu.verify.family_ref import Adapter, Port
    from chialu.verify.family_tb import emit
    from chialu.targets.rtl.families.selftest import run_python_case
    controlled = FAM.Module('controlled_exit', {}, '''module controlled_exit(
        input [8:0] a,b, input cin,amode, output [8:0] s, output cout);
      assign {cout,s} = {1'b0,a} + {1'b0,b} + cin + amode;
endmodule
''', (('amode', 1),))
    module, source = redundant.representation_adder_sv(8, 'carry_save_datapath', {}, assimilator=controlled)
    ports = (Port('a', 'input', 8), Port('b', 'input', 8), Port('cin', 'input', 1), Port('amode', 'input', 1),
             Port('s', 'output', 8), Port('cout', 'output', 1))
    def control_reference(row):
        total = row['a'] + row['b'] + row['cin'] + row['amode']
        return {'s': total & 255, 'cout': (total >> 8) & 1}
    adapter = Adapter(ports, control_reference, domains={'a': 128, 'b': 128})
    result = run_python_case('', 'control_forwarding', emit(module, {}, adapter, args.vectors, 17), root, source)
    assert result.endswith(': PASS'), result
    print('PASS representation-only generation, conflicting pins and rejected-factory regression', flush=True)
    print('PASS assimilator control-port forwarding', flush=True)


if __name__ == '__main__':
    main()
