"""The behavior rules are necessary and sufficient on representative
rules (docs/behav_checker_plan.md, pitfall 7): an excluded member under
the contract that excludes it fails to render or fails conformance, an
admitted conditional member conforms under a contract that admits it,
the lint gate holds, and a rejection names the rule.

    python3 -m chialu.verify.behavior_rules_selftest
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from adir.errors import BindError
from adir.variables import Binding
from chialu import behavior_rules as BR
from chialu.modules import alu as ALU
from chialu.targets import derive
from chialu.verify.alu_ref import normalize_spec

ROOT = Path(__file__).resolve().parents[2]


def bindings(modes, ops, rounding=("RNE",), x_form="exact", accuracy="exact", **extra) -> dict:
    """The bindings `chialu.ALU.elaborate` reads, as ADIR would hand them."""
    b = {"modes": Binding(None, "runtime" if len(modes) > 1 else "fixed",
                          value=modes[0] if len(modes) == 1 else None, members=list(modes) if len(modes) > 1 else None),
         "ops": Binding(None, "runtime" if len(ops) > 1 else "fixed",
                        value=ops[0] if len(ops) == 1 else None, members=list(ops) if len(ops) > 1 else None),
         "rounding": Binding(None, "runtime" if len(rounding) > 1 else "fixed",
                             value=rounding[0] if len(rounding) == 1 else None,
                             members=list(rounding) if len(rounding) > 1 else None),
         "x_form": Binding(None, "fixed", value=x_form), "accuracy": Binding(None, "fixed", value=accuracy),
         "check_en": Binding(None, "fixed", value=False), "flags": Binding(None, "fixed", value=[]),
         "sr_bits": Binding(None, "fixed", value=8), "flag_scope": Binding(None, "fixed", value="per_result")}
    for k, v in extra.items():
        b[k] = Binding(None, "fixed", value=v)
    return b


def spec_of(modes, ops, **kw) -> dict:
    spec = normalize_spec(ALU.spec_from_bindings(bindings(modes, ops, **kw)))
    spec["dut_name"] = "alu_core"
    return spec


def variables_of(b: dict) -> dict:
    return {v.name: v for v in ALU.elaborate(b).variables}


def must_raise(fn, *needles):
    try:
        fn()
    except (ValueError, BindError) as e:
        text = str(e)
        for n in needles:
            assert n in text, f"the error names no {n!r}: {text[:300]}"
        return text
    raise AssertionError(f"no error raised; expected one naming {needles}")


def conforms(spec, selections, tag: str, out: Path, vectors: int = 64) -> bool:
    from chialu.verify.variant_selftest import check_seed
    r = check_seed(spec, selections, out / tag, vectors, 7)
    return bool(r["pass"]), r


def instance_of(elab, specs=None):
    """The declaration check's view of an elaboration: ADIR's lazy
    bindings over the compiled templates under `core.*: {search: all}`,
    which is how a run file binds them."""
    from adir.variables import Bindings, VariableTree, _topological
    from adir import Variable, Enum
    xform = Variable("x_form", Enum(("exact", "guard_round_sticky")), ("fixed",))
    settings = {"core.*": {"search": "all"},
                "x_form": {"fixed": elab.info.get("spec", {}).get("x_form", "exact")}}
    settings.update(specs or {})
    tree = VariableTree(list(elab.variables) + [xform], elab.index_sets, settings)
    bindings = Bindings(tree)
    bindings.bind_defaults()

    class _Template:
        normalize_declaration = None

        @staticmethod
        def line_kind(kind):
            return None

    class _Inst:
        template = _Template()

        def __init__(self):
            self.tree = tree
            self.bindings = bindings

        def variable_order(self):
            return _topological([b.variable for b in self.bindings.values()])

    return _Inst()


def checked(inst, **vars_) -> dict:
    from adir.declaration import Declaration, check_declaration
    return check_declaration(inst, Declaration(vars=dict(vars_), present=True), None)


def main():
    out = Path(tempfile.mkdtemp(prefix="chialu-behavior-rules-"))
    fp16 = {"count": 1, "format": "fp16"}

    # -- the lint gate
    lint = BR.lint()
    assert lint["ok"], {k: v for k, v in lint.items() if k not in ("counts",)}
    assert not lint["unregistered"] and not lint["stale"] and not lint["retired_stale"]
    print(f"lint: {lint['families']} families ({lint['counts']}), {lint['rules']} rules, 0 unregistered, 0 stale")

    # -- the option rule: guard_round_sticky with a cvt op in the float mode, and with SR
    cvt = bindings([fp16], ["fadd", "fmul", "cvt(int8)"], x_form="guard_round_sticky")
    problems = BR.check_options(normalize_spec(ALU.spec_from_bindings(cvt)))
    assert problems and "no_cvt_in_float_modes" in problems[0], problems
    must_raise(lambda: ALU.elaborate(cvt), "x_form: guard_round_sticky", "no_cvt_in_float_modes")
    sr = bindings([fp16], ["fadd", "fmul"], rounding=("RNE", "SR"), x_form="guard_round_sticky")
    must_raise(lambda: ALU.elaborate(sr), "no_sr")
    # the render-time last defense states the same fact
    from chialu.targets.rtl.alu_mode import tight_x
    from chialu.verify.formats import parse_format
    must_raise(lambda: tight_x({"x_form": "guard_round_sticky"}, {}, 0, "float", [parse_format("int8")], False),
               "conversion targets")
    assert tight_x({"x_form": "guard_round_sticky"}, {}, 0, "float", [], False) is True
    assert tight_x({"x_form": "guard_round_sticky"}, {}, 0, "integer", [], False) is False
    print("x_form: the option rule rejects a cvt op and SR at load; tight_x is the last defense")

    # -- round_fused_in_reduction needs x_form exact
    tight = bindings([fp16], ["fadd", "fmul"], x_form="guard_round_sticky")
    v = variables_of(tight)["core.fp_multiplier.*.family"]
    assert not v.domain.contains("round_fused_in_reduction"), v.domain.describe()
    why = v.domain.exclusion_reason("round_fused_in_reduction")
    assert why and "x_form_exact" in why, why
    fused_mul = {"core.fp_multiplier.m0": ("round_fused_in_reduction", {})}
    must_raise(lambda: derive.seed_alu_text(spec_of([fp16], ["fadd", "fmul"], x_form="guard_round_sticky"),
                                            families=fused_mul), "exact X")
    exact = variables_of(bindings([fp16], ["fadd", "fmul"]))["core.fp_multiplier.*.family"]
    assert exact.domain.contains("round_fused_in_reduction")
    ok, r = conforms(spec_of([fp16], ["fadd", "fmul"]), fused_mul, "round_fused_exact", out)
    assert ok, r.get("detail")
    print(f"round_fused_in_reduction: excluded under guard_round_sticky ({why[:60]}...), render refused; conforms at exact")

    # -- the fused multiply-add's as_stored needs no SR
    srb = bindings([fp16], ["fadd", "fsub", "fmul"], rounding=("RNE", "SR"))
    elab = ALU.elaborate(srb)
    vs = {v.name: v for v in elab.variables}
    v = vs["core.fp_fma.*.subnormal_representation"]
    assert list(v.domain.members_) == ["pseudo_normalized_wide_exponent"], v.domain.describe()
    why = v.domain.exclusion_reason("as_stored")
    assert why and "no_sr" in why and "SR" in why, why
    changed = [d for d in elab.info["behavior_report"]["defaults_changed"] if d["variable"] == v.name]
    assert changed and changed[0]["to"] == "pseudo_normalized_wide_exponent", changed
    as_stored = {"core.fp_fma.m0": ("classic_fma", {"subnormal_representation": "as_stored"})}
    must_raise(lambda: derive.seed_alu_text(spec_of([fp16], ["fadd", "fsub", "fmul"], rounding=("RNE", "SR")),
                                            families=as_stored), "as_stored")
    ok, r = conforms(spec_of([fp16], ["fadd", "fsub", "fmul"]), as_stored, "fma_as_stored_rne", out)
    assert ok, r.get("detail")
    print("fp_fma subnormal_representation as_stored: excluded under SR with the default re-derived; conforms under RNE")

    # -- the fp_fma organizations against fma_contract (the classification on the families): a mode with a fused
    #    op under the fused contract loses separate_multiplier_and_adder, a mode without one keeps both organizations
    #    (the per-index domain), and a fused family serves a mode with fadd and fsub alone
    fused_ops = ["fadd", "fsub", "fmul", "fmadd"]
    modes_two = [dict(fp16, ops=fused_ops), {"count": 1, "format": "bf16", "ops": ["fadd", "fsub"]}]
    elab = ALU.elaborate(bindings(modes_two, fused_ops))
    v = {x.name: x for x in elab.variables}["core.fp_fma.*.family"]
    assert v.index_domains and "m0" in v.index_domains and "m1" not in v.index_domains, v.index_domains
    m0 = v.index_domains["m0"]
    assert not m0.contains("separate_multiplier_and_adder") and m0.contains("classic_fma") and m0.contains("bridge_fma"), \
        m0.describe()
    why = m0.exclusion_reason("separate_multiplier_and_adder") or ""
    assert "fma_contract_sequential_or_no_fused_op_in_mode" in why and "fma_contract 'fused'" in why, why
    assert v.domain.contains("separate_multiplier_and_adder") and v.domain.contains("classic_fma")
    expanded = {x.name: x for x in v.expand(["m0", "m1"])}
    assert expanded["core.fp_fma.m0.family"].domain.default() == "classic_fma"
    assert expanded["core.fp_fma.m1.family"].domain.default() == "separate_multiplier_and_adder"
    changed = [d for d in elab.info["behavior_report"]["defaults_changed"] if d["variable"] == v.name]
    assert changed and changed[0]["indexes"] == ["m0"] and changed[0]["to"] == "classic_fma", changed
    spec_two = spec_of(modes_two, fused_ops)
    must_raise(lambda: derive.seed_alu_text(spec_two, families={"core.fp_fma.m0": ("separate_multiplier_and_adder", {})}),
               "fma_contract fused")
    ok, r = conforms(spec_two, {"core.fp_fma.m0": ("classic_fma", {}), "core.fp_fma.m1": ("classic_fma", {})},
                     "fused_ops_fused_contract", out)
    assert ok, r.get("detail")
    print("fp_fma under fma_contract fused: the separate organization leaves the mode with fmadd alone (index_domains) "
          "and its forced seed raises; classic_fma conforms on fmadd and in the mode with fadd and fsub alone")
    # under the sequential contract the fused families leave, and the separate multiplier then adder conform
    v = variables_of(bindings([fp16], fused_ops, fma_contract="sequential"))["core.fp_fma.*.family"]
    assert list(v.domain.members_) == ["separate_multiplier_and_adder"], v.domain.describe()
    why = v.domain.exclusion_reason("classic_fma") or ""
    assert "fma_contract_fused_or_no_fused_op_in_mode" in why and "fma_contract 'sequential'" in why, why
    spec_seq = spec_of([fp16], fused_ops, fma_contract="sequential")
    must_raise(lambda: derive.seed_alu_text(spec_seq, families={"core.fp_fma.m0": ("classic_fma", {})}),
               "fma_contract sequential")
    ok, r = conforms(spec_seq, {"core.fp_fma.m0": ("separate_multiplier_and_adder", {})}, "fused_ops_sequential", out)
    assert ok, r.get("detail")
    # without a fused op both organizations stay under either contract
    for contract in ("fused", "sequential"):
        v = variables_of(bindings([fp16], ["fadd", "fsub", "fmul"], fma_contract=contract))["core.fp_fma.*.family"]
        assert v.domain.contains("separate_multiplier_and_adder") and v.domain.contains("classic_fma"), v.domain.describe()
    print("fp_fma under fma_contract sequential: the fused families leave the mode with fmadd, the forced seed raises, "
          "separate_multiplier_and_adder conforms; a mode without a fused op keeps both under either contract")

    # -- the PLAM member selects the computed function: out of an exact unit, in an approximate one
    posit = {"count": 1, "format": "posit8_0"}
    v = variables_of(bindings([posit], ["fmul"]))["core.posit_unit.*.approximation"]
    assert not v.domain.contains("logarithmic_fraction"), v.domain.describe()
    assert "approximate_unit" in (v.domain.exclusion_reason("logarithmic_fraction") or "")
    from chialu.spaces.dsp_posit_spaces import posit_unit_space
    from chialu.modules.common import FIXED_OR_SEARCH
    space = posit_unit_space()
    approx_spec = dict(spec_of([posit], ["fmul"]), accuracy="approximate")
    pruned = {x.name: x for x in BR.prune_slot("posit_unit", space, "core.posit_unit.*",
                                               space.variables("core.posit_unit.*", FIXED_OR_SEARCH, indexed_by="s"),
                                               approx_spec, ["m0"])}
    assert pruned["core.posit_unit.*.approximation"].domain.contains("logarithmic_fraction")
    plam = {"core.posit_unit.m0": ("posit_adder_multiplier", {"approximation": "logarithmic_fraction"})}
    ok, r = conforms(spec_of([posit], ["fmul"]), plam, "plam_exact", out)
    assert not ok, "the PLAM multiplier conformed bit-exactly, so the selector rule is not necessary"
    print(f"posit approximation logarithmic_fraction: excluded from an exact unit, kept in an approximate one; "
          f"forced, {r.get('mismatch_count')} vectors mismatch")

    # -- the dot: a numeric selector is never searched and stays YAML-fixed; a family needing the architecture
    #    contract leaves the fused unit's menu; a retired member is still rejected by the generator
    from adir.instance import load
    tdw = load(str(ROOT / "targets" / "eval" / "vec_dot_acc_cmp_fp16_tdw.yaml"))
    b = tdw.bindings["core.window_bits"]
    assert b.time == "fixed" and b.value == 76, (b.time, b.value)
    dot = load(str(ROOT / "targets" / "vec_dot_acc.yaml"))
    b = dot.bindings["core.window_bits"]
    assert b.time == "search" and b.domain.members() == [0], b.domain.describe()
    fam = dot.bindings["core.family"]
    assert not fam.domain.contains("streaming_accurate_accumulator")
    assert "dot_contract_architecture" in (fam.domain.exclusion_reason("streaming_accurate_accumulator") or "")
    assert "removed from the menu" in (dot.elaboration.info.get("behavior_rules") or "")
    import json
    spec = json.loads({a.path: a for a in dot.artifacts.values()}["verify_bundle"].texts["spec.json"])
    must_raise(lambda: derive.seed_for(spec, family=("streaming_accurate_accumulator", {})), "architecture contract")
    from chialu.spaces.fma_dot_spaces import UNSUPPORTED_DOT_CHOICES
    assert len(UNSUPPORTED_DOT_CHOICES) == 8 and "kulisch_long_accumulator.carry_resolution" in UNSUPPORTED_DOT_CHOICES
    must_raise(lambda: derive.seed_for(spec, family=("kulisch_long_accumulator", {"carry_resolution": "periodic_sweep"})),
               "periodic")
    print("dot: window_bits searches one member and takes a fixed 76; streaming_accurate_accumulator leaves the fused "
          "menu with its reason; a retired member is rejected")

    # -- a declaration or a fixed binding naming an excluded member is rejected with the reason
    from adir.variables import bind_one
    v = vs["core.fp_fma.*.subnormal_representation"].expand(["m0"])[0]
    fam_var = vs["core.fp_fma.*.family"].expand(["m0"])[0]
    parent = {fam_var.name: Binding(fam_var, "search", domain=fam_var.domain)}
    text = must_raise(lambda: bind_one(v, {"core.fp_fma.m0.subnormal_representation": {"fixed": "as_stored"}}, parent),
                      "outside", "no_sr")
    from adir.declaration import Declaration, check_declaration

    class _Inst:
        """The declaration check's view of an instance: the fp_fma variables of the SR unit, all searched."""
        class template:
            normalize_declaration = None

            @staticmethod
            def line_kind(kind):
                return None
        bindings = {x.name: Binding(x, "search", domain=x.domain) for x in v.expand(["m0"]) + [
            y.expand(["m0"])[0] for y in vs.values() if y.name == "core.fp_fma.*.family"]}
        bindings["core.family"] = Binding(vs["core.family"], "fixed", value="unit_per_class")

        def variable_order(self):
            return [self.bindings[name].variable for name in
                    ("core.family", "core.fp_fma.m0.family", "core.fp_fma.m0.subnormal_representation")]
    decl = Declaration(vars={"core.fp_fma.m0.family": "classic_fma", "core.fp_fma.m0.subnormal_representation": "as_stored"},
                       present=True)
    r = check_declaration(_Inst(), decl, None)
    assert not r["ok"] and "no_sr" in r["detail"], r["detail"]
    print("a fixed binding and a VAR line naming as_stored under SR are rejected with the rule's reason")

    # -- the conformance node's rule-defect note names the governed members of a declaration
    members = BR.declared_rule_members({"core.fp_fma.m0.family": "classic_fma",
                                        "core.fp_fma.m0.subnormal_representation": "as_stored",
                                        "core.adder.m1.family": "ripple_carry"})
    assert any("classic_fma" in m for m in members) and any("as_stored" in m for m in members), members
    assert not any("ripple_carry" in m for m in members), members

    # Compact X now normalizes the exact product before truncation. Stored
    # subnormals are legal with either separate or fused arithmetic.
    fma_ops = ["fadd", "fsub", "fmul"]
    tight_fma = bindings([fp16], fma_ops, x_form="guard_round_sticky")
    elab = ALU.elaborate(tight_fma)
    v = {v.name: v for v in elab.variables}["core.unpacker.*.denormal_handling"]
    assert v.domain.contains("in_datapath") and not v.member_when, v
    inst = instance_of(elab)
    r = checked(inst, **{"core.unpacker.m0.denormal_handling": "in_datapath"})
    assert r["ok"], r["detail"]
    spec_tight = spec_of([fp16], fma_ops, x_form="guard_round_sticky")
    unpack = ("per_unit_unpack", {"denormal_handling": "in_datapath"})
    for family in ("separate_multiplier_and_adder", "classic_fma"):
        ok, r = conforms(spec_tight, {"core.fp_fma.m0": (family, {}), "core.unpacker.m0": unpack},
                         "in_datapath_tight_" + family, out)
        assert ok, r.get("detail")
    v = variables_of(bindings([fp16], ["fcmp"], x_form="guard_round_sticky"))["core.unpacker.*.denormal_handling"]
    assert v.domain.contains("in_datapath") and not v.member_when
    print("stored-subnormal operands conform with separate and fused compact-X producers")

    # -- the dual LZA strings under the unswapped datapath, and the split select nested under the dual strings
    exact_b = bindings([fp16], fma_ops)
    elab = ALU.elaborate(exact_b)
    vs = {v.name: v for v in elab.variables}
    for lk in ("lz", "near_lz"):
        v = vs[f"core.fp_adder.*.{lk}.string_form"]
        assert v.member_when["dual_pos_neg_strings"][:2] == ("core.fp_adder.*.operand_order", ("shift_each_operand",)), v
        assert vs[f"core.fp_adder.*.{lk}.split_string_select"].when == (f"core.fp_adder.*.{lk}.string_form",
                                                                          ("dual_pos_neg_strings",))
    inst = instance_of(elab)
    r = checked(inst, **{"core.fp_adder.m0.lz.string_form": "dual_pos_neg_strings"})
    assert not r["ok"] and "core.fp_adder.m0.operand_order is one of ['shift_each_operand']; it is 'swap_before_shift'" \
        in r["detail"], r["detail"]
    r = checked(inst, **{"core.fp_adder.m0.operand_order": "shift_each_operand",
                         "core.fp_adder.m0.lz.string_form": "dual_pos_neg_strings"})
    assert r["ok"] and r["decl.core.fp_adder.m0.lz.split_string_select"] == "true_sign", r["detail"]
    r = checked(inst, **{"core.fp_adder.m0.lz.split_string_select": "maximum_count"})
    assert not r["ok"] and "declared, but inactive" in r["detail"], r["detail"]
    spec_exact = spec_of([fp16], fma_ops)
    dual = {"lz.family": "lza", "lz.string_form": "dual_pos_neg_strings"}
    must_raise(lambda: derive.seed_alu_text(spec_exact, families={
        "core.fp_adder.m0": ("single_path", dict(dual, operand_order="swap_before_shift"))}), "dual_pos_neg_strings")
    ok, r = conforms(spec_exact, {"core.fp_adder.m0": ("single_path", dict(dual, operand_order="shift_each_operand"))},
                     "dual_strings_unswapped", out)
    assert ok, r.get("detail")
    print("lza string_form dual_pos_neg_strings: conditioned on operand_order; rejected under swap_before_shift, forced "
          "it raises, conforms under shift_each_operand; split_string_select is a decision under the dual strings alone")

    # -- bridge_fma: the cascade leaves the ALU's slot under every contract, its product rounding is a decision under
    #    the cascade alone, bridge_reuse needs the exact X, and its subnormal_representation is a deferred rule
    vs = {v.name: v for v in ALU.elaborate(exact_b).variables}
    v = vs["core.fp_fma.*.composition_style"]
    assert not v.domain.contains("cascade_mul_then_add") and v.domain.contains("bridge_reuse"), v.domain.describe()
    assert "fma_contract_cascade_product_rounding" in (v.domain.exclusion_reason("cascade_mul_then_add") or "")
    assert vs["core.fp_fma.*.cascade_product_rounding"].when == ("core.fp_fma.*.composition_style", ("cascade_mul_then_add",))
    must_raise(lambda: derive.seed_alu_text(spec_exact, families={
        "core.fp_fma.m0": ("bridge_fma", {"composition_style": "cascade_mul_then_add"})}), "cascade_mul_then_add")
    v = vs_tight = {v.name: v for v in ALU.elaborate(tight_fma).variables}["core.fp_fma.*.composition_style"]
    assert not v.domain.contains("bridge_reuse") and v.domain.contains("monolithic_fused"), v.domain.describe()
    assert "x_form_exact" in (v.domain.exclusion_reason("bridge_reuse") or "")
    must_raise(lambda: derive.seed_alu_text(spec_tight, families={"core.fp_fma.m0": ("bridge_fma", {})}), "exact X")
    ok, r = conforms(spec_exact, {"core.fp_fma.m0": ("bridge_fma", {})}, "bridge_reuse_exact", out)
    assert ok, r.get("detail")
    # the bridge's subnormal_representation under monolithic_fused is classic_fma's: as_stored renders under RNE
    ok, r = conforms(spec_exact, {"core.fp_fma.m0": ("bridge_fma", {"composition_style": "monolithic_fused",
                                                                    "subnormal_representation": "as_stored"})},
                     "bridge_monolithic_as_stored", out)
    assert ok, r.get("detail")
    print("bridge_fma: the cascade is removed and its forced seed raises, cascade_product_rounding nests under the "
          "cascade, bridge_reuse is removed at the tight X and conforms at the exact X; monolithic_fused with as_stored "
          "conforms")

    # -- reduced_latency_fma's fused rounding: removed at the tight X, conditioned on sharing dedicated_per_mode
    v = {x.name: x for x in ALU.elaborate(tight_fma).variables}["core.fp_fma.*.rounding_position"]
    assert not v.domain.contains("fused_with_cpa_dual_sum"), v.domain.describe()
    assert "x_form_exact" in (v.domain.exclusion_reason("fused_with_cpa_dual_sum") or "")
    fused_round = {"rounding_position": "fused_with_cpa_dual_sum"}
    must_raise(lambda: derive.seed_alu_text(spec_tight, families={"core.fp_fma.m0": ("reduced_latency_fma", fused_round)}),
               "exact X")
    bf16 = {"count": 1, "format": "bf16"}
    elab = ALU.elaborate(bindings([fp16, bf16], fma_ops))      # two formats, so sharing offers shared_across_formats
    vs = {v.name: v for v in elab.variables}
    v = vs["core.fp_fma.*.rounding_position"]
    assert v.member_when and v.member_when["fused_with_cpa_dual_sum"][:2] == ("core.fp_fma.*.sharing", ("dedicated_per_mode",)), \
        v.member_when
    assert "sharing_dedicated_per_mode" in v.member_when["fused_with_cpa_dual_sum"][2]
    assert vs["core.fp_fma.*.sharing"].domain.contains("shared_across_formats")
    inst = instance_of(elab)
    shared = {"core.fp_fma.m0.family": "reduced_latency_fma", "core.fp_fma.m0.sharing": "shared_across_formats",
              "core.fp_fma.m1.family": "reduced_latency_fma", "core.fp_fma.m1.sharing": "shared_across_formats"}
    r = checked(inst, **dict(shared, **{"core.fp_fma.m0.rounding_position": "fused_with_cpa_dual_sum"}))
    assert not r["ok"] and "core.fp_fma.m0.sharing is one of ['dedicated_per_mode']" in r["detail"], r["detail"]
    r = checked(inst, **{"core.fp_fma.m0.family": "reduced_latency_fma",
                         "core.fp_fma.m0.rounding_position": "fused_with_cpa_dual_sum"})
    assert r["ok"] and r["decl.core.fp_fma.m0.rounding_position"] == "fused_with_cpa_dual_sum", r["detail"]
    spec_two_fmt = spec_of([fp16, bf16], fma_ops)
    must_raise(lambda: derive.seed_alu_text(spec_two_fmt, families={
        "core.fp_fma.m0": ("reduced_latency_fma", dict(fused_round, sharing="shared_across_formats")),
        "core.fp_fma.m1": ("reduced_latency_fma", dict(fused_round, sharing="shared_across_formats"))}), "dedicated_per_mode")
    ok, r = conforms(spec_exact, {"core.fp_fma.m0": ("reduced_latency_fma", fused_round)}, "fused_rounding_dedicated", out)
    assert ok, r.get("detail")
    print("reduced_latency_fma rounding_position fused_with_cpa_dual_sum: removed at the tight X, conditioned on sharing; "
          "the VAR line is rejected under shared_across_formats, forced it raises, and it conforms under dedicated_per_mode")
    print(f"PASS behavior rules: {out}")


if __name__ == "__main__":
    main()
