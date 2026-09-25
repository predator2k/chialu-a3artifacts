"""Model/YAML dispatch and noise thresholds, with no synthesis or Ray jobs."""
import io
import json
import pickle
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import numpy as np
import pytest
import yaml

from chialu import surrogate_gnn as gnn
from chialu.surrogate_gnn_pack import pack, topo_levels
from chialu.surrogate_metrics import pair_metrics
from chialu.surrogate_seeds import Stage, XGB, accuracy, calibration_knobs, fit, predict, scheme_trained

ROOT = Path(__file__).resolve().parents[1]


def test_yaml_defaults_overrides_and_generated_variants(tmp_path):
    path = tmp_path / 'target.yaml'
    path.write_text('adir: {}')
    assert calibration_knobs(path, SimpleNamespace())['model'] == 'xgboost'
    cal = dict(model='gnn', min_delay_gap_pct=7, min_area_gap_pct=3,
               gnn=dict(config='G1', python='/torch/python', host='gpu', workdir='/scratch/gnn'))
    path.write_text(yaml.safe_dump({'adir': {'search': {'extensions': {'calibration': cal}}}}))
    knobs = calibration_knobs(path, SimpleNamespace(min_delay_gap_pct=10))
    assert knobs['min_delay_gap_pct'] == 10 and knobs['min_area_gap_pct'] == 3
    assert knobs['gnn'] == cal['gnn'] and knobs['model'] == 'gnn'
    for p in ROOT.joinpath('targets').rglob('*.yaml'):
        d = yaml.safe_load(p.read_text())
        c = d.get('adir', {}).get('search', {}).get('extensions', {}).get('calibration')
        if c:
            assert (c['model'], c['min_delay_gap_pct'], c['min_area_gap_pct']) == ('xgboost', 5, 2), p
            assert c['gnn']['config'] == 'G5' and c['gnn']['ensemble_size'] == 3
    for value in (-1, float('nan'), float('inf')):
        with pytest.raises(ValueError):
            calibration_knobs(path, SimpleNamespace(min_area_gap_pct=value))
    with pytest.raises(ValueError, match='model'):
        calibration_knobs(path, SimpleNamespace(model='wrong'))


@pytest.mark.parametrize('weighted', [False, True])
def test_xgboost_predictions_and_trees_bit_identical(weighted):
    """Compare to the pre-dispatch fitting algorithm, including its saved booster bytes."""
    from xgboost import XGBRegressor
    from chialu.surrogate_features import vector
    rng = np.random.default_rng(12)
    feats = [{'a': float(a), 'b': float(b)} for a, b in rng.random((32, 2))]
    ys = {'area_um2': [10 + f['a'] * 3 for f in feats], 'delay_ps': [200 + f['b'] * 10 for f in feats]}
    weights = [5 if i < 8 else 1 for i in range(32)] if weighted else None
    names = sorted({k for f in feats for k in f})
    x = np.stack([vector(f, names) for f in feats])
    reference = {}
    for t, y in ys.items():
        m = XGBRegressor(**XGB, random_state=7, n_jobs=8, verbosity=0)
        m.fit(x, np.log(np.asarray(y, dtype=float)),
              sample_weight=None if weights is None else np.asarray(weights, float))
        reference[t] = m
    default = fit(feats, ys, 7, weights)
    explicit = fit(feats, ys, 7, weights, model='xgboost')
    legacy = dict(models=reference, names=names)
    for bundle in (default, explicit, pickle.loads(pickle.dumps(legacy))):
        for t in ys:
            assert bundle['models'][t].get_booster().save_raw() == reference[t].get_booster().save_raw()
            np.testing.assert_array_equal(predict(bundle, feats)[t], np.exp(reference[t].predict(x)))


def test_gap_threshold_truth_only_ties_and_double_log_regression():
    # 100 -> 106 is 6%, but log(log(106))-log(log(100)) is only ~1.3%.
    y = np.log([100., 104., 106.])
    p = np.log([100., 106., 104.])
    m = pair_metrics(y, p)
    assert m['pairs'] == 1 and m['accuracy'] == 1
    assert m['pairs_all_pairs'] == 3 and m['accuracy_all_pairs'] == pytest.approx(2 / 3)
    assert accuracy(np.exp(p), np.exp(y), .99)['pairs'] == 1
    assert pair_metrics(np.log([100, 105]), [0, 0])['accuracy'] == .5
    assert pair_metrics(np.log([100, 104.999]), [0, 1])['pairs'] == 0
    assert pair_metrics([1, 1], [0, 1], 0)['accuracy'] is None
    assert pair_metrics(np.log([100, 101]), [-100, 100])['pairs'] == 0
    assert pair_metrics(y, p, 0)['pairs'] == 3
    assert pair_metrics(y, p, 10)['pairs'] == 0
    # Physical rescaling changes neither pair membership nor order.
    assert pair_metrics(y - 8, p - 8)['pairs'] == 1


def test_gap_bins_and_all_pair_spearman_identity():
    from scipy.stats import spearmanr
    for gap, label in [(1, '0-2'), (2, '2-5'), (5, '5-10'), (10, '10-20'), (20, '10-20'), (21, '>20')]:
        out = pair_metrics(np.log([100, 100 + gap]), [0, 1])
        assert out['gap_bins'][label]['pairs'] == 1
        assert sum(v['pairs'] for v in out['gap_bins'].values()) == 1
    y, p = [0, 2, 3, 4], [3, 0, 4, 1]
    assert pair_metrics(y, p, 0)['rho'] == pytest.approx(spearmanr(y, p).statistic)


def test_comparison_front_hard_bootstrap_and_saved_log_arrays(tmp_path):
    from chialu.surrogate_compare import metrics, hard_pairs, metric_context, paired_bootstrap, summarize, LADDER
    y = np.log([[100, 100], [100.5, 104], [101, 106]])
    p = np.log([[100, 100], [100.5, 106], [101, 104]])
    m = metrics(y, p)
    assert m['hard_pairs'] == m['front_pairs'] == m['delay_pairs'] == 1
    assert m['hard_pairs_all_pairs'] == 3 and m['hard_accuracy'] == 1
    assert m['area_pairs'] == 0 and m['area_rho'] is None
    assert len(hard_pairs(y)[0]) == 1
    ctx = metric_context(y, min_delay_gap_pct=10, min_area_gap_pct=0)
    assert metrics(y, p, context=ctx)['hard_pairs'] == 0
    b = paired_bootstrap(y, p, y, n_bootstrap=5, min_delay_gap_pct=10)
    assert b['hard_accuracy']['valid_replicates'] == 0
    np.savez(tmp_path / 'S1_seed0.npz', truth=y, names=['a', 'b', 'c'], **{k: p for k in LADDER})
    reports = [dict(fold='S1_seed0', protocol='S1')]
    s = summarize(reports, tmp_path, 2)
    assert s['protocols']['S1']['mean_metrics']['B0']['hard_pairs'] == 1
    s = summarize(reports, tmp_path, 2, dict(min_delay_gap_pct=10, min_area_gap_pct=0))
    assert s['protocols']['S1']['mean_metrics']['B0']['hard_pairs'] == 0
    assert json.loads((tmp_path / 'S1_seed0.json').read_text())['metrics']['B0']['hard_pairs'] == 0


def tiny_graph(v=1):
    """A three-node chain exercises topology, pooling and a nontrivial numeric input."""
    return dict(x_cat=np.array([[3], [2], [1]]), x_num=np.array([[v], [2], [3]], dtype=np.float32),
                edge_index=np.array([[0, 1], [1, 2]]), edge_type=np.array([1, 1]), edge_mode=np.array([-1, 0]),
                edge_w=np.array([.1, .2], dtype=np.float32), globals=np.array([v], dtype=np.float32),
                meta=dict(cat_fields=['node_type'], num_fields=['value'], global_names=['est_area'],
                          node_types=['top', 'mode', 'choice'], edge_types=['path'], vocab_sizes={'node_type': 4}))


def test_graph_packing_never_logs_labels_twice(tmp_path):
    gs = [tiny_graph(1), tiny_graph(2)]
    y = np.log([[100, 106], [200, 210]])
    pack(gs, y, tmp_path / 'graphs.npz')
    with np.load(tmp_path / 'graphs.npz') as data:
        np.testing.assert_array_equal(data['y'], y)
        np.testing.assert_array_equal(data['node_off'], [0, 3, 6])
        np.testing.assert_array_equal(data['level'], [0, 1, 2, 0, 1, 2])
        np.testing.assert_array_equal(data['edge_index'][:, 2:], gs[1]['edge_index'])
    with pytest.raises(ValueError, match='cycle'):
        topo_levels(2, np.array([[0, 1], [1, 0]]))


def test_gnn_dispatch_gating_and_stage_knobs(monkeypatch):
    calls = []
    def fake_execute(request, config):
        calls.append((request, config))
        return {'members': []} if request['action'] == 'fit' else np.log([[123, 456]])
    monkeypatch.setattr(gnn, 'execute', fake_execute)
    stage = Stage.__new__(Stage)
    stage.knobs = dict(model='gnn', gnn={'config': 'G1', 'epochs': 2}, min_per_scheme=3,
                       min_area_gap_pct=3, min_delay_gap_pct=9)
    stage.a = SimpleNamespace(seed=11)
    stage.graph_space = {'test': True}
    assert stage.graph_rows([], {'models': {}, 'names': []}) is None
    monkeypatch.setattr(stage, 'graph_rows', lambda rows, bundle=None: [tiny_graph(i) for i, _ in enumerate(rows)])
    rows = [dict(feat={}, vals={}, scheme=s, area_um2=100+i, delay_ps=200+i)
            for i, s in enumerate(['a', 'a', 'a', 'b'])]
    b = stage.fit_rows(rows, [1, 2, 3, 4])
    assert b['model_type'] == 'gnn' and scheme_trained(b, 'a') and not scheme_trained(b, 'b')
    assert not scheme_trained(b, 'never')
    assert calls[0][1]['min_delay_gap_pct'] == 9 and calls[0][1]['epochs'] == 2
    np.testing.assert_array_equal(calls[0][0]['weights'], [1, 2, 3, 4])
    assert stage.metric_gap('area_um2') == 3
    assert stage.predict_rows(pickle.loads(pickle.dumps(b)), rows[:1])['delay_ps'][0] == pytest.approx(456)


def test_eda_dispatch_keeps_scheme_gate(monkeypatch):
    from adir.registry import underlying
    from chialu import eda, surrogate_features
    b = dict(model_type='gnn', schemes={'seen': 4}, min_per_scheme=3, graph_space={})
    monkeypatch.setattr(eda, '_surrogate_parts', lambda *args: (b, {}))
    monkeypatch.setattr(surrogate_features, 'features', lambda *args: {'EST__area': 1})
    def graph_input(space, files, vals, *rest):
        assert vals['check.rule.family'] == 'parity'
        assert vals['core.adder.m0.family'] == 'ripple'
        return tiny_graph()
    monkeypatch.setattr(gnn, 'graph_input', graph_input)
    monkeypatch.setattr(gnn, 'predict', lambda bundle, graphs: {'area_um2': [123.456], 'delay_ps': [456.789]})
    node = underlying(eda.surrogate)
    assert not node({}, {}, 'unused', scheme='unseen')['ok']
    out = node({}, {}, 'unused', scheme='seen', full_decl={
        'decl.check.rule.family': 'parity', 'decl.core.adder.m0.family': 'ripple'})
    assert out['ok'] and out['area_um2'] == 123.46 and out['delay_ps'] == 456.79
    assert out['known'] is None


def test_local_interpreter_transport_without_torch(tmp_path, monkeypatch):
    worker = tmp_path / 'surrogate_gnn_worker.py'
    worker.write_text('import pathlib, pickle, sys\np=pathlib.Path(sys.argv[1])\nr=pickle.loads((p/"request.pkl").read_bytes())\n(p/"result.pkl").write_bytes(pickle.dumps(r["probe"]))\n')
    monkeypatch.setattr(gnn, '__file__', str(tmp_path / 'surrogate_gnn.py'))
    assert gnn.execute({'probe': [3, 4]}, dict(python=sys.executable)) == [3, 4]


def test_remote_transport_quotes_paths_and_ships_package(monkeypatch):
    def fake_run(cmd, **kw):
        assert cmd[:3] == ['ssh', '-o', 'BatchMode=yes']
        assert cmd[3] == 'gpu'
        import shlex
        assert shlex.split(cmd[4])[-1] == '/scratch/with space'
        with zipfile.ZipFile(io.BytesIO(kw['input'])) as archive:
            assert set(gnn.WORKER_FILES) < set(archive.namelist())
            assert pickle.loads(archive.read('request.pkl'))['probe'] == 42
        return SimpleNamespace(returncode=0, stdout=pickle.dumps(42), stderr=b'')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    assert gnn.execute({'probe': 42}, dict(python='/python with space', host='gpu', workdir='/scratch/with space')) == 42
    with pytest.raises(ValueError):
        gnn.options(dict(host='gpu'))


@pytest.fixture(scope='module')
def torch_python():
    candidate = Path('$CHIALU_HOME/venvs/torch-cpu/bin/python')
    interpreter = str(candidate) if candidate.exists() else sys.executable
    probe = subprocess.run([interpreter, '-c', 'import torch, numpy'], capture_output=True)
    if probe.returncode:
        pytest.skip('CPU torch unavailable: installation index supplied no matching wheel')
    return interpreter


@pytest.mark.parametrize('config', ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8'])
def test_real_torch_ensemble_reload_and_batch_invariance(torch_python, config):
    gs = [tiny_graph(i + 1) for i in range(6)]
    ys = {'area_um2': [100 + i * 4 for i in range(6)], 'delay_ps': [200 + i * 7 for i in range(6)]}
    b = fit([{}] * 6, ys, seed=4, weights=[1, 1, 1, 1, 5, 5], schemes=['a'] * 6, min_per_scheme=4,
            model='gnn', graphs=gs, graph_space={},
            gnn=dict(config=config, python=torch_python, ensemble_size=2, epochs=2, patience=1,
                     hidden=8, batch=8, dropout=0, cat_drop=0, threads=1))
    p = predict(b, [], graphs=gs)
    q = predict(pickle.loads(pickle.dumps(b)), [], graphs=gs[:1])
    assert len(b['members']) == 2 and scheme_trained(b, 'a')
    for k in ys:
        assert np.isfinite(p[k]).all() and (p[k] > 0).all()
        np.testing.assert_allclose(p[k][:1], q[k], rtol=2e-5)


def test_numeric_gnn_passes_full_declaration_and_keeps_checker_records(tmp_path):
    from chialu.surrogate_seeds import surrogate_numeric_file, surrogate_declaration
    numeric = tmp_path / 'unit.numeric.yaml'
    numeric.write_text((ROOT / 'targets/int_subword_alu.numeric.yaml').read_text())
    path = surrogate_numeric_file(numeric, tmp_path / 'model.pkl', {})
    assert 'full_decl' not in yaml.safe_load(path.read_text())['adir']['evaluate']['nodes']['surrogate']['inputs']
    path = surrogate_numeric_file(numeric, tmp_path / 'model.pkl', {}, model_type='gnn')
    assert yaml.safe_load(path.read_text())['adir']['evaluate']['nodes']['surrogate']['inputs']['full_decl'] == 'declaration'
    row = {'measurements': {'declaration': {'value': {'decl.core.a': 1, 'decl.check.a': 2,
                                                    'decl.x_form': 'exact', 'decl.domain': []}}}}
    assert surrogate_declaration(row, 'gnn') == {'core.a': 1, 'check.a': 2, 'x_form': 'exact'}
    assert surrogate_declaration(row) == {'core.a': 1, 'x_form': 'exact'}


def test_seed_cli_overrides_reach_stage(tmp_path, monkeypatch):
    from chialu import surrogate_seeds as ss
    target = tmp_path / 'target.yaml'
    target.write_text('adir: {}')
    seen = []
    class FakeStage:
        def __init__(self, args):
            seen.append(calibration_knobs(target, args))
            self.pool = SimpleNamespace(shutdown=lambda: None)
            self.out = tmp_path
            self.report = {}
        def save_report(self): pass
        def setup(self): pass
        def sample(self): return {}
        def log(self, message): pass
    monkeypatch.setattr(ss, 'Stage', FakeStage)
    assert ss.main([str(target), '--run-dir', str(tmp_path), '--stage', 'sample', '--model', 'gnn',
                    '--min-delay-gap-pct', '11', '--min-area-gap-pct', '4']) == 0
    assert (seen[0]['model'], seen[0]['min_delay_gap_pct'], seen[0]['min_area_gap_pct']) == ('gnn', 11, 4)


def test_compare_cli_rescores_saved_logs_with_yaml_and_overrides(tmp_path):
    from chialu import surrogate_compare as cmp
    rows = [dict(name=f'r{i:03}', vals={'core.x': i}, feat={'a': i}, scheme=f's{i % 4}',
                 area_um2=100 + i, delay_ps=200 + 3*i, source='round1') for i in range(20)]
    dataset = tmp_path / 'dataset.jsonl'
    dataset.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    _, info = cmp.load_dataset(dataset)
    splits = cmp.make_splits(rows, [0])
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'manifest.json').write_text(json.dumps({'dataset': info, 'seeds': [0]}))
    lookup = {r['name']: r for r in rows}
    for fold in splits['folds']:
        y = np.log([[lookup[n]['area_um2'], lookup[n]['delay_ps']] for n in fold['test']])
        np.savez(output / (fold['id'] + '.npz'), truth=y, names=fold['test'], **{k: y for k in cmp.LADDER})
        (output / (fold['id'] + '.json')).write_text(json.dumps({'fold': fold['id'], 'protocol': fold['protocol']}))
    config = tmp_path / 'config.yaml'
    config.write_text('adir:\n  search:\n    extensions:\n      calibration:\n        min_delay_gap_pct: 7\n        min_area_gap_pct: 4\n')
    assert cmp.main(['--dataset', str(dataset), '--output', str(output), '--splits-dir', str(tmp_path / 'splits'),
                     '--seeds', '0', '--bootstrap', '2', '--jobs', '1', '--summarize-only',
                     '--calibration', str(config), '--min-delay-gap-pct', '11']) == 0
    summary = json.loads((output / 'summary.json').read_text())
    assert summary['identity']['gaps'] == {'min_delay_gap_pct': 11, 'min_area_gap_pct': 4}


def test_surrogate_seeds_defaults_to_three_repeats_and_records_invocations(tmp_path, monkeypatch):
    """--synth-repeats defaults to 3 (the targets' count), and report.json keeps the
    command line, steps and seed of every invocation, earlier ones included."""
    import json
    from types import SimpleNamespace
    from chialu import surrogate_seeds as SS
    seen = []
    monkeypatch.setattr(SS.Stage, 'setup', lambda self: setattr(self, 'pool', SimpleNamespace(shutdown=lambda: None)))
    monkeypatch.setattr(SS.Stage, 'seeds', lambda self: seen.append((self.a.synth_repeats, self.a.seed)))
    run = tmp_path / 'run'
    (run / 'surrogate').mkdir(parents=True)
    (run / 'surrogate' / 'dataset.jsonl').write_text('')
    target = str(ROOT / 'targets' / 'int_subword_alu.yaml')
    assert SS.main([target, '--run-dir', str(run), '--stage', 'seeds']) == 0
    assert SS.main([target, '--run-dir', str(run), '--stage', 'seeds', '--seed', '7']) == 0
    assert seen == [(3, 0), (3, 7)]
    inv = json.loads((run / 'surrogate' / 'report.json').read_text())['invocations']
    assert [(i['seed'], i['stages'], i['synth_repeats'], i['exit']) for i in inv] == [(0, ['seeds'], 3, 0), (7, ['seeds'], 3, 0)]
    assert inv[1]['argv'][-2:] == ['--seed', '7'] and inv[0]['argv'][1:3] == ['-m', 'chialu.surrogate_seeds']
