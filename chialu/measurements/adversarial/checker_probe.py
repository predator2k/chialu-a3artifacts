"""Checker false alarms under modular children of binary arithmetic slots."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys
from adir.registry import underlying
from chialu import eda
from chialu.targets.derive import checker_rtl, seed_alu_text, verify_files, detect_budget
from chialu.verify.alu_ref import normalize_spec
ROOT = Path(__file__).resolve().parent / 'scratch' / ('checker_' + sys.argv[1])
ROOT.mkdir(parents=True, exist_ok=True)

def check(job):
    family, slot, child = job
    name = family + '_' + child
    pins = {slot + '.family': child}
    if child == 'end_around_carry':
        pins.update({slot + '.modulus': 'generic_p_correction', slot + '.modulus_value': 3})
    spec = normalize_spec({'unit':'alu', 'dut_name':'alu_core', 'check_en':True,
                           'modes':[{'format':'int8','count':1}], 'ops':['add','sub','adc'],
                           'checker_family':family, slot:{k.removeprefix(slot + '.'): v for k,v in pins.items()},
                           'checker_name':'alu_checker', 'n_random':128, 'n_random_masks':128})
    directory = ROOT / name; directory.mkdir(exist_ok=True)
    try:
        spec['detect'] = detect_budget(spec, 128)
        from chialu.targets.rtl.families import library_closure
        checker = checker_rtl(spec)
        checker += library_closure(checker)
        rtl = seed_alu_text(spec).text
        files = verify_files(spec, directory, checker)
        (directory / 'checker.sv').write_text(checker)
        (directory / 'seed.sv').write_text(rtl)
        result = underlying(eda.fault)(rtl, files, checker, 300)
        return dict(name=name, result=result)
    except Exception as e:
        return dict(name=name, error=repr(e))

if __name__ == '__main__':
    jobs = [(f, s, c) for f, s in [('an_code','coded_adder'),('berger','carry_replica'),('parity_prediction_adder','carry_replica')]
            for c in ['ripple_carry','end_around_carry']]
    with ProcessPoolExecutor(3) as pool:
        rows = list(pool.map(check, jobs))
    (ROOT / 'summary.json').write_text(json.dumps(rows, indent=2))
    for r in rows:
        print(r['name'], r.get('error') or r['result'])
