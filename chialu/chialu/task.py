"""The task statement of a chiALU run, rendered from the bound unit for
the system prompt's Task section (`task: {script: <path>/chialu/task.py}`
in the run file): the modes, the ops and the structure kinds, the clock
and the library, the goal and the gates, the checker or the error
budget, what varies and what a round does. One text per run; the
composer renders it once and puts it in every call's system text, so a
new target needs no hand-written statement."""
from __future__ import annotations

from typing import Optional


def render(instance) -> str:
    info = instance.elaboration.info or {}
    unit = str(info.get("unit") or "alu")
    spec = info.get("spec") or {}
    fixed = {b.name: b.value for b in instance.bindings.values() if b.time == "fixed"}
    runtime = {b.name: list(b.members) for b in instance.bindings.values() if b.time == "runtime"}
    paragraphs: list = []
    if unit == "alu":
        paragraphs += _alu(instance, info, spec, fixed, runtime)
    elif unit == "vec_dot_acc":
        paragraphs += _dot(spec, fixed)
    elif unit == "vec_sfu":
        paragraphs += _sfu(spec, fixed, runtime)
    else:
        paragraphs.append(f"The unit is `{unit}`; its modes are {_json_modes(spec.get('modes'))}.")
    paragraphs.append(_objective(instance, fixed))
    gates = _gates(instance, info, fixed)
    if gates:
        paragraphs.append(gates)
    reviewed = any(str((c or {}).get("metric", "")).startswith("review.") for c in (instance.raw.get("constraints") or [])
                   if isinstance(c, dict))
    declared = any(b.time == "search" for b in instance.bindings.values()) and \
        (instance.search.get("prompts") or {}).get("declarations", True) is not False
    paragraphs.append(_round(unit, _structured(instance), reviewed, declared))
    return "\n\n".join(p.strip() for p in paragraphs if p and p.strip()) + "\n"


# ------------------------------------------------------------- the ALU

def _structured(instance) -> bool:
    """A run whose program is the ALU's per-structure members under a declaration (the `rtl_members`
    family of the ALU graph): the library realizes a declared family and a VAR line re-renders it. A run
    over one plain program (the generic controls, a hand seed) edits text alone, and its statement says
    nothing of families, declarations or the review."""
    core = ((getattr(instance, "raw", None) or {}).get("artifacts") or {}).get("core") or {}
    return bool(core.get("indexed_by"))


def _domain_sources(instance) -> set:
    """The domain sources the run file's `search.prompts.sources` names.
    The composer writes one `context/<source>.md` per source, so a task
    statement that points the agent at a file names it only when the run
    carries that source; a generic-control run empties the list and its
    call directory holds none of them."""
    prompts = (instance.search.get("prompts") or {}) if hasattr(instance, "search") else {}
    return {str(s) for s in (prompts.get("sources") or [])}


def _source_note(have: set, *entries) -> str:
    """The parenthetical naming the context files the run carries, from
    (source, what it holds) pairs; the empty string when it carries none."""
    parts = [f"`context/{s}.md` {what}" for s, what in entries if s in have]
    return f" ({_words(parts)})" if parts else ""


def _alu(instance, info: dict, spec: dict, fixed: dict, runtime: dict) -> list:
    modes = spec.get("modes") or []
    kinds = {_format_kind(str(m.get("format", ""))) for m in modes}
    ops = list(spec.get("ops") or [])
    out = [f"The unit is an ALU serving {_modes_phrase(modes)}, selected per instruction by the `mode` port, "
           f"with the ops {_words([f'`{o}`' for o in ops])} (an op is legal in a mode where its format admits it)."]
    manifest = [m for m in (info.get("manifest") or []) if isinstance(m, dict)]
    skinds = sorted({str(m.get("kind")) for m in manifest if m.get("kind")})
    structured = _structured(instance)
    if skinds and structured:
        note = _source_note(_domain_sources(instance),
                            ("chialu_families", "lists the families per kind"),
                            ("chialu_timing", "their synthesized delay and area at this clock"),
                            ("chialu_structures", "the structures under the parent's declaration"))
        out.append(f"The ops need {len(manifest)} structures of the kinds {_words([f'`{k}`' for k in skinds])}, one per "
                   "(mode, lane, kind), each realized by a library family the declaration block names: a VAR line alone "
                   f"changes a structure's micro-architecture and the template re-renders it{note}. Structures of "
                   "different modes may share one physical datapath, named by `group=` in their STRUCTURE lines; which "
                   "families and which sharing give the smallest area under the clock and the shortest delay is the "
                   "question of the search.")
    notes = []
    if "float" in kinds:
        rnd = runtime.get("rounding") or ([fixed["rounding"]] if fixed.get("rounding") else [])
        rtxt = (f" under the rounding mode{'s' if len(rnd) != 1 else ''} {_words([f'`{r}`' for r in rnd])}"
                + (" selected at run time" if len(rnd) > 1 else "")) if rnd else ""
        notes.append(f"A float mode unpacks its operands, computes on the significands and rounds per lane and "
                     f"format{rtxt}" + ("; the significand adder and multiplier are integer structures with library "
                                        "families of their own" if structured else "")
                     + ". A wrong exponent bias, a missed subnormal or a wrong flag fails conformance.")
        if structured and ("integer" in kinds or "fixed-point" in kinds):
            notes.append("With integer and float modes together, the float significand add may share the integer "
                         "adders' carry-propagate adder (the int+fp group of the sharing schemes).")
    if "posit" in kinds:
        notes.append("A posit mode decodes the regime, the exponent and the fraction before the significand arithmetic "
                     "and encodes after it; the posit unit itself stays inline in the top, and the adder and multiplier "
                     "behind it are structures a plan can share with the other modes.")
    if "block" in kinds:
        notes.append("A block mode applies one shared scale to the elements of a block; the block quantizer stays "
                     "inline in the top, and folding the lanes of one kind into a shared datapath carries most of the area.")
    if "decimal" in kinds:
        notes.append("A decimal mode computes on BCD digits with the decimal families.")
    if any(str(o).startswith("cvt(") for o in ops):
        notes.append("The conversions among the formats round under the unit's rounding mode; a plan can fold the "
                     "converters into one internal-format datapath.")
    flags = fixed.get("flags") or spec.get("flags") or []
    if flags:
        notes.append(f"The `flags` output carries {_words([f'`{f}`' for f in flags])}, in that order, and is checked bit-exact.")
    if fixed.get("underflow_contract") == "fpnew_merged_16":
        notes.append("Preserve the reference's `fpnew_merged_16` underflow contract: for RNE fmul, "
                     "bf16 and the lower fp8 lane detect tininess before rounding; fp16, the upper "
                     "fp8 lane and all other operations/rounding modes detect it after rounding with "
                     "unbounded exponent. This explicitly preserves the MERGED reference's narrow-lane "
                     "underflow bug. The numerical results are unchanged; underflow still requires inexactness.")
    if fixed.get("accuracy") == "approximate":
        budget = fixed.get("error_budget") or {}
        notes.append("The unit is approximate: the conformance judge accepts any result within the error budget"
                     + (f" ({_budget(budget)})" if budget else "")
                     + " over the random vectors on every mode, so a rewrite may truncate columns, drop carries or "
                       "replace a multiplier by a logarithmic one as long as every mode stays within the budget.")
    out += notes
    return out


def _dot(spec: dict, fixed: dict) -> list:
    modes = spec.get("modes") or []
    parts = []
    for m in modes:
        parts.append(f"{m.get('elements')} x `{m.get('format_ab')}` products"
                     + (f" with {_an(str(m.get('format_c')))} `{m.get('format_c')}` addend" if m.get("format_c") else "")
                     + f" into `{m.get('format_d')}`")
    fused = str(spec.get("dot_contract") or "") == "fused"
    overflow = {"saturate": "saturates", "wrap": "wraps"}.get(str(spec.get("overflow") or "saturate"), str(spec.get("overflow")))
    out = [f"The unit is a vector dot-product accumulator: {_words(parts)}"
           + (", the products and the addend summed in one fused rounding" if fused else "")
           + f"; an integer mode reduces exactly and {overflow} on overflow, "
             "a float mode aligns the products and the addend before one reduction.",
           "The seed is one behavioral module; a rewrite chooses the multiplier tree, the reduction (a carry-save "
           "tree, a binary tree, a chain) and the alignment scheme within the EVOLVE region."]
    return out


def _sfu(spec: dict, fixed: dict, runtime: dict) -> list:
    modes = spec.get("modes") or []
    funcs = runtime.get("functions") or spec.get("functions") or []
    budget = fixed.get("error_budget") or spec.get("budget") or {}
    out = [f"The unit is a vector special-function unit: {_modes_phrase(modes)} evaluate one of "
           f"{_words([f'`{f}`' for f in funcs])} per instruction"
           + (f" within {_budget(budget)}" if budget else "") + ".",
           "The seed holds one table per function and lane; a rewrite may share a table across the lanes, fold the "
           "functions into a range reduction with a small polynomial, or keep a table for the hard cases and compute "
           "the rest, as long as every lane stays within the budget over every input pattern."]
    return out


# ------------------------------------------------------------- shared parts

def _objective(instance, fixed: dict) -> str:
    clock = fixed.get("clock_ps")
    pdk = _pdk(instance)
    g = instance.goal
    from chialu.timing import least_delay
    if clock and least_delay(instance):
        where = (f" on {pdk}" if pdk else "") + (f", mapping every candidate for its least delay (a {int(clock)} ps "
                                                 "target no design reaches; there is no timing constraint)")
    else:
        where = (f" on {pdk}" if pdk else "") + (f" with a {int(clock)} ps ({int(clock) / 1000:g} ns) timing target" if clock else "")
    if g.kind == "pareto":
        metrics = _words([f"`{e.text}`" for _, e in g.levels])
        goal = f"the goal is Pareto over {metrics}"
    else:
        d, e = g.levels[0]
        goal = f"the goal is to {d} `{e.text}`"
    infeasible = {"slack": "an infeasible candidate ranks below every feasible one, by its constraint slack",
                  "zero": "an infeasible candidate scores 0"}.get(str(g.infeasible), f"infeasible: {g.infeasible}")
    rule = ""
    if g.score_rule == "ratio_to_seed":
        rule = (" The score is the ratio to the seed, the smaller ratio where there are two, so a candidate scores "
                f"above 1.0 only where it beats the seed on every metric; {infeasible}.")
    return f"Synthesis runs{where}; {goal}.{rule}"


def _gates(instance, info: dict, fixed: dict) -> str:
    texts = [c.text for c in instance.constraints]
    steps = []
    if any(t.startswith("lint.") for t in texts):
        steps.append("lint")
    if any(t.startswith("conformance.") for t in texts):
        steps.append("the error budget over the random vectors" if fixed.get("accuracy") == "approximate"
                     else "bit-exact conformance against the reference model")
    if any(t.startswith("fault.") for t in texts):
        alias = next((t.split("<=")[-1].strip() for t in texts if t.startswith("fault.alias_rate")), "")
        fam = _checker_family(info)
        steps.append(f"the fault campaign of the concurrent checker ({fam}), which must detect every injected fault"
                     + (f" at an alias rate at most {alias}" if alias else ""))
    if any("abc_delay_ps <=" in t for t in texts):
        steps.append("synthesis under the clock")
    if any(t.startswith("review.") for t in texts):
        steps.append("the review, which reads the modules against the families they declare and "
                     "tolerates one that does not realize its own")
    if not steps:
        return ""
    return "Every candidate passes " + _words(steps) + "; a failed gate rejects the candidate and its measurements come back as feedback."


def _round(unit: str, structured: bool = True, reviewed: bool = True, declared: bool = True) -> str:
    if unit == "alu" and structured:
        return ("A round edits one unit module, regroups the structures in the declaration block, or declares other "
                "families"
                + ("; the review reads the result against the families it declares, and a second "
                   "module whose text does not realize the family it names rejects the candidate. " if reviewed else ". ")
                + "What has already been tried in a region, with the lines it replaced and the "
                "reason, is in `history/<region>.md`, named for the mutable region and not for any "
                "file on disk -- the program is one file holding every unit, and `regions.md` lists "
                "the regions it is made of; read a region's history before you change it again.")
    if unit == "alu":
        return ("A round rewrites the modules within their EVOLVE regions and keeps the top's interface and its exact "
                "behavior. What has already been tried in a region is in `history/<region>.md`, and `regions.md` "
                "lists the regions the program is made of.")
    if not declared:
        return "A round rewrites the program within its EVOLVE region and keeps the top's interface and its exact behavior."
    return "A round rewrites the module within its EVOLVE region and keeps the interface and the declaration block consistent with the text."


def _checker_family(info: dict) -> str:
    check = info.get("check") or {}
    fams = []
    for g in check.get("groups") or []:
        for e in g.get("entries") or []:
            f = str(e.get("family") or "")
            if f and f not in fams:
                mod = e.get("modulus")
                fams.append(f"{f.replace('_', ' ')}" + (f" modulo {mod}" if mod else ""))
    return _words(fams) if fams else "as the check block specifies"


def _pdk(instance) -> str:
    for n in instance.graph.active:
        ni = instance.nodes.get(n)
        ins = getattr(ni, "inputs", {}) or {}
        i = ins.get("pdk")
        if i is not None and getattr(i, "literal", None):
            return str(i.literal)
    return ""


def _format_kind(name: str) -> str:
    try:
        from chialu.verify.formats import (BCDFormat, BlockFormat, FixedFormat, FloatFormat, IntFormat,
                                           PositFormat, X87Format, parse_format)
        f = parse_format(name)
    except Exception:  # noqa: BLE001
        return ""
    if isinstance(f, FixedFormat):
        return "fixed-point"
    if isinstance(f, BCDFormat):
        return "decimal"
    if isinstance(f, IntFormat):
        return "integer"
    if isinstance(f, (FloatFormat, X87Format)):
        return "float"
    if isinstance(f, PositFormat):
        return "posit"
    if isinstance(f, BlockFormat):
        return "block"
    return ""


def _modes_phrase(modes: list) -> str:
    parts = []
    for m in modes:
        if "count" in m:
            n = int(m.get("count") or 1)
            parts.append(f"{n} x `{m.get('format')}`" + (" lanes" if n > 1 else ""))
        else:
            parts.append(_json_modes([m]))
    return _words(parts) if parts else "no modes"


def _json_modes(modes) -> str:
    import json
    return json.dumps(modes, default=str)


def _budget(b: dict) -> str:
    names = {"mred": "mean relative error", "error_rate": "error rate", "max_ulp": "at most {} ulp",
             "max_abs": "maximum absolute error", "max_rel": "maximum relative error"}
    parts = []
    for k, v in b.items():
        n = names.get(k, k.replace("_", " "))
        parts.append(n.format(v) if "{}" in n else f"{n} at most {v}")
    return _words(parts)


def _an(word: str) -> str:
    """The indefinite article before a format name (`an int32`, `a bf16`)."""
    return "an" if word[:1].lower() in "aeiou" or word[:3].lower() in ("int", "uin", "fp1", "fp3", "fp6", "fp8", "fxs") else "a"


def _words(items: list) -> str:
    items = [str(x) for x in items if str(x)]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]
