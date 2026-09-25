"""Conservative geometry bounds for binary integer component slots.

A slot is one choice reused at every width at which its parent instantiates it.
Search domains must fit the smallest such width, including short tail blocks.
Explicit fixed bindings retain the renderer's exact geometry validation.
"""
from dataclasses import replace
from adir import Enum, Range


def constrain_integer(out, prefix, kind, modes):
    if kind not in ('adder', 'comparator', 'multiplier', 'bitcount'):
        return
    width = min(f.width for _, f in modes)

    def narrow(name, allowed):
        if name not in out:
            return
        var = out[name]
        domain = var.search_domain or var.domain
        members = tuple(v for v in domain.members() if allowed(v))
        if members:
            # Preserve range bindings (including YAML min/max/step overrides).
            # These geometry predicates truncate ranges without adding holes.
            narrowed = (Range(members[0], members[-1], domain.step)
                        if isinstance(domain, Range) else Enum(members))
            out[name] = replace(var, search_domain=narrowed)

    for name, var in list(out.items()):
        if name.endswith('.negative_pp_encoding'):
            out[name] = replace(var, member_when={**(var.member_when or {}),
                'twos_complement_row': (name.rsplit('.', 1)[0] + '.hard_multiple_gen',
                    ('cpa_precompute', 'specialized_3m_cpa'),
                    'two\'s-complement rows require an assimilated hard multiple')})
        if not name.endswith('.family'):
            continue
        base = name[:-7]
        path = base[len(prefix):].strip('.')
        families = set(var.domain.members())
        if not families & {'ripple_carry', 'parallel_prefix'}:
            continue
        w = width
        if kind == 'bitcount':
            w = 2
        if kind == 'multiplier':
            # Recursive leaf products and squarer cross-products have short CPAs.
            w = 2
            if path in ('adder', 'pre_adder'):
                w = 4
        if path.endswith(('block_adder', 'sum_block')):
            w = 1  # every parent sizing rule can leave a single-bit tail
        if path.endswith(('tile_adder', 'hard_multiple_adder')):
            w = 1  # staggered/redundant tiles can end in one product column
        narrow(name, lambda f: not (
            (w < 8 and f == 'fpga_carry_chain') or
            (w < 3 and f == 'carry_lookahead') or
            (w < 2 and f in ('manchester_carry_chain', 'conditional_sum',
                             'carry_skip', 'carry_select', 'carry_increment', 'sparse_prefix_hybrid',
                             'end_around_carry'))))
        for key, limit in (('chunk_width_bits', w), ('chain_segment_length', w),
                           ('block_width', w), ('group_size', w - 1),
                           ('base_block_width', max(1, w // 2)),
                           ('log2_sparsity', max(0, w.bit_length() - 1))):
            narrow(base + '.' + key, lambda v, limit=limit: v <= limit)
        narrow(base + '.modulus_value', lambda v: v < 2 ** w)
        # A recursive level needs > group_size**levels bits. Conditions retain
        # every level which can occur for at least one admitted group size.
        level_name = base + '.levels'
        if level_name in out:
            narrow(level_name, lambda v: 2 ** v < w or v == 1)
            lv = out[level_name]
            group = out[base + '.group_size']
            groups = (group.search_domain or group.domain).members()
            conditions = dict(lv.member_when or {})
            for v in (lv.search_domain or lv.domain).members():
                if v > 1:
                    conditions[v] = (base + '.group_size', tuple(g for g in groups if g ** v < w),
                                     'each recursive level needs multiple real lookahead groups')
            out[level_name] = replace(lv, member_when=conditions)
        narrow(base + '.skip_levels', lambda v: v == 1)
        # Radix depends on the number of actual base blocks.
        radix_name = base + '.selection_radix'
        if radix_name in out:
            narrow(radix_name, lambda v: v <= w)
            rv = out[radix_name]
            bv = out[base + '.base_block_width']
            bs = (bv.search_domain or bv.domain).members()
            conditions = dict(rv.member_when or {})
            for r in (rv.search_domain or rv.domain).members():
                if r > 2 and any((w + b - 1) // b >= r for b in bs):
                    conditions[r] = (base + '.base_block_width', tuple(b for b in bs if (w + b - 1) // b >= r),
                                     'the merge radix must fit the number of real base blocks')
            out[radix_name] = replace(rv, member_when=conditions)
        # A prefix over FPGA segments needs two complete/partial segments.
        pn = base + '.prefix_over_chain'
        if pn in out and w > 2:
            pv = out[pn]
            out[pn] = replace(pv, member_when={True: (base + '.chain_segment_length',
                tuple(v for v in out[base + '.chain_segment_length'].domain.members() if v < w),
                'a prefix overlay needs at least two actual segments')})
        # Higher valency is implemented only for these prefix graphs.
        vn = base + '.valency'
        if vn in out and base + '.topology' in out:
            vv = out[vn]
            out[vn] = replace(vv, member_when={**(vv.member_when or {}), **{
                v: (base + '.topology', ('sklansky', 'kogge_stone', 'brent_kung'),
                    'only these topologies implement multi-input prefix cells') for v in (3, 4)}})
