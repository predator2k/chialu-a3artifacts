"""Independent integer-sum simulation and structural CSA compressor coverage."""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import tempfile
from unittest.mock import patch

from chialu.targets.rtl.families.redundant import Mod
from chialu.targets.rtl.families.redundant_reduce import MODULES, csa_rows
from chialu.targets.rtl.families.selftest import run_python_case
from chialu.verify.elaboration import elaborate
from chialu.verify.family_ref import Adapter, Port
from chialu.verify.family_tb import Bench, emit, emit_text


def _run(source, name, ports, reference, directory, vectors=96, patterns=None):
    adapter = Adapter(tuple(ports), reference)
    if patterns is None:
        bench = emit(name, {}, adapter, vectors, 947)
    else:
        adapter.stimulus = lambda n, seed: patterns
        bench = Bench(emit_text(name, {}, adapter.ports, len(patterns)), adapter, 0, 947)
    result = run_python_case('', directory.name, bench, directory.parent, source)
    assert result.endswith(': PASS'), result
    return {'vectors': len((directory / 'expected.hex').read_text().split()),
            'source_sha256': hashlib.sha256(source.encode()).hexdigest()}


def primitives(root):
    results = []
    for kind, names in (('3_2', 'abc'), ('4_2', ('a', 'b', 'c', 'd', 'cin')), ('7_3', 'abcdefg')):
        ports = [Port(p, 'input', 1) for p in names] + [Port('total', 'output', 3)]
        outs = 's, carry, carry2' if kind == '7_3' else 's, carry, cout' if kind == '4_2' else 's, carry'
        weighted = "{2'b0,s}+{1'b0,carry,1'b0}"
        if kind == '7_3':
            weighted += "+{carry2,2'b0}"
        elif kind == '4_2':
            weighted += "+{1'b0,cout,1'b0}"
        source = (f'module test(input wire {", ".join(names)}, output wire [2:0] total);\n'
                  f'wire {outs}; fam_redundant_csa_bit_{kind} cell_inst({", ".join(names)}, {outs});\n'
                  f'assign total={weighted}; endmodule\n' + MODULES)
        patterns = [dict(zip(names, bits)) for bits in product((0, 1), repeat=len(names))]
        result = _run(source, 'test', ports, lambda x: {'total': sum(x.values())},
                      root / f'bit_{kind}', patterns=patterns)
        result.update(compressor=kind, exhaustive=True)
        results.append(result)
        print(f'bit {kind}: PASS {result["vectors"]} exhaustive integer sums', flush=True)
    return results


def tree(root, compressor, count, width, vectors, *, tails=False):
    names = [f'x{i}' for i in range(count)]
    inputs = f'input wire [{width-1}:0] ' + ', '.join(names) + ', ' if names else ''
    m = Mod('test', inputs + f'output wire [{width-1}:0] total', 'independent integer-sum reduction test')
    rows = csa_rows(m, names, width, 'tree', compressor, require_full=not tails)
    m.assign('total', f'{rows[0]} + {rows[1]}')
    source = m.render()
    directory = root / f'tree_{compressor.replace(":", "_")}_{count}_w{width}'
    ports = [Port(name, 'input', width) for name in names] + [Port('total', 'output', width)]
    # Exhaustive on every combination of one-bit rows, including the full
    # seven-one case. Wider frames use every corner plus seeded random words.
    patterns = [dict(zip(names, bits)) for bits in product((0, 1), repeat=count)] if width == 1 else None
    result = _run(source, 'test', ports, lambda x: {'total': sum(x.values()) % (1 << width)},
                  directory, vectors, patterns)
    stats = m.reduction_stats[0]
    hierarchy = elaborate(source, 'test', directory / 'elaboration')
    counts = Counter(row['module'] for row in hierarchy)
    full = f'fam_redundant_csa_{compressor.replace(":", "_")}'
    assert counts[full] == stats['full_word_cells'], (counts, stats)
    assert counts[full.replace('csa_', 'csa_bit_')] == stats['full_bit_cells'], (counts, stats)
    if compressor != '3:2':
        assert counts['fam_redundant_csa_3_2'] == stats['tail_3_2_word_cells'], (counts, stats)
    for row in hierarchy:
        if row['module'] == full:
            assert row['parameters']['W'] == width, row
            for name in 'abcdefg'[:int(compressor[0])]:
                assert row['ports'][name] == {'direction': 'input', 'width': width}, row
    if not tails:
        assert stats['full_word_cells'] > 0
    result.update(stats)
    result['primitive_modules'] = dict(counts)
    print(f'{directory.name}: PASS full={stats["full_word_cells"]} tail={stats["tail_3_2_word_cells"]}', flush=True)
    return result


def rns_activity(root, compressor, vectors):
    """Use seven independent three-bit chunks in the real RNS entry path.

    W21/count6 derives {15,16,17,31,7,11}.  Modulo seven, every chunk
    has weights 1,2,4, so its lowest bit is independently controllable.
    The first full outer reduction therefore has a column in which all
    selected inputs can be one at once, rather than padded/sparse zeros.
    """
    from chialu.targets.rtl.families import redundant as R
    from chialu.targets.rtl.families import library_closure
    from chialu.verify.alu_ref import normalize_spec
    from chialu.verify.variant_selftest import check_seed

    width, chunk, count = 21, 3, 6
    arity = int(compressor[0])
    pins = {'implementation': 'periodic_csa_moma', 'chunk_bits': chunk, 'moduli_count': count,
            'column_reducer.family': 'csa_tree', 'column_reducer.compressor': compressor,
            'column_reducer.final_cpa.family': 'parallel_prefix',
            'column_reducer.final_cpa.topology': 'brent_kung'}
    cfg = R.rns_cfg('rns_forward_converter', pins, width, 'adder')
    assert cfg['moduli'] == (15, 16, 17, 31, 7, 11), cfg
    m = Mod('test', 'input wire [20:0] x, output wire [2:0] total, '
            'output wire all_active, output wire [2:0] column', 'real RNS chunk compressor activity')
    value = R._fwd(m, 'x', width, 7, 'res', cfg, 'probe')
    m.assign('total', value)
    module = f'fam_redundant_csa_{compressor.replace(":", "_")}'
    instance = re.search(module + r' #\(\.W\(\d+\)\) (res_sum_csa\d+) ', '\n'.join(m.lines))
    assert instance, 'the selected complete outer compressor was not emitted'
    prefix = instance[1]
    m.assign('all_active', ' & '.join(f'{prefix}.{p}[0]' for p in 'abcdefg'[:arity]))
    expression = f"{{2'b0,{prefix}.s[0]}} + {{1'b0,{prefix}.carry[1],1'b0}}"
    expression += f" + {{{prefix}.carry2[2],2'b0}}" if arity == 7 else f" + {{1'b0,{prefix}.chain[1],1'b0}}"
    m.assign('column', expression)
    patterns = [{'x': sum(bit << (chunk*i) for i, bit in enumerate(bits))}
                for bits in product((0, 1), repeat=arity)]
    def reference(x):
        population = sum((x['x'] >> (chunk*i)) & 1 for i in range(arity))
        return {'total': x['x'] % 7, 'all_active': int(population == arity), 'column': population}
    directory = root / f'rns_activity_{arity}'
    source = m.render()
    result = _run(source, 'test', [Port('x', 'input', width), Port('total', 'output', 3),
                                     Port('all_active', 'output', 1), Port('column', 'output', 3)],
                  reference, directory, patterns=patterns)
    hierarchy = elaborate(source + library_closure(source), 'test', directory / 'elaboration')
    counts = Counter(row['module'] for row in hierarchy)
    assert counts[module] == sum(stat['full_word_cells'] for stat in m.reduction_stats)
    assert counts[module.replace('csa_', 'csa_bit_')] == sum(stat['full_bit_cells'] for stat in m.reduction_stats)
    final = re.search(r'(fam_prefix_brent_kung_w\d+) (u\d+) \([^\n]*\.s\(res_sum_r\)', source)
    assert final, 'the selected final CPA was not connected to the reduction output'
    assert any(row['module'] == final[1] and row['instance'] == final[2] for row in hierarchy)
    result.update(compressor=compressor, input_width=width, chunk_bits=chunk, moduli_count=count,
                  probed_instance=prefix, all_active_witness=patterns[-1]['x'], full_column_population=arity,
                  reductions=m.reduction_stats, primitive_modules=dict(counts), final_cpa_module=final[1])
    # The exact same binding also traverses the public ALU seed, including
    # the complete RNS reverse converter and the selected final CPA.
    spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                           'modes': [{'format': 'uint21', 'count': 1}], 'ops': ['add'],
                           'flags': ['carry', 'int_overflow', 'overflow']})
    chosen = {'core': ('rns_internal', {}), 'core.channels': ('rns_forward_converter', pins)}
    from chialu.verify.stimulus import plan_alu
    def plan_with_witness(*args, **kwargs):
        values, metadata = plan_alu(*args, **kwargs)
        for pattern in patterns:
            a, b = pattern['x'], 0
            values.append({'a': a, 'b': b})
            metadata.append({'op': 'add', 'mode': 0, 'count': 1, 'lane_pairs': [(a, b)], 'ctrl': {}, 'words': None})
        return values, metadata
    with patch('chialu.verify.stimulus.plan_alu', side_effect=plan_with_witness):
        seed_result = check_seed(spec, chosen, directory / 'seed', vectors, 947)
    assert seed_result['pass'], seed_result
    result['seed_pass'] = True
    result['seed_vectors'] = len((directory / 'seed' / 'expected.hex').read_text().split())
    result['seed_sha256'] = hashlib.sha256((directory / 'seed' / 'seed.sv').read_bytes()).hexdigest()
    print(f'RNS {compressor}: PASS full input activity, column population, and uint21 seed golden', flush=True)
    return result


def rejected_geometries():
    from chialu.targets.rtl.alu_seed import alu_seed
    from chialu.targets.rtl.families.redundant import rns_sv
    from chialu.verify.alu_ref import normalize_spec

    for compressor in ('4:2', '7:3'):
        pins = {'implementation': 'periodic_csa_moma', 'chunk_bits': 1, 'moduli_count': 3,
                'column_reducer.family': 'csa_tree', 'column_reducer.compressor': compressor}
        spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                               'modes': [{'format': 'uint1', 'count': 1}], 'ops': ['add']})
        chosen = {'core': ('rns_internal', {}), 'core.channels': ('rns_forward_converter', pins)}
        for callback in (lambda: rns_sv('adder', 1, 'rns_forward_converter', pins),
                         lambda: alu_seed(spec, families=chosen)):
            try:
                callback()
            except ValueError as error:
                assert 'requires at least one full compressor group' in str(error), error
            else:
                raise AssertionError(f'{compressor}: all-tail RNS target was accepted')
    print('PASS native and public ALU rejection of all-tail 4:2/7:3 targets', flush=True)


def owner_paths():
    from chialu.targets.rtl.families import redundant as R
    from chialu.targets.rtl.families.selection import SelectedPins, SelectionTrace
    for family, slot in (('csa_tree', 'final_cpa'), ('binary_tree', 'cpa')):
        pins = {'implementation': 'periodic_csa_moma', 'chunk_bits': 3,
                'modular_adder.family': 'parallel_prefix', 'modular_adder.topology': 'brent_kung',
                'column_reducer.family': family,
                f'column_reducer.{slot}.family': 'parallel_prefix',
                f'column_reducer.{slot}.topology': 'brent_kung'}
        if family == 'csa_tree':
            pins['column_reducer.compressor'] = '4:2'
        pins = SelectedPins('core.channels', pins)
        with SelectionTrace() as trace:
            R.rns_sv('adder', 21, 'rns_forward_converter', pins)
        wanted = {'core.channels.modular_adder', 'core.channels.column_reducer.' + slot}
        observed = {owner for owner, selected, _, _ in trace.generated if selected == 'parallel_prefix'}
        assert wanted <= observed, (wanted, observed)
        assert all('family' not in own for owner, _, own, _ in trace.generated if owner in wanted)
    print('PASS column CPA selectors retain both complete owner paths', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--vectors', type=int, default=96)
    parser.add_argument('--section', choices=('all', 'cells', 'rns'), default='all')
    args = parser.parse_args()
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-redundant-reduce-'))
    root.mkdir(parents=True, exist_ok=True)
    results = primitives(root) if args.section != 'rns' else []
    for compressor in ('3:2', '4:2', '7:3') if args.section != 'rns' else ():
        arity = int(compressor[0])
        for count in sorted({arity, arity+1, 2*arity+1, 31}):
            for width in (2, 8, 17):
                results.append(tree(root, compressor, count, width, args.vectors))
        results.append(tree(root, compressor, arity, 1, args.vectors))
        if arity > 3:
            result = tree(root, compressor, 3, 5, args.vectors, tails=True)
            assert result['full_word_cells'] == 0 and result['tail_3_2_word_cells'] == 1
            results.append(result)
        for count in range(arity):
            try:
                csa_rows(Mod('bad', '', ''), ['a']*count, 8, 'bad', compressor, require_full=True)
            except ValueError as error:
                assert 'actual input rows' in str(error)
            else:
                raise AssertionError(f'{compressor}: padded small row count accepted')
    if args.section != 'cells':
        owner_paths()
        rejected_geometries()
        for compressor in ('4:2', '7:3'):
            results.append(rns_activity(root, compressor, args.vectors))
    (root / 'summary.json').write_text(json.dumps(results, indent=2))
    print(f'PASS {len(results)} cases; {sum(r["vectors"]+r.get("seed_vectors", 0) for r in results)} vectors; {root}', flush=True)


if __name__ == '__main__':
    main()
