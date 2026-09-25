"""The generators the three unit-class templates register with ADIR:
the seed realization of the searched core, the generated checker, the
verification files, and the seed set over the sharing plans
the problem text carries."""
from __future__ import annotations

import tempfile
from pathlib import Path

from chialu.targets import derive


def spec_of(ctx, overrides=None) -> dict:
    spec = derive.spec_from_bindings(ctx.template.name, ctx.bindings)
    values = overrides if overrides is not None else getattr(getattr(ctx, "declaration", None), "vars", {})
    if "x_form" in values:
        binding = ctx.bindings.get("x_form")
        form = values["x_form"]
        domain = (binding.domain if binding.time == "search" else binding.variable.domain) if binding else None
        if domain is None or not domain.contains(form) or (binding.time == "fixed" and form != binding.value):
            raise ValueError(f"x_form={form!r}: outside the bound design choices")
        spec["x_form"] = form
        from chialu.behavior_rules import check_options
        problems = check_options(spec)
        if problems:
            raise ValueError("; ".join(problems))
    return spec


def core_seed(ctx) -> str:
    """The default seed of the core artifact (the baseline plan): its text,
    or its members for a multi-file core."""
    from chialu.targets.rtl.structures import strip_manifest_header
    spec = spec_of(ctx)
    if spec.get("unit") == "alu":
        from chialu.targets.rtl.alu_seed import structure_manifest
        families = families_of(ctx, structure_manifest(spec))
        return seed_output(ctx, derive.seed_alu_text(spec, None, families=families))
    return strip_manifest_header(derive.seed_for(spec, family=core_family_of(ctx)))


def core_members_of(ctx):
    """The member names of a multi-file core artifact (`artifacts.core`
    with `members` or `indexed_by` in the run file), or None for a
    single-text core."""
    inst = ctx.instance
    raw = getattr(inst, "raw", None) or {}
    arts = raw.get("artifacts") or (raw.get("adir") or {}).get("artifacts") or {}
    core = arts.get("core") if isinstance(arts, dict) else None
    if not isinstance(core, dict):
        return None
    if core.get("members"):
        return [str(m) for m in core["members"]]
    if core.get("indexed_by"):
        return [str(m) for m in (inst.elaboration.index_sets.get(str(core["indexed_by"])) or [])]
    return None


def seed_output(ctx, st):
    """A rendered ALU seed as the core artifact takes it: the one text, or
    {member: text} for a multi-file core (`alu_seed.member_names`), the
    manifest header lines stripped either way (they travel in the
    declaration block)."""
    from chialu.targets.rtl.structures import strip_manifest_header
    names = core_members_of(ctx)
    from chialu.declaration_values import NOTE_PREFIX
    notes = "".join(NOTE_PREFIX + note + "\n" for note in getattr(st, "notes", ()))
    if names is None:
        return notes + strip_manifest_header(st.text)
    missing = [m for m in names if m not in st.members]
    if missing:
        raise ValueError(f"the seed has no text for the members {missing}")
    return {m: (notes if m == "top" else "") + strip_manifest_header(st.members[m]) for m in names}


def _active_pins(ctx, base, kind, family, pins, overrides, automatic=(), width=16, ignored=None):
    """Discard inactive candidate/default values, retaining fixed-contract errors."""
    from chialu.variant_contracts import family_schemas, recursive_inactive_parameters, validate_partial
    schemas = family_schemas(kind, family, width)
    if not schemas:
        raise ValueError(f"{base}: no declared {kind}/{family} schema")
    functions = spec_of(ctx).get("functions", ()) if kind == "sfu" else ()
    failures = []

    def explicit(name):
        binding = ctx.bindings.get(name)
        return (name in overrides and name not in automatic) or (binding is not None and binding.time == "fixed")

    def local_defaults(product, prefix, supplied):
        # ADIR combines equal variable names across families into a union
        # domain. A search default must also belong to this selected family.
        result = dict(supplied)
        for axis in product.axes:
            name = prefix + "." + axis.name
            binding = ctx.bindings.get(name)
            if axis.name not in result and binding is None:
                continue
            candidate = result[axis.name] if axis.name in result else binding.value if binding.time == "fixed" else binding.domain.default()
            if not explicit(name) and not axis.domain.contains(candidate):
                candidates = (axis.at(i) for i in range(axis.count))
                candidate = next((v for v in candidates if binding is None or binding.domain.contains(v)), None)
                if candidate is None:
                    raise ValueError(f"{name}: search domain has no values in {product.name}'s {axis.domain.describe()}")
            result[axis.name] = candidate
        for slot in product.slots:
            selector = slot.name + ".family"
            name = prefix + "." + selector
            binding = ctx.bindings.get(name)
            if selector not in result and binding is None:
                continue
            candidate = result[selector] if selector in result else binding.value if binding.time == "fixed" else binding.domain.default()
            child = next((f for f in slot.families if f.name == candidate), None)
            if child is None and not explicit(name):
                child = next((f for f in slot.families if binding is None or binding.domain.contains(f.name)), None)
                if child is None:
                    raise ValueError(f"{name}: search domain has no families allowed by {product.name}")
                candidate = child.name
            result[selector] = candidate
            if child is not None:
                child_prefix = slot.name + "."
                children = {key[len(child_prefix):]: result.pop(key) for key in list(result)
                            if key.startswith(child_prefix) and key != selector}
                normalized = local_defaults(child, prefix + "." + slot.name, children)
                result.update({child_prefix + key: value for key, value in normalized.items()})
        return result

    for schema in schemas:
        dropped = {}
        try:
            filtered = local_defaults(schema, base, pins)
            inactive = recursive_inactive_parameters(schema, filtered, functions=functions)
            if kind == "dot":
                from chialu.targets.rtl.families.dot import geom_of, dot_geometry_inactive_parameters
                from chialu.verify.dot_ref import normalize_dot_spec, parse_modes
                spec = normalize_dot_spec(spec_of(ctx))
                for mode in parse_modes(spec["modes"]):
                    geometry = geom_of(mode["fab"], mode["fc"], mode["fd"], mode["elements"],
                                       spec["accumulate"], spec["sr_bits"], "SR" in spec["rounding"])
                    inactive.update(dot_geometry_inactive_parameters(family, filtered, geometry))
            for key, reason in inactive.items():
                for path in list(filtered):
                    if path != key and not path.startswith(key + "."):
                        continue
                    name = base + "." + path
                    binding = ctx.bindings.get(name)
                    if (binding is not None and binding.time == "fixed") or (ignored is None and explicit(name)):
                        raise ValueError(f"{name}: inactive ({reason}); explicitly selected")
                    if name in overrides and name not in automatic:
                        dropped[name] = reason
                    filtered.pop(path)
            validate_partial(schema, filtered)
            if ignored is not None:
                ignored.update(dropped)
            return filtered
        except ValueError as error:
            failures.append(str(error))
    raise ValueError("; ".join(dict.fromkeys(failures)))


def _reject_unselected_choices(ctx, selections, overrides, automatic=(), ignored=None):
    from chialu.plans import inactive_reason
    active = {base + ".family" for base in selections}
    active.update(base + "." + key for base, (_, pins) in selections.items() for key in pins)
    fixed = {name for name, binding in list(ctx.bindings.items())
             if name.startswith("core.") and binding.time == "fixed"}
    fixed.update(name for name, choice in ctx.instance.tree.specs.items()
                 if name.startswith("core.") and "*" not in name and isinstance(choice, dict) and "fixed" in choice)
    unused = fixed - active
    for name in overrides:
        if not name.startswith("core.") or name in automatic or name in active or name in (ignored or {}):
            continue
        reason = inactive_reason(ctx, name, overrides)
        if ignored is not None and name not in fixed and reason:
            ignored[name] = reason
        else:
            unused.add(name)
    if unused:
        raise ValueError(f"explicit choices are unknown or inactive under the selected families: {sorted(unused)}")


class Selections(dict):
    """Resolved family choices and the explicit inactive values omitted."""

    def __init__(self):
        super().__init__()
        self.ignored = {}

    @property
    def notes(self):
        return [f"ignored VAR {name}: inactive ({reason})" for name, reason in sorted(self.ignored.items())]


def checker(ctx) -> str:
    return derive.checker_rtl(spec_of(ctx))


def verify_bundle(ctx) -> dict:
    """{file name: text}: the members of the `verify_bundle` artifact."""
    spec = spec_of(ctx)
    chk = derive.checker_rtl(spec) if spec.get("checker_name") else None
    out = Path(ctx.run_dir) / "verify" if ctx.run_dir else Path(tempfile.mkdtemp(prefix="chialu_verify_"))
    return derive.verify_files(spec, out, chk)


def _declared_value(ctx, var, plan_overrides: dict, kind: str | None, vars_: dict):
    """The value a seed declares for one searched variable: the plan's
    override where it has one, else the first member of the domain."""
    b = ctx.bindings[var.name]
    dom = b.domain
    suffix = var.name.split(".")[-1]
    if kind and kind in plan_overrides and suffix in plan_overrides[kind]:
        v = plan_overrides[kind][suffix]
        if dom.contains(v):
            return v
    if var.name == "core.family":
        return "unit_per_class" if dom.contains("unit_per_class") else dom.members()[0]
    if var.name == "core.subword.family":
        from chialu.plans import SUBWORD_FAMILY
        v = SUBWORD_FAMILY.get(vars_.get("__plan__", "baseline"))
        if v and dom.contains(v):
            return v
    if var.name == "checker.family" and dom.contains("residue"):
        return "residue"
    if var.name == "checker.modulus" and dom.contains(15):
        return 15
    return dom.members()[0] if dom.finite() else dom.sample(__import__("random").Random(0))


def declared_vars(ctx, plan: str, decisions_only: bool = True) -> dict:
    """The VAR lines of a plan's seed: the active searched variables,
    parents before children, the plan's family overrides applied; a
    walk of the variable tree, so the choices under a family the plan
    picks are opened as it goes. With `decisions_only` a value equal
    to its domain's default is left out, since an undeclared decision
    stands at its default (the block then lists the plan's decisions
    alone)."""
    from chialu.plans import FAMILY_OVERRIDES
    overrides = FAMILY_OVERRIDES.get(plan, {})
    inst = ctx.instance
    bindings = ctx.bindings
    vars_ = {"__plan__": plan}

    def walk(name: str, value):
        """The active children of a variable at `value`."""
        for child in inst.tree.children_of(name):
            if value is None and not any(child.condition_holds(m) for m in (bindings.get(name).members or [])):
                continue
            if value is not None and not child.condition_holds(value):
                continue
            b = bindings.get(child.name)
            if b is None:
                continue
            if b.time == "search":
                parts = child.name.split(".")
                kind = parts[1] if len(parts) > 2 and parts[0] == "core" else None
                v = _declared_value(ctx, child, overrides, kind, vars_)
                vars_[child.name] = v
            elif b.time == "fixed":
                v = b.value
            else:
                v = None
            walk(child.name, v)

    for root in inst.tree.roots():
        b = bindings.get(root.name)
        if b is None:
            continue
        if b.time == "search":
            parts = root.name.split(".")
            kind = parts[1] if len(parts) > 2 and parts[0] == "core" else None
            v = _declared_value(ctx, root, overrides, kind, vars_)
            vars_[root.name] = v
        elif b.time == "fixed":
            v = b.value
        else:
            v = None
        walk(root.name, v)
    vars_.pop("__plan__")
    # Tree conditions open component families; applicability conditions can
    # further disable own pins and nested slots. These values came from the
    # search domains, so remove them before they become candidate VAR lines.
    spec = spec_of(ctx)
    if spec.get("unit") == "alu":
        from chialu.targets.rtl.alu_seed import structure_manifest
        selections = families_of(ctx, structure_manifest(spec), vars_, _automatic_overrides=set(vars_))
        resolved = {base + ".family": family for base, (family, _) in selections.items()}
        resolved.update({base + "." + key: value for base, (_, pins) in selections.items() for key, value in pins.items()})
    else:
        selected = core_family_of(ctx, vars_, _automatic_overrides=set(vars_))
        resolved = {"core.family": selected[0], **{"core." + key: value for key, value in selected[1].items()}} if selected else {}
    vars_ = {key: resolved.get(key, value) for key, value in vars_.items() if not key.startswith("core.") or key in resolved}
    # Resolving an alias may open another family branch after the first
    # tree walk. Export its active search decisions as well, including a
    # propagated nondefault topology that was not in the old branch.
    for key, value in resolved.items():
        binding = bindings.get(key)
        if binding is not None and binding.time == "search":
            vars_[key] = value
    if decisions_only:
        vars_ = {k: v for k, v in vars_.items() if v != bindings[k].domain.default()}
    return vars_


def split_fixed_families(part: list, manifest, bindings: dict) -> list:
    """A partition with every group split by the families its members are
    fixed to (a preset on one structure): one datapath has one family,
    so a member fixed to another family gets a unit of its own."""
    out = []
    for unit, members in part:
        if len(members) < 2:
            out.append((unit, tuple(members)))
            continue
        by_fixed: dict = {}
        for m in members:
            s = manifest.get(m)
            b = bindings.get(f"core.{s.slot or s.kind}.{s.index}.family")
            key = b.value if b is not None and b.time == "fixed" else None
            by_fixed.setdefault(key, []).append(m)
        if len(by_fixed) == 1:
            out.append((unit, tuple(members)))
            continue
        free = by_fixed.pop(None, [])
        if free:
            out.append((unit, tuple(free)) if len(free) > 1 else (free[0], (free[0],)))
        for fam, ms in by_fixed.items():
            out.append((f"{unit}_{fam}", tuple(ms)) if len(ms) > 1 else (ms[0], (ms[0],)))
    return out


def _shared_exit_defaults(ctx, manifest, overrides, automatic, ignored):
    """Resolve ADIR names of one carry-save or RNS CPA without losing domains.

    The representation/channel slot has one global CPA binding. All
    selected per-mode adders must therefore share its family and active
    pins. Different fixed per-mode exits need an indexed representation
    or channel interface; the current interfaces require a common binding.
    """
    from adir.domains import Enum
    from chialu.variant_contracts import family_schemas, inactive_parameters
    from chialu.variants import Axis

    bindings = ctx.bindings

    def value(name):
        if name in overrides:
            return overrides[name]
        bound = bindings.get(name)
        return None if bound is None else bound.value if bound.time == "fixed" else bound.domain.default()

    core = value("core.family")
    if core == "redundant_internal" and value("core.representation.family") == "carry_save_datapath":
        shared_prefix = "core.representation.assimilator"
        indexed_interface = "per-mode representation interface"
    elif core == "rns_internal":
        shared_prefix = "core.channels.modular_adder"
        indexed_interface = "per-mode channel interface"
    else:
        return {}
    exits = sorted({f"core.{s.slot}.{s.index}": s.width for s in manifest if s.slot == "adder"}.items())
    if not exits:
        return {}
    prefixes = [name for name, _ in exits] + [shared_prefix]
    resolved = {}

    def explicit(name, bound):
        return (name in overrides and name not in automatic) or (bound is not None and bound.time == "fixed")

    def choose(names, domain):
        selected, constraints, preferred = [], [], []
        for name in names:
            bound = bindings.get(name)
            if bound is None:
                raise ValueError(f"{name}: the shared exit has no ADIR binding")
            allowed = bound.variable.domain if bound.time == "fixed" else bound.domain
            wanted = value(name)
            if not allowed.contains(wanted):
                raise ValueError(f"{name}={wanted!r}: outside the user-bound {allowed.describe()}")
            if bound.time == "fixed" and wanted != bound.value:
                raise ValueError(f"{name}: candidate override conflicts with fixed {bound.value!r}")
            constraints.append(allowed)
            preferred.append(wanted)
            if explicit(name, bound):
                selected.append((name, wanted))
        if selected and any(wanted != selected[0][1] for _, wanted in selected[1:]):
            raise ValueError(f"shared exit has conflicting explicit aliases: {selected}; "
                             f"choose one common family/pin binding for {shared_prefix}, or a {indexed_interface}")
        def allowed(value):
            return domain.contains(value) and all(constraint.contains(value) for constraint in constraints)
        if selected:
            candidate = selected[0][1]
            if not allowed(candidate):
                raise ValueError(f"shared exit {names}: explicit {candidate!r} has an empty intersection with "
                                 f"the user search domains {[constraint.describe() for constraint in constraints]}")
            return candidate
        axis = Axis(names[0], domain)
        for candidate in preferred:
            if allowed(candidate):
                return candidate
        for index in range(axis.count):
            candidate = axis.at(index)
            if allowed(candidate):
                return candidate
        raise ValueError(f"shared exit {names}: empty intersection of user search domains "
                         f"{[constraint.describe() for constraint in constraints]} and {domain.describe()}")

    def walk(product, owners):
        own, failures = {}, {}
        for axis in product.axes:
            names = [owner + "." + axis.name for owner in owners]
            try:
                own[axis.name] = choose(names, axis.domain)
            except ValueError as error:
                # Applicability can depend on a later control axis. A
                # purely automatic inactive domain is not an exit choice.
                own[axis.name] = value(names[0])
                failures[axis.name] = error
        inactive = inactive_parameters(product.name, own)
        for key, selected in own.items():
            if key in inactive:
                for owner in owners:
                    name = owner + "." + key
                    bound = bindings.get(name)
                    if bound is not None and bound.time == "fixed":
                        raise ValueError(f"shared exit {key}: inactive ({inactive[key]}); explicitly selected")
                    if name in overrides and name not in automatic:
                        ignored[name] = inactive[key]
                continue
            if key in failures:
                raise failures[key]
            resolved.update({owner + "." + key: selected for owner in owners})
        for slot in product.slots:
            if slot.name in inactive:
                continue
            names = [owner + "." + slot.name + ".family" for owner in owners]
            selected = choose(names, Enum(tuple(family.name for family in slot.families)))
            resolved.update({name: selected for name in names})
            walk(next(family for family in slot.families if family.name == selected),
                 [owner + "." + slot.name for owner in owners])

    names = [prefix + ".family" for prefix in prefixes]
    # The unit-level component supplies the exact CPA family vocabulary.
    domain = ctx.instance.tree.resolve(shared_prefix + ".family").domain
    family = choose(names, domain)
    resolved.update({name: family for name in names})
    schemas = family_schemas("adder", family, max(width for _, width in exits)+1)
    if len(schemas) != 1:
        raise ValueError(f"shared exit {family}: expected one unambiguous CPA family schema")
    walk(schemas[0], prefixes)
    return resolved


def families_of(ctx, manifest, overrides: dict | None = None, *, _automatic_overrides=(),
                choose=None) -> dict:
    """{`core.<slot>.<index>`: (family, {choice: value})} for every
    slotted structure of the manifest: the declared VAR values
    (`overrides`, a seed's or a candidate's) first, else a fixed
    binding's value, else the domain default of a searched one (an
    undeclared decision stands at its default). The seed's lane modules
    realize these through the family library where it has a module.

    `choose(name, domain)` replaces the default of an undeclared
    searched decision, which is what a sampler needs: the space a
    design is drawn from is conditional -- a family opens its own
    choices and its component slots, each of which opens more, and the
    effective domain of a pin is the family's rather than the
    variable's (`chain_segment_length` is `2..64 by 1` on the binding
    and `8..64 by 8` under the family that declares it). Rebuilding
    that traversal outside this function reproduces its conditions
    approximately and its narrowing not at all; passing a chooser walks
    the same path the render walks, so a sampled design is legal by
    construction and needs no repair afterwards. The chooser must
    answer the same name the same way within one call, since a value is
    asked for again as the parent of each of its children."""
    inst, bindings = ctx.instance, ctx.bindings
    from chialu.declaration_values import canonical_vars
    overrides = canonical_vars(ctx, overrides or {})
    out = Selections()
    resolved_aliases = _shared_exit_defaults(ctx, manifest, overrides, set(_automatic_overrides), out.ignored)
    _automatic_overrides = set(_automatic_overrides) | (resolved_aliases.keys() - overrides.keys())
    overrides.update(resolved_aliases)

    def value_of(name):
        variable = inst.tree.resolve(name)
        if variable is not None and variable.when and not variable.condition_holds(value_of(variable.parent)):
            return None
        if name in overrides:
            return overrides[name]
        b = bindings.get(name)
        if b is None:
            return None
        if b.time == "fixed":
            return b.value
        return choose(name, b.domain) if choose is not None else b.domain.default()

    for s in manifest:
        if not s.slot or not s.library:
            continue
        base = f"core.{s.slot}.{s.index}"
        if base in out:
            continue
        fam = value_of(base + ".family")
        if fam is None:
            continue
        # a unit mixing decimal and binary modes opens both classes under one slot: a structure's default is the
        # first family of its own format's class, and an explicit family of the other class is an error
        from chialu.targets.rtl.families.decimal import DECIMAL_FAMILIES
        decimal = DECIMAL_FAMILIES.get(s.kind, ())
        if decimal:
            from chialu.verify.formats import BCDFormat, parse_format
            try:
                is_bcd = isinstance(parse_format(s.format), BCDFormat)
            except ValueError:
                is_bcd = False
            if (fam in decimal) != is_bcd:
                name = base + ".family"
                b = bindings.get(name)
                explicit = (name in overrides and name not in _automatic_overrides) or (b is not None and b.time == "fixed")
                cls = "decimal" if fam in decimal else "binary"
                want = "decimal" if is_bcd else "binary"
                if explicit:
                    raise ValueError(f"{name}={fam}: a {cls} family for {s.id}, whose format {s.format} needs a {want} one")
                members = b.domain.members() if b is not None and b.domain.finite() else []
                fam = next((m for m in members if (m in decimal) == is_bcd), None)
                if fam is None:
                    raise ValueError(f"{name}: no {want} family in the domain for {s.id} ({s.format})")
        pins = {}

        def walk(name, value):
            """The active descendants of a variable at `value`: the family's
            choices and its component slots' families and choices, keyed
            relative to the structure (`reduction.cpa.adder.topology`)."""
            for child in inst.tree.children_of(name):
                if not child.condition_holds(value):
                    continue
                if not child.name.startswith(base + "."):
                    # another structure's slot opened by this one (the fp_adder and fp_multiplier slots under
                    # the fp_fma's separate_multiplier_and_adder): its pins are its own
                    continue
                v = value_of(child.name)
                if v is None:
                    continue
                pins[child.name[len(base) + 1:]] = v
                walk(child.name, v)

        walk(base + ".family", fam)
        # a posit unit whose ops include fdiv or fsqrt needs the add_mul_div operator set: an undeclared
        # operator_set follows the ops (its domain default is add_mul), an explicit add_mul stays an error the seed raises
        if s.kind == "posit_unit" and str(fam) == "posit_adder_multiplier" and pins.get("operator_set") == "add_mul" \
                and set(s.ops) & {"fdiv", "fsqrt"}:
            name = base + ".operator_set"
            b = bindings.get(name)
            explicit = (name in overrides and name not in _automatic_overrides) or (b is not None and b.time == "fixed")
            if not explicit and b is not None and b.domain.contains("add_mul_div"):
                pins["operator_set"] = "add_mul_div"
                walk(name, "add_mul_div")
        out[base] = (str(fam), _active_pins(ctx, base, s.kind, str(fam), pins,
                                          overrides, _automatic_overrides, s.width, out.ignored))
    # the core family itself and its unit-level component slots (the representation of a
    # redundant_internal core, the channels of an rns_internal core): the lanes' adders,
    # multipliers and comparators follow them
    core = value_of("core.family")
    if core is not None:
        out["core"] = (str(core), {})
        for slot in ("representation", "channels"):
            fam = value_of(f"core.{slot}.family")
            if fam is None:
                continue
            pins = {}

            def walk_slot(name, value, base=f"core.{slot}"):
                for child in inst.tree.children_of(name):
                    if not child.condition_holds(value):
                        continue
                    v = value_of(child.name)
                    if v is None:
                        continue
                    pins[child.name[len(base) + 1:]] = v
                    walk_slot(child.name, v, base)

            walk_slot(f"core.{slot}.family", fam)
            out[f"core.{slot}"] = (str(fam), _active_pins(ctx, f"core.{slot}", slot,
                                                          str(fam), pins, overrides, _automatic_overrides, ignored=out.ignored))
    # the unit-level slot without a structure: how the lanes of one datapath are packed
    sub = value_of("core.subword.family")
    if sub is not None:
        binary_adders = [s for s in manifest if s.kind == "adder" and s.format.startswith(("int", "uint", "fxs"))
                         and not s.format.endswith(("_sm", "_ones", "_sign_magnitude", "_ones_complement"))]
        if sub == "partitioned_carry_chain" and not binary_adders:
            name = "core.subword.family"
            binding = bindings.get(name)
            explicit = (name in overrides and name not in _automatic_overrides) or binding.time == "fixed"
            if explicit or not binding.domain.contains("replicated_lanes"):
                raise ValueError("core.subword.family=partitioned_carry_chain requires binary integer adder structures")
            sub = "replicated_lanes"
        pins = {}
        for child in inst.tree.children_of("core.subword.family"):
            if child.condition_holds(sub):
                v = value_of(child.name)
                if v is not None:
                    pins[child.name[len("core.subword."):]] = v
        out["core.subword"] = (str(sub), _active_pins(ctx, "core.subword", "subword",
                                                    str(sub), pins, overrides, _automatic_overrides, ignored=out.ignored))
    _reject_unselected_choices(ctx, out, overrides, _automatic_overrides, out.ignored)
    return out


def core_family_of(ctx, overrides: dict | None = None, *, _automatic_overrides=()) -> tuple:
    """(family, {choice: value}) of a unit whose architecture is one
    family at the core (`core.family`: the dot accumulator's and the
    SFU's spaces): the declared value (`overrides`) first, else a fixed
    binding's value, else the domain default; the pins are the family's
    active choices and component families, keyed relative to `core.`."""
    inst, bindings = ctx.instance, ctx.bindings
    from chialu.declaration_values import canonical_vars
    overrides = canonical_vars(ctx, overrides or {})

    def value_of(name):
        variable = inst.tree.resolve(name)
        if variable is not None and variable.when and not variable.condition_holds(value_of(variable.parent)):
            return None
        if name in overrides:
            return overrides[name]
        b = bindings.get(name)
        if b is None:
            return None
        return b.value if b.time == "fixed" else b.domain.default()

    fam = value_of("core.family")
    if fam is None:
        return None
    pins = {}

    def walk(name, value):
        for child in inst.tree.children_of(name):
            if not child.condition_holds(value):
                continue
            v = value_of(child.name)
            if v is None:
                continue
            pins[child.name[len("core."):]] = v
            walk(child.name, v)

    walk("core.family", fam)
    spec = spec_of(ctx)
    kind = "dot" if spec.get("unit") == "vec_dot_acc" else "sfu"
    from chialu.verify.formats import parse_format
    width = max(parse_format(m.get("format_ab", m.get("format"))).width for m in spec["modes"])
    selected = str(fam), _active_pins(ctx, "core", kind, str(fam), pins, overrides, _automatic_overrides, width)
    _reject_unselected_choices(ctx, {"core": selected}, overrides, _automatic_overrides)
    return selected


def seed(ctx, plan: str):
    """The seed of a sharing plan: (text, VAR values, STRUCTURE lines)."""
    from chialu.plans import partition, group_of
    from chialu.targets.rtl.structures import strip_manifest_header
    spec = spec_of(ctx)
    if spec.get("unit") != "alu":
        vars_ = declared_vars(ctx, plan)
        text = derive.seed_for(spec, family=core_family_of(ctx, vars_))
        return strip_manifest_header(text), vars_, []
    from chialu.targets.rtl.alu_seed import structure_manifest
    from chialu.targets.rtl import families as FAM
    manifest = structure_manifest(spec)
    vars_ = declared_vars(ctx, plan)
    with FAM.library_realization(realization_of(ctx) == "library"):
        families = families_of(ctx, manifest, vars_)
        # None lets selected families construct their required baseline groups
        # (PG fusion, shared format rounders). An explicit plan stays strict.
        part = None if plan == "baseline" else split_fixed_families(partition(manifest, plan), manifest, ctx.bindings)
        st = derive.seed_alu_text(spec, part, families=families)
        groups = group_of([(unit.name, unit.members) for unit in st.units])
        for s in st.structures:
            s.group = groups.get(s.id, "")
        return seed_output(ctx, st), vars_, st.structures.declaration_lines()


def realization_of(ctx_or_instance) -> str:
    """`library` or `behavioral`: the run file's `realization` (library
    unless bound otherwise)."""
    from chialu.modules.common import vals
    b = getattr(ctx_or_instance, "bindings", None) or {}
    v = vals(b, "realization")
    return str(v[0]) if v else "library"
