"""Check the complete simulation runner and preserved-artifact revalidation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from chialu.verify.combinational_sim import revalidate, simulate
from chialu.verify.family_ref import Adapter, Port
from chialu.verify.family_tb import emit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-comb-runner-'))
    original = root / 'original'
    adapter = Adapter((Port('a', 'input', 2), Port('b', 'input', 2), Port('y', 'output', 2)),
                      lambda value: {'y': value['a'] ^ value['b']})
    adapter.stimulus = lambda n, seed: [{'a': a, 'b': b} for a in range(4) for b in range(4)]
    bench = emit('checked_xor', {}, adapter, 0, 1)
    bench.write(original)
    source = 'module checked_xor(input wire [1:0] a,b, output wire [1:0] y); assign y=a^b; endmodule\n'
    record = simulate(source, 'checked_xor', str(bench), original)
    assert record['pass'] and record['vectors'] == 16
    assert revalidate(original)['pass']
    names = ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex', 'network.json', 'process.sv', 'actual.hex', 'procedural-result.json')
    for mutation in ('hash', 'source', 'incomplete', 'unknown', 'different', 'failed'):
        directory = root / mutation
        directory.mkdir(parents=True, exist_ok=True)
        for name in names:
            shutil.copyfile(original/name, directory/name)
        path = directory / 'procedural-result.json'
        changed = json.loads(path.read_text())
        name = 'actual.hex'
        if mutation == 'source':
            name = 'process.sv'
            with (directory/name).open('a') as stream:
                stream.write('module extra; endmodule\n')
        elif mutation == 'failed':
            changed['pass'] = False
        else:
            words = (directory/name).read_text().split()
            if mutation == 'incomplete':
                words.pop()
            elif mutation == 'unknown':
                words[0] = 'x'
            else:
                words[0] = format(int(words[0], 16) ^ 1, 'x')
            (directory/name).write_text('\n'.join(words)+'\n')
        if mutation != 'hash':
            changed['hashes'][name] = hashlib.sha256((directory/name).read_bytes()).hexdigest()
        path.write_text(json.dumps(changed))
        try:
            revalidate(directory)
        except ValueError:
            pass
        else:
            raise AssertionError(f'{mutation} corrupted evidence was accepted')
    print('PASS full Yosys/Verilator flow, 16 exact vectors and six artifact-revalidation rejections', flush=True)


if __name__ == '__main__':
    main()
