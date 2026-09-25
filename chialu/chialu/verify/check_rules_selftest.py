"""The `check` rule table through ADIR (docs/checker-spec-plan.md).

A small int16 ALU binds a two-rule table (residue or multi-residue over
the arithmetic ops under a bound, the logic ops unchecked); the
elaboration's variables carry the feasible domains and no `checker.*`
variable; the checker artifact, the verify bundle and check_manifest.json
are generated; the seed passes conformance and the fault gate; the
`checker_gen` node regenerates the checker under a candidate's
declaration and the gate still passes; malformed and infeasible tables
are rejected at bind time with the model's reason; the one-rule spelling
still loads.

    python3 -m chialu.verify.check_rules_selftest [--work DIR] [--no-eda]
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

import yaml

from chialu.verify.domain_selftest import RUN as LEGACY_RUN

# the logic ops first: the fault plan applies mask i to vector i mod N over a stimulus ordered by op, so the
# masks land on the unchecked pairs' vectors and the gate proves they are outside it
OPS = ["and", "xor", "shl", "add", "sub", "adc", "neg", "mul_wide"]
ARITH = ["add", "sub", "adc", "neg", "mul_wide"]
LOGIC = ["and", "xor", "shl"]


def run_doc(check_block, ops=OPS, modes=None):
    doc = copy.deepcopy(LEGACY_RUN)
    v = doc["adir"]["variables"]
    for k in [k for k in v if k.startswith("checker.")] + ["check_en"]:
        v.pop(k, None)
    modes = modes or [{"count": 1, "format": "int16"}]
    v["modes"] = {"runtime": modes} if len(modes) > 1 else {"fixed": modes[0]}
    v["ops"] = {"runtime": list(ops)}
    v["check"] = {"fixed": check_block}
    v["verify.n_random"] = {"fixed": 60}
    v["verify.n_random_masks"] = {"fixed": 400}
    nodes = doc["adir"]["evaluate"]["nodes"]
    nodes["checker_gen"] = {"node": "chialu.eda.checker_gen",
                            "inputs": {"files": "artifacts.verify_bundle", "decl": "decl.check"}}
    nodes["fault"]["inputs"]["checker_rtl"] = "checker_gen.rtl_text"
    nodes.pop("synth_ppa", None)
    doc["adir"]["evaluate"]["feedback"] = ["conformance.detail", "fault.detail"]
    doc["adir"]["constraints"] = [c for c in doc["adir"]["constraints"] if "synth_ppa" not in c["metric"]]
    doc["adir"]["goal"] = {"maximize": "declaration.ok"}
    return doc


TABLE = {
    "default": {"detect": "none"},
    "fallback": "duplicate",
    "rules": [
        {"name": "int_arith", "formats": ["int16"], "ops": ARITH,
         "detect": {"random_alias": 5.0e-2, "single_bit": 1.0},
         "choices": [{"family": "residue", "modulus": [15, 31, 63], "generator_style": "csa_tree",
                      "comparator.family": ["direct_compare", "two_rail_tree"]},
                     {"family": "multi_residue", "moduli_count": [2, 3], "moduli_set": "low_cost_2a_minus_1"},
                     {"family": "rns_redundant", "base_moduli_count": 3, "redundant_moduli": [1, 2]}]},
        {"name": "int_logic", "formats": ["int16"], "ops": LOGIC, "detect": "none"},
    ],
}


def load(doc, work, name):
    from adir.instance import load as adir_load
    path = work / f"{name}.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    return adir_load(path, run_dir_override=str(work / f"run_{name}"))


def expect_bind_error(doc, work, name, fragment):
    from adir import BindError
    try:
        load(doc, work, name)
    except BindError as e:
        assert fragment in str(e), f"{name}: {e}"
        return str(e)
    raise AssertionError(f"{name}: the table was accepted")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work")
    ap.add_argument("--no-eda", action="store_true")
    args = ap.parse_args(argv)
    work = Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix="chialu_check_rules_"))
    work.mkdir(parents=True, exist_ok=True)
    from chialu.verify.formats import parse_format
    I16 = parse_format("int16").name

    inst = load(run_doc(TABLE), work, "rules")
    names = {v.name for v in inst.searched()}
    assert not any(n.startswith("checker.") for n in inst.bindings), "the legacy checker variables leaked"
    fam = inst.bindings["check.int_arith.family"]
    assert fam.time == "search" and fam.domain.members() == ["residue", "multi_residue", "rns_redundant"], fam.to_json()
    assert inst.bindings["check.int_arith.residue.modulus"].domain.members() == [31, 63], "modulus 15 aliases at 1/15 > 5e-2"
    assert inst.bindings["check.int_arith.multi_residue.moduli_count"].domain.members() == [2, 3]
    assert inst.bindings["check.int_arith.residue.comparator.family"].domain.members() == ["direct_compare", "two_rail_tree"]
    assert "check.int_arith.residue.comparator.tree_arity" in inst.tree.by_name      # active under two_rail_tree alone
    assert "check.int_logic.family" not in inst.tree.by_name and "check.int_logic.family" not in names
    assert inst.elaboration.info["check"]["unchecked"] == [(0, op) for op in sorted(LOGIC)] or \
        sorted(inst.elaboration.info["check"]["unchecked"]) == sorted((0, op) for op in LOGIC)
    checker = inst.artifacts["checker"].text
    assert "check rule int_arith: residue" in checker and "unchecked pairs (detect none)" in checker, checker[:400]
    files = inst.artifacts["verify_bundle"].texts
    assert "check_manifest.json" in files, sorted(files)
    manifest = json.loads(files["check_manifest.json"])
    mech = {r["op"]: r["mechanism"] for r in manifest}
    assert all(mech[op] == "code" for op in ARITH) and all(mech[op] == "unchecked" for op in LOGIC), mech
    arith = next(r for r in manifest if r["op"] == "add")
    assert arith["rule"] == "int_arith" and arith["family"] == "residue" and arith["pins"]["modulus"] == 31
    assert abs(arith["output_alias"] - 1 / 31) < 1e-12 and arith["detect"] == {"random_alias": 0.05, "single_bit": 1.0}
    spec = json.loads(files["spec.json"])
    assert spec["check"]["groups"][0]["family"] == "residue" and spec["detect"]["random_alias"][0] == "<="
    core = inst.artifacts["core"].text
    print("  ok   bound: variables, artifacts, manifest")

    # a declaration that switches the rule's family and pins regenerates the checker
    from adir.registry import underlying
    from chialu import eda as _eda

    class eda:                                          # the nodes as plain in-process calls
        checker_gen = staticmethod(underlying(_eda.checker_gen))
        conformance = staticmethod(underlying(_eda.conformance))
        fault = staticmethod(underlying(_eda.fault))
    gen = eda.checker_gen(files, {"int_arith": {"family": "rns_redundant", "rns_redundant": {"base_moduli_count": 3, "redundant_moduli": 2}}})
    assert gen["ok"] and "check rule int_arith: rns_redundant" in gen["rtl_text"] and "redundant moduli [127, 2047]" in gen["rtl_text"], gen["detail"]
    assert next(r for r in gen["manifest"] if r["op"] == "add")["family"] == "rns_redundant"
    same = eda.checker_gen(files, None)
    assert same["ok"] and same["rtl_text"] == checker
    other = eda.checker_gen(files, {"int_arith": {"family": "residue", "residue": {"modulus": 63, "comparator": {"family": "two_rail_tree", "tree_arity": 3}}}})
    assert other["ok"] and "comparator: two_rail_tree tree_arity=3" in other["rtl_text"] and "_m63" in other["rtl_text"]
    print("  ok   checker_gen: declarations regenerate the checker")

    if not args.no_eda:
        conf = eda.conformance(core, files)
        assert conf.get("pass"), conf.get("detail")
        for label, text in (("artifact", checker), ("rns_redundant", gen["rtl_text"]), ("residue63_two_rail", other["rtl_text"])):
            fr = eda.fault(core, files, text)
            assert fr.get("pass"), (label, fr.get("detail"))
            g = fr["groups"]["int_arith"]
            assert set(fr["groups"]) == {"int_arith"} and fr["sites"] > 0 and g["stuck_n"] > 0 and g["escape"] is not None, fr["groups"]
            assert g["clean_n"] > 0 and g["single_n"] == 32 and g["random_n"] == spec["n_random_masks"], g
            print(f"  ok   fault gate under the {label} checker: seam alias {fr['alias_rate']:.3f}, cov {fr['single_bit_coverage']:.3f}, "
                  f"fa {fr['false_alarms']}; rule int_arith: escape {g['escape']:.3f} over {g['stuck_n']} internal faults "
                  f"({g['stuck_masked']} masked, {fr['sites']} sites)")
        # a mute checker escapes every internal fault: the rule's gate names it
        from chialu.verify.alu_matrix import mute_checker
        from chialu.verify import alu_ref as A
        muted = mute_checker(A.alu_layout(A.normalize_spec(spec)), spec, spec["checker_name"])
        fr = eda.fault(core, files, muted)
        assert not fr["pass"] and "rule int_arith: ErrorDetect.escape" in fr["detail"], fr["detail"]
        print("  ok   a mute checker fails the rule's escape gate")
        # a mask on an unchecked pair's vector is outside the gate: the campaign counted arithmetic vectors alone
        from chialu.verify.harness import build_fault_verification, build_verification
        spec_full = json.loads(files["spec.json"])
        ver = build_verification(spec_full, work / "ver")
        plan, _check = build_fault_verification(spec_full, ver, work / "ver", n_random_masks=spec_full["n_random_masks"])
        n_vec = len(ver.vecs)
        logic_vectors = sum(1 for i in range(len(plan.masks)) if ver.meta[i % n_vec]["op"] in LOGIC)
        assert logic_vectors, "the stimulus has no logic vector"
        print(f"  ok   {logic_vectors} masks on unchecked pairs are outside the gate")

    # rejections at bind time
    bad = copy.deepcopy(TABLE); bad["rules"][0]["formats"] = ["fp16"]
    expect_bind_error(run_doc(bad), work, "bad_format", "is not a mode of the unit")
    bad = copy.deepcopy(TABLE); bad["rules"][0]["choices"][0]["A"] = 3
    expect_bind_error(run_doc(bad), work, "bad_pin", "neither a pin of the family")
    bad = copy.deepcopy(TABLE); bad["rules"][0]["ops"] = ARITH + ["and"]; bad["rules"][0]["fallback"] = "error"; bad["rules"][1]["ops"] = ["xor", "shl"]
    expect_bind_error(run_doc(bad), work, "bad_fallback", "need a replica under fallback error")
    bad = copy.deepcopy(TABLE); bad["rules"][0]["detect"] = {"random_alias": 1.0e-3}; bad["rules"][0]["choices"] = [{"family": "residue", "modulus": [7, 15]}]
    expect_bind_error(run_doc(bad), work, "infeasible", "no checker point meets the rule")
    bad = copy.deepcopy(TABLE); bad["rules"][1]["name"] = "int_arith"
    expect_bind_error(run_doc(bad), work, "dup_name", "is used twice")
    bad = copy.deepcopy(run_doc(TABLE)); bad["adir"]["variables"]["checker.family"] = {"fixed": "residue"}
    expect_bind_error(bad, work, "legacy_mix", "checker.family")
    print("  ok   six malformed or infeasible tables are rejected at bind time")

    # a rule without a requirement reports every family; a default with a requirement becomes a group
    open_table = {"default": {"detect": {"random_alias": 0.5}}, "rules": [{"name": "arith", "formats": ["int16"], "ops": ARITH}]}
    inst2 = load(run_doc(open_table), work, "open")
    assert inst2.bindings["check.arith.family"].domain.members() == list(__import__("chialu.targets.rtl.alu_checker", fromlist=["FAMILIES"]).FAMILIES)
    assert inst2.bindings["check.default.family"].domain.members()
    m2 = {r["op"]: r for r in json.loads(inst2.artifacts["verify_bundle"].texts["check_manifest.json"])}
    assert m2["and"]["rule"] == "default" and m2["and"]["mechanism"] == "replica" and m2["add"]["mechanism"] == "code"
    print("  ok   an open rule offers every family; a default with a bound is a group")

    # the one-rule spelling still loads and its checker is unchanged in kind
    legacy = load(copy.deepcopy(LEGACY_RUN), work, "legacy")
    assert legacy.bindings["checker.modulus"].value == 15 and "module alu_checker" in legacy.artifacts["checker"].text
    assert "check_manifest.json" in legacy.artifacts["verify_bundle"].texts
    print("  ok   the check_en + checker.* spelling loads with a manifest")
    print("PASS check rules through adir", work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
