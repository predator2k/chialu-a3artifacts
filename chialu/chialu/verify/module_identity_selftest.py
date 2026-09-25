"""Module-name uniqueness, lexical collision guards and selection owners."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import redundant as R, rns_cpa as C, adder_ext, mul
from chialu.targets.rtl.families.mul import dedupe_modules
from chialu.targets.rtl.families.selection import SelectedPins, SelectionTrace, SelectionError
from chialu.verify.rns_cpa_range_selftest import build_one, run_batch


OLD_COLLISIONS = ((98, 3153), (157, 3978), (281, 2357), (835, 2058), (1367, 2151), (1868, 2611))
IMPLEMENTATION_HASHES_AT_IMPORT = {
    str(Path(value.__file__).resolve()): hashlib.sha256(Path(value.__file__).read_bytes()).hexdigest()
    for value in (adder_ext, mul, C)
}
SELFTEST_SHA256_AT_IMPORT = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def module(body, header='module m(input logic a,b,output logic y);'):
    return header + '\n' + body + '\nendmodule\n'


def lexical_cases():
    cases = []
    ordinary = module('assign y = a & b;')
    accepted = [
        ('identical', ordinary, ordinary),
        ('spaces', ordinary, module('  assign  y=a  &  b ;  ')),
        ('comments', ordinary, module('/* lead */ assign/* split */y = a & b; // tail')),
        ('header_spaces', ordinary, module('assign y=a&b;', 'module  m ( input logic a, b, output logic y );')),
        ('header_tabs', ordinary, module('assign y=a&b;', '\tmodule\tm(input logic a,b,output logic y);')),
        ('line_comment_string', module('localparam S="http://example/a"; assign y=a;'),
         module('localparam S = "http://example/a"; /* outside */ assign y = a;')),
        ('block_comment_string', module('localparam S="/* still string */"; assign y=a;'),
         module('localparam S = "/* still string */"; // outside\nassign y=a;')),
        ('escaped_quote_string', module(r'localparam S="quote: \" // /* content */"; assign y=a;'),
         module(r'localparam S = "quote: \" // /* content */"; /* outside */ assign y = a;')),
        ('endmodule_in_block_comment', module('/*\nendmodule\n*/\nassign y=a;'),
         module('/* ignored alternate comment */\nassign y=a;')),
    ]
    for name, left, right in accepted:
        output = dedupe_modules(left + right)
        # Comments may contain keyword text; real declarations are counted
        # only at the start of lines in these controlled fixtures.
        assert len(re.findall(r'^\s*module\s+m\b', output, re.M)) == 1, (name, output)
        assert 'assign' in output and output.rstrip().endswith('endmodule'), (name, output)
        cases.append({'case': name, 'expected': 'accept', 'pass': True})
    rejected = [
        ('different_function', ordinary, module('assign y=a|b;')),
        ('different_port', ordinary, module('assign y=a&b;', 'module m(input logic a,b,output logic [1:0] y);')),
        ('different_string_line_marker', module('localparam S="// alpha"; assign y=a;'), module('localparam S="// beta"; assign y=a;')),
        ('different_string_block_marker', module('localparam S="/* alpha */"; assign y=a;'), module('localparam S="/* beta */"; assign y=a;')),
        ('string_internal_space', module('localparam S="a b"; assign y=a;'), module('localparam S="ab"; assign y=a;')),
        ('hidden_spaced_header_change', ordinary, module('assign y=a|b;', 'module  m(input logic a,b,output logic y);')),
        ('hidden_tab_header_change', ordinary, module('assign y=a|b;', '\tmodule\tm(input logic a,b,output logic y);')),
        ('function_after_comment_endmodule', module('/*\nendmodule\n*/\nassign y=a;'), module('/*\nendmodule\n*/\nassign y=b;')),
        ('and_operator', module('assign y=a&&b;'), module('assign y=a& &b;')),
        ('logical_shift', module('assign y=a<<b;'), module('assign y=a< <b;')),
        ('arithmetic_shift', module('assign y=a<<<b;'), module('assign y=a< <<b;')),
        ('shift_assignment', module('always_comb y<<=1;'), module('always_comb y<< =1;')),
        ('arithmetic_shift_assignment', module('always_comb y<<<=1;'), module('always_comb y<<< =1;')),
        ('nonblocking_event', module('event e; initial ->>e; assign y=a;'), module('event e; initial -> >e; assign y=a;')),
        ('equal_operator', module('assign y=a===b;'), module('assign y=a== =b;')),
        ('part_select_operator', module('wire [3:0] t; assign y=t[0+:1];'), module('wire [3:0] t; assign y=t[0+ :1];')),
        ('unbased_literal', module("assign y='0;"), module("assign y=' 0;")),
        ('real_literal', module('localparam real V=1.0; assign y=a;'), module('localparam real V=1 . 0; assign y=a;')),
        ('exponent_literal', module('localparam real V=1e+2; assign y=a;'), module('localparam real V=1e +2; assign y=a;')),
        ('based_literal', module("assign y=1'b0;"), module("assign y=1 'b0;")),
        ('separated_identifier', module('wire ab; assign y=ab;'), module('wire ab; assign y=a b;')),
    ]
    for name, left, right in rejected:
        try:
            dedupe_modules(left + right)
        except ValueError:
            cases.append({'case': name, 'expected': 'reject', 'pass': True})
        else:
            raise AssertionError(f'dedupe silently accepted different SV tokens: {name}')
    return cases


def boundary_cases():
    cases = []
    accepted = [
        ('dollar_identifier', module('wire foo$module; assign y=foo$module;')),
        ('dollar_end_identifier', module('wire foo$endmodule; assign y=foo$endmodule;')),
        ('keyword_prefix_identifier', module('wire module$signal; assign y=module$signal;')),
        ('escaped_keyword_identifier', module('wire \\endmodule ; assign y=\\endmodule ;')),
        ('automatic_module', module('assign y=a;', 'module automatic m(input a,output y);')),
        ('valid_end_label', module('assign y=a;').replace('endmodule\n', 'endmodule : m\n')),
        ('valid_comment_end_label', module('assign y=a;').replace('endmodule\n', 'endmodule /* comment */ : m\n')),
    ]
    for name, source in accepted:
        output = dedupe_modules(source + source)
        assert output.count('assign y') == 1, (name, output)
        cases.append({'case': name, 'expected': 'accept', 'pass': True})
    directives = '`timescale 1ns/1ps\n// before\n' + module('assign y=a;') + '// after\n'
    output = dedupe_modules(directives)
    assert output == directives
    cases.append({'case': 'outside_directives_preserved', 'expected': 'accept', 'pass': True})
    rejected = [
        ('nested', 'module m;\nmodule n;\nendmodule\nendmodule\n'),
        ('unterminated', 'module m;\nassign y=a;\n'),
        ('unmatched_end', 'endmodule\n'),
        ('missing_name', 'module ;\nendmodule\n'),
        ('mismatched_label', module('assign y=a;').replace('endmodule\n', 'endmodule : wrong\n')),
        ('mismatched_comment_label', module('assign y=a;').replace('endmodule\n', 'endmodule /* comment */ : wrong\n')),
    ]
    for name, source in rejected:
        try:
            dedupe_modules(source)
        except ValueError:
            cases.append({'case': name, 'expected': 'reject', 'pass': True})
        else:
            raise AssertionError(f'malformed module boundary accepted: {name}')
    return cases


def owner_cases():
    owner = 'core.channels.modular_adder'
    pins = SelectedPins(owner, {})
    reports = []
    for supplied_module in (False, True):
        m = R.Mod('owner_test', 'input [3:0] a,b,input cin,output [3:0] s,output cout', '')
        with SelectionTrace() as trace:
            selected = FAM.adder_module('end_around_carry', pins, 4) if supplied_module else None
            assert C.raw_binary(m, 'end_around_carry', pins, 4, 'a', 'b', 'cin', 's', 'cout', module=selected)
        source = m.render()
        source += FAM.library_closure(source)
        trace.check({owner: ('end_around_carry', pins)}, source, 'owner_test')
        generated = [r for r in trace.report()['generated'] if r['family'] == 'end_around_carry']
        assert generated and all(r['owner'] == owner for r in generated)
        reports.append({'case': 'empty_owner_preserved', 'provided_module': supplied_module, 'pass': True, 'generated': generated})
    m = R.Mod('lost_owner', 'input [3:0] a,b,input cin,output [3:0] s,output cout', '')
    with SelectionTrace() as trace:
        C.raw_binary(m, 'end_around_carry', dict(pins), 4, 'a', 'b', 'cin', 's', 'cout')
    source = m.render()
    try:
        trace.check({owner: ('end_around_carry', pins)}, source + FAM.library_closure(source), 'lost_owner')
    except SelectionError:
        reports.append({'case': 'reproduced_empty_owner_loss_detected', 'pass': True})
    else:
        raise AssertionError('dropping empty SelectedPins owner was not detected')
    return reports


def module_blocks(source):
    """Independent exact-text extraction for the generated, line-based SV."""
    records = {}
    for match in re.finditer(r'(?ms)^module\s+(\w+)\b.*?^endmodule[ \t]*(?:\n|$)', source):
        name, block = match.group(1), match.group(0)
        if name in records:
            assert records[name] == block, f'conflicting stored evidence for {name}'
        records[name] = block
    return records


def names_and_legacy(legacy_root=None):
    names, correspondence = {}, []
    old_records = {}
    if legacy_root is not None:
        summary = json.loads((legacy_root / 'summary.json').read_text())
        assert summary['pass'] and summary['full_public_p_range'] and summary['p_values'] == 4093
        for result_path in sorted(legacy_root.glob('*/result.json')):
            report = json.loads(result_path.read_text())
            assert report['pass']
            for file in ('dut.sv', 'tb.sv', 'vectors.hex', 'expected.hex', 'actual.hex'):
                assert hashlib.sha256((result_path.parent / file).read_bytes()).hexdigest() == report['artifacts_sha256'][file]
            blocks = module_blocks((result_path.parent / 'dut.sv').read_text())
            for record in report['moduli']:
                p = record['modulus']
                assert p not in old_records and record['pass']
                old_records[p] = (record, blocks)
        assert set(old_records) == set(range(3, 4096))
    for p in range(3, 4096):
        source, record, _ = build_one(p)
        name = record['selected_module']
        assert re.search(r'_p[0-9a-f]{64}_w12$', name)
        assert name not in names
        names[name] = p
        if old_records:
            previous, old_blocks = old_records[p]
            new_blocks = module_blocks(source)
            assert name in new_blocks and record['wrapper'] in new_blocks
            for key, block in new_blocks.items():
                old_key = previous['selected_module'] if key == name else key
                renamed = re.sub(r'\b' + re.escape(name) + r'\b', previous['selected_module'], block)
                assert old_key in old_blocks and renamed == old_blocks[old_key], (p, key, 'change beyond module identifier')
            correspondence.append({'modulus': p, 'old_name': previous['selected_module'], 'new_name': name,
                                   'native_body_sha256': hashlib.sha256(new_blocks[name].encode()).hexdigest(),
                                   'old_native_body_sha256': hashlib.sha256(old_blocks[previous['selected_module']].encode()).hexdigest(),
                                   'exact_after_identifier_substitution': True})
    return {'pass': True, 'p_values': len(names), 'unique_names': len(names),
            'legacy_correspondence_checked': bool(old_records), 'legacy_equivalent_p_values': len(correspondence),
            'correspondence': correspondence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--legacy-range', type=Path)
    parser.add_argument('--section', choices=('all', 'names', 'joint', 'lexical', 'owner'), default='all')
    args = parser.parse_args()
    root = (args.out or Path(tempfile.mkdtemp(prefix='chialu-module-identity-'))).resolve()
    root.mkdir(parents=True, exist_ok=True)
    report = {'pass': True, 'implementation_sha256_at_import': IMPLEMENTATION_HASHES_AT_IMPORT}
    if args.section in ('all', 'names'):
        report['names'] = names_and_legacy(args.legacy_range)
        (root / 'names.json').write_text(json.dumps(report['names'], indent=2))
        print('PASS all 4093 names; legacy rename-only correspondence', report['names']['legacy_equivalent_p_values'], flush=True)
    if args.section in ('all', 'joint'):
        moduli = [p for pair in OLD_COLLISIONS for p in pair]
        report['joint'] = run_batch((root / 'joint_original_collisions', moduli))
        assert len({r['selected_module'] for r in report['joint']['moduli']}) == 12
    if args.section in ('all', 'owner'):
        report['owners'] = owner_cases()
        print('PASS empty SelectedPins owner and loss mutation', flush=True)
    if args.section in ('all', 'lexical'):
        report['lexical'] = lexical_cases()
        report['boundaries'] = boundary_cases()
        print('PASS', len(report['lexical']), 'lexical collision and', len(report['boundaries']), 'boundary cases', flush=True)
    report['selftest_sha256_at_import'] = SELFTEST_SHA256_AT_IMPORT
    (root / 'summary.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
