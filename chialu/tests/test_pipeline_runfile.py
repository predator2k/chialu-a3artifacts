"""chialu.pipeline: the derived run file is safe to write from concurrent
repetitions and resolves its relative paths as the target does, and the
pipeline's exit code is the worst of its stages'."""
import json
import multiprocessing as mp
from pathlib import Path

import pytest
import yaml

from chialu import pipeline

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "targets/int_subword_alu.yaml"


def _derive(args):
    target, no_llm, repeats = args
    from chialu.pipeline import derived_run_file
    out = []
    for _ in range(20):
        p = derived_run_file(Path(target), no_llm, repeats)
        out.append((str(p), p.read_text()))
    return out


@pytest.fixture
def cleanup_derived():
    made = []
    yield made
    for p in made:
        Path(p).unlink(missing_ok=True)


def _repeats(text):
    nodes = yaml.safe_load(text)["adir"]["evaluate"]["nodes"]
    return {n["inputs"]["repeats"] for n in nodes.values()
            if n.get("node") in ("chialu.eda.synth_ppa", "chialu.eda.synth_unit")}


def test_concurrent_derivations_never_see_a_partial_or_foreign_file(tmp_path, cleanup_derived):
    target = tmp_path / "t.yaml"
    target.write_text(TARGET.read_text())
    jobs = [(str(target), False, 3)] * 6 + [(str(target), False, 5)] * 3 + [(str(target), True, 3)] * 3
    with mp.get_context("spawn").Pool(12) as pool:
        results = pool.map(_derive, jobs)
    by_args = {}
    for args, res in zip(jobs, results):
        for path, text in res:
            by_args.setdefault(args, set()).add((path, text))
    # every reader saw one complete file per derivation, its own
    for (target_, no_llm, repeats), seen in by_args.items():
        assert len(seen) == 1, (no_llm, repeats, [p for p, _ in seen])
        path, text = seen.pop()
        assert Path(path).parent == target.parent
        assert _repeats(text) == {repeats}
        assert (".nollm." if no_llm else ".pipeline.") in Path(path).name
    names = {Path(p).name for s in results for p, _ in s}
    assert len(names) == 3
    assert not [f for f in tmp_path.iterdir() if f.name.endswith(".tmp")]      # no temporary left behind
    assert target.read_text() == TARGET.read_text()                             # the source stays intact


def test_derived_file_resolves_paths_as_the_target(tmp_path, cleanup_derived):
    from adir.instance import load
    derived = pipeline.derived_run_file(TARGET, False, 3)
    cleanup_derived.append(derived)
    assert derived.parent == TARGET.parent
    a = load(str(TARGET), run_dir_override=str(tmp_path / "a"))
    b = load(str(derived), run_dir_override=str(tmp_path / "b"))
    assert a.base_dir == b.base_dir
    assert a.knowledge and a.knowledge == b.knowledge
    assert json.dumps(a.task, sort_keys=True, default=str) == json.dumps(b.task, sort_keys=True, default=str)
    assert json.dumps(a.role, sort_keys=True, default=str) == json.dumps(b.role, sort_keys=True, default=str)


def _main(tmp_path, monkeypatch, codes, stages):
    target = tmp_path / "target.yaml"
    target.write_text(TARGET.read_text())
    seq = iter(codes)
    monkeypatch.setattr(pipeline, "sh", lambda cmd, *a, **kw: next(seq))
    (tmp_path / "run").mkdir()
    (tmp_path / "run/discovered.json").write_text(json.dumps({"plans": {"front_1": {}}}))
    argv = [str(target), "--run-dir", str(tmp_path / "run"), "--local"]
    for s in stages:
        argv += ["--stage", s]
    rc = pipeline.main(argv)
    return rc, json.loads((tmp_path / "run/pipeline.json").read_text())


def test_exit_is_zero_when_every_stage_passes(tmp_path, monkeypatch):
    rc, rep = _main(tmp_path, monkeypatch, [0, 0], ["train", "numeric"])
    assert rc == 0 and rep["exit"] == 0
    assert rep["argv"][-4:] == ["--stage", "train", "--stage", "numeric"]
    assert (tmp_path / "run/run_file.yaml").read_text() == Path(rep["run_file"]).read_text()


def test_exit_is_the_worst_stage(tmp_path, monkeypatch):
    rc, rep = _main(tmp_path, monkeypatch, [0, 3], ["train", "numeric"])
    assert rc == 3 and rep["exit"] == 3 and rep["stages"]["train"]["exit"] == 0


def test_failed_seeds_stage_fails_the_pipeline_even_when_search_passes(tmp_path, monkeypatch):
    rc, rep = _main(tmp_path, monkeypatch, [1, 0], ["seeds", "search"])
    assert rep["stages"]["seeds"]["exit"] == 1 and rep["stages"]["search"]["exit"] == 0
    assert rc == 1


def test_signal_counts_as_failure():
    assert pipeline.stages_exit({"search": {"exit": -9}}, ["search"]) == 137
    assert pipeline.stages_exit({"search": "skipped (--no-llm)"}, ["search"]) == 0
    # an earlier leg's stage that this invocation did not run does not count
    assert pipeline.stages_exit({"seeds": {"exit": 1}, "search": {"exit": 0}}, ["search"]) == 0
    assert pipeline.stages_exit({"numeric": {"exit": 0, "front_seeds_exit": 2}}, ["legacy_numeric"]) == 2


def test_seeds_then_search_in_two_invocations_keep_both_records(tmp_path, monkeypatch):
    """The launcher runs the seeds stage and the search as two commands (each rc logged): the second
    keeps the first's stage record and both command lines, and refuses another repeat count."""
    rc, _ = _main(tmp_path, monkeypatch, [0], ["seeds"])
    assert rc == 0
    (tmp_path / "run/results_db.jsonl").write_text(json.dumps({"is_seed": True, "seed_name": "front_1"}) + "\n")
    seq = iter([4])
    monkeypatch.setattr(pipeline, "sh", lambda cmd, *a, **kw: next(seq))
    target = tmp_path / "target.yaml"
    rc = pipeline.main([str(target), "--run-dir", str(tmp_path / "run"), "--local", "--stage", "search",
                        "--search-seed", "2"])
    rep = json.loads((tmp_path / "run/pipeline.json").read_text())
    assert rc == 4 and rep["stages"]["seeds"]["exit"] == 0 and rep["stages"]["search"]["exit"] == 4
    assert [i["stages"] for i in rep["invocations"]] == [["seeds"], ["search"]]
    assert [i["exit"] for i in rep["invocations"]] == [0, 4]
    with pytest.raises(ValueError, match="synth_repeats"):
        pipeline.main([str(target), "--run-dir", str(tmp_path / "run"), "--local", "--stage", "search",
                       "--synth-repeats", "5"])
