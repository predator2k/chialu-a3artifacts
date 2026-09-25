"""chiALU library: unit class 1, y = op(a, b) (docs/formats-and-options.md).

`chialu.ALU` has no main format: `modes` lists the (count, format)
modes the datapath serves (fixed: one; runtime: several, a `mode` port
selects), `ops` the op set, and the unit options (rounding, daz_in,
ftz_out, unary_dual, flags, sr_bits, the convention options) complete
the contract. Which ops are legal in a mode follows the mode's format
family (section 4 of the spec).

The elaboration adds the searched variables: `core.family` (the
physical partitioning), one family space per physical structure of the
seed (`core.<kind>.<index>.family` and that family's choices, indexed by
the structures of that kind), the non-structure slots (`core.subword.*`,
...), and the checker's space (`checker.*`) when the unit is checked.
The sharing plan lives in the seed's STRUCTURE lines.
"""
from __future__ import annotations

import re

from adir import BindError, Bool, Elaboration, Enum, Range, Struct, Template, Variable
from chialu.lines import MOVE, STRUCTURE, normalize_declaration
from chialu.prompts import focus_map
from chialu.modules import generators
from chialu.modules import check_rules
from chialu.modules.common import (FIXED, FIXED_OR_RUNTIME, FIXED_OR_SEARCH, checker_variables,
                                   clock_variable, convention_variables, omitted_options,
                                   option_variables, vals, value, var)
from chialu.papers import PRESETS
from chialu.plans import PLANS, PLAN_DOC, plan_seed, replan
from chialu.spaces.arith_spaces import cpa_space, div_space, mul_space, shifter_space
from chialu.spaces.fp_spaces import fp_fma_space, fp_add_space, fp_div_space, fp_mul_space
from chialu.spaces.misc_spaces import X_FORM
from chialu.verify.alu_ref import (CONVENTION_NAMES, OPS, alu_layout, checked_modes, cvt_target,
                                   family_of, is_cvt, legal_pairs, op_class)
from chialu.verify.formats import BCDFormat, BlockFormat, FloatFormat, X87Format, parse_format

CVT_RE = re.compile(r"^cvt\((.+)\)$")
ERROR_METRICS = ("max_ulp", "max_abs", "error_rate", "med", "nmed", "mred")


def _validate_mode(m):
    if not isinstance(m, dict) or not {"count", "format"} <= set(m) or set(m) - {"count", "format", "ops"}:
        raise BindError(f"mode {m!r}: needs {{count, format}} and optionally ops")
    if not isinstance(m["count"], int) or m["count"] < 1:
        raise BindError(f"mode {m!r}: count must be a positive integer")
    try:
        parse_format(str(m["format"]))
    except ValueError as e:
        raise BindError(f"mode {m!r}: {e}") from None
    if "ops" in m:
        if not isinstance(m["ops"], (list, tuple)) or not m["ops"]:
            raise BindError("mode.ops must be a nonempty list")
        for operation in m["ops"]:
            _validate_op(operation)


def _validate_op(op):
    if not isinstance(op, str):
        raise BindError(f"op {op!r}: not a name")
    if CVT_RE.match(op):
        try:
            parse_format(CVT_RE.match(op).group(1))
        except ValueError as e:
            raise BindError(f"{op}: {e}") from None
        return
    if op not in OPS:
        raise BindError(f"unknown op {op!r} (known: {', '.join(OPS)} and cvt(<format>))")


def _validate_one_budget(b, where: str):
    if not isinstance(b, dict) or not b:
        raise BindError(f"{where}: a non-empty mapping {{metric: bound}}")
    for k, v in b.items():
        if k == "bit_exact":
            if v is not True:
                raise BindError(f"{where}.bit_exact: true (the mode computes the exact result)")
            if len(b) > 1:
                raise BindError(f"{where}: bit_exact is the whole budget of an exact mode")
            continue
        if k not in ERROR_METRICS:
            raise BindError(f"{where}: unknown metric {k!r} (known: {ERROR_METRICS + ('bit_exact',)})")
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise BindError(f"{where}.{k}: a number")


def _validate_check(block):
    """The Struct's own check is the type alone: ADIR reports a validator's
    error as `outside <doc>`, so the shape is checked by the elaboration
    (check_rules.validate_check), whose messages name the rule and key."""
    if block is not None and not isinstance(block, dict):
        raise BindError("check: a mapping {default, rules, fallback, checker_choices}")


def _validate_budget(b):
    """One budget, or one per accuracy mode in mode order under
    `accuracy_ctl: runtime` (the count is checked against
    `accuracy_modes` at elaboration, which is where both are bound)."""
    if isinstance(b, (list, tuple)):
        if not b:
            raise BindError("error_budget: a budget per accuracy mode, in mode order")
        for i, one in enumerate(b):
            _validate_one_budget(one, f"error_budget[{i}]")
        return
    _validate_one_budget(b, "error_budget")


def spec_from_bindings(b: dict, checked=None) -> dict:
    """The verify-layer spec of the bindings (the same dict
    chialu.targets.derive builds)."""
    spec = {"unit": "alu",
            "modes": [{"count": int(m["count"]), "format": str(m["format"]),
                       **({"ops": list(m["ops"])} if "ops" in m else {})}
                      for m in vals(b, "modes")],
            "ops": list(vals(b, "ops"))}
    for name in ("rounding", "daz_in", "ftz_out", "unary_dual", "check_sr"):
        if name in b:
            spec[name] = list(vals(b, name))
    if "quotient_semantics" in b:
        spec["quotient_semantics"] = list(vals(b, "quotient_semantics"))
    spec["flags"] = list(value(b, "flags", ()) or ())
    spec["sr_bits"] = value(b, "sr_bits")
    spec["underflow_contract"] = value(b, "underflow_contract", "ieee")
    xb = b.get("x_form")
    spec["x_form"] = xb.domain.default() if xb is not None and xb.time == "search" else value(b, "x_form", "exact")
    for name in CONVENTION_NAMES:
        if name in b:
            spec[name] = value(b, name)
    spec["accuracy"] = value(b, "accuracy", "exact")
    spec["accuracy_ctl"] = value(b, "accuracy_ctl", "static")
    if spec["accuracy_ctl"] == "runtime":
        spec["accuracy_mode"] = list(range(int(value(b, "accuracy_modes", 2))))
    if spec["accuracy"] == "approximate" and "error_budget" in b:
        spec["budget"] = value(b, "error_budget")
    block = value(b, "check")
    if block is not None:
        # the rule table: the groups' families and pins as bound, a searched one at its default
        from chialu.verify.alu_ref import normalize_spec
        full = normalize_spec(dict(spec, check_en=True))
        modes = [(int(m["count"]), parse_format(str(m["format"]))) for m in full["modes"]]
        table, domains, variables = check_rules.check_elaboration(block, modes, list(full["ops"]), alu_layout(full))
        spec["check"] = check_rules.check_spec(table, domains, variables, b)
        checked = bool(table["groups"])
    elif checked is None and "check_en" in b:
        checked = True in vals(b, "check_en")
    spec["check_en"] = bool(checked)
    return spec


def _union_space(*spaces):
    """One space over several: a unit whose modes mix decimal and binary
    formats opens both families' sets under one slot (the slot's space is
    per kind, the structure's format decides which class realizes it)."""
    from adir.spaces import Space
    fams, seen = [], set()
    for sp in spaces:
        for f in sp.families:
            if f.name not in seen:
                seen.add(f.name)
                fams.append(f)
    return Space(fams, free_form_allowed=False)


def core_slots(modes, ops, classes, families, approx: bool, bcd: bool, width: int) -> dict:
    """The component slots of the core: one family space per op class
    and structure kind the modes and ops need. A unit with BCD modes
    beside binary ones opens the union of the decimal and binary spaces
    of a kind; generators.families_of gives each structure a default of
    its format's class. The slots hold every family of their space; the
    behavior rules (chialu.behavior_rules.prune_slot) remove, with a
    reason, the selectors of an exact unit (the truncated and the
    logarithmic multiplier, the approximate adder, which change the
    computed function and belong to an approximate unit's space alone)
    and every family or member the bound contract excludes."""
    if approx:
        from chialu.spaces.approx_spaces import (approx_adder_space, approx_div_space,
                                                 approx_mul_space)
    if bcd:
        from chialu.spaces.decimal_spaces import (decimal_adder_space, decimal_div_space,
                                                  decimal_mul_space)
    binary_too = bcd and any(not isinstance(f, BCDFormat) for _, f in modes)

    def pick(approx_space, decimal_space, binary_space):
        if approx:
            return approx_space()
        if bcd and binary_too:
            return _union_space(binary_space(), decimal_space())
        return decimal_space() if bcd else binary_space()
    slots = {}
    if classes & {"arith", "select", "div", "convert"}:
        slots["adder"] = pick(lambda: approx_adder_space(), lambda: decimal_adder_space(), cpa_space)
    if "mul" in classes:
        slots["multiplier"] = pick(lambda: approx_mul_space(width), lambda: decimal_mul_space(), lambda: mul_space(width))
    if "div" in classes:
        slots["divider"] = pick(lambda: approx_div_space(), lambda: decimal_div_space(), div_space)
    if "shift" in classes:
        slots["shifter"] = shifter_space()
    if {"popcount", "clz", "ctz"} & set(ops):
        from chialu.spaces.shift_simd_spaces import bitcount_space
        slots["bitcount"] = bitcount_space()
    if len(modes) > 1:
        from chialu.spaces.shift_simd_spaces import subword_space
        slots["subword"] = subword_space()
    if "fp" in classes or "float" in families or "block" in families:
        fmant = max([f.man_bits for _, f in modes if isinstance(f, (FloatFormat, X87Format))]
                    + [f.elem.man_bits for _, f in modes
                       if isinstance(f, BlockFormat) and isinstance(f.elem, FloatFormat)] + [0])
        fused = {"fmadd", "fmsub", "fnmsub", "fnmadd"} & set(ops)     # the separate family computes them
        if {"fadd", "fsub", "fcmp", "fmin", "fmax"} & set(ops) or fused:   # through the two slots (sequential)
            slots["fp_adder"] = fp_add_space()
        if "fmul" in ops or fused:
            slots["fp_multiplier"] = fp_mul_space(max(fmant, 1))
        if {"fadd", "fsub", "fmul"} & set(ops) or fused:
            # the multiply-add organization of a float mode: separate structures on the two slots above, or one
            # fused datapath, under which those two slots' variables of the mode are inactive
            slots["fp_fma"] = fp_fma_space(max(fmant, 1))
        if {"fdiv", "fsqrt"} & set(ops):
            slots["fp_divider"] = fp_div_space()
    if "posit" in families:
        from chialu.spaces.dsp_posit_spaces import posit_unit_space
        slots["posit_unit"] = posit_unit_space()
    if any(is_cvt(op) for op in ops):
        from chialu.spaces.fp_spaces import fp_cvt_space
        slots["converter"] = fp_cvt_space()
    if {"and", "or", "xor", "not", "fabs", "fneg"} & set(ops):
        from chialu.spaces.misc_spaces import logic_space
        slots["logic"] = logic_space()
    if {"min", "max", "cmp"} & set(ops):
        from chialu.spaces.adder_spaces import comparator_space
        slots["comparator"] = comparator_space()
    if {"fcmp", "fmin", "fmax"} & set(ops):
        from chialu.spaces.fp_spaces import fp_cmp_space
        slots["fp_comparator"] = fp_cmp_space()
    if "float" in families:
        from chialu.spaces.misc_spaces import rounder_space, unpacker_space
        slots["rounder"] = rounder_space()
        slots["unpacker"] = unpacker_space()
    return slots


def core_families(slots: dict) -> list:
    """The core's physical partitionings, each opening its slots. The
    time-shared `merged_mul_div` (the divider reusing the multiplier over
    cycles) and the streaming `online_msdf_core` are deferred with the
    single-cycle scope (docs/deferred-families.md). Every partitioning
    computes the same ops (behavior neutral): the sharing and the
    internal representation change no result."""
    from adir.spaces import Family
    from chialu.spaces.redundant_spaces import rns_space, signed_digit_space
    rns_components = {"channels": rns_space()}
    if "adder" in slots:
        rns_components["adder"] = slots["adder"]
    return [
        Family("unit_per_class", behavior="neutral", components=dict(slots),
               doc="one unit per op class, shared operand routing"),
        Family("redundant_internal", behavior="neutral", components=dict(slots, representation=signed_digit_space()),
               doc="operands converted to a redundant form at entry, carry-free ops inside, "
                   "one conversion at exit"),
        Family("rns_internal", behavior="neutral", components=rns_components,
               doc="forward-convert to residue channels, compute per modulus, reverse-convert "
                   "at the boundary"),
    ]


def interface_lines(lay: dict, checked: bool, check_port: bool) -> list:
    """The port list of the bound unit, one markdown line per port. A
    list rather than a string, so ADIR's composer leaves it to the
    `chialu_interface` PromptSource instead of printing it in the unit
    description."""
    ports = list(lay["core_in"]) + list(lay["chk_extra"])
    if check_port:
        ports.append(("check_en", "in", 1))
    ports += list(lay["core_out"])
    lines = []
    for p in ports:
        name, d, w = (p.name, p.direction, p.width) if hasattr(p, "name") else p
        lines.append(f"* `{name}`: {d}put, {w} bits")
    if checked:
        lines.append("* `check_err`: output, 1 bit")
    return lines


def elaborate(bindings: dict) -> Elaboration:
    from chialu.verify.alu_ref import normalize_spec
    spec = normalize_spec(spec_from_bindings(bindings))
    from chialu.verify.reference_underflow import validate
    validate(spec)
    modes = [(m["count"], parse_format(str(m["format"]))) for m in vals(bindings, "modes")]
    ops = list(vals(bindings, "ops"))
    if not modes or not ops:
        raise BindError("chialu.ALU: modes and ops must be bound")
    families = {family_of(f) for _, f in modes}
    legal = legal_pairs(modes, ops, [mode.get("ops") for mode in spec["modes"]])
    for mi, (n, f) in enumerate(modes):
        for op in ops:
            tgt = cvt_target(op)
            if tgt is not None and isinstance(tgt, BlockFormat) \
                    and not isinstance(f, BlockFormat) and n % tgt.size:
                raise BindError(f"chialu.ALU: {op} in mode {mi} ({n}x{f.name}) needs a count "
                                f"that is a multiple of the block size {tgt.size}")
        if not any(i == mi for i, _ in legal):
            raise BindError(f"chialu.ALU: mode {mi} ({n}x{f.name}) serves none of the ops "
                            f"{ops} (section 4 of the spec)")
    for op in ops:
        if not any(o == op for _, o in legal):
            raise BindError(f"chialu.ALU: op {op!r} is legal in none of the modes "
                            f"{[f.name for _, f in modes]}")
    approx = value(bindings, "accuracy") == "approximate"
    block = value(bindings, "check")
    check_table, check_vars = None, []
    if block is not None:
        check_table, _domains, check_vars = check_rules.check_elaboration(block, modes, ops, alu_layout(spec))
        checked = bool(check_table["groups"])
    else:
        checked = True in vals(bindings, "check_en")
    if spec.get("flag_scope") == "per_operation" and True in vals(bindings, "check_flags"):
        raise BindError("chialu.ALU: flag_scope per_operation with check_flags: the checker "
                        "duplicates one flag word per result, so the two conventions cannot "
                        "both hold")
    exact_modes = checked_modes(spec)
    if approx and checked and not exact_modes:
        raise BindError("chialu.ALU: check_en with accuracy: approximate: an approximate core "
                        "has no unique correct output to check against (under accuracy_ctl runtime "
                        "a mode whose error_budget is {bit_exact: true} does, and the checker checks "
                        "that mode alone)")
    if approx and spec.get("accuracy_ctl") == "runtime":
        budgets = value(bindings, "error_budget") or []
        n_modes = len(spec.get("accuracy_mode") or ())
        if not isinstance(budgets, (list, tuple)) or len(budgets) != n_modes:
            raise BindError(f"chialu.ALU: accuracy_ctl runtime with accuracy_modes {n_modes}: "
                            f"error_budget is a list of {n_modes} budgets, one per mode in mode order")
    classes = {op_class(op) for op in ops}
    width = max(f.width for _, f in modes)
    bcd = any(isinstance(f, BCDFormat) for _, f in modes)
    lay = alu_layout(spec)
    # yaml_behav_checker, the option half: a unit option whose value the bound contract contradicts is
    # rejected here, before any space compiles or any artifact renders (docs/behav_checker_plan.md)
    from chialu import behavior_rules as BR
    problems = BR.check_options(spec)
    xb = bindings.get("x_form")
    if xb is not None and xb.time == "search":
        for form in xb.domain.members():
            problems.extend(BR.check_options({**spec, "x_form": form}))
    if problems:
        raise BindError("chialu.ALU: " + "; ".join(problems))
    slots = core_slots(modes, ops, classes, families, approx, bcd, width)
    fams = core_families(slots)
    from chialu.targets.rtl.alu_seed import structure_manifest
    manifest = structure_manifest(spec)
    index_sets = manifest.index_sets()
    variables = [Variable("core.family", Enum(tuple(f.name for f in fams)), FIXED_OR_SEARCH,
                          doc="the core's physical partitioning")]
    users: dict = {}
    for f in fams:
        for slot, space in f.components.items():
            users.setdefault(slot, [space, []])[1].append(f.name)
    # plan_behav_checker: every slot's compiled variables pass the behavior rules, which remove (with a reason
    # kept in the domain) the families and members the bound contract excludes, per structure index where a
    # per-mode rule differs across the slot's modes
    report = BR.Report()
    for slot, (space, fam_names) in users.items():
        when = ("core.family", tuple(fam_names))
        key = f"structures:{slot}"
        if slot in ("fp_adder", "fp_multiplier") and key in index_sets and "structures:fp_fma" in index_sets:
            # the float adder and multiplier of a mode exist as structures of their own under the mode's
            # separate_multiplier_and_adder alone; a fused family closes both slots there (the fp_fma slot itself
            # opens under the core families, so the condition chains)
            when = ("core.fp_fma.*.family", ("separate_multiplier_and_adder",))
        if key in index_sets:
            slot_vars = space.variables(f"core.{slot}.*", FIXED_OR_SEARCH, indexed_by=key, when=when)
            slot_vars = BR.prune_slot(slot, space, f"core.{slot}.*", slot_vars, spec, index_sets[key], report)
            prefix = f"core.{slot}.*"
        else:
            slot_vars = space.variables(f"core.{slot}", FIXED_OR_SEARCH, when=when)
            slot_vars = BR.prune_slot(slot, space, f"core.{slot}", slot_vars, spec, None, report)
            prefix = f"core.{slot}"
        from chialu.modules.space_conditions import constrain
        variables += constrain(space, prefix, slot_vars, kind=slot, modes=modes, spec=spec,
                               independent=value(bindings, "search_geometry", "general") == "independent_modes")
    # Resolve cross-slot member conditions against compiled templates and static controls.
    # A sibling the unit does not compile is a static exclusion.
    variables = BR.bind_member_conditions(variables, report, available=("x_form",))
    # the menu: the slots' families less the ones the rules exclude at every structure of the slot
    family_menu = {}
    for slot, (space, _fam_names) in users.items():
        gone = report.menu_excluded.get(f"core.{slot}.*" if f"structures:{slot}" in index_sets else f"core.{slot}", {})
        family_menu[slot] = [{"family": f.name, "doc": f.doc, "choices": list(f.design_choices)}
                             for f in space.families if f.name not in gone]
    if block is not None:
        variables += check_vars
    elif checked:
        variables += checker_variables()
    if "div" in classes:
        variables.append(var("quotient_semantics", Enum(("truncate_zero", "floor")), FIXED_OR_RUNTIME,
                             doc="truncate_zero: every division op truncates; floor: every one "
                                 "floors; both provisioned: quot/rem truncate and div/mod floor"))
    names = ["tb.sv", "vectors.hex"] + ([] if approx else ["expected.hex"]) \
        + (["fault_tb.sv", "masks.hex", "check_manifest.json"] if checked else []) + ["spec.json"]
    index_sets["verify_files"] = names
    from chialu.targets.rtl.alu_seed import member_names
    index_sets["rtl_members"] = member_names(manifest)      # the multi-file seed (artifacts.core.indexed_by)
    check_port = len(vals(bindings, "check_en")) > 1
    info = {"unit": "alu", "top": "alu_core", "spec": spec,
            "interface": interface_lines(lay, checked, check_port),
            "manifest": manifest.to_json(), "families": family_menu,
            "checked": checked, "approximate": approx, "check": check_table,
            "prompt_omit": omitted_options([f for _, f in modes], ops, vals(bindings, "rounding"),
                                           checked, value(bindings, "flags", ()) or (), "alu"),
            "behavior_report": report.to_json()}
    text = report.prompt_text()
    if text:
        info["behavior_rules"] = text          # a string: the composer prints it in the unit section
    return Elaboration(index_sets, variables, info)


def verify_variables(with_masks: bool = True, masks_when=("check_en", True)) -> list:
    out = [var("verify.n_random", Range(1, 10_000_000), FIXED,
               doc="random vectors of the conformance testbench"),
           var("verify.seed", Range(0, 2 ** 31 - 1), FIXED, doc="the stimulus seed")]
    if with_masks:
        out.append(var("verify.n_random_masks", Range(1, 10_000_000), FIXED, when=masks_when,
                       doc="random fault masks of the fault harness"))
    return out


ALU = Template(
    name="chialu.ALU",
    variables=[
        var("modes", Struct(_validate_mode, "{count: <int>, format: <format>, ops?: [<operation>]}"), FIXED_OR_RUNTIME,
            doc="the (count, format) modes the datapath serves; runtime: a `mode` port selects"),
        var("ops", Struct(_validate_op, "op name or cvt(<format>)"), FIXED_OR_RUNTIME,
            doc="the op set; legality per mode follows the format family; runtime: an `op` port"),
        var("accuracy", Enum(("exact", "approximate")), FIXED,
            requires={"approximate": ["error_bound"]},
            doc="approximate drops the bit-exact gate and needs an error budget and a bound on it"),
        var("error_budget", Struct(_validate_budget, "{max_ulp | max_abs | error_rate | med | nmed | mred: <bound>}"),
            FIXED, when=("accuracy", "approximate"),
            doc="the accuracy budget of an approximate core; under accuracy_ctl runtime, one budget per "
                "accuracy mode in mode order, a mode whose budget is {bit_exact: true} computing the exact result"),
        var("accuracy_ctl", Enum(("static", "runtime")), FIXED, when=("accuracy", "approximate"),
            doc="where the approximate structures' operating mode is set: static (one point per structure, "
                "named in its module comment) or runtime (an accuracy_mode_sel port selects it per operation)"),
        var("accuracy_modes", Range(2, 8), FIXED, when=("accuracy_ctl", "runtime"),
            doc="the accuracy modes the port selects, mode 0 the coarsest and the last the most accurate; "
                "a structure with fewer modes of its own maps the selections above its top mode onto it"),
        var("check_en", Bool(), FIXED_OR_RUNTIME,
            doc="the one-rule spelling of the checker: fixed true (the `checker.*` family over every op), "
                "fixed false (absent), runtime (a port); a `check` block replaces it"),
        var("realization", Enum(("library", "behavioral")), FIXED,
            doc="how the seed realizes a declared family: from the family library (its module instantiated, "
                "named in the unit's comment), or as the behavioral text the unit would have without a "
                "library module (the library ablation of docs/evaluation-plan.md section 6; the review then "
                "judges the text alone)"),
        var("check", Struct(_validate_check, "{default: {detect}, rules: [{name, formats, ops, detect, choices, fallback}], "
                                             "fallback, checker_choices}"), FIXED,
            doc="the check specification: per (format, op) whether the result is checked and how well "
                "(docs/checker-spec-plan.md); a rule's `detect` states the bound (random_alias, single_bit) or `none`, "
                "its `choices` restricts the checker families and pins, `fallback` decides an op the code does not "
                "cover (duplicate | none | error); the search chooses one family per rule group under check.<rule>.*"),
        clock_variable(),
        *option_variables(),
        var("search_geometry", Enum(("general", "independent_modes")), FIXED,
            doc="general admits explicit shared geometries; independent_modes bounds sampled nested components "
                "by the smallest mode and remainder width, before sharing schemes are applied"),
        var("x_form", X_FORM, FIXED_OR_SEARCH,
            doc="the form of a float mode's unrounded X between the producers and the rounder: exact (the "
                "multiplier's 2p-bit product, the adder's full window) or guard_round_sticky (p + 3 significand "
                "bits with the sticky and an exponent of exp_bits + 3, as HardFloat's RawFloat and FPnew's rounding "
                "input), which serves float modes without conversion ops and without the stochastic rounding mode"),
        var("underflow_contract", Enum(("ieee", "fpnew_merged_16")), FIXED,
            doc="IEEE tininess, or the 16-bit FPnew/TransDot MERGED compatibility contract: "
                "RNE multiplication detects tininess before rounding in bf16 and fp8 lane 0; "
                "all other cases use tininess after rounding"),
        *convention_variables(),
        *verify_variables(masks_when=None),
    ],
    binding_defaults={"underflow_contract": {"fixed": "ieee"}, "search_geometry": {"fixed": "general"}, "check": {"fixed": None}, "check_en": {"fixed": False},
                      "check.*": {"search": "all"}, "verify.n_random_masks": {"fixed": 2000},
                      "realization": {"fixed": "library"},
                      "flag_scope": {"fixed": "per_result"}, "x_form": {"fixed": "exact"},
                      "fma_contract": {"fixed": "fused"}},
    elaborate=elaborate,
    generators={"core": generators.core_seed, "checker": generators.checker,
                "verify_bundle": generators.verify_bundle},
    seed_generator=generators.seed,
    seeds=PLANS,
    line_kinds=[STRUCTURE, MOVE],
    normalize_declaration=normalize_declaration,
    focus_map=focus_map,
    plan_doc=PLAN_DOC,
    plan_seed=plan_seed,
    replan=replan,
    presets=PRESETS,
    doc="unit class 1: y = op(a, b)",
)
