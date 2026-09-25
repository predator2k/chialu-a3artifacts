"""chiALU library: unit class 3, vecD = vecC + vecA . vecB
(docs/formats-and-options.md section 6).

`chialu.VecDotAcc` has `modes` of {elements, format_ab, format_c,
format_d} (fixed one, runtime several through the `mode` port),
`accumulate` (false removes C and format_c), `check_en`, the
rounding/daz/ftz/flags/sr_bits options, `overflow` (integer and fixed
d: wrap or saturate), `dot_contract` (fused: exact products and sum, one
rounding; sequential: every product and addition rounded to format_d)
and the convention options. The multipliers and the reduction tree are
the core's family space (`core.*`).
"""
from __future__ import annotations

from adir import BindError, Bool, Elaboration, Enum, Struct, Template
from chialu.lines import MOVE, normalize_declaration
from chialu.modules import generators
from chialu.modules.alu import _validate_budget, verify_variables
from chialu.modules.common import (FIXED, FIXED_OR_RUNTIME, FIXED_OR_SEARCH, checker_variables,
                                   clock_variable, convention_variables, omitted_options,
                                   option_variables, vals, value, var)
from chialu.papers import PRESETS
from chialu.spaces.fma_dot_spaces import dot_acc_space
from chialu.verify.alu_ref import CONVENTION_NAMES

# flag_scope is an ALU option: a VecDotAcc flag word belongs to its output group. fma_contract is an ALU option
# too: the rounding of the unit's own products is dot_contract
DOT_CONVENTIONS = tuple(n for n in CONVENTION_NAMES if n not in ("flag_scope", "fma_contract"))
from chialu.verify.formats import parse_format


def _validate_dot_mode(m):
    if not isinstance(m, dict) or not {"elements", "format_ab", "format_d"} <= set(m) \
            or not set(m) <= {"elements", "format_ab", "format_c", "format_d", "scale_ab"}:
        raise BindError(f"mode {m!r}: needs {{elements, format_ab, format_c, format_d}}")
    if not isinstance(m["elements"], int) or m["elements"] < 1:
        raise BindError(f"mode {m!r}: elements must be a positive integer")
    for k in ("format_ab", "format_c", "format_d", "scale_ab"):
        if k in m:
            try:
                parse_format(str(m[k]))
            except ValueError as e:
                raise BindError(f"mode {m!r}: {k}: {e}") from None
    if m.get("scale_ab"):
        from chialu.verify.dot_ref import parse_modes
        try:
            parse_modes([m])
        except ValueError as error:
            raise BindError(f"mode {m!r}: {error}") from error


def _validate_dot_architecture(architecture):
    from chialu.verify.dot_arch_ref import selection
    try:
        selection({"dot_architecture": architecture})
    except ValueError as error:
        raise BindError(f"dot_architecture: {error}") from error


def _validate_dot_budget(budget):
    if budget is not None:
        _validate_budget(budget)


def spec_from_bindings(b: dict, checked=None) -> dict:
    spec = {"unit": "vec_dot_acc",
            "modes": [{k: (int(v) if k == "elements" else str(v)) for k, v in m.items()}
                      for m in vals(b, "modes")],
            "accumulate": bool(value(b, "accumulate", True))}
    for name in ("rounding", "daz_in", "ftz_out", "check_sr"):
        if name in b:
            spec[name] = list(vals(b, name))
    spec["flags"] = list(value(b, "flags", ()) or ())
    spec["sr_bits"] = value(b, "sr_bits")
    for name in CONVENTION_NAMES + ("overflow", "dot_contract"):
        if name in b:
            spec[name] = value(b, name)
    if spec.get("dot_contract") == "architecture":
        from chialu.verify.dot_arch_ref import resolved_architecture
        architecture = value(b, "dot_architecture")
        if architecture is None:
            raise BindError("architecture dot contract needs the fixed dot_architecture {family, pins}")
        spec["dot_architecture"] = resolved_architecture(architecture)
        budget = value(b, "error_budget")
        if budget is not None:
            spec["budget"] = budget
    if checked is None and "check_en" in b:
        checked = True in vals(b, "check_en")
    spec["check_en"] = bool(checked)
    return spec


def elaborate(bindings: dict) -> Elaboration:
    from chialu.verify.dot_ref import dot_layout, normalize_dot_spec, validate_dot_modes
    spec = normalize_dot_spec(spec_from_bindings(bindings))
    lay = dot_layout(spec)
    try:
        validate_dot_modes(lay["modes"], lay["accumulate"])
    except ValueError as e:
        raise BindError(f"chialu.VecDotAcc: {e}") from None
    acc = lay["accumulate"]
    for m in lay["modes"]:
        if m["elements"] == 1 and not acc and not hasattr(m["fab"], "size"):
            raise BindError("chialu.VecDotAcc: 1 element without accumulate is a plain "
                            "multiply; that is chialu.ALU (class 1)")
    checked = True in vals(bindings, "check_en")
    elem_bits = max(m["fab"].width for m in lay["modes"])
    space = dot_acc_space(elem_bits)
    variables = space.variables("core", FIXED_OR_SEARCH)
    if spec.get("dot_contract") == "architecture":
        from dataclasses import replace
        from adir.spaces import Space
        from chialu.variant_contracts import validate_pins
        family, pins = spec["dot_architecture"]["family"], spec["dot_architecture"]["pins"]
        validate_pins("dot", family, pins, elem_bits)
        selected = next(f for f in space.families if f.name == family)
        space = Space([selected], free_form_allowed=False)
        fixed = {"core.family": family, **{"core."+key: val for key, val in pins.items()}}
        variables = [replace(v, domain=Enum((fixed[v.name],))) if v.name in fixed else v
                     for v in space.variables("core", FIXED_OR_SEARCH)]
    # plan_behav_checker over the one core slot: the families and members the contract excludes leave the
    # domains with a reason, a numeric behavior selector (window_bits) is never searched, and a pin the
    # architecture contract fixed against a rule is rejected here (docs/behav_checker_plan.md)
    from chialu import behavior_rules as BR
    report = BR.Report()
    try:
        variables = BR.prune_slot("dot", space, "core", variables, spec, None, report)
        variables = BR.bind_member_conditions(variables, report)
    except BindError as e:
        raise BindError(f"chialu.VecDotAcc: {e.path}: {e.msg}") from None
    gone = report.menu_excluded.get("core", {})
    if checked:
        variables += checker_variables(comparator=False)   # the dot checker realizes residue alone
    names = ["tb.sv", "vectors.hex", "expected.hex"] + (["fault_tb.sv", "masks.hex"] if checked else []) \
        + ["spec.json"]
    ports = list(lay["core_in"]) + list(lay["chk_extra"]) + list(lay["core_out"])
    formats = [f for m in lay["modes"] for f in (m["fab"], m.get("fc"), m["fd"]) if f is not None]
    info = {"unit": "vec_dot_acc", "top": "dot_core", "spec": spec, "checked": checked,
            "interface": [f"* `{p.name}`: {p.direction}put, {p.width} bits" for p in ports],
            "families": {"core": [{"family": f.name, "doc": f.doc, "choices": list(f.design_choices)}
                                  for f in space.families if f.name not in gone]},
            "prompt_omit": omitted_options(formats, ["dot"], vals(bindings, "rounding"), checked,
                                           spec["flags"], "vec_dot_acc"),
            "behavior_report": report.to_json()}
    text = report.prompt_text()
    if text:
        info["behavior_rules"] = text
    return Elaboration({"verify_files": names}, variables, info)


VEC_DOT_ACC = Template(
    name="chialu.VecDotAcc",
    variables=[
        var("modes", Struct(_validate_dot_mode, "{elements: <int>, format_ab: <format>, "
                                                "format_c: <format>, format_d: <format>, scale_ab?: <float format>}"),
            FIXED_OR_RUNTIME, doc="the reductions the datapath serves; runtime: a `mode` port selects"),
        var("accumulate", Bool(), FIXED, doc="false ties C to 0 and drops the port and format_c"),
        var("check_en", Bool(), FIXED_OR_RUNTIME, doc="the residue checker"),
        clock_variable(),
        *option_variables(with_unary_dual=False),
        var("overflow", Enum(("wrap", "saturate")), FIXED, doc="integer and fixed-point d results"),
        # `architecture` needs `dot_architecture` bound, which its own `when` already carries: the
        # loader activates that variable under this value and a run file that leaves it out fails
        # there. A `requires` entry would instead demand a constraint row with
        # `satisfies: dot_architecture`, which discharges nothing.
        var("dot_contract", Enum(("fused", "sequential", "architecture")), FIXED,
            doc="fused and sequential unit contracts, or the explicit selected architecture's partial-rounding contract"),
        var("dot_architecture", Struct(_validate_dot_architecture, "{family: <dot family>, pins: {<pin>: <value>}}"),
            FIXED, when=("dot_contract", "architecture"),
            doc="the frozen algorithm contract; its specified architecture pins are fixed while other structural choices remain searchable"),
        var("error_budget", Struct(_validate_dot_budget, "null or {max_ulp | max_abs | error_rate | med | nmed | mred: <bound>}"),
            FIXED, when=("dot_contract", "architecture"),
            doc="null reports mathematical error without a limit; a mapping applies its limits, while the algorithm and flags remain bit-exact gates"),
        *convention_variables(DOT_CONVENTIONS),
        *verify_variables(),
    ],
    elaborate=elaborate,
    generators={"core": generators.core_seed, "checker": generators.checker,
                "verify_bundle": generators.verify_bundle},
    seed_generator=generators.seed,
    seeds=("baseline",),
    line_kinds=[MOVE],
    normalize_declaration=normalize_declaration,
    presets=PRESETS,
    doc="unit class 3: vecD = vecC + vecA . vecB",
)
