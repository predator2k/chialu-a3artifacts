"""Archive offline seed receipts and prompt-size estimates; never call a model."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = {
    "fpnew": "fpnew_fpnew_parallel_alu_core",
    "hardfloat": "hardfloat_alu_core",
    "transdot": "transdot_transdot_merged_alu_core",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "measurements/handseeds")
    args = ap.parse_args()
    summary = {}
    for ref, baseline in REFERENCES.items():
        run = args.scratch / ref
        target = ROOT / "targets/eval" / f"fp_alu_cmp_{ref}.hand_adaevolve.yaml"
        config = yaml.safe_load(target.read_text())["adir"]
        records = list((run / "seeds").glob("*/record.json"))
        assert len(records) == 1, records
        record = json.loads(records[0].read_text())
        measurements = {k: v["value"] for k, v in record["measurements"].items()}
        assert record["feasible"] and not record["hard_fail"] and not record.get("stderr"), record.get("stderr")
        for node, metric in (("lint", "ok"), ("conformance", "pass"), ("synth_ppa", "ok")):
            assert measurements[node][metric] is True, (ref, node, measurements[node])
        ppa = measurements["synth_ppa"]
        assert ppa["repeats"] == len(ppa["runs"]) >= 3   # SYNTH_REPEATS (3 since 2026-09-24)
        assert all(r["ok"] for r in ppa["runs"])
        prompt = (run / "prompt_sample.md").read_text()
        system = (run / "problem.md").read_text()
        assert "<<<<<<< HISTORY *" in prompt and ">>>>>>> HISTORY" in prompt
        assert "## Operator: free" in prompt and "program.sv" in prompt
        if ref == "transdot":
            assert "fpnew_merged_16" not in system   # standard contract since TransDot's UF fix (2026-09-25)
        source = Path(config["search"]["seeds"]["files"][0])
        size = source.stat().st_size
        assert size <= config["search"]["max_solution_bytes"]
        freeze = json.loads((run / "verify/freeze.json").read_text())
        old = json.loads((ROOT / "measurements/median5/results" / f"{baseline}.json").read_text())["repeats5"]
        dest = args.out / ref
        dest.mkdir(parents=True, exist_ok=True)
        for src, name in ((records[0], "record.json"), (run / "prompt_sample.md", "prompt_sample.md"),
                          (run / "problem.md", "problem.md"), (run / "contract.json", "contract.json"),
                          (run / "skydiscover.yaml", "skydiscover.yaml"), (run / "verify/freeze.json", "freeze.json")):
            shutil.copyfile(src, dest / name)
        summary[ref] = dict(target=str(target.relative_to(ROOT)), run_dir=str(run),
            seed=str(source), seed_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            target_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            feasible=True, lint=True, conformance=True, vectors=freeze["n_vectors"],
            area_um2=ppa["area_um2"], delay_ps=ppa["abc_delay_ps"],
            original_area_um2=old["area_um2"], original_delay_ps=old["abc_delay_ps"],
            area_change_pct=100*(ppa["area_um2"]/old["area_um2"]-1),
            delay_change_pct=100*(ppa["abc_delay_ps"]/old["abc_delay_ps"]-1),
            statistics=ppa["statistics"], original_statistics=old["statistics"],
            seed_bytes=size, seed_tokens_estimate=size/4,
            prompt_bytes=len((system+prompt).encode()), prompt_tokens_estimate=len((system+prompt).encode())/4,
            token_estimator="UTF-8 bytes / 4; seed is read through file tools, not inlined; excludes feedback/history",
            history_entries=config["search"]["history"]["entries"], history_response_verified=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
