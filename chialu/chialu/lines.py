"""chiALU's declaration line kinds: `STRUCTURE` (one physical structure
of the seed and the shared datapath that realizes it) and `MOVE` (a
rewrite applied from the move library)."""
from __future__ import annotations

from adir import LineKind
from adir.declaration import parse_fields


def parse_structure(tokens):
    if not tokens:
        raise ValueError("STRUCTURE needs an id")
    return parse_fields(tokens)


def check_structures(ctx, entries) -> tuple:
    """Every structure of the seed manifest is declared, every declared
    id is a structure of the seed, and the members of a group are
    compatible kinds."""
    from chialu.targets.rtl.structures import StructureManifest
    info = (ctx.elaboration.info or {})
    expected = {s["id"]: s for s in info.get("manifest") or []}
    declared = StructureManifest.from_fields(entries)
    problems = []
    unknown = [s.id for s in declared if expected and s.id not in expected]
    if unknown:
        problems.append(f"ids not in the seed manifest: {unknown[:6]}")
    missing = [i for i in expected if declared.get(i) is None]
    if missing:
        problems.append(f"structures of the seed not declared: {missing[:6]}")
    groups: dict = {}
    for s in declared:
        if s.group:
            groups.setdefault(s.group, []).append(s)
    from chialu.targets.rtl.structures import is_inline
    decl_vars = getattr(getattr(ctx, "declaration", None), "vars", None) or {}
    for g, members in groups.items():
        inline = [m.id for m in members if is_inline(m)]
        if inline:
            problems.append(f"group {g}: {inline[0]} is realized inline in the top and has no unit to share")
            continue
        try:
            declared.group_kind({m.kind for m in members})
        except ValueError as e:
            problems.append(f"group {g}: {e}")
            continue
        # one datapath realizes the members, so the members of one kind have one family
        # (fixed, declared, or the default)
        by_kind: dict = {}
        for m in members:
            fam = effective_family(ctx, m)
            if fam is not None:
                by_kind.setdefault(m.slot or m.kind, {}).setdefault(fam, []).append(m.id)
        for kind, fams in by_kind.items():
            if len(fams) > 1:
                problems.append(f"group {g}: its {kind} members have different families ("
                                + ", ".join(f"{ids[0]}: {f}" for f, ids in fams.items()) + ")")
    return (not problems, "; ".join(problems) if problems else "structures ok")


def effective_family(ctx, s):
    """The active, canonical family a structure's declaration selects."""
    from chialu.declaration_values import canonical_vars
    from chialu.plans import inactive_reason
    name = f"core.{s.slot or s.kind}.{s.index}.family"
    decl_vars = canonical_vars(ctx, getattr(getattr(ctx, "declaration", None), "vars", None) or {})
    if inactive_reason(ctx, name, decl_vars):
        return None
    if name in decl_vars:
        return decl_vars[name]
    b = ctx.bindings.get(name)
    if b is None:
        return None
    if b.time == "fixed":
        return b.value
    return b.domain.default() if b.time == "search" else None


def parse_move(tokens):
    if not tokens:
        raise ValueError("MOVE needs a move id")
    d = parse_fields(tokens)
    d["move"] = d.pop("_")[0]
    return d


def check_moves(ctx, entries) -> tuple:
    """A move id is looked up in the move library; an unknown id is kept
    as custom rather than rejected."""
    try:
        from chialu.moves import load_moves
        known = load_moves()
    except Exception:  # noqa: BLE001
        known = {}
    for e in entries:
        if known and e["move"] not in known:
            e["custom"] = True
    return (True, "moves recorded")


def _share_declaration(ctx, decl):
    """The block completed by the sharing plan: the members of a group
    (one physical datapath) share every decision any member of the
    same kind declares, so a family or a pin declared once per group
    reaches each structure's own variables. The block's own lines are
    kept; the copies exist for the check and the nodes."""
    from chialu.targets.rtl.structures import StructureManifest
    entries = []
    for kind, tokens in decl.lines:
        if kind == "STRUCTURE":
            try:
                entries.append(parse_structure(tokens))
            except ValueError:
                return decl
    if not entries:
        return decl
    declared = StructureManifest.from_fields(entries)
    groups: dict = {}
    for s in declared:
        if s.group:
            groups.setdefault(s.group, []).append(s)
    if not groups:
        return decl
    out = dict(decl.vars)
    bindings = ctx.bindings
    for members in groups.values():
        by_kind: dict = {}
        for s in members:
            by_kind.setdefault(s.slot or s.kind, []).append(s)
        for slot, ms in by_kind.items():
            if len(ms) < 2:
                continue
            prefixes = [f"core.{slot}.{m.index}." for m in ms]
            shared: dict = {}
            for name, v in decl.vars.items():
                for pre in prefixes:
                    if name.startswith(pre):
                        shared.setdefault(name[len(pre):], v)
            for suffix, v in shared.items():
                for pre in prefixes:
                    name = pre + suffix
                    b = bindings.get(name)
                    if name in out or b is None or b.time != "search" or not b.domain.contains(v):
                        continue
                    # a choice reaches a member only under a family that has it
                    w = b.variable.when
                    if w is not None and w[0] == pre + "family":
                        fb = bindings.get(pre + "family")
                        fam = out.get(pre + "family", fb.value if fb is not None and fb.time == "fixed"
                                      else (fb.domain.default() if fb is not None else None))
                        if not b.variable.condition_holds(fam):
                            continue
                    out[name] = v
    d = type(decl)()
    d.present, d.raw, d.lines, d.vars = decl.present, list(decl.raw), list(decl.lines), out
    return d


def normalize_declaration(ctx, decl):
    """Canonicalize harmless spellings and omit only proved inactive choices."""
    from chialu.declaration_values import canonical_vars, NOTE_PREFIX
    from chialu.modules.generators import families_of, spec_of
    from chialu.targets.rtl.alu_seed import structure_manifest
    from copy import copy
    result = copy(decl)
    result.vars = canonical_vars(ctx, decl.vars)
    result = _share_declaration(ctx, result)
    spec = spec_of(ctx)
    if spec.get("unit") == "alu":
        selections = families_of(ctx, structure_manifest(spec), result.vars)
        result.vars = {k: v for k, v in result.vars.items() if k not in selections.ignored}
        program = getattr(getattr(ctx, "candidate", None), "program", "") or ""
        rendered_notes = [line[len(NOTE_PREFIX):] for line in program.splitlines() if line.startswith(NOTE_PREFIX)]
        result.notes = list(dict.fromkeys(getattr(decl, "notes", []) + selections.notes + rendered_notes))
    return result


STRUCTURE = LineKind("STRUCTURE", parse_structure, check_structures)
MOVE = LineKind("MOVE", parse_move, check_moves)
