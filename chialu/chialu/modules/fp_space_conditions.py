"""Width contracts for the complete floating-point component tree.

A component selection is reused at every occurrence of that slot. Domains
therefore use the smallest occurrence, including remainder blocks and the
small internal adders of counters and recursive multipliers.
"""
from dataclasses import replace
from adir import Enum, Range


def constrain_float(space, prefix, variables, *, kind, modes, spec, independent=False):
    if kind not in ('fp_fma', 'fp_adder', 'fp_multiplier', 'fp_comparator', 'rounder', 'unpacker'):
        return variables
    from chialu.targets.rtl.engine import Engine
    out = {v.name: v for v in variables}
    # Compact and exact X are both searchable. These bounds hold for either.
    engines = [Engine('geometry', f, int(spec.get('sr_bits') or 8), False, tight=True) for _, f in modes]

    def narrow(name, predicate, *, per_index=False):
        if name not in out:
            return
        v = out[name]
        if name.endswith('.family'):
            domains = dict(v.index_domains or {})
            for mi, e in enumerate(engines):
                ix = f'm{mi}'
                d = domains.get(ix, v.domain)
                values = [x for x in d.members() if (predicate(x, e) if per_index else all(predicate(x, ge) for ge in engines))]
                if values and values != list(d.members()):
                    domains[ix] = Enum(tuple(values))
            if v.indexed_by:
                out[name] = replace(v, index_domains=domains or None)
            else:
                d = next(iter(domains.values()), v.domain)
                out[name] = replace(v, domain=d, member_when={
                    x: c for x, c in (v.member_when or {}).items() if d.contains(x)} or None)
        else:
            d = v.searchable
            values = [x for x in d.members() if all(predicate(x, e) for e in engines)]
            if values:
                # Keep integer axes numeric, including YAML min/max/step
                # overrides, whenever the retained grid has no holes.
                if isinstance(d, Range) and values == list(Range(values[0], values[-1], d.step).members()):
                    domain = Range(values[0], values[-1], d.step)
                else:
                    domain = Enum(tuple(values))
                out[name] = replace(v, search_domain=domain)

    def condition(name, member, sibling, allowed, reason):
        if name in out and out[name].domain.contains(member):
            v = out[name]
            # A general FMA declaration already conditions fused rounding on
            # its sharing interface. Keep that contract. Numeric mode geometry
            # admits dedicated FMA only, so its remaining condition is X form.
            if member in (v.member_when or {}) and v.member_when[member][0] != sibling and not independent:
                return
            out[name] = replace(v, member_when={**(v.member_when or {}), member: (sibling, tuple(allowed), reason)})

    if kind == 'fp_fma':
        if independent:
            narrow(prefix + '.sharing', lambda x, e: x == 'dedicated_per_mode')
        condition(prefix + '.composition_style', 'bridge_reuse', 'x_form', ('exact',),
                  'the exact product bridge requires the exact X interface')
        condition(prefix + '.rounding_position', 'fused_with_cpa_dual_sum', 'x_form', ('exact',),
                  'product-frame fused rounding requires the exact X interface')
    if kind == 'fp_multiplier':
        condition(prefix + '.family', 'round_fused_in_reduction', 'x_form', ('exact',),
                  'product-frame fused rounding requires the exact X interface')

    if not independent:
        return list(out.values())

    def width(path, e):
        parts = path.split('.')
        if any(p in ('block_adder', 'sum_block', 'tile_adder', 'hard_multiple_adder') for p in parts):
            return 1  # a block/tile or partially redundant hard multiple can end in one bit
        if 'final_adder' in parts:
            return 2  # first pair of popcounts, also inside LZC prefix_sum
        if any(p in ('sig_mul', 'multiplier', 'cross', 'segment') for p in parts):
            if any(p in ('cross', 'segment') for p in parts):
                return 1  # a composite multiplier can have a one-bit tail
            if parts[-1] == 'adder' and 'reduction' not in parts and 'cpa' not in parts:
                return 2  # recursive pre-adds
            if 'reduction' in parts:
                return 2  # shared with recursive base multipliers
            return e.SW
        if 'exp' in parts or 'exp_adder' in parts:
            return e.EW
        if 'subtractor' in parts:
            return min(e.EW, e.SW)
        return e.XW + 1

    def walk(families, base):
        names = {f.name for f in families}
        path = base[len(prefix) + 1:]
        w = lambda e: width(path, e)
        if 'ripple_carry' in names:
            if 'sparse_prefix_hybrid' in names:
                # This union has two distinct topology controls. ADIR's single
                # sibling member condition cannot express their disjunction.
                # Binary valency is valid for every admitted topology; fixed
                # declarations still retain the full renderer-supported domain.
                narrow(base + '.valency', lambda x, e: x == 2)
            else:
                for valency in (3, 4):
                    condition(base + '.valency', valency, base + '.topology',
                              ('sklansky', 'kogge_stone', 'brent_kung'),
                              'nonbinary prefix nodes are implemented for these topologies')
            minimum = {'manchester_carry_chain': 2, 'carry_lookahead': 3,
                       'conditional_sum': 2, 'carry_skip': 4, 'carry_select': 4,
                       'carry_increment': 4, 'sparse_prefix_hybrid': 2,
                       'fpga_carry_chain': 8}
            narrow(base + '.family', lambda x, e: w(e) >= minimum.get(x, 1))
            for key in ('chunk_width_bits', 'chain_segment_length', 'block_width', 'pseudo_carry_group'):
                narrow(base + '.' + key, lambda x, e: x <= w(e))
            narrow(base + '.group_size', lambda x, e: x < w(e))
            narrow(base + '.base_block_width', lambda x, e: x < w(e))
            # Shared template conditions must be valid at every occurrence.
            # The general RTL target still admits explicit larger geometries.
            low = min(w(e) for e in engines)
            if base + '.levels' in out:
                for level in out[base + '.levels'].domain.members():
                    if level > 1:
                        allowed = [g for g in range(2, 9) if low > g ** level]
                        if allowed:
                            condition(base + '.levels', level, base + '.group_size', allowed,
                                      'each lookahead level needs actual subgroups')
                        else:
                            narrow(base + '.levels', lambda x, e, level=level: x != level)
            if base + '.selection_radix' in out:
                for radix in (4,):
                    allowed = [b for b in range(1, 5) if low > (radix - 1) * b]
                    if allowed:
                        condition(base + '.selection_radix', radix, base + '.base_block_width', allowed,
                                  'the merge needs that many real base blocks')
                    else:
                        narrow(base + '.selection_radix', lambda x, e, radix=radix: x != radix)
            # One skip level exists even when the sizing rule makes one block.
            narrow(base + '.skip_levels', lambda x, e: x == 1)
            # A full segment and another segment must exist for an overlay.
            if base + '.prefix_over_chain' in out:
                allowed = [s for s in range(2, 65) if s < low]
                if allowed:
                    condition(base + '.prefix_over_chain', True, base + '.chain_segment_length', allowed,
                              'prefix overlay requires at least two actual segments')
                else:
                    narrow(base + '.prefix_over_chain', lambda x, e: not x)
            narrow(base + '.log2_sparsity', lambda x, e: (1 << x) <= w(e))
            narrow(base + '.modulus', lambda x, e: x != 'generic_p_correction' or w(e) >= 2)
            narrow(base + '.modulus_value', lambda x, e: x < (1 << w(e)))
        if 'booth_recoded_parallel' in names:
            condition(base + '.negative_pp_encoding', 'twos_complement_row',
                      base + '.hard_multiple_gen', ('cpa_precompute', 'specialized_3m_cpa'),
                      "two's-complement rows require assimilated hard multiples")
        if 'recursive_karatsuba' in names:
            narrow(base + '.family', lambda x, e: x != 'recursive_karatsuba' or e.SW >= 4, per_index=True)
            # Three-way splitting uses ceil(W/3); W=4 leaves no high part.
            if min(e.SW for e in engines) <= 4:
                narrow(base + '.split_kind', lambda x, e: x != 'three_way' or e.SW > 2 * ((e.SW + 2) // 3))
        children = {}
        for f in families:
            for slot, sub in f.components.items():
                children.setdefault(slot, {}).update({c.name: c for c in sub.families})
        for slot, fs in children.items():
            walk(list(fs.values()), base + '.' + slot)
    walk(space.families, prefix)
    return list(out.values())
