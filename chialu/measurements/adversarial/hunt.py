"""Deterministic forced-member and sharing-pair coverage, followed by full ALU gates.

Run with env.sh sourced. Scratch contains replayable plans, RTL and gate results.
No synthesis, Ray, or model calls. Conformance uses the unmodified target bundle.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import re
from types import SimpleNamespace
import time

ROOT = Path(__file__).resolve().parents[2]
TARGETS = {'int': 'targets/int_subword_alu.yaml', 'fp': 'targets/eval/fp_alu_cmp.yaml',
           'hf': 'targets/eval/fp_alu_cmp_hf.yaml'}
S = {}


def setup(kind, output):
    import chialu.priors
    import yaml
    from adir.instance import load, Instance, _bind_variables
    from adir.registry import get_template
    from chialu.surrogate_seeds import schemes_of
    target = ROOT / TARGETS[kind]
    inst = load(str(target), run_dir_override=str(output / 'instance'))
    num = Instance()
    num.path = target.with_name(target.stem + '.numeric.yaml')
    num.base_dir = num.path.parent
    num.raw = yaml.safe_load(num.path.read_text())['adir']
    num.search = num.raw['search']
    num.template = get_template(num.raw['module'])
    _bind_variables(num, num.raw['variables'])
    ctx = inst.ctx(run_dir=output / 'instance')
    schemes, manifest = schemes_of(inst, ctx, 'natural')
    S.update(inst=inst, num=num, ctx=ctx, schemes=schemes, manifest=manifest, output=output)


def program(name, plan):
    from adir.evaluate import program_from_seed_text
    from adir.seeds import _seed_texts
    i = S['inst']
    res = i.template.plan_seed(S['ctx'], name, plan)
    texts, values, lines = _seed_texts(i.seed_artifacts()[0], res, name)
    return program_from_seed_text(i, texts, values, lines)


def render(job):
    from adir.declaration import check_declaration
    from adir.evaluate import candidate_from_program
    from chialu.front_seeds import realize, plan_of, LEVELS
    from chialu.surrogate_features import scheme_repair
    from chialu.eda import rtl_of
    name, vals, scheme = job
    row = dict(name=name, scheme=scheme)
    try:
        sp = dict(S['schemes'])[scheme]
        vals = scheme_repair(vals, sp)
        row['values'] = vals
        rec = {'declarations': {'vars': vals}}
        try:
            raw = plan_of(rec, S['manifest'], 0, set(), LEVELS[0], sp)
            program(name, raw)
            row['raw'] = 'ok'
        except Exception as e:
            row['raw'] = str(e)[:500]
        plan, err = realize(S['inst'], S['ctx'], S['manifest'], rec, name, 0, sp)
        if plan is None:
            row['error'] = err
            return row
        row['plan'] = plan
        prog = program(name, plan)
        cand = candidate_from_program(S['inst'], prog)
        check = check_declaration(S['inst'], cand.declaration, S['inst'].ctx(declaration=cand.declaration))
        row['decl_ok'] = bool(check.get('ok'))
        if not row['decl_ok']:
            row['error'] = str(check)[:500]
        rtl = rtl_of(prog)
        row['sha256'] = hashlib.sha256(rtl.encode()).hexdigest()
        (S['output'] / 'rtl' / (name + '.sv')).write_text(rtl)
    except Exception as e:
        row['error'] = f'{type(e).__name__}: {e}'[:700]
    return row


def features(row):
    # Family-parent pairs, each pin value, and every pair of sharing axes.
    vals = row['values']
    out = {('member', k, json.dumps(v, sort_keys=True)) for k, v in vals.items()}
    for k, v in vals.items():
        parts = k.split('.')
        for n in range(3, len(parts)):
            parent = '.'.join(parts[:n]) + '.family'
            if parent != k and parent in vals:
                out.add(('nested', parent, str(vals[parent]), k, str(v)))
    axes = re.split(r'_(?=(?:add|mul|log|pair|fmt|sw|round|unpack|fadd|fmul|fcmp|fma|intfp)-)', row['scheme'])
    out.update(('sharing', a, b) for i, a in enumerate(axes) for b in axes[i + 1:])
    return out


def evaluate(row):
    from adir.registry import underlying
    from chialu.eda import conformance, lint
    rtl = (S['output'] / 'rtl' / (row['name'] + '.sv')).read_text()
    files = next(a.texts for a in S['inst'].artifacts.values() if a.path == 'verify_bundle')
    start = time.time()
    result = {'name': row['name'], 'scheme': row['scheme'], 'sha256': row['sha256']}
    try:
        result['lint'] = underlying(lint)(rtl)
        result['conformance'] = underlying(conformance)(rtl, files, 600)
    except Exception as e:
        result['error'] = repr(e)
    result['seconds'] = round(time.time() - start, 2)
    (S['output'] / 'results' / (row['name'] + '.json')).write_text(json.dumps(result, indent=2))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('kind', choices=TARGETS)
    p.add_argument('--phase', choices=['prepare', 'evaluate'], default='prepare')
    p.add_argument('--draws', type=int, default=300)
    p.add_argument('--forced', type=int, default=400)
    p.add_argument('--select', type=int, default=80)
    p.add_argument('--jobs', type=int, default=6)
    p.add_argument('--list', default='chosen.json', help='Prepared plan list for evaluation')
    args = p.parse_args()
    out = ROOT / 'measurements/adversarial/scratch' / args.kind
    for d in ('rtl', 'results'):
        (out / d).mkdir(parents=True, exist_ok=True)
    setup(args.kind, out)
    print('loaded', args.kind, len(S['schemes']), 'schemes', flush=True)
    if args.phase == 'evaluate':
        chosen = json.loads((out / args.list).read_text())
        with ProcessPoolExecutor(args.jobs) as pool:
            for r in pool.map(evaluate, chosen):
                print(r['name'], r.get('conformance', {}).get('pass'), r.get('conformance', {}).get('detail', '')[:200], flush=True)
        return
    from adir.backends.numeric import sample_declaration
    from chialu.surrogate_seeds import Stage
    rng = random.Random(20260924)
    jobs = [(f'r{i:04d}', sample_declaration(S['num'], rng), S['schemes'][i % len(S['schemes'])][0])
            for i in range(args.draws)]
    stage = SimpleNamespace(num=S['num'], schemes=S['schemes'], a=SimpleNamespace(seed=20260924))
    forced, report = Stage.coverage_items(stage, jobs, per_family=1, per_value=1, cap=args.forced)
    jobs += forced
    (out / 'coverage_requested.json').write_text(json.dumps(report, indent=2))
    rows = []
    with (out / 'rendered.jsonl').open('w') as f, ProcessPoolExecutor(args.jobs) as pool:
        for row in pool.map(render, jobs, chunksize=1):
            rows.append(row)
            f.write(json.dumps(row) + '\n'); f.flush()
            if len(rows) % 50 == 0:
                print('rendered', len(rows), 'errors', sum('error' in r for r in rows), flush=True)
    good = [r for r in rows if 'error' not in r]
    feats = {r['name']: features(r) for r in good}
    counts = Counter(x for f in feats.values() for x in f)
    chosen, covered = [], set()
    while good and len(chosen) < args.select:
        best = max(good, key=lambda r: sum(1 / counts[x] for x in feats[r['name']] - covered))
        chosen.append(best); covered |= feats[best['name']]; good.remove(best)
    (out / 'chosen.json').write_text(json.dumps(chosen, indent=1))
    summary = dict(target=args.kind, draws=args.draws, forced=report, rendered=len(rows),
                   errors=[{'name': r['name'], 'error': r['error']} for r in rows if 'error' in r],
                   raw_errors=sum(r.get('raw') != 'ok' for r in rows), selected=len(chosen),
                   features_total=len(counts), features_selected=len(covered),
                   dropped=sum(bool(r.get('plan', {}).get('dropped') or r.get('plan', {}).get('reduced_after')) for r in rows))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != 'errors'}), flush=True)


if __name__ == '__main__':
    main()
