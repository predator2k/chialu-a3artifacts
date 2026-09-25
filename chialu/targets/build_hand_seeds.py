"""Package the external reference sources without running synthesis or an LLM.

Run from any checkout: python targets/build_hand_seeds.py --a3-root <a3eval>.
Only new *_hand_seed.sv files under runs/ are written. Reference RTL is
unchanged; the wrappers normalize flags to the comparison's four-bit word.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def joined(root: Path, reference: str, point: str) -> str:
    path = root / 'baselines' / reference / 'build.py'
    spec = importlib.util.spec_from_file_location(f'hand_{reference}_builder', path)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True  # reference checkouts are read-only
    spec.loader.exec_module(module)
    text = module.joined(point, f'{reference}_alu_core.sv')
    # Older TransDot wrappers repeat an operation-wide status into two lane
    # words. Both words are identical; retain one word at the target boundary.
    text = text.replace('output logic [7:0]  flags', 'output logic [3:0]  flags')
    text = text.replace("flags = vec ? {fl_main, fl_main} : {4'b0, fl_main};", 'flags = fl_main;')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--a3-root', type=Path, default=Path('$A3EVAL'))
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    root = args.a3_root.resolve()
    designs = [
        ('fpnew', 'fpnew_parallel_hand_seed.sv', joined(root, 'fpnew', 'PARALLEL')),
        ('hardfloat', 'hardfloat_hand_seed.sv', (root / 'runs/hardfloat/alu_core.v').read_text()),
        ('transdot', 'transdot_merged_hand_seed.sv', joined(root, 'transdot', 'MERGED')),
    ]
    manifest = {}
    for reference, name, text in designs:
        output = root / 'runs' / reference / name
        text = '// ADIR-DECL v1\n// ADIR-END\n' + text
        output.write_text(text)
        manifest[reference] = dict(path=str(output), bytes=len(text.encode()),
                                   sha256=hashlib.sha256(text.encode()).hexdigest())
    if args.manifest:
        args.manifest.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
