"""Render the baseline table from complete receipts, never from rounded constants."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pair(r):
    return f"{r['area_um2']:,.3f} / {r['abc_delay_ps']:,.2f}" if r['ok'] else 'failed'


def main():
    results = {p.stem: json.loads(p.read_text()) for p in sorted((HERE / 'results').glob('*.json'))}
    rows = ['# Baselines re-measured 2026-09-24', '',
            'Area µm² / delay ps. Columns r0–r4 use seeds base, 11, 23, 37, 53. ',
            'The single column is a separate compatibility synthesis; median is per metric. ',
            'Cells, status, seconds, all hashes, scripts and log references are in each linked receipt.', '',
            '| Design | clock ps | single | r0 | r1 | r2 | r3 | r4 | median |',
            '| --- | ---: | --- | --- | --- | --- | --- | --- | --- |']
    for name, r in results.items():
        one, five = r['repeats1'], r['repeats5']
        rows.append(f"| [{name}](results/{name}.json) | {r.get('clock_ps', 300)} | {pair(one)} | "
                    + ' | '.join(pair(run) for run in five['runs']) + f" | {pair(five)} |")
    (HERE / 'BASELINES.md').write_text('\n'.join(line.rstrip() for line in rows)+'\n')
    parallel = json.loads((HERE / 'parallel.json').read_text())
    cost = ['# Whole-ALU synthesis cost', '',
            'Local <host> wall seconds including receipt storage; medium / Nangate45 / 300 ps, report=False. ',
            'Independent jobs and other host load affect timings. Four internal workers reserve four EDA slots.', '',
            '| Target | repeats=1 | repeats=5, serial | repeats=5, four workers | serial ratio |',
            '| --- | ---: | ---: | ---: | ---: |']
    for name in ('int_subword_alu', 'fp_alu_cmp', 'fp_alu_cmp_hf'):
        r=results[name]; a,b=r['repeats1']['wall_seconds'],r['repeats5']['wall_seconds']
        cost.append(f"| {name} | {a:.2f} | {b:.2f} | {parallel[name]['wall_seconds']:.2f} | {b/a:.2f} |")
    a,b=[results['int_subword_alu'][f'repeats{n}']['wall_seconds'] for n in (1,5)]
    db=json.loads((HERE/'db_cost.json').read_text())
    cost += ['',f'9,704 integer surrogate labels, using this baseline as the proxy: {9704*b/3600:.2f} core-hours ',
             f'(formerly {9704*a/3600:.2f}; extra {9704*(b-a)/3600:.2f}), ideally {9704*b/3600/60:.2f} hours at 60 cores. ',
             'This is synthesis only: generation, feature extraction, simulation and retraining are excluded; ',
             'design complexity and memory may change throughput. Use one internal worker with 60 independent jobs.', '',
             f'The existing DB has {db["rows"]:,} rows ({db["successful"]:,} successful); ',
             f'{db["seconds_rows"]:,} rows record seconds, totalling {db["seconds_sum"]/3600:.2f} core-hour equivalents. ',
             f'A conservative fivefold planning estimate is {db["five_upper_estimate_seconds"]/3600:.2f} core-hour equivalents ',
             f'or {db["five_upper_estimate_seconds"]/3600/60:.2f} hours at 60 cores. ',
             'This is a budget estimate, not a measured bound: checkpoint reuse and text deduplication reduce work; ',
             'generation cost, unknown timings, host contention, retries and long-tail failed rows can increase it. ',
             'No dataset re-labelling or full synthesis DB rebuild was run. Only the isolated one-row DB test was rebuilt.']
    (HERE / 'COST.md').write_text('\n'.join(line.rstrip() for line in cost)+'\n')


if __name__ == '__main__':
    main()
