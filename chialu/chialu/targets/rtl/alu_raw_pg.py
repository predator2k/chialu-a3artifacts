"""Plan and wire a raw-pattern PG/CPA shared by integer and floating operations."""
from chialu.verify import alu_ref as A


def plan(manifest, modes, legal, families, dual):
    selected = [mi for mi, (_, fmt) in enumerate(modes)
                if A.family_of(fmt) in ('float', 'posit', 'block') and (families or {}).get(f'core.logic.m{mi}', (None,))[0] == 'alu_pg_fused']
    groups = {}
    for mi in selected:
        count, fmt = modes[mi]
        width = fmt.width
        candidates = [index for index, (lanes, other) in enumerate(modes)
                      if getattr(other, 'encoding', '') in ('twos_complement', 'unsigned') and A.family_of(other) in ('integer', 'fixed')
                      and other.width == width and lanes >= count and f'core.adder.m{index}' in (families or {})
                      and any(st.kind == 'adder' and st.mode == index for st in manifest)]
        if dual:
            candidates = [index for index in candidates if any((index, op) in legal for op in ('neg', 'abs'))]
        if not candidates:
            raise ValueError(f'core.logic.m{mi}: raw PG sharing needs a same-width binary integer adder with enough lanes'
                             + (' and neg/abs for both unary result sets' if dual else ''))
        companion = candidates[0]
        group = groups.setdefault((width, companion), {'width': width, 'companion': companion, 'logic_modes': [], 'sets': 2 if dual else 1})
        group['logic_modes'].append(mi)
    by_mode = {}
    for group in groups.values():
        group['modes'] = group['logic_modes'] + [group['companion']]
        group['owners'] = [f'core.logic.m{mi}' for mi in group['logic_modes']]
        if (families or {}).get(f"core.logic.m{group['companion']}", (None,))[0] == 'alu_pg_fused':
            group['owners'].append(f"core.logic.m{group['companion']}")
        for mi in group['modes']:
            by_mode[mi] = dict(group, role='adder' if mi == group['companion'] else 'logic', count=modes[mi][0])
    return list(groups.values()), by_mode


def ports(info, mi, kind):
    if kind != info['role']:
        return []
    count = info['count'] * info['sets']
    width = info['width']
    return [(f'pg_{name}_m{mi}', 'out', count * width) for name in ('a', 'b')] + \
           [(f'pg_{name}_m{mi}', 'out', count) for name in ('cin', 'use_g')] + \
           [(f'pg_{name}_m{mi}', 'in', count * width) for name in ('p', 'g', 'sum')] + \
           [(f'pg_cout_m{mi}', 'in', count)]


def wire(top, groups, modes, families, library_used, mode_width):
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.alu_pg import fused_module
    for ordinal, group in enumerate(groups):
        width, companion, sets = group['width'], group['companion'], group['sets']
        family, pins = families[f'core.adder.m{companion}']
        adder = FAM.adder_module(family, pins, width)
        if adder is None:
            raise ValueError(f'raw PG companion {family} rejected width {width}')
        module = None
        for owner in group['owners']:
            module = fused_module(adder, width, owner, use_gate=True,
                                  consumers=group['owners'] + [f'core.adder.m{companion}'])
        for name, text in FAM.module_texts(module.name, module.text).items():
            FAM.collect_modules(library_used, ((name, text),))
        for mi in group['modes']:
            count = modes[mi][0] * sets
            for name in ('p', 'g', 'sum'):
                top.logic(f'pg_{name}_m{mi}', count * width)
            top.logic(f'pg_cout_m{mi}', count)
        for lane in range(modes[companion][0]):
            for si in range(sets):
                served = [mi for mi in group['modes'] if lane < modes[mi][0]]
                conns = {}
                for name, bits in [('a', width), ('b', width), ('cin', 1), ('use_g', 1)]:
                    signal = top.logic(f'rawpg{ordinal}_{name}_l{lane}_s{si}', bits)
                    choices = []
                    for mi in served:
                        index = si * modes[mi][0] + lane
                        bus = f'pg_{name}_m{mi}'
                        value = f'{bus}[{index*width} +: {width}]' if bits > 1 else f'{bus}[{index}]' if modes[mi][0]*sets > 1 else bus
                        choices.append(f'mode == {mode_width}\'d{mi} ? {value}')
                    top.assign(signal, ' : '.join(choices) + " : '0")
                    conns[name] = signal
                for name, port, bits in [('p', 'pg_p', width), ('g', 'pg_g', width), ('sum', 's', width), ('cout', 'cout', 1)]:
                    signal = top.logic(f'rawpg{ordinal}_{name}_l{lane}_s{si}', bits)
                    conns[port] = signal
                    for mi in served:
                        index = si * modes[mi][0] + lane
                        bus = f'pg_{name}_m{mi}'
                        target = f'{bus}[{index*width} +: {width}]' if bits > 1 else f'{bus}[{index}]' if modes[mi][0]*sets > 1 else bus
                        top.assign(target, signal)
                conns.update({name: name for name, _ in module.ctrl})
                top.instance(module.name, f'u_rawpg{ordinal}_l{lane}_s{si}', conns)
