"""chiALU's PromptSources for ADIR's composer, and the focus map of
its templates: the interface of the bound unit (static), the family
menu per structure kind (static), the structure table of the parent
(per round, the region in focus expanded), and the map from a
program's regions (the unit modules) to the variables they decide.
The composer owns the prompt; these supply data."""
from __future__ import annotations

from pathlib import Path

from adir import PromptSource

_CARD_CACHE: dict = {}      # (knowledge root, family) -> the cards named <family>.md, one per domain
_DIR_CACHE: dict = {}       # (knowledge root, slot) -> the domain directory of the slot's cards


def _interface(instance, archive, parent) -> str:
    info = instance.elaboration.info or {}
    text = info.get("interface", "")
    if isinstance(text, (list, tuple)):
        text = "\n".join(str(x) for x in text)
    return f"## Interface\n\n{text}\n" if text else ""


def _card_hits(root: Path, family: str) -> list:
    """The family cards named `<family>.md` under arch/<domain>/, relative
    to the knowledge root, in domain order. A variant card of the same
    name (arch/<domain>/<family>/<variant>.md) is not one of them."""
    key = (str(root), family)
    if key not in _CARD_CACHE:
        arch = root / "arch"
        hits = sorted(arch.glob(f"*/{family}.md")) if arch.is_dir() else []
        _CARD_CACHE[key] = [str(h.relative_to(root)) for h in hits]
    return _CARD_CACHE[key]


def slot_dir(instance, slot: str) -> str:
    """The knowledge domain directory of a slot: the directory that holds
    most of the cards its families name unambiguously ('' without
    cards)."""
    root = Path(instance.knowledge) if instance.knowledge else None
    if root is None:
        return ""
    key = (str(root), slot)
    if key not in _DIR_CACHE:
        count: dict = {}
        for f in ((instance.elaboration.info or {}).get("families") or {}).get(slot) or []:
            hits = _card_hits(root, f["family"])
            if len(hits) == 1:
                d = Path(hits[0]).parent.name
                count[d] = count.get(d, 0) + 1
        _DIR_CACHE[key] = max(count, key=count.get) if count else ""
    return _DIR_CACHE[key]


def card_of(instance, family: str, slot: str | None = None) -> str:
    """The knowledge card of a family, relative to the knowledge root,
    or ''. A name two domains share (the rounder and the unpacker both
    have a shared_per_lane) resolves to the card in the slot's own
    domain."""
    root = Path(instance.knowledge) if instance.knowledge else None
    if root is None:
        return ""
    hits = _card_hits(root, family)
    if not hits:
        return ""
    if len(hits) > 1 and slot:
        d = slot_dir(instance, slot)
        for h in hits:
            if Path(h).parent.name == d:
                return h
    return hits[0]


def var_prefix(s: dict) -> str:
    """`core.<slot>.<index>.` of a manifest entry: the index is the id
    without its kind and its lane (`m0.l0.adder` -> `m0`), since the
    lanes of one mode share their decisions."""
    from chialu.targets.rtl.structures import structure_index
    slot = s.get("slot") or s["kind"]
    return f"core.{slot}.{structure_index(s['id'], s['kind'])}."


def family_domain(instance, slot: str):
    """The families a structure of `slot` may declare under the bindings:
    the union, in domain order, of the domains of the slot's family
    variables (`core.<slot>.family`, or `core.<slot>.<index>.family` per
    structure of the manifest); a fixed binding contributes its value.
    None when the slot has no family binding."""
    manifest = (instance.elaboration.info or {}).get("manifest") or []
    # the dot accumulator and the SFU are one family at the core: their menu's slot is `core`
    names = ["core.family" if slot == "core" else f"core.{slot}.family"] \
        + [var_prefix(s) + "family" for s in manifest if (s.get("slot") or s["kind"]) == slot]
    members, fixed, found = [], [], False
    for n in dict.fromkeys(names):
        b = instance.bindings.get(n)
        if b is None:
            continue
        found = True
        if b.time == "fixed":
            fixed.append(b.value)
        elif b.time == "search" and b.domain.finite():
            for v in b.domain.members():
                if v not in members:
                    members.append(v)
    # the searched domains first, in their order (the first member is the default);
    # a value some instance is fixed to (a preset) follows when the search lacks it
    for v in fixed:
        if v not in members:
            members.append(v)
    return members if found else None


def _families(instance, archive, parent) -> str:
    """The family menu: per structure kind, the families a structure may
    declare under its binding, in domain order, each with its one-line
    doc and its card; the choices under a family are the card's and
    stand at their defaults unless declared."""
    menu = (instance.elaboration.info or {}).get("families") or {}
    if not menu:
        return ""
    from chialu.targets.rtl.families import has_module
    core_level = list(menu) == ["core"]
    L = ["## Families per structure kind", "",
         ("The unit's architecture is one family at the core, `core.family`, one of the families "
          "listed here in the order of its domain; the first is the default. A family's own "
          "choices and component families (`core.<choice>`, `core.<component>.family`) are named "
          "in its card and stand at their defaults unless declared. A family marked [library] is "
          "realized by construction: the seed instantiates the family library's module for it "
          "(chialu/targets/rtl/families, parameterized by the family's choices); the others are "
          "behavioral in the seed and are realized by the rewrite."
          if core_level else
          "A structure's family is `core.<kind>.<id>.family`, one of the families its binding "
          "admits, listed here in the order of its domain; the first is the default. A family's "
          "own choices (`core.<kind>.<id>.<choice>`) are named in its card and stand at their "
          "defaults unless declared. A family marked [library] is realized by construction: the "
          "seed's lane module instantiates the family library's module for it "
          "(chialu/targets/rtl/families, parameterized by the family's choices); the others are "
          "behavioral in the seed and are realized by the rewrite."), ""]
    from chialu.modules.generators import realization_of
    library_on = realization_of(instance) == "library"
    if not library_on:
        # the legend: no family carries the mark under `realization: behavioral`
        import re as _re
        L[2] = _re.sub(r"A family marked \[library\] is realized by construction:.*$",
                       "No family is marked [library]: the run's `realization` is behavioral, so the seed renders "
                       "every structure as the behavioral text of its function and the rewrite realizes the "
                       "declared family itself.", L[2], flags=_re.S)
    for slot, fams in menu.items():
        allowed = family_domain(instance, slot)
        if allowed is not None:
            order = {v: i for i, v in enumerate(allowed)}
            fams = sorted((f for f in fams if f["family"] in order), key=lambda f: order[f["family"]])
        if not fams:
            continue
        L.append(f"* `{slot}`:")
        for f in fams:
            card = card_of(instance, f["family"], slot)
            doc = (f.get("doc") or "").strip().replace("\n", " ")
            L.append(f"    * `{f['family']}`" + (f": {doc}" if doc else "")
                     + (f" [{card}]" if card else "")
                     + (" [library]" if library_on and has_module(slot.split(".")[-1], f["family"]) else "")
                     + (f" (choices: {', '.join(f['choices'][:8])}{', ...' if len(f['choices']) > 8 else ''})"
                        if f.get("choices") else ""))
    L.append("")
    return "\n".join(L)


def _family_of(instance, decl: dict, s: dict) -> tuple:
    """(family, declared?) of a structure under a declaration."""
    name = var_prefix(s) + "family"
    if name in decl:
        return decl[name], True
    b = instance.bindings.get(name)
    if b is None:
        return "", False
    if b.time == "fixed":
        return b.value, True
    return (b.domain.default() if b.time == "search" else ""), False


def manifest_of(instance, parent) -> list:
    """The seed manifest with the module (`sv=`) and the group each
    structure has under the parent's STRUCTURE lines: the elaboration
    knows the structures, the rendered seed assigns the modules."""
    from chialu.lines import parse_structure
    base = [dict(s) for s in (instance.elaboration.info or {}).get("manifest") or []]
    lines = ((parent or {}).get("declarations") or {}).get("lines") or []
    declared = {}
    for kind, tokens in lines:
        if kind != "STRUCTURE":
            continue
        try:
            e = parse_structure(list(tokens))
        except ValueError:
            continue
        sid = e["_"][0] if isinstance(e.get("_"), list) and e["_"] else None
        if sid:
            declared[sid] = e
    for s in base:
        e = declared.get(s["id"])
        if e:
            s["sv"] = e.get("sv") or s.get("sv") or ""
            s["group"] = e.get("group") or s.get("group") or ""
    return base


def completed_declaration(parent) -> dict:
    """The parent's declaration as the check completed it (the `decl.*`
    outputs of the declaration node: a group's members share what one
    declares, the rest at their defaults), else its VAR lines."""
    m = ((parent or {}).get("measurements") or {}).get("declaration") or {}
    v = m.get("value") if isinstance(m, dict) else None
    if isinstance(v, dict) and any(k.startswith("decl.") for k in v):
        return {k[5:]: x for k, x in v.items() if k.startswith("decl.") and not isinstance(x, list)}
    return ((parent or {}).get("declarations") or {}).get("vars") or {}


def _attribution(parent) -> dict:
    m = ((parent or {}).get("measurements") or {}).get("synth_unit") or {}
    v = m.get("value") if isinstance(m, dict) else None
    return (v or {}).get("attribution") or {}


def _row(instance, decl, attr, s) -> str:
    fam, declared = _family_of(instance, decl, s)
    a = attr.get(s["id"]) or {}
    num = ""
    if a.get("area_um2") is not None:
        num = f"; unit area {a['area_um2']:.4g} um2"
        if a.get("abc_delay_ps") is not None:
            num += f", delay {a['abc_delay_ps']:.4g} ps"
        if a.get("shared_with"):
            num += f" (shared with {', '.join(a['shared_with'][:3])})"
    return (f"* `{s['id']}`: {s['kind']}, mode {s['mode']} lane {s['lane']}, {s.get('format') or '-'}, "
            f"ops {', '.join(s.get('ops') or [])}"
            + (f", group `{s['group']}`" if s.get("group") else "")
            + (f"; family {fam}{'' if declared else ' (default)'}" if fam else "")
            + (f"; module `{s['sv']}`" if s.get("sv") else "") + num)


def _alternatives(instance, s: dict, fam: str) -> tuple:
    """(the other families the structure's own binding admits, fixed?)"""
    b = instance.bindings.get(var_prefix(s) + "family")
    if b is None:
        return [], False
    if b.time == "fixed":
        return [], True
    members = b.domain.members() if b.time == "search" and b.domain.finite() else []
    return [m for m in members if m != fam], False


def _structures(instance, archive, parent, focus=None) -> str:
    """The structure table of the seed under the parent's declaration:
    one physical structure per (mode, lane, op class) with its family,
    its module and its unit synthesis numbers. With a region in focus
    the structures that region realizes come first, with the family
    alternatives its binding admits and the card of each."""
    info = instance.elaboration.info or {}
    manifest = manifest_of(instance, parent)
    if not manifest:
        return ""
    decl = completed_declaration(parent)
    attr = _attribution(parent)
    L = ["## The structures of the seed", "",
         "One physical structure per (mode, lane, op class); a STRUCTURE line per structure in "
         "the declaration block, `group=` naming the shared datapath (one module) that realizes it. "
         "A family shown as default is undeclared.", ""]
    focused = [s for s in manifest if focus and s.get("sv") == focus]
    if focused:
        L += [f"### In focus: `{focus}`", ""]
        for s in focused:
            L.append(_row(instance, decl, attr, s))
            slot = s.get("slot") or s["kind"]
            fam, _ = _family_of(instance, decl, s)
            alts, fixed = _alternatives(instance, s, fam)
            if alts:
                L.append("    * alternatives: " + ", ".join(
                    f"`{m}`" + (f" [{card_of(instance, m, slot)}]" if card_of(instance, m, slot) else "")
                    for m in alts[:12]))
            elif fixed and fam:
                L.append(f"    * the family is fixed to `{fam}`; the choices under it are open")
            card = card_of(instance, fam, slot) if fam else ""
            if card:
                L.append(f"    * card of the current family: `{card}`")
        L += ["", "### The other structures", ""]
    for s in manifest:
        if s in focused:
            continue
        L.append(_row(instance, decl, attr, s))
    L.append("")
    return "\n".join(L)


def focus_map(ctx, parent) -> dict:
    """{module: [searched variable names]}: a program's mutable regions
    are the unit modules, each realizing one or more structures, whose
    variables are `core.<kind>.<id>.*`. One pass over the bindings: a
    name is bucketed by the structure prefix it starts with (a nested
    slot's variable belongs to the structure above it)."""
    manifest = manifest_of(ctx.instance, parent)
    if hasattr(ctx.bindings, "activate"):
        ctx.bindings.activate(dict(((parent or {}).get("declarations") or {}).get("vars") or {}))
    by_prefix: dict = {}        # variable prefix -> the modules realizing structures of that index
    out: dict = {}
    for s in manifest:
        sv = s.get("sv")
        if not sv:
            continue
        svs = by_prefix.setdefault(var_prefix(s), [])
        if sv not in svs:
            svs.append(sv)
        out.setdefault(sv, [])
    if not by_prefix:
        return out
    depth = max(p.count(".") for p in by_prefix)
    for n, b in ctx.bindings.items():
        if b.time != "search" or not n.startswith("core."):
            continue
        parts = n.split(".")
        for k in range(3, min(len(parts), depth + 1)):
            svs = by_prefix.get(".".join(parts[:k]) + ".")
            if svs is not None:
                for sv in svs:
                    if n not in out[sv]:
                        out[sv].append(n)
                break
    return out


INTERFACE = PromptSource("chialu_interface", _interface, static=True,
                         doc="the interface of the bound unit")
FAMILIES = PromptSource("chialu_families", _families, static=True,
                        doc="the families per structure kind under their bindings, with their cards")
STRUCTURES = PromptSource("chialu_structures", _structures,
                          doc="the seed's structure table under the parent's declaration, the region in focus expanded")


def _timing(instance, archive, parent) -> str:
    from chialu.timing import render
    return render(instance)


TIMING = PromptSource("chialu_timing", _timing, static=True,
                      doc="the library families' synthesized delay and area per structure kind at the run's clock "
                          "(chialu/synth), for pruning the families worth exploring")
