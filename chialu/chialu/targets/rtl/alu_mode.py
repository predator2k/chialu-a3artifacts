"""The shared machinery of the ALU mode emitters.

One emitter per (mode, format family) writes into the seed module the
mode's function library (the engine's unpack/arith/pack functions for the
mode's format and every cvt target), the operand decode, and the mode's
always_comb body with one case arm per legal op. The base class owns the
names, the placement of a result into y or the dual target, the flag
words, the SR words, the conversion of a value set into a block target,
and the registration of the arithmetic structures a mode realizes in the
seed's structure manifest (chialu.targets.rtl.structures).

Subclasses: IntModeEmitter (integer, fixed point, BCD), FloatModeEmitter
(floats, fp80, posits) and BlockModeEmitter (block formats).
"""
from __future__ import annotations

from chialu.targets.rtl.engine import (FW, Conventions, Engine, flag_bit,
                                        fmt_tag, _core)
from chialu.targets.rtl.structures import KIND_SLOT, StructureManifest, kind_of
from chialu.targets.rtl.writer import CombBlock, SvModule, bool_, onehot
from chialu.targets.rtl.families.module_library import ModuleLibrary, collect_modules
from chialu.verify import alu_ref as A
from chialu.verify.formats import (NAN, BlockFormat, FloatFormat, PositFormat, X87Format,
                                    X87Format)

NOFLAG = f"{FW}'d0"


class Expr:
    """A lane-index expression: an SV constant expression over a module
    parameter (`LANE`, `LANE0`), so one module text serves every lane.
    Arithmetic with ints renders the expression; `name` is the identifier
    fragment used where a lane index names a signal."""

    def __init__(self, text: str, atom: bool = False, name: str | None = None):
        self.text, self.atom = text, atom
        self.name = name if name is not None else (text if atom else None)

    def __str__(self):
        return self.text

    def __format__(self, spec):
        return self.text

    def _bin(self, other, op, rev=False):
        a, b = (other, self) if rev else (self, other)
        return Expr(f"({a}{op}{b})")

    def __add__(self, o):
        return self._bin(o, "+")

    def __radd__(self, o):
        return self._bin(o, "+", True)

    def __mul__(self, o):
        return self._bin(o, "*")

    def __rmul__(self, o):
        return self._bin(o, "*", True)

    def __sub__(self, o):
        return self._bin(o, "-")

    def __rsub__(self, o):
        return self._bin(o, "-", True)


def lane_tag(i) -> str:
    """The identifier fragment naming lane i: the int itself, or the name
    of a lane expression (a lane module's LANE, a group's lane j)."""
    if isinstance(i, Expr):
        if i.name is None:
            raise ValueError(f"lane expression {i.text} has no name for identifiers")
        return i.name
    return str(i)


LANE = Expr("LANE", atom=True)       # the lane parameter of a lane module


def flag(name: str) -> str:
    """The flag word with one flag set."""
    return onehot(FW, flag_bit(name))


def flag_if(cond: str, name: str) -> str:
    return f"({cond} ? {flag(name)} : {NOFLAG})"


def x87_to_core(b: str) -> str:
    """SV expression: an fp80 pattern as its 79-bit core (the explicit
    integer bit dropped)."""
    return f"{{{b}[79], {b}[78:64], {b}[62:0]}}"


def core_to_x87(cb: str) -> str:
    """SV expression: a 79-bit core pattern as an fp80 pattern (the integer
    bit set for every nonzero exponent)."""
    return f"{{{cb}[78], {cb}[77:63], (({cb}[77:63] != 0) ? 1'b1 : 1'b0), {cb}[62:0]}}"


def tight_x(spec: dict, families: dict, mi: int, fam: str, targets, sr: bool = False) -> bool:
    """Whether mode `mi`'s X is the guard-round-sticky form: the unit
    option `x_form` is `guard_round_sticky` and the mode is a float mode
    (an integer, posit or block mode keeps the exact X). The option
    serves a unit without conversion ops in its float modes and without
    the stochastic mode, which `chialu.behavior_rules.check_options`
    rejects at load (the converters need the exact value, and the
    stochastic mode compares the dropped bits exactly); the raise here
    is the last defense behind that check."""
    if str((spec or {}).get("x_form", "exact")) != "guard_round_sticky" or fam != "float":
        return False
    if targets or sr:
        raise ValueError(f"x_form guard_round_sticky serves float modes without conversion ops and without the "
                         f"stochastic rounding mode; mode {mi}"
                         + (f" has the conversion targets {[str(t) for t in targets]}" if targets else "")
                         + (" has SR provisioned" if sr else "")
                         + " (chialu.behavior_rules.OPTION_RULES states the rule; the load-time check missed it)")
    # Both separate and fused producers normalize before compressing to X.
    # The separate multiplier normalizes its exact product, so stored
    # subnormal significands are also safe here.
    return True


class ModeEmitter:
    """The SV of one mode of a chialu.ALU spec."""

    def __init__(self, spec: dict, lay: dict, mi: int, count: int, fmt,
                 ops_legal: list, force: int, mod: SvModule,
                 manifest: StructureManifest | None = None,
                 lanes=None, bus: str | None = None, unit_sv: str = "",
                 lib: SvModule | None = None, targets=None,
                 tgt_param: str | None = None, split: str | None = None,
                 shared_unpack: bool = False, shared: dict | None = None, families: dict | None = None,
                 library_used: dict | None = None, geometry=None):
        """lanes: the lanes of the mode this emitter writes (all by
        default; the symbolic LANE for a lane module); bus: the suffix of
        its result buses y_<bus>, d_<bus>, fl_<bus> (the mode prefix by
        default); unit_sv: the module name registered as the sv symbol
        of the structures it realizes; lib: where the functions go (the
        mode's package; the module itself by default); targets: the
        mode-wide cvt targets, which fix the engine's geometry for every
        emitter of the mode; families: {`core.<slot>.<index>`: (family,
        {choice: value})} the declared families of the structures, which
        the emitter realizes through the family library where it has a
        module; library_used: {module name: text} the seed collects."""
        self.spec, self.lay, self.mi = spec, lay, mi
        self.families = families or {}
        self.library_used = library_used if library_used is not None else ModuleLibrary()
        self.count, self.fmt = count, fmt
        self.ops = ops_legal                     # [(op index, op)]
        self.force = force
        self.mod = mod
        self.lib = lib or mod
        self.manifest = manifest
        self.p = f"m{mi}"
        self.lanes = list(range(count)) if lanes is None else list(lanes)
        self.groups = None                       # block-target cvt groups (all)
        self.bus = bus or self.p
        self.unit_sv = unit_sv
        self.fam = A.family_of(fmt)
        # the operand ports the mode reads: a and b, and c for a float mode with a fused multiply-add op
        self.ternary = self.fam == "float" and any((mi, op) in lay["legal"] for op in A.FUSED_OPS)
        self.srcs = ("a", "b", "c") if self.ternary else ("a", "b")
        self.sr_bits = lay["sr_bits"]
        self.sr = lay["sr"]
        self.conv = Conventions.from_spec(spec)
        self.targets = (list(targets) if targets is not None else
                        [A.cvt_target(op) for _, op in ops_legal if A.is_cvt(op)])
        self.eng = Engine(self.p, fmt, self.sr_bits, self.sr, self.targets,
                          conv=self.conv, tight=tight_x(spec, self.families, mi, self.fam, self.targets, self.sr))
        if geometry is not None and self.fam in ("float", "posit"):
            self.eng.widen(geometry.SW)
            self.eng.widen_exp(geometry.EW)
            self.eng.XW = max(self.eng.XW, geometry.XW)
            self.eng.XT = 3 + self.eng.EW + self.eng.XW + 1
        self.own_tag = None                      # the mode's own pack tag
        self.blk: CombBlock | None = None
        self.oi = 0                              # the op index being emitted
        self.tgt_param = tgt_param               # a converter lane module: the parameter
                                                 # (op index) that keeps one cvt target
        # the float mode's datapath split into structures: a "producer" (an
        # arithmetic or converter lane module) writes its unrounded result
        # to the x bus, the "rounder" lane module packs it into y and the
        # flags, the "unpacker" decodes the operands onto the xa/xb buses
        # that every other lane module of the mode reads (shared_unpack)
        self.split = split
        self.shared_unpack = shared_unpack
        self.shared = shared or {}               # kind -> the unit-level instance the lane reads (subword sharing)
        self._tmps: list[str] = []               # op temporaries, in declaration order
        self.set_idx = 0                         # the result set being emitted

    # ---- the family library -------------------------------------------------
    @property
    def amodes(self) -> int:
        """The unit's accuracy modes under `accuracy_ctl: runtime`, 0
        without the control: what a runtime-controlled approximate
        structure renders its mode switch over."""
        if str(self.spec.get("accuracy_ctl", "static")) != "runtime":
            return 0
        return len(self.spec.get("accuracy_mode") or ())

    def family_for(self, kind: str, target: str = ""):
        """(family, pins) declared for the structure of `kind` in this
        mode (its lanes share the decision), or None. Under runtime
        accuracy control the pins of a family that offers a runtime
        quality control carry the unit's mode count, so its module
        renders the mode switch and takes the `amode` port."""
        slot = KIND_SLOT.get(kind)
        if not slot:
            return None
        got = self.families.get(f"core.{slot}.m{self.mi}" + (f".{target}" if target else ""))
        if got and self.amodes:
            from chialu.targets.rtl.families.approx import RUNTIME_FAMILIES
            fam, pins = got
            if fam in RUNTIME_FAMILIES:
                from chialu.targets.rtl.families.selection import copy_pins
                return fam, copy_pins(pins, _accuracy_modes=self.amodes)
        return got

    def ctrl_conns(self, module) -> str:
        """The control connections of a library instance: the ports the
        module declares beside its operands, driven by the lane module's
        own control inputs of the same name."""
        return "".join(f", .{n}({n})" for n, _w in (getattr(module, "ctrl", ()) or ()))

    def library_module(self, module) -> str:
        """Register a library Module the emitter instantiates; its text
        lands in the seed after the generated modules. Returns its name."""
        from chialu.targets.rtl.families import module_texts
        collect_modules(self.library_used, module_texts(module.name, module.text))
        return module.name

    # ---- names ------------------------------------------------------------
    def tag(self, i) -> str:
        return lane_tag(i)

    def pat(self, src: str, i) -> str:
        """Lane i of operand a or b (the mode's pattern width)."""
        return f"{self.p}_{src}{self.tag(i)}"

    def x(self, src: str, k: int) -> str:
        """Value k of operand `src` as an X."""
        return f"{self.p}_x{src}[{k}]"

    def den(self, src: str, k: int) -> str:
        """The denormal-read flag of value k of operand `src`."""
        return f"{self.p}_den{src}[{k}]"

    def tmp(self, name: str, width: int, signed: bool = False) -> str:
        """A module-scope temporary (declared once). Every temporary gets a
        don't-care default at the top of the comb block (emit): an op's
        temporaries are assigned only inside that op's case arm, and
        without the default yosys infers a latch per unassigned path
        (933 in the alu_mixed32 top), which inflates the area and splits
        ABC's timing paths; `'x` costs no logic."""
        if not self.mod.declared(name):
            self._tmps.append(name)
        return self.mod.logic(name, width, signed=signed)

    # ---- X field tests ------------------------------------------------------
    def special(self, x: str) -> str:
        XT = self.eng.XT
        return f"{x}[{XT-1}:{XT-2}]"

    def is_nan(self, x: str) -> str:
        return f"({self.special(x)} == 2'd1)"

    def is_inf(self, x: str) -> str:
        return f"({self.special(x)} == 2'd2)"

    def is_snan(self, x: str, pat: str, fmt=None, off: int = 0) -> str:
        """The value `x` is a NaN whose pattern `pat` (an element at bit
        `off` of it) has the quiet bit clear: a signalling NaN, the one
        NaN operand IEEE 754 flags as invalid. 0 for a format with no
        signalling NaN (no NaN, no significand bit, or one NaN pattern)."""
        fmt = fmt or self.fmt
        if isinstance(fmt, BlockFormat):
            fmt = fmt.elem
        if isinstance(fmt, X87Format):
            return f"({self.is_nan(x)} && !{pat}[{off + 62}])"
        core = _core(fmt) if isinstance(fmt, FloatFormat) else None
        if core is None or not core.has_nan or core.man_bits == 0 or not core.has_inf:
            return "1'b0"
        return f"({self.is_nan(x)} && !{pat}[{off + core.man_bits - 1}])"

    def is_zero(self, x: str) -> str:
        return f"({self.special(x)} == 2'd0 && {x}[{self.eng.XW}:0] == 0)"

    def x_sign(self, x: str) -> str:
        return f"{x}[{self.eng.XT-3}]"

    def nan_pattern(self, fmt) -> str:
        """The canonical NaN pattern of a float format as an SV literal."""
        core = _core(fmt)
        b = core.encode_special(NAN)
        if isinstance(fmt, X87Format):
            b = fmt._from_core(b)
        return f"{fmt.width}'d{b}"

    def pattern_sign(self, src: str, i, j: int = 0) -> str:
        """The sign bit of element j of lane i of operand `src` as the
        reference reads it for an invalid conversion: the pattern's sign
        for floats and float block elements, 0 for a posit NaR and for
        unsigned formats."""
        if self.fam == "posit":
            xa = self.x(src, i)
            return f"(({self.special(xa)} == 2'd0) && {self.x_sign(xa)})"
        if self.fam == "block":
            el = self.fmt.elem
            if isinstance(el, FloatFormat) and el.signed:
                return f"{self.pat(src, i)}[{j * el.width + el.width - 1}]"
            return "1'b0"
        core = _core(self.fmt)
        if not core.signed:
            return "1'b0"
        return f"{self.pat(src, i)}[{self.fmt.width - 1}]"

    def elem(self, i, j: int, size: int):
        """The value index of element j of lane i (the lane itself for a
        scalar mode)."""
        if size == 1:
            return i
        value = i * size + j
        return Expr(value.text, name=f"{self.tag(i)}_e{j}") if isinstance(value, Expr) else value

    # ---- SR words ------------------------------------------------------------
    def word(self, r: int) -> str:
        if self.sr:
            return f"sr_rnd[{r}*{self.sr_bits} +: {self.sr_bits}]"
        return f"{self.sr_bits}'d0"

    def words(self, base: int, n: int) -> str:
        if self.sr:
            return f"sr_rnd[{base}*{self.sr_bits} +: {n*self.sr_bits}]"
        return f"{n*self.sr_bits}'d0"

    # ---- result placement ------------------------------------------------------
    def result_sets(self, op: str) -> list:
        """(set_idx, src, oth): the first set computes from a (and b), the
        dual set of a unary op from b (and a)."""
        sets = [(0, "a", "b")]
        if A.is_unary(op) and (self.lay["d_w"] or self.lay["dual_in_y"]):
            sets.append((1, "b", "a"))
        return sets

    def guard(self, set_idx: int) -> str:
        return "" if set_idx == 0 else "if (dual) "

    def lhs(self, set_idx: int, i: int, w_out: int, off: int = 0,
            width: int | None = None) -> str:
        """The bits of y (or of the dual target) that hold result i of a
        set: value i at i*w_out, `off` bits into it, `width` bits wide."""
        width = w_out if width is None else width
        base = i * w_out + off
        if set_idx == 0:
            return f"y_{self.bus}[{base} +: {width}]"
        if self.lay["dual_in_y"]:
            return f"y_{self.bus}[{self.lay['y_w'] // 2 + base} +: {width}]"
        return f"d_{self.bus}[{base} +: {width}]"

    def put(self, set_idx: int, i: int, w_out: int, expr: str, off: int = 0,
            width: int | None = None):
        self.blk.stmt(f"{self.guard(set_idx)}{self.lhs(set_idx, i, w_out, off, width)} = {expr};")

    def put_flags(self, r: int, expr: str, set_idx: int = 0):
        target = f"fl_{self.bus}[{r}*{FW} +: {FW}]"
        self.blk.stmt(f"{self.guard(set_idx)}{target} = {expr};")

    # ---- the x bus of a split float mode -----------------------------------------
    def xbus(self, set_idx: int) -> str:
        return f"x_{self.bus}" if set_idx == 0 else f"xd_{self.bus}"

    def x_slice(self, set_idx: int, k) -> str:
        XT = self.eng.XT
        return f"{self.xbus(set_idx)}[{k}*{XT} +: {XT}]"

    def put_x(self, set_idx: int, k, expr: str):
        """A producer's unrounded result of value k onto the x bus."""
        self.blk.stmt(f"{self.guard(set_idx)}{self.x_slice(set_idx, k)} = {expr};")

    # ---- structures ------------------------------------------------------------
    def structure(self, op: str, lane: int, sv: str = "", kind: str | None = None):
        """Register the structure that realizes `op` for one lane."""
        if self.manifest is None:
            return None
        kind = kind or kind_of(op)
        tgt = A.cvt_target(op)
        return self.manifest.add(kind, self.mi, lane, [op], self.fmt.width,
                                 self.fmt.name, sv=sv or self.unit_sv,
                                 target=tgt.name if tgt is not None and kind == "converter" else "")

    def note_structures(self, op: str):
        """A comment in the op's case arm naming the structures it uses."""
        if self.manifest is None:
            return
        ids = [s.id for s in self.manifest if s.mode == self.mi and op in s.ops]
        if ids:
            self.blk.stmt("// structures: " + ", ".join(ids))

    # ---- library -----------------------------------------------------------------
    def library(self):
        """The engine functions of the mode into the module: the value
        layout, the rounding decision, the arithmetic, the unpack of the
        mode's own format, the pack of the own format (rounded ops) and of
        every cvt target."""
        e, mod, fmt = self.eng, self.lib, self.fmt
        for text in (e.vdecl(), e.rup_fn(), e.arith()):
            mod.function(text)
        if self.ternary:
            # the fused multiply-add on X, which a mode with a fused op computes behaviorally with
            mod.function(e.fma_fn())
        if self.fam == "float":
            mod.function(e.unpack_float(fmt, "s"))
        elif self.fam == "posit":
            mod.function(e.unpack_posit(fmt, "s"))
        elif self.fam == "block":
            mod.function(e.unpack_block(fmt, "s"))
        else:
            mod.function(e.unpack_int(fmt, "s"))
        if self.fam in ("float", "posit", "block"):
            self.own_tag = self.add_pack(fmt)
        for t in self.targets:
            self.add_pack(t)

    def add_pack(self, t) -> str:
        """The pack (or block quantizer) into format t; returns its tag."""
        e, mod = self.eng, self.lib
        tag = fmt_tag(t)
        if isinstance(t, BlockFormat):
            mod.function(e.quant_block(t, tag))
        elif isinstance(t, (FloatFormat, X87Format)):
            mod.function(e.pack_float(t, tag))
        elif isinstance(t, PositFormat):
            mod.function(e.pack_posit(t, tag))
        else:
            mod.function(e.pack_int(t, tag))
        return tag

    # ---- the mode's datapath ------------------------------------------------
    def emit(self):
        mod, lay, p, bus = self.mod, self.lay, self.p, self.bus
        w = self.fmt.width
        y_w, d_w, v_max = lay["y_w"], lay["d_w"], lay["v_max"]
        mod.logic(f"y_{bus}", y_w)
        mod.logic(f"d_{bus}", max(d_w, 1))
        mod.logic(f"fl_{bus}", v_max * FW)
        for i in self.lanes:
            for src in self.srcs:
                mod.logic(self.pat(src, i), w)
                mod.assign(self.pat(src, i), f"{src}[{i*w} +: {w}]")
        self.declare_values()
        if self.split == "unpacker":
            # the operand decode onto the mode's xa/xb/den buses; no result
            self.emit_unpacker_outputs()
            return
        blk = self.blk = mod.comb()
        blk.stmt(f"y_{bus} = '0; d_{bus} = '0; fl_{bus} = '0;")
        if "float_rounder" in self.shared:
            blk.stmt(f"rsx_{bus} = '0; rsword_{bus} = '0;")
        if "raw_pg" in self.shared:
            blk.stmt(f"pg_a_{bus} = '0; pg_b_{bus} = '0; pg_cin_{bus} = '0; pg_use_g_{bus} = '0;")
            if self.shared["raw_pg"]["role"] == "adder":
                for i in self.lanes:
                    for si in range(self.shared["raw_pg"]["sets"]):
                        blk.stmt(f"pg_use_g_{bus}[({i})+{si*self.count}] = 1'b1;")
        for kind in ("fp_adder", "fp_multiplier", "fp_fma", "fp_divider", "fp_sqrt", "fp_comparator"):
            if f"interop_{kind}" in self.shared:
                blk.stmt(f"ix_{kind}_a_{bus} = '0;" + (f" ix_{kind}_b_{bus} = '0;" if kind != "fp_sqrt" else "")
                         + (f" ix_{kind}_sub_{bus} = '0;" if kind == "fp_adder" else "")
                         + (f" ix_{kind}_c_{bus} = '0; ix_{kind}_op_{bus} = '0;" if kind == "fp_fma" else ""))
        if "adder" in self.shared:
            # the lane drives only its slice of the unit's shared adder operands
            blk.stmt(f"pc_a_{bus} = '0; pc_b_{bus} = '0; pc_cin_{bus} = '0;")
            for pa, pb, propagate, generate in getattr(self, "pg_partition_terms", ()):
                blk.stmt(f"{pa} = {propagate}; {pb} = {generate} << 1;")
        if self.split == "producer":
            blk.stmt(f"{self.xbus(0)} = '0;" + (f" {self.xbus(1)} = '0;" if lay["d_w"] or lay.get("dual_in_y") else ""))
        multi_op = len(self.spec["ops"]) > 1
        opw = max(1, (len(self.spec["ops"]) - 1).bit_length())
        if multi_op:
            blk.open("case (op)")
        for oi, op in self.ops:
            self.oi = oi
            if multi_op:
                blk.open(f"{opw}'d{oi}: begin")
            self.register_op(op)
            self.note_structures(op)
            guard = self.tgt_param and kind_of(op) == "converter"
            if guard:
                # the unit's parameter keeps this target's logic only
                blk.open(f"if ({self.tgt_param} == -1 || {self.tgt_param} == {oi}) begin")
            self.emit_op(op)
            if guard:
                blk.close("end")
            if multi_op:
                blk.close("end")
        if multi_op:
            blk.stmt("default: ;")
            blk.close("endcase")
        # the don't-care defaults of the op temporaries, right after the
        # output defaults (before the case): no latch, no logic
        pad = blk._indent * 2
        lines = [pad + " ".join(f"{t} = 'x;" for t in self._tmps[k:k + 6])
                 for k in range(0, len(self._tmps), 6)]
        blk.lines[1:1] = lines

    def declare_values(self):
        raise NotImplementedError

    def emit_unpacker_outputs(self):
        """The unpacker lane module: its unpacked values onto the output
        buses xa_/xb_/dena_/denb_ of the mode (one slice per value)."""
        mod, p, bus = self.mod, self.p, self.bus
        XT = self.eng.XT
        size = self.fmt.size if self.fam == "block" else 1
        # a comb block with a zero default: the lane module drives only its
        # lane's slice of the mode-wide buses, the other slices stay 0 so
        # the unit's OR of its lanes is clean
        blk = mod.comb()
        blk.stmt(" ".join(f"x{src}_{bus} = '0; den{src}_{bus} = '0;" for src in self.srcs))
        for i in self.lanes:
            for j in range(size):
                k = self.elem(i, j, size)
                for src in self.srcs:
                    blk.stmt(f"x{src}_{bus}[{k}*{XT} +: {XT}] = {self.x(src, k)};")
                    blk.stmt(f"den{src}_{bus}[{k}] = {self.den(src, k)};")

    def emit_op(self, op: str):
        raise NotImplementedError

    def register_op(self, op: str):
        """Register the structures of one op: one per lane by default."""
        for i in self.lanes:
            self.structure(op, i)

    # ---- unpacked operands (float, posit, block modes) ------------------------
    def declare_unpacked(self):
        """p_u{a,b}{i}: the unpacked lane (V plus the denormal flag; size of
        them for a block), then per value k the X array p_x{a,b}[k] and the
        denormal flags p_den{a,b}[k]."""
        mod, p, fmt, e = self.mod, self.p, self.fmt, self.eng
        VW, XT = e.VW, e.XT
        size = fmt.size if self.fam == "block" else 1
        nv = self.count * size
        unp = None
        unp_slot = "unpacker"
        if self.fam == "float" and not self.shared_unpack and hasattr(self, "_fp_module") and "float_unpacker" not in self.shared:
            fam = self.family_for("unpacker")
            if fam:
                m = self._fp_module("unpacker", fam, fmt=_core(fmt))
                if m:
                    unp = (self.library_module(m), fam[0])
        elif self.fam == "posit" and not self.shared_unpack and hasattr(self, "_posit_module"):
            # the posit unit's decoder (the mode's posit_unit structure)
            fam = self.family_for("posit_unit")
            if fam:
                m = self._posit_module("decode", fam, fmt=fmt)
                if m:
                    unp = (self.library_module(m), fam[0])
                    unp_slot = "posit_unit"
        for i in self.lanes:
            for src in self.srcs:
                u = f"{p}_u{src}{self.tag(i)}"
                if self.fam == "block":
                    mod.logic(u, size * (VW + 1))
                    mod.assign(u, f"{p}_unpack_s({self.pat(src, i)}, daz)")
                else:
                    mod.logic(u, VW + 1)
                    arg = x87_to_core(self.pat(src, i)) if isinstance(fmt, X87Format) \
                        else self.pat(src, i)
                    if "float_unpacker" in self.shared:
                        mod.assign(u, f"usu{src}_{self.bus}[({i})*{VW+1} +: {VW+1}]")
                    elif unp is not None:
                        mod.raw(f"  // structure core.{unp_slot}.m{self.mi}: family {unp[1]} realized by the library module {unp[0]}"
                                + (" (the decoder)" if unp_slot == "posit_unit" else ""))
                        mod.raw(f"  {unp[0]} u_{p}_unpack_{src}{self.tag(i)} (.b({arg}), .daz(daz), .u({u}));")
                    else:
                        mod.assign(u, f"{p}_unpack_s({arg}, daz)")
        for src in self.srcs:
            mod.logic(f"{p}_x{src}", XT, dims=f" [0:{max(nv - 1, 0)}]")
            mod.logic(f"{p}_den{src}", 1, dims=f" [0:{max(nv - 1, 0)}]")
        if self.shared_unpack:
            # the mode's unpacker structure decoded the operands: read its buses
            for i in self.lanes:
                for j in range(size):
                    k = self.elem(i, j, size)
                    for src in self.srcs:
                        mod.assign(self.x(src, k), f"x{src}_{self.bus}[{k}*{XT} +: {XT}]")
                        mod.assign(self.den(src, k), f"den{src}_{self.bus}[{k}]")
            return
        for i in self.lanes:
            for j in range(size):
                k = self.elem(i, j, size)
                for src in self.srcs:
                    u = f"{p}_u{src}{self.tag(i)}"
                    if self.fam == "block":
                        mod.assign(self.x(src, k), f"{p}_x({u}[{j*(VW+1)} +: {VW}])")
                        mod.assign(self.den(src, k), f"{u}[{j*(VW+1)+VW}]")
                    else:
                        mod.assign(self.x(src, k), f"{p}_x({u}[{VW-1}:0])")
                        mod.assign(self.den(src, k), f"{u}[{VW}]")

    # ---- conversion into a block target (shared by every source family) -------
    def cvt_to_block(self, op: str, tgt: BlockFormat, set_idx: int, src: str,
                     base: int, nvals: int, den_of=None):
        """Values of operand `src` (X array, nvals of them) grouped into
        blocks of tgt; the quantizer's flags per element, plus the
        source's denormal flag when den_of is given."""
        p, e = self.p, self.eng
        XT = e.XT
        ttag = fmt_tag(tgt)
        tw, tsize = tgt.width, tgt.size
        nblk = nvals // tsize
        for g in (self.groups if self.groups is not None else range(nblk)):
            tmp = f"{p}_o{self.oi}c{set_idx}_{self.tag(g)}"
            self.tmp(f"{tmp}_xs", tsize * XT)
            self.tmp(tmp, tsize * FW + tw)
            for j in range(tsize):
                self.blk.stmt(f"{tmp}_xs[{j*XT} +: {XT}] = {self.x(src, g*tsize + j)};")
            self.blk.stmt(f"{tmp} = {p}_quant_{ttag}({tmp}_xs, rnd, "
                          f"{self.words(base + g*tsize, tsize)}, ftz);")
            self.put(set_idx, g, tw, f"{tmp}[{tw-1}:0]")
            # an exactly zero source element keeps its sign in a signed float element (the reference's
            # rounder.block takes the source signs; the quantizer's pack yields +0), as the block
            # arithmetic path does after its quantizer
            el = tgt.elem
            if isinstance(el, FloatFormat) and el.signed:
                we, XW = el.width, e.XW
                for j in range(tsize):
                    exact_zero = f"({tmp}_xs[{j*XT} +: {XW+1}] == 0 && {tmp}_xs[{j*XT+XT-2} +: 2] == 0)"
                    zero = f"{{{tmp}_xs[{j*XT+XT-3}], {we-1}'d0}}"
                    self.put(set_idx, g, tw, f"{exact_zero} ? {zero} : {tmp}[{j*we} +: {we}]", off=j*we, width=we)
            for j in range(tsize):
                k = g * tsize + j
                fl = f"{tmp}[{tw + j*FW} +: {FW}]"
                if den_of is not None:
                    fl += f" | {flag_if(den_of(k), 'denormal')}"
                self.put_flags(base + k, fl, set_idx)

    def register_cvt(self, op: str, lanes: int):
        for i in range(lanes):
            self.structure(op, i)


def bool_sv(v) -> str:
    return bool_(v)
