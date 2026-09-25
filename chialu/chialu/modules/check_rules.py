"""The check specification of chialu.ALU (docs/checker-spec-plan.md): a
rule table that states, per data format and op, whether the result is
checked and how well, in place of the unit-wide `check_en` plus
`checker.*` spelling (which stays as the one-rule form).

    check:
      fixed:
        default: {detect: none}
        fallback: duplicate
        checker_choices: [...]          # the list a rule without `choices` inherits
        rules:
          - name: int_arith
            formats: [int16]
            ops: [add, sub, adc, sbb, neg, abs, mul_wide]
            detect: {random_alias: 5.0e-2, single_bit: 1.0}
            choices:
              - {family: multi_residue, moduli_count: [2, 3], moduli_set: low_cost_2a_minus_1,
                 comparator.family: [direct_compare, two_rail_tree]}
              - {family: rns_redundant, base_moduli_count: 3, redundant_moduli: [1, 2]}
          - name: int_logic
            formats: [int16]
            ops: [and, or, xor, not, shl, shr_arith]
            detect: none

A rule selects the (format, op) pairs its `formats` and `ops` name; a
pair a later rule selects again takes the later rule; `default` covers
every pair no rule selects. `detect: none` leaves a pair unchecked; a
`detect` with bounds is a requirement (`random_alias`: the largest
`output_alias` admitted, `single_bit`: the smallest single-bit floor);
a rule with `choices` and no `detect` states no requirement, so its
numbers are reported and gate nothing. `choices` restricts the checker
space (one entry per family: its own pins, `comparator.*` and the
adder slots' pins by dotted path; a scalar fixes a pin, a list is the
set, an omitted pin opens the domain); `fallback` decides a pair the
chosen code does not cover (`duplicate`: a replica, `none`: unchecked,
legal without a requirement alone, `error`: the build fails).

The elaboration intersects each rule's declaration with the feasible
set (`feasible_families`), names the survivors as the variables
`check.<rule>.family` and `check.<rule>.<family>.<pin>` (the family
between the rule and the pin, so two entries never collide), opens the
adder slots of a family under `check.<rule>.<family>.<slot>.*`, and
fails the build with the model's reasons when nothing survives. The
run file need not bind them: the template defaults `check.*` to
`search: all`, so the search chooses one family per rule group and its
pins, and `chialu.eda.checker_gen` regenerates the checker from a
candidate's declaration (an ADIR generator that depends on a searched
variable is a node, design section 3.7).
"""
from __future__ import annotations

import re

from adir import BindError, Enum, Variable
from chialu.modules.common import FIXED_OR_SEARCH
from chialu.targets.rtl.alu_checker import (CHECKER_SLOTS, FALLBACKS, FAMILIES, REQUIREMENT_KEYS,
                                             feasibility)
from chialu.verify.formats import parse_format

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
BLOCK_KEYS = ("default", "rules", "fallback", "checker_choices")
RULE_KEYS = ("name", "formats", "ops", "detect", "choices", "fallback")
DEFAULT_KEYS = ("detect", "choices", "fallback")
PREFIX = "check"


# ---------------------------------------------------------------- validation (bind time, no unit context)

def _validate_detect(v, where: str):
    if v is None or v == "none":
        return
    if not isinstance(v, dict) or not v:
        raise BindError(f"{where}.detect: none, or a mapping over {REQUIREMENT_KEYS}")
    bad = set(v) - set(REQUIREMENT_KEYS)
    if bad:
        raise BindError(f"{where}.detect: unknown keys {sorted(bad)} (known: {REQUIREMENT_KEYS})")
    for k, x in v.items():
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not 0 <= float(x) <= 1:
            raise BindError(f"{where}.detect.{k}: a number in [0, 1]")


def _validate_choices(entries, where: str):
    if not isinstance(entries, (list, tuple)) or not entries:
        raise BindError(f"{where}: a nonempty list of entries, one per family")
    seen = set()
    for i, e in enumerate(entries):
        if not isinstance(e, dict) or "family" not in e:
            raise BindError(f"{where}[{i}]: a mapping with `family`")
        fam = e["family"]
        if fam not in FAMILIES:
            raise BindError(f"{where}[{i}].family: {fam!r} (one of {', '.join(FAMILIES)})")
        if fam in seen:
            raise BindError(f"{where}: family {fam!r} appears twice (an entry is identified by its family)")
        seen.add(fam)
        for k, v in e.items():
            if k == "family":
                continue
            if not isinstance(k, str) or not k:
                raise BindError(f"{where}[{i}]: pin names are strings")
            head = k.split(".", 1)[0]
            if "." in k and head not in CHECKER_SLOTS:
                raise BindError(f"{where}[{i}].{k}: a slot pin names one of {CHECKER_SLOTS}")
            if isinstance(v, (dict,)):
                raise BindError(f"{where}[{i}].{k}: a scalar or a list")


def _validate_fallback(v, where: str):
    if v not in FALLBACKS:
        raise BindError(f"{where}.fallback: {v!r} (one of {', '.join(FALLBACKS)})")


def validate_check(block):
    """The shape of a `check` block; None is the absent block (the legacy
    spelling decides the checking)."""
    if block is None:
        return
    if not isinstance(block, dict):
        raise BindError("check: a mapping {default, rules, fallback, checker_choices}")
    bad = set(block) - set(BLOCK_KEYS)
    if bad:
        raise BindError(f"check: unknown keys {sorted(bad)} (known: {BLOCK_KEYS})")
    if "fallback" in block:
        _validate_fallback(block["fallback"], "check")
    if "checker_choices" in block:
        _validate_choices(block["checker_choices"], "check.checker_choices")
    default = block.get("default")
    if default is not None:
        if not isinstance(default, dict):
            raise BindError("check.default: a mapping {detect, choices, fallback}")
        bad = set(default) - set(DEFAULT_KEYS)
        if bad:
            raise BindError(f"check.default: unknown keys {sorted(bad)}")
        _validate_detect(default.get("detect"), "check.default")
        if "choices" in default:
            _validate_choices(default["choices"], "check.default.choices")
        if "fallback" in default:
            _validate_fallback(default["fallback"], "check.default")
    rules = block.get("rules") or []
    if not isinstance(rules, (list, tuple)):
        raise BindError("check.rules: a list")
    names = set()
    for i, r in enumerate(rules):
        where = f"check.rules[{i}]"
        if not isinstance(r, dict):
            raise BindError(f"{where}: a mapping")
        bad = set(r) - set(RULE_KEYS)
        if bad:
            raise BindError(f"{where}: unknown keys {sorted(bad)} (known: {RULE_KEYS})")
        name = r.get("name")
        if not isinstance(name, str) or not NAME_RE.match(name) or name in ("default", "family"):
            raise BindError(f"{where}.name: an identifier other than `default` and `family`")
        if name in names:
            raise BindError(f"{where}.name: {name!r} is used twice")
        names.add(name)
        for key in ("formats", "ops"):
            v = r.get(key)
            if not isinstance(v, (list, tuple)) or not v or not all(isinstance(x, str) for x in v):
                raise BindError(f"{where}.{key}: a nonempty list of names")
        for f in r["formats"]:
            try:
                parse_format(f)
            except ValueError as e:
                raise BindError(f"{where}.formats: {e}") from None
        _validate_detect(r.get("detect"), where)
        if "choices" in r:
            _validate_choices(r["choices"], f"{where}.choices")
        if "fallback" in r:
            _validate_fallback(r["fallback"], where)
        if r.get("detect") is None and "choices" not in r and "checker_choices" not in block:
            pass    # every family, report only: legal


# ---------------------------------------------------------------- resolution against the unit

def resolve_check(block: dict, modes, ops, legal) -> dict:
    """The rule table against a bound unit: `modes` [(count, Format)],
    `ops` the op list, `legal` the legal (mode index, op) pairs. Returns
    {"fallback", "groups": [{name, pairs, detect, fallback, entries}],
    "unchecked": [pairs]}; `detect` is None for no requirement, a dict
    for a requirement; `entries` None opens every family."""
    validate_check(block)
    block = block or {}
    fallback = str(block.get("fallback", "duplicate"))
    inherited = block.get("checker_choices")
    by_name = {fmt.name: [] for _c, fmt in modes}
    for mi, (_c, fmt) in enumerate(modes):
        by_name[fmt.name].append(mi)
    legal = set(legal)
    owner: dict = {}
    rules = list(block.get("rules") or [])
    for r in rules:
        fmt_names = []
        for f in r["formats"]:
            name = parse_format(f).name
            if name not in by_name:
                raise BindError(f"check.rules[{r['name']}].formats: {f!r} is not a mode of the unit "
                                f"(modes: {', '.join(by_name)})")
            fmt_names.append(name)
        for op in r["ops"]:
            if op not in ops:
                raise BindError(f"check.rules[{r['name']}].ops: {op!r} is not an op of the unit (ops: {', '.join(ops)})")
        pairs = {(mi, op) for name in fmt_names for mi in by_name[name] for op in r["ops"] if (mi, op) in legal}
        if not pairs:
            raise BindError(f"check.rules[{r['name']}]: selects no legal (format, op) pair")
        for pr in pairs:
            owner[pr] = r["name"]
    default = dict(block.get("default") or {"detect": "none"})
    groups, unchecked = [], []
    for r in rules:
        pairs = sorted(pr for pr, n in owner.items() if n == r["name"])
        if not pairs:
            raise BindError(f"check.rules[{r['name']}]: every pair it selects is taken by a later rule")
        detect = r.get("detect")
        if detect == "none":
            unchecked += pairs
            continue
        groups.append({"name": r["name"], "pairs": pairs, "detect": dict(detect) if detect else None,
                       "fallback": str(r.get("fallback", fallback)),
                       "entries": [dict(e) for e in (r.get("choices") or inherited or [])] or None})
    rest = sorted(pr for pr in legal if pr not in owner)
    if rest:
        detect = default.get("detect", "none")
        if detect == "none" or detect is None and "choices" not in default and not inherited:
            unchecked += rest
        else:
            groups.append({"name": "default", "pairs": rest, "detect": dict(detect) if isinstance(detect, dict) else None,
                           "fallback": str(default.get("fallback", fallback)),
                           "entries": [dict(e) for e in (default.get("choices") or inherited or [])] or None})
    return {"fallback": fallback, "groups": groups, "unchecked": sorted(unchecked)}


def _entry_slot_pins(entries, family: str) -> dict:
    """The `<slot>.<path>` restrictions of the entry over `family`."""
    for e in entries or ():
        if e.get("family") == family:
            return {k: v for k, v in e.items() if "." in k and k.split(".", 1)[0] != "comparator"}
    return {}


def group_domains(group: dict, modes, lay) -> dict:
    """The narrowed domains of one group: the feasible families in
    declaration order, each with the union of its surviving own pins,
    comparator families and comparator pins, and the entry's slot
    restrictions. Nothing surviving is a build error naming the model's
    reasons."""
    pairs = [(modes[mi][1], op) for mi, op in group["pairs"]]
    lanes = {modes[mi][1].name: modes[mi][0] for mi, _op in group["pairs"]}
    dual = lay["d_w"] > 0 or lay["dual_in_y"]
    try:
        survivors, rejected = feasibility(pairs, group["detect"], group["fallback"], group["entries"],
                                          dual_possible=dual, lanes=lanes)
    except ValueError as e:
        raise BindError(f"check.rules[{group['name']}]: {e}") from None
    if not survivors:
        reasons = sorted({f"{p['family']}: {p['reject']}" for p in rejected})
        raise BindError(f"check.rules[{group['name']}]: no checker point meets the rule; "
                        + "; ".join(reasons[:6]) + (" ..." if len(reasons) > 6 else ""))
    order = [e["family"] for e in group["entries"]] if group["entries"] else list(FAMILIES)
    doms: dict = {"families": [], "own": {}, "comparator": {}, "comparator_pins": {}, "slots": {}}
    for p in survivors:
        f = p["family"]
        if f not in doms["own"]:
            doms["families"].append(f)
            doms["own"][f] = {}
            doms["comparator"][f] = []
            doms["comparator_pins"][f] = {}
            doms["slots"][f] = _entry_slot_pins(group["entries"], f)
        for k, v in p["pins"].items():
            vs = doms["own"][f].setdefault(k, [])
            if v not in vs:
                vs.append(v)
        if p["comparator"]:
            cf = p["comparator"]["family"]
            if cf not in doms["comparator"][f]:
                doms["comparator"][f].append(cf)
            pins = doms["comparator_pins"][f].setdefault(cf, {})
            for k, v in p["comparator"].items():
                if k == "family":
                    continue
                vs = pins.setdefault(k, [])
                if v not in vs:
                    vs.append(v)
            for k, allowed in (p.get("comparator_pins") or {}).items():
                vs = pins.setdefault(k, [])
                for v in allowed:
                    if v not in vs:
                        vs.append(v)
    doms["families"].sort(key=lambda f: order.index(f) if f in order else len(order))
    return doms


def group_variables(group: dict, doms: dict) -> list:
    """The ADIR variables of one group (docs/checker-spec-plan.md, "The
    variables ADIR sees"): the family, its own pins under the family's
    name, the comparator family and pins, and the adder slots' spaces
    narrowed by the entry."""
    from adir.spaces import Space
    from chialu.spaces.arith_spaces import cpa_space
    from chialu.spaces.checker_spaces import checker_space
    base = f"{PREFIX}.{group['name']}"
    fam_var = f"{base}.family"
    out = [Variable(fam_var, Enum(tuple(doms["families"])), FIXED_OR_SEARCH,
                    doc=f"the checker family of the check rule {group['name']}"
                        + (f" (detect {group['detect']})" if group["detect"] else " (no requirement: reported)"))]
    space = {f.name: f for f in checker_space().families}
    for f in doms["families"]:
        when = (fam_var, (f,))
        for pin, vals in doms["own"][f].items():
            out.append(Variable(f"{base}.{f}.{pin}", Enum(tuple(vals)), FIXED_OR_SEARCH, when=when,
                                doc=f"{pin} of {f} under the rule {group['name']}"))
        cmps = doms["comparator"].get(f) or []
        if cmps:
            cmp_var = f"{base}.{f}.comparator.family"
            out.append(Variable(cmp_var, Enum(tuple(cmps)), FIXED_OR_SEARCH, when=when,
                                doc=f"the comparator of {f} under the rule {group['name']}"))
            merged: dict = {}
            for cf, pins in (doms["comparator_pins"].get(f) or {}).items():
                for pin, vals in pins.items():
                    fams, union = merged.setdefault(pin, ([], []))
                    fams.append(cf)
                    for v in vals:
                        if v not in union:
                            union.append(v)
            for pin, (fams, union) in merged.items():
                out.append(Variable(f"{base}.{f}.comparator.{pin}", Enum(tuple(union)), FIXED_OR_SEARCH,
                                    when=(cmp_var, tuple(fams)), doc=f"{pin} of the comparator {', '.join(fams)}"))
        fam = space[f]
        restrictions = doms["slots"].get(f) or {}
        for slot, sub in fam.components.items():
            if slot == "comparator":
                continue
            prefix = f"{base}.{f}.{slot}"
            slot_vars = Space(list(sub.families), free_form_allowed=False).variables(prefix, FIXED_OR_SEARCH, when=when, max_depth=2)
            for v in slot_vars:
                key = v.name[len(base) + len(f) + 2:]          # `<slot>.<path>`
                if key in restrictions:
                    vals = restrictions[key]
                    vals = list(vals) if isinstance(vals, (list, tuple)) else [vals]
                    bad = [x for x in vals if not v.domain.contains(x)]
                    if bad:
                        raise BindError(f"check.rules[{group['name']}].choices[{f}].{key}: {bad} outside {v.domain.describe()}")
                    v = Variable(v.name, Enum(tuple(vals)), v.binding_times, when=v.when, doc=v.doc)
                out.append(v)
            unknown = [k for k in restrictions if k.split(".", 1)[0] == slot
                       and f"{base}.{f}.{k}" not in {v.name for v in slot_vars}]
            if unknown:
                raise BindError(f"check.rules[{group['name']}].choices[{f}]: {unknown} name no pin of the slot {slot!r} "
                                f"within two levels")
        bad_slots = sorted({k.split('.', 1)[0] for k in restrictions} - set(fam.components))
        if bad_slots:
            raise BindError(f"check.rules[{group['name']}].choices[{f}]: {bad_slots} are not slots of {f}")
    return out


def check_elaboration(block: dict, modes, ops, lay) -> tuple:
    """(table, per-group domains, variables) of a `check` block against a
    bound unit."""
    table = resolve_check(block, modes, ops, lay["legal"])
    domains, variables = {}, []
    for g in table["groups"]:
        d = group_domains(g, modes, lay)
        domains[g["name"]] = d
        variables += group_variables(g, d)
    return table, domains, variables


# ---------------------------------------------------------------- the spec record

def _bound(bindings, name):
    """(True, value) of a fixed binding, (False, None) otherwise."""
    b = bindings.get(name) if hasattr(bindings, "get") else None
    if b is not None and getattr(b, "time", None) == "fixed":
        return True, b.value
    return False, None


def check_spec(table: dict, domains: dict, variables: list, bindings, declared: dict | None = None) -> dict:
    """spec["check"] of a bound unit: every group with the family, own
    pins, comparator and slot records the generator reads. A fixed
    binding stands; a searched variable stands at its domain's default
    (the first member), which is what the seed declares; `declared`, the
    nested mapping of a candidate's `decl.check`, overrides both (the
    checker-generation node)."""
    declared = declared or {}
    by_name = {v.name: v for v in variables}
    groups = []
    for g in table["groups"]:
        base = f"{PREFIX}.{g['name']}"
        decl_g = declared.get(g["name"]) or {}

        def pick(name, default):
            parts = name[len(PREFIX) + 1:].split(".")     # <rule>.<...>
            cur = declared
            for p in parts:
                if not isinstance(cur, dict) or p not in cur:
                    cur = None
                    break
                cur = cur[p]
            if cur is not None and not isinstance(cur, dict):
                return cur
            fixed, v = _bound(bindings, name)
            return v if fixed else default
        del decl_g
        resolved = {}
        for v in [x for x in variables if x.name == f"{base}.family" or x.name.startswith(base + ".")]:
            if v.when is not None:
                parent, members = v.when
                if parent not in resolved or resolved[parent] not in members:
                    continue
            resolved[v.name] = pick(v.name, v.domain.default())
        family = resolved[f"{base}.family"]
        head = f"{base}.{family}."
        pins, comparator, slots = {}, {}, {}
        for name, val in resolved.items():
            if not name.startswith(head):
                continue
            key = name[len(head):]
            if key.startswith("comparator."):
                comparator[key[len("comparator."):]] = val
            elif "." in key:
                slot, path = key.split(".", 1)
                slots.setdefault(slot, {})[path] = val
            else:
                pins[key] = val
        groups.append({"name": g["name"], "pairs": [list(p) for p in g["pairs"]], "detect": g["detect"],
                       "fallback": g["fallback"], "family": family, "pins": pins,
                       "comparator": comparator or None, "slots": slots})
    return {"fallback": table["fallback"], "groups": groups, "unchecked": [list(p) for p in table["unchecked"]]}


def apply_declaration(spec: dict, declared: dict) -> dict:
    """spec["check"] with a candidate's `decl.check` mapping applied: the
    family of a group, its own pins, its comparator and its slot pins
    where the mapping names them (the mapping carries every active
    check variable of the candidate, declared or at its default)."""
    out = dict(spec)
    table = dict(spec["check"])
    groups = []
    for g in table["groups"]:
        d = (declared or {}).get(g["name"]) or {}
        g = dict(g)
        family = d.get("family", g["family"])
        under = d.get(family) if isinstance(d.get(family), dict) else {}
        if family != g["family"]:
            g.update(family=family, pins={}, comparator=None, slots={})
        pins = dict(g.get("pins") or {})
        comparator = dict(g.get("comparator") or {})
        slots = {k: dict(v) for k, v in (g.get("slots") or {}).items()}
        for k, v in under.items():
            if k == "comparator" and isinstance(v, dict):
                comparator.update(v)
            elif isinstance(v, dict):
                slots.setdefault(k, {}).update(_flatten(v))
            else:
                pins[k] = v
        g.update(pins=pins, comparator=comparator or None, slots=slots)
        groups.append(g)
    table["groups"] = groups
    out["check"] = table
    return out


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flatten(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out
