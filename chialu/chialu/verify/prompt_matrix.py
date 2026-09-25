"""Prompt sampling over a matrix of ALU run files (the prompt counterpart
of alu_matrix): every unit is bound through ADIR, its seeds (and, with a
discover model, the discovered plans) run through the graph in ADIR's
local executor, a few candidates with random declaration blocks, a
regrouped plan, a bad VAR and an edit outside the regions are evaluated
as further parents, and prompts are composed under random combinations
of every composer knob, the diff mode, the context and the backend's
notes, then checked line by line against the instance.

    python3 -m chialu.verify.prompt_matrix [--work DIR] [--out DIR] [--only a,b] [--per-unit 40]
        [--discover N --agent opencode --model <model>] [--review <agent>[:<model>]] [--no-eda] [--seed 0]

The report (stdout and <out>/report.md) lists per unit the seeds, the
parents, the prompts sampled and every check that failed, with the
prompt file and the offending line.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = REPO_ROOT / "chialu" / "knowledge"

CONV = {"nan_payload": "canonical", "invalid_result": "saturate", "nan_to_int": "zero",
        "minmax_nan": "propagate", "tininess": "after", "int_div_zero": "riscv", "zero_sign": "positive",
        "quire_overflow": "wrap", "block_scale_rounding": "nearest", "block_element_overflow": "saturate",
        "sr_compare": "gt", "check_flags": False}
BASE_VARS = {"accuracy": "exact", "rounding": "RNE", "daz_in": False, "ftz_out": False, "unary_dual": False,
             "flags": [], "sr_bits": 8, "check_sr": True, **CONV,
             "verify.n_random": 120, "verify.seed": 11, "verify.n_random_masks": 1500,
             "clock_ps": 3000, "core.family": "unit_per_class", "checker.family": "residue", "checker.modulus": 15,
             "checker.comparator.family": "direct_compare"}

# name -> (the task line, the variable bindings that depart from BASE_VARS; a plain value is `fixed`,
# {"runtime": [...]} / {"search": ...} as written). A unit's clock_ps sits a tenth above its
# baseline seed's synthesized delay, so the delay constraint is meaningful per unit.
MATRIX = {
    "int_full": ("Every integer op on a 16-bit datapath with int16, unsigned and 2 x int8 modes; area under the delay bound.", {
        "modes": {"runtime": [{"count": 1, "format": "int16"}, {"count": 1, "format": "uint16"}, {"count": 2, "format": "int8"}]},
        "ops": {"runtime": ["add", "sub", "adc", "sbb", "neg", "abs", "add_sat", "sub_sat", "mul", "mul_wide", "mul_high",
                            "mul_sat", "min", "max", "cmp", "shl", "shr_logical", "shr_arith", "rol", "ror",
                            "and", "or", "xor", "not", "popcount", "clz", "ctz"]},
        "check_en": True, "unary_dual": {"runtime": [False, True]}, "flags": ["carry", "int_overflow"],
        "core.*": {"search": "all"},
        "core.adder.m0": {"preset": "kogge_stone1973_prefix"}}),
    "int_div": ("An integer ALU with division on int16 and 2 x int8 modes; the core partitioning and the checker are searched.", {
        "clock_ps": 20000,
        "modes": {"runtime": [{"count": 1, "format": "int16"}, {"count": 2, "format": "int8"}]},
        "ops": {"runtime": ["add", "sub", "mul", "div", "quot", "rem", "mod", "min"]},
        "quotient_semantics": {"runtime": ["truncate_zero", "floor"]},
        "check_en": {"runtime": [False, True]}, "checker.family": "duplication", "core.family": {"search": "all"},
        "core.*": {"search": "all"}}),
    "float_ieee": ("An IEEE float ALU over fp16, bf16 and 2 x fp8e5m2 with every rounding mode and the flags; the checker duplicates the flags.", {
        "clock_ps": 50000,
        "modes": {"runtime": [{"count": 1, "format": "fp16"}, {"count": 1, "format": "bf16"}, {"count": 2, "format": "fp8e5m2"}]},
        "ops": {"runtime": ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp", "fmin", "fmax", "fabs", "fneg"]},
        "rounding": {"runtime": ["RNE", "RTZ", "RDN", "RUP", "SR"]}, "daz_in": {"runtime": [False, True]},
        "ftz_out": {"runtime": [False, True]}, "sr_bits": 10, "check_sr": {"runtime": [False, True]},
        "flags": ["invalid", "div_zero", "overflow", "underflow", "inexact", "nan", "denormal", "unordered"],
        "check_flags": True, "check_en": True, "checker.family": "inverse_residue",
        "core.*": {"search": "all"}}),
    "mixed_cvt": ("A subword ALU over fp16, int16, 2 x int8 and a fixed-point mode with conversions among them.", {
        "clock_ps": 14000,
        "modes": {"runtime": [{"count": 1, "format": "fp16"}, {"count": 1, "format": "int16"}, {"count": 2, "format": "int8"},
                              {"count": 1, "format": "fxs1i7f8"}]},
        "ops": {"runtime": ["add", "mul", "min", "fadd", "fmul", "cvt(int8)", "cvt(fp16)", "cvt(fxs1i7f8)"]},
        "check_en": True, "checker.family": "multi_residue", "checker.moduli_count": 2, "core.*": {"search": "all"},
        "core.subword.family": {"search": ["partitioned_carry_chain", "replicated_lanes"]}}),
    "approx": ("An approximate int16 adder and multiplier under a mean relative error budget; no checker.", {
        "modes": {"runtime": [{"count": 1, "format": "int16"}, {"count": 2, "format": "int8"}]},
        "ops": {"runtime": ["add", "mul", "mul_wide"]},
        "accuracy": "approximate", "error_budget": {"mred": 0.02, "error_rate": 0.6},
        "accuracy_ctl": "static", "check_en": False,
        "core.*": {"search": "all"}}),
    "block_mx": ("A block-format ALU: one MXFP4 block of 8 elements or 8 fp8e4m3 values, elementwise add and mul and the conversions between them.", {
        "clock_ps": 16000,
        "modes": {"runtime": [{"count": 1, "format": "blksfps0e8m0Nefp4e2m1s8"}, {"count": 8, "format": "fp8e4m3"}]},
        "ops": {"runtime": ["fadd", "fmul", "cvt(blksfps0e8m0Nefp4e2m1s8)", "cvt(fp8e4m3)"]},
        "ftz_out": {"runtime": [False, True]}, "check_en": True, "checker.modulus": 31,
        "core.*": {"search": "all"}}),
    "posit_bcd_ones": ("A posit16 mode beside a BCD mode, a ones' complement and a sign-magnitude mode; the zero sign is preserved.", {
        "clock_ps": 32000,
        "modes": {"runtime": [{"count": 1, "format": "posit16_1"}, {"count": 1, "format": "bcd3"},
                              {"count": 1, "format": "int8_ones"}, {"count": 1, "format": "int8_sm"}]},
        "ops": {"runtime": ["add", "sub", "mul_wide", "min", "fadd", "fmul", "fmin", "cvt(int12)"]},
        "zero_sign": "preserve", "invalid_result": "zero", "check_en": True, "checker.family": "berger",
        "core.*": {"search": "all"}}),
    "wide_fp": ("An fp32 and 2 x fp16 float ALU with add, mul, compare, min and max; the fp adder families are narrowed.", {
        "clock_ps": 21000,
        "modes": {"runtime": [{"count": 1, "format": "fp32"}, {"count": 2, "format": "fp16"}]},
        "ops": {"runtime": ["fadd", "fmul", "fmin", "fmax", "fcmp"]},
        "check_en": True, "core.*": {"search": "all"},
        "core.fp_adder.*.family": {"search": ["single_path", "two_path"]}}),
    "x87_dual": ("An fp80 and fp64 ALU with add, sub, compare, min, max and the dual unary ops.", {
        "clock_ps": 60000,
        "modes": {"runtime": [{"count": 1, "format": "fp80"}, {"count": 1, "format": "fp64"}]},
        "ops": {"runtime": ["fadd", "fsub", "fcmp", "fmin", "fmax", "fabs", "fneg"]},
        "unary_dual": True, "check_en": True, "checker.family": "duplication", "verify.n_random": 60,
        "core.*": {"search": "all"}}),
    "sr_fixed": ("An unsigned and fixed-point ALU under stochastic rounding with a switchable checker that accepts the one-ulp window.", {
        "clock_ps": 44000,
        "modes": {"runtime": [{"count": 1, "format": "uint16"}, {"count": 1, "format": "fxs0i8f8"}, {"count": 2, "format": "fxs1i3f4"}]},
        "ops": {"runtime": ["add", "sub", "mul", "div", "shl", "shr_logical", "popcount", "cvt(uint16)"]},
        "rounding": {"runtime": ["RNE", "SR"]}, "check_sr": False, "sr_bits": 8,
        "check_en": {"runtime": [False, True]}, "checker.family": "parity_prediction_adder",
        "core.*": {"search": "all"}}),
}

KNOB_VALUES = {"operator": ["structural", "local", "free"],
               "show": ["path", "declarations_metrics", "declarations_only", "full"],
               "context_programs": [0, 1, 2, 3],
               "feedback_depth": ["none", "summary", "full"],
               "member_focus": ["none", "one", "all"],
               "show_plan_table": [True, False],
               "knowledge_depth": ["path", "index", "cards"],
               "decisions": ["kinds", "families", "choices"]}


def run_file(name: str, task: str, over: dict, work: Path, args) -> dict:
    """The run record of one unit of the matrix."""
    v = dict(BASE_VARS)
    v.update(over)
    checked = v.get("check_en") not in (False, {"runtime": [False]})
    approx = v.get("accuracy") == "approximate"
    variables = {}
    for k, val in v.items():
        if isinstance(val, dict) and set(val) & {"runtime", "search", "fixed", "preset"}:
            variables[k] = val
        else:
            variables[k] = {"fixed": val}
    if approx or not checked:
        for k in ("checker.family", "checker.modulus", "checker.moduli_count", "checker.comparator.family",
                  "verify.n_random_masks"):
            variables.pop(k, None)
    elif v.get("checker.family", "residue") not in ("residue", "inverse_residue"):
        variables.pop("checker.modulus", None)
    if approx:
        variables["check_en"] = {"fixed": False}
    if any(op in ("div", "quot", "rem", "mod") for op in (v.get("ops") or {}).get("runtime", [])) \
            and "quotient_semantics" not in variables:
        variables["quotient_semantics"] = {"fixed": "truncate_zero"}
    nodes = {
        "declaration": {"node": "adir.declaration"},
        "lint": {"node": "chialu.eda.lint", "inputs": {"rtl_text": "candidate.core"}},
        "conformance": {"node": "chialu.eda.conformance",
                        "inputs": {"rtl_text": "candidate.core", "files": "artifacts.verify_bundle"}},
        "yosys_stat": {"node": "chialu.eda.yosys_stat", "inputs": {"rtl_text": "candidate.core", "top": "alu_core"}},
        "synth_unit": {"node": "chialu.eda.synth_unit",
                       "inputs": {"rtl_text": "candidate.core", "structures": "decl.STRUCTURE", "pdk": "nangate45",
                                  "clock_ps": "vars.clock_ps", "effort": "low", "timeout_s": 900},
                       "when": ["conformance.pass", "yosys_stat.cells le 2.0 * seed.yosys_stat.cells"]},
        "synth_ppa": {"node": "chialu.eda.synth_ppa",
                      "inputs": {"rtl_text": "candidate.core", "top": "alu_core", "pdk": "nangate45",
                                 "clock_ps": "vars.clock_ps", "effort": "low", "timeout_s": 900},
                      "when": ["conformance.pass", "synth_unit.area_um2 le 1.2 * seed.synth_unit.area_um2"]},
    }
    feedback = ["conformance.detail", "synth_unit.attribution", "synth_ppa.detail"]
    constraints = [{"metric": "declaration.ok", "eq": True, "hard": True},
                   {"metric": "lint.ok", "eq": True, "hard": True}]
    if not approx:
        constraints.append({"metric": "conformance.pass", "eq": True, "hard": True})
    artifacts = {"core": {"role": "seed", "kind": "text", "source": "generated", "language": "systemverilog",
                          "evolve": ["alu_core", "alu_core_u_*"]},
                 "verify_bundle": {"role": "fixed", "kind": "text", "source": "generated", "indexed_by": "verify_files"}}
    if checked and not approx:
        nodes["fault"] = {"node": "chialu.eda.fault",
                          "inputs": {"rtl_text": "candidate.core", "files": "artifacts.verify_bundle",
                                     "checker_rtl": "artifacts.checker"}}
        feedback.insert(1, "fault.detail")
        constraints += [{"metric": "fault.pass", "eq": True, "hard": True},
                        {"metric": "fault.alias_rate", "le": 0.09, "hard": True}]
        artifacts["checker"] = {"role": "fixed", "kind": "text", "source": "generated", "language": "systemverilog"}
    # a delay past the target is infeasible (kept with its measurements); the front stands under the target
    constraints.append({"metric": "synth_ppa.abc_delay_ps", "le": "vars.clock_ps"})
    if approx:
        # the requirement `accuracy: approximate` opens: the budget the conformance judge applies
        constraints.append({"metric": "conformance.pass", "eq": True, "hard": True, "satisfies": "error_bound"})
    search = {"backend": "adaevolve", "iterations": 1, "diff_mode": True,
              "seeds": {"generated": ["baseline", "packed_banks", "per_position", "dedicated_speed"]},
              "context": {"programs": 1, "show": "path"},
              "prompts": {"variants": {"operator": ["structural", "local", "free"], "member_focus": ["none", "one"],
                                       "feedback_depth": ["summary", "full"]},
                          "sample": "ucb", "sources": ["chialu_interface", "chialu_families", "chialu_structures", "chialu_timing"],
                          "log": False},
              "tactics": {"sources": ["target", "worst_constraint"], "select": "ucb"},
              "instructions": {"enabled": True, "slot": "guidance",
                               "seed": "Prefer a change that shortens the critical path of the region in focus.",
                               "select": "ucb"},
              "models": {"solution": {"agent": args.agent, "model": args.model},
                         "strategy": {"agent": args.agent, "model": args.model}}}
    if args.discover:
        search["seeds"]["discover"] = int(args.discover)
        search["models"]["discover"] = {"agent": args.agent, "model": args.model, "timeout_s": 1800}
    if getattr(args, "review", None):
        ragent, _, rmodel = args.review.partition(":")
        nodes["review"] = {"node": f"chialu.review.{ragent}",
                           "inputs": {"rtl_text": "candidate.core", "structures": "decl.STRUCTURE",
                                      **({"model": f"'{rmodel}'"} if rmodel else {})},
                           "when": ["conformance.pass"]}
        feedback.append("review.detail")
        constraints.append({"metric": "review.agree", "ge": 1.0})
    (work / "task.md").write_text(f"# {name}\n\n{task}\n")
    rec = {"adir": {"module": "chialu.ALU", "run_dir": str(work / "run"),
                    "variables": variables, "artifacts": artifacts,
                    "evaluate": {"nodes": nodes, "feedback": feedback},
                    "constraints": constraints,
                    "goal": {"pareto": [{"minimize": "synth_ppa.area_um2"}, {"minimize": "synth_ppa.abc_delay_ps"}],
                             "score": {"rule": "ratio_to_seed", "infeasible": "slack"}},
                    "knowledge": str(KNOWLEDGE), "task": {"context": "task.md"},
                    "search": search, "archive": {"store": "jsonl", "path": "results_db.jsonl"}}}
    if args.discover and name == "mixed_cvt":
        rec["adir"]["task"]["author"] = "discover"
    return rec


# ---------------------------------------------------------------- parents

def _replace_block(program: str, vars_: dict, lines: list) -> str:
    """The program with its declaration block replaced, the block's
    comment prefix (`// ` in SystemVerilog) kept."""
    from adir.declaration import MARK_END, MARK_START, render_block
    i = program.index(MARK_START)
    j = program.index(MARK_END, i) + len(MARK_END)
    prefix = program[program.rfind("\n", 0, i) + 1:i]
    return program[:i - len(prefix)] + render_block(vars_, lines, prefix).strip() + program[j:]


def _group_families(inst, vars_: dict, parent_vars: dict, lines: list) -> dict:
    """A random family on one member of a group applied to the group's other
    members (one datapath has one family), their old choices dropped."""
    from chialu.lines import parse_structure
    from chialu.prompts import var_prefix
    manifest = {s["id"]: s for s in (inst.elaboration.info or {}).get("manifest") or []}
    groups: dict = {}
    for kind, tokens in lines:
        if kind != "STRUCTURE":
            continue
        try:
            e = parse_structure(list(tokens))
        except ValueError:
            continue
        sid = e["_"][0] if isinstance(e.get("_"), list) and e["_"] else None
        if sid in manifest and e.get("group"):
            groups.setdefault(e["group"], []).append(sid)
    out = dict(vars_)
    for members in groups.values():
        prefixes = [var_prefix(manifest[m]) for m in members]
        changed = [p for p in prefixes if out.get(p + "family") is not None and out.get(p + "family") != parent_vars.get(p + "family")]
        if not changed:
            continue
        fam = out[changed[0] + "family"]
        for p in prefixes:
            if out.get(p + "family") == fam:
                continue
            for name in [n for n in out if n.startswith(p)]:
                out.pop(name)
            b = inst.bindings.get(p + "family")
            if b is not None and b.time == "search" and fam in b.domain.members():
                out[p + "family"] = fam
    return out


def random_declaration(inst, rng: random.Random, parent_vars: dict, n_structures: int = 2) -> dict:
    """Random VAR values of a few structures: a family from its domain and
    the choices that family opens, plus a unit-level slot family."""
    from chialu.prompts import var_prefix
    manifest = (inst.elaboration.info or {}).get("manifest") or []
    out = dict(parent_vars)
    slotted = [s for s in manifest if s.get("slot")]
    for s in rng.sample(slotted, min(n_structures, len(slotted))):
        prefix = var_prefix(s)
        fb = inst.bindings.get(prefix + "family")
        if fb is None or fb.time != "search":
            continue
        fam = rng.choice(fb.domain.members())
        # the parent's choices under this structure belong to its old family
        for name in [n for n in out if n.startswith(prefix)]:
            out.pop(name)
        out[prefix + "family"] = fam
        for child in inst.tree.children_of(prefix + "family"):
            if not child.condition_holds(fam) or "." in child.name[len(prefix):]:
                continue        # a nested slot's variable: left at its default
            b = inst.bindings.get(child.name)
            if b is None or b.time != "search":
                continue
            if rng.random() < 0.5:
                out[child.name] = b.domain.sample(rng) if not b.domain.finite() else rng.choice(b.domain.members())
    for name in ("core.subword.family", "checker.generator_style", "checker.granularity"):
        b = inst.bindings.get(name)
        if b is not None and b.time == "search" and rng.random() < 0.5:
            out[name] = rng.choice(b.domain.members())
    return out


def make_parents(inst, run: Path, recs: list, rng: random.Random, log) -> list:
    """Further evaluated parents beyond the seeds: candidates with random
    declarations (one with a MOVE line), a regrouped plan, a VAR outside
    its domain, and an edit outside the mutable regions."""
    from adir.declaration import parse_block
    from adir.evaluate import candidate_from_program, evaluate_candidate, load_seed_values, replan_program
    from adir.nodes import Executor
    archive = inst.archive(run)
    seed_values = load_seed_values(run)
    executor = Executor(run / "cache")
    programs = {r["candidate_id"]: (run / "programs" / f"{r['candidate_id'].replace(':', '_')}.sv").read_text()
                for r in recs}
    seed_texts = list(programs.values())
    out = []

    def evaluate(cid, text, parent, replanned=False):
        # as the evaluate entry does: the template's replan hook re-renders a program whose
        # declaration regroups structures or changes a family the library realizes
        if not replanned and getattr(inst.template, "replan", None) is not None:
            new = replan_program(inst, text, parent, programs.get(parent["candidate_id"]))
            if new is not None:
                text, replanned = new, True
        cand = candidate_from_program(inst, text, iteration=1, parent_id=parent["candidate_id"],
                                      meta={"candidate_id": cid, **({"replanned": True} if replanned else {})})
        rec = evaluate_candidate(inst, run, cand, seed_values=seed_values, archive=archive, executor=executor,
                                 seed_programs=seed_texts, parent_program=programs.get(parent["candidate_id"]))
        from adir.composer import save_program
        save_program(run, rec["candidate_id"], ".sv", text)
        out.append(rec)
        log(f"  parent {cid}: {'feasible' if rec['feasible'] else 'infeasible'}"
            f"{' (hard failure)' if rec['hard_fail'] else ''}, score {rec['score']['combined_score']:.3f}"
            + (f"; {str(rec.get('stderr'))[:120]}" if rec.get("stderr") else ""))
        return rec

    for i in range(3):
        parent = rng.choice(recs)
        d = parse_block(programs[parent["candidate_id"]])
        vars_ = random_declaration(inst, rng, d.vars, n_structures=rng.choice([1, 2, 3]))
        lines = list(d.lines)
        vars_ = _group_families(inst, vars_, d.vars, lines)
        if i == 0:
            lines.append(("MOVE", ["abs_by_sign_mask", "region=alu_core"]))
        evaluate(f"cand:declared{i}", _replace_block(programs[parent["candidate_id"]], vars_, lines), parent)
    # a regrouping: the first two structures of one kind share a datapath
    base = recs[0]
    text = programs[base["candidate_id"]]
    d = parse_block(text)
    by_kind: dict = {}
    for k, t in d.lines:
        if k == "STRUCTURE" and not any(x.startswith("group=") for x in t):
            kind = next((x[5:] for x in t if x.startswith("kind=")), "")
            slot = next((x[5:] for x in t if x.startswith("slot=")), "-")
            if slot != "-":
                by_kind.setdefault(kind, []).append(t[0])
    pair = next((ids[:2] for ids in by_kind.values() if len(ids) >= 2), None)
    if pair:
        lines = [(k, t + ["group=shared_pair"] if k == "STRUCTURE" and t[0] in pair else t) for k, t in d.lines]
        regrouped = _replace_block(text, d.vars, lines)
        try:
            new = replan_program(inst, regrouped, base, text)
        except Exception as e:  # noqa: BLE001
            new = None
            log(f"  replan raised {type(e).__name__}: {e}")
        if new:
            evaluate("cand:regrouped", new, base, replanned=True)
    # a VAR outside its domain
    fam = next((n for n in d.vars) if d.vars else (n for n, b in list(inst.bindings.items())
                                                    if b.time == "search" and n.endswith(".family")), None)
    if fam is None:
        fam = next(n for n, b in list(inst.bindings.items()) if b.time == "search" and n.endswith(".family"))
    evaluate("cand:badvar", _replace_block(text, {**d.vars, fam: "no_such_family"}, list(d.lines)), base)
    # an edit outside the regions
    k = text.rfind("endmodule")
    evaluate("cand:outside", text[:k] + "  logic stray;\nendmodule" + text[k + len("endmodule"):], base)
    return out


# ---------------------------------------------------------------- sampling

FAKE_ATTEMPTS = ("Attempt 1 (score 0.980): a carry-select adder in m1.l0; conformance passed, area rose 4%.\n"
                 "Attempt 2 (score 0.000): a shared multiplier for the int8 lanes; the fault gate found a "
                 "false alarm.")
FAKE_FAILED = ("Previous Failed Attempts\n\nThe SEARCH block did not match the program: the module header "
               "had changed. Error: no match for SEARCH block 1.")
FAKE_BACKEND = ("## Paradigm\n\nThe current paradigm is sharing across lanes; a breakthrough would move "
                "the rounding into the reduction.\n\n## Sibling context\n\nTwo siblings of this parent "
                "changed the multiplier family; both passed conformance.")


def sample_prompts(inst, run: Path, out_dir: Path, n: int, rng: random.Random, log) -> list:
    from adir import composer
    archive = inst.archive(run)
    recs = [r for r in archive.records()]
    if not recs:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    samples = []
    orig = composer.choose_config
    try:
        for i in range(n):
            cfg = {k: rng.choice(v) for k, v in KNOB_VALUES.items()}
            composer.choose_config = lambda inst_, archive_, rng_, cfg=cfg: dict(cfg)
            inst.search["diff_mode"] = rng.random() < 0.7
            parent = rng.choice(recs)
            others = [r for r in recs if r is not parent]
            insp = rng.sample(others, min(len(others), rng.choice([0, 1, 2, 3])))
            att = rng.choice(["No previous attempts yet.", FAKE_ATTEMPTS])
            failed = FAKE_FAILED if rng.random() < 0.25 else ""
            tail = FAKE_BACKEND if rng.random() < 0.3 else ""
            fake = (f"{composer.MARK_CURRENT}\ncandidate_id: {parent['candidate_id']}\n{composer.MARK_INSPIRATIONS}\n"
                    + "\n".join(f"candidate_id: {r['candidate_id']}" for r in insp)
                    + (f"\n{failed}" if failed else "")
                    + f"\n{composer.MARK_ATTEMPTS}\n{att}\n{composer.MARK_END_BACKEND}\n{tail}")
            t0 = time.time()
            try:
                system, user, side = composer.compose(inst, run, fake, random.Random(rng.random()), archive)
            except Exception as e:  # noqa: BLE001
                log(f"  compose raised {type(e).__name__}: {e} under {cfg}")
                samples.append({"i": i, "cfg": cfg, "error": f"{type(e).__name__}: {e}", "parent": parent["candidate_id"]})
                continue
            meta = {"i": i, "cfg": cfg, "diff_mode": inst.search["diff_mode"], "parent": parent["candidate_id"],
                    "tactic_id": side.get("tactic_id"), "instruction_id": side.get("instruction_id"),
                    "inspirations": [r["candidate_id"] for r in insp], "attempts": att != "No previous attempts yet.",
                    "failed": bool(failed), "backend": bool(tail), "side": side,
                    "seconds": round(time.time() - t0, 2), "system_chars": len(system), "user_chars": len(user)}
            f = out_dir / f"{i:03d}.md"
            f.write_text(f"<!-- sample {json.dumps({k: v for k, v in meta.items() if k != 'side'}, default=str)} -->\n\n"
                         f"# System\n\n{system}\n\n# User\n\n{user}\n")
            meta["file"] = str(f)
            meta["system"], meta["user"] = system, user
            samples.append(meta)
    finally:
        composer.choose_config = orig
    return samples


# ---------------------------------------------------------------- checks

def check_prompt(inst, run: Path, s: dict) -> list:
    """The problems of one sample: (check name, detail)."""
    from chialu.prompts import family_domain, manifest_of, var_prefix
    problems = []
    if "error" in s:
        return [("compose_error", s["error"])]
    system, user, cfg = s["system"], s["user"], s["cfg"]
    both = system + "\n" + user

    def add(name, detail):
        problems.append((name, detail[:200]))

    for pat, name in (("(source ", "source_failed"), ("convention option (spec section 3.9)", "stale_convention_doc"),
                      ("* interface:", "interface_in_unit_slot"), ("... [arch/", "truncated_doc"),
                      ("## Tactic\n\nnone", "tactic_none")):
        if pat in both:
            add(name, pat)
    if system.count("## Interface") != 1:
        add("interface_count", str(system.count("## Interface")))
    for m in re.finditer(r"`?(arch/[A-Za-z0-9_./-]+\.md)`?", both):
        if not (KNOWLEDGE / m.group(1)).is_file():
            add("card_missing", m.group(1))
    for m in re.finditer(r"^## (.+)\n\n(?=## )", both, re.M):
        add("empty_section", m.group(1))
    for m in re.finditer(r"^(?!.*```).*\bNone\b.*$", both, re.M):
        add("literal_none", m.group(0).strip())
    if "nan" in both.split("## Response")[0].lower() and re.search(r"\bnan\b(?![-_a-z])", user):
        pass
    # the family menu against the bindings
    fam_sec = system.split("## Families per structure kind")[1].split("\n## ")[0] if "## Families per structure kind" in system else ""
    slot = None
    listed: dict = {}
    for line in fam_sec.splitlines():
        m = re.match(r"^\* `([a-z_]+)`:$", line)
        if m:
            slot = m.group(1)
            listed[slot] = []
            continue
        m = re.match(r"^    \* `([a-z_0-9]+)`", line)
        if m and slot:
            listed[slot].append(m.group(1))
    for slot_, fams in listed.items():
        dom = family_domain(inst, slot_)
        if dom is not None and fams != dom:
            add("menu_vs_domain", f"{slot_}: menu {fams} domain {dom}")
    # the decisions section against the menu
    dec_sec = system.split("## The decisions open to you")[1].split("\n## ")[0]
    for m in re.finditer(r"^\* `core\.([a-z_]+)(?:\.\*)?\.family`[^:]*: (.+)$", dec_sec, re.M):
        slot_, members = m.group(1), [x.strip() for x in m.group(2).split(".")[0].split(",")]
        if slot_ in listed and cfg["decisions"] == "kinds" and members != listed[slot_]:
            add("decisions_vs_menu", f"{slot_}: decisions {members} menu {listed[slot_]}")
    # the parent, the program, the focus
    archive = inst.archive(run)
    parent = next((r for r in archive.records() if r["candidate_id"] == s["parent"]), None)
    m = re.search(r"The program is the file `([^`]+)` \((\d+) lines", user)
    if cfg["show"] != "full":
        if not m:
            add("no_program_path", f"show: {cfg['show']} without a program path")
        elif not Path(m.group(1)).is_file():
            add("program_path_missing", m.group(1))
        else:
            n_lines = Path(m.group(1)).read_text().count("\n") + 1
            if n_lines != int(m.group(2)):
                add("program_line_count", f"{m.group(2)} vs {n_lines}")
    elif "The program:" not in user and parent is not None:
        add("no_program_text", "show: full without the program text")
    fm = re.search(r"The region in focus is `([^`]+)`(?:, lines (\d+)-(\d+) of the file)?", user)
    focus = fm.group(1) if fm else None
    if cfg["member_focus"] == "one" and parent is not None and not fm:
        add("no_focus", "member_focus one without a region in focus")
    if fm and fm.group(2) and m and Path(m.group(1)).is_file():
        lines = Path(m.group(1)).read_text().splitlines()
        lo, hi = int(fm.group(2)), int(fm.group(3))
        span = "\n".join(lines[lo - 1:hi])
        if f"module {focus}" not in span:
            add("focus_span", f"{focus} not within lines {lo}-{hi}")
    if focus and "### In focus: `" in user and f"### In focus: `{focus}`" not in user:
        add("focus_table", f"the structure table's focus differs from {focus}")
    if focus and parent is not None:
        prefixes = [var_prefix(x) for x in manifest_of(inst, parent) if x.get("sv") == focus]
        op_sec = user.split("## Operator")[1].split("\n## ")[0] if "## Operator" in user else ""
        for vm in re.finditer(r"^\* `(core\.[^`]+|checker\.[^`]+)`", op_sec, re.M):
            if not any(vm.group(1).startswith(p) for p in prefixes):
                add("structural_outside_focus", vm.group(1))
        tac = user.split("## Tactic")[1].split("\n## ")[0] if "## Tactic" in user else ""
        tv = re.search(r"`(core\.[^`]+|checker\.[^`]+)`: no candidate has tried", tac)
        if tv and not any(tv.group(1).startswith(p) for p in prefixes):
            add("tactic_outside_focus", tv.group(1))
    if cfg["operator"] == "local" and "no candidate has tried" in user.split("## Tactic")[1].split("\n## ")[0] if "## Tactic" in user else False:
        add("tactic_declares_under_local", "unexplored_values under local")
    if cfg["operator"] == "structural" and parent is not None and "Decisions of the parent" in user:
        op_sec = user.split("## Operator")[1].split("\n## ")[0]
        for vm in re.finditer(r"^\* `([^`]+)`: (.+)$", op_sec, re.M):
            name, rest = vm.group(1), vm.group(2)
            b = inst.bindings.get(name)
            if b is None or b.time != "search":
                add("structural_unknown_var", name)
                continue
            marks = rest.count("*") + rest.count("(default)")
            if marks != 1:
                add("structural_marks", f"{name}: {marks} marks")
            if b.domain.finite() and len(b.domain.members()) <= 32:
                shown = [x.replace("*", "").replace(" (default)", "").strip() for x in rest.split(", ")]
                if shown != [str(x) for x in b.domain.members()]:
                    add("structural_members", f"{name}: {shown[:4]} vs {[str(x) for x in b.domain.members()][:4]}")
    # the response format
    if s["diff_mode"] and "<<<<<<< SEARCH" not in user:
        add("response_diff", "diff_mode without SEARCH/REPLACE")
    if not s["diff_mode"] and "(the complete program)" not in user:
        add("response_full", "no diff_mode without the complete-program request")
    # knowledge depth
    if cfg["knowledge_depth"] == "cards" and "## Knowledge cards" not in user:
        add("no_cards", "knowledge_depth cards without cards")
    if cfg["knowledge_depth"] == "path" and "## Knowledge cards" in user:
        add("cards_under_path", "knowledge_depth path with cards")
    # the context programs
    n_ctx = len(re.findall(r"^### (seed:|cand:)", user, re.M))
    want = min(int(cfg["context_programs"]), len(s["inspirations"]))
    if n_ctx != want:
        add("context_count", f"{n_ctx} shown, {want} expected")
    if cfg["feedback_depth"] == "none" and "Feedback of its evaluation" in user:
        add("feedback_under_none", "")
    if cfg["show_plan_table"] is False and "## The structures of the seed" in user:
        add("plan_table_under_false", "")
    if s["attempts"] and "## History" not in user:
        add("no_history", "")
    if (s["failed"] or s["backend"]) and "## Notes from the search" not in user:
        add("no_backend_notes", "")
    if len(system) > 60000:
        add("system_size", str(len(system)))
    if len(user) > 40000:
        add("user_size", str(len(user)))
    # the seeds table: a "(defaults)" seed that differs in its lines says so
    for row in re.finditer(r"^\| `([^`]+)` \| \(defaults\) \| ([^|]+) \|", system, re.M):
        if row.group(1) != "baseline" and "differ" not in row.group(2) and "same" not in row.group(2):
            add("seed_row_lines", row.group(0)[:100])
    return problems


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work")
    ap.add_argument("--out")
    ap.add_argument("--only", help="comma-separated unit names")
    ap.add_argument("--per-unit", type=int, default=40)
    ap.add_argument("--discover", type=int, default=0, help="discovered plans per unit (needs the agent CLI)")
    ap.add_argument("--review", default=None, help="the declaration review node: <agent>[:<model>]")
    ap.add_argument("--agent", default="claude")
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--no-eda", action="store_true", help="bind and render only; no seeds, no prompts")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    from adir.cli import do_check, do_seeds
    from adir.instance import load
    work = Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix="chialu_prompts_"))
    out = Path(args.out) if args.out else work / "prompts"
    work.mkdir(parents=True, exist_ok=True)
    names = [n for n in MATRIX if not args.only or n in args.only.split(",")]
    tools = all(shutil.which(t) for t in ("verilator", "yosys"))
    report = [f"# prompt matrix ({len(names)} units, {args.per_unit} prompts each, seed {args.seed})", ""]
    log = lambda m: print(m, flush=True)  # noqa: E731
    totals: dict = {}
    for name in names:
        task, over = MATRIX[name]
        w = work / name
        w.mkdir(parents=True, exist_ok=True)
        rng = random.Random(f"{args.seed}:{name}")
        t0 = time.time()
        log(f"== {name}")
        try:
            path = w / "run.yaml"
            path.write_text(yaml.safe_dump(run_file(name, task, over, w, args), sort_keys=False))
            inst = load(path)
            run = Path(inst.run_dir)
            do_check(inst, run, quiet=True)
        except Exception as e:  # noqa: BLE001
            log(f"  bind failed: {type(e).__name__}: {e}")
            report += [f"## {name}", "", f"* bind failed: `{type(e).__name__}: {e}`", ""]
            continue
        n_search = len(inst.searched())
        log(f"  bound: {len(inst.bindings)} bindings, {n_search} searched, "
            f"{len(inst.elaboration.info.get('manifest') or [])} structures")
        if args.no_eda or not tools:
            report += [f"## {name}", "", f"* bound: {len(inst.bindings)} bindings, {n_search} searched; no EDA", ""]
            continue
        try:
            recs = do_seeds(inst, run, quiet=True)
        except Exception as e:  # noqa: BLE001
            log(f"  seeds failed: {type(e).__name__}: {e}")
            report += [f"## {name}", "", f"* seeds failed: `{type(e).__name__}: {e}`", ""]
            continue
        for r in recs:
            log(f"  seed {r['seed_name']}: {'feasible' if r['feasible'] else 'infeasible'}"
                f"{' (hard failure)' if r['hard_fail'] else ''}, goal {r['goal_values']}, "
                f"score {r['score']['combined_score']:.3f}" + (f"; {str(r.get('stderr'))[:120]}" if r.get("stderr") else ""))
        try:
            parents = make_parents(inst, run, recs, rng, log)
        except Exception as e:  # noqa: BLE001
            import traceback
            log(f"  parents failed: {type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}")
            parents = []
        samples = sample_prompts(inst, run, out / name, args.per_unit, rng, log)
        found: dict = {}
        for s in samples:
            for check, detail in check_prompt(inst, run, s):
                found.setdefault(check, []).append((s.get("file", f"sample {s['i']}"), detail))
        sizes_u = [s["user_chars"] for s in samples if "user_chars" in s]
        by_show: dict = {}
        for s in samples:
            if "user_chars" in s:
                by_show.setdefault(s["cfg"]["show"], []).append(s["user_chars"])
        sizes_s = [s["system_chars"] for s in samples if "system_chars" in s]
        secs = [s["seconds"] for s in samples if "seconds" in s]
        log(f"  {len(samples)} prompts; user chars median {statistics.median(sizes_u) if sizes_u else 0:.0f} "
            f"max {max(sizes_u) if sizes_u else 0}; system chars {min(sizes_s) if sizes_s else 0}-{max(sizes_s) if sizes_s else 0}; "
            f"compose {statistics.median(secs) if secs else 0:.2f} s median; "
            f"checks: {', '.join(f'{k} x{len(v)}' for k, v in sorted(found.items())) or 'clean'} ({time.time() - t0:.0f} s)")
        report += [f"## {name}", "",
                   f"* bound: {len(inst.bindings)} bindings, {n_search} searched, "
                   f"{len(inst.elaboration.info.get('manifest') or [])} structures",
                   "* seeds: " + ", ".join(f"`{r['seed_name']}` {'feasible' if r['feasible'] else 'infeasible'} "
                                          f"{r['score']['combined_score']:.3f}" for r in recs),
                   "* further parents: " + (", ".join(f"`{r['candidate_id']}` {'feasible' if r['feasible'] else 'infeasible'}"
                                                      + (' (hard failure)' if r['hard_fail'] else '') for r in parents) or "none"),
                   f"* prompts: {len(samples)}; user chars median {statistics.median(sizes_u) if sizes_u else 0:.0f}, "
                   f"max {max(sizes_u) if sizes_u else 0}; system chars {min(sizes_s) if sizes_s else 0} to {max(sizes_s) if sizes_s else 0}",
                   "* user chars by show: " + ", ".join(f"{k} {statistics.median(v):.0f} (max {max(v)})"
                                                        for k, v in sorted(by_show.items())),
                   ""]
        if found:
            report.append("| check | count | example file | example |")
            report.append("| --- | --- | --- | --- |")
            for k, v in sorted(found.items()):
                f, d = v[0]
                report.append(f"| {k} | {len(v)} | {Path(f).name} | {d.replace('|', '/')} |")
            report.append("")
        for k, v in found.items():
            totals[k] = totals.get(k, 0) + len(v)
    report += ["## Totals", "", *(f"* {k}: {n}" for k, n in sorted(totals.items())), "" if totals else "* every check clean", ""]
    out.mkdir(parents=True, exist_ok=True)
    # one report per invocation (several run side by side over disjoint units)
    (out / f"report_{'_'.join(names)}.md").write_text("\n".join(report))
    log("\n".join(report[-(len(totals) + 4):]))
    for name in names:
        d = out / name
        if d.is_dir():
            i = report.index(f"## {name}") if f"## {name}" in report else -1
            if i >= 0:
                j = next((k for k in range(i + 1, len(report)) if report[k].startswith("## ")), len(report))
                (d / "report.md").write_text("\n".join(report[i:j]))
    log(f"[prompt_matrix] prompts under {out}; work under {work}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
