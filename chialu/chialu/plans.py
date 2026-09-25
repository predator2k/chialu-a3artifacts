"""The sharing plans a generated seed may follow: which seed structures
one physical datapath realizes, and which family each structure
declares. A plan name is what `search.seeds.generated` lists."""
from __future__ import annotations

from chialu.targets.rtl.structures import COMPATIBLE_KINDS, StructureManifest, is_inline

PLANS = ("baseline", "packed_banks", "per_position", "dedicated_speed", "fused_fma")

# family overrides of a plan: kind -> {variable suffix: value}; a value the
# structure's space does not offer is skipped
FAMILY_OVERRIDES = {
    "dedicated_speed": {
        "adder": {"family": "parallel_prefix", "topology": "kogge_stone"},
        "multiplier": {"family": "booth_recoded_parallel"},
        "fp_adder": {"family": "two_path"},
        "fp_multiplier": {"family": "round_fused_in_reduction"},
        "comparator": {"family": "prefix_comparator"},
    },
    "packed_banks": {"adder": {"family": "ripple_carry"},
                     "multiplier": {"family": "twin_precision_subword"},
                     "logic": {"family": "wide_gate_row"}},
    "per_position": {"logic": {"family": "wide_gate_row"}},
    # every float mode's fadd, fsub and fmul through one fused multiply-add datapath (the fp_fma slot's
    # classic_fma), which closes the mode's fp_adder and fp_multiplier slots; a unit without a float mode
    # renders as the baseline
    "fused_fma": {"fp_fma": {"family": "classic_fma"}},
}
# the kinds one physical datapath realizes for several structures under a plan
# (families.partition.validate_partition): a binary integer adder under the partitioned carry chain, a
# twin-precision multiplier, a wide gate row; per_position keeps replicated lanes, so only its gate rows share
SHARED_KINDS = {"packed_banks": ("adder", "multiplier", "logic"), "per_position": ("logic",)}
SUBWORD_FAMILY = {"packed_banks": "partitioned_carry_chain", "per_position": "replicated_lanes",
                  "dedicated_speed": "replicated_lanes", "baseline": "partitioned_carry_chain",
                  "fused_fma": "partitioned_carry_chain"}


def partition(manifest: StructureManifest, plan: str) -> list:
    """[(unit name, member ids)] of a plan over the seed's structures."""
    if plan not in PLANS:
        raise ValueError(f"unknown plan {plan!r} (plans: {PLANS})")
    slotted = [s for s in manifest if s.slot and not is_inline(s)]
    if plan in ("baseline", "dedicated_speed"):
        return [(s.id, (s.id,)) for s in slotted]
    if plan == "fused_fma":
        # one unit per structure, except that a float mode's fp_fma, fp_adder and fp_multiplier of one lane form
        # the fused datapath's unit (named after the fp_fma structure); a mode whose fp_fma stays separate has
        # the group split back by the seed (families.partition.fuse_multiply_add)
        fmas = {(s.mode, s.lane): s.id for s in slotted if s.kind == "fp_fma"}
        fused: dict = {}
        out = []
        for s in slotted:
            host = fmas.get((s.mode, s.lane)) if s.kind in ("fp_fma", "fp_adder", "fp_multiplier") else None
            if host is None:
                out.append((s.id, (s.id,)))
            else:
                fused.setdefault(host, []).append(s.id)
        return out + [(host, tuple(members)) for host, members in fused.items()]
    groups: dict = {}
    out = []
    for s in slotted:
        if s.kind not in SHARED_KINDS[plan] or not _binary(s.format):
            out.append((s.id, (s.id,)))          # a comparator, a float structure: its own unit
            continue
        key = s.kind if plan == "packed_banks" else f"{s.kind}_l{s.lane}"
        groups.setdefault(key, []).append(s.id)
    for key, members in groups.items():
        if len(members) == 1:
            out.append((members[0], tuple(members)))
        else:
            out.append((f"{'packed' if plan == 'packed_banks' else 'pos'}_{key}", tuple(members)))
    return out


def _binary(fmt: str) -> bool:
    """A two's complement or unsigned integer/fixed-point format, whose lanes a packed datapath can share."""
    return fmt.startswith(("int", "uint", "fxs")) and not fmt.endswith(("_sm", "_ones", "_sign_magnitude", "_ones_complement"))


def group_of(part: list) -> dict:
    """structure id -> unit name for the grouped members of a partition."""
    out = {}
    for unit, members in part:
        if len(members) > 1:
            for m in members:
                out[m] = unit
    return out


# ---------------------------------------------------------------- plans as data

PLAN_DOC = """A plan groups the seed's structures into shared datapaths and names
families. Its parts:

* `options`: unit-wide searched implementation choices, currently `{"x_form": "exact"}`
  or `{"x_form": "guard_round_sticky"}` where the target admits it.

* `shared`: `{"<group>": {"members": [<id, glob over ids such as "m1.*.adder", or a bare kind>, ...],
  "family": "<family>", "pin": {"<choice>": <value>}, "why": "one sentence"}}`. One physical
  structure (one module) realizes every member of a group. A group needs two members or more.
  The seed realizes these groups and no others:
  * binary integer adders (two's complement or unsigned, across modes and lanes) under the
    subword family `partitioned_carry_chain`: one lane-partitioned adder;
  * binary integer multipliers under the family `twin_precision_subword`: one gated matrix;
    a group of simultaneous lanes from one mode takes this family automatically (the returned
    declaration records the family change and closes the previous family's pins);
  * integer logic structures under the family `wide_gate_row`: one gate row;
  * the rounders, or the unpackers, of several float formats with identical families and pins
    (one physical datapath per lane position; an omitted group family defaults to
    `shared_across_formats`, and an explicit family keeps its inner choices);
  * the float adders, multipliers, comparators or dividers of two float formats or more: one
    datapath per lane position at the widest geometry, the operands muxed by the mode;
  * the binary integer adders, multipliers, comparators, shifters, logic structures or
    bit counters of two modes or more under any library family of their kind (and without the
    sharing families above): one module per lane position at the widest served width, the
    operands extended and muxed by the mode (one mode computes per operation);
  * one adder with the comparators of its own mode and lane (min, max and cmp ride the
    adder's subtractor);
  * `alu_pg_fused` logic with its lane's adder, optionally including its comparator:
    PG terms serve logic and addition, and comparison uses the same subtractor. Explicit
    partitions merge these logic/adder groups automatically; a triple's comparator takes
    `subtractor_comparator` and the lane adder's family/pins in the returned declaration;
  * the binary integer adders with the float adders of single-lane float modes, under
    `partitioned_carry_chain`: one lane-partitioned adder wide enough for the significand add,
    which the float adder (a single-path family, operands swapped before one shifter, two's
    complement subtraction) takes through ports.
  Any other pair of kinds, a comparator of another lane, or the lanes of one mode alone (they
  compute at once) cannot share a module. A mode whose fp_fma selects a fused family computes its
  adds and multiplies in that datapath, so its fp_adder and fp_multiplier leave any group.
  `family` is the family of the shared structure, applied to every member whose kind admits it
  (and to the other lanes of the members' modes, which share its variable); `pin` names choices
  of that family. Omit both to leave them to the search; members then declaring different
  families take the first member's.
* `structures`: `{"<selector>": {"family": "<family>", "pin": {...}}}` for structures outside a
  group, or for a group by its name; a selector is a structure id, a glob over ids, or a bare
  kind (every structure of that kind).
* `components`: `{"<slot>": {"family": "<family>", "pin": {...}}}` for a unit-level slot that has
  no structure of its own (`subword`: how the lanes of one datapath are packed).

A plan's seed realizes a family by construction only where the family library has a module
for it (the families marked [library] in the menu); any other family makes the seed's module
behavioral, and the review then rejects the seed as not realizing what it declares. Give a
group or a structure a library family, or leave its family to the search.
Use only families the menu lists for a kind, and only choices its card names. Boolean pins
accept true/false or True/False, including quoted spellings. An explicit choice made inactive
by the selected families is ignored with a note naming the choice and the reason. Unknown
choices and unrealizable active selections remain errors. A structure not named keeps its defaults."""


def _select(manifest: StructureManifest, selector: str) -> list:
    """The ids a selector names: an id, a glob over ids, or a bare kind."""
    import fnmatch
    sel = str(selector)
    ids = [s.id for s in manifest if s.slot and not is_inline(s)]
    if sel in ids:
        return [sel]
    if any(ch in sel for ch in "*?["):
        return [i for i in ids if fnmatch.fnmatchcase(i, sel)]
    return [s.id for s in manifest if s.slot and s.kind == sel]


def partition_of_plan(manifest: StructureManifest, plan: dict) -> list:
    """[(unit name, member ids)] of a plan: its shared groups, then one
    unit per remaining slotted structure."""
    used, out = set(), []
    for gname, g in (plan.get("shared") or {}).items():
        if not isinstance(g, dict):
            raise ValueError(f"group {gname}: a mapping")
        members = []
        for sel in g.get("members") or []:
            found = _select(manifest, sel)
            if not found:
                inline = [s.id for s in manifest if is_inline(s) and (s.id == str(sel) or s.kind == str(sel))]
                raise ValueError(f"group {gname}: {sel!r} names no structure"
                                 + (f" ({inline[0]} is realized inline in the top and has no unit to share)"
                                    if inline else ""))
            members += [i for i in found if i not in used and i not in members]
        if len(members) < 2:
            raise ValueError(f"group {gname}: fewer than two members ({members})")
        used |= set(members)
        out.append((str(gname), tuple(members)))
    for s in manifest:
        if s.slot and not is_inline(s) and s.id not in used:
            out.append((s.id, (s.id,)))
    return out


def partition_of_declaration(manifest: StructureManifest, lines: list) -> list:
    """[(unit name, member ids)] the STRUCTURE lines of a declaration
    state through their `group=` fields."""
    from chialu.lines import parse_structure
    groups: dict = {}
    order = []
    for kind, tokens in lines:
        if kind != "STRUCTURE":
            continue
        try:
            e = parse_structure(list(tokens))
        except ValueError:
            continue
        sid = e["_"][0] if isinstance(e.get("_"), list) and e["_"] else None
        g = e.get("group")
        st = manifest.get(sid) if sid else None
        if st is not None and g and not is_inline(st):
            if g not in groups:
                order.append(g)
            groups.setdefault(g, []).append(sid)
    out = [(g, tuple(groups[g])) for g in order if len(groups[g]) > 1]
    grouped = {m for _, ms in out for m in ms}
    for s in manifest:
        if s.slot and not is_inline(s) and s.id not in grouped:
            out.append((s.id, (s.id,)))
    return out


def plan_vars(ctx, manifest: StructureManifest, plan: dict, partition: list, keep_defaults: bool = False) -> dict:
    """The VAR values a plan declares: a group's family and pins on every
    member whose kind admits them, the `structures` entries, and the
    unit-level `components`."""
    from chialu.declaration_values import canonical_value
    vars_: dict = {}
    bindings = ctx.bindings
    for option, value in (plan.get("options") or {}).items():
        b = bindings.get(option)
        if option != "x_form" or b is None or b.time != "search" or not b.domain.contains(value):
            raise ValueError(f"options: {option}={value!r} is not a searched design choice")
        vars_[option] = value

    def put(sid: str, family, pin: dict, where: str) -> bool:
        s = manifest.get(sid)
        prefix = f"core.{s.slot}.{s.index}."
        took = False
        if family:
            b = bindings.get(prefix + "family")
            if b is not None:
                family = canonical_value(b.domain, family)
            if b is not None and b.time == "search" and b.domain.contains(family):
                vars_[prefix + "family"] = family
                took = True
            elif b is not None and b.time == "fixed" and b.value == family:
                took = True
            elif b is not None and b.time == "search" and b.domain.exclusion_reason(family):
                # a family the behavior rules removed under this contract: the plan contradicts the YAML
                raise ValueError(f"{where}: {family} on {sid}{_why(b.domain, family)}")
        for choice, value in (pin or {}).items():
            b = bindings.get(prefix + str(choice))
            if b is None:
                if took:
                    raise ValueError(f"{where}: {family or s.kind} has no choice {choice!r} on {sid}")
                continue
            value = canonical_value(b.domain, value)
            if not b.domain.contains(value):
                raise ValueError(f"{where}: {choice}={value!r} is outside {b.domain.describe()}{_why(b.domain, value)}")
            if b.time == "search":
                vars_[prefix + str(choice)] = value
        return took

    groups = dict(partition)
    # the variables a group declares belong to the group: a structure outside the group whose family variable
    # it shares (the other lane of a mode, `core.<slot>.m<i>` holding every lane) takes the group's declaration
    # rather than contradicting it, since one variable cannot hold two families (a group without a family or
    # pins claims nothing, and the `structures` entries set its members' variables as before)
    claimed: set = set()
    for gname, g in (plan.get("shared") or {}).items():
        fam = g.get("family")
        sts = [manifest.get(sid) for sid in groups[gname]]
        if not fam and {s.kind for s in sts} in ({"rounder"}, {"unpacker"}) and len({s.format for s in sts}) >= 2:
            # a rounder's or an unpacker's family names its sharing pattern, and a group across formats is the
            # pattern shared_across_formats by default. An explicitly selected family keeps its inner cells.
            fam = SHARING_FAMILY[sts[0].kind]
        took = []
        for sid in groups[gname]:
            before = dict(vars_)
            took.append(put(sid, fam, g.get("pin") or {}, f"group {gname}"))
            if took[-1] or vars_ != before:
                s = manifest.get(sid)
                claimed.add(f"core.{s.slot}.{s.index}.")
        if fam and not any(took):
            raise ValueError(f"group {gname}: no member admits the family {fam!r}")
    for sel, spec in (plan.get("structures") or {}).items():
        if not isinstance(spec, dict):
            continue
        ids = list(groups.get(sel) or _select(manifest, sel))
        if not ids:
            raise ValueError(f"structures: {sel!r} names no structure")
        if sel not in (plan.get("shared") or {}):
            ids = [sid for sid in ids if f"core.{manifest.get(sid).slot}.{manifest.get(sid).index}." not in claimed]
            if not ids:
                continue
        fam = spec.get("family")
        took = [put(sid, fam, spec.get("pin") or {}, f"structures {sel}") for sid in ids]
        if fam and not any(took):
            raise ValueError(f"structures {sel}: no structure admits the family {fam!r}")
    # a group of one kind that names no family, whose members declare different families or pins (their own
    # `structures` entries, or their defaults), takes its first member's declaration: one module serves the
    # group, so the members must agree, and the first member is the one the plan lists first
    for gname, g in (plan.get("shared") or {}).items():
        if g.get("family") or g.get("pin"):
            continue
        sts = [manifest.get(sid) for sid in groups[gname]]
        if len({s.kind for s in sts}) != 1:
            continue
        # the members whose slot the plan's other choices keep open (a fused multiply-add closes its mode's
        # fp_adder and fp_multiplier slots)
        prefixes = [x for x in dict.fromkeys(f"core.{s.slot}.{s.index}." for s in sts if s.slot)
                    if _active_under(ctx, x + "family", vars_)]
        if len(prefixes) < 2:
            continue

        def declared_under(prefix):
            fam_name = prefix + "family"
            b = bindings.get(fam_name)
            out = {k[len(prefix):]: v for k, v in vars_.items() if k.startswith(prefix)}
            if "family" not in out and b is not None:
                out["family"] = b.value if b.time == "fixed" else b.domain.default()
            return out
        head = declared_under(prefixes[0])
        for prefix in prefixes[1:]:
            if declared_under(prefix) == head:
                continue
            for k in [k for k in vars_ if k.startswith(prefix)]:
                del vars_[k]
            for suffix, value in head.items():
                b = bindings.get(prefix + suffix)
                if b is not None and b.time == "search" and b.domain.contains(value):
                    vars_[prefix + suffix] = value
    for slot, spec in (plan.get("components") or {}).items():
        if not isinstance(spec, dict):
            continue
        name = f"core.{slot}.family"
        b = bindings.get(name)
        if b is None:
            raise ValueError(f"components: no slot {slot!r}")
        fam = spec.get("family")
        if fam:
            fam = canonical_value(b.domain, fam)
            if not b.domain.contains(fam):
                raise ValueError(f"components {slot}: no family {fam!r}{_why(b.domain, fam)}")
            if b.time == "search":
                vars_[name] = fam
        for choice, value in (spec.get("pin") or {}).items():
            cb = bindings.get(f"core.{slot}.{choice}")
            if cb is not None:
                value = canonical_value(cb.domain, value)
            if cb is None or not cb.domain.contains(value):
                raise ValueError(f"components {slot}: {choice}={value!r}" + (_why(cb.domain, value) if cb is not None else ""))
            if cb.time == "search":
                vars_[f"core.{slot}.{choice}"] = value
    # A value equal to its domain's default is left out, for the renderer fills the default in anyway.
    # A caller that draws the variables the plan leaves open reads an absent one as open, and would
    # redraw the plan's own choice: `keep_defaults` returns every value the plan decides. (Without it,
    # every `sw-pcc` plan's subword -- partitioned_carry_chain, the default -- was drawn at random.)
    if keep_defaults:
        return dict(vars_)
    return {k: v for k, v in vars_.items() if v != bindings[k].domain.default()}


def _active_under(ctx, name: str, vars_: dict) -> bool:
    return inactive_reason(ctx, name, vars_) is None


def inactive_reason(ctx, name: str, vars_: dict) -> str | None:
    """The first closed ancestor, or None; undeclared ancestors use defaults."""
    tree, bindings = ctx.instance.tree, ctx.bindings

    def value_of(n):
        if n in vars_:
            return vars_[n]
        b = bindings.get(n)
        if b is None:
            return None
        return b.value if b.time == "fixed" else b.domain.default()
    seen = set()
    v = tree.resolve(name)
    while v is not None and v.when and v.name not in seen:
        seen.add(v.name)
        parent = v.when[0]
        if not v.condition_holds(value_of(parent)):
            return f"{v.name} requires {parent} in {v.when[1]!r}; selected {value_of(parent)!r}"
        v = tree.resolve(parent)
    return None


def _why(domain, value) -> str:
    """`: <reason>` where the behavior rules removed the value from the domain, else ''."""
    from chialu.behavior_rules import outside_reason
    return outside_reason(domain, value)


def normalize_lane_multipliers(ctx, manifest, partition, overrides):
    """Select a partitioned matrix for a group of simultaneous binary lanes.

    Update the declaration as well as the renderer's input. A family change
    closes its old pins; a fixed family or restricted domain stays a refusal.
    Across-mode groups retain their chosen library family and multiplexing.
    """
    for name, members in partition or ():
        sts = [manifest.get(sid) for sid in members]
        if len(sts) < 2 or any(st is None or st.kind != "multiplier" or not _binary(st.format) for st in sts):
            continue
        if len({st.mode for st in sts}) != 1:
            continue
        prefix = f"core.multiplier.{sts[0].index}."
        binding = ctx.bindings.get(prefix + "family")
        family = "twin_precision_subword"
        if binding is None:
            raise ValueError(f"partition {name}: simultaneous multiplier lanes require a {prefix}family binding")
        current = overrides.get(prefix + "family", binding.value if binding.time == "fixed" else binding.domain.default())
        if current == family:
            continue
        if binding.time != "search" or not binding.domain.contains(family):
            raise ValueError(f"partition {name}: simultaneous multiplier lanes require {prefix}family={family}; "
                             f"the binding fixes or excludes it (selected {current})")
        for key in list(overrides):
            if key.startswith(prefix):
                del overrides[key]
        overrides[prefix + "family"] = family


def _render(ctx, partition, overrides: dict | None = None):
    """The seed of a partition, its structures realized by the family
    library under the declared VAR values (`overrides`)."""
    from chialu.modules.generators import families_of, realization_of, spec_of
    from chialu.targets import derive
    from chialu.targets.rtl import families as FAM
    spec = spec_of(ctx, overrides)
    if spec.get("unit") != "alu":
        raise ValueError("sharing plans are the ALU's")
    with FAM.library_realization(realization_of(ctx) == "library"):
        manifest = derive.seed_alu_text(spec, None).structures
        if overrides is None:
            overrides = {}
        normalize_lane_multipliers(ctx, manifest, partition, overrides)
        families = families_of(ctx, manifest, overrides)
        from chialu.targets.rtl.families.alu_pg import fuse_partition
        fused = fuse_partition(manifest, partition, families)
        changed = False
        for _name, members in fused or ():
            sts = [manifest.get(sid) for sid in members]
            if any(st is None for st in sts):
                continue  # retain validate_partition's unknown-member diagnostic
            for comparator in (s for s in sts if s.kind == "comparator" and _binary(s.format)):
                peers = [s for s in sts if (s.mode, s.lane) == (comparator.mode, comparator.lane)]
                if not {"adder", "logic"} <= {s.kind for s in peers}:
                    continue
                index = comparator.index
                if families.get(f"core.logic.{index}", (None,))[0] != "alu_pg_fused":
                    continue
                # The group has one CPA: make its comparator declaration name
                # that CPA, including its pins, instead of a second subtractor.
                adder, pins = families[f"core.adder.{index}"]
                prefix = f"core.comparator.{index}."
                wanted = {"family": "subtractor_comparator", "subtractor.family": adder,
                          **{f"subtractor.{k}": v for k, v in pins.items()}}
                for suffix, value in wanted.items():
                    binding = ctx.bindings.get(prefix + suffix)
                    if binding is None or (binding.value != value if binding.time == "fixed"
                                           else not binding.domain.contains(value)):
                        raise ValueError(f"PG comparator sharing requires {prefix}{suffix}={value}")
                for key in list(overrides):
                    if key.startswith(prefix) and key != prefix + "zero_detect":
                        del overrides[key]
                # a pin at its default is not declared (as plan_vars leaves defaults out), so a render of the
                # returned declaration declares the same set again
                overrides.update({prefix + k: v for k, v in wanted.items()
                                  if ctx.bindings[prefix + k].time == "search"
                                  and (k == "family" or k == "subtractor.family"
                                       or v != ctx.bindings[prefix + k].domain.default())})
                changed = True
        if changed:
            families = families_of(ctx, manifest, overrides)
        st = derive.seed_alu_text(spec, partition, families=families)
    st.notes = families.notes
    if overrides is not None:
        from chialu.declaration_values import canonical_vars
        normalized = canonical_vars(ctx, overrides)
        overrides.clear()
        overrides.update({k: v for k, v in normalized.items() if k not in families.ignored})
    # the groups the seed realizes, which may differ from the partition asked for: a fused multiply-add
    # absorbs its lane's adder and multiplier, a full-word datapath its modes' other lanes
    # (families.partition.fuse_multiply_add, complete_word_groups)
    groups = group_of([(u.name, u.members) for u in st.units]) if st.units else group_of(partition)
    for s in st.structures:
        s.group = groups.get(s.id, "")
    return st


def plan_seed(ctx, name: str, plan: dict):
    """A plan as a seed: (text, VAR values, STRUCTURE lines)."""
    from chialu.modules.generators import spec_of
    from chialu.targets import derive
    from chialu.targets.rtl.structures import strip_manifest_header
    spec = spec_of(ctx)
    if spec.get("unit") != "alu":
        raise ValueError("sharing plans are the ALU's")
    from chialu.modules.generators import split_fixed_families
    manifest = derive.seed_alu_text(spec, None).structures
    raw = partition_of_plan(manifest, plan)
    vars_ = plan_vars(ctx, manifest, plan, raw, keep_defaults=True)
    # a member whose family is fixed (a preset) leaves a group the plan gives another family
    partition = split_fixed_families(raw, manifest, ctx.bindings)
    st = _render(ctx, partition, vars_)
    vars_ = {k: v for k, v in vars_.items() if v != ctx.bindings[k].domain.default()}
    from chialu.modules.generators import seed_output
    from chialu.declaration_values import RenderResult
    return RenderResult(seed_output(ctx, st), vars_, st.structures.declaration_lines(), notes=st.notes)


def _region_texts(ctx, marked: str) -> dict:
    """{region name: text} of a marked program: the EVOLVE regions (the
    top and the unit modules), whether the program is one text or the
    member-marked text of a multi-file seed."""
    from adir import artifacts as A
    a = ctx.instance.seed_artifacts()[0]
    names = [name for _s, _e, name in A.find_regions(A.strip_markers(marked), a.evolve, a.language)]
    _fixed, regions = A.regions_of(marked)
    return dict(zip(names, regions))


def _family_changed(manifest, members, vars_new: dict, vars_old: dict) -> bool:
    """Whether a member's family or family choices differ between two
    declarations (an undeclared value is the default on both sides)."""
    if vars_new.get("x_form") != vars_old.get("x_form"):
        return True
    prefixes = []
    for sid in members:
        s = manifest.get(sid)
        if s is not None and s.slot:
            prefixes.append(f"core.{s.slot}.{s.index}.")
    keys = {k for k in list(vars_new) + list(vars_old) if any(k.startswith(p) for p in prefixes)}
    return any(vars_new.get(k) != vars_old.get(k) for k in keys)


def replan(ctx, decl, parent_decl, parent_program: str | None = None):
    """A regrouping in the candidate's STRUCTURE lines, or a change of a
    declared family or family choice, re-renders the seed: the family
    library realizes the declared families by construction, so a
    declaration alone changes the datapath. A unit keeps the parent's
    region text (`keep`) when its members and families are unchanged,
    or when the candidate edited that region itself (its text differs
    from the parent's: the rewrite wins over the library); the top and
    the other units are fresh. The candidate's VAR lines stay."""
    from chialu.modules.generators import spec_of
    from chialu.targets import derive
    from chialu.targets.rtl.alu_seed import sv_ident
    from chialu.targets.rtl.structures import strip_manifest_header
    from chialu.lines import normalize_declaration
    original_vars = dict(decl.vars)
    decl = normalize_declaration(ctx, decl)
    parent_decl = normalize_declaration(ctx, parent_decl)
    repaired = original_vars != decl.vars
    spec = spec_of(ctx)
    if spec.get("unit") != "alu":
        # one family at the core (the dot accumulator, the SFU): a changed family or choice re-renders the seed
        from chialu.modules.generators import core_family_of
        vars_new, vars_old = dict(decl.vars), dict(parent_decl.vars)
        core_new = {k: v for k, v in vars_new.items() if k.startswith("core.")}
        core_old = {k: v for k, v in vars_old.items() if k.startswith("core.")}
        if core_new == core_old:
            return None
        text = derive.seed_for(spec, family=core_family_of(ctx, vars_new))
        return strip_manifest_header(text), vars_new, [], []
    manifest = derive.seed_alu_text(spec, None).structures
    new = partition_of_declaration(manifest, decl.lines)
    old = partition_of_declaration(manifest, parent_decl.lines)
    top = spec.get("dut_name", "alu_core")
    vars_new, vars_old = dict(decl.vars), dict(parent_decl.vars)
    unchanged = {(u, frozenset(m)) for u, m in old}
    edited = set()
    if parent_program is not None and getattr(ctx, "candidate", None) is not None:
        try:
            mine = _region_texts(ctx, next(iter(ctx.candidate.marked.values())))
            theirs = _region_texts(ctx, parent_program)
            edited = {n for n, t in mine.items() if theirs.get(n) is not None and theirs[n] != t}
        except Exception:  # noqa: BLE001 - a malformed parent keeps nothing
            edited = set()
    keep, fresh = [], []
    for u, m in new:
        module = f"{top}_u_{sv_ident(u)}"
        same_members = (u, frozenset(m)) in unchanged
        if same_members and (not _family_changed(manifest, m, vars_new, vars_old) or module in edited):
            keep.append(module)
        else:
            fresh.append(module)
    if not fresh and {(u, frozenset(m)) for u, m in new} == unchanged:
        if not repaired:
            return None
        candidate = getattr(ctx, "candidate", None)
        if candidate is not None and candidate.texts:
            # A spelling/projection repair alone must preserve the candidate's
            # actual RTL edits, including its top module.
            import re
            from chialu.declaration_values import RenderResult, NOTE_PREFIX
            texts = {m: re.sub(r"^[ \t]*// ADIR-DECL v1\n.*?^[ \t]*// ADIR-END[^\n]*\n", "", t,
                               flags=re.M | re.S) for m, t in candidate.texts.items()}
            texts = {m: re.sub(r"^" + re.escape(NOTE_PREFIX) + r"[^\n]*\n", "", t, flags=re.M)
                     for m, t in texts.items()}
            member = ctx.instance.seed_artifacts()[0].declaration_member or next(iter(texts))
            notes = getattr(decl, "notes", [])
            texts[member] = "".join(NOTE_PREFIX + note + "\n" for note in notes) + texts[member]
            return RenderResult(texts, vars_new, decl.lines, [], notes=notes)
    st = _render(ctx, new, vars_new)
    # Fusion can change an otherwise untouched group's membership and its
    # physical family choices. Do not restore that group's stale parent RTL.
    actual = {u.module: (u.name, u.members) for u in st.units}
    keep = [module for module in keep if module in actual
            and (actual[module][0], frozenset(actual[module][1])) in unchanged
            and (not _family_changed(manifest, actual[module][1], vars_new, vars_old) or module in edited)]
    from chialu.modules.generators import seed_output
    from chialu.declaration_values import RenderResult
    st.notes = list(dict.fromkeys(getattr(decl, "notes", []) + st.notes))
    return RenderResult(seed_output(ctx, st), vars_new, st.structures.declaration_lines(), keep, notes=st.notes)


# ---------------------------------------------------------------- sharing schemes by enumeration

# the group kinds the seed realizes (validate_partition), each with the family the sharing implies, or None
# where the members' own family (tied across the group) is the search's
SHARING_FAMILY = {"multiplier": "twin_precision_subword", "logic": "wide_gate_row",
                  "rounder": "shared_across_formats", "unpacker": "shared_across_formats", "adder": None, "fp_adder": None}
# FP partitions select physical sharing independently of their families.
# SHARING_FAMILY supplies legacy defaults only when a plan omits a stage family.
FLOAT_STAGE_KINDS = ("rounder", "unpacker")
FLOAT_ARITH_KINDS = ("fp_adder", "fp_multiplier", "fp_comparator", "fp_divider")
FLOAT_SHARE_KINDS = FLOAT_STAGE_KINDS + FLOAT_ARITH_KINDS
NATURAL_RULES = ("none", "all", "per_mode", "per_lane")


def _narrowest(members, structures) -> str:
    """The member of a shared float bank with the fewest significand bits: its per-mode domains are the
    narrowest (e.g. no recursive significand split below four bits), so the choices a sampler draws for it
    are valid for every wider member, and scheme_repair ties the bank to them."""
    from chialu.verify.formats import FloatFormat, parse_format
    fmt = {s.id: s.format for s in structures}

    def bits(sid):
        try:
            f = parse_format(fmt.get(sid, ""))
            return f.man_bits if isinstance(f, FloatFormat) else 1 << 20
        except ValueError:
            return 1 << 20
    return min(members, key=lambda sid: (bits(sid), members.index(sid)))


def _float_schemes(floats, fmas, level):
    """Independent FP banks, plus the mode-selected fused FMA bank.

    Arithmetic currently has one bank per kind, selected by mode. Stages
    support arbitrary disjoint banks per lane. Enumerate physical banks,
    not aliases made by including an otherwise independent SIMD lane.
    FMA sharing owns both arithmetic slots in its modes. Its structure
    entries provide a default fused family; plan_of retains searched fused
    families and pins while enforcing the sharing selector.
    """
    from itertools import combinations, product
    floats = {k: sorted(v, key=lambda s: (s.mode, s.lane, s.id)) for k, v in floats.items()}
    fmas = sorted(fmas, key=lambda s: (s.mode, s.lane, s.id))

    def subsets(members):
        modes = sorted({s.mode for s in members})
        choices = [()]
        for n in range(2, len(modes) + 1):
            if level != "all" and n != len(modes):
                continue
            for ms in combinations(modes, n):
                sts = [s for s in members if s.mode in ms]
                if len({s.format for s in sts}) >= 2 and any(
                        len({s.mode for s in sts if s.lane == lane}) >= 2
                        for lane in {s.lane for s in sts}):
                    choices.append(ms)
        return choices

    def banks(kind, members):
        if kind not in FLOAT_STAGE_KINDS:
            return [[tuple(s.id for s in members if s.mode in ms and
                           sum(t.lane == s.lane and t.mode in ms for t in members) > 1)]
                    if ms else [] for ms in subsets(members)]
        lanes = sorted({s.lane for s in members})
        axes = []
        for lane in lanes:
            sts = [s for s in members if s.lane == lane]
            parts = _set_partitions(sts) if level == "all" else ([[s] for s in sts], [sts])
            choices = []
            for part in parts:
                groups = [tuple(s.id for s in g) for g in part if len(g) > 1]
                if any(len({s.mode for s in g}) != len(g) or len({s.format for s in g}) < 2
                       for g in part if len(g) > 1):
                    continue
                if groups not in choices:
                    choices.append(groups)
            axes.append(choices)
        return [sum((list(g) for g in combo), []) for combo in product(*axes)]

    tokens = {"fp_adder": "fadd", "fp_multiplier": "fmul", "fp_comparator": "fcmp",
              "fp_divider": "fdiv", "rounder": "round", "unpacker": "unpack"}
    def label(groups):
        return "+".join(".".join(s.rsplit(".", 1)[0] for s in group) for group in groups) or "none"

    for fma_modes in subsets(fmas):
        axes = []
        kinds = [k for k in FLOAT_SHARE_KINDS if floats.get(k)]
        for kind in kinds:
            members = [s for s in floats[kind]
                       if kind not in ("fp_adder", "fp_multiplier") or s.mode not in fma_modes]
            axes.append(banks(kind, members))
        for combo in product(*axes):
            shared, structures, names = {}, {}, []
            for kind, groups in zip(kinds, combo):
                names.append(f"{tokens[kind]}-{label(groups)}")
                for i, members in enumerate(groups):
                    shared[f"{kind}_bank{i}"] = {"members": list(members), "canonical": _narrowest(members, floats[kind]),
                        "why": f"one {kind} bank for mutually exclusive modes"}
            for s in fmas:
                if s.mode in fma_modes:
                    structures[s.id] = {"family": "classic_fma", "pin": {"sharing": "shared_across_formats"}}
            names.append("fma-" + (".".join(f"m{m}" for m in fma_modes) or "none"))
            # Keep the four historical names for the same physical banks.
            states = {}
            for kind, groups in zip(kinds, combo):
                full = {s.id for s in floats[kind] if sum(t.lane == s.lane for t in floats[kind]) > 1}
                grouped = {sid for group in groups for sid in group}
                complete = grouped == full and (kind not in FLOAT_STAGE_KINDS or all(
                    len([g for g in groups if g[0].split(".")[1] == lane]) == 1
                    for lane in {sid.split(".")[1] for sid in full}))
                states[kind] = "none" if not groups else "all" if complete else "subset"
            stage = {states[k] for k in kinds if k in FLOAT_STAGE_KINDS}
            arith = {states[k] for k in kinds if k in FLOAT_ARITH_KINDS}
            legacy = None
            if not fma_modes and len(stage) <= 1 and len(arith) <= 1 and "subset" not in stage | arith:
                legacy = ("all" if "all" in arith else "stage") if "all" in stage else (
                    "arith" if "all" in arith else "none")
            yield legacy or "_".join(names), shared, structures


def _groups_by_rule(members: list, rule: str) -> list:
    """The groups (lists of structure ids, two members or more) a natural
    rule makes of a kind's structures: none, all in one, the lanes of
    each mode together, the same lane across the modes together."""
    if rule == "none" or len(members) < 2:
        return []
    if rule == "all":
        return [[s.id for s in members]]
    key = (lambda s: s.mode) if rule == "per_mode" else (lambda s: s.lane)
    out: dict = {}
    for s in members:
        out.setdefault(key(s), []).append(s.id)
    return [ids for ids in out.values() if len(ids) >= 2]


def _set_partitions(items: list):
    """Every set partition of a list (Bell number of them), as lists of lists."""
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in _set_partitions(rest):
        for i in range(len(part)):
            yield part[:i] + [[first] + part[i]] + part[i + 1:]
        yield [[first]] + part


def sharing_schemes(manifest, level: str = "natural", admits=None) -> list:
    """[(name, plan)] of the sharing plans the seed realizes for a unit,
    by enumeration rather than by a model. Integer kinds retain their
    natural rules / set partitions (up to five structures). Float kinds
    vary independently: natural has full banks or none; all has every
    arithmetic mode subset and every stage partition per common lane.
    Shared FMA subsets exclude separate arithmetic banks in their modes.
    Stage families and inner choices remain searchable, including C2's
    dedicated and per-lane families. `admits(structure_id, family)` says whether a structure's slot
    admits a family (an approximate multiplier space has no twin
    matrix); a kind whose implied family a member lacks forms no group.
    The adder-with-gates pairing under alu_pg_fused is not enumerated: it
    needs a carry-propagate adder family and one family per mode, which
    a scheme cannot state."""
    from itertools import product
    slotted = [s for s in manifest if s.slot and not is_inline(s)]
    by_kind: dict = {}
    for s in slotted:
        by_kind.setdefault(s.kind, []).append(s)
    binary = lambda s: _binary(s.format)  # noqa: E731
    integer = lambda s: s.format.startswith(("int", "uint", "fxs", "bcd"))  # noqa: E731
    # FP banks do not imply shared_across_formats as their family: C2 also
    # realizes the dedicated and per-lane stage families in explicit banks.
    _admits = admits or (lambda sid, fam: True)
    ok = lambda sid, fam: True if fam is None else _admits(sid, fam)  # noqa: E731
    adders = [s for s in by_kind.get("adder", []) if binary(s)]
    muls = [s for s in by_kind.get("multiplier", []) if binary(s) and ok(s.id, SHARING_FAMILY["multiplier"])]
    logics = [s for s in by_kind.get("logic", []) if integer(s) and ok(s.id, SHARING_FAMILY["logic"])]
    cmps = {(s.mode, s.lane): s for s in by_kind.get("comparator", []) if binary(s)}
    floats = {k: [s for s in by_kind.get(k, []) if not integer(s)]
              for k in FLOAT_SHARE_KINDS}
    # the float adders of single-lane float modes may join the integer adders' bank (their significand add)
    lanes_of_mode: dict = {}
    for s in slotted:
        lanes_of_mode.setdefault(s.mode, set()).add(s.lane)
    from chialu.verify.formats import FloatFormat, parse_format

    def is_float(s) -> bool:
        try:
            return isinstance(parse_format(s.format), FloatFormat)
        except ValueError:
            return False
    fp_adders = [s for s in by_kind.get("fp_adder", []) if is_float(s) and len(lanes_of_mode.get(s.mode, ())) == 1]
    modes = {s.mode for s in slotted}

    def partitions(members):
        if level == "all" and 2 <= len(members) <= 5:
            seen, out = set(), []
            for part in _set_partitions(list(members)):
                groups = tuple(sorted(tuple(s.id for s in g) for g in part if len(g) >= 2))
                if groups not in seen:
                    seen.add(groups)
                    out.append(("p%d" % len(out), [list(g) for g in groups]))
            return out
        out, seen = [], set()
        for rule in NATURAL_RULES:
            groups = tuple(sorted(tuple(ids) for ids in _groups_by_rule(members, rule)))
            if groups in seen:
                continue
            seen.add(groups)
            out.append((rule, [list(g) for g in groups]))
        return out

    axes = [("add", partitions(adders)), ("mul", partitions(muls)), ("log", partitions(logics))]
    pair_rules = ["none"] + (["comparator"] if cmps else [])
    fmas = [s for s in by_kind.get("fp_fma", []) if ok(s.id, "classic_fma")]
    fmt_rules = list(_float_schemes(floats, fmas, level)) if any(floats.values()) or fmas else [("none", {}, {})]
    intfp_rules = ["none"] + (["all"] if fp_adders and adders else [])
    schemes = []
    for (a_rule, a_groups), (m_rule, m_groups), (l_rule, l_groups), pair, (fmt, fp_groups, fp_structures), intfp in product(
            axes[0][1], axes[1][1], axes[2][1], pair_rules, fmt_rules, intfp_rules):
        a_groups = [list(g) for g in a_groups]
        if intfp == "all":
            # every float adder joins the integer adders' bank: the group of its lane's adder, else the first,
            # else a new bank of the integer adder of its lane (or the first integer adder)
            for f in fp_adders:
                host = next((g for g in a_groups if any(manifest.get(i).lane == f.lane for i in g)), a_groups[0] if a_groups else None)
                if host is None:
                    partner = next((s for s in adders if s.lane == f.lane), adders[0])
                    host = [partner.id]
                    a_groups.append(host)
                host.append(f.id)
        banked = {i for g in a_groups for i in g}
        shared: dict = {}
        for i, g in enumerate(a_groups):
            with_fp = any(manifest.get(x).kind == "fp_adder" for x in g)
            shared[f"adders_{i}"] = {"members": g, "why": "one lane-partitioned adder for these lanes"
                                     + (", its width the float significand add's, which the float adder takes through ports" if with_fp else "")}
        for i, g in enumerate(m_groups):
            shared[f"multipliers_{i}"] = {"members": g, "family": SHARING_FAMILY["multiplier"],
                                          "why": "one gated twin-precision matrix for these lanes"}
        for i, g in enumerate(l_groups):
            shared[f"gate_rows_{i}"] = {"members": g, "family": SHARING_FAMILY["logic"], "why": "one gate row for these lanes"}
        pairs = 0
        if pair != "none":
            for s in adders:
                if s.id in banked:
                    continue
                partner = cmps.get((s.mode, s.lane))
                if partner is None:
                    continue
                shared[f"pair_m{s.mode}_l{s.lane}"] = {"members": [s.id, partner.id],
                                                       "why": "the comparator rides the adder's subtractor"}
                pairs += 1
            if not pairs:
                continue                                  # the rule made no group: the same scheme as `none`
        occupied = {m for g in shared.values() for m in g["members"]}
        if any(occupied.intersection(g["members"]) for g in fp_groups.values()):
            continue
        shared.update(fp_groups)
        # the subword family says how one datapath's lanes pack, which needs two binary integer modes or more;
        # a unit without them (an all-float ALU) opens the slot and never instantiates it, so it stays unstated
        packs = len({s.mode for s in adders}) > 1 or len({s.mode for s in muls}) > 1
        sub_options = (["partitioned_carry_chain"] if a_groups else
                       ["partitioned_carry_chain", "replicated_lanes"]) if packs else [None]
        for sub in sub_options:
            name = (f"add-{a_rule}_mul-{m_rule}_log-{l_rule}_pair-{pair}_" + ("fmt-" + fmt if fmt in ("none", "stage", "arith", "all") else "fmt-banks_" + fmt) + (f"_intfp-{intfp}" if intfp_rules != ["none"] else "")
                    + (f"_sw-{'pcc' if sub == 'partitioned_carry_chain' else 'rep'}" if sub else ""))
            plan = {"shared": dict(shared), "structures": dict(fp_structures),
                    "why": f"sharing scheme {name}: adders {a_rule}, multipliers {m_rule}, gate rows {l_rule}, "
                           f"adder partner {pair}, float sharing {fmt}" + (f", float adders in the integer bank {intfp}" if intfp_rules != ["none"] else "")
                           + (f", subword {sub}" if sub else "")}
            if sub:
                plan["components"] = {"subword": {"family": sub}}
            schemes.append((name, plan))
    return schemes
