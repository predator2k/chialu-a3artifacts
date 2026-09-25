"""Numeric declarations obey family-local domains before plan repair."""
from pathlib import Path
import random

import pytest
import yaml

from adir import Enum, Variable
from adir.backends.numeric import _prune, sample_declaration
from adir.instance import Instance, _bind_variables
from adir.registry import get_template
import chialu.priors  # registers the templates and priors
from chialu.surrogate_features import scheme_repair
from chialu.surrogate_seeds import schemes_of
from chialu.front_seeds import plan_of, LEVELS
from adir.variables import ABSENT, Binding, _topological
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def numeric_instance(target):
    inst = Instance()
    inst.path = ROOT / target
    inst.base_dir = inst.path.parent
    inst.raw = yaml.safe_load(inst.path.read_text())['adir']
    inst.search = inst.raw['search']
    inst.template = get_template(inst.raw['module'])
    _bind_variables(inst, inst.raw['variables'])
    return inst


def test_disjoint_member_domains_cover_parent():
    v = Variable('output', Enum(('count', 'encoded')), when=('family', ('lzc', 'priority')),
                 member_when={'count': ('family', ('lzc',)), 'encoded': ('family', ('priority',))})
    assert v.siblings == ['family']
    with pytest.raises(ValueError):
        Variable('output', Enum(('count', 'encoded')), when=('family', ('lzc', 'priority')),
                 member_when={'count': ('family', ('lzc',)), 'encoded': ('family', ('lzc',))})


def test_inactivity_conjunction_expands_indexes_and_orders_controls():
    variable = Variable('core.*.topology', Enum(('tree',)), indexed_by='modes',
                        inactive_when=((('core.*.family', ('incrementer',)),
                                        ('core.*.structure', ('chain',))),))
    v = variable.expand(('m1',))[0]
    assert v.siblings == ['core.m1.family', 'core.m1.structure']
    for family, structure, inactive in [('incrementer', 'chain', True),
                                         ('incrementer', 'tree', False),
                                         ('adder', 'chain', False), ('incrementer', ABSENT, False)]:
        values = {'core.m1.family': family, 'core.m1.structure': structure}
        assert v.inactive(lambda name: ('search', values[name])) == inactive
    with pytest.raises(ValueError):
        Variable('x', Enum((1,)), inactive_when=((('x', (1,)),),))


def test_numeric_sampling_and_mutation_prune_conjunction():
    family = Variable('family', Enum(('adder', 'incrementer')), ('search',))
    structure = Variable('structure', Enum(('chain', 'tree')), ('search',))
    topology = Variable('topology', Enum(('ks', 'bk')), ('search',),
                        inactive_when=((('family', ('incrementer',)), ('structure', ('chain',))),))
    order = _topological([topology, structure, family])
    inst = SimpleNamespace(variable_order=lambda: order,
                           bindings={v.name: Binding(v, 'search', domain=v.domain) for v in order})
    for seed in range(30):
        values = sample_declaration(inst, random.Random(seed))
        active = values['family'] != 'incrementer' or values['structure'] != 'chain'
        assert ('topology' in values) == active
    assert _prune(inst, dict(family='incrementer', structure='chain', topology='ks')) == {
        'family': 'incrementer', 'structure': 'chain'}


@pytest.mark.parametrize('target', ['targets/int_subword_alu.numeric.yaml',
                                   'targets/eval/fp_alu_cmp.numeric.yaml',
                                   'targets/eval/fp_alu_cmp_hf.numeric.yaml'])
def test_numeric_choices_are_active_and_family_local(target):
    inst = numeric_instance(target)
    rtl = numeric_instance(target.replace(".numeric", ""))
    ctx = rtl.ctx()
    schemes, manifest = schemes_of(rtl, ctx, "all")
    for seed in range(20):
        values = sample_declaration(inst, random.Random(seed))
        # Exercise raw plans, without front_seeds.realize or any dropped pin.
        _, scheme = schemes[seed % len(schemes)]
        record = {"declarations": {"vars": scheme_repair(values, scheme)}}
        plan = plan_of(record, manifest, seed, set(), LEVELS[0], scheme)
        rtl.template.plan_seed(ctx, "sample", plan)
        for name, value in values.items():
            if name.endswith('.topology') and '.exp_incrementer.' in name:
                assert values[name.rsplit('.', 1)[0] + '.structure'] == 'prefix_and_tree'
            if name.startswith('core.unpacker.') and ('.lzc.' in name or '.shifter.' in name):
                assert values['.'.join(name.split('.')[:3]) + '.denormal_handling'] == 'in_unpack'
