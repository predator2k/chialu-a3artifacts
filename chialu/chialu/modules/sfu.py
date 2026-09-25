"""chiALU library: unit class 2, vecC = sfu(vecA)
(docs/formats-and-options.md section 5).

`chialu.VecSFU` has `modes` of {count, format} over floats, custom
floats, posits and blocks (fixed one, runtime several through the
`mode` port), `functions` (the named fixed functions; fixed one or
runtime several, `fn_sel` selects), `reconfig_slots` writable-table
slots (each with its capacity contract slot.<i>.approx /
slot.<i>.segments), the rounding/daz/ftz/flags/sr_bits options, the
convention options and the accuracy budget. The architecture space is
the survey-derived approximation knowledge base (sfu_spaces), as the
core's family space (`core.*`).
"""
from __future__ import annotations

from adir import BindError, Elaboration, Enum, Range, Struct, Template
from chialu.lines import MOVE, normalize_declaration
from chialu.modules import generators
from chialu.modules.alu import _validate_budget, _validate_mode, verify_variables
from chialu.modules.common import (CONVENTIONS, FIXED, FIXED_OR_RUNTIME, FIXED_OR_SEARCH,
                                   clock_variable, convention_variables, omitted_options,
                                   option_variables, vals, value, var)
from chialu.papers import PRESETS
from chialu.spaces.sfu_spaces import sfu_approx_space
from chialu.verify.alu_ref import CONVENTION_NAMES
from chialu.verify.sfu_ref import FUNCTIONS

# check_flags, flag_scope and fma_contract are ALU options (a VecSFU has no checker flags, one flag word
# per result, and no multiply-add op)
SFU_CONVENTIONS = tuple(n for n in CONVENTION_NAMES if n not in ("check_flags", "flag_scope", "fma_contract"))


def spec_from_bindings(b: dict) -> dict:
    """The verify-layer spec of the bindings plus the slot bindings
    (slot.<i>.approx, slot.<i>.segments)."""
    spec = {"unit": "vec_sfu",
            "modes": [{"count": int(m["count"]), "format": str(m["format"])}
                      for m in vals(b, "modes")],
            "functions": [f for f in vals(b, "functions") if f != "none"]}
    for name in ("rounding", "daz_in", "ftz_out"):
        if name in b:
            spec[name] = list(vals(b, name))
    spec["flags"] = list(value(b, "flags", ()) or ())
    spec["sr_bits"] = value(b, "sr_bits")
    for name in SFU_CONVENTIONS:
        if name in b:
            spec[name] = value(b, name)
    n_slots = int(value(b, "reconfig_slots", 0) or 0)
    slots = []
    for i in range(n_slots):
        slots.append({"approx": value(b, f"slot.{i}.approx", "pwl"),
                      "segments": int(value(b, f"slot.{i}.segments", 8))})
    spec["reconfig_slots"] = n_slots
    spec["slots"] = slots
    from chialu.sfu_accuracy import from_bindings
    spec["sfu_accuracy"] = from_bindings(b)
    spec["budget"] = spec["sfu_accuracy"]["precision_target"]
    return spec


def elaborate(bindings: dict) -> Elaboration:
    from chialu.verify.sfu_ref import normalize_sfu_spec, sfu_layout, validate_sfu_modes
    spec = normalize_sfu_spec(spec_from_bindings(bindings))
    n_slots = spec["reconfig_slots"]
    # the slots' capacity contracts are bound after elaboration; the layout
    # here assumes the widest table (64 pwq segments) for the port widths
    spec["slots"] = [{"approx": "pwq", "segments": 64} for _ in range(n_slots)]
    lay = sfu_layout(spec)
    try:
        validate_sfu_modes(lay["modes"], spec)
    except ValueError as e:
        raise BindError(f"chialu.VecSFU: {e}") from None
    variables = []
    for i in range(n_slots):
        variables.append(var(f"slot.{i}.approx", Enum(("pwl", "pwq")), FIXED,
                             doc="evaluator form the slot guarantees"))
        variables.append(var(f"slot.{i}.segments", Range(8, 64, 8), FIXED,
                             doc="writable table capacity (uniform segments)"))
    space = sfu_approx_space(multi_fn=lay["total"] > 1)
    variables += space.variables("core", FIXED_OR_SEARCH)
    modes = lay["modes"]
    ports = list(lay["core_in"]) + list(lay["core_out"])
    info = {"unit": "vec_sfu", "top": "sfu_core", "spec": spec, "checked": False,
            "interface": [f"* `{p.name}`: {p.direction}put, {p.width} bits" for p in ports],
            "families": {"core": [{"family": f.name, "doc": f.doc, "choices": list(f.design_choices)}
                                  for f in space.families]},
            "prompt_omit": omitted_options([f for _, f in modes], spec["functions"],
                                           vals(bindings, "rounding"), False, spec["flags"], "vec_sfu")}
    return Elaboration({"verify_files": ["tb.sv", "vectors.hex", "spec.json"]}, variables, info)


def _sfu_convention_variables() -> list:
    return convention_variables(SFU_CONVENTIONS)


def _validate_sfu_budget(budget):
    if budget is None:
        return
    if not isinstance(budget, dict):
        raise BindError("SFU error_budget is a metric-to-bound mapping or null")
    _validate_budget(budget)


VEC_SFU = Template(
    name="chialu.VecSFU",
    variables=[
        var("modes", Struct(_validate_mode, "{count: <int>, format: <format>}"), FIXED_OR_RUNTIME,
            doc="the (count, format) modes over floats, posits and blocks; runtime: a `mode` port"),
        var("functions", Enum(FUNCTIONS), FIXED_OR_RUNTIME,
            doc="named fixed functions; fixed one (or none), runtime an fn_sel-selected subset"),
        var("reconfig_slots", Range(0, 8), FIXED,
            doc="anonymous writable-table slots; each slot.<i> then declares its capacity contract"),
        var("error_budget", Struct(_validate_sfu_budget, "{max_ulp | max_abs | ...: <bound>} or null"), FIXED,
            doc="precision target for implementation/parameter search; null uses the default 1 ULP target; fixed implementations report their error range"),
        clock_variable(),
        *option_variables(with_unary_dual=False, with_check_sr=False),
        *_sfu_convention_variables(),
        *verify_variables(with_masks=False),
    ],
    elaborate=elaborate,
    generators={"core": generators.core_seed, "verify_bundle": generators.verify_bundle},
    seed_generator=generators.seed,
    seeds=("baseline",),
    line_kinds=[MOVE],
    normalize_declaration=normalize_declaration,
    presets=PRESETS,
    binding_defaults={"error_budget": {"fixed": None}, "core.family": {"search": "all"},
                      "core.*": {"search": "all"}},
    doc="unit class 2: vecC = sfu(vecA)",
)
