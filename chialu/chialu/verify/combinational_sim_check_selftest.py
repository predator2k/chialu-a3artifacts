"""Exercise independent source checking and Yosys simlib cell semantics."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile

from chialu.verify.combinational_sim import emit_module  # Test input generation only.
from chialu.verify.combinational_sim_check import CorrespondenceError, verify_source


BINARY = ('$and', '$or', '$xor', '$ge', '$gt', '$lt', '$logic_and', '$mul', '$sub', '$add', '$eq')


def network(kind, aw=2, bw=3, yw=4, signed_a=0, signed_b=0):
    ports, connections, position = {}, {}, 2
    names = [('A', aw)] + ([] if kind in ('$not', '$logic_not', '$neg') else [('B', bw)])
    if kind in ('$mux', '$_MUX_'):
        names += [('S', 1)]
    for name, width in names:
        bits = list(range(position, position + width))
        position += width
        ports[name] = {'direction': 'input', 'bits': bits,
                       'signed': signed_a if name == 'A' else signed_b if name == 'B' else 0}
        connections[name] = bits[:]
    bits = list(range(position, position + yw))
    ports['Y'] = {'direction': 'output', 'bits': bits, 'signed': 0}
    connections['Y'] = bits[:]
    if kind == '$_MUX_':
        parameters = {}
    elif kind == '$mux':
        parameters = {'WIDTH': yw}
    else:
        parameters = {'A_WIDTH': aw, 'A_SIGNED': signed_a, 'Y_WIDTH': yw}
        if kind not in ('$not', '$logic_not', '$neg'):
            parameters.update(B_WIDTH=bw, B_SIGNED=signed_b)
    cell = {'type': kind, 'parameters': parameters,
            'port_directions': {name: 'input' if name != 'Y' else 'output' for name in connections},
            'connections': connections}
    return {'ports': ports, 'cells': {'cell0': cell}}


def rejects(module, source, top='dut'):
    try:
        verify_source(module, source, top)
    except CorrespondenceError:
        return
    raise AssertionError('mutated source or graph was accepted')


def mutations():
    count = 0
    for kind in BINARY + ('$not', '$logic_not', '$neg', '$mux', '$_MUX_'):
        module = network(kind, 1, 1, 1) if kind in ('$mux', '$_MUX_') else network(kind)
        source = emit_module(module, 'dut')[0]
        before = deepcopy(module)
        assert verify_source(module, source, 'dut')['pass']
        assert module == before, 'checker changed the JSON module'
        if kind in ('$mux', '$_MUX_'):
            bad = source.replace(' ? ', ' : ', 1)
        elif kind == '$not':
            bad = source.replace(' = ~', ' = !', 1)
        elif kind == '$logic_not':
            bad = source.replace(' = !', ' = ~', 1)
        elif kind == '$neg':
            bad = source.replace(' = -', ' = ~', 1)
        else:
            token = {'$and': '&', '$or': '|', '$xor': '^', '$ge': '>=', '$gt': '>',
                     '$lt': '<', '$logic_and': '&&', '$mul': '*', '$sub': '-', '$add': '+', '$eq': '=='}[kind]
            replacement = '|' if token != '|' else '&'
            bad = source.replace(f') {token} (', f') {replacement} (', 1)
        rejects(module, bad)
        changed = deepcopy(module)
        con = changed['cells']['cell0']['connections']
        con['A'][0] = '1'
        rejects(changed, source)
        count += 2
    module = network('$sub', signed_a=1, signed_b=1)
    source = emit_module(module, 'dut')[0]
    bad = re.sub(r'\$signed\((n\[\d+\]\[\d+(?::\d+)?\])\)', r'\1', source, count=1)
    assert bad != source
    rejects(module, bad)
    for replacement in (
            source.replace('input wire signed [1:0] A', 'input wire [1:0] A', 1),
            source.replace('input wire signed [1:0] A', 'input wire signed [2:0] A', 1),
            source.replace('input [1:0] i0', 'input [2:0] i0', 1),
            source.replace('automatic [3:0]', 'automatic [4:0]', 1),
            source.replace('reg [63:0]', 'reg [62:0]', 1),
            source.replace('n [0:0]', 'n [0:1]', 1),
            source.replace('n[0][3:2] = i0', 'n[0][3:2] = i1', 1),
            source.replace('n[0][3:2] = i0', '{n[0][2],n[0][3]} = i0', 1),
            source.replace('n[0][10:7] =', '{n[0][7],n[0][10:8]} =', 1),
            source.replace('$signed(n[0][3:2])', '$signed({n[0][2],n[0][3]})', 1),
            source.replace('reg [63:0]', '(* mem2reg *) reg [63:0]', 1),
            source.replace('begin\n', 'begin\n$display("extra");\n', 1),
            source.replace('endfunction\n', "endfunction\nassign Y = 4'b0;\n", 1),
            source.replace('endmodule', 'endmodule\nmodule extra; endmodule', 1),
            source + '// not part of the grammar\n',
            source.replace('evaluate(A,B)', 'evaluate(B,A)', 1),
            source.replace("evaluate={n[0][10:7]}", "evaluate={n[0][10:8],n[0][6]}", 1),
    ):
        assert replacement != source
        rejects(module, replacement)
        count += 1
    count += 1
    for modify in (
            lambda m: m['cells']['cell0']['parameters'].update(A_WIDTH=3),
            lambda m: m['cells']['cell0']['parameters'].update(A_SIGNED=2),
            lambda m: m['cells']['cell0']['parameters'].update(UNRECOGNIZED=1),
            lambda m: m['cells']['cell0'].update(type='$div'),
            lambda m: m['cells']['cell0']['connections']['Y'].__setitem__(0, 2),
            lambda m: m['cells']['cell0']['connections']['Y'].__setitem__(1, m['cells']['cell0']['connections']['Y'][0]),
            lambda m: m['cells']['cell0']['connections']['A'].__setitem__(0, 999),
            lambda m: m['cells']['cell0']['connections']['A'].__setitem__(0, True),
            lambda m: m['cells']['cell0']['connections']['A'].__setitem__(0, 'z'),
            lambda m: m['ports']['B']['bits'].__setitem__(0, 2),
            lambda m: m['ports']['A'].update(direction='inout'),
            lambda m: m['ports']['A'].update(offset=1),
            lambda m: m.update(memories={'mem': {}}),
            lambda m: m.update(processes={'process': {}}),
            lambda m: m.update(unknown_behavior={}),
            lambda m: m.update(attributes={'blackbox': '1'}),
            lambda m: m.update(attributes={'whitebox': '1'}),
            lambda m: m.update(netnames=[]),
            lambda m: m.update(parameter_default_values={'WIDTH': '100'}),
    ):
        changed = deepcopy(module)
        modify(changed)
        rejects(changed, source)
        count += 1
    # Two-cell dependency: the checker permits another valid topological
    # order, but never reads a producer after its consumer has executed.
    chain = network('$and', 2, 2, 2)
    chain['ports']['Y']['bits'] = [8, 9]
    chain['cells']['cell1'] = deepcopy(chain['cells']['cell0'])
    chain['cells']['cell1'].update(type='$xor')
    chain['cells']['cell1']['connections'] = {'A': [6, 7], 'B': [2, 3], 'Y': [8, 9]}
    source = emit_module(chain, 'dut')[0]
    lines = source.splitlines()
    indices = [i for i, line in enumerate(lines) if ' = (' in line]
    assert len(indices) == 2
    wrong = lines[:]
    wrong[indices[0]], wrong[indices[1]] = wrong[indices[1]], wrong[indices[0]]
    rejects(chain, '\n'.join(wrong))
    rejects(chain, source.replace(lines[indices[0]] + '\n', '', 1))
    rejects(chain, source.replace(lines[indices[0]], lines[indices[0]] + '\n' + lines[indices[0]], 1))
    cycle = deepcopy(chain)
    cycle['cells']['cell0']['connections']['A'] = [8, 9]
    rejects(cycle, source)
    independent = deepcopy(chain)
    independent['cells']['cell1']['connections']['A'] = [4, 5]
    source = emit_module(independent, 'dut')[0]
    lines = source.splitlines()
    indices = [i for i, line in enumerate(lines) if ' = (' in line]
    lines[indices[0]], lines[indices[1]] = lines[indices[1]], lines[indices[0]]
    assert verify_source(independent, '\n'.join(lines), 'dut')['pass']
    count += 4
    mux = network('$_MUX_', 1, 1, 1)
    mux['cells']['cell0']['connections']['A'] = ['x']
    source = emit_module(mux, 'dut')[0]
    assert verify_source(mux, source, 'dut')['pass']
    rejects(mux, source.replace("1'bx", "1'b0"))
    metadata = deepcopy(mux)
    metadata['cells']['scope'] = {'type': '$scopeinfo', 'parameters': {}, 'connections': {}, 'port_directions': {}}
    assert verify_source(metadata, source, 'dut')['ignored_metadata_cells'] == 1
    metadata['cells']['scope']['connections'] = {'A': []}
    rejects(metadata, source)
    count += 2
    print(f'PASS {count} source/graph mutations, independent statement order, metadata and input immutability', flush=True)
    return count


def primitive_networks():
    cases = []
    for kind in BINARY:
        for aw, bw, yw, signed_a, signed_b in itertools.product((1, 2, 3), (1, 2, 3), (1, 3, 6), (0, 1), (0, 1)):
            cases.append(network(kind, aw, bw, yw, signed_a, signed_b))
    for aw, yw, signed in itertools.product((1, 2, 3), (1, 3, 6), (0, 1)):
        for kind in ('$not', '$logic_not', '$neg'):
            cases.append(network(kind, aw, 0, yw, signed))
    for width in (1, 2, 3, 5):
        cases.append(network('$mux', width, width, width))
    cases.append(network('$_MUX_', 1, 1, 1))
    cases.append(network('$xor', 70, 70, 73, 1, 1))
    reordered = network('$sub', 2, 3, 4, 1, 1)
    reordered['cells']['cell0']['connections']['A'] = [3, '0', 2]
    reordered['cells']['cell0']['parameters']['A_WIDTH'] = 3
    reordered['ports']['Y']['bits'].reverse()
    cases.append(reordered)
    # No constant-x connection: Verilator is two-state and resolves a 1'bx
    # literal per context (~$signed(1'bx) folds to 0s inline, while the same
    # literal through the simlib port reads as 0 and inverts to 1s), so
    # neither side has a value to compare. The mutation section checks that
    # an x constant is emitted as 1'bx and that 1'b0 in its place is rejected.
    return cases


def yosys_share(explicit=None):
    if explicit is not None:
        directory = Path(explicit).resolve()
    elif os.environ.get('YOSYSDATDIR'):
        directory = Path(os.environ['YOSYSDATDIR']).resolve()
    else:
        executable = shutil.which('yosys')
        if executable is None:
            raise ValueError('Yosys data files require --yosys-share or YOSYSDATDIR')
        directory = Path(executable).resolve().parent.parent / 'share' / 'yosys'
    if not all((directory / name).is_file() for name in ('simlib.v', 'simcells.v')):
        raise ValueError(f'Yosys simlib.v/simcells.v absent at {directory}; supply --yosys-share')
    return directory


def primitive_semantics(directory, share=None, cases=None):
    directory.mkdir(parents=True, exist_ok=True)
    if cases is None:
        matrix = primitive_networks()
        batches = [primitive_semantics(directory / f'batch_{start//64:02}', share, matrix[start:start+64])
                   for start in range(0, len(matrix), 64)]
        report = {'pass': all(batch['pass'] for batch in batches),
                  'cell_geometries': sum(batch['cell_geometries'] for batch in batches),
                  'patterns': sum(batch['patterns'] for batch in batches),
                  'cell_kinds': sorted({kind for batch in batches for kind in batch['cell_kinds']}),
                  'batches': [str((directory / f'batch_{i:02}' / 'result.json').resolve()) for i in range(len(batches))],
                  'reference': 'official Yosys simlib/simcells; hashes and commands in each batch'}
        assert report['cell_geometries'] == len(matrix)
        (directory / 'result.json').write_text(json.dumps(report, indent=2))
        print(f'PASS complete matrix: {report["cell_geometries"]} geometries / {report["patterns"]} patterns', flush=True)
        return report
    source, declarations, actions = [], [], []
    required = set()
    comparisons = 0
    rng = random.Random(17)
    for index, module in enumerate(cases):
        top = f'checked_cell_{index}'
        emitted = emit_module(module, top)[0]
        assert verify_source(module, emitted, top)['pass']
        source.append(emitted)
        cell = module['cells']['cell0']
        kind = cell['type']
        required.add(kind)
        wire_values = {}
        inputs = [(name, p) for name, p in module['ports'].items() if p['direction'] == 'input']
        outputs = [(name, p) for name, p in module['ports'].items() if p['direction'] == 'output']
        for name, port in inputs:
            var = f'p{index}_{name}'
            declarations.append(f'reg [{len(port["bits"])-1}:0] {var};')
            for bit_index, bit in enumerate(port['bits']):
                wire_values[bit] = f'{var}[{bit_index}]'
        width = len(cell['connections']['Y'])
        declarations.append(f'wire [{width-1}:0] r{index};')
        for bit_index, bit in enumerate(cell['connections']['Y']):
            wire_values[bit] = f'r{index}[{bit_index}]'

        def expression(bits):
            # Reference connects external input bits directly to simlib.
            # No wire-bank layout or source-expression helper is shared.
            return '{' + ','.join("1'b" + b if isinstance(b, str) else wire_values[b] for b in reversed(bits)) + '}'

        params = ','.join(f'.{name}({value})' for name, value in cell['parameters'].items())
        conns = [f'.{port}({expression(bits)})' for port, bits in cell['connections'].items() if port != 'Y']
        conns.append(f'.Y(r{index})')
        declarations.append('\\' + kind + (' #(' + params + ')' if params else '') + f' reference_{index} ({",".join(conns)});')
        process_conns = [f'.{name}(p{index}_{name})' for name, _ in inputs]
        for name, port in outputs:
            declarations.append(f'wire [{len(port["bits"])-1}:0] q{index}_{name};')
            process_conns.append(f'.{name}(q{index}_{name})')
        declarations.append(f'{top} candidate_{index} ({",".join(process_conns)});')
        bits = sum(len(p['bits']) for _, p in inputs)
        if bits <= 11:
            patterns = list(itertools.product(*(range(1 << len(p['bits'])) for _, p in inputs)))
        else:
            patterns = [tuple(value & ((1 << len(p['bits'])) - 1) for _, p in inputs)
                        for value in (0, 1, -1, 1 << 69, (1 << 69) - 1, int('10' * 35, 2))]
            patterns += [tuple(rng.getrandbits(len(p['bits'])) for _, p in inputs) for _ in range(16)]
        # Local four-state operator checks supplement the binary input scope
        # of the DUT runner; they do not authorize unknown DUT outputs.
        patterns += [('x',) * len(inputs), ('z',) * len(inputs)]
        for values in patterns:
            for (name, port), value in zip(inputs, values):
                width_in = len(port['bits'])
                literal = f"{width_in}'b" + value * width_in if isinstance(value, str) else f"{width_in}'d{value}"
                actions.append(f'p{index}_{name}={literal};')
            actions.append('#1;')
            for name, port in outputs:
                actions.append(f'if(q{index}_{name} !== {expression(port["bits"])}) $fatal(1,"cell {index} {kind} mismatch");')
            comparisons += 1
    library_directory = yosys_share(share)
    libraries = [library_directory / 'simlib.v', library_directory / 'simcells.v']
    for kind in sorted(required):
        body = None
        for path in libraries:
            candidate = re.search(r'module\s+\\' + re.escape(kind) + r'\s*\(.*?\bendmodule\b', path.read_text(), re.S)
            if candidate:
                body = candidate[0]
                break
        assert body is not None, kind
        source.append(body)
    source += ['module tb;', *declarations, 'initial begin', *actions,
               f'$display("PASS {len(cases)} cell geometries / {comparisons} patterns"); $finish; end endmodule']
    path = directory / 'cells.sv'
    path.write_text('\n'.join(source) + '\n')
    from chialu.verify import simulate as SIM
    compile_command = ['verilator', *SIM.VERILATOR_FLAGS, '-j', str(SIM.VERILATOR_JOBS),
                       '--top-module', 'tb', '-Mdir', 'obj_sim', '-o', 'sim', 'cells.sv']
    result = subprocess.run(compile_command, cwd=directory, capture_output=True, text=True, timeout=600)
    (directory / 'compile.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    result = subprocess.run(['./obj_sim/sim'], cwd=directory, capture_output=True, text=True, timeout=120)
    (directory / 'simulation.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    assert 'PASS ' in result.stdout and 'FATAL' not in result.stdout, result.stdout
    report = {'pass': True, 'cell_geometries': len(cases), 'patterns': comparisons, 'cell_kinds': sorted(required),
              'references': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in libraries},
              'test_source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'commands': [compile_command, ['./obj_sim/sim']]}
    (directory / 'result.json').write_text(json.dumps(report, indent=2))
    print(result.stdout.strip(), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--section', choices=('all', 'mutations', 'cells'), default='all')
    parser.add_argument('--yosys-share', type=Path, help='directory containing official simlib.v and simcells.v')
    args = parser.parse_args()
    root = (args.out or Path(tempfile.mkdtemp(prefix='chialu-comb-check-'))).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.section != 'cells':
        mutations()
    if args.section != 'mutations':
        primitive_semantics(root, args.yosys_share)


if __name__ == '__main__':
    main()
