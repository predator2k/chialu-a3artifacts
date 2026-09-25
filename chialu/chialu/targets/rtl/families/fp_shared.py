"""Share the selected arithmetic cells of float format paths through mode muxes."""
from collections import defaultdict
import hashlib
import json
import re

from . import fp


def _connections(text):
    out = {}
    pos = 0
    while pos < len(text):
        match = re.search(r'\.(\w+)\s*\(', text[pos:])
        if match is None:
            break
        start = pos + match.end()
        depth, end = 1, start
        while depth:
            if text[end] == '(':
                depth += 1
            elif text[end] == ')':
                depth -= 1
            end += 1
        out[match.group(1)] = text[start:end-1]
        pos = end
    return out


def _ports(kind, width):
    unary = {'a': ('input', width)}
    if kind in ('lzc', 'tzc'):
        return dict(unary, n=('output', width.bit_length()))
    if kind == 'shifter':
        return dict(unary, amt=('input', max(1, (width-1).bit_length())), op=('input', 3),
                    y=('output', width), sticky=('output', 1))
    if kind == 'incr':
        return dict(unary, cin=('input', 1), s=('output', width), cout=('output', 1))
    if kind == 'adder':
        return dict(unary, b=('input', width), cin=('input', 1), s=('output', width),
                    cout=('output', 1), s1=('output', width))
    raise ValueError(f'sharing port contract is absent for {kind}')


def shared_sv(kind, formats, geometry, family, pins, tokens=None, mode_ids=None, name=None, normalized_input=False):
    """One physical selected cell per structural position across format modes.

    Format-dependent field extraction and final encoding stay combinational.
    Each corresponding LZC, barrel, CPA and incrementer receives a mode-muxed
    input and has one physical instance; its result fans back to those fields.
    An unpacker without normalization shares its exponent subtraction instead.
    """
    allowed = {'rounder': ('dedicated_per_op', 'shared_per_lane', 'shared_across_formats'),
               'unpacker': ('per_unit_unpack', 'shared_per_lane', 'shared_across_formats')}
    if family not in allowed.get(kind, ()):
        raise ValueError(f'format sharing does not implement {kind} family {family!r}')
    if len(formats) < 2 or len(set(f.name for f in formats)) < 2:
        raise ValueError('shared_across_formats needs at least two distinct formats')
    mode_ids = list(range(len(formats))) if mode_ids is None else list(mode_ids)
    key = json.dumps([kind, [f.name for f in formats], geometry.tag(), pins, mode_ids, bool(normalized_input)], sort_keys=True)
    if family != 'shared_across_formats':
        key += family
    name = name or 'fam_fp_shared_' + hashlib.sha256(key.encode()).hexdigest()[:16]
    captured = {}
    token = fp.capture_modules.set(captured)
    try:
        for index, fmt in enumerate(formats):
            path_name = f'{name}_format{index}'
            if kind == 'rounder':
                fp.round_sv(fmt, geometry, family, pins, tokens or {}, name=path_name, normalized_input=normalized_input)
            else:
                fp.unpack_sv(fmt, geometry, family, pins, name=path_name)
    finally:
        fp.capture_modules.reset(token)
    paths = [captured[f'{name}_format{i}'] for i in range(len(formats))]
    sw = max(1, max(mode_ids).bit_length())
    ports, body, extra = [f'input logic [{sw-1}:0] mode'], [], []
    groups = defaultdict(list)
    for index, path in enumerate(paths):
        declared = set(re.findall(r'\blogic(?:\s+signed)?(?:\s*\[[^]]+\])?\s+(\w+)', '\n'.join(path.lines + path.ports)))
        def rename(text):
            return re.sub(r'\b\w+\b', lambda m: f'f{index}_{m[0]}' if m[0] in declared else m[0], text)
        ports += [rename(port) for port in path.ports]
        instances = {n for n, *_ in path.instances}
        body += [rename(line) for line in path.lines if not any(re.search(rf'\bu{n}\s*\(', line) for n in instances)]
        occurrence = defaultdict(int)
        for number, child_kind, child_family, child_pins, width, conns, signed, head in path.instances:
            signature = json.dumps([child_kind, child_family, child_pins, width, signed, head], sort_keys=True)
            occurrence[signature] += 1
            connections = {port: rename(value) for port, value in _connections(conns).items()}
            groups[(signature, occurrence[signature])].append((index, child_kind, width, connections, head))
        extra += path.extra
    witnesses = []
    for ordinal, entries in enumerate(groups.values()):
        _index, child_kind, width, _, head = entries[0]
        contract = _ports(child_kind, width)
        connections = []
        for port, (direction, pw) in contract.items():
            if not any(port in entry[3] for entry in entries):
                continue
            wire = f'shared{ordinal}_{port}'
            body.append(f'  logic [{pw-1}:0] {wire};')
            connections.append(f'.{port}({wire})')
            if direction == 'input':
                options = [(mode_ids[i], conn.get(port, "'0") or "'0") for i, _, _, conn, _ in entries]
                expr = ' : '.join(f'(mode == {sw}\'d{mode}) ? ({value})' for mode, value in options) + " : '0"
                body.append(f'  assign {wire} = {expr};')
            else:
                for _, _, _, conn, _ in entries:
                    if conn.get(port):
                        body.append(f'  assign {conn[port]} = {wire};')
        body.append(f'  {head} shared_cell{ordinal} ({", ".join(connections)});')
        if len(entries) > 1:
            witnesses.append(f'{name}.shared_cell{ordinal}')
    if not witnesses and kind == 'unpacker' and not any(path.instances for path in paths):
        # With denormal_handling=in_datapath there is no LZC or barrel to
        # share. Mux the encoded exponent and its format's bias instead:
        # one subtraction produces the stored exponent for every format.
        # Field extraction, specials, DAZ and the hidden bit stay as above.
        ew = geometry.EW
        body = [re.sub(r'\s*assign f\d+_ex0 = [^;]+;', '', line) for line in body]
        for wire in ('shared_exp_code', 'shared_exp_bias', 'shared_exponent'):
            body.append(f'  logic signed [{ew-1}:0] {wire};')
        codes, biases = [], []
        for index, (fmt, mode) in enumerate(zip(formats, mode_ids)):
            code = f"$signed({{{{({ew}-{fmt.exp_bits}){{1'b0}}}}, f{index}_e}})"
            if fmt.man_bits:
                code = f"f{index}_sub_ ? {ew}'sd1 : {code}"
            cond = f"mode == {sw}'d{mode}"
            codes.append(f'({cond}) ? ({code})')
            biases.append(f'({cond}) ? {fp._slit(ew, fmt.bias + fmt.man_bits)}')
            body.append(f'  assign f{index}_ex0 = shared_exponent;')
        body.append('  assign shared_exp_code = ' + ' : '.join(codes) + " : '0;")
        body.append('  assign shared_exp_bias = ' + ' : '.join(biases) + " : '0;")
        body.append('  assign shared_exponent = shared_exp_code - shared_exp_bias;')
        witnesses.append(name)
    if not witnesses:
        raise ValueError(f'{kind}: no selected component can be physically shared across these formats; split the group')
    from .mul import dedupe_modules
    text = f'// {kind}: one physical cell at each shared position, selected by mode\nmodule {name} (\n  ' + ',\n  '.join(ports) + '\n);\n'
    text += '\n'.join(body) + '\nendmodule\n' + dedupe_modules(''.join(extra))
    return name, text, witnesses
