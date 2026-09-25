"""Dump the complete model input for two micro-architectures that differ in one choice.

The point of the pair is the conditional tree: `popcount_counter_tree` needs a `final_adder`
sub-slot to sum its counter stages, `priority_encoder` does not. So the two designs do not merely
hold different values -- they have different SETS of variables. What the dump shows is that the
feature vector nevertheless has the same width in both cases, because the columns are opened per
top-level structure and everything below that is folded into one (area, delay) pair.
"""
import json, sys
sys.path.insert(0, '$CHIALU_HOME/coeff')
from harness import context, plans_of, family_choices, declaration, tie_group, group_map
from xplan_features import build
from adir.registry import underlying
from chialu import eda
from chialu.plans import partition_of_plan, plan_vars
from chialu.modules.generators import spec_of

inst, ctx, man = context('targets/int_subword_alu.yaml', '$CHIALU_HOME/tmp/dump')
plans = plans_of(inst, man); fc = family_choices(inst, man)
pname, plan = plans[0]
spec = json.dumps(spec_of(ctx)); raw = partition_of_plan(man, plan)
manifest_by_id = {s.id: dict(id=s.id, kind=s.kind, slot=s.slot, index=s.index, mode=s.mode,
                             lane=s.lane, width=s.width, format=s.format) for s in man}
ids = sorted(manifest_by_id)
base = {k: v[0] for k, v in sorted(fc.items())}

out = {}
for label, fam in (("A", "popcount_counter_tree"), ("B", "priority_encoder")):
    over = dict(base)
    for m in ('m0', 'm1', 'm2'):
        over[f'core.bitcount.{m}.family'] = fam
    over = tie_group(ctx, over, group_map(man, plan, fc))
    vs = plan_vars(ctx, man, plan, raw)
    vs.update({k: v for k, v in over.items() if k not in vs})
    est = underlying(eda.estimate)({'spec.json': spec}, declaration(ctx, man, vs),
                                   'nangate45', 'medium', 1.0, 1.0, json.dumps(plan), '', '')
    meas = {'est_area': est['area_um2'], 'est_delay': est['delay_ps'], 'coverage': est['coverage']}
    out[label] = {'fam': fam, 'est': est, 'design': over,
                  'feat': build(meas, {'rows': est.get('rows') or []}, pname, plan, manifest_by_id, ids)}

json.dump({'plan': pname, 'structures': [manifest_by_id[i] for i in ids],
           'A': {'fam': out['A']['fam'], 'feat': out['A']['feat'],
                 'design': {k.replace('core.', ''): str(v) for k, v in sorted(out['A']['design'].items())},
                 'rows': out['A']['est'].get('rows')},
           'B': {'fam': out['B']['fam'], 'feat': out['B']['feat'],
                 'design': {k.replace('core.', ''): str(v) for k, v in sorted(out['B']['design'].items())},
                 'rows': out['B']['est'].get('rows')}},
          open('$CHIALU_HOME/coeff/results/feature_example.json', 'w'), indent=1)
print(f"A: {len(out['A']['feat'])} columns, B: {len(out['B']['feat'])} columns")
print(f"differing: {sum(1 for k in out['A']['feat'] if out['A']['feat'][k] != out['B']['feat'].get(k))}")
