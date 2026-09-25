"""Synthesis receipts preserve the old mapping and make every median replayable."""
import copy
import json
import shutil
import statistics
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from adir.registry import underlying
from chialu import eda, synthdb
from chialu.synth_records import aggregate, get, replay, seeds_for, trace

RTL = 'module test(input [7:0] a,b,output [7:0] c); assign c=a+b; endmodule\n'


@pytest.fixture
def synth(tmp_path, monkeypatch):
    if not shutil.which('yosys'):
        pytest.skip('yosys required')
    monkeypatch.setenv('CHIALU_SYNTH_RECORDS', str(tmp_path / 'artifacts'))
    return underlying(eda.synth_ppa)


def test_seed_policy_and_descriptor_override():
    pdk = {'abc': {'scripts': {'medium': '+strash;dc2;map -D {clock_ps};topo;stime'}}}
    assert eda.abc_script_for(pdk, 'medium', 300, 23) == '+strash;permute -S 23;dc2;map -D 300;topo;stime'
    assert seeds_for() == [None, 11, 23, 37, 53]
    assert len(seeds_for(8)) == 8
    for n, seeds in [(0, None), (5, [1]), (3, [1, 1])]:
        with pytest.raises(ValueError):
            seeds_for(n, seeds)


def test_strict_median_and_independent_metrics():
    runs = [dict(ok=True, status='ok', repeat_index=i, abc_seed=i, area_um2=a,
                 abc_delay_ps=d, cells=i+10) for i, (a, d) in enumerate(zip([1, 2, 3, 4, 5], [5, 3, 4, 2, 1]))]
    r = aggregate(runs, 1)
    assert (r['area_um2'], r['abc_delay_ps'], r['cells_run_index']) == (3, 3, 2)
    runs[0].update(ok=False, status='timeout')
    r = aggregate(runs, 1)
    assert not r['ok'] and r['area_um2'] is None and r['abc_delay_ps'] is None
    assert r['successful_runs'] == 4 and len(r['runs']) == 5
    assert r['statistics']['area_um2']['median'] == 3.5


def test_cache_identity(monkeypatch):
    monkeypatch.setattr(synthdb, 'tool_hash', lambda *_: 'tool')
    monkeypatch.setattr(synthdb, 'liberty_hash', lambda *_: 'lib')
    kw = dict(pdk={'name': 'test'})
    assert eda.flow_id(kw) == eda.flow_id(dict(kw, repeats=5))
    assert eda.flow_id(dict(kw, repeats=1)) != eda.flow_id(kw)
    assert eda.flow_id(dict(kw, repeats=5, seeds=[1, 2, 3, 4])) != eda.flow_id(kw)
    assert eda._unit_key(RTL, 'test', [], kw['pdk'], 'medium', 300, 1) != eda._unit_key(RTL, 'test', [], kw['pdk'], 'medium', 300, 5)


def test_real_mapping_checkpoint_replay_and_failure(synth, tmp_path):
    one = synth(RTL, 'test', 'nangate45', 300, report=False, repeats=1)
    five = synth(RTL, 'test', 'nangate45', 300, report=False)
    assert one['ok'] and five['ok']
    for field in ('area_um2', 'abc_delay_ps', 'cells'):
        assert one[field] == five['runs'][0][field]
    for field in ('area_um2', 'abc_delay_ps'):
        assert five[field] == statistics.median(r[field] for r in five['runs'])
    for run in five['runs']:
        assert replay(run)['matches']
        assert get(run['log']) and run['tools']['executables']['yosys-abc']
        assert run['mapping_input'] == ('rtl' if run['repeat_index'] == 0 else 'rtlil')
    # Re-reading the checkpoint must preserve the mapping that the same script gets
    # from full elaboration, not introduce another uncontrolled perturbation.
    pdk = copy.deepcopy(eda._pdk('nangate45'))
    pdk['abc']['scripts']['medium'] = five['runs'][1]['abc_script']
    full = synth(RTL, 'test', pdk, 300, report=False, repeats=1)
    assert (full['area_um2'], full['abc_delay_ps']) == (five['runs'][1]['area_um2'], five['runs'][1]['abc_delay_ps'])
    from chialu.synth_records import main
    path = tmp_path / 'result.json'; path.write_text(json.dumps(five))
    assert main([str(path), '--run', '3']) == 0
    corrupt = copy.deepcopy(five['runs'][0]); corrupt['area_um2'] += 1
    assert not replay(corrupt)['matches']
    corrupt['tools']['versions'] = 'wrong'
    with pytest.raises(ValueError, match='tool identity'):
        replay(corrupt)
    failed = synth('this is not valid verilog', 'test', 'nangate45', 300, report=False)
    assert not failed['ok'] and len(failed['runs']) == 5
    assert all(r['status'] == 'fail' and get(r['stderr']) for r in failed['runs'])
    timeout = synth(RTL, 'test', 'nangate45', 300, report=False, timeout_s=0.001)
    assert not timeout['ok'] and len(timeout['runs']) == 5
    assert all(r['status'] == 'timeout' for r in timeout['runs'])


def test_old_integer_baseline_exact(synth):
    rtl = Path('targets/seeds/int_subword_alu.baseline.sv').read_text()
    r = synth(rtl, 'alu_core', 'nangate45', 300, report=False, repeats=1)
    # Captured from the unmodified synthesis implementation before this change.
    assert (r['area_um2'], r['abc_delay_ps'], r['cells']) == (5743.472, 1735.74, 4992)


def test_generated_and_derived_consumers(tmp_path):
    from chialu.pipeline import derived_run_file
    from chialu.surrogate_seeds import surrogate_run_file
    import re
    # the generators' repeat count (targets/make_targets.py SYNTH_REPEATS), read without importing the script
    SYNTH_REPEATS = int(re.search(r'^SYNTH_REPEATS = (\d+)', Path('targets/make_targets.py').read_text(), re.M).group(1))
    for file in Path('targets').rglob('*.yaml'):
        if '.surrogate' in file.name:
            continue
        doc = yaml.safe_load(file.read_text())
        for n in doc['adir'].get('evaluate', {}).get('nodes', {}).values():
            if n.get('node') in ('chialu.eda.synth_ppa', 'chialu.eda.synth_unit'):
                # Derived files are checked separately; generators own the primary files.
                if not any(x in file.name for x in ('.nollm', '.calib', '.best', '.pipeline')):
                    assert n['inputs']['repeats'] == SYNTH_REPEATS, file
    target = tmp_path / 'target.yaml'
    target.write_text(Path('targets/int_subword_alu.yaml').read_text())
    for n in (1, 5):
        for f in (derived_run_file(target, True, n), derived_run_file(target, False, n),
                  surrogate_run_file(target, 'sample', n), surrogate_run_file(target, 'full', n)):
            nodes = yaml.safe_load(f.read_text())['adir']['evaluate']['nodes']
            assert nodes['synth_ppa']['inputs']['repeats'] == n
            if '.surrogate_sample' in f.name:
                assert nodes['synth_ppa']['inputs']['report'] is False
            if 'synth_unit' in nodes:
                assert nodes['synth_unit']['inputs']['repeats'] == n


def test_synthdb_build_resynth_knob_and_receipts(synth, tmp_path, monkeypatch):
    monkeypatch.setattr(synthdb, 'build_tasks', lambda *a: [('adder', 'ripple_carry', {}, 'base', 8)])
    monkeypatch.setenv('CHIALU_SYNTH_DIR', str(tmp_path / 'db1'))
    assert synthdb.main(['build', '--kinds', 'adder', '--families', 'ripple_carry', '--widths', '8',
                         '--limit', '1', '--jobs', '1', '--repeats', '1']) == 0
    rows = synthdb.load('nangate45')
    assert len(rows) == 1 and rows[0]['flow']['repeats'] == 1
    assert len(rows[0]['result']['runs']) == 1
    monkeypatch.setenv('CHIALU_SYNTH_DIR', str(tmp_path / 'db5'))
    assert synthdb.main(['resynth', str(tmp_path / 'db1'), '--jobs', '1', '--repeats', '5']) == 0
    newer = synthdb.load('nangate45')
    assert len(newer) == 1 and newer[0]['flow']['repeats'] == 5
    assert len(newer[0]['result']['runs']) == 5
    assert synthdb.row_key(rows[0]) != synthdb.row_key(newer[0])


def test_unit_and_profile_preserve_receipts(synth, tmp_path, monkeypatch):
    monkeypatch.setattr(eda, 'SYNTH_CACHE_DIR', tmp_path / 'unit_cache')
    unit = underlying(eda.synth_unit)(RTL, [{'id': 'a', 'sv': 'test'}], 'nangate45', 300, repeats=5)
    assert len(unit['attribution']['a']['runs']) == 5
    from chialu.profile import measure
    result = measure(RTL, 'test', 'nangate45', 300, 'medium', 60, repeats=1)
    assert len(result['runs']) == 1


def test_local_executor_cache_keeps_receipts(synth, tmp_path):
    from adir.nodes import Executor, resolve_node
    spec = resolve_node('chialu.eda.synth_ppa')
    ex = Executor(tmp_path / 'cache', use_ray=False)
    kw = dict(rtl_text=RTL, top='test', pdk='nangate45', clock_ps=300, report=False)
    ex.run(spec, dict(kw, repeats=1))
    five = ex.run(spec, kw)
    assert ex.calls == 2 and len(five['runs']) == 5
    assert ex.run(spec, kw) == five and ex.hits == 1
    assert spec.resources['eda'] >= eda.SYNTH_WORKERS


def test_parallel_and_report_records(synth, monkeypatch):
    monkeypatch.setattr(eda, 'SYNTH_WORKERS', 2)
    r = synth(RTL, 'test', 'nangate45', 300, report=True)
    assert r['ok'] and len(r['runs']) == 5
    assert replay(r['report_run']['attribution_run'])['matches']
    assert replay(r['runs'][3])['matches']


def test_surrogate_dataset_and_seed_receipts(synth, monkeypatch, tmp_path):
    import adir.evaluate
    from chialu import surrogate_seeds as ss
    result = synth(RTL, 'test', 'nangate45', 300, report=False)
    monkeypatch.setattr(adir.evaluate, 'candidate_from_program', lambda *a, **kw: None)
    monkeypatch.setattr(adir.evaluate, 'evaluate_candidate', lambda *a, **kw: {
        'feasible': True, 'measurements': {'synth_ppa': {'value': result}, 'conformance': {'value': {'pass': True}}}})
    monkeypatch.setattr(ss, 'pinned_executor', lambda *a: None)
    st = ss.Stage.__new__(ss.Stage)
    st.inst = st.inst_sample = None
    st.out = st.run = tmp_path
    st.node_ip = None
    st.report = {}
    st.a = SimpleNamespace(top=1, prefix='front')
    row = st.evaluate('baseline', RTL)
    row.update(name='baseline', source='sample', scheme='unshared', plan={'why': 'test'})
    st.rows = [row]
    st.data_file = tmp_path / 'dataset.jsonl'
    import threading
    st.lock = threading.Lock()
    st.append(dict(row, name='second'))
    assert len(json.loads(st.data_file.read_text())['runs']) == 5
    monkeypatch.setattr(st, 'confirm_front', lambda: None)
    st.seeds()
    doc = json.loads((tmp_path / 'discovered.json').read_text())
    assert len(doc['synthesis']['front_1']['runs']) == 5
    assert len(st.report['seeds'][0]['synthesis']['runs']) == 5


def test_database_prefers_requested_repeat_count(monkeypatch):
    monkeypatch.setattr(synthdb, 'tool_hash', lambda *_: 'tool')
    single = {'tool_hash': 'tool', 'flow': {'repeats': 1}}
    median = {'tool_hash': 'tool', 'flow': {'repeats': 5}}
    assert synthdb._flow_filter('pdk', [single, median], 'adder') == [median]
    monkeypatch.setenv('CHIALU_DB_FLOW', 'strict')
    assert synthdb._flow_filter('pdk', [single], 'adder') == []


def test_pipeline_cli_forwards_repeat_count(tmp_path, monkeypatch):
    from chialu import pipeline
    target = tmp_path / 'target.yaml'
    target.write_text(Path('targets/int_subword_alu.yaml').read_text())
    commands = []
    monkeypatch.setattr(pipeline, 'sh', lambda cmd, *a, **kw: commands.append(cmd) or 0)
    assert pipeline.main([str(target), '--run-dir', str(tmp_path / 'run'), '--stage', 'train',
                          '--synth-repeats', '1', '--local']) == 0
    command = commands[0]
    assert command[command.index('--synth-repeats') + 1] == '1'
    record = json.loads((tmp_path / 'run/pipeline.json').read_text())
    assert record['synth_repeats'] == 1
    with pytest.raises(ValueError, match='different synthesis repeat count'):
        pipeline.main([str(target), '--run-dir', str(tmp_path / 'run'), '--stage', 'train', '--resume'])
