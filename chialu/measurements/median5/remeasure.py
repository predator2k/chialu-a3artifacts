"""Re-measure archived RTL without changing the source archives or invoking models.

Each job runs both the compatibility flow and the five-run flow. The artifact
store holds their inputs, scripts and logs so every receipt is replayable.
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def measure(job, counts=(1, 5)):
    from adir.registry import underlying
    from chialu.eda import synth_ppa
    rtl = Path(job['rtl']).read_text()
    out = dict(job)
    for n in counts:
        start = time.monotonic()
        r = underlying(synth_ppa)(rtl, job['top'], 'nangate45', job.get('clock_ps', 300),
                                  repeats=n, report=False, timeout_s=3600)
        out[f'repeats{n}'] = dict(r, wall_seconds=time.monotonic() - start)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jobs', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--repeats', default='1,5', help='comma-separated repeat counts, one measurement each')
    a = ap.parse_args()
    counts = tuple(int(n) for n in a.repeats.split(','))
    a.out.mkdir(parents=True, exist_ok=True)
    jobs = json.loads(a.jobs.read_text())
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = [pool.submit(measure, j, counts) for j in jobs if not (a.out / (j['id'] + '.json')).exists()]
        for fu in as_completed(futures):
            r = fu.result()
            (a.out / (r['id'] + '.json')).write_text(json.dumps(r, indent=2) + '\n')
            print(r['id'], [(r[f'repeats{n}']['area_um2'], r[f'repeats{n}']['abc_delay_ps'],
                              r[f'repeats{n}']['wall_seconds']) for n in counts], flush=True)


if __name__ == '__main__':
    main()
