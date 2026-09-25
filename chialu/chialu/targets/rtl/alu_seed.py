"""The behavioral reference of a chialu.ALU spec in SystemVerilog, as a
hierarchy of one module per physical structure.

`alu_seed(spec, name)` builds the seed from the spec's modes and ops:
the top module `alu_core` (the spec's ports from alu_ref.alu_layout,
the control decode, the ops without an architecture slot, the mode mux)
instantiates one module per physical structure of the partition (a seed
structure, or a `shared` group of them), each computing the results of
its lanes and ops on result buses the top ORs together (one op is active
at a time, so the buses are disjoint). Every (mode, op) pair computes
the verify layer's exact semantics; the text carries the structure
manifest in its header. The default partition is one module per seed
structure with an architecture slot; the instance's or a design point's
`shared` groups give a coarser one.

The checker instantiates pruned monolithic copies of the same logic
(`alu_ref_module`, force = 1 rounds toward zero, 2 away from zero: the
two ends of the one-ulp window of an unchecked SR)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from chialu.verify.ports import Port
from chialu.targets.rtl.alu_block import BlockModeEmitter
from chialu.targets.rtl.alu_float import FloatModeEmitter
from chialu.targets.rtl.alu_int import IntModeEmitter
from chialu.targets.rtl.engine import (FORCE_NONE, FORCE_RAZ, FORCE_RTZ,  # noqa: F401
                                       FORCE_RND_EXPR, FW, RND, Engine, flag_bit,
                                       fmt_tag)
from chialu.targets.rtl.alu_mode import LANE, Expr
from chialu.targets.rtl.structures import INLINE_KINDS, KIND_SLOT, StructureManifest, is_inline, kind_of
from chialu.targets.rtl.writer import SvModule, SvPackage
from chialu.targets.rtl.families.module_library import ModuleLibrary, collect_modules, dedupe_modules
from chialu.verify import alu_ref as A
from chialu.verify.formats import BlockFormat

_tag = fmt_tag           # the historical name, still imported by dot_seed
MODULE_RE = re.compile(r"^\s*module\s+([A-Za-z_]\w*)", re.M)


@dataclass
class SeedUnit:
    """One physical structure of the seed: a module realizing the seed
    structures `members` (one kind, or an integer kind with its float
    counterpart: the unit's kind is then the integer one) for their lanes."""
    name: str               # the unit name (a structure id or a group name)
    members: tuple          # structure ids
    kind: str
    slot: str | None
    module: str             # the SV module name

    def lanes_of(self, manifest, mi: int) -> list:
        return sorted({manifest.get(m).lane for m in self.members
                       if manifest.get(m).mode == mi})

    def kinds_in(self, manifest, mi: int) -> tuple:
        """The kinds of the members this unit serves in mode `mi`, sorted
        (an adder with the comparators it absorbs, or one kind)."""
        return tuple(sorted({manifest.get(x).kind for x in self.members
                             if manifest.get(x).mode == mi}))

    def kind_in(self, manifest, mi: int) -> str:
        """The kind of the datapath this unit is in mode `mi`: the one
        kind of its members there, or the deepest common ancestor of
        several (a comparator rides the adder), which decides the ports."""
        ks = self.kinds_in(manifest, mi)
        if not ks:
            return self.kind
        if len(ks) == 1:
            return ks[0]
        try:
            return manifest.group_kind(set(ks))
        except ValueError:
            return ks[0]

    def modes(self, manifest) -> list:
        return sorted({manifest.get(m).mode for m in self.members})


@dataclass
class SeedText:
    text: str
    structures: StructureManifest
    top: str = ""                                   # the top module alone
    modules: dict = field(default_factory=dict)     # module name -> text
    units: list = field(default_factory=list)       # SeedUnit per module
    members: dict = field(default_factory=dict)     # member name -> text (member_names order): the multi-file seed

    def __str__(self):
        return self.text

    def unit_of(self, unit_name: str):
        return next((u for u in self.units if u.name == unit_name), None)


MEMBER_HEAD = ("packages", "top")
MEMBER_TAIL = ("library",)


def member_names(manifest) -> list:
    """The members of the multi-file seed, fixed for an instance whatever
    the sharing plan: `packages` (the engine functions), `top` (the top
    module and its inline helpers), one member per slotted structure
    (`m0_l0_adder`: the unit module realizing it, or a pointer to the
    member that does), and `library` (the family library modules)."""
    from chialu.targets.rtl.structures import is_inline
    return list(MEMBER_HEAD) + [sv_ident(s.id) for s in manifest if s.slot and not is_inline(s)] + list(MEMBER_TAIL)


def _members_of(manifest, pkg_text: str, top_text: str, units: list, modules: dict, lane_mods: dict,
                misc_mods: dict, blk_mods: dict, library_used: dict) -> dict:
    """The member texts of a rendered seed: a unit's module goes to the
    member of its first structure; a lane module (one per mode and kind,
    shared by that kind's lanes and units) to the member of the first
    structure of its mode and kind; the misc and block-conversion helpers
    stay with the top; the other structure members carry the pointer."""
    from chialu.targets.rtl.structures import is_inline
    structs = [s for s in manifest if s.slot and not is_inline(s)]
    by_id = {s.id: sv_ident(s.id) for s in structs}
    bodies: dict = {m: [] for m in member_names(manifest)}
    home: dict = {}                                   # structure id -> the member holding its module
    for u in units:
        first = next((m for m in u.members if m in by_id), None)
        if first is None:
            bodies["top"].append(modules[u.module])
            continue
        bodies[by_id[first]].append(modules[u.module])
        for m in u.members:
            if m in by_id:
                home[m] = by_id[first]
    for key in sorted(lane_mods, key=str):
        mi, kind = key[0], key[1]                     # (mode, kind[, target]) of a lane module
        first = next((s for s in structs if s.mode == mi and s.kind == kind), None)
        (bodies[by_id[first.id]] if first is not None else bodies["top"]).append(lane_mods[key])
    bodies["packages"].append(pkg_text)
    bodies["top"].insert(0, top_text)
    bodies["top"] += [misc_mods[k] for k in sorted(misc_mods)] + [blk_mods[k] for k in sorted(blk_mods)]
    bodies["library"] += [library_used[k] for k in sorted(library_used)]
    out = {}
    for name, parts in bodies.items():
        text = "\n".join(t for t in parts if t)
        if not text and name in by_id.values():
            sid = next(s.id for s in structs if by_id[s.id] == name)
            where = home.get(sid)
            text = (f"// {sid}: realized by the unit module in member {where}\n" if where
                    else f"// {sid}: realized inline in the top (member top)\n")
        elif name == "library":
            text = ("// ---- the family library modules the lane modules instantiate (chialu/targets/rtl/families; "
                    "fixed text, replaced by editing the instances)\n" + text) if text else "// no library modules\n"
        out[name] = text if text.endswith("\n") else text + "\n"
    return out


def sv_ident(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def _emitter_class(fam: str):
    if fam == "block":
        return BlockModeEmitter
    if fam in ("float", "posit"):
        return FloatModeEmitter
    return IntModeEmitter


def _legal(lay, skip):
    return {pr for pr in lay["legal"] if pr not in set(skip)}


def structure_manifest(spec: dict) -> StructureManifest:
    """The manifest of a spec without emitting: every legal (mode, op,
    lane) registered through the emitters."""
    spec = A.normalize_spec(spec)
    lay = A.alu_layout(spec)
    modes, ops = lay["modes"], lay["ops"]
    manifest = StructureManifest()
    scratch = SvModule("scratch")
    for mi, (count, fmt) in enumerate(modes):
        ops_legal = [(oi, op) for oi, op in enumerate(ops) if (mi, op) in lay["legal"]]
        g = _emitter_class(A.family_of(fmt))(spec, lay, mi, count, fmt, ops_legal,
                                             FORCE_NONE, scratch, manifest)
        for _oi, op in ops_legal:
            g.register_op(op)
    return manifest


def default_partition(manifest: StructureManifest) -> list:
    """One physical structure per seed structure that has a slot."""
    return [(st.id, (st.id,)) for st in manifest if st.slot]


X_PRODUCERS = ("fp_adder", "fp_multiplier", "fp_fma", "fp_divider", "converter")
ROUNDS = ("fadd", "fsub", "fmul", "fdiv", "fsqrt") + tuple(A.FUSED_OPS)


def _rounds_op(op: str) -> bool:
    if op in ROUNDS:
        return True
    tgt = A.cvt_target(op)
    return tgt is not None and not isinstance(tgt, BlockFormat)


def _split_of(fam: str, kind: str) -> tuple:
    """(split, shared_unpack) of a lane module: only a float mode's datapath
    is split into unpacker, producers and rounder."""
    if fam != "float":
        return None, False
    if kind == "unpacker":
        return "unpacker", False
    if kind == "rounder":
        return "rounder", True
    if kind in X_PRODUCERS:
        return "producer", True
    return None, True                    # fp_comparator, logic: read the unpacker's buses


def _extra_ports(fam: str, kind: str, mi: int, count: int, XT: int, dual: bool, ternary: bool = False) -> list:
    """(name, direction, width) beyond the result buses: the unpacked
    operand buses every float lane module reads (the unpacker writes; a
    third one, c, for a mode with a fused multiply-add op, `ternary`), the
    x bus the producers write and the rounder reads."""
    if fam != "float":
        return []
    xw = count * XT
    srcs = ("a", "b", "c") if ternary else ("a", "b")
    unp = [(f"x{src}_m{mi}", "out", xw) for src in srcs] + [(f"den{src}_m{mi}", "out", count) for src in srcs]
    if kind == "unpacker":
        return unp
    ports = [(n, "in", w) for n, _d, w in unp]
    if kind in X_PRODUCERS:
        ports.append((f"x_m{mi}", "out", xw))
        if dual:
            ports.append((f"xd_m{mi}", "out", xw))
    if kind == "rounder":
        ports.append((f"x_m{mi}", "in", xw))
        if dual:
            ports.append((f"xd_m{mi}", "in", xw))
    return ports


def _shared_ports(shared: dict, kind: str, mi: int, W: int) -> list:
    """(name, direction, width) of the buses a lane module of `kind` shares
    with its unit under subword sharing: the twin-precision multiplier's
    packed product bus, the partitioned adder's operand / carry-in buses
    (the lane writes its slice) and its sum / carry-out buses."""
    out = []
    if kind == "multiplier" and "multiplier" in shared:
        out.append((f"tp_p_m{mi}", "in", 2 * W))
    if kind == "adder" and "adder" in shared:
        L = W // int(shared["adder"]["fine"])
        out += [(f"pc_a_m{mi}", "out", W), (f"pc_b_m{mi}", "out", W), (f"pc_cin_m{mi}", "out", L),
                (f"pc_s_m{mi}", "in", W), (f"pc_co_m{mi}", "in", L)]
    info = shared.get(f"xs_{kind}")
    if info is not None:
        # the lane's operands out to, and its results back from, the unit's instance shared across modes
        out += [(f"xs_{kind}_{sig}_m{mi}", "out" if operand else "in", info["count"] * width)
                for sig, operand, width in xs_signals(kind, info)]
    if kind == "fp_adder" and "fp_cpa" in shared:
        # the float adder's significand add on the unit's carry-propagate adder shared with the integer adders
        iw = int(shared["fp_cpa"]["iw"])
        out += [(f"sa_a_m{mi}", "out", iw), (f"sa_b_m{mi}", "out", iw), (f"sa_cin_m{mi}", "out", 1),
                (f"sa_s_m{mi}", "in", iw), (f"sa_cout_m{mi}", "in", 1)]
    return out


def _shared_of(u, manifest, mi, modes, families: dict | None, W: int, xw: dict | None = None) -> dict:
    """kind -> sharing info for a unit and mode: the multiplier structures
    declaring twin_precision_subword share one gated matrix, the adder
    structures under the partitioned_carry_chain subword family share
    one lane-partitioned adder, a logic unit under wide_gate_row is one
    full-width gate row; only the binary integer modes take part. A unit
    whose members are integer adders and the float adders of single-lane
    float modes shares one carry-propagate adder between them (`fp_cpa`
    for the float mode: the significand width `iw`; `adder.fp` for the
    integer modes: the adder's width `w`, a multiple of the finest lane
    that holds the significand add and its carry-out bit)."""
    fams = families or {}
    fmt = modes[mi][1]
    logic = fams.get(f"core.logic.m{mi}")
    if u.kind == "logic" and logic and logic[0] == "wide_gate_row" and A.family_of(fmt) not in ("float", "posit", "block"):
        return {"logic": {"pins": logic[1], "served": u.modes(manifest)}}

    def is_int(m):
        f = modes[m][1]
        return getattr(f, "encoding", None) in ("twos_complement", "unsigned") and A.family_of(f) not in ("float", "posit", "block") \
            and W % f.width == 0
    member_kinds = {manifest.get(x).kind for x in u.members}
    fp_cpa = None
    sub = fams.get("core.subword")
    if "adder" in member_kinds and "fp_adder" in member_kinds and sub and sub[0] == "partitioned_carry_chain" and xw:
        int_modes = [m for m in u.modes(manifest) if is_int(m) and "adder" in u.kinds_in(manifest, m)]
        fp_modes = [m for m in u.modes(manifest) if A.family_of(modes[m][1]) == "float" and modes[m][0] == 1
                    and "fp_adder" in u.kinds_in(manifest, m)]
        if int_modes and fp_modes:
            iw = max(int(xw[m]) for m in fp_modes) + 1
            fine = min(modes[m][1].width for m in int_modes)
            w_sh = ((max(W, iw + 1) + fine - 1) // fine) * fine       # the carry-out of the significand add is bit iw
            fp_cpa = {"iw": iw, "w": w_sh, "fine": fine, "fp_modes": fp_modes, "int_modes": int_modes}
    if fp_cpa and A.family_of(fmt) == "float":
        return {"fp_cpa": fp_cpa}
    if getattr(fmt, "encoding", None) not in ("twos_complement", "unsigned") or A.family_of(fmt) in ("float", "posit", "block"):
        return {}
    kinds = set(u.kinds_in(manifest, mi))
    out = {}
    served = [m for m in u.modes(manifest)
              if getattr(modes[m][1], "encoding", None) in ("twos_complement", "unsigned")
              and A.family_of(modes[m][1]) not in ("float", "posit", "block") and W % modes[m][1].width == 0]
    mf = fams.get(f"core.multiplier.m{mi}")
    if "multiplier" in kinds and mf and mf[0] == "twin_precision_subword":
        if mi not in served:
            raise ValueError(f"core.multiplier.m{mi}: twin_precision_subword requires lane width {fmt.width} "
                             f"to divide word width {W}; use independent lane multipliers")
        out["multiplier"] = {"pins": mf[1], "served": served}
    sub = fams.get("core.subword")
    # a unit whose modes do not tile the bus (int12 beside uint4x4 on a 16-bit bus) keeps its own adder
    if "adder" in kinds and u.kind == "adder" and sub and sub[0] == "partitioned_carry_chain" and served:
        out["adder"] = {"pins": sub[1], "served": served, "fine": min(modes[m][1].width for m in served)}
        if fp_cpa:
            out["adder"]["fp"] = fp_cpa
    lf = fams.get(f"core.logic.m{mi}")
    if u.kind == "logic" and lf and lf[0] == "wide_gate_row":
        out["logic"] = {"pins": lf[1], "served": served}
    return out


# the integer kinds a group across modes realizes as one library instance per lane position at the widest
# served width, the lanes' operands muxed by the mode and extended to that width (_xs_glue); the kinds that
# have a sharing family of their own (the partitioned adder, the twin-precision matrix, the wide gate row)
# take that instead where it is selected
XS_KINDS = ("adder", "multiplier", "comparator", "shifter", "logic", "bitcount")
XS_COUNT_OPS = ("popcount", "clz", "ctz")


def _xs_counts(families: dict | None, mi: int, width: int, legal) -> list:
    """The count ops of a mode whose declared bit-count family has a library
    module (a count op without one stays behavioral in its lane module)."""
    from chialu.targets.rtl import families as FAM
    sel = (families or {}).get(f"core.bitcount.m{mi}")
    if not sel:
        return []
    fns = {"popcount": FAM.popcount_module, "clz": FAM.lzc_module, "ctz": FAM.tzc_module}
    return [op for op in XS_COUNT_OPS if (mi, op) in legal and fns[op](sel[0], sel[1], width) is not None]


def xs_signals(kind: str, info: dict) -> list:
    """[(signal, operand?, width)] of a lane's side of a kind shared across
    modes, at the mode's width `info["w"]`."""
    w = int(info["w"])
    if kind == "adder":
        return [("a", True, w), ("b", True, w), ("cin", True, 1), ("s", False, w), ("co", False, 1)]
    if kind == "multiplier":
        return [("a", True, w), ("b", True, w), ("p", False, 2 * w)]
    if kind == "comparator":
        return [("a", True, w), ("b", True, w), ("lt", False, 1), ("eq", False, 1)]
    if kind == "shifter":
        return [("a", True, w), ("amt", True, max(1, (w - 1).bit_length())), ("op", True, 3), ("y", False, w)]
    if kind == "logic":
        return [("a", True, w), ("b", True, w), ("op", True, 2), ("y", False, w)]
    if kind == "bitcount":
        return [x for op in info.get("counts", ()) for x in ((f"{op}_a", True, w), (f"{op}_n", False, w.bit_length()))]
    raise ValueError(f"no shared-across-modes signals for kind {kind}")


def _xs_binary(fmt) -> bool:
    return getattr(fmt, "encoding", None) in ("twos_complement", "unsigned") \
        and A.family_of(fmt) not in ("float", "posit", "block", "bcd")


def xs_kind(u, manifest, modes) -> str | None:
    """The kind a unit shares across modes by one library instance per lane
    position (XS_KINDS), or None: its members are of that one kind, in
    binary integer modes, and span two modes or more (the lanes of one mode
    compute at once and never share)."""
    kinds = {manifest.get(m).kind for m in u.members}
    if len(kinds) != 1 or next(iter(kinds)) not in XS_KINDS:
        return None
    served = u.modes(manifest)
    if len(served) < 2 or not all(_xs_binary(modes[mi][1]) for mi in served):
        return None
    return next(iter(kinds))


def _xs_glue(m, u, kind: str, per_mode: dict, manifest, modes, families: dict, legal, mdw: int, library_used,
             name: str):
    """The unit's instances of a kind shared across modes: lane position r
    (the r-th member lane of each served mode) is one library module at the
    widest width among the modes it serves, its operands the mode's lane
    operands (off the lane modules' xs_ buses) extended to that width and
    muxed by the mode, its result sliced back to each mode's width. The
    extensions keep every result exact: an add low-aligned with the
    carry-out read at the mode's top bit, a product or a comparison
    sign- or zero-extended by the mode's encoding (one bit wider, signed,
    when the served encodings mix), a shift zero-, sign- (shr_arith) or
    replication-extended (a rotate on a width that divides the shared
    one), a leading- or trailing-zero count padded with ones below or
    above the mode's bits."""
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.fidelity import shared as record_sharing
    from chialu.targets.rtl.families.selection import register_origin
    slot = KIND_SLOT[kind]
    lanes = {mi: u.lanes_of(manifest, mi) for mi in per_mode}
    owners = {mi: f"core.{slot}.m{mi}" for mi in per_mode}
    selected = {mi: (families or {}).get(owners[mi]) for mi in per_mode}
    if any(sel is None for sel in selected.values()):
        raise ValueError(f"{u.name}: a {kind} shared across modes needs a declared family in every served mode")
    first = next(iter(per_mode))
    family, pins = selected[first]
    for mi, (fam_, pins_) in selected.items():
        if fam_ != family or dict(pins_) != dict(pins):
            raise ValueError(f"{u.name}: one {kind} shared across modes serves {owners[first]} ({family}) and "
                             f"{owners[mi]} ({fam_}); declare one family and one pin set for the group")

    def bus(mi, sig, width, lane):
        if per_mode[mi]["count"] * width == 1:
            return f"xs_{kind}_{sig}_m{mi}"                  # a one-bit bus is declared without a range
        return f"xs_{kind}_{sig}_m{mi}[{lane * width} +: {width}]"

    def zext(x, w, W):
        return x if w == W else f"{{{{{W - w}{{1'b0}}}}, {x}}}"

    def sext(x, sign, w, W):
        return x if w == W else f"{{{{{W - w}{{{sign}}}}}, {x}}}"
    ctrl = lambda mod_: "".join(f", .{n}({n})" for n, _w in (getattr(mod_, "ctrl", ()) or ()))  # noqa: E731
    results: dict = {}                               # (mi, sig) -> {lane: expression}
    n_pos = max(len(ls) for ls in lanes.values())
    for r in range(n_pos):
        entries = [(mi, lanes[mi][r]) for mi in per_mode if r < len(lanes[mi])]
        widths = {mi: modes[mi][1].width for mi, _l in entries}
        signed = {mi: modes[mi][1].encoding == "twos_complement" for mi, _l in entries}
        W = max(widths.values())
        mixed = len(set(signed.values())) > 1
        pos = f"xs_{kind}_r{r}"
        units = []                                   # (library module, instance, {port: (width, [(mi, expr)]) or result})
        if kind in ("multiplier", "comparator"):
            Wm, sgn = W + (1 if mixed else 0), any(signed.values())
            mod_ = (FAM.mul_module if kind == "multiplier" else FAM.comparator_module)(family, pins, Wm, sgn)

            def ext(mi, l, sig, Wm=Wm):
                w = widths[mi]
                x = bus(mi, sig, w, l)
                return sext(x, f"xs_{kind}_{sig}_m{mi}[{l * w + w - 1}]", w, Wm) if signed[mi] else zext(x, w, Wm)
            ins = {"a": (Wm, lambda mi, l: ext(mi, l, "a")), "b": (Wm, lambda mi, l: ext(mi, l, "b"))}
            outs = {"p": (2 * Wm, lambda mi, l, v: f"{v}[{2 * widths[mi] - 1}:0]")} if kind == "multiplier" else \
                {"lt": (1, lambda mi, l, v: v), "eq": (1, lambda mi, l, v: v)}
            units.append((mod_, Wm, ins, outs, ""))
        elif kind == "adder":
            mod_ = FAM.adder_module(family, pins, W)
            ins = {"a": (W, lambda mi, l: zext(bus(mi, "a", widths[mi], l), widths[mi], W)),
                   "b": (W, lambda mi, l: zext(bus(mi, "b", widths[mi], l), widths[mi], W)),
                   "cin": (1, lambda mi, l: bus(mi, "cin", 1, l))}
            outs = {"s": (W, lambda mi, l, v: f"{v}[{widths[mi] - 1}:0]"),
                    "co": (1, lambda mi, l, v: v if widths[mi] == W else f"xs_{kind}_s_r{r}[{widths[mi]}]")}
            units.append((mod_, W, ins, {"s": outs["s"], "cout": outs["co"]}, ""))
        elif kind == "shifter":
            mod_ = FAM.shifter_module(family, pins, W)
            aw = max(1, (W - 1).bit_length())
            for mi, _l in entries:
                if any((mi, op) in legal for op in ("rol", "ror")) and W % widths[mi]:
                    raise ValueError(f"{u.name}: a shifter shared across modes rotates mode {mi}'s {widths[mi]}-bit lanes "
                                     f"on a {W}-bit shifter, which needs the width to divide {W}")

            def sh_a(mi, l):
                w = widths[mi]
                x = bus(mi, "a", w, l)
                if w == W:
                    return x
                op = bus(mi, "op", 3, l)
                sign = f"xs_shifter_a_m{mi}[{l * w + w - 1}]"
                rot = f"{{{W // w}{{{x}}}}}" if W % w == 0 else zext(x, w, W)
                return f"((({op}) == 3'd3 || ({op}) == 3'd4) ? {rot} : ({op}) == 3'd2 ? {sext(x, sign, w, W)} : {zext(x, w, W)})"
            ins = {"a": (W, sh_a),
                   "amt": (aw, lambda mi, l: zext(bus(mi, "amt", max(1, (widths[mi] - 1).bit_length()), l),
                                                 max(1, (widths[mi] - 1).bit_length()), aw)),
                   "op": (3, lambda mi, l: bus(mi, "op", 3, l))}
            outs = {"y": (W, lambda mi, l, v: f"{v}[{widths[mi] - 1}:0]")}
            units.append((mod_, W, ins, outs, ", .sticky()"))
        elif kind == "logic":
            mod_ = FAM.logic_module(family, pins, W)
            ins = {"a": (W, lambda mi, l: zext(bus(mi, "a", widths[mi], l), widths[mi], W)),
                   "b": (W, lambda mi, l: zext(bus(mi, "b", widths[mi], l), widths[mi], W)),
                   "op": (2, lambda mi, l: bus(mi, "op", 2, l))}
            outs = {"y": (W, lambda mi, l, v: f"{v}[{widths[mi] - 1}:0]")}
            units.append((mod_, W, ins, outs, ""))
        else:                                        # bitcount: one counter per count op the served modes have
            for op in XS_COUNT_OPS:
                if not any(op in per_mode[mi].get("counts", ()) for mi, _l in entries):
                    continue
                fn = {"popcount": FAM.popcount_module, "clz": FAM.lzc_module, "ctz": FAM.tzc_module}[op]
                mod_ = fn(family, pins, W)

                def cnt(mi, l, op=op):
                    w = widths[mi]
                    x = bus(mi, f"{op}_a", w, l)
                    if w == W:
                        return x
                    ones = f"{{{W - w}{{1'b1}}}}"
                    return {"popcount": zext(x, w, W), "clz": f"{{{x}, {ones}}}", "ctz": f"{{{ones}, {x}}}"}[op]
                units.append((mod_, W, {f"{op}_a": (W, cnt)},
                              {f"{op}_n": (W.bit_length(), lambda mi, l, v: f"{v}[{widths[mi].bit_length() - 1}:0]")}, op))
        if not units:
            raise ValueError(f"{owners[first]}: family {family} has no library counter to share across modes")
        for mod_, width, ins, outs, extra_ in units:
            if mod_ is None:
                raise ValueError(f"{owners[first]}: family {family} has no library module at the {width}-bit width "
                                 f"its {kind} shared across modes {sorted(per_mode)} takes")
            for n_, t_ in FAM.module_texts(mod_.name, mod_.text).items():
                collect_modules(library_used, ((n_, t_),))
            for mi, _l in entries:
                if mi != first:
                    register_origin(owners[mi], family, dict(pins), mod_.name, parameters=getattr(mod_, "params", None))
            op_tag = f"_{extra_}" if extra_ and not extra_.startswith(",") else ""
            conns = []
            serving = [(mi, l) for mi, l in entries if kind != "bitcount" or op_tag[1:] in per_mode[mi].get("counts", ())]
            for port, (pw, fn_) in ins.items():
                wire = m.logic(f"{pos}_{port}", pw)
                m.assign(wire, " : ".join(f"(mode == {mdw}'d{mi}) ? {fn_(mi, l)}" for mi, l in serving) + " : '0")
                conns.append(f".{port.split('_')[-1] if kind == 'bitcount' else port}({wire})")
            for port, (pw, fn_) in outs.items():
                sig = {"cout": "co"}.get(port, port)
                wire = m.logic(f"xs_{kind}_{sig}_r{r}", pw)
                conns.append(f".{port.split('_')[-1] if kind == 'bitcount' else port}({wire})")
                for mi, l in serving:
                    results.setdefault((mi, sig), {})[l] = fn_(mi, l, wire)
            inst = f"u_xs_{kind}{op_tag}_r{r}"
            params = ", ".join(f".{k}({v})" for k, v in (getattr(mod_, "params", None) or {}).items())
            m.raw(f"  // structure core.{slot}: family {family} realized by one library module {mod_.name} at {width} "
                  f"bits, shared by lane position {r} of modes {', '.join(str(mi) for mi, _l in serving)} "
                  f"(one mode per operation: the operands muxed by the mode)")
            m.raw(f"  {mod_.name} " + (f"#({params}) " if params else "") + f"{inst} (" + ", ".join(conns)
                  + ctrl(mod_) + (extra_ if extra_.startswith(",") else "") + ");")
            consumers = [x for x in u.members if (manifest.get(x).mode, manifest.get(x).lane) in set(serving)]
            if len(set(consumers)) > 1:
                record_sharing(f"core.{slot}", family, [f"{m.name}.{inst}"], consumers,
                               "One library instance serves these modes' lanes, one mode per operation.")
    # each mode's result buses: the member lanes' slices of their instances' results, the other lanes 0
    for mi, info in per_mode.items():
        count = modes[mi][0]
        for sig, operand, width in xs_signals(kind, info):
            if operand:
                continue
            got = results.get((mi, sig), {})
            parts = [got.get(l, f"{width}'d0") for l in reversed(range(count))]
            m.assign(f"xs_{kind}_{sig}_m{mi}", parts[0] if len(parts) == 1 else "{" + ", ".join(parts) + "}")


def _lane_module_name(name: str, mi: int, kinds, shared: dict) -> str:
    """A lane module's name: its mode and kinds, `_sh` when the unit shares a
    datapath with it, `_xs` when that is an instance shared across modes (a
    mode may have lanes in such a group and lanes in units of their own,
    whose lane modules differ)."""
    return f"{name}_m{mi}_{'_'.join(kinds)}" + ("_sh" if shared else "") \
        + ("_xs" if any(k.startswith("xs_") for k in shared) else "")


def _block_target(st) -> bool:
    """A conversion into a block format (several lanes into one block): it
    stays inline in the top (the cvtblk modules) and is no unit;
    structures.is_inline names every such structure."""
    return is_inline(st)


# the float kinds a group across modes realizes as one datapath per lane position at the union geometry
FP_SHARE_KINDS = ("fp_adder", "fp_multiplier", "fp_comparator", "fp_divider", "fp_sqrt", "fp_fma")


def _grouped_format_stages(units, manifest):
    """Explicit rounder/unpacker groups, split by simultaneous lane position.

    Keep the member sets, not just the modes: sharing lane 0 must not also
    share an undeclared lane 1. Independent groups may serve different lanes.
    """
    out = {}
    for u in units:
        if u.kind not in ("rounder", "unpacker"):
            continue
        sts = [manifest.get(member) for member in u.members]
        if len({st.mode for st in sts}) < 2:
            continue
        out.setdefault(u.kind, []).append({(st.mode, st.lane) for st in sts})
    return out


def _grouped_across_modes(units, manifest, modes, ieee_modes) -> dict:
    """{kind: the modes that share it} of the units whose members are
    float structures of one shareable kind spanning two float modes or
    more. One unit per kind shares: the shared datapath's operand and
    result wires are named per (kind, mode), so a second group of the
    same kind would collide, and the sharing schemes enumerate one."""
    out: dict = {}
    for u in units:
        if u.kind not in FP_SHARE_KINDS:
            continue
        ms = sorted({manifest.get(m).mode for m in u.members} & set(ieee_modes))
        if len(ms) < 2 or len({modes[mi][1].name for mi in ms}) < 2:
            continue
        if u.kind in out:
            raise ValueError(f"{u.kind}: two groups across modes ({out[u.kind]} and {ms}) ask for two shared "
                             f"datapaths of one kind, which the seed names by (kind, mode); group them as one")
        out[u.kind] = ms
    return out


def union_geometry(spec: dict, families: dict | None = None, lay: dict | None = None,
                   mode_targets: dict | None = None):
    """The geometry every float and posit mode computes at when any of
    them shares a datapath: the widest significand, exponent and X of
    the unit's own modes. One geometry for the unit rather than one per
    group, since a shared module takes and returns X and every mode
    that feeds it must agree on the layout; the modes that share nothing
    are widened with them, which is what the estimate prices them at.
    Returns None when the unit has no float or posit mode."""
    from chialu.targets.rtl.alu_mode import tight_x
    from chialu.targets.rtl.families.fp import Geom
    lay = lay or A.alu_layout(A.normalize_spec(spec))
    modes, ops = lay["modes"], lay["ops"]
    if mode_targets is None:
        mode_targets = {mi: [A.cvt_target(op) for op in ops if (mi, op) in lay["legal"] and A.is_cvt(op)]
                        for mi in range(len(modes))}
    engines = [Engine("geometry", fmt, lay["sr_bits"], lay["sr"], mode_targets[mi],
                      tight=tight_x(spec, families or {}, mi, A.family_of(fmt), mode_targets[mi], lay["sr"]))
               for mi, (_, fmt) in enumerate(modes) if A.family_of(fmt) in ("float", "posit")]
    if not engines:
        return None
    return Geom(max(e.XW for e in engines), max(e.EW for e in engines), max(e.SW for e in engines), lay["sr_bits"])


def _units(manifest: StructureManifest, partition, top: str) -> list:
    """SeedUnit objects of a partition [(unit name, member ids)]; members
    without a slot (quantizers, conversions into block formats) stay in
    the top and yield no unit."""
    units = []
    for uname, members in partition:
        members = tuple(members)
        sts = [manifest.get(m) for m in members]
        if any(s is None for s in sts):
            missing = [m for m, s in zip(members, sts) if s is None]
            raise ValueError(f"partition {uname}: unknown structures {missing}")
        if all(_block_target(s) for s in sts):
            continue
        sts = [s for s in sts if not _block_target(s)]
        members = tuple(s.id for s in sts)
        kinds = {s.kind for s in sts}
        try:
            kind = manifest.group_kind(kinds)
        except ValueError as e:
            raise ValueError(f"partition {uname}: {e}")
        slot = KIND_SLOT.get(kind)
        if slot is None or kind in INLINE_KINDS:
            continue
        units.append(SeedUnit(uname, members, kind, slot, f"{top}_u_{sv_ident(uname)}"))
    return units


def _amode_width(spec: dict) -> int:
    """The accuracy-mode port's width, 0 without runtime accuracy control."""
    n = len(spec.get("accuracy_mode") or ()) if str(spec.get("accuracy_ctl", "static")) == "runtime" else 0
    return max(1, (n - 1).bit_length()) if n else 0


def _control_decode(mod: SvModule, spec: dict, force: int):
    aw = _amode_width(spec)
    if aw:
        mod.logic("amode", aw)
        mod.assign("amode", "accuracy_mode_sel")
    rnds = list(spec["rounding"])
    mod.logic("rnd_sel", 3)
    if len(rnds) > 1:
        sel_w = max(1, (len(rnds) - 1).bit_length())
        blk = mod.comb()
        blk.open("case (rounding_sel)")
        for k, m in enumerate(rnds):
            blk.stmt(f"{sel_w}'d{k}: rnd_sel = 3'd{RND[m]};")
        blk.stmt(f"default: rnd_sel = 3'd{RND[rnds[0]]};")
        blk.close("endcase")
    else:
        mod.assign("rnd_sel", f"3'd{RND[rnds[0]]}")
    mod.logic("rnd", 3)
    mod.assign("rnd", FORCE_RND_EXPR[force])
    for nm, port in (("daz", "daz_in"), ("ftz", "ftz_out"), ("dual", "unary_dual")):
        vals = list(spec[port])
        mod.logic(nm)
        if len(vals) > 1:
            mod.assign(nm, f"{port}_sel[0] ? 1'b{1 if vals[1] else 0} : 1'b{1 if vals[0] else 0}")
        else:
            mod.assign(nm, f"1'b{1 if vals[0] else 0}")


def _reference_underflow(mod: SvModule, spec: dict) -> str:
    """Independent exact-product test for the MERGED compatibility flag.

    Keep this at the interface, so all generated arithmetic families serve
    the same reference contract, including a plan that shares its rounder.
    """
    if spec.get("underflow_contract") != "fpnew_merged_16" or "fmul" not in spec["ops"]:
        return "1'b0"
    terms = []
    for mi, eb, mb in ((1, 8, 7), (2, 5, 2)):
        width, pw, bias = 1 + eb + mb, 2 * (mb + 1), (1 << (eb - 1)) - 1
        name = f"merged_tiny_m{mi}"
        mod.function(f"""function automatic {name}(input [{width-1}:0] aa, bb);
  integer ea, eb, shift;
  reg [{pw-1}:0] product;
  begin
    ea = aa[{width-2}:{mb}];
    eb = bb[{width-2}:{mb}];
    product = {{(ea != 0), aa[{mb-1}:0]}} * {{(eb != 0), bb[{mb-1}:0]}};
    shift = {bias+1+2*mb} - ((ea == 0) ? 1 : ea) - ((eb == 0) ? 1 : eb);
    {name} = (shift >= {pw}) || ((shift >= 0) && (product < ({pw}'d1 << shift)));
  end
endfunction""")
        # Only the lower lane is the shared, wider datapath. NX and the
        # rounded minimum normal exclude specials, exact products and zero.
        terms.append(f"((mode == 2'd{mi}) && (y[{width-2}:0] == {width-1}'d{1 << mb})"
                     f" && {name}(a[{width-1}:0], b[{width-1}:0]))")
    mod.logic("merged_underflow")
    mod.assign("merged_underflow", f"(op == 3'd{spec['ops'].index('fmul')}) && (rnd == 3'd0)"
               f" && fl_all[{flag_bit('inexact')}] && (" + " || ".join(terms) + ")")
    return "merged_underflow"


def _mode_select(mod: SvModule, lay: dict, spec: dict):
    modes = lay["modes"]
    v_max = lay["v_max"]
    mod.logic("fl_all", v_max * FW)
    if len(modes) > 1:
        mdw = max(1, (len(modes) - 1).bit_length())
        blk = mod.comb()
        blk.open("case (mode)")
        for mi in range(len(modes)):
            blk.stmt(f"{mdw}'d{mi}: begin y = y_m{mi}; fl_all = fl_m{mi};"
                     + (f" d = d_m{mi};" if lay["d_w"] else "") + " end")
        blk.stmt("default: begin y = '0; fl_all = '0;" + (" d = '0;" if lay["d_w"] else "") + " end")
        blk.close("endcase")
    else:
        mod.assign("y", "y_m0")
        mod.assign("fl_all", "fl_m0")
        if lay["d_w"]:
            mod.assign("d", "d_m0")
    flags = lay["flags"]
    if flags:
        extra_uf = _reference_underflow(mod, spec)
        nf = len(flags)
        if lay.get("flag_scope", "per_result") == "per_operation":
            # one status for the whole operation: the or of every result's word, which is the
            # convention FPnew reports for a vectorial op (docs/formats-and-options.md 3.8)
            for j, fname in enumerate(flags):
                expression = " | ".join(f"fl_all[{r*FW + flag_bit(fname)}]" for r in range(v_max))
                if fname == "underflow" and extra_uf != "1'b0":
                    expression += " | " + extra_uf
                mod.assign(f"flags[{j}]", expression)
        else:
            for r in range(v_max):
                for j, fname in enumerate(flags):
                    expression = f"fl_all[{r*FW + flag_bit(fname)}]"
                    if r == 0 and fname == "underflow" and extra_uf != "1'b0":
                        expression += " | " + extra_uf
                    mod.assign(f"flags[{r*nf+j}]", expression)


def _header(name: str, modes, ops) -> list:
    return [f"{name}: behavioral reference derived from the instance (modes "
            f"{', '.join(f'{n}x{f.name}' for n, f in modes)}; ops {', '.join(ops)}). "
            f"Every (mode, op) pair computes the verify layer's exact semantics."]


from chialu.targets.rtl.families.selection import checked_alu_seed as _checked_alu_seed


@_checked_alu_seed
def alu_seed(spec: dict, name: str = "alu_core", force: int = FORCE_NONE,
             skip=(), with_manifest: bool = True, partition=None,
             hierarchical: bool = True, families: dict | None = None) -> SeedText:
    """The reference of a normalized spec. `skip` lists (mode index, op)
    pairs left out (the checker covers them by residue, so their
    duplicate logic is not generated); a copy with `force` or `skip` is a
    checker copy: monolithic and without a manifest. `partition` is
    [(unit name, member structure ids)] (default: one unit per slotted
    structure); hierarchical=False writes one flat module. `families`
    ({`core.<slot>.<index>`: (family, {choice: value})}) names the
    declared family of every structure: a lane module instantiates the
    family library's module for it where the library has one
    (chialu.targets.rtl.families), and the modules used are appended
    after the generated ones.

    The hierarchy is written once per shared piece: a package per mode
    holds the engine functions, a lane module per (mode, kind)
    parameterized by LANE holds the datapath of one lane, a unit module
    per physical structure instantiates the lane modules of its members
    and ORs their buses per mode, and the top instantiates the units."""
    spec = A.normalize_spec(spec)
    lay = A.alu_layout(spec)
    modes, ops = lay["modes"], lay["ops"]
    legal = _legal(lay, skip)
    is_seed = with_manifest and force == FORCE_NONE and not skip
    if not is_seed or not hierarchical:
        return _monolithic(spec, lay, legal, name, force, is_seed)
    manifest = structure_manifest(spec)
    from chialu.targets.rtl.families.alu_pg import fuse_partition
    partition = fuse_partition(manifest, partition, families or {})
    from chialu.targets.rtl.families.partition import fuse_multiply_add, validate_partition
    partition = fuse_multiply_add(manifest, partition, families or {})
    from chialu.targets.rtl.families.partition import complete_word_groups
    partition = complete_word_groups(manifest, partition, families or {})
    validate_partition(manifest, partition, families or {})
    units = _units(manifest, partition if partition is not None
                   else default_partition(manifest), name)
    ports_in = list(lay["core_in"])
    ports_out = list(lay["core_out"])
    y_w, d_w, v_max = lay["y_w"], lay["d_w"], lay["v_max"]
    lane_ports = [p for p in ports_in if p.name in ("a", "b", "c", "op", "mode", "sr_rnd")]
    # the modes whose lane modules read the third operand (a fused multiply-add op is legal in them)
    ternary_modes = {mi for mi in range(len(modes)) if any((mi, op) in legal for op in A.FUSED_OPS)}

    def srcs_of(mi):
        return ("a", "b", "c") if mi in ternary_modes else ("a", "b")
    ctrl_ports = [Port("rnd", "in", 3), Port("daz", "in", 1), Port("ftz", "in", 1),
                  Port("dual", "in", 1)]
    if _amode_width(spec):
        # the accuracy mode of a runtime-controlled approximate structure reaches
        # every lane module beside the rounding and denormal controls
        ctrl_ports.append(Port("amode", "in", _amode_width(spec)))
    # the cvt targets per mode fix the engine geometry of every emitter of the mode
    mode_targets = {mi: [A.cvt_target(op) for oi, op in enumerate(ops)
                         if (mi, op) in legal and A.is_cvt(op)]
                    for mi in range(len(modes))}

    from chialu.targets.rtl import alu_raw_pg
    raw_groups, raw_modes = alu_raw_pg.plan(manifest, modes, legal, families or {}, bool(d_w or lay.get("dual_in_y")))
    format_sharing = {}
    interop_modes = [mi for mi, (_, fmt) in enumerate(modes) if A.family_of(fmt) == "posit"
                     and (families or {}).get(f"core.posit_unit.m{mi}", (None, {}))[0] == "posit_ieee_interop"
                     and (families or {})[f"core.posit_unit.m{mi}"][1].get("interop_style") == "unified_dual_format_datapath"]
    ieee_modes = [mi for mi, (_, fmt) in enumerate(modes) if A.family_of(fmt) == "float"]
    isa_modes = [mi for mi, (_, fmt) in enumerate(modes) if A.family_of(fmt) == "posit"
                 and (families or {}).get(f"core.posit_unit.m{mi}", (None, {}))[0] == "posit_ieee_interop"
                 and (families or {})[f"core.posit_unit.m{mi}"][1].get("interop_style") == "isa_posit_replaces_float"]
    if isa_modes and any((mi, op) in legal and op in ("fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp", "fmin", "fmax", "fabs", "fneg")
                         for mi in ieee_modes for op in ops):
        raise ValueError("isa_posit_replaces_float requires companion IEEE modes to allow conversion operations only")
    if interop_modes and not ieee_modes:
        raise ValueError("unified_dual_format_datapath needs a posit and an IEEE floating mode")
    math_ops = {"fp_adder": {"fadd", "fsub"}, "fp_multiplier": {"fmul"}, "fp_divider": {"fdiv"},
                "fp_sqrt": {"fsqrt"}, "fp_comparator": {"fcmp", "fmin", "fmax"},
                "fp_fma": {"fadd", "fsub", "fmul"} | set(A.FUSED_OPS)}
    math_sharing = {kind: [mi for mi in interop_modes + ieee_modes if any((mi, op) in legal for op in operations)]
                    for kind, operations in math_ops.items() if interop_modes and set(ops) & operations and kind != "fp_fma"}
    math_sharing = {kind: selected for kind, selected in math_sharing.items() if selected}
    if interop_modes and not any(set(selected) & set(interop_modes) and set(selected) & set(ieee_modes) for selected in math_sharing.values()):
        raise ValueError("unified_dual_format_datapath needs a common active arithmetic operation in its posit and IEEE modes")
    # a float kind's structures grouped across modes are one physical datapath per lane at the union
    # geometry, the operands muxed by the mode: a group is the plan's statement that they share, and a
    # group of one mode's structures (its lanes) is not one (the lanes compute at once)
    format_groups = _grouped_format_stages(units, manifest)
    for kind, groups in format_groups.items():
        format_sharing[kind] = sorted({mi for group in groups for mi, _lane in group})
    for kind, selected in _grouped_across_modes(units, manifest, modes, ieee_modes).items():
        if kind in math_sharing:
            continue                                    # the posit interop already shares this kind
        math_sharing[kind] = selected
    # a fused multiply-add shared across formats: one physical datapath per lane at the widest geometry serves
    # every float mode whose fp_fma selects the sharing (the seed muxes the operands by the mode)
    fma_shared = [mi for mi in ieee_modes
                  if (families or {}).get(f"core.fp_fma.m{mi}", (None, {}))[0] not in (None, "separate_multiplier_and_adder")
                  and dict((families or {})[f"core.fp_fma.m{mi}"][1]).get("sharing") == "shared_across_formats"
                  and any((mi, op) in legal for op in math_ops["fp_fma"])]
    if fma_shared:
        if len(fma_shared) < 2 or len({modes[mi][1].name for mi in fma_shared}) < 2:
            raise ValueError("fp_fma sharing shared_across_formats requires two distinct selected formats")
        math_sharing["fp_fma"] = fma_shared
    for kind in ("rounder", "unpacker"):
        selected = [mi for mi, (_, fmt) in enumerate(modes)
                    if A.family_of(fmt) == "float" and (families or {}).get(f"core.{kind}.m{mi}", (None,))[0] == "shared_across_formats"]
        if selected and kind in format_sharing and not set(selected) <= set(format_sharing[kind]):
            raise ValueError(f"{kind}.shared_across_formats modes outside the explicit sharing groups: "
                             "add them to a compatible group or select shared_per_lane for those modes")
        if selected and kind not in format_sharing:
            if len(selected) < 2 or len({modes[mi][1].name for mi in selected}) < 2:
                raise ValueError(f"{kind}.shared_across_formats requires two distinct selected formats")
            first_pins = families[f"core.{kind}.m{selected[0]}"][1]
            if any(dict(families[f"core.{kind}.m{mi}"][1]) != dict(first_pins) for mi in selected[1:]):
                raise ValueError(f"{kind}.shared_across_formats requires compatible pins on its one physical datapath")
            format_sharing[kind] = selected
    geometry = union_geometry(spec, families, lay, mode_targets) if (format_sharing or math_sharing) else None

    def result_count(mi, kind):
        copies = 2 if (d_w or lay.get("dual_in_y")) and kind in ("rounder", "fp_sqrt") and (mi, "fsqrt") in legal else 1
        return modes[mi][0] * copies

    def extra(fam, kind, mi, count, XT, dual):
        ports = _extra_ports(fam, kind, mi, count, XT, dual, ternary=mi in ternary_modes)
        if mi in raw_modes:
            ports += alu_raw_pg.ports(raw_modes[mi], mi, kind)
        if mi in format_sharing.get(kind, ()):
            if kind == "rounder":
                count = result_count(mi, kind)
                core = __import__("chialu.targets.rtl.engine", fromlist=["_core"])._core(modes[mi][1])
                ports += [(f"rsx_m{mi}", "out", count * XT), (f"rsword_m{mi}", "out", count * lay["sr_bits"]),
                          (f"rsfl_m{mi}", "in", count * FW), (f"rsbits_m{mi}", "in", count * core.width)]
            else:
                ports += [(f"usu{src}_m{mi}", "in", count * (geometry.VW + 1)) for src in srcs_of(mi)]
        for operation, selected in math_sharing.items():
            owner_kind = "fp_divider" if operation == "fp_sqrt" else operation
            if kind != owner_kind or mi not in selected:
                continue
            operation_count = result_count(mi, operation)
            ports.append((f"ix_{operation}_a_m{mi}", "out", operation_count * XT))
            if operation != "fp_sqrt":
                ports.append((f"ix_{operation}_b_m{mi}", "out", operation_count * XT))
            if operation == "fp_adder":
                ports.append((f"ix_{operation}_sub_m{mi}", "out", count))
            if operation == "fp_fma":
                ports.append((f"ix_{operation}_c_m{mi}", "out", operation_count * XT))
                ports.append((f"ix_{operation}_op_m{mi}", "out", count * 3))
            if operation == "fp_comparator":
                ports += [(f"ilt_{operation}_m{mi}", "in", count), (f"ieq_{operation}_m{mi}", "in", count)]
            else:
                ports.append((f"iy_{operation}_m{mi}", "in", operation_count * XT))
        return ports

    library_used: dict = ModuleLibrary()  # strict named SV definitions, in order of use

    def emitter(mi, ops_legal, mod, **kw):
        count, fmt = modes[mi]
        return _emitter_class(A.family_of(fmt))(spec, lay, mi, count, fmt, ops_legal,
                                                force, mod, manifest, targets=mode_targets[mi],
                                                families=families, library_used=library_used,
                                                geometry=geometry,
                                                **kw)

    def out_ports(m, mi):
        m.port(f"y_m{mi}", "out", y_w)
        if d_w:
            m.port(f"d_m{mi}", "out", d_w)
        m.port(f"fl_m{mi}", "out", v_max * FW)

    # ---- one package per mode: the engine functions, written once
    packages = {mi: SvPackage(f"{name}_m{mi}_pkg",
                              header=[f"{name}_m{mi}_pkg: the exact-arithmetic functions of "
                                      f"mode {mi} ({modes[mi][0]}x{modes[mi][1].name})"])
                for mi in range(len(modes))}
    # the engine geometry per mode (the x/xa/xb bus width is count * XT)
    xt, xw = {}, {}
    for mi in range(len(modes)):
        probe = emitter(mi, [], SvModule("_probe"), lanes=[LANE], lib=SvPackage("_probe_pkg"))
        xt[mi] = probe.eng.XT
        xw[mi] = probe.eng.XW
    dual_sets = bool(d_w or lay.get("dual_in_y"))
    # ---- one lane module per (mode, kind) the units need
    lane_mods = {}                     # (mi, kinds, shared kinds) -> module name
    W_bus = next(p.width for p in lane_ports if p.name == "a")
    unit_shared = {}                   # (unit name, mi) -> the sharing of the unit's lane modules in the mode
    for u in units:
        shares = xs_kind(u, manifest, modes)
        for mi in u.modes(manifest):
            unit_shared[(u.name, mi)] = _shared_of(u, manifest, mi, modes, families, W_bus, xw)
            if shares and not ({"adder", "multiplier", "logic"} & set(unit_shared[(u.name, mi)])):
                # a group of one integer kind across modes without its kind's sharing family: one library
                # instance per lane position (_xs_glue)
                unit_shared[(u.name, mi)][f"xs_{shares}"] = {
                    "w": modes[mi][1].width, "count": modes[mi][0],
                    "counts": _xs_counts(families, mi, modes[mi][1].width, legal) if shares == "bitcount" else []}
            kind = u.kind_in(manifest, mi)
            if mi in raw_modes and kind == raw_modes[mi]["role"]:
                unit_shared[(u.name, mi)]["raw_pg"] = raw_modes[mi]
            if mi in format_sharing.get(kind, ()):
                unit_shared[(u.name, mi)][f"float_{kind}"] = True
            for operation, selected in math_sharing.items():
                if kind == ("fp_divider" if operation == "fp_sqrt" else operation) and mi in selected:
                    unit_shared[(u.name, mi)][f"interop_{operation}"] = True
    for u in units:
        for mi in u.modes(manifest):
            mk = u.kind_in(manifest, mi)          # the datapath's kind in this mode (its ports)
            kinds = u.kinds_in(manifest, mi)      # the member kinds whose ops it realizes
            shared = unit_shared[(u.name, mi)]
            key = (mi, kinds, tuple(sorted(shared)))
            if key in lane_mods or "logic" in shared:
                continue
            lm = SvModule(_lane_module_name(name, mi, kinds, shared))
            lm.parameter("int LANE", 0)
            if mk == "converter":
                # one conversion target per unit: TGT is the cvt op's index
                # (-1 keeps every target)
                lm.parameter("int TGT", -1)
            lm.ports_from(lane_ports)
            lm.ports_from(ctrl_ports)
            fam_mi = A.family_of(modes[mi][1])
            if mk != "unpacker":
                out_ports(lm, mi)
            for pn, pd, pw in extra(fam_mi, mk, mi, modes[mi][0], xt[mi], dual_sets):
                lm.port(pn, pd, pw)
            for k_ in kinds:
                for pn, pd, pw in _shared_ports(shared, k_, mi, W_bus):
                    lm.port(pn, pd, pw)
            lm.import_package(packages[mi].name)
            if mk == "rounder":
                ops_legal = [(oi, op) for oi, op in enumerate(ops)
                             if (mi, op) in legal and _rounds_op(op)]
            elif mk == "unpacker":
                ops_legal = []
            else:
                ops_legal = [(oi, op) for oi, op in enumerate(ops)
                             if (mi, op) in legal and kind_of(op) in kinds
                             and not isinstance(A.cvt_target(op), BlockFormat)]
            split, shared_unp = _split_of(fam_mi, mk)
            if (families or {}).get(f"core.unpacker.m{mi}", (None,))[0] == "per_unit_unpack" \
                    and mi not in format_sharing.get("unpacker", ()):
                shared_unp = False
            g = emitter(mi, ops_legal, lm, lanes=[LANE], lib=packages[mi],
                        tgt_param="TGT" if mk == "converter" else None,
                        split=split, shared_unpack=shared_unp, shared=shared)
            g.manifest = None                        # the dry pass registered them
            g.library()
            g.emit()
            lm.header = [f"{lm.name}: lane LANE of mode {mi} ({modes[mi][1].name}) for the "
                         f"{'/'.join(kinds)} ops {', '.join(op for _o, op in ops_legal)}; the result "
                         f"buses are the mode's, with only this lane's bits written"
                         + ("; the unit's shared " + " and ".join(shared) + " serve this lane through the pc_/tp_ buses" if shared else "")]
            lane_mods[key] = lm.render()
    # ---- one unit module per physical structure: its lanes' lane modules, ORed per mode
    modules = ModuleLibrary()
    for u in units:
        m = SvModule(u.module)
        m.ports_from(lane_ports)
        m.ports_from(ctrl_ports)
        served = u.modes(manifest)
        for mi in served:
            if u.kind_in(manifest, mi) != "unpacker":
                out_ports(m, mi)
            for pn, pd, pw in extra(A.family_of(modes[mi][1]), u.kind_in(manifest, mi),
                                           mi, modes[mi][0], xt[mi], dual_sets):
                m.port(pn, pd, pw)
        conns0 = {p.name: p.name for p in lane_ports}
        conns0.update({p_.name: p_.name for p_ in ctrl_ports})
        mdw = max(1, (len(modes) - 1).bit_length())
        wide_done = False
        for mi in served:
            mk = u.kind_in(manifest, mi)
            shared = unit_shared[(u.name, mi)]
            if "logic" in shared:
                # wide_gate_row: one full-width gate row serves every lane packing of the unit
                if not wide_done:
                    from chialu.targets.rtl import families as FAM
                    wide_dual = bool(d_w or lay["dual_in_y"]) and "not" in ops
                    row_width = W_bus * (2 if wide_dual else 1)
                    lg = FAM.logic_module("wide_gate_row", shared["logic"]["pins"], row_width)
                    for n_, t_ in FAM.module_texts(lg.name, lg.text).items():
                        collect_modules(library_used, ((n_, t_),))
                    opw = max(1, (len(ops) - 1).bit_length())
                    sel = " : ".join(f"(op == {opw}'d{ops.index(o)}) ? 2'd{k}" for k, o in enumerate(("and", "or", "xor", "not")) if o in ops)
                    m.logic("lg_op", 2)
                    m.assign("lg_op", f"{sel} : 2'd0")
                    m.logic("lg_en")
                    m.assign("lg_en", " | ".join(f"(op == {opw}'d{ops.index(o)})" for o in ("and", "or", "xor", "not") if o in ops))
                    m.logic("lg_y", row_width)
                    if wide_dual:
                        m.logic("lg_dual")
                        m.assign("lg_dual", f"dual && (op == {opw}'d{ops.index('not')})")
                    m.raw(f"  // structure core.logic: family wide_gate_row realized by one library gate row over the whole word "
                          f"(the packings {', '.join(f'{modes[x][0]} x {modes[x][1].name}' for x in shared['logic']['served'])})")
                    lg_params = ", ".join(f".{key}({value})" for key, value in lg.params.items())
                    row_a, row_b = ("{b, a}", "{a, b}") if wide_dual else ("a", "b")
                    m.raw(f"  {lg.name} #({lg_params}) u_wide_row (.a({row_a}), .b({row_b}), .op(lg_op), .y(lg_y));")
                    from chialu.targets.rtl.families.selection import register_origin
                    for shared_mode in served:
                        owner = f"core.logic.m{shared_mode}"
                        selected = families[owner]
                        register_origin(owner, selected[0], selected[1], lg.name, parameters=lg.params)
                    if len(u.members) > 1:
                        from chialu.targets.rtl.families.fidelity import shared as record_sharing
                        record_sharing("core.logic", "wide_gate_row", [f"{m.name}.u_wide_row"], u.members,
                                       "One bitwise row serves the selected mode and lane packings.")
                    wide_done = True
                active = modes[mi][0] * modes[mi][1].width
                low = f"lg_y[{active-1}:0]"
                low = f"{{{{{y_w-active}{{1'b0}}}}, {low}}}" if y_w > active else low
                if wide_dual and lay["dual_in_y"]:
                    high = f"lg_y[{W_bus} +: {active}]"
                    high = f"{{{{{y_w-active}{{1'b0}}}}, {high}}}" if y_w > active else high
                    low = f"({low} | (lg_dual ? ({high} << {y_w//2}) : {y_w}'d0))"
                m.assign(f"y_m{mi}", f"lg_en ? {low} : '0")
                if d_w:
                    high = f"lg_y[{W_bus} +: {active}]"
                    high = f"{{{{{d_w-active}{{1'b0}}}}, {high}}}" if d_w > active else high
                    m.assign(f"d_m{mi}", f"lg_dual ? {high} : '0" if wide_dual else "'0")
                m.assign(f"fl_m{mi}", "'0")
                continue
            xports = extra(A.family_of(modes[mi][1]), mk, mi, modes[mi][0], xt[mi], dual_sets)
            for k_ in u.kinds_in(manifest, mi):
                xports = xports + [(pn, pd, pw) for pn, pd, pw in _shared_ports(shared, k_, mi, W_bus) if (pn, pd, pw) not in xports]
            for pn, pd, pw in (_shared_ports(shared, "adder", mi, W_bus) + _shared_ports(shared, "multiplier", mi, W_bus)
                               + _shared_ports(shared, "fp_adder", mi, W_bus)
                               + [x for k_ in XS_KINDS if k_ not in ("adder", "multiplier")
                                  for x in _shared_ports(shared, k_, mi, W_bus)]):
                m.logic(pn, pw)                            # the unit-internal shared buses
            has_y = mk != "unpacker"
            # one lane-module instance per member structure of the mode: a
            # lane, and for a converter the target (TGT = its cvt op's index)
            insts = []
            for x in u.members:
                st = manifest.get(x)
                if st.mode != mi:
                    continue
                tgt = ops.index(st.ops[0]) if st.kind == "converter" else None
                sfx = f"l{st.lane}" + (f"_t{tgt}" if tgt is not None else "")
                if all(sfx != s0 for s0, _l, _t in insts):
                    insts.append((sfx, st.lane, tgt))
            for sfx, l, tgt in insts:
                conns = dict(conns0)
                if has_y:
                    m.logic(f"y_m{mi}_{sfx}", y_w)
                    if d_w:
                        m.logic(f"d_m{mi}_{sfx}", d_w)
                    m.logic(f"fl_m{mi}_{sfx}", v_max * FW)
                    conns.update({f"y_m{mi}": f"y_m{mi}_{sfx}", f"fl_m{mi}": f"fl_m{mi}_{sfx}"})
                    if d_w:
                        conns[f"d_m{mi}"] = f"d_m{mi}_{sfx}"
                for pn, pd, pw in xports:
                    if pd == "in":
                        conns[pn] = pn                    # the unit's own input bus
                    else:
                        m.logic(f"{pn}_{sfx}", pw)
                        conns[pn] = f"{pn}_{sfx}"
                params = f".LANE({l})" + (f", .TGT({tgt})" if tgt is not None else "")
                m.raw(f"  {_lane_module_name(name, mi, u.kinds_in(manifest, mi), shared)} #({params}) u_m{mi}_{sfx} ("
                      + ", ".join(f".{k}({v})" for k, v in conns.items()) + ");")
            if has_y:
                m.assign(f"y_m{mi}", " | ".join(f"y_m{mi}_{sfx}" for sfx, _l, _t in insts))
                if d_w:
                    m.assign(f"d_m{mi}", " | ".join(f"d_m{mi}_{sfx}" for sfx, _l, _t in insts))
                m.assign(f"fl_m{mi}", " | ".join(f"fl_m{mi}_{sfx}" for sfx, _l, _t in insts))
            for pn, pd, pw in xports:
                if pd == "out":
                    m.assign(pn, " | ".join(f"{pn}_{sfx}" for sfx, _l, _t in insts))
        # the unit's instances shared across modes by lane position (a group of one integer kind without its
        # kind's sharing family)
        xs_any: dict = {}
        for mi in served:
            for k, v in unit_shared[(u.name, mi)].items():
                if k.startswith("xs_"):
                    xs_any.setdefault(k[3:], {})[mi] = v
        for kind_, per_mode in xs_any.items():
            _xs_glue(m, u, kind_, per_mode, manifest, modes, families, legal, mdw, library_used, name)
        # the unit's shared datapaths: one instance over the served modes, selected by the mode
        from chialu.targets.rtl import families as FAM
        sh_any = {k: v for mi in served for k, v in unit_shared[(u.name, mi)].items() if k in ("adder", "multiplier")}
        for kind_, info in sh_any.items():
            sv_modes = info["served"]
            widths = [modes[x][1].width for x in sv_modes]
            sel_expr = " : ".join(f"(mode == {mdw}'d{x}) ? {max(1, (max(2, len(sv_modes)) - 1).bit_length())}'d{k}" for k, x in enumerate(sv_modes))
            if kind_ == "multiplier":
                signed_ = [modes[x][1].encoding == "twos_complement" for x in sv_modes]
                mod_ = FAM.twin_precision_module(widths, signed_, info["pins"], W_bus)
                if mod_ is None:
                    raise ValueError("core.multiplier: the shared twin-precision matrix is a library construction and "
                                     "the library's realization is off (realization: behavioral); use a plan without "
                                     "shared multipliers")
                for n_, t_ in FAM.module_texts(mod_.name, mod_.text).items():
                    collect_modules(library_used, ((n_, t_),))
                # the one matrix realizes every served mode's core.multiplier.m* selection (as the partitioned adder does)
                from chialu.targets.rtl.families.selection import register_origin
                for x in sv_modes:
                    sel_ = (families or {}).get(f"core.multiplier.m{x}")
                    if sel_ and sel_[0] == "twin_precision_subword":
                        register_origin(f"core.multiplier.m{x}", sel_[0], sel_[1], mod_.name)
                m.logic("tp_sel", max(1, (max(2, len(sv_modes)) - 1).bit_length()))
                m.assign("tp_sel", f"{sel_expr} : '0" if len(modes) > 1 else "'0")
                m.logic("tp_p", 2 * W_bus)
                m.raw(f"  // structure core.multiplier: family twin_precision_subword realized by one library matrix over the "
                      f"packings {', '.join(f'{modes[x][0]} x {modes[x][1].name}' for x in sv_modes)}")
                m.raw(f"  {mod_.name} u_twin (.a(a), .b(b), .sel(tp_sel), .p(tp_p));")
                for x in sv_modes:
                    m.assign(f"tp_p_m{x}", "tp_p")
            else:
                # the segments are the served lanes' declared adder family (one physical adder: the modes it serves
                # must agree); the partitioned module then realizes every member's core.adder.m* selection
                from chialu.targets.rtl.families.selection import register_origin
                declared = [(x, (families or {}).get(f"core.adder.m{x}")) for x in sv_modes]
                declared = [(x, sel) for x, sel in declared if sel]
                segment = declared[0][1] if declared else None
                if segment and segment[0] == "end_around_carry":
                    # a modulo 2^n - 1 adder wraps its carry-out into bit 0, which a two's complement or
                    # unsigned lane's add must not see: it cannot be a segment of the partitioned adder
                    raise ValueError("adder.end_around_carry requires a ones' complement format: the lane-partitioned "
                                     f"adder of subword partitioned_carry_chain (modes {sv_modes}) adds binary lanes")
                for x, sel in declared[1:]:
                    if sel[0] != segment[0] or dict(sel[1]) != dict(segment[1]):
                        raise ValueError(f"subword partitioned_carry_chain: one lane-partitioned adder serves modes "
                                         f"{sv_modes}, whose declared adder families differ (core.adder.m{declared[0][0]}: "
                                         f"{segment[0]}, core.adder.m{x}: {sel[0]}); declare one family for them or "
                                         f"choose core.subword.family replicated_lanes")
                fp = info.get("fp")
                # with float adders in the bank: the adder is as wide as the significand add plus its carry-out bit
                # (rounded to the finest lane), each float mode a full-width lane of its own, the integer operands
                # in the low bits and the significands at bit 0 (their carry-out is the sum's bit iw)
                W_sh = fp["w"] if fp else W_bus
                fp_modes = fp["fp_modes"] if fp else []
                all_modes = list(sv_modes) + fp_modes
                widths_all = widths + [W_sh] * len(fp_modes)
                sel_expr = " : ".join(f"(mode == {mdw}'d{x}) ? {max(1, (max(2, len(all_modes)) - 1).bit_length())}'d{k}"
                                      for k, x in enumerate(all_modes))
                mod_ = FAM.partitioned_adder_module(widths_all, info["pins"], W_sh, segment=segment)
                if mod_ is None:
                    raise ValueError("core.adder: the lane-partitioned adder is a library construction and the "
                                     "library's realization is off (realization: behavioral); choose "
                                     "core.subword.family replicated_lanes and a plan without shared adders")
                for n_, t_ in FAM.module_texts(mod_.name, mod_.text).items():
                    collect_modules(library_used, ((n_, t_),))
                for x, sel in declared:
                    register_origin(f"core.adder.m{x}", sel[0], sel[1], mod_.name)
                L = W_sh // info["fine"]
                L_bus = W_bus // info["fine"]
                sw = max(1, (max(2, len(all_modes)) - 1).bit_length())
                m.logic("pc_sel", sw)
                m.assign("pc_sel", f"{sel_expr} : '0" if len(modes) > 1 else "'0")
                m.logic("pc_a", W_sh)
                m.logic("pc_b", W_sh)
                m.logic("pc_cin", L)
                m.logic("pc_s", W_sh)
                m.logic("pc_co", L)
                iw = fp["iw"] if fp else 0

                def zext(expr, width, to):
                    return f"{{{{{to - width}{{1'b0}}}}, {expr}}}" if to > width else expr
                for nm, bus_w, fp_w in (("pc_a", W_bus, iw), ("pc_b", W_bus, iw), ("pc_cin", L_bus, 1)):
                    arms = [f"(mode == {mdw}'d{x}) ? {zext(f'{nm}_m{x}', bus_w, W_sh if nm != 'pc_cin' else L)}" for x in sv_modes]
                    sa = {"pc_a": "sa_a", "pc_b": "sa_b", "pc_cin": "sa_cin"}[nm]
                    arms += [f"(mode == {mdw}'d{x}) ? {zext(f'{sa}_m{x}', fp_w, W_sh if nm != 'pc_cin' else L)}" for x in fp_modes]
                    m.assign(nm, " : ".join(arms) + " : '0" if len(modes) > 1 else f"{nm}_m0")
                m.raw(f"  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the "
                      f"selected packing's lane boundaries ({', '.join(f'{modes[x][0]} x {modes[x][1].name}' for x in sv_modes)})"
                      + (f"; the float significand add of mode{'s' if len(fp_modes) > 1 else ''} {', '.join(str(x) for x in fp_modes)} "
                         f"on the same adder ({iw} bits at bit 0, the whole width one lane)" if fp else ""))
                m.raw(f"  {mod_.name} u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));")
                for x in sv_modes:
                    m.assign(f"pc_s_m{x}", f"pc_s[{W_bus-1}:0]" if W_sh > W_bus else "pc_s")
                    m.assign(f"pc_co_m{x}", f"pc_co[{L_bus-1}:0]" if L > L_bus else "pc_co")
                for x in fp_modes:
                    m.assign(f"sa_s_m{x}", f"pc_s[{iw-1}:0]")
                    m.assign(f"sa_cout_m{x}", f"pc_s[{iw}]")
        m.header = [f"{u.module}: physical structure `{u.name}` (kind {u.kind}, "
                    f"slot {u.slot}); realizes " + ", ".join(
                        manifest.get(x).brief() for x in u.members),
                    "the seed's body: one instance of the lane module per lane, defined outside "
                    "the mutable regions; the lane module instantiates the family library's module "
                    "of the declared family where the library has one (a comment names it) and is "
                    "behavioral otherwise; a rewrite replaces these instances with the family's "
                    "logic inside this module, keeps the module's name and ports, and may share "
                    "one datapath among the lanes"]
        for x in u.members:
            st = manifest.get(x)
            if not st.sv:
                st.sv = u.module
        modules[u.module] = m.render()
    # ---- the slot-less ops (logic, conversions) as lane modules of their own:
    # a `misc` module per mode (parameter LANE: the logic ops and the
    # conversions to scalar targets) and a `cvtblk` module per mode and
    # target block size (parameter LANE0, its first lane: the conversions of
    # a scalar mode into block targets); a block mode's conversions into
    # block targets stay inline in the top
    misc_mods, blk_mods, top_inline = {}, {}, {}
    for mi, (count, fmt) in enumerate(modes):
        size = fmt.size if isinstance(fmt, BlockFormat) else 1
        # the ops no unit realizes: a slot-less kind (quantizer), and every
        # conversion into a block format (several lanes into one block)
        inline = [(oi, op) for oi, op in enumerate(ops)
                  if (mi, op) in legal and (KIND_SLOT.get(kind_of(op)) is None
                                            or isinstance(A.cvt_target(op), BlockFormat))]
        misc = [(oi, op) for oi, op in inline
                if not isinstance(A.cvt_target(op), BlockFormat)]
        blk = [(oi, op) for oi, op in inline
               if isinstance(A.cvt_target(op), BlockFormat) and size == 1]
        rest = [(oi, op) for oi, op in inline if (oi, op) not in misc and (oi, op) not in blk]
        if misc:
            lm = SvModule(f"{name}_m{mi}_misc")
            lm.parameter("int LANE", 0)
            lm.ports_from(lane_ports)
            lm.ports_from(ctrl_ports)
            out_ports(lm, mi)
            lm.import_package(packages[mi].name)
            g = emitter(mi, misc, lm, lanes=[LANE], lib=packages[mi])
            g.manifest = None
            g.library()
            g.emit()
            lm.header = [f"{lm.name}: lane LANE of mode {mi} ({fmt.name}) for the slot-less ops "
                         f"{', '.join(op for _o, op in misc)}"]
            misc_mods[mi] = lm.render()
        for tsize in sorted({A.cvt_target(op).size for _o, op in blk}):
            ops_t = [(oi, op) for oi, op in blk if A.cvt_target(op).size == tsize]
            lm = SvModule(f"{name}_m{mi}_cvtblk{tsize}")
            lm.parameter("int LANE0", 0)
            lm.ports_from(lane_ports)
            lm.ports_from(ctrl_ports)
            out_ports(lm, mi)
            lm.import_package(packages[mi].name)
            lanes = [Expr(f"(LANE0+{j})", name=f"g{j}") for j in range(tsize)]
            g = emitter(mi, ops_t, lm, lanes=lanes, lib=packages[mi])
            g.groups = [Expr(f"(LANE0/{tsize})", name="G")]
            g.manifest = None
            g.library()
            g.emit()
            lm.header = [f"{lm.name}: lanes LANE0..LANE0+{tsize-1} of mode {mi} ({fmt.name}) "
                         f"converted into one block: {', '.join(op for _o, op in ops_t)}"]
            blk_mods[(mi, tsize)] = lm.render()
        if rest:
            top_inline[mi] = rest
    # ---- the top: control decode, the inline ops, the units, the OR, the mode mux
    top = SvModule(name)
    top.ports_from(ports_in + ports_out)
    _control_decode(top, spec, force)
    lane_conns = {p.name: p.name for p in lane_ports}
    lane_conns.update({p_.name: p_.name for p_ in ctrl_ports})

    def lane_inst(module, inst, param, value, b, mi):
        top.logic(f"y_{b}", y_w)
        if d_w:                            # the unit drives a detect bus only when the checker is on
            top.logic(f"d_{b}", d_w)
        top.logic(f"fl_{b}", v_max * FW)
        conns = dict(lane_conns, **{f"y_m{mi}": f"y_{b}", f"fl_m{mi}": f"fl_{b}"})
        if d_w:
            conns[f"d_m{mi}"] = f"d_{b}"
        top.raw(f"  {module} #(.{param}({value})) {inst} ("
                + ", ".join(f".{k}({v})" for k, v in conns.items()) + ");")
        return b

    for mi, (count, fmt) in enumerate(modes):
        buses = []
        if mi in top_inline:
            top.import_package(packages[mi].name)
            g = emitter(mi, top_inline[mi], top, bus=f"m{mi}_i", lib=packages[mi])
            g.library()
            g.emit()
            buses.append(f"m{mi}_i")
        if mi in misc_mods:
            for l in range(count):
                buses.append(lane_inst(f"{name}_m{mi}_misc", f"u_m{mi}_misc_l{l}", "LANE", l,
                                       f"m{mi}_misc_l{l}", mi))
        for (mmi, tsize), _t in blk_mods.items():
            if mmi != mi:
                continue
            for gidx in range(count // tsize):
                buses.append(lane_inst(f"{name}_m{mi}_cvtblk{tsize}", f"u_m{mi}_cvtblk{tsize}_g{gidx}",
                                       "LANE0", gidx * tsize, f"m{mi}_cvtblk{tsize}_g{gidx}", mi))
        xbus_writers = {}                  # extra bus name -> the per-unit wires ORed into it
        for u in units:
            if mi not in u.modes(manifest):
                continue
            b = f"m{mi}_{sv_ident(u.name)}"
            mk = u.kind_in(manifest, mi)
            if mk != "unpacker":
                top.logic(f"y_{b}", y_w)
                if d_w:
                    top.logic(f"d_{b}", d_w)
                top.logic(f"fl_{b}", v_max * FW)
                buses.append(b)
            for pn, pd, pw in extra(A.family_of(fmt), mk, mi, count, xt[mi], dual_sets):
                if pd == "out":
                    top.logic(f"{pn}_{b}", pw)
                    xbus_writers.setdefault((pn, pw), []).append(f"{pn}_{b}")
        top.logic(f"y_m{mi}", y_w)
        if d_w:
            top.logic(f"d_m{mi}", d_w)
        top.logic(f"fl_m{mi}", v_max * FW)
        # the detect bus is declared, ORed and connected together or not at all: a `d_<unit>` wire
        # emitted while the unit carries no `d_m<i>` port is read by the OR and driven by nothing,
        # which `check -assert` reports and which leaves the checker's own output at X in simulation
        for sig in ("y", "d", "fl") if d_w else ("y", "fl"):
            top.assign(f"{sig}_m{mi}", " | ".join(f"{sig}_{b}" for b in buses) if buses else "'0")
        for (pn, pw), wires in xbus_writers.items():
            top.logic(pn, pw)
            top.assign(pn, " | ".join(wires))
    for u in units:
        conns = {p.name: p.name for p in lane_ports}
        conns.update({p_.name: p_.name for p_ in ctrl_ports})
        for mi in u.modes(manifest):
            b = f"m{mi}_{sv_ident(u.name)}"
            mk = u.kind_in(manifest, mi)
            if mk != "unpacker":
                conns[f"y_m{mi}"] = f"y_{b}"
                if d_w:
                    conns[f"d_m{mi}"] = f"d_{b}"
                conns[f"fl_m{mi}"] = f"fl_{b}"
            for pn, pd, pw in extra(A.family_of(modes[mi][1]), mk, mi, modes[mi][0], xt[mi], dual_sets):
                conns[pn] = f"{pn}_{b}" if pd == "out" else pn     # outputs: own wire; inputs: the mode bus
        top.instance(u.module, f"u_{sv_ident(u.name)}", conns)
    if raw_groups:
        alu_raw_pg.wire(top, raw_groups, modes, families, library_used, max(1, (len(modes)-1).bit_length()))
    if math_sharing:
        from chialu.targets.rtl.families import fp as FP
        first = (interop_modes or ieee_modes)[0]
        top.import_package(packages[first].name)
        g = geometry
        shift = g.XW - g.SW
        norm = f"{name}_shared_operand"
        top.function(f'''
  function automatic [{g.XT-1}:0] {norm}(input [{g.XT-1}:0] value);
    logic [{g.XT-1}:0] n;
    logic signed [{g.EW-1}:0] exponent;
    logic [{g.XW-1}:0] significand;
    n = m{first}_norm(value);
    exponent = $signed(n[{g.XW+g.EW}:{g.XW+1}]) + {g.EW}'sd{shift};
    significand = n[{g.XW}:1] >> {shift};
    {norm} = {{n[{g.XT-1}:{g.XT-3}], exponent, significand, n[0]}};
  endfunction
''')
        defaults = {"fp_adder": "single_path", "fp_multiplier": "sig_mul_then_round", "fp_divider": "sig_div_then_round",
                    "fp_sqrt": "sig_sqrt_then_round", "fp_comparator": "dedicated_magnitude_comparator", "fp_fma": "classic_fma"}
        for kind, selected in math_sharing.items():
            from chialu.targets.rtl import families as FAM
            from chialu.targets.rtl.families.fidelity import shared as witness_shared
            slot = "fp_divider" if kind == "fp_sqrt" else kind
            requested = [(mi, families[f"core.{slot}.m{mi}"]) for mi in selected if f"core.{slot}.m{mi}" in (families or {})]
            family, pins = requested[0][1] if requested else (defaults[kind], {})
            if any(f != family or dict(p) != dict(pins) for _, (f, p) in requested[1:]):
                raise ValueError(f"unified {kind} requires compatible family/pins on one physical datapath")
            if family == "round_fused_in_reduction":
                # the family rounds inside its reduction to one format, while the shared datapath hands each mode's
                # rounder an unrounded result (several IEEE formats, or a posit's variable target precision)
                raise ValueError(f"{slot}.{family} requires a datapath of its own: a fused rounding stage cannot serve "
                                 f"the unified {kind} datapath of modes {selected}, whose rounders take its unrounded result")
            component = None
            for _, selection in requested or [(first, (family, pins))]:
                component = FAM.fp_module(kind, *selection, geometry)
            if component is None:
                raise ValueError(f"unified {kind}: selected family {family} rejected the common geometry")
            for module_name, module_text in FAM.module_texts(component.name, component.text).items():
                collect_modules(library_used, ((module_name, module_text),))
            for mi in selected:
                count = result_count(mi, kind)
                if kind == "fp_comparator":
                    top.logic(f"ilt_{kind}_m{mi}", count)
                    top.logic(f"ieq_{kind}_m{mi}", count)
                else:
                    top.logic(f"iy_{kind}_m{mi}", count * g.XT)
            for lane in range(max(result_count(mi, kind) for mi in selected)):
                conns = {}
                for arg in ("a",) if kind == "fp_sqrt" else ("a", "b", "c") if kind == "fp_fma" else ("a", "b"):
                    signal = top.logic(f"shared_{kind}_{arg}_l{lane}", g.XT)
                    options = [(mi, f"ix_{kind}_{arg}_m{mi}[{lane*g.XT} +: {g.XT}]") for mi in selected if lane < result_count(mi, kind)]
                    top.assign(signal, " : ".join(f"mode == {mdw}'d{mi} ? {norm}({value})" for mi, value in options) + " : '0")
                    conns["x" + arg] = signal
                for ctrl, cw in (("sub", 1),) if kind == "fp_adder" else (("op", 3),) if kind == "fp_fma" else ():
                    wire = top.logic(f"shared_{kind}_{ctrl}_l{lane}", cw)
                    top.assign(wire, " : ".join(f"mode == {mdw}'d{mi} ? ix_{kind}_{ctrl}_m{mi}"
                                                + (f"[{lane * cw} +: {cw}]" if modes[mi][0] > 1 else "")
                                                for mi in selected if lane < result_count(mi, kind)) + f" : {cw}'d0")
                    conns["fop" if ctrl == "op" else ctrl] = wire
                if kind == "fp_comparator":
                    for out in ("lt", "eq"):
                        result = top.logic(f"shared_{kind}_{out}_l{lane}")
                        conns[out] = result
                        for mi in selected:
                            if lane < result_count(mi, kind):
                                top.assign(f"i{out}_{kind}_m{mi}" + (f"[{lane}]" if modes[mi][0] > 1 else ""), result)
                else:
                    result = top.logic(f"shared_{kind}_y_l{lane}", g.XT)
                    conns["y"] = result
                    for mi in selected:
                        if lane < result_count(mi, kind):
                            top.assign(f"iy_{kind}_m{mi}[{lane*g.XT} +: {g.XT}]", result)
                instance = f"u_shared_{kind}_l{lane}"
                top.instance(component.name, instance, conns)
                consumers = [f"mode{mode}" for mode in selected if lane < result_count(mode, kind)]
                if len(consumers) > 1:
                    for mi in interop_modes:
                        witness_shared(f"core.posit_unit.m{mi}", "unified_dual_format_datapath", [f"{name}.{instance}"], consumers)
                    if kind == "fp_fma":
                        for mi in selected:
                            if lane < result_count(mi, kind):
                                witness_shared(f"core.fp_fma.m{mi}", "shared_across_formats", [f"{name}.{instance}"], consumers)
    for kind, selected in format_sharing.items():
        from chialu.targets.rtl import families as FAM
        from chialu.targets.rtl.engine import _core
        formats = [_core(modes[mi][1]) for mi in selected]
        probe = emitter(selected[0], [], SvModule("shared_geometry"))
        shared_module = None
        # a shared rounder needs no normalizer when every sharing mode's rounded ops come through a fused
        # multiply-add, whose one normalize is its last stage
        from chialu.targets.rtl.families.fp import fma_normalizes
        normalized = kind == "rounder" and all(
            fma_normalizes(*(families or {}).get(f"core.fp_fma.m{mi}", (None, {})))
            and {op for op in ops if (mi, op) in legal and _rounds_op(op)} <= {"fadd", "fsub", "fmul"} | set(A.FUSED_OPS)
            for mi in selected)
        if kind in format_groups:
            from chialu.targets.rtl.alu_fp_share import emit_format_groups
            emit_format_groups(top, library_used, kind, selected, format_groups[kind], modes, families,
                               geometry, result_count, ternary_modes, probe.eng.tokens, normalized)
            continue
        for mi in selected:
            family, pins = families[f"core.{kind}.m{mi}"]
            shared_module = FAM.fp_shared_module(kind, family, pins, formats, geometry, selected,
                                                tokens=probe.eng.tokens, normalized_input=normalized)
        for module_name, module_text in FAM.module_texts(shared_module.name, shared_module.text).items():
            collect_modules(library_used, ((module_name, module_text),))
        # the shared unpacker decodes the third operand too when a sharing mode has a fused multiply-add op
        shared_srcs = ("a", "b", "c") if any(mi in ternary_modes for mi in selected) else ("a", "b")
        for mi, fmt in zip(selected, formats):
            count = result_count(mi, kind)
            if kind == "rounder":
                top.logic(f"rsfl_m{mi}", count * FW)
                top.logic(f"rsbits_m{mi}", count * fmt.width)
            else:
                for src in shared_srcs:
                    top.logic(f"usu{src}_m{mi}", count * (geometry.VW + 1))
        for lane in range(max(result_count(mi, kind) for mi in selected)):
            for src in ((None,) if kind == "rounder" else shared_srcs):
                conns = {"mode": "mode"}
                for index, (mi, fmt) in enumerate(zip(selected, formats)):
                    live = lane < result_count(mi, kind)
                    if kind == "rounder":
                        conns.update({f"f{index}_x": f"rsx_m{mi}[{lane*geometry.XT} +: {geometry.XT}]" if live else "'0",
                                      f"f{index}_word": (f"rsword_m{mi}" if result_count(mi, kind) * lay['sr_bits'] == 1 else
                                                           f"rsword_m{mi}[{lane*lay['sr_bits']} +: {lay['sr_bits']}]") if live else "'0",
                                      f"f{index}_rnd": "rnd", f"f{index}_ftz": "ftz",
                                      f"f{index}_fl": f"rsfl_m{mi}[{lane*FW} +: {FW}]" if live else "",
                                      f"f{index}_bits": f"rsbits_m{mi}[{lane*fmt.width} +: {fmt.width}]" if live else ""})
                    else:
                        uw = geometry.VW + 1
                        arg = f"{src}[{lane*modes[mi][1].width} +: {modes[mi][1].width}]" if live else "'0"
                        if modes[mi][1].width != fmt.width and live:
                            from chialu.targets.rtl.alu_mode import x87_to_core
                            arg = x87_to_core(arg)
                        conns.update({f"f{index}_b": arg, f"f{index}_daz": "daz",
                                      f"f{index}_u": f"usu{src}_m{mi}[{lane*uw} +: {uw}]" if live else ""})
                top.instance(shared_module.name, f"u_shared_{kind}_l{lane}" + (f"_{src}" if src else ""), conns)
    _mode_select(top, lay, spec)
    # every package is needed: the lane modules import theirs, the top its inline ones
    pkg_text = "\n".join(packages[mi].render() for mi in range(len(modes))
                         if packages[mi]._func_order)
    top.header = _header(name, modes, ops) + [
        f"HIERARCHY: {len(units)} physical structure modules instantiated by {name}, "
        f"built from {len(lane_mods)} lane modules (one per mode and kind, parameter LANE) "
        f"and {len(modes)} packages of engine functions (one per mode); a float mode's "
        f"datapath is split into an unpacker (the xa/xb/den buses), the arithmetic and "
        f"converter structures (unrounded results on the x bus) and a rounder (y and the "
        f"flags); {len(misc_mods)} misc lane modules and {len(blk_mods)} block-conversion "
        f"group modules" + (f"; block-to-block conversions inline in {name}" if top_inline else "")] \
        + [f"UNIT {u.name} module={u.module} kind={u.kind} members={','.join(u.members)}"
           for u in units] + manifest.header_lines() \
        + ([f"LIBRARY: {', '.join(sorted(library_used))} (chialu.targets.rtl.families: the modules of the "
            f"declared families the lane modules instantiate; their text follows the generated modules)"]
           if library_used else [])
    top_text = top.render()
    for key, text in lane_mods.items():
        modules[f"{name}_m{key[0]}_{key[1]}" + (f"_{'_'.join(key[2])}" if key[2] else "")] = text
    for mi, text in misc_mods.items():
        modules[f"{name}_m{mi}_misc"] = text
    for (mi, tsize), text in blk_mods.items():
        modules[f"{name}_m{mi}_cvtblk{tsize}"] = text
    for mi in range(len(modes)):
        if packages[mi]._func_order:
            modules[packages[mi].name] = packages[mi].render()
    # the modules outside the mutable regions in a fixed order, so a sharing plan
    # changes the regions alone
    text = pkg_text + "\n" + top_text + "\n" + "\n".join(
        modules[u.module] for u in units) + "\n" + "\n".join(lane_mods[k] for k in sorted(lane_mods)) \
        + "\n" + "\n".join(misc_mods[k] for k in sorted(misc_mods)) \
        + "\n" + "\n".join(blk_mods[k] for k in sorted(blk_mods))
    members = _members_of(manifest, pkg_text, top_text, units, modules, lane_mods, misc_mods, blk_mods, library_used)
    if library_used:
        modules.update(library_used)
        text += ("\n// ---- the family library modules the lane modules instantiate "
                 "(chialu/targets/rtl/families; fixed text, replaced by editing the instances)\n"
                 + "\n".join(library_used[k] for k in sorted(library_used)))
    return SeedText(dedupe_modules(text), manifest, top_text, modules, units, members)


def _monolithic(spec, lay, legal, name, force, is_seed) -> SeedText:
    modes, ops = lay["modes"], lay["ops"]
    manifest = StructureManifest() if is_seed else None
    mod = SvModule(name)
    mod.ports_from(list(lay["core_in"]) + list(lay["core_out"]))
    _control_decode(mod, spec, force)
    for mi, (count, fmt) in enumerate(modes):
        ops_legal = [(oi, op) for oi, op in enumerate(ops) if (mi, op) in legal]
        g = _emitter_class(A.family_of(fmt))(spec, lay, mi, count, fmt, ops_legal,
                                             force, mod, manifest)
        g.library()
        g.emit()
    _mode_select(mod, lay, spec)
    mod.header = _header(name, modes, ops)
    if manifest is not None:
        mod.header += manifest.header_lines()
    text = mod.render()
    return SeedText(text, manifest or StructureManifest(), text, {}, [])


def alu_ref_module(spec: dict, name: str = "alu_core", force: int = FORCE_NONE,
                   skip=()) -> str:
    """The flat module text alone (the checker's reference copies)."""
    return alu_seed(spec, name, force, skip, with_manifest=False,
                    hierarchical=False).text


def module_names(text: str) -> list:
    return MODULE_RE.findall(text or "")
