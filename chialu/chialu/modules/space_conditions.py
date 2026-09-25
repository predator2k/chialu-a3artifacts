"""Lower family-local domains and activity into the numeric variable tree.

These constraints apply before sampling; explicit declarations still pass the
renderer contracts. A union of choice domains is not a Cartesian product with
the family selector.
"""
from dataclasses import replace

from adir import Enum, Range


def constrain(space, prefix, variables, *, kind, modes, spec, independent=False):
    from chialu.targets.rtl.families.alu_contracts import ALU_ACTIVITY_RULES
    out = {v.name: v for v in variables}

    def walk(families, base):
        choices, slots = {}, {}
        for family in families:
            for choice, domain in family.design_choices.items():
                choices.setdefault(choice, []).append((family.name, domain))
            for slot, sub in family.components.items():
                children = slots.setdefault(slot, {})
                children.update({f.name: f for f in sub.families})
        for choice, entries in choices.items():
            name = base + '.' + choice
            var = out.get(name)
            if var is None or len(entries) < 2 or not var.domain.finite():
                continue
            members = var.domain.members()
            legal = [value for value in members if any(domain.contains(value) for _, domain in entries)]
            if len(legal) != len(members):
                var = replace(var, domain=Enum(tuple(legal)))
                out[name] = var
            conditions = dict(var.member_when or {})
            for value in var.domain.members():
                allowed = tuple(f for f, domain in entries if domain.contains(value))
                if len(allowed) != len(entries) and value not in conditions:
                    conditions[value] = (base + '.family', allowed,
                                         'the value belongs to the selected family\'s choice domain')
            if conditions:
                out[name] = replace(var, member_when=conditions)
        names = {f.name for f in families}
        for owners, keys, tests, reason in ALU_ACTIVITY_RULES:
            applicable = tuple(f for f in owners if f in names)
            if not applicable:
                continue
            clause = [(base + '.family', applicable)]
            for control, members, required in tests:
                var = out.get(base + '.' + control)
                if var is None:
                    break
                allowed = tuple(v for v in var.domain.members() if (v in members) == required)
                if not allowed:
                    break
                clause.append((var.name, allowed))
            else:
                for key in keys:
                    name = base + '.' + key + ('.family' if key in slots else '')
                    if name in out:
                        var = out[name]
                        out[name] = replace(var, inactive_when=var.inactive_when + (tuple(clause),))
        if 'lza' in names and kind == 'fp_adder':
            name = base + '.indicator_restriction'
            if name in out:
                var = out[name]
                out[name] = replace(var, member_when={**(var.member_when or {}),
                    'positive_result_only': (prefix + '.operand_order', ('swap_before_shift',),
                                             'a single unswapped indicator must handle either sign')})
        for slot, children in slots.items():
            walk(list(children.values()), base + '.' + slot)

    walk(space.families, prefix)
    if kind == 'bitcount' and max(f.width for _, f in modes) < 128:
        name = prefix + '.final_adder.family'
        if name in out:
            var = out[name]
            out[name] = replace(var, domain=var.domain.without({'fpga_carry_chain':
                'the counter result is narrower than the minimum eight-bit carry-chain segment'}),
                member_when={**(var.member_when or {}), 'carry_lookahead':
                    (prefix + '.counter_primitive', ('compressor_4_2', 'counter_7_3', 'lut_rom'),
                     'two-bit group counts cannot construct selectable intergroup carry')})
    if kind == 'fp_multiplier':
        name = prefix + '.sig_mul.family'
        if name in out:
            var = out[name]
            domains = dict(var.index_domains or {})
            for mi, (_, fmt) in enumerate(modes):
                if getattr(fmt, 'man_bits', 32) + 1 < 4:
                    index = f'm{mi}'
                    domain = domains.get(index, var.domain)
                    domains[index] = domain.without({'recursive_karatsuba':
                        'a recursive split requires at least four significand bits'})
            out[name] = replace(var, index_domains=domains or None)
    from chialu.targets.rtl.engine import Engine
    engines = [Engine('geometry', f, int(spec.get('sr_bits') or 8), 'SR' in spec.get('rounding', ()),
                      tight=spec.get('x_form') == 'guard_round_sticky') for _, f in modes]
    for name, var in list(out.items()):
        if not name.endswith('.chunk_width_bits'):
            continue
        path = name[len(prefix) + 1:]
        limit = None
        if path in ('exp.adder.chunk_width_bits', 'exp_adder.chunk_width_bits'):
            limit = min(e.EW for e in engines)
        elif kind == 'fp_adder' and path == 'sig_adder.chunk_width_bits':
            limit = min(e.XW + 1 for e in engines)
        elif kind == 'bitcount' and path == 'final_adder.chunk_width_bits':
            # The first two group counts can meet in a two-bit adder.
            limit = 2
        if limit is not None:
            out[name] = replace(var, search_domain=Range(1, min(32, limit)))
    if kind == 'adder':
        # A partitioned chain can copy the first mode's choice to every lane.
        # Every requested full chunk must therefore fit the narrowest lane.
        width = min(f.width for _, f in modes)
        name = prefix + '.chunk_width_bits'
        if name in out:
            out[name] = replace(out[name], search_domain=Range(1, min(32, width)))
    from chialu.modules.integer_geometry import constrain_integer
    constrain_integer(out, prefix, kind, modes)
    from .fp_space_conditions import constrain_float
    return constrain_float(space, prefix, list(out.values()), kind=kind, modes=modes, spec=spec, independent=independent)
