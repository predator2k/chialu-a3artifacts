"""The prompt sources, the plans and the declaration lines of chiALU,
EDA-free: the family menu under the bindings, the lane-shared variable
index and the slot depth, the focus map, the card lookup of a shared
name, the partitions over inline structures, and the group rules of
the declaration check.

    python3 -m chialu.verify.prompt_selftest
"""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(record: dict, name: str):
    from adir.instance import load
    work = Path(tempfile.mkdtemp(prefix=f"chialu_prompt_{name}_"))
    p = work / "run.yaml"
    p.write_text(yaml.safe_dump(record, sort_keys=False))
    return load(p, run_dir_override=str(work / "run")), work


def main(argv=None) -> int:
    import chialu.domain  # noqa: F401
    from adir.declaration import Declaration, parse_block
    from adir.seeds import seed_programs
    from chialu.lines import check_structures, normalize_declaration
    from chialu.plans import partition
    from chialu.prompts import card_of, family_domain, focus_map, manifest_of, var_prefix
    from chialu.targets.rtl.structures import StructureManifest, is_inline
    from chialu.verify.domain_selftest import RUN
    fails = []

    def check(name, cond, detail=""):
        print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f": {detail}" if detail and not cond else ""))
        if not cond:
            fails.append(name)

    # ---- the integer unit of the domain selftest
    inst, work = _load(RUN, "int")
    names = set(inst.bindings)
    check("the lanes of a mode share their variables",
          "core.adder.m1.family" in names and not any(".l0." in n or ".l1." in n for n in names))
    b = inst.bindings.get("core.multiplier.m0.reduction.cpa.family")
    check("a nested slot's variable binds when named (lazily)", b is not None and b.time == "search")
    check("the defaults' view is small", len(inst.bindings) < 2000, str(len(inst.bindings)))
    check("the family menu follows the narrowed domain",
          family_domain(inst, "adder") == ["ripple_carry", "parallel_prefix", "carry_lookahead"],
          str(family_domain(inst, "adder")))
    check("the checker offers its generator's variables alone",
          {n for n in names if n.startswith("checker.")} == {"checker.family", "checker.modulus",
                                                             "checker.generator_style",
                                                             "checker.comparator.family"},
          str(sorted(n for n in names if n.startswith("checker."))))
    programs = seed_programs(inst, work / "run")
    text = programs[0][1]
    parent = {"candidate_id": "seed:baseline",
              "declarations": {"vars": {}, "lines": [list(x) for x in parse_block(text).lines]}}
    ctx = inst.ctx()
    fm = focus_map(ctx, parent)
    brute: dict = {}
    for s in manifest_of(inst, parent):
        if s.get("sv"):
            pre = var_prefix(s)
            brute.setdefault(s["sv"], set()).update(n for n, b in ctx.bindings.items()
                                                    if n.startswith(pre) and b.time == "search")
    check("focus_map matches its definition", {k: set(v) for k, v in fm.items()} == brute)
    check("every region has variables", all(fm.values()), str([k for k, v in fm.items() if not v][:3]))
    # the group rules of the declaration check
    manifest = StructureManifest.from_json(inst.elaboration.info["manifest"])
    lines = [("STRUCTURE", s.fields()) for s in manifest]
    adders = [s for s in manifest if s.kind == "adder"]
    grouped = []
    for k, t in lines:
        sid = t[0]
        grouped.append((k, t + ["group=g"] if sid in (adders[0].id, adders[1].id) else t))
    decl = Declaration(vars={f"core.adder.{adders[0].index}.family": "parallel_prefix",
                             f"core.adder.{adders[1].index}.family": "ripple_carry"},
                       lines=grouped, present=True)
    ok, detail = check_structures(inst.ctx(declaration=decl), [dict(zip(["_"], [[t[0]]]), **dict(x.split("=", 1) for x in t[1:])) for k, t in grouped])
    check("a group with two families is rejected", not ok and "different families" in detail, detail[:120])
    decl2 = Declaration(vars={f"core.adder.{adders[0].index}.family": "parallel_prefix",
                              f"core.adder.{adders[0].index}.topology": "kogge_stone"},
                        lines=grouped, present=True)
    norm = normalize_declaration(inst.ctx(declaration=decl2), decl2)
    other = f"core.adder.{adders[1].index}."
    check("a group member takes the family and the choice its family admits",
          norm.vars.get(other + "family") == "parallel_prefix" and norm.vars.get(other + "topology") == "kogge_stone"
          if adders[0].index != adders[1].index else True)
    # ---- a float unit: the shared card names resolve by the slot
    ex = REPO_ROOT / "targets" / "fp_alu.yaml"
    if ex.is_file():
        from adir.instance import load
        finst = load(ex, run_dir_override=str(Path(tempfile.mkdtemp(prefix="chialu_prompt_f_")) / "run"))
        check("the unpacker's shared_per_lane card is the unpack card",
              card_of(finst, "shared_per_lane", "unpacker").endswith("arch/unpack/shared_per_lane.md"),
              card_of(finst, "shared_per_lane", "unpacker"))
        check("the rounder's shared_per_lane card is the round card",
              card_of(finst, "shared_per_lane", "rounder").endswith("arch/round/shared_per_lane.md"))
        check("the float unit binds under 100000 variables (the lanes share theirs)", len(finst.bindings) < 100000,
              str(len(finst.bindings)))
    # ---- a posit unit: no plan groups the inline posit unit
    prec = copy.deepcopy(RUN)
    prec["adir"]["variables"]["modes"] = {"runtime": [{"count": 1, "format": "posit16_1"}, {"count": 2, "format": "int8"}]}
    prec["adir"]["variables"]["ops"] = {"runtime": ["add", "fadd", "fmul"]}
    pinst, pwork = _load(prec, "posit")
    pman = StructureManifest.from_json(pinst.elaboration.info["manifest"])
    check("the posit unit is inline", any(is_inline(s) for s in pman))
    for plan in ("packed_banks", "per_position"):
        part = partition(pman, plan)
        members = {m for _, ms in part for m in ms}
        check(f"plan {plan} leaves the inline structures out", not any(is_inline(pman.get(m)) for m in members))
    print(f"[prompt_selftest] {'all pass' if not fails else f'{len(fails)} failures: {fails}'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
