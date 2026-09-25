"""Reproduce binary CPA contract violations inside decimal arithmetic."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys
from chialu.verify.variant_selftest import seed_fixture, check_seed
from chialu.targets.rtl.families.selftest import run_space_case
ROOT = Path(__file__).resolve().parent / 'scratch' / ('decimal_' + sys.argv[1])
ROOT.mkdir(parents=True, exist_ok=True)

def check(job):
    family, slot, modulus = job
    pins = {slot + '.family': 'end_around_carry', slot + '.modulus': modulus}
    if modulus == 'generic_p_correction':
        pins[slot + '.modulus_value'] = 3
    name = family + '_' + modulus
    try:
        component = run_space_case(('bcd_adder', 8, family, pins, name), ROOT)
        spec, selections = seed_fixture('bcd_adder', family, pins, 8)
        result = check_seed(spec, selections, ROOT / name, 256, 42)
        return dict(name=name, pins=pins, component=component, result=result)
    except Exception as e:
        return dict(name=name, pins=pins, error=repr(e))

if __name__ == '__main__':
    jobs = [(f, s, m) for f, s in [('bcd_direct_addition', 'digit_adder'), ('speculative_decimal_addition', 'carry_network')]
            for m in ['mod_2n_minus_1', 'mod_2n_plus_1_diminished_one', 'generic_p_correction']]
    with ProcessPoolExecutor(3) as pool:
        rows = list(pool.map(check, jobs))
    (ROOT / 'summary.json').write_text(json.dumps(rows, indent=2))
    for r in rows:
        print(r['name'], r.get('error') or {k:r['result'].get(k) for k in ['pass','mismatch_count','detail']})
