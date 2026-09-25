"""Optional simulation scheduling for a checked, two-state combinational DAG.

The seed source is never rewritten. Yosys elaborates the SystemVerilog; a
straight-line automatic function evaluates the resulting cells without
scheduling every intermediate glitch. A separate source checker
must accept every cell and connection before the new source is simulated.
Original hierarchy audits and original-path timeouts remain separate.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import json
import marshal
from pathlib import Path
import re
import shutil
import subprocess
import time


SOURCE_SHA256_AT_IMPORT = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


_BINARY = {'$and': '&', '$or': '|', '$xor': '^', '$ge': '>=',
           '$gt': '>', '$lt': '<', '$eq': '==', '$logic_and': '&&', '$mul': '*', '$sub': '-', '$add': '+'}
_MUX = ('$mux', '$_MUX_')
_UNARY = {'$not': '~', '$logic_not': '!', '$neg': '-'}


def _require(condition, detail):
    if not condition:
        raise ValueError(detail)


def _parameter(cell, name):
    value = cell['parameters'][name]
    if isinstance(value, str):
        _require(bool(re.fullmatch('[01]+', value)), f'non-binary parameter {name}')
        return int(value, 2)
    _require(type(value) is int, f'invalid parameter {name}')
    return value


def emit_module(module, top):
    """Render the deliberately small grammar accepted by the independent checker."""
    _require(bool(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', top)), 'unsupported top identifier')
    _require(not module.get('memories') and not module.get('processes'), 'unlowered memory or process')
    ports = module['ports']
    inputs, outputs = [], []
    for name, port in ports.items():
        _require(bool(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name)), 'unsupported port identifier')
        _require(port.get('offset', 0) == 0 and not port.get('upto'), 'only descending zero-based ports are supported')
        _require(port['bits'] and port['direction'] in ('input', 'output'), 'empty port or inout')
        (inputs if port['direction'] == 'input' else outputs).append((name, port))
    _require(inputs and outputs, 'at least one input and output required')
    cells, metadata = [], 0
    for name, cell in module['cells'].items():
        if cell['type'] == '$scopeinfo':
            _require(not cell['connections'] and not cell['port_directions'], 'connected metadata cell')
            metadata += 1
            continue
        _require(cell['type'] in {*_BINARY, *_UNARY, *_MUX}, f'unsupported cell {name}: {cell["type"]}')
        expected = {'A': 'input', 'Y': 'output'}
        if cell['type'] not in _UNARY:
            expected['B'] = 'input'
        if cell['type'] in _MUX:
            expected['S'] = 'input'
        _require(cell['port_directions'] == expected and set(cell['connections']) == set(expected), 'cell port mismatch')
        con = cell['connections']
        _require(all(con.values()), 'empty cell connection')
        if cell['type'] in _MUX:
            width = 1 if cell['type'] == '$_MUX_' else _parameter(cell, 'WIDTH')
            _require(width == len(con['A']) == len(con['B']) == len(con['Y']) and len(con['S']) == 1,
                     'mux width mismatch')
        else:
            for port in ('A', 'Y') + (() if cell['type'] in _UNARY else ('B',)):
                _require(_parameter(cell, port + '_WIDTH') == len(con[port]), 'cell width mismatch')
            for port in ('A',) + (() if cell['type'] in _UNARY else ('B',)):
                _require(_parameter(cell, port + '_SIGNED') in (0, 1), 'invalid signedness')
        cells.append(cell)
    owners = {}
    def driven(bits, owner):
        for bit in bits:
            _require(type(bit) is int and bit >= 2 and bit not in owners, 'non-wire or multiple driver')
            owners[bit] = owner
    for _, port in inputs:
        driven(port['bits'], None)
    for index, cell in enumerate(cells):
        driven(cell['connections']['Y'], index)
    def owner_of(bit):
        if type(bit) is str:
            _require(bit in ('0', '1', 'x'), 'unsupported constant')
            return None
        _require(type(bit) is int and bit in owners, f'undriven bit {bit}')
        return owners[bit]
    children, pending = [[] for _ in cells], []
    for index, cell in enumerate(cells):
        deps = {owner_of(bit) for port, bits in cell['connections'].items() if port != 'Y' for bit in bits}
        deps.discard(None)
        pending.append(len(deps))
        for owner in deps:
            children[owner].append(index)
    for _, port in outputs:
        for bit in port['bits']:
            owner_of(bit)
    ready = deque(index for index, count in enumerate(pending) if not count)
    order = []
    while ready:
        index = ready.popleft()
        order.append(index)
        for child in children[index]:
            pending[child] -= 1
            if pending[child] == 0:
                ready.append(child)
    _require(len(order) == len(cells), 'combinational cycle')

    def expression(bits):
        groups = []
        for bit in bits:
            if type(bit) is str:
                groups.append((None, bit, bit))
                continue
            bank, offset = divmod(bit, 64)
            if groups and groups[-1][0] == bank and groups[-1][2] + 1 == offset:
                groups[-1] = (bank, groups[-1][1], offset)
            else:
                groups.append((bank, offset, offset))
        pieces = []
        for bank, low, high in reversed(groups):
            if bank is None:
                pieces.append("1'b" + low)
            elif low == 0 and high == 63:
                pieces.append(f'n[{bank}]')
            elif low == high:
                pieces.append(f'n[{bank}][{low}]')
            else:
                pieces.append(f'n[{bank}][{high}:{low}]')
        return pieces[0] if len(pieces) == 1 else '{' + ','.join(pieces) + '}'

    # Bound even malformed sparse IDs before declaring the procedural array.
    _require(max(owners) < 64 * max(1024, len(owners)), 'excessively sparse bit IDs')
    lines = [f'module {top}(' + ','.join(f"{p['direction']} wire {'signed ' if p.get('signed') else ''}[{len(p['bits'])-1}:0] {n}"
                                        for n, p in ports.items()) + ');']
    lines += [f'function automatic [{sum(len(p["bits"]) for _, p in outputs)-1}:0] evaluate;']
    lines += [f'input [{len(p["bits"])-1}:0] i{i};' for i, (_, p) in enumerate(inputs)]
    lines += [f'reg [63:0] n [0:{max(owners)//64}];', 'begin']
    lines += [f'{expression(p["bits"])} = i{i};' for i, (_, p) in enumerate(inputs)]
    for index in order:
        cell = cells[index]
        con, kind = cell['connections'], cell['type']
        a = expression(con['A'])
        if kind in _MUX:
            rhs = f'{expression(con["S"])} ? {expression(con["B"])} : {a}'
        elif kind in _UNARY:
            rhs = _UNARY[kind] + (f'$signed({a})' if _parameter(cell, 'A_SIGNED') else a)
        else:
            b = expression(con['B'])
            if _parameter(cell, 'A_SIGNED') and _parameter(cell, 'B_SIGNED'):
                a, b = f'$signed({a})', f'$signed({b})'
            rhs = f'({a}) {_BINARY[kind]} ({b})'
        lines += [f'{expression(con["Y"])} = {rhs};']
    lines += ['evaluate={' + ','.join(expression(p['bits']) for _, p in outputs) + '};', 'end', 'endfunction',
              'assign {' + ','.join(n for n, _ in outputs) + '}=evaluate(' + ','.join(n for n, _ in inputs) + ');', 'endmodule']
    return '\n'.join(lines) + '\n', {'cells': len(cells), 'types': dict(Counter(c['type'] for c in cells)),
                                   'ignored_metadata_cells': metadata, 'acyclic': True, 'unique_drivers': True}


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def simulate(source, top, bench, directory, *, timeout=600):
    """Simulate supplied source/bench; vectors and expected files must already exist.

    This entry point requires bit-exact expected outputs. It raises on an
    unsupported network, failed certificate, failed command or
    incomplete/unknown/differing output. No fallback or automatic coverage mark.
    The caller must independently audit the original instantiated hierarchy.
    """
    from chialu.verify import combinational_sim_check
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    record = {'simulation_path': 'checked_combinational_process', 'top': top, 'formal': False,
              'state_domain': 'two-state stable combinational outputs',
              'frontend_assumption': 'the yosys frontend and the recorded Yosys passes preserve source semantics',
              'original_hierarchy_audit_required': True, 'pass': False, 'commands': [],
              'implementation_hashes': {
                  'emitter_source_observed_at_import': SOURCE_SHA256_AT_IMPORT,
                  'emitter_loaded_functions': hashlib.sha256(b''.join(marshal.dumps(fn.__code__) for fn in
                                            (_require, _parameter, emit_module, _hash, simulate))).hexdigest(),
                  'emitter_loaded_operations': dict(_BINARY),
                  'emitter_loaded_unary_operations': dict(_UNARY),
                  'checker_verify_loaded_code': hashlib.sha256(marshal.dumps(combinational_sim_check.verify_source.__code__)).hexdigest()}}
    (directory / 'lib.sv').write_text(source)
    (directory / 'tb.sv').write_text(bench)
    def save():
        (directory / 'procedural-result.json').write_text(json.dumps(record, indent=2) + '\n')
    def run(argv, output, seconds=timeout):
        start = time.monotonic()
        row = {'argv': argv, 'timeout_s': seconds, 'output': output}
        record['commands'].append(row)
        try:
            with (directory / output).open('w') as out, (directory / (output + '.stderr')).open('w') as err:
                completed = subprocess.run(argv, cwd=directory, stdout=out, stderr=err, timeout=seconds)
            row['returncode'] = completed.returncode
            completed.check_returncode()
        finally:
            row['seconds'] = round(time.monotonic() - start, 3)
            save()
    try:
        for tool, flag in (('yosys', '-V'), ('verilator', '--version')):
            run([tool, flag], tool + '-version.log', 20)
        _require(bool(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', top)), 'unsupported top identifier')
        from chialu.eda import frontend_read
        read = frontend_read(directory / 'lib.sv', top).strip()
        script = f'{read}; hierarchy -check -top {top}; proc; '
        script += 'setattr -mod -unset keep_hierarchy; setattr -unset keep_hierarchy; flatten; check -assert; opt; '
        script += 'memory_map; pmuxtree; techmap t:$shiftx; opt; clean; check -assert; write_json network.json'
        run(['yosys', '-Q', '-T', '-p', script], 'lowering.log')
        data = json.loads((directory / 'network.json').read_text())
        _require(set(data['modules']) == {top}, 'unflattened modules remain')
        module = data['modules'][top]
        lowered, record['network'] = emit_module(module, top)
        (directory / 'process.sv').write_text(lowered)
        record['certificate'] = combinational_sim_check.verify_source(module, lowered, top)
        del data, module, lowered
        # Verilator reads `process.sv` and `tb.sv` as they stand, so neither is converted here
        from chialu.verify import simulate as SIM
        shutil.rmtree(directory / 'obj_sim', ignore_errors=True)
        (directory / 'actual.hex').unlink(missing_ok=True)
        run(['verilator', *SIM.VERILATOR_FLAGS, '-j', str(SIM.VERILATOR_JOBS), '--top-module', 'tb',
             '-Mdir', 'obj_sim', '-o', 'sim', 'tb.sv', 'process.sv'], 'compile.log')
        _require((directory / 'obj_sim' / 'sim').is_file(), 'verilator produced no model')
        run(['./obj_sim/sim'], 'simulate.log')
        expected = (directory / 'expected.hex').read_text().split()
        actual = (directory / 'actual.hex').read_text().split()
        _require(bool(expected) and len(actual) == len(expected), 'incomplete simulation outputs')
        _require(all(re.fullmatch('[0-9a-fA-F]+', word) for word in actual + expected), 'unknown or malformed simulation word')
        mismatches = sum(int(a, 16) != int(b, 16) for a, b in zip(actual, expected))
        record.update(vectors=len(actual), mismatches=mismatches)
        _require(not mismatches, f'{mismatches} simulation mismatches')
        _require('PASS' in (directory / 'simulate.log').read_text() and 'FAIL' not in (directory / 'simulate.log').read_text(), 'bench did not pass')
        record['pass'] = True
    except Exception as exc:
        record['failure'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        record['hashes'] = {name: _hash(directory / name) for name in
                           ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex', 'algorithm.hex', 'network.json', 'process.sv', 'process.v', 'bench.v', 'actual.hex')
                           if (directory / name).exists()}
        save()
    return record


def revalidate(directory):
    """Check preserved passing artifacts with the currently loaded checker.

    This writes a new certificate without replacing the original report.
    It permits independent review after a checker version is frozen, even
    when the original worker retained an older imported checker module.
    """
    from chialu.verify import combinational_sim_check
    directory = Path(directory)
    record_path = directory / 'procedural-result.json'
    record = json.loads(record_path.read_text())
    _require(record.get('pass') is True, 'original simulation did not pass')
    required = ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex', 'network.json', 'process.sv', 'actual.hex')
    hashes = {}
    for name in required:
        hashes[name] = _hash(directory / name)
        _require(hashes[name] == record.get('hashes', {}).get(name), f'preserved artifact changed: {name}')
    data = json.loads((directory / 'network.json').read_text())
    top = record['top']
    _require(set(data['modules']) == {top}, 'unflattened modules remain')
    certificate = combinational_sim_check.verify_source(data['modules'][top], (directory / 'process.sv').read_text(), top)
    expected = (directory / 'expected.hex').read_text().split()
    actual = (directory / 'actual.hex').read_text().split()
    _require(bool(expected) and len(expected) == len(actual) == record['vectors'], 'incomplete preserved output')
    _require(all(re.fullmatch('[0-9a-fA-F]+', word) for word in actual + expected), 'unknown preserved output')
    _require(all(int(a, 16) == int(e, 16) for a, e in zip(actual, expected)), 'preserved outputs disagree')
    result = {'pass': True, 'vectors': len(actual), 'certificate': certificate, 'hashes': hashes,
              'original_report_sha256': _hash(record_path),
              'provenance': 'fresh correspondence check of unchanged simulation artifacts; original report retained',
              'old_version_hash_note': 'older reports may describe disk contents read after worker import; this certificate identifies the checker observed at its own import',
              'checker_verify_loaded_code': hashlib.sha256(marshal.dumps(combinational_sim_check.verify_source.__code__)).hexdigest()}
    (directory / 'revalidated-certificate.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('top')
    parser.add_argument('bench', type=Path)
    parser.add_argument('--data', type=Path, required=True, help='directory containing vectors.hex and expected.hex')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ('vectors.hex', 'expected.hex', 'algorithm.hex'):
        if (args.data / name).exists() and (args.data / name).resolve() != (args.out / name).resolve():
            shutil.copyfile(args.data / name, args.out / name)
    result = simulate(args.source.read_text(), args.top, args.bench.read_text(), args.out, timeout=args.timeout)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
