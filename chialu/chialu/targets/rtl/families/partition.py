"""Validate physical sharing requested by an ALU structure partition."""
from collections import Counter

# a float kind whose structures across modes are one physical datapath per lane position at the union
# geometry of those modes, the operands muxed by the mode (alu_seed._grouped_across_modes for arithmetic,
# alu_fp_share.emit_format_groups for rounders and unpackers)
FP_SHARE_KINDS = ({"fp_adder"}, {"fp_multiplier"}, {"fp_comparator"}, {"fp_divider"},
                  {"rounder"}, {"unpacker"})
# the integer kinds whose structures across modes are one library instance per lane position at the widest
# served width (alu_seed.XS_KINDS, _xs_glue)
XS_KINDS = ("adder", "multiplier", "comparator", "shifter", "logic", "bitcount")


def is_float_structure(st) -> bool:
    from chialu.verify.formats import FloatFormat, parse_format
    try:
        return isinstance(parse_format(st.format), FloatFormat)
    except ValueError:
        return False


def validate_partition(manifest, partition, selections):
    from chialu.targets.rtl.structures import is_inline
    from .selection import SelectionError
    if partition is None:
        return
    # an fp_fma structure under separate_multiplier_and_adder has no unit of its own (the adder's and the
    # multiplier's structures realize the ops), so no group needs to hold it, unless it carries a fused
    # multiply-add op, which the two structures compute together in one unit
    required = {st.id for st in manifest if st.slot and not is_inline(st)
                and not (st.kind == "fp_fma" and not multiply_add_unit(st, selections))}
    members = Counter(member for _, group in partition for member in group)
    missing = required - members.keys()
    repeated = {member for member, count in members.items() if count > 1}
    unknown = members.keys() - {st.id for st in manifest}
    if missing or repeated or unknown:
        raise SelectionError(f"partition membership: missing={sorted(missing)}, repeated={sorted(repeated)}, unknown={sorted(unknown)}")
    from chialu.targets.rtl.alu_seed import sv_ident
    names = [sv_ident(name) for name, _ in partition]
    if len(set(names)) != len(names):
        raise SelectionError("partition unit names collide as RTL identifiers")
    for name, group in partition:
        structures = [manifest.get(member) for member in group if member in required]
        if len(structures) < 2:
            continue
        kinds = {st.kind for st in structures}
        chosen = [selections.get(f"core.{st.slot}.{st.index}") for st in structures]
        same = all(value == chosen[0] for value in chosen) and chosen[0] is not None
        if kinds == {"adder", "logic"} and len({(st.width, st.lane) for st in structures}) == 1:
            logic = [st for st in structures if st.kind == "logic"]
            if all(selections.get(f"core.logic.{st.index}", (None,))[0] == "alu_pg_fused" for st in logic):
                continue
        if same and kinds == {"logic"} and chosen[0][0] == "wide_gate_row" and all(st.format.startswith(("int", "uint", "fxs", "bcd")) for st in structures):
            continue
        binary = all(st.format.startswith(("int", "uint", "fxs")) and not st.format.endswith(("_sm", "_ones", "_sign_magnitude", "_ones_complement"))
                     for st in structures)
        if same and binary and ((kinds == {"logic"} and chosen[0][0] == "wide_gate_row") or
                                (kinds == {"multiplier"} and chosen[0][0] == "twin_precision_subword")):
            continue
        if kinds == {"adder"} and binary and selections.get("core.subword", (None,))[0] == "partitioned_carry_chain":
            continue
        # the integer adders' lane-partitioned adder, wide enough for the float adders' significand add, serves both:
        # the float adder families take the adder through ports (fp.py add_sv, sig_adder.external)
        if kinds == {"adder", "fp_adder"} and selections.get("core.subword", (None,))[0] == "partitioned_carry_chain":
            ints = [st for st in structures if st.kind == "adder"]
            fps = [st for st in structures if st.kind == "fp_adder"]
            ints_binary = all(st.format.startswith(("int", "uint", "fxs")) and not st.format.endswith(("_sm", "_ones", "_sign_magnitude", "_ones_complement"))
                              for st in ints)
            from chialu.verify.formats import FloatFormat, parse_format

            def is_float(st) -> bool:
                try:
                    return isinstance(parse_format(st.format), FloatFormat)
                except ValueError:
                    return False
            if ints and fps and ints_binary and all(st.lane == 0 and is_float(st) for st in fps):
                continue
        if kinds in FP_SHARE_KINDS and all(is_float_structure(st) for st in structures):
            kind = structures[0].kind
            if len({st.mode for st in structures}) == 1:
                raise SelectionError(f"partition {name}: {kind} lanes of the same mode compute simultaneously; "
                                     "packed-SIMD sharing is not implemented; put each lane in its own group: "
                                     + ", ".join(st.id for st in structures))
            if not same:
                raise SelectionError(f"partition {name}: cross-mode {kind} sharing requires identical families "
                                     "and pins; copy one member's family and choices to every member, or split "
                                     "the group: " + ", ".join(st.id for st in structures))
            if kinds in ({"rounder"}, {"unpacker"}) and not any(
                    len({st.mode for st in structures if st.lane == lane}) > 1
                    for lane in {st.lane for st in structures}):
                raise SelectionError(f"partition {name}: {kind} sharing requires a common lane position across "
                                     "modes; group lane 0 with lane 0, lane 1 with lane 1, or split the group")
        # a float kind's structures across two formats or more: one datapath per lane position at the union
        # geometry of the modes, its operands muxed by the mode. The members declare one family and one pin
        # set, since one module serves them; a group inside one mode is not a sharing (its lanes compute at
        # once), which the distinct-format test refuses
        if same and kinds in FP_SHARE_KINDS and all(is_float_structure(st) for st in structures) \
                and len({st.format for st in structures}) >= 2:
            continue
        # an integer kind's structures across two modes or more, without the kind's own sharing family (the
        # partitioned adder, the twin-precision matrix, the wide gate row, taken above where selected): one
        # library instance per lane position at the widest served width, the operands extended and muxed by the
        # mode, since one mode computes per operation (alu_seed._xs_glue). The members declare one family and
        # one pin set; a group inside one mode is refused (its lanes compute at once)
        if same and binary and len(kinds) == 1 and next(iter(kinds)) in XS_KINDS \
                and chosen[0][0] != "alu_pg_fused" and len({st.mode for st in structures}) >= 2:
            continue
        # a fused multiply-add: the mode's fp_fma, fp_adder and fp_multiplier are one datapath per lane (or one
        # unit, under the sequential contract of the fused ops through the separate multiplier and adder)
        if kinds <= {"fp_adder", "fp_fma", "fp_multiplier"} and "fp_fma" in kinds \
                and fused_multiply_add_group(structures, selections):
            continue
        # a comparator rides its lane's adder (min/max/cmp from the subtractor): one adder and one comparator per
        # (mode, lane) of a binary integer mode, which the seed's unit realizes as a lane module with both kinds
        if len(kinds) > 1 and "adder" in kinds and kinds <= {"adder", "comparator", "logic"} and binary:
            per_lane = Counter((st.mode, st.lane, st.kind) for st in structures)
            lanes = {(m, l) for m, l, _k in per_lane}
            # A union of lane-local mechanisms: comparator -> subtractor and
            # PG logic -> adder. Each consumer needs its own lane's adder; the
            # lanes still compute concurrently in separate lane modules.
            if all(per_lane.get((m, l, "adder")) == 1
                   and all(per_lane.get((m, l, k), 0) <= 1 for k in ("comparator", "logic"))
                   for m, l in lanes) and all(
                       selections.get(f"core.logic.{st.index}", (None,))[0] == "alu_pg_fused"
                       for st in structures if st.kind == "logic"):
                continue
        raise SelectionError(f"partition {name}: physical sharing is not implemented for these selected structures: "
                             + ", ".join(st.id for st in structures))


def fused_multiply_add_selected(st, selections) -> bool:
    """Whether an fp_fma structure selects a fused family (one datapath for
    fadd, fsub and fmul) rather than separate_multiplier_and_adder."""
    return selections.get(f"core.fp_fma.{st.index}", (None,))[0] not in (None, "separate_multiplier_and_adder")


FUSED_OPS = ("fmadd", "fmsub", "fnmsub", "fnmadd")


def multiply_add_unit(st, selections) -> bool:
    """Whether an fp_fma structure needs a unit with its lane's adder and
    multiplier: it selects a fused family (one datapath for fadd, fsub,
    fmul and the fused ops), or it carries a fused multiply-add op, which
    the separate multiplier then adder compute under the sequential
    contract in one lane module."""
    return fused_multiply_add_selected(st, selections) or any(op in FUSED_OPS for op in st.ops)


def fused_multiply_add_group(structures, selections) -> bool:
    """Whether a group of fp_fma, fp_adder and fp_multiplier structures is
    a multiply-add's: every fp_fma needs the unit (multiply_add_unit) and
    every (mode, lane) holds one fp_fma and at most one structure of each
    other kind."""
    fmas = [st for st in structures if st.kind == "fp_fma"]
    if not fmas or not all(multiply_add_unit(st, selections) for st in fmas):
        return False
    per_lane = Counter((st.mode, st.lane, st.kind) for st in structures)
    lanes = {(m, l) for m, l, _k in per_lane}
    return all(per_lane.get((m, l, "fp_fma")) == 1 and per_lane.get((m, l, k), 0) <= 1
               for m, l in lanes for k in ("fp_adder", "fp_multiplier"))


def fuse_multiply_add(manifest, partition, selections):
    """The partition with each fused fp_fma's adder and multiplier (same
    mode and lane) in the fp_fma's group, and each separate fp_fma out of
    every group: one fused datapath serves fadd, fsub and fmul, or the two
    slots' own units do (alu_pg.fuse_partition does the same for the fused
    logic row). An explicit partition must already share a fused one; a
    group of a separate fp_fma with its lane's adder and multiplier alone
    splits into their own units."""
    from .selection import SelectionError
    fmas = [st for st in manifest if st.kind == "fp_fma"]
    if not fmas:
        return partition
    from chialu.targets.rtl.alu_seed import default_partition
    explicit = partition is not None
    groups = [(name, list(members)) for name, members in (partition if explicit else default_partition(manifest))]
    for fma in fmas:
        if not multiply_add_unit(fma, selections):
            for index, (_name, members) in enumerate(groups):
                if fma.id in members:
                    members.remove(fma.id)
                    # a group that held the separate fp_fma with its own lane's adder and multiplier alone (the
                    # fused_fma plan's group under a mode that stays separate) splits back into their own units
                    own = {st.id for st in manifest if st.kind in ("fp_adder", "fp_multiplier")
                           and st.mode == fma.mode and st.lane == fma.lane}
                    if members and set(members) <= own and len(members) > 1:
                        split = [(member, [member]) for member in members]
                        groups[index:index + 1] = split
                    break
            continue
        # the lane's adder and multiplier structures, whichever the mode's ops register (a fused family serves the
        # ops the mode has; the sequential contract's fused ops need both)
        adder = next((st for st in manifest if st.kind == "fp_adder" and st.mode == fma.mode and st.lane == fma.lane), None)
        mul = next((st for st in manifest if st.kind == "fp_multiplier" and st.mode == fma.mode and st.lane == fma.lane), None)
        ids = {fma.id} | {st.id for st in (adder, mul) if st is not None}
        owners = [i for i, (_, members) in enumerate(groups) if ids & set(members)]
        if explicit and (len(owners) != 1 or not ids <= set(groups[owners[0]][1])):
            # the fused datapath realizes its lane's fadd, fsub and fmul, so its adder and multiplier structures
            # have no unit of their own: a plan that leaves them in units of their own (it names no group for
            # them), or groups them with other modes' structures (a sharing across formats the fused mode takes
            # no part in), has them absorbed into the fp_fma's unit; the rest of such a group keeps its sharing
            # (a group left with one member is that member's own unit). The fp_fma structure itself must sit in
            # a unit of its own or already with its lane's structures
            home = next(i for i in owners if fma.id in groups[i][1])
            if set(groups[home][1]) - ids:
                raise SelectionError(f"a fused multiply-add partition must share {', '.join(sorted(ids))}")
            for sid in sorted(ids - set(groups[home][1])):
                index = next(i for i, (_, members) in enumerate(groups) if sid in members)
                name, members = groups[index]
                members.remove(sid)
                rest = [manifest.get(m) for m in members]
                if len(rest) == 1 and name != members[0]:
                    groups[index] = (members[0], members)
                elif len(rest) > 1 and len({st.kind for st in rest}) == 1 and len({st.mode for st in rest}) == 1:
                    # the rest is one mode's lanes, which compute at once: the sharing across formats is void
                    groups[index:index + 1] = [(m, [m]) for m in members]
                next(ms for _n, ms in groups if fma.id in ms).append(sid)
            continue
        # the fused unit keeps the fp_fma structure's group (and so its name)
        keep = next(i for i in owners if fma.id in groups[i][1])
        for index in sorted((i for i in owners if i != keep), reverse=True):
            groups[keep][1].extend(groups[index][1])
            groups.pop(index)
    return [(name, tuple(members)) for name, members in groups if members]


def word_datapath(structures, selections) -> bool:
    """Whether a group of one integer kind is one full-word datapath that
    computes every lane of each mode it serves: a gate row under
    wide_gate_row, a twin-precision matrix, a lane-partitioned adder under
    the partitioned carry chain."""
    kinds = {st.kind for st in structures}
    if len(kinds) != 1:
        return False
    kind = next(iter(kinds))
    binary = all(st.format.startswith(("int", "uint", "fxs")) and not st.format.endswith(
        ("_sm", "_ones", "_sign_magnitude", "_ones_complement")) for st in structures)
    chosen = {selections.get(f"core.{st.slot}.{st.index}", (None,))[0] for st in structures}
    if kind == "logic":
        return chosen == {"wide_gate_row"} and all(st.format.startswith(("int", "uint", "fxs", "bcd")) for st in structures)
    if kind == "multiplier":
        return binary and chosen == {"twin_precision_subword"}
    if kind == "adder":
        return binary and selections.get("core.subword", (None,))[0] == "partitioned_carry_chain"
    return False


def complete_word_groups(manifest, partition, selections):
    """The partition with every lane of a mode that a full-word group
    serves (word_datapath) in that group: the one row, matrix or
    partitioned adder already computes the mode's every lane, so a lane
    left in a unit of its own (a per-lane grouping: lane 0 of every mode
    together, the second lane of a two-lane mode alone) would be a second
    copy of the whole datapath. Only a lane in a unit of its own joins;
    one another group holds stays there."""
    if partition is None:
        return partition
    groups = [(name, list(members)) for name, members in partition]
    for index, (_name, members) in enumerate(groups):
        sts = [manifest.get(m) for m in members]
        if len(sts) < 2 or not word_datapath(sts, selections):
            continue
        kind = sts[0].kind
        served = {st.mode for st in sts}
        for other_index, (_other, others) in enumerate(groups):
            if other_index == index or len(others) != 1:
                continue
            st = manifest.get(others[0])
            if st is not None and st.kind == kind and st.mode in served and word_datapath(sts + [st], selections):
                members.append(others.pop())
    return [(name, tuple(members)) for name, members in groups if members]
