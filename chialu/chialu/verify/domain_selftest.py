"""The chiALU domain through ADIR end to end, without a model or a
cluster: a small checked ALU is bound from a run file, its seed
artifact, checker and verify bundle are generated, the four sharing
plans are rendered as seeds with their declaration blocks, and, when
verilator and yosys are on the PATH, every seed runs through the
conformance, fault and synthesis nodes in ADIR's local executor.

    python3 -m chialu.verify.domain_selftest [--no-eda] [--work DIR]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from chialu.verify.simulate import scaled

REPO_ROOT = Path(__file__).resolve().parents[2]

RUN = {
    "cluster_name": "domain_selftest",
    "cache": {"synth_ppa": {"cache": True}},
    "adir": {
        "module": "chialu.ALU",
        "variables": {
            "modes": {"runtime": [{"count": 1, "format": "int16"}, {"count": 2, "format": "int8"}]},
            "ops": {"runtime": ["add", "sub", "min", "mul_wide", "shl"]},
            "check_en": {"fixed": True},
            "accuracy": {"fixed": "exact"},
            "rounding": {"fixed": "RNE"},
            "daz_in": {"fixed": False},
            "ftz_out": {"fixed": False},
            "unary_dual": {"fixed": False},
            "flags": {"fixed": []},
            "sr_bits": {"fixed": 16},
            "nan_payload": {"fixed": "canonical"}, "invalid_result": {"fixed": "saturate"},
            "nan_to_int": {"fixed": "zero"}, "minmax_nan": {"fixed": "propagate"},
            "tininess": {"fixed": "after"}, "int_div_zero": {"fixed": "riscv"},
            "zero_sign": {"fixed": "positive"}, "quire_overflow": {"fixed": "wrap"},
            "block_scale_rounding": {"fixed": "nearest"},
            "block_element_overflow": {"fixed": "saturate"},
            "sr_compare": {"fixed": "gt"}, "check_flags": {"fixed": False},
            "check_sr": {"fixed": True},
            "verify.n_random": {"fixed": 200}, "verify.seed": {"fixed": 7},
            "verify.n_random_masks": {"fixed": 300},
            "clock_ps": {"fixed": 3000},
            "core.family": {"fixed": "unit_per_class"},
            "core.*": {"search": "all"},
            "core.adder.*.family": {"search": ["ripple_carry", "parallel_prefix", "carry_lookahead"]},
            "checker.family": {"fixed": "residue"},
            "checker.modulus": {"fixed": 15},
            "checker.generator_style": {"fixed": "csa_tree"},
            "checker.comparator.family": {"fixed": "direct_compare"},
        },
        "artifacts": {
            "core": {"role": "seed", "kind": "text", "source": "generated", "language": "systemverilog",
                     "indexed_by": "rtl_members", "declaration_member": "top",
                     "evolve": ["alu_core", "alu_core_u_*"]},
            "checker": {"role": "fixed", "kind": "text", "source": "generated",
                        "language": "systemverilog"},
            "verify_bundle": {"role": "fixed", "kind": "text", "source": "generated",
                              "indexed_by": "verify_files"},
        },
        "evaluate": {
            "nodes": {
                "declaration": {"node": "adir.declaration"},
                "lint": {"node": "chialu.eda.lint", "inputs": {"rtl_text": "candidate.core"}},
                "conformance": {"node": "chialu.eda.conformance",
                                "inputs": {"rtl_text": "candidate.core", "files": "artifacts.verify_bundle"}},
                "fault": {"node": "chialu.eda.fault",
                          "inputs": {"rtl_text": "candidate.core", "files": "artifacts.verify_bundle",
                                     "checker_rtl": "artifacts.checker"}},
                "synth_ppa": {"node": "chialu.eda.synth_ppa",
                              "inputs": {"rtl_text": "candidate.core", "top": "alu_core", "pdk": "nangate45",
                                         "clock_ps": "vars.clock_ps", "effort": "medium", "timeout_s": scaled(600)},
                              "when": ["conformance.pass"]},
            },
            "feedback": ["conformance.detail", "fault.detail", "synth_ppa.detail"],
        },
        "constraints": [
            {"metric": "declaration.ok", "eq": True, "hard": True},
            {"metric": "lint.ok", "eq": True, "hard": True},
            {"metric": "conformance.pass", "eq": True, "hard": True},
            {"metric": "fault.pass", "eq": True, "hard": True},
            {"metric": "synth_ppa.abc_delay_ps", "le": "vars.clock_ps"},
        ],
        "goal": {"pareto": [{"minimize": "synth_ppa.area_um2"}, {"minimize": "synth_ppa.abc_delay_ps"}],
                 "score": {"rule": "ratio_to_seed", "infeasible": "slack"}},
        "knowledge": str(REPO_ROOT / "chialu" / "knowledge"),
        "search": {"backend": "adaevolve", "iterations": 1,
                   "seeds": {"generated": ["baseline", "packed_banks", "per_position", "dedicated_speed"]},
                   "prompts": {"variants": {"operator": ["structural", "local"], "member_focus": ["one"]},
                               "sources": ["chialu_interface", "chialu_families", "chialu_structures", "chialu_timing"]},
                   "models": {"solution": {"agent": "claude", "model": "claude-opus-5"}}},
        "archive": {"store": "jsonl", "path": "results_db.jsonl"},
    },
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-eda", action="store_true", help="bind and render the seeds only")
    ap.add_argument("--work")
    args = ap.parse_args(argv)
    from adir.cli import do_check, do_seeds
    from adir.instance import load
    from adir.seeds import seed_programs
    from adir.nodes import Executor
    work = Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix="chialu_domain_"))
    work.mkdir(parents=True, exist_ok=True)
    path = work / "run.yaml"
    path.write_text(yaml.safe_dump(RUN, sort_keys=False))
    fails = []

    def check(name, cond, detail=""):
        print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f": {detail}" if detail and not cond else ""))
        if not cond:
            fails.append(name)

    inst = load(path, run_dir_override=str(work / "run"))
    searched = [v.name for v in inst.searched()]
    check("bound through adir", len(inst.bindings) > 40, f"{len(inst.bindings)} bindings")
    check("structure-indexed adder families", any(n.startswith("core.adder.m") and n.endswith(".family")
                                                   for n in searched))
    check("the adder family domain is the narrowed list",
          inst.bindings[next(n for n in searched if n.startswith("core.adder.m") and n.endswith(".family"))]
          .domain.members() == ["ripple_carry", "parallel_prefix", "carry_lookahead"])
    check("the checker modulus is fixed", inst.bindings["checker.modulus"].value == 15)
    check("the seed artifact has a module", "module alu_core" in inst.artifacts["core"].text)
    check("the checker is generated", "module alu_checker" in inst.artifacts["checker"].text)
    files = inst.artifacts["verify_bundle"].texts
    check("verify files", {"tb.sv", "vectors.hex", "expected.hex", "fault_tb.sv", "masks.hex", "spec.json"}
          <= set(files), sorted(files))
    do_check(inst, work / "run", quiet=True)
    # a plan the discover role could have proposed: the two int8 adders as one prefix adder
    plan = {"shared": {"add8": {"members": ["m1.*.adder"], "family": "parallel_prefix",
                                "pin": {"topology": "kogge_stone"}, "why": "one 16-bit prefix adder for both lanes"}},
            "why": "sharing across the int8 lanes"}
    # a second plan that absorbs the comparators into the adders (the discover role proposes such groups)
    plan2 = {"shared": {"add_cmp8": {"members": ["m1.*.adder", "m1.*.comparator"], "family": "parallel_prefix",
                                     "why": "min rides the adder's subtractor"}}, "why": "comparator-in-adder sharing"}
    (work / "run" / "discovered.json").write_text(json.dumps({"plans": {"add8_plan": plan, "add_cmp8_plan": plan2}}))
    try:
        text, pvars, plines = inst.template.plan_seed(inst.ctx(), "add8_plan", plan)
        text = "\n".join(text.values()) if isinstance(text, dict) else text      # the multi-file core's members
        check("plan_seed renders the plan", "module alu_core_u_add8" in text
              and pvars.get("core.adder.m1.family") == "parallel_prefix"
              and pvars.get("core.adder.m1.topology") == "kogge_stone"
              and sum(1 for k, t in plines if "group=add8" in " ".join(t)) == 2,
              f"{sorted(pvars)} {[t for k, t in plines if 'group=' in ' '.join(t)][:2]}")
    except Exception as e:  # noqa: BLE001
        check("plan_seed renders the plan", False, f"{type(e).__name__}: {e}")
    programs = seed_programs(inst, work / "run")
    check("four seeds and the plans", [n for n, _ in programs] == ["baseline", "packed_banks", "per_position",
                                                                     "dedicated_speed", "add8_plan", "add_cmp8_plan"],
          str([n for n, _ in programs]))
    from adir.declaration import parse_block
    for name, prog in programs:
        d = parse_block(prog)
        missing = [n for n in d.vars if inst.bindings.get(n) is None or inst.bindings.get(n).time != "search"]
        check(f"seed {name} declares only searched variables", not missing, str(missing[:5]))
        structs = [t for k, t in d.lines if k == "STRUCTURE"]
        check(f"seed {name} declares its structures", len(structs) == len(inst.elaboration.info["manifest"]),
              f"{len(structs)} of {len(inst.elaboration.info['manifest'])}")
        check(f"seed {name} keeps the block inside the mutable region",
              prog.index("EVOLVE-BLOCK-START") < prog.index("ADIR-DECL v1"))
    grouped = [t for k, t in parse_block(programs[1][1]).lines if k == "STRUCTURE" and any(x.startswith("group=") for x in t)]
    check("packed_banks groups structures", len(grouped) > 0)
    tools = all(shutil.which(t) for t in ("verilator", "yosys"))
    if args.no_eda or not tools:
        print(f"  skip EDA ({'requested' if args.no_eda else 'verilator/yosys not all on PATH'})")
    else:
        recs = do_seeds(inst, work / "run", quiet=True)
        for r in recs:
            check(f"seed {r['seed_name']} passes the gates", r["feasible"] and not r["hard_fail"],
                  (r.get("stderr") or "")[:300])
            area = (r["measurements"].get("synth_ppa") or {}).get("value", {}).get("area_um2")
            check(f"seed {r['seed_name']} has an area", area is not None and area > 0, str(area))
        check("the first seed scores 1.0", abs(recs[0]["score"]["combined_score"] - 1.0) < 1e-9,
              str(recs[0]["score"]))
        system = (work / "run" / "problem.md").read_text()
        sample = (work / "run" / "prompt_sample.md").read_text()
        check("the system text is compact", len(system) < 60000, f"{len(system)} chars")
        check("the system text carries the family menu", "## Families per structure kind" in system)
        check("the sample prompt is compact", len(sample) < 40000, f"{len(sample)} chars")
        check("the sample prompt names the program file", "The program is the file `" in sample)
        # the per-round sources are files of the call directory now, indexed in the prompt
        calls = sorted((work / "run" / "agent").glob("*/context/chialu_structures.md"),
                       key=lambda f: f.stat().st_mtime) if (work / "run" / "agent").is_dir() else []
        check("the sample prompt indexes the structure table", "`context/chialu_structures.md`" in sample)
        check("the structure table has a region in focus",
              bool(calls) and "### In focus: `" in calls[-1].read_text(),
              f"{len(calls)} call directories with a structure table")
        for pname in ("add8_plan", "add_cmp8_plan"):
            plan_rec = next((r for r in recs if r["seed_name"] == pname), None)
            check(f"the discovered plan {pname} passes the gates", bool(plan_rec) and plan_rec["feasible"],
                  str((plan_rec or {}).get("stderr") or (plan_rec or {}).get("feedback", {}).get("conformance.detail", "no record"))[:300])
        # a replan: the parent (baseline) with the two int8 adders regrouped in its STRUCTURE lines
        from adir.evaluate import replan_program, candidate_from_program, evaluate_candidate
        base = recs[0]
        base_program = (work / "run" / "programs" / "seed_baseline.sv").read_text()
        regrouped = "\n".join(
            (l + " group=add8") if l.startswith("// STRUCTURE m1.l0.adder ") or l.startswith("// STRUCTURE m1.l1.adder ") else l
            for l in base_program.splitlines())
        new = replan_program(inst, regrouped, base, base_program)
        check("a regrouping re-renders the seed", new is not None and "module alu_core_u_add8" in new
              and "module alu_core_u_m1_l0_adder" not in new, (new or "")[:0])
        if new:
            cand = candidate_from_program(inst, new, iteration=1, parent_id=base["candidate_id"],
                                          meta={"replanned": True})     # as the entry marks a re-rendered program
            rec = evaluate_candidate(inst, work / "run", cand, seed_values={}, archive=None,
                                     executor=Executor(work / "run" / "cache"), seed_programs=[p for _, p in programs])
            check("the replanned candidate passes the gates", rec["feasible"] and not rec["hard_fail"],
                  str(rec.get("stderr"))[:300])
        check("no seed declares more than 16 lines",
              all(len((r["declarations"] or {}).get("vars") or {}) <= 16 for r in recs),
              str([len((r["declarations"] or {}).get("vars") or {}) for r in recs]))
        summary = {r["seed_name"]: {"area": (r["measurements"].get("synth_ppa") or {}).get("value", {}).get("area_um2"),
                                    "delay": (r["measurements"].get("synth_ppa") or {}).get("value", {}).get("abc_delay_ps"),
                                    "score": r["score"]["combined_score"]} for r in recs}
        print("  " + json.dumps(summary))
    print(f"[domain_selftest] {'all pass' if not fails else f'{len(fails)} failures: {fails}'} ({work})")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
