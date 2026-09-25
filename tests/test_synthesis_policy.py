"""The plain evaluator and reporting boundary retain the complete synthesis receipt."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('plain_median_test', ROOT / 'harness/plain_loop.py')
plain = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = plain
spec.loader.exec_module(plain)


def test_plain_evaluator_repeat_knob_and_receipt(tmp_path, monkeypatch):
    from chialu.synth_records import replay
    monkeypatch.setenv('CHIALU_SYNTH_RECORDS', str(tmp_path / 'artifacts'))
    monkeypatch.setenv('CHIALU_SYNTH_REPORT', '0')
    from chialu import eda
    monkeypatch.setattr(eda, 'SYNTH_REPORT', False)
    t = SimpleNamespace(checker_rtl=None, top='test', pdk='nangate45', clock_ps=300,
                        synth_timeout_s=60, effort='medium', synth_repeats=5)
    ev = plain.Evaluator(t, ('synth',), synth_infeasible=True)
    m, _, _, _ = ev.run('module test(input [7:0] a,b,output [7:0] c); assign c=a+b; endmodule')
    assert m['synth_ppa']['repeats'] == 5 and len(m['synth_ppa']['runs']) == 5
    assert replay(m['synth_ppa']['runs'][2])['matches']
    t.synth_repeats = 1
    assert ev.run('module test(input a,output b); assign b=a; endmodule')[0]['synth_ppa']['repeats'] == 1


def test_summary_points_to_complete_archive(tmp_path):
    receipt = {'candidate_id': 'seed:baseline', 'is_seed': True, 'feasible': True,
               'goal_values': [10, 20], 'score': {'combined_score': 1}}
    archive = SimpleNamespace(records=lambda: [receipt], front=lambda goal: [receipt])
    t = SimpleNamespace(synth_repeats=5)
    import time
    plain.summarize(tmp_path, archive, None, t, 0, time.time())
    summary = json.loads((tmp_path / 'summary.json').read_text())
    assert summary['synthesis_records']['path'] == str(tmp_path / 'results_db.jsonl')
    assert summary['seed']['candidate_id'] == receipt['candidate_id']


def test_baseline_constants_have_five_run_receipts():
    for name in ('int_subword_alu', 'fp_alu_cmp', 'fp_alu_cmp_hf'):
        record = json.loads((ROOT / 'measurements/median5' / (name + '.json')).read_text())
        assert record['repeats5']['successful_runs'] == 5
        assert len(record['repeats5']['runs']) == 5
