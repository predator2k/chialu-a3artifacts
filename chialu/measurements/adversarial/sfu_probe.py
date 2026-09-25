"""SFU bit-accurate evaluator versus its RTL with modular arithmetic children."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys
import subprocess
from chialu.targets.rtl.families import sfu, sfutest
from chialu.verify.formats import parse_format
ROOT = Path(__file__).resolve().parent / 'scratch' / ('sfu_' + sys.argv[1])
ROOT.mkdir(parents=True, exist_ok=True)

def check(child):
    pins = {'adder.family':child}
    if child == 'end_around_carry':
        pins.update({'adder.modulus':'generic_p_correction', 'adder.modulus_value':3})
    fmt = parse_format('fp8e4m3')
    try:
        name, text, net = sfu.sfu_sv('exp2', fmt, sfutest.geom_of(fmt), 'pwl', pins)
        result = sfutest.simulate(fmt, 'exp2', 'pwl', pins, text, name, net, 256, ROOT / child)
        binary = ROOT / child / 'pwl_exp2_fp8e4m3/obj_sim/sim'
        stdout = subprocess.check_output([str(binary)], text=True)
        (ROOT / child / 'stdout.txt').write_text(stdout)
        return dict(child=child, pins=pins, result=result, passed='PASS' in stdout.splitlines(),
                    stdout=stdout, bytes=len(text))
    except Exception as e:
        return dict(child=child, pins=pins, error=repr(e))

if __name__ == '__main__':
    with ProcessPoolExecutor(2) as pool:
        rows=list(pool.map(check,['ripple_carry','end_around_carry']))
    (ROOT/'summary.json').write_text(json.dumps(rows,indent=2))
    print(rows)
