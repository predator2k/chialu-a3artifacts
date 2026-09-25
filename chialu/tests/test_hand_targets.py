"""The hand experiment must preserve the gates, provider and history protocol."""
import json
from pathlib import Path
from types import SimpleNamespace

import yaml

from targets import make_targets as targets

ROOT = Path(__file__).resolve().parents[1]


def test_provider_output_limit():
    text = targets.search_block(True, provider="deepseek", model="deepseek-flash")
    models = yaml.safe_load(text)["search"]["models"]
    assert all(m["max_output_tokens"] == 393216 for m in models.values())
    default = yaml.safe_load(targets.search_block(True))["search"]["models"]
    assert default["solution"]["provider"] == targets.PROVIDER
    assert default["solution"]["max_output_tokens"] == targets.MAX_OUTPUT_TOKENS


def test_hand_experiment_gates():
    for ref in ("fpnew", "hardfloat", "transdot"):
        name = f"fp_alu_cmp_{ref}"
        config = yaml.safe_load((ROOT / "targets/eval" / f"{name}.hand_adaevolve.yaml").read_text())["adir"]
        search = config["search"]
        assert config["run_dir"] == f"run/{name}.hand_adaevolve"
        assert search["backend"] == "adaevolve" and search["iterations"] == 20
        assert search["history"] == {"entries": 7}
        assert search["prompts"]["declarations"] is False
        assert search["prompts"]["variants"]["operator"] == ["free"]
        assert search["prompts"]["omit_vars"] == ["realization", "core.*", "behavior_rules"]
        assert search["seeds"]["discovered"] is False
        assert len(search["seeds"]["files"]) == 1
        assert not search["replan"]
        nodes = config["evaluate"]["nodes"]
        assert set(nodes) == {"declaration", "lint", "conformance", "yosys_stat", "synth_ppa"}
        assert nodes["synth_ppa"]["inputs"]["repeats"] == targets.SYNTH_REPEATS
        assert {c["metric"] for c in config["constraints"] if c.get("hard")} == {
            "declaration.ok", "lint.ok", "conformance.pass", "synth_ppa.ok"}
        for model in search["models"].values():
            assert (model["agent"], model["provider"], model["model"], model["effort"]) == (
                "opencode", "deepseek", "deepseek-flash", "high")
            assert model["max_output_tokens"] <= 393216
        comparison = yaml.safe_load((ROOT / "targets/eval" / f"{name}.yaml").read_text())["adir"]
        for key in ("modes", "ops", "rounding", "tininess", "flag_scope", "underflow_contract"):
            assert config["variables"].get(key) == comparison["variables"].get(key)
    assert search["max_solution_bytes"] > 407707


def test_history_round_trip(tmp_path):
    from adir.backends.skydiscover import record_history
    from adir.composer import _history_notes
    (tmp_path / "last_prompt.json").write_text(json.dumps({"regions": ["*"]}))
    for i in range(1, 10):
        saved = record_history(tmp_path, f"<<<<<<< HISTORY *\nreplaced:\na\nwith:\nb\nwhy: trial {i}\n>>>>>>> HISTORY")
        assert saved == [{"region": "*", "edit": i}]
    prompt = "\n".join(_history_notes(SimpleNamespace(search={"history": {"entries": 7}}), tmp_path, None, {}))
    assert "history/*.md" in prompt
    assert "why: trial 1 --" not in prompt and "why: trial 2 --" not in prompt
    assert all(f"why: trial {i} --" in prompt for i in range(3, 10))


def test_comparison_bindings():
    from chialu.verify.search_coverage_selftest import bind
    for ref in ("fpnew", "hardfloat", "transdot"):
        inst = bind(f"targets/eval/fp_alu_cmp_{ref}.yaml")
        assert inst.bindings
        if ref == "hardfloat":
            assert not any(k.startswith("core.fp_adder.m2.") for k in inst.bindings)
