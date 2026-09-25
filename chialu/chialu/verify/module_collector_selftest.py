"""Inject conflicts before collection in ALU, SFU and Dot seed paths."""
from __future__ import annotations

import argparse
import copy
import inspect
import json
from pathlib import Path
import pickle
import tempfile
from unittest.mock import patch

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families.module_library import ModuleLibrary, collect_modules, dedupe_modules
from chialu.targets.rtl.families.sfu import Net
from chialu.targets.rtl.alu_mode import ModeEmitter
from chialu.verify.module_identity_selftest import lexical_cases, boundary_cases


def text(name, value=0, comment=''):
    return f'// {comment}\nmodule {name}(output wire y);\nassign y = 1\'b{value};\nendmodule\n'


def rejected(function, fragment='conflicting definitions'):
    try:
        function()
    except ValueError as error:
        assert fragment in str(error), str(error)
        return str(error)
    raise AssertionError('a conflicting module was silently discarded')


def map_cases():
    first, equivalent, changed = text('m'), text('m', comment='same tokens; another spelling'), text('m', 1)
    library = ModuleLibrary({'m': first})
    library.setdefault('m', equivalent)
    library['m'] = equivalent
    library.update([('m', equivalent)])
    library |= {'m': equivalent}
    assert library['m'] == first
    for operation in (lambda: library.setdefault('m', changed), lambda: library.__setitem__('m', changed),
                      lambda: library.update({'m': changed}), lambda: library.__ior__({'m': changed}),
                      lambda: library | {'m': changed}, lambda: {'m': changed} | library,
                      lambda: ModuleLibrary([('m', first), ('m', changed)])):
        rejected(operation)
        assert dict(library) == {'m': first}
    rejected(lambda: library.update([('new', text('new')), ('m', changed)]))
    assert 'new' not in library
    plain = {'m': first}
    rejected(lambda: collect_modules(plain, [('new', text('new')), ('m', changed)]))
    assert plain == {'m': first}
    collect_modules(plain, {'m': equivalent, 'new': text('new')})
    assert set(plain) == {'m', 'new'}
    for duplicate in (library.copy(), copy.deepcopy(library), pickle.loads(pickle.dumps(library))):
        assert isinstance(duplicate, ModuleLibrary)
        rejected(lambda duplicate=duplicate: duplicate.setdefault('m', changed))
    for method in (FAM.split_modules, lambda source: FAM.module_texts('m', source), FAM.library_closure):
        rejected(lambda method=method: method(first + changed))
        method(first + equivalent)
    rejected(lambda: FAM.module_texts('absent', first), 'does not define its requested module')
    return {'pass': True, 'mutation_apis': ['assignment', 'setdefault', 'update', '|=', '|', 'reverse |', 'constructor pairs'],
            'transactional_update': True, 'legacy_plain_dict': True, 'copy_pickle_preserve_strictness': True,
            'split_module_texts_closure': True}


def preprocessing_cases():
    dependent = "module macro_module(output wire y);\nassign y=`K;\nendmodule\n"
    contexts = "`define K 1'b0\n" + dependent + "`undef K\n`define K 1'b1\n" + dependent
    rejected(lambda: dedupe_modules(contexts))
    rejected(lambda: FAM.split_modules(contexts))
    rejected(lambda: ModuleLibrary([('macro_module', dependent), ('macro_module', dependent)]))
    # A single definition is retained, but repeated context-dependent
    # definitions require a real preprocessing step rather than guessing.
    assert dedupe_modules(dependent) == dependent
    literal = "module m(output wire y);\nlocalparam S=\"`K // /* text */\"; assign y=1'b0;\nendmodule\n"
    assert len(FAM.split_modules(literal + literal)) == 1
    comment = "// `K changes nothing here\n" + text('m')
    assert len(FAM.split_modules(comment + comment)) == 1
    first = text('m')
    rejected(lambda: FAM.split_modules(first + first + '`default_nettype none\n'))
    assert '`default_nettype none' in FAM.split_modules(first + '`default_nettype none\n')['m']
    return {'pass': True, 'different_macro_contexts_rejected': True,
            'identical_macro_dependent_bodies_rejected': True, 'string_and_comment_backticks_accepted': True,
            'semantic_suffix_validated_before_merge': True}


def direct_collectors():
    first = FAM.Module('m', {}, text('m'))
    changed = FAM.Module('m', {}, text('m', 1))
    equivalent = FAM.Module('m', {}, text('m', comment='equivalent comment'))
    for initial in ({}, ModuleLibrary()):
        emitter = ModeEmitter.__new__(ModeEmitter)
        emitter.library_used = initial
        emitter.library_module(first)
        emitter.library_module(equivalent)
        rejected(lambda: emitter.library_module(changed))
    net = Net('collector_net', '')
    net.inst(first, {'y': 'unused'}, '')
    net.inst(equivalent, {'y': 'unused2'}, '')
    assert len(net.extra) == 1 and net.extra_names == {'m'}
    assert len([event for event in net.events if event[0] == 'instance']) == 2
    rejected(lambda: net.inst(changed, {'y': 'unused3'}, ''))
    assert len(net.extra) == 1
    return {'pass': True, 'alu_plain_and_strict_maps': True, 'sfu_net_inst_preserves_events_and_extra': True}


def static_registry(directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'a.sv').write_text(text('registry_collision'))
    (directory / 'b.sv').write_text(text('registry_collision', 1))
    with patch.object(FAM, 'HERE', directory), patch.object(FAM, 'SV_FILES', ('a.sv', 'b.sv')), \
         patch.object(FAM, '_MODULE_TEXT', ModuleLibrary()):
        rejected(FAM._module_texts_of_files)
        assert not FAM._MODULE_TEXT
        (directory / 'b.sv').write_text(text('registry_collision', comment='equivalent'))
        assert set(FAM._module_texts_of_files()) == {'registry_collision'}
    return {'pass': True, 'cross_file_collision_rejected_before_cache': True}


def fixture(unit):
    if unit in ('alu', 'alu_fp'):
        from chialu.verify.alu_ref import normalize_spec
        floating = unit == 'alu_fp'
        formats = ('fp16', 'bf16') if floating else ('int8', 'int16')
        spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                               'modes': [{'count': 1, 'format': fmt} for fmt in formats],
                               'ops': ['fadd', 'fsub'] if floating else ['add', 'sub']})
        choices = {f'core.fp_adder.m{i}': ('single_path', {}) for i in range(2)} if floating else \
                  {f'core.adder.m{i}': ('ripple_carry', {'chunk_width_bits': 1}) for i in range(2)}
        return spec, choices, 'alu_mode.py'
    if unit == 'sfu':
        from chialu.verify.sfu_ref import normalize_sfu_spec
        spec = normalize_sfu_spec({'unit': 'vec_sfu', 'dut_name': 'sfu_core', 'check_en': False,
                                   'modes': [{'count': 1, 'format': 'fp8e4m3'}, {'count': 1, 'format': 'fp8e5m2'}],
                                   'functions': ['exp']})
        return spec, ('direct_lut', {}), 'sfu_seed.py'
    from chialu.verify.dot_ref import normalize_dot_spec
    mode = {'elements': 4, 'format_ab': 'int4', 'format_c': 'int8', 'format_d': 'int8'}
    spec = normalize_dot_spec({'unit': 'vec_dot_acc', 'dut_name': 'dot_core', 'check_en': False, 'modes': [dict(mode), dict(mode)]})
    return spec, ('integer_mac', {'accumulator_width_bits': 16}), 'dot_seed.py'


def seed_injection(unit, directory):
    from chialu.targets.derive import seed_alu_text, seed_for
    from chialu.verify.variant_selftest import check_seed
    spec, choice, receiver = fixture(unit)
    original = FAM.module_texts
    report = {'unit': unit}
    for conflicting in (True, False):
        calls = []
        def inject(name, source=None):
            result = original(name, source)
            caller = inspect.currentframe().f_back
            if Path(caller.f_code.co_filename).name == receiver:
                calls.append((caller.f_code.co_name, name))
                ordinal = len(calls)
                result['collector_injected_collision'] = text('collector_injected_collision',
                                                              int(conflicting and ordinal > 1), f'call {ordinal}')
            return result
        with patch.object(FAM, 'module_texts', inject):
            if conflicting:
                def generate():
                    return seed_alu_text(spec, families=choice) if spec['unit'] == 'alu' else seed_for(spec, family=choice)
                report['rejection'] = rejected(generate, 'collector_injected_collision')
            else:
                result = check_seed(spec, choice, directory / unit, 32, 939)
                assert result['pass'], result
                assert result.get('metrics', {}).get('bit_exact', True), result
                result['verified_vectors'] = len((directory / unit / 'vectors.hex').read_text().split())
                report['simulation'] = result
        assert len(calls) >= 2, (unit, receiver, calls)
        report['conflict_calls' if conflicting else 'equivalent_calls'] = calls
    report['pass'] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    root = (args.out or Path(tempfile.mkdtemp(prefix='chialu-module-collector-'))).resolve()
    root.mkdir(parents=True, exist_ok=True)
    report = {'pass': True, 'map': map_cases(), 'preprocessing': preprocessing_cases(), 'direct': direct_collectors(),
              'static': static_registry(root / 'registry'),
              'lexical': lexical_cases(), 'boundaries': boundary_cases()}
    report['seeds'] = []
    for unit in ('alu', 'alu_fp', 'sfu', 'dot'):
        report['seeds'].append(seed_injection(unit, root / 'seeds'))
        print(unit, 'PASS collision rejected and equivalent definitions simulate against golden', flush=True)
    (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS strict collectors, module identity and three unit simulations', root, flush=True)


if __name__ == '__main__':
    main()
