"""Float, fp80 and posit modes of the ALU seed: every value unpacked into
the engine's X representation, the arithmetic ops through the engine's
add/mul/div/sqrt and the mode's pack, the comparisons and min/max on X,
sign ops on the pattern, and conversions into every cvt target."""
from __future__ import annotations

from chialu.targets.rtl.alu_mode import (NOFLAG, ModeEmitter, core_to_x87,
                                          flag, flag_if)
from chialu.targets.rtl.engine import FW, fmt_tag, _core
from chialu.targets.rtl.writer import bool_, cmp_flags
from chialu.verify import alu_ref as A
from chialu.verify.formats import (BlockFormat, FloatFormat, PositFormat,
                                    X87Format, _mask)


def _rounds(op: str) -> bool:
    """An op whose result the mode's rounder packs: the arithmetic ops and
    the conversions into scalar targets (compare, min/max and the sign ops
    write patterns directly)."""
    if op in ("fadd", "fsub", "fmul", "fdiv", "fsqrt") or op in A.FUSED_OPS:
        return True
    tgt = A.cvt_target(op)
    return tgt is not None and not isinstance(tgt, BlockFormat)


FMA_SERVED = frozenset({"fadd", "fsub", "fmul"} | set(A.FUSED_OPS))
"""The ops a fused fp_fma family computes through its one datapath."""


class FloatModeEmitter(ModeEmitter):

    def isa_posit(self):
        family = self.families.get(f"core.posit_unit.m{self.mi}")
        return bool(family and family[0] == "posit_ieee_interop" and family[1].get("interop_style") == "isa_posit_replaces_float")

    def family_for(self, kind, target=""):
        family = super().family_for(kind, target)
        if family is None and self.isa_posit():
            defaults = {"fp_adder": "single_path", "fp_multiplier": "sig_mul_then_round",
                        "fp_comparator": "dedicated_magnitude_comparator"}
            if kind in defaults:
                return defaults[kind], {}
        return family

    def declare_values(self):
        self.lib_inst: dict = {}
        self.declare_unpacked()
        if self.fam == "float":
            self.declare_library()
        elif self.fam == "posit":
            self.declare_posit_library()
            self.declare_library()
        self.declare_secondary_library()
        self.declare_sign_library()

    def declare_secondary_library(self):
        """A second simultaneous unary result needs its own arithmetic/pack ports."""
        if not (self.lay["d_w"] or self.lay.get("dual_in_y")):
            return
        unary = [(index, op) for index, op in self.ops if op == "fsqrt" or A.is_cvt(op)]
        if not unary:
            return
        prefix, operations, primary = self.p, self.ops, self.lib_inst
        try:
            self.p, self.ops, self.lib_inst, self.library_set = prefix + "_second", unary, {}, 1
            if self.fam == "posit":
                self.declare_posit_library()
            self.declare_library()
            secondary = self.lib_inst
        finally:
            self.p, self.ops, self.lib_inst, self.library_set = prefix, operations, primary, 0
        primary.update({key + (1,): value for key, value in secondary.items()})

    def library_instance(self, *key):
        return self.lib_inst.get(key + (self.set_idx,)) if self.set_idx else self.lib_inst.get(key)

    def declare_sign_library(self):
        """Apply floating sign masks through the selected logic gate row."""
        from chialu.targets.rtl import families as FAM
        ops = [op for _, op in self.ops if op in ("fabs", "fneg")]
        family = self.family_for("logic") if ops else None
        if not family:
            return
        if family[0] == "alu_pg_fused" and "raw_pg" in self.shared:
            for i in self.lanes:
                for si in range(self.shared["raw_pg"]["sets"]):
                    index = f"(({i})+{si*self.count})"
                    wires = tuple(f"pg_{arg}_{self.bus}[{index}*{self.fmt.width} +: {self.fmt.width}]"
                                  for arg in ("a", "b", "p", "g", "sum"))
                    self.lib_inst[("raw_sign", self.tag(i), si)] = wires + (f"pg_cin_{self.bus}[{index}]",)
            return
        module = FAM.logic_module(family[0], family[1], self.fmt.width)
        if module is None:
            return
        name = self.library_module(module)
        params = ", ".join(f".{key}({value})" for key, value in module.params.items())
        sets = max(len(self.result_sets(op)) for op in ops)
        for i in self.lanes:
            for si in range(sets):
                tag = f"{self.tag(i)}_s{si}"
                a = self.tmp(f"{self.p}_sign_a{tag}", self.fmt.width)
                b = self.tmp(f"{self.p}_sign_b{tag}", self.fmt.width)
                op = self.tmp(f"{self.p}_sign_op{tag}", 2)
                y = self.mod.logic(f"{self.p}_sign_y{tag}", self.fmt.width)
                self.mod.raw(f"  {name} #({params}) u_sign_{tag} (.a({a}), .b({b}), .op({op}), .y({y}));")
                self.lib_inst[("sign_logic", self.tag(i), si)] = (a, b, op, y)

    # ---- the family library ---------------------------------------------------------
    def _fp_module(self, kind: str, fam, **kw):
        from chialu.targets.rtl import families as FAM
        from chialu.targets.rtl.families.fp import Geom
        return FAM.fp_module(kind, fam[0], fam[1], Geom.of_engine(self.eng), **kw)

    def producers_normalize(self, round_ops) -> bool:
        """Whether every producer of the mode's rounded ops delivers a
        normalized X: the fused multiply-add does (its one normalize is
        the last stage; families/fp.py fma_normalizes names the one
        anticipator choice that leaves a position to the rounder), so a
        mode whose rounded ops are fadd, fsub and fmul through it needs
        no normalizer in the rounder."""
        from chialu.targets.rtl.families.fp import fma_normalizes
        fma = self.family_for("fp_fma")
        return bool(fma) and fma_normalizes(fma[0], fma[1]) and bool(round_ops) and set(round_ops) <= FMA_SERVED

    def shared_arithmetic(self, kind):
        if f"interop_{kind}" not in self.shared:
            return False
        for i in self.lanes:
            index = f"(({i})+{getattr(self, 'library_set', 0)*self.count})"
            a = f"ix_{kind}_a_{self.bus}[{index}*{self.eng.XT} +: {self.eng.XT}]"
            b = f"ix_{kind}_b_{self.bus}[{index}*{self.eng.XT} +: {self.eng.XT}]"
            y = f"iy_{kind}_{self.bus}[{index}*{self.eng.XT} +: {self.eng.XT}]"
            if kind == "fp_adder":
                wires = (a, b, f"ix_{kind}_sub_{self.bus}[{i}]", y)
            elif kind == "fp_fma":
                c = f"ix_{kind}_c_{self.bus}[{index}*{self.eng.XT} +: {self.eng.XT}]"
                wires = (a, b, c, f"ix_{kind}_op_{self.bus}[{index}*3 +: 3]", y)
            elif kind == "fp_sqrt":
                wires = (a, y)
            elif kind == "fp_comparator":
                wires = (a, b, f"ilt_{kind}_{self.bus}[{i}]", f"ieq_{kind}_{self.bus}[{i}]")
            else:
                wires = (a, b, y)
            self.lib_inst[(kind, self.tag(i))] = wires
        return True

    def _posit_module(self, kind: str, fam, **kw):
        from chialu.targets.rtl import families as FAM
        from chialu.targets.rtl.families.fp import Geom
        return FAM.posit_module(kind, fam[0], fam[1], geom=Geom.of_engine(self.eng), **kw)

    def _posit_unit_of(self, tgt):
        """The (family, pins) of the posit unit of the mode whose format is
        `tgt` (a float lane converting into a posit format reads the posit
        mode's interop decision), or None."""
        from chialu.verify.formats import parse_format
        for j, m in enumerate(self.spec["modes"]):
            f = parse_format(str(m["format"]))
            if isinstance(f, PositFormat) and f.name == tgt.name:
                return self.families.get(f"core.posit_unit.m{j}")
        return None

    def declare_posit_library(self):
        """The posit unit of a posit mode (its posit_unit structure) from the
        library: the encoder per lane (its x set in every op arm, as the
        rounder's), and under posit_adder_multiplier the unit's X adder
        (fp.add_sv with the sig_datapath slot's significand adder), its
        multiplier (exact, or the PLAM module under an approximate
        contract with approximation logarithmic_fraction), and under
        operator_set add_mul_div its divider and square root (the sig_div
        slot); under posit_ieee_interop with boundary_converters one
        dedicated converter per lane and scalar target out of the lane."""
        mod, p, e, fmt = self.mod, self.p, self.eng, self.fmt
        XT = e.XT
        fam = self.family_for("posit_unit")
        if not fam or self.split is not None:
            return
        family, pins = fam
        ops = {op for _o, op in self.ops}

        def inst(name, conns, comment):
            mod.raw(f"  // {comment}")
            mod.raw(f"  {name} {conns};")

        m = self._posit_module("encode", fam, fmt=fmt, tokens=e.tokens)
        if m:
            name = self.library_module(m)
            for i in self.lanes:
                t = self.tag(i)
                x = self.tmp(f"{p}_pe_x{t}", XT)
                word = self.tmp(f"{p}_pe_w{t}", self.sr_bits)
                fl, bits = mod.logic(f"{p}_pe_fl{t}", FW), mod.logic(f"{p}_pe_b{t}", fmt.width)
                inst(name, f"u_{p}_penc{t} (.x({x}), .rnd(rnd), .word({word}), .ftz(ftz), .fl({fl}), .bits({bits}))",
                     f"structure core.posit_unit.m{self.mi}: family {family} realized by the library module {name} (the encoder)")
                self.lib_inst[("posit_enc", t)] = (x, word, fl, bits)
        if family == "posit_adder_multiplier":
            plam = str(pins.get("approximation", "none")) == "logarithmic_fraction"
            op_set = str(pins.get("operator_set", "add_mul"))
            if op_set == "add_mul" and ops & {"fdiv", "fsqrt"}:
                raise ValueError("posit operator_set=add_mul cannot implement fdiv/fsqrt; select add_mul_div")
            sig_pins = {"sig_adder." + k[len("sig_datapath."):]: v for k, v in pins.items() if k.startswith("sig_datapath.")}
            sig_pins.setdefault("sig_adder.family", "parallel_prefix")
            # the unit's own X adder and multiplier stand where no core.fp_adder / core.fp_multiplier family is
            # selected for the mode (the behavioral seed); a selected family is realized by the float path below
            if ops & {"fadd", "fsub"} and self.family_for("fp_adder") is None:
                m = self._fp_module("fp_adder", ("single_path", sig_pins))
                if m:
                    name = self.library_module(m)
                    for i in self.lanes:
                        t = self.tag(i)
                        xa, xb, sub = self.tmp(f"{p}_fa_xa{t}", XT), self.tmp(f"{p}_fa_xb{t}", XT), self.tmp(f"{p}_fa_sub{t}", 1)
                        y = mod.logic(f"{p}_fa_y{t}", XT)
                        inst(name, f"u_{p}_fadd{t} (.xa({xa}), .xb({xb}), .sub({sub}), .y({y}))",
                             f"structure core.posit_unit.m{self.mi}: family {family}: the unit's adder on X realized by the library "
                             f"module {name} (sig_datapath {sig_pins['sig_adder.family']})")
                        self.lib_inst[("fp_adder", t)] = (xa, xb, sub, y)
            if "fmul" in ops and (plam or self.family_for("fp_multiplier") is None):
                m = self._posit_module("plam", fam, fmt=fmt) if plam else self._fp_module("fp_multiplier", ("sig_mul_then_round", {}))
                if m:
                    name = self.library_module(m)
                    for i in self.lanes:
                        t = self.tag(i)
                        xa, xb = self.tmp(f"{p}_fm_xa{t}", XT), self.tmp(f"{p}_fm_xb{t}", XT)
                        y = mod.logic(f"{p}_fm_y{t}", XT)
                        inst(name, f"u_{p}_fmul{t} (.xa({xa}), .xb({xb}), .y({y}))",
                             f"structure core.posit_unit.m{self.mi}: family {family}: the unit's multiplier on X realized by the "
                             f"library module {name}" + (" (PLAM: the fraction multiply as a Mitchell add, under the approximate contract)"
                                                        if plam else " (the exact product)"))
                        self.lib_inst[("fp_multiplier", t)] = (xa, xb, y)
            # as for the adder and the multiplier: a selected core.fp_divider family is realized by the float path
            if op_set == "add_mul_div" and ops & {"fdiv", "fsqrt"} and self.family_for("fp_divider") is None:
                div_pins = {k: v for k, v in pins.items() if k.startswith("sig_div.")}
                for op, kind, short, dfam in (("fdiv", "fp_divider", "fd", "sig_div_then_round"),
                                              ("fsqrt", "fp_sqrt", "fq", "sig_sqrt_then_round")):
                    if op not in ops:
                        continue
                    dp = dict(div_pins) if op == "fdiv" else {"sig_sqrt." + k[len("sig_div."):]: v for k, v in div_pins.items()}
                    m = self._fp_module(kind, (dfam, dp))
                    if not m:
                        continue
                    name = self.library_module(m)
                    for i in self.lanes:
                        t = self.tag(i)
                        xa = self.tmp(f"{p}_{short}_xa{t}", XT)
                        y = mod.logic(f"{p}_{short}_y{t}", XT)
                        if op == "fdiv":
                            xb = self.tmp(f"{p}_{short}_xb{t}", XT)
                            inst(name, f"u_{p}_{op}{t} (.xa({xa}), .xb({xb}), .y({y}))",
                                 f"structure core.posit_unit.m{self.mi}: family {family} (operator_set add_mul_div): the unit's "
                                 f"divider on X realized by the library module {name}")
                            self.lib_inst[(kind, t)] = (xa, xb, y)
                        else:
                            inst(name, f"u_{p}_{op}{t} (.xa({xa}), .y({y}))",
                                 f"structure core.posit_unit.m{self.mi}: family {family} (operator_set add_mul_div): the unit's "
                                 f"square root on X realized by the library module {name}")
                            self.lib_inst[(kind, t)] = (xa, y)
        if family == "posit_ieee_interop":
            style = str(pins.get("interop_style", "boundary_converters"))
            direction = str(pins.get("conversion_direction", "posit_to_ieee"))
            if direction == "ieee_to_posit" and any(isinstance(_core(A.cvt_target(op)), (FloatFormat, X87Format)) for op in ops if A.cvt_target(op) is not None):
                raise ValueError("conversion_direction=ieee_to_posit cannot implement a posit-to-IEEE conversion operation")
            if direction in ("posit_to_ieee", "bidirectional"):
                for op in sorted(ops):
                    tgt = A.cvt_target(op)
                    if tgt is None or isinstance(tgt, BlockFormat):
                        continue
                    tc = _core(tgt)
                    if not isinstance(tc, (FloatFormat, PositFormat)) or getattr(tc, "exp_only", False):
                        continue
                    m = self._posit_module("cvt", fam, fmt=fmt, target=tc, tokens=e.tokens)
                    if not m:
                        continue
                    name = self.library_module(m)
                    for i in self.lanes:
                        t = self.tag(i) + "_" + fmt_tag(tgt)
                        x = self.tmp(f"{p}_cv_x{t}", XT)
                        word = self.tmp(f"{p}_cv_w{t}", self.sr_bits)
                        fl, bits = mod.logic(f"{p}_cv_fl{t}", FW), mod.logic(f"{p}_cv_b{t}", tc.width)
                        inst(name, f"u_{p}_cvt{t} (.x({x}), .rnd(rnd), .word({word}), .ftz(ftz), .fl({fl}), .bits({bits}))",
                             f"structure core.posit_unit.m{self.mi}: family {family} (boundary_converters): the converter into "
                             f"{tgt.name} realized by the library module {name}")
                        self.lib_inst[("converter", self.tag(i), tgt.name)] = (x, word, fl, bits)
            else:
                mod.raw(f"  // structure core.posit_unit.m{self.mi}: family {family} ({style}): the conversions share the lane's X "
                        f"datapath and pack functions")

    def declare_library(self):
        """One library instance per lane for the float structures whose
        declared family the library realizes: the significand adder (fadd,
        fsub), the significand multiplier (fmul), the comparator (fcmp,
        fmin, fmax), the rounder (one per rounding op and lane under
        dedicated_per_op, one per lane otherwise) and the converters'
        rounders per target; the unpacker is instantiated where the
        operands are decoded (declare_unpacked)."""
        mod, p, e = self.mod, self.p, self.eng
        XT = e.XT
        ops = {op for _o, op in self.ops}
        core = _core(self.fmt.elem if self.fam == "block" else self.fmt)

        def inst(name, conns, comment):
            mod.raw(f"  // {comment}")
            mod.raw(f"  {name} {conns};")

        fma = self.family_for("fp_fma")
        fused = bool(fma) and fma[0] != "separate_multiplier_and_adder"
        fused_ops = ops & set(A.FUSED_OPS)
        contract = str(self.spec.get("fma_contract", "fused"))
        if fused_ops and self.split != "rounder" and fma:
            # the rules of the fused multiply-add ops: the fused contract (one rounding of the exact product plus
            # addend) is a fused family's datapath, the sequential one (the product rounded to the format first)
            # is the separate multiplier's then adder's; a unit without declared families (the checker's reference
            # copy, the behavioral realization) computes either contract with the engine's functions. The fp_fma
            # families carry the two rules as their classification (fp_spaces.FUSED_REQUIRES, SEPARATE_REQUIRES;
            # chialu/behavior_rules.py prunes the family per mode), so these raises are the last defense
            if contract == "fused" and not fused:
                raise ValueError(f"core.fp_fma.m{self.mi}: the fused multiply-add ops {sorted(fused_ops)} under "
                                 f"fma_contract fused round the exact product plus addend once, which needs a fused "
                                 f"fp_fma family (classic_fma, reduced_latency_fma, multipath_fma, bridge_fma); "
                                 f"separate_multiplier_and_adder rounds the product first, which is fma_contract "
                                 f"sequential (chialu.behavior_rules removes it under this contract)")
            if contract == "sequential" and fused:
                raise ValueError(f"core.fp_fma.m{self.mi}: {fma[0]} rounds the exact product plus addend once, and "
                                 f"fma_contract sequential asks for the product rounded to the format before the add; "
                                 f"the sequential contract's fused ops go through separate_multiplier_and_adder "
                                 f"(chialu.behavior_rules removes the fused families under this contract)")
        if fused and self.split != "rounder" and ops & FMA_SERVED \
                and not any(("fp_fma", self.tag(i)) in self.lib_inst for i in self.lanes):
            # one fused multiply-add serves fadd, fsub, fmul and the fused ops under its op code `fop`, and the
            # adder's and the multiplier's library slots point at the same instance
            if not self.shared_arithmetic("fp_fma"):
                from chialu.targets.rtl.families.fp import fma_takes_rnd
                m = self._fp_module("fp_fma", fma, fmt=core)
                if m is None:
                    raise ValueError(f"core.fp_fma.m{self.mi}: {fma[0]} has no module at this geometry")
                name = self.library_module(m)
                # the fused rounding of reduced_latency_fma reads the rounding mode and delivers a rounded result
                rnd_conn = ", .rnd(rnd)" if fma_takes_rnd(*fma) else ""
                for i in self.lanes:
                    t = self.tag(i)
                    xa, xb, xc = self.tmp(f"{p}_ff_xa{t}", XT), self.tmp(f"{p}_ff_xb{t}", XT), self.tmp(f"{p}_ff_xc{t}", XT)
                    fop = self.tmp(f"{p}_ff_op{t}", 3)
                    y = mod.logic(f"{p}_ff_y{t}", XT)
                    inst(name, f"u_{p}_ffma{t} (.xa({xa}), .xb({xb}), .xc({xc}), .fop({fop}){rnd_conn}, .y({y}))",
                         f"structure core.fp_fma.m{self.mi}: family {fma[0]} realized by the library module {name}; the "
                         f"fadd, fsub and fmul of structures core.fp_adder.m{self.mi} and core.fp_multiplier.m{self.mi}"
                         + (", and the fused multiply-add ops," if fused_ops else "") + " go through it")
                    self.lib_inst[("fp_fma", t)] = (xa, xb, xc, fop, y)
            for i in self.lanes:
                t = self.tag(i)
                xa, xb, xc, fop, y = self.lib_inst[("fp_fma", t)]
                self.lib_inst[("fp_adder", t)] = (xa, xb, "", y)
                self.lib_inst[("fp_multiplier", t)] = (xa, xb, y)
                self.lib_inst[("fp_fma_op", t)] = fop
        if fused_ops and contract == "fused" and self.split != "rounder" \
                and not any(("fp_fma", self.tag(i)) in self.lib_inst for i in self.lanes):
            # the fused ops without a library datapath (the behavioral realization, the checker's reference copy):
            # one {p}_fma per lane whose operands and negation flags the ops' arms drive, rather than one call per
            # op, since each call unrolls the function's alignment and normalization loops
            for i in self.lanes:
                t = self.tag(i)
                bxa, bxb = self.tmp(f"{p}_bf_xa{t}", XT), self.tmp(f"{p}_bf_xb{t}", XT)
                bxc = self.tmp(f"{p}_bf_xc{t}", XT)
                bnp, bnc = self.tmp(f"{p}_bf_np{t}", 1), self.tmp(f"{p}_bf_nc{t}", 1)
                by = mod.logic(f"{p}_bf_y{t}", XT)
                mod.assign(by, f"{p}_fma({bxa}, {bxb}, {bxc}, {bnp}, {bnc})")
                self.lib_inst[("fp_fma_behav", t)] = (bxa, bxb, bxc, bnp, bnc, by)
        if fused_ops and contract == "sequential" and self.split != "rounder" \
                and not any(("fma_product_rounder", self.tag(i)) in self.lib_inst for i in self.lanes):
            # the sequential contract's product rounding and read back: the mode's rounder and unpacker families
            # (dedicated instances for the product; a shared one is the unit's, so the product takes its own)
            fam_r = self.family_for("rounder") or ("dedicated_per_op", {})
            if fam_r[0] == "shared_across_formats":
                fam_r = ("dedicated_per_op", {})
            m = self._fp_module("rounder", fam_r, fmt=core, tokens=e.tokens)
            if m:
                name = self.library_module(m)
                for i in self.lanes:
                    t = self.tag(i)
                    x, word = self.tmp(f"{p}_fp_rx{t}", XT), self.tmp(f"{p}_fp_rw{t}", self.sr_bits)
                    fl, bits = mod.logic(f"{p}_fp_rfl{t}", FW), mod.logic(f"{p}_fp_rb{t}", core.width)
                    inst(name, f"u_{p}_fmaprod_round{t} (.x({x}), .rnd(rnd), .word({word}), .ftz(ftz), .fl({fl}), .bits({bits}))",
                         f"structure core.rounder.m{self.mi}: family {fam_r[0]} realized by the library module {name} for "
                         f"the fused multiply-add's product, rounded to {core.name} under fma_contract sequential")
                    self.lib_inst[("fma_product_rounder", t)] = (x, word, fl, bits)
            fam_u = self.family_for("unpacker")
            m = self._fp_module("unpacker", fam_u, fmt=core) if fam_u and fam_u[0] != "shared_across_formats" else None
            if m:
                name = self.library_module(m)
                for i in self.lanes:
                    t = self.tag(i)
                    b, u = self.tmp(f"{p}_fp_ub{t}", core.width), mod.logic(f"{p}_fp_uu{t}", e.VW + 1)
                    inst(name, f"u_{p}_fmaprod_unpack{t} (.b({b}), .daz(daz), .u({u}))",
                         f"structure core.unpacker.m{self.mi}: family {fam_u[0]} realized by the library module {name} "
                         f"for the fused multiply-add's rounded product, read back as the adder's operand")
                    self.lib_inst[("fma_product_unpacker", t)] = (b, u)
        # the sequential contract's fused ops go through the lane's multiplier and adder, whatever else the lane serves
        sequential = bool(fused_ops) and contract == "sequential"
        if (ops & {"fadd", "fsub"} or sequential) and self.split != "rounder" \
                and not any(("fp_adder", self.tag(i)) in self.lib_inst for i in self.lanes):
            fam = self.family_for("fp_adder")
            # fp_cpa: the unit shares one carry-propagate adder between this mode's significand add and the
            # integer adders; the family module takes its significand adder through the sa_* ports
            ext = "fp_cpa" in self.shared
            m = None if self.shared_arithmetic("fp_adder") else self._fp_module("fp_adder", fam, external_sig_adder=ext) if fam else None
            if m:
                name = self.library_module(m)
                for i in self.lanes:
                    t = self.tag(i)
                    xa, xb, sub = self.tmp(f"{p}_fa_xa{t}", XT), self.tmp(f"{p}_fa_xb{t}", XT), self.tmp(f"{p}_fa_sub{t}", 1)
                    y = mod.logic(f"{p}_fa_y{t}", XT)
                    sa = (f", .sa_a(sa_a_{self.bus}), .sa_b(sa_b_{self.bus}), .sa_cin(sa_cin_{self.bus}), "
                          f".sa_s(sa_s_{self.bus}), .sa_cout(sa_cout_{self.bus})") if ext else ""
                    inst(name, f"u_{p}_fadd{t} (.xa({xa}), .xb({xb}), .sub({sub}), .y({y}){sa})",
                         f"structure core.fp_adder.m{self.mi}: family {fam[0]} realized by the library module {name}"
                         + (" (its significand adder is the unit's shared carry-propagate adder)" if ext else ""))
                    self.lib_inst[("fp_adder", t)] = (xa, xb, sub, y)
        if ("fmul" in ops or sequential) and self.split != "rounder" \
                and not any(("fp_multiplier", self.tag(i)) in self.lib_inst for i in self.lanes):
            fam = self.family_for("fp_multiplier")
            scale_feedback = bool(self.fam == "block" and fam and fam[0] == "round_fused_in_reduction")
            fractional_scale = scale_feedback and (not self.fmt.scale.exp_only or not isinstance(core, FloatFormat))
            m = None if self.shared_arithmetic("fp_multiplier") else self._fp_module("fp_multiplier", fam, M=getattr(core, "man_bits", e.SW - 1), bias=getattr(core, "bias", 0),
                                scale_feedback=scale_feedback, scale_format=self.fmt.scale if scale_feedback else None,
                                fmt=core, tokens=e.tokens) if fam else None
            if m:
                name = self.library_module(m)
                fused = fam[0] == "round_fused_in_reduction"
                for i in self.lanes:
                    t = self.tag(i)
                    xa, xb = self.tmp(f"{p}_fm_xa{t}", XT), self.tmp(f"{p}_fm_xb{t}", XT)
                    y = mod.logic(f"{p}_fm_y{t}", XT)
                    feedback = ""
                    if scale_feedback:
                        scale = self.tmp(f"{p}_fm_scale{t}", e.EW)
                        raw = mod.logic(f"{p}_fm_raw{t}", XT)
                        feedback = f", .scale_exp({scale}), .raw_y({raw})"
                        if fractional_scale:
                            scale_sig = self.tmp(f"{p}_fm_scale_sig{t}", self.fmt.scale.man_bits + 1)
                            scale_sp = self.tmp(f"{p}_fm_scale_sp{t}", 2)
                            word = self.tmp(f"{p}_fm_scale_word{t}", self.sr_bits)
                            feedback += f", .scale_sig({scale_sig}), .scale_sp({scale_sp}), .word({word})"
                    inst(name, f"u_{p}_fmul{t} (.xa({xa}), .xb({xb}){', .rnd(rnd)' if fused else ''}, .y({y}){feedback})",
                         f"structure core.fp_multiplier.m{self.mi}: family {fam[0]} realized by the library module {name}")
                    self.lib_inst[("fp_multiplier", t)] = (xa, xb, y)
                    if scale_feedback:
                        self.lib_inst[("fp_multiplier_scale", t)] = (scale, raw)
                        if fractional_scale:
                            self.lib_inst[("fp_multiplier_fractional_scale", t)] = (scale_sig, scale_sp, word)
        if ops & {"fcmp", "fmin", "fmax"}:
            fam = self.family_for("fp_comparator")
            m = None if self.shared_arithmetic("fp_comparator") else self._fp_module("fp_comparator", fam) if fam else None
            if m:
                name = self.library_module(m)
                for i in self.lanes:
                    t = self.tag(i)
                    xa, xb = self.tmp(f"{p}_fc_xa{t}", XT), self.tmp(f"{p}_fc_xb{t}", XT)
                    lt, eq = mod.logic(f"{p}_fc_lt{t}", 1), mod.logic(f"{p}_fc_eq{t}", 1)
                    inst(name, f"u_{p}_fcmp{t} (.xa({xa}), .xb({xb}), .lt({lt}), .eq({eq}))",
                         f"structure core.fp_comparator.m{self.mi}: family {fam[0]} realized by the library module {name}")
                    self.lib_inst[("fp_comparator", t)] = (xa, xb, lt, eq)
        if ops & {"fdiv", "fsqrt"} and self.split != "rounder":
            fam = self.family_for("fp_divider")
            for op, kind, short in (("fdiv", "fp_divider", "fd"), ("fsqrt", "fp_sqrt", "fq")):
                op_family = fam
                if op_family is None and self.isa_posit():
                    op_family = ("sig_sqrt_then_round" if op == "fsqrt" else "sig_div_then_round", {})
                m = None if op in ops and self.shared_arithmetic(kind) else self._fp_module(kind, op_family) if op_family and op in ops else None
                if not m:
                    continue
                name = self.library_module(m)
                for i in self.lanes:
                    t = self.tag(i)
                    xa = self.tmp(f"{p}_{short}_xa{t}", XT)
                    y = mod.logic(f"{p}_{short}_y{t}", XT)
                    if op == "fdiv":
                        xb = self.tmp(f"{p}_{short}_xb{t}", XT)
                        inst(name, f"u_{p}_{op}{t} (.xa({xa}), .xb({xb}), .y({y}))",
                             f"structure core.fp_divider.m{self.mi}: family {op_family[0]} realized by the library module {name} ({op})")
                        self.lib_inst[(kind, t)] = (xa, xb, y)
                    else:
                        inst(name, f"u_{p}_{op}{t} (.xa({xa}), .y({y}))",
                             f"structure core.fp_divider.m{self.mi}: family {op_family[0]} realized by the library module {name} ({op})")
                        self.lib_inst[(kind, t)] = (xa, y)
        # the rounder: this lane module packs when it is the rounder structure or the mode is not split
        packs_here = self.split in (None, "rounder")
        round_ops = [op for op in ops if _rounds(op) and A.cvt_target(op) is None]
        if packs_here and round_ops:
            fam = self.family_for("rounder")
            mfam = self.family_for("fp_multiplier")
            from chialu.targets.rtl.families.fp import fma_takes_rnd
            fma_rounds = bool(self.family_for("fp_fma")) and fma_takes_rnd(*self.family_for("fp_fma"))
            if fam is None and ((mfam and mfam[0] == "round_fused_in_reduction") or fma_rounds) and self.fam != "block":
                fam = ("dedicated_per_op", {})          # a producer that rounds for itself needs the library rounder
            if fam and "float_rounder" in self.shared:
                word_bus = f"rsword_{self.bus}"
                word_width = next(width for name, _, width in mod.ports if name == word_bus)
                for i in self.lanes:
                    index = f"(({i})+{getattr(self, 'library_set', 0)*self.count})"
                    self.lib_inst[("rounder", self.tag(i), None)] = (
                        f"rsx_{self.bus}[{index}*{XT} +: {XT}]",
                        word_bus if word_width == 1 else f"{word_bus}[{index}*{self.sr_bits} +: {self.sr_bits}]",
                        f"rsfl_{self.bus}[{index}*{FW} +: {FW}]",
                        f"rsbits_{self.bus}[{index}*{core.width} +: {core.width}]")
                m = None
            else:
                m = self._fp_module("rounder", fam, fmt=core, tokens=e.tokens,
                                    normalized_input=self.producers_normalize(round_ops)) if fam else None
            if m:
                name = self.library_module(m)
                per_op = fam[0] == "dedicated_per_op"
                keys = [(op, i) for op in sorted(round_ops) for i in self.lanes] if per_op else [(None, i) for i in self.lanes]
                for op, i in keys:
                    t = self.tag(i) + (f"_{op}" if op else "")
                    x = self.tmp(f"{p}_rd_x{t}", XT)
                    word = self.tmp(f"{p}_rd_w{t}", self.sr_bits)
                    fl, bits = mod.logic(f"{p}_rd_fl{t}", FW), mod.logic(f"{p}_rd_b{t}", core.width)
                    inst(name, f"u_{p}_round{t} (.x({x}), .rnd(rnd), .word({word}), .ftz(ftz), .fl({fl}), .bits({bits}))",
                         f"structure core.rounder.m{self.mi}: family {fam[0]} realized by the library module {name}"
                         + (f" ({op})" if op else ""))
                    self.lib_inst[("rounder", self.tag(i), op if per_op else None)] = (x, word, fl, bits)
        # the converters into float targets: the target's rounder, one per target and lane
        if packs_here:
            for op in ops:
                tgt = A.cvt_target(op)
                if tgt is None or isinstance(tgt, BlockFormat):
                    continue
                if all(("converter", self.tag(i), tgt.name) in self.lib_inst for i in self.lanes):
                    continue
                tc = _core(tgt)
                if isinstance(tc, PositFormat):
                    # into a posit format: the posit mode's boundary converter (posit_ieee_interop)
                    pu = self._posit_unit_of(tc)
                    if pu and pu[0] == "posit_ieee_interop" and str(pu[1].get("conversion_direction", "posit_to_ieee")) == "posit_to_ieee" and self.fam != "posit":
                        raise ValueError("conversion_direction=posit_to_ieee cannot implement an IEEE-to-posit conversion operation")
                    if not pu or pu[0] != "posit_ieee_interop" \
                            or str(pu[1].get("conversion_direction", "posit_to_ieee")) not in ("ieee_to_posit", "bidirectional"):
                        continue
                    m = self._posit_module("cvt", pu, fmt=_core(self.fmt), target=tc, tokens=e.tokens)
                    if not m:
                        continue
                    name = self.library_module(m)
                    for i in self.lanes:
                        t = self.tag(i) + "_" + fmt_tag(tgt)
                        x = self.tmp(f"{p}_cv_x{t}", XT)
                        word = self.tmp(f"{p}_cv_w{t}", self.sr_bits)
                        fl, bits = mod.logic(f"{p}_cv_fl{t}", FW), mod.logic(f"{p}_cv_b{t}", tc.width)
                        inst(name, f"u_{p}_cvt{t} (.x({x}), .rnd(rnd), .word({word}), .ftz(ftz), .fl({fl}), .bits({bits}))",
                             f"structure core.converter.m{self.mi}.{tgt.name}: the boundary converter of the {tgt.name} mode's "
                             f"posit unit (family {pu[0]}) realized by the library module {name}")
                        self.lib_inst[("converter", self.tag(i), tgt.name)] = (x, word, fl, bits)
                    continue
                fam = self.family_for("converter", target=tgt.name)
                # the generator names the module from its own content (the family, the
                # target format, the engine geometry and the pins). A name built from
                # the mode prefix would give one text several names, because
                # declare_secondary_library renders the same converter under the
                # prefix it renames.
                m = self._fp_module("converter", fam, fmt=tc, tokens=e.tokens) if fam else None
                if m:
                    name = self.library_module(m)
                    for i in self.lanes:
                        t = self.tag(i) + "_" + fmt_tag(tgt)
                        x = self.tmp(f"{p}_cv_x{t}", XT)
                        word = self.tmp(f"{p}_cv_w{t}", self.sr_bits)
                        fl, bits = mod.logic(f"{p}_cv_fl{t}", FW), mod.logic(f"{p}_cv_b{t}", tc.width)
                        inst(name, f"u_{p}_cvt{t} (.x({x}), .rnd(rnd), .word({word}), .ftz(ftz), .fl({fl}), .bits({bits}))",
                             f"structure core.converter.m{self.mi}.{tgt.name}: family {fam[0]} realized by the library module {name}")
                        self.lib_inst[("converter", self.tag(i), tgt.name)] = (x, word, fl, bits)

    # ---- structures: a posit mode also owns its decode/encode -------------------
    def register_op(self, op: str):
        super().register_op(op)
        if self.fam == "posit":
            for i in range(self.count):
                self.structure(op, i, kind="posit_unit")
        if self.fam == "float":
            # the mode's normalize-and-round stage and operand decode are
            # structures of their own (the seed splits the datapath there)
            for i in range(self.count):
                self.structure(op, i, kind="unpacker")
                if _rounds(op):
                    self.structure(op, i, kind="rounder")
                if op in ("fadd", "fsub", "fmul"):
                    # the mode's multiply-add organization: separate structures on the fp_adder and
                    # fp_multiplier slots, or one fused datapath for the three ops
                    self.structure(op, i, kind="fp_fma")
                if op in A.FUSED_OPS:
                    # a fused multiply-add op is the fp_fma structure's (kind_of), and under the separate
                    # organization the lane's multiplier then adder compute it (fma_contract sequential)
                    self.structure(op, i, kind="fp_adder")
                    self.structure(op, i, kind="fp_multiplier")

    # ---- ops -------------------------------------------------------------------
    def emit_op(self, op: str):
        count = self.count
        tgt = A.cvt_target(op)
        for set_idx, src, oth in self.result_sets(op):
            self.set_idx = set_idx
            base = 0 if set_idx == 0 else A.n_results(self.fmt, count, op)
            if tgt is not None:
                self.emit_cvt(op, tgt, set_idx, src, base)
                continue
            for i in self.lanes:
                self.emit_scalar_op(op, set_idx, src, oth, i, base + i)

    def emit_scalar_op(self, op: str, set_idx: int, src: str, oth: str, i: int, r: int):
        p, e, fmt, blk = self.p, self.eng, self.fmt, self.blk
        w = fmt.width
        xa, xb = self.x(src, i), self.x(oth, i)
        pa, pb = self.pat(src, i), self.pat(oth, i)
        den = self.den(src, i) + ("" if A.is_unary(op) else f" | {self.den(oth, i)}")
        core = _core(fmt)
        nan_a, nan_b = self.is_nan(xa), self.is_nan(xb)
        nan_prop = self.conv.nan_payload == "propagate"
        if op in ("fabs", "fneg"):
            sign_gate = self.lib_inst.get(("sign_logic", self.tag(i), set_idx))
            raw_gate = self.lib_inst.get(("raw_sign", self.tag(i), set_idx))
            if self.fam == "posit":
                nar = f"{{1'b1, {{{w-1}{{1'b0}}}}}}"
                complement = f"~{pa}"
                if sign_gate:
                    ga, gb, go, gy = sign_gate
                    blk.stmt(f"{ga} = {pa}; {gb} = '0; {go} = 2'd3;")
                    complement = gy
                negative = f"({complement} + 1'b1)"
                if raw_gate:
                    ga, gb, _gp, _gg, total, cin = raw_gate
                    blk.stmt(f"{ga} = {pa}; {gb} = '1; {cin} = 1'b1;")
                    negative = total
                body = f"({pa}[{w-1}] ? {negative} : {pa})" if op == "fabs" else negative
                expr = f"({pa} == {nar}) ? {pa} : {body}"
                fl = f"{NOFLAG} | (({pa} == {nar}) ? {flag('nan')} : 0)"
            else:
                top = "(80'd1 << 79)" if isinstance(fmt, X87Format) else f"({w}'d1 << {w-1})"
                if not core.signed:
                    body = pa
                elif op == "fabs":
                    body = f"({pa} & ~{top})"
                else:
                    body = f"({pa} ^ {top})"
                if sign_gate:
                    ga, gb, go, gy = sign_gate
                    mask = (f"~{top}" if op == "fabs" else top) if core.signed else (f"{w}'d{(1 << w)-1}" if op == "fabs" else "'0")
                    blk.stmt(f"{ga} = {pa}; {gb} = {mask}; {go} = 2'd{0 if op == 'fabs' else 2};")
                    body = gy
                if raw_gate:
                    ga, gb, propagate, generate, _total, cin = raw_gate
                    mask = (f"~{top}" if op == "fabs" else top) if core.signed else (f"{w}'d{(1 << w)-1}" if op == "fabs" else "'0")
                    blk.stmt(f"{ga} = {pa}; {gb} = {mask}; {cin} = 1'b0;")
                    body = generate if op == "fabs" else propagate
                if core.has_nan:
                    nan_out = f"({body})" if nan_prop else self.nan_pattern(fmt)
                    expr = f"{nan_a} ? {nan_out} : {body}"
                else:
                    expr = body
                fl = flag_if(nan_a, "nan")
            self.put(set_idx, i, w, expr)
            self.put_flags(r, fl, set_idx)
            return
        if op == "fcmp":
            if self.fam == "posit":
                expr = cmp_flags(w, f"($signed({pa}) > $signed({pb}))", f"({pa} == {pb})",
                                 f"($signed({pa}) < $signed({pb}))")
                if ("fp_comparator", self.tag(i)) in self.lib_inst:
                    lt, eq, gt = self._cmp_exprs(i, xa, xb)
                    expr = f"({nan_a} || {nan_b}) ? ({expr}) : {cmp_flags(w, gt, eq, lt)}"
                fl = NOFLAG
            else:
                lt_ab, eq_ab, lt_ba = self._cmp_exprs(i, xa, xb)
                code = cmp_flags(w, f"({lt_ba})", f"({eq_ab})", f"({lt_ab})")
                expr = f"({nan_a} || {nan_b}) ? {w}'d0 : {code}"
                snan = f"({self.is_snan(xa, pa)} || {self.is_snan(xb, pb)})"     # a quiet comparison: invalid for a signalling NaN
                fl = f"{flag_if(f'{nan_a} || {nan_b}', 'unordered')} | {flag_if(snan, 'invalid')} | {flag_if(den, 'denormal')}"
            self.put(set_idx, i, w, expr)
            self.put_flags(r, fl, set_idx)
            return
        if op in ("fmin", "fmax"):
            if self.fam == "posit":
                pick_a = f"($signed({pa}) <= $signed({pb}))" if op == "fmin" else f"($signed({pa}) >= $signed({pb}))"
                if ("fp_comparator", self.tag(i)) in self.lib_inst:
                    lt, eq, gt = self._cmp_exprs(i, xa, xb)
                    pick_a = f"({nan_a} || {nan_b}) ? ({pick_a}) : ({lt if op == 'fmin' else gt} || {eq})"
                expr = f"({pick_a}) ? {pa} : {pb}"
                fl = NOFLAG
            else:
                sa = f"{pa}[{w-1}]" if core.signed else "1'b0"
                sbit = f"{pb}[{w-1}]" if core.signed else "1'b0"
                za, zb = self.is_zero(xa), self.is_zero(xb)
                lt_ab, eq_ab, lt_ba = self._cmp_exprs(i, xa, xb)
                if op == "fmin":
                    pick_a = (f"(({za} && {zb}) ? ({sa} == 1'b1 || {sa} == {sbit}) : "
                              f"({lt_ab} || {eq_ab}))")
                else:
                    pick_a = (f"(({za} && {zb}) ? ({sa} == 1'b0 || {sa} == {sbit}) : "
                              f"({lt_ba} || {eq_ab}))")
                prop = self.conv.minmax_nan == "propagate"
                if core.has_nan:
                    canon = self.nan_pattern(fmt)
                    nan_res = f"({bool_(nan_prop)} ? ({nan_a} ? {pa} : {pb}) : {canon})"
                    if prop:
                        expr = f"({nan_a} || {nan_b}) ? {nan_res} : ({pick_a} ? {pa} : {pb})"
                    else:
                        expr = (f"({nan_a} && {nan_b}) ? {nan_res} : {nan_a} ? {pb} : {nan_b} ? {pa} : "
                                f"({pick_a} ? {pa} : {pb})")
                else:
                    expr = f"{pick_a} ? {pa} : {pb}"
                nanflag = flag("nan") if core.has_nan else NOFLAG
                snan = f"({self.is_snan(xa, pa)} || {self.is_snan(xb, pb)})"     # invalid for a signalling NaN operand
                fl = (f"(({nan_a} || {nan_b}) ? (({flag('unordered')}) | {flag_if(snan, 'invalid')} | "
                      f"(({bool_(prop)} || ({nan_a} && {nan_b})) ? {nanflag} : {NOFLAG})) : {NOFLAG})"
                      f" | {flag_if(den, 'denormal')}")
            self.put(set_idx, i, w, expr)
            self.put_flags(r, fl, set_idx)
            return
        if op in A.FUSED_OPS and self.fam == "float":
            self.emit_fused_op(op, set_idx, src, oth, i, r)
            return
        # arithmetic: fadd fsub fmul fdiv fsqrt
        xexpr = {"fadd": f"{p}_add({xa}, {xb}, 1'b0)", "fsub": f"{p}_add({xa}, {xb}, 1'b1)",
                 "fmul": f"{p}_mul({xa}, {xb})", "fdiv": f"{p}_div({xa}, {xb})",
                 "fsqrt": f"{p}_sqrt({xa})"}[op]
        t = self.tmp(f"{p}_o{self.oi}t{set_idx}_{self.tag(i)}", FW + w)
        tx = self.tmp(f"{t}_x", e.XT)
        if self.split != "rounder":                   # the rounder reads the x bus instead
            lib = self.lib_inst.get(("fp_adder", self.tag(i))) if op in ("fadd", "fsub") else \
                self.lib_inst.get(("fp_multiplier", self.tag(i))) if op == "fmul" else \
                self.lib_inst.get(("fp_divider", self.tag(i))) if op == "fdiv" else \
                self.library_instance("fp_sqrt", self.tag(i)) if op == "fsqrt" else None
            fop = self.lib_inst.get(("fp_fma_op", self.tag(i)))       # the op code of a fused multiply-add serving the op
            from chialu.targets.rtl.families.fp import FMA_OP_CODES
            if lib is not None and op in ("fadd", "fsub"):
                la, lb, lsub, ly = lib
                sel = f"{fop} = 3'd{FMA_OP_CODES[op]};" if fop else f"{lsub} = 1'b{1 if op == 'fsub' else 0};"
                blk.stmt(f"{la} = {xa}; {lb} = {xb}; {sel} {tx} = {ly};")
            elif lib is not None and op == "fsqrt":
                la, ly = lib
                blk.stmt(f"{la} = {xa}; {tx} = {ly};")
            elif lib is not None:
                la, lb, ly = lib
                blk.stmt(f"{la} = {xa}; {lb} = {xb};"
                         + (f" {fop} = 3'd{FMA_OP_CODES['fmul']};" if fop and op == "fmul" else "") + f" {tx} = {ly};")
            else:
                blk.stmt(f"{tx} = {xexpr};")
        if self.fam == "posit":
            enc = self.library_instance("posit_enc", self.tag(i))
            if enc is not None:
                ex_, ew_, efl, ebits = enc
                blk.stmt(f"{ex_} = {tx}; {ew_} = {self.word(r)}; {t} = {{{efl}, {ebits}}};")
            else:
                blk.stmt(f"{t} = {p}_pack_{self.own_tag}({tx}, rnd, {self.word(r)}, ftz);")
            self.put(set_idx, i, w, f"{t}[{w-1}:0]")
            nan_ops = nan_a + (f" || {nan_b}" if op != "fsqrt" else "")
            fl = f"{t}[{FW+w-1}:{w}] | {flag_if(nan_ops, 'invalid')}"
            if op == "fdiv":
                fl += f" | {flag_if(f'{self.is_zero(xb)} && !{self.is_zero(xa)} && !{nan_a} && !{nan_b}', 'div_zero')}"
                fl += f" | {flag_if(self.is_zero(xb), 'invalid')}"
            if op == "fsqrt":
                neg_fin = f"{self.x_sign(xa)} && {self.special(xa)} != 2'd1 && {xa}[{e.XW}:0] != 0"
                fl += f" | {flag_if(neg_fin, 'invalid')}"
                fl += f" | {flag_if(f'{self.is_inf(xa)} && {self.x_sign(xa)}', 'invalid')}"
            self.put_flags(r, fl, set_idx)
            return
        self.emit_float_arith(op, set_idx, i, r, xa, xb, pa, pb, t, tx, den)

    def emit_fused_op(self, op: str, set_idx: int, src: str, oth: str, i: int, r: int):
        """fmadd, fmsub, fnmsub, fnmadd: (-1)^np * a * b + (-1)^nc * c
        through the lane's fused multiply-add under fma_contract fused, or,
        under the sequential contract, the product through the lane's
        multiplier with fmul's zero-sign rule, rounded to the format by the
        mode's rounding (the product rounder) and read back as an operand
        (the product unpacker, daz applies; a special product crosses as it
        is), then the lane's adder; the product's rounding flags join the
        op's."""
        from chialu.targets.rtl.families.fp import FMA_OP_CODES
        p, e, fmt, blk = self.p, self.eng, self.fmt, self.blk
        w, XT, VW = fmt.width, e.XT, e.VW
        np_, nc_ = A.FUSED_OPS[op]
        xa, xb, xc = self.x(src, i), self.x(oth, i), self.x("c", i)
        pa, pb, pc = self.pat(src, i), self.pat(oth, i), self.pat("c", i)
        den = f"{self.den(src, i)} | {self.den(oth, i)} | {self.den('c', i)}"
        core = _core(fmt)
        signed = core.signed
        sa = f"{pa}[{w-1}]" if signed else "1'b0"
        sbit = f"{pb}[{w-1}]" if signed else "1'b0"
        contract = str(self.spec.get("fma_contract", "fused"))
        t = self.tmp(f"{p}_o{self.oi}t{set_idx}_{self.tag(i)}", FW + w)
        tx = self.tmp(f"{t}_x", XT)
        extra_flags = None
        # the product's zero and sign for the zero-sign rule: the operands' under the fused contract, the rounded
        # and read-back product's under the sequential one
        zp = f"({self.is_zero(xa)} || {self.is_zero(xb)})"
        ps = f"({sa} ^ {sbit} ^ 1'b{np_})"
        if self.split != "rounder":                   # the rounder reads the x bus instead
            fma = self.lib_inst.get(("fp_fma", self.tag(i)))
            if contract == "sequential":
                xan, xcn = self.tmp(f"{t}_an", XT), self.tmp(f"{t}_cn", XT)
                blk.stmt(f"{xan} = {{{xa}[{XT-1}:{XT-2}], {xa}[{XT-3}] ^ 1'b{np_}, {xa}[{XT-4}:0]}};")
                blk.stmt(f"{xcn} = {{{xc}[{XT-1}:{XT-2}], {xc}[{XT-3}] ^ 1'b{nc_}, {xc}[{XT-4}:0]}};")
                praw = self.tmp(f"{t}_p", XT)
                mul = self.lib_inst.get(("fp_multiplier", self.tag(i)))
                if mul is not None:
                    la, lb, ly = mul
                    blk.stmt(f"{la} = {xan}; {lb} = {xb}; {praw} = {ly};")
                else:
                    blk.stmt(f"{praw} = {p}_mul({xan}, {xb});")
                pz = self.tmp(f"{t}_pz", XT)
                blk.stmt(f"{pz} = {{{praw}[{XT-1}:{XT-2}], {self.is_zero(praw)} ? {ps} : {praw}[{XT-3}], {praw}[{XT-4}:0]}};")
                pk = self.tmp(f"{t}_pk", FW + w)
                rd = self.lib_inst.get(("fma_product_rounder", self.tag(i)))
                if rd is not None:
                    rx, rw, rfl, rbits = rd
                    blk.stmt(f"{rx} = {pz}; {rw} = {self.word(r)}; {pk} = {{{rfl}, {rbits}}};")
                else:
                    blk.stmt(f"{pk} = {p}_pack_{self.own_tag}({pz}, rnd, {self.word(r)}, ftz);")
                # the packer may canonicalize an exact zero to +0 (as emit_float_arith restores the sign after it):
                # the product's zero keeps its sign into the read back
                pkb = self.tmp(f"{t}_pkb", w)
                if signed:
                    blk.stmt(f"{pkb} = {self.is_zero(pz)} ? {{{self.x_sign(pz)}, {w-1}'d0}} : {pk}[{w-1}:0];")
                else:
                    blk.stmt(f"{pkb} = {pk}[{w-1}:0];")
                un = self.lib_inst.get(("fma_product_unpacker", self.tag(i)))
                pu = self.tmp(f"{t}_pu", VW + 1)
                if un is not None:
                    ub, uu = un
                    blk.stmt(f"{ub} = {pkb}; {pu} = {uu};")
                else:
                    blk.stmt(f"{pu} = {p}_unpack_s({pkb}, daz);")
                px = self.tmp(f"{t}_px", XT)
                # a NaN or infinite product crosses as it is (a ROUNDED one, from round_fused_in_reduction, goes
                # through the product rounder like any finite one); an unsigned float's negative product is an
                # invalid operation
                neg = "" if signed else f"({self.x_sign(pz)} && !{self.is_zero(pz)}) ? {p}_mkx(2'd1, 1'b0, 0, 0, 1'b0) : "
                blk.stmt(f"{px} = ({self.special(pz)} == 2'd1 || {self.special(pz)} == 2'd2) ? {pz} : {neg}{p}_x({pu}[{VW-1}:0]);")
                add = self.lib_inst.get(("fp_adder", self.tag(i)))
                if add is not None:
                    aa, ab, asub, ay = add
                    blk.stmt(f"{aa} = {px}; {ab} = {xcn};" + (f" {asub} = 1'b0;" if asub else "") + f" {tx} = {ay};")
                else:
                    blk.stmt(f"{tx} = {p}_add({px}, {xcn}, 1'b0);")
                zp, ps = self.is_zero(px), self.x_sign(px)
                # the product's rounding flags, which a NaN operand suppresses (the op reports the operand flags
                # alone) as does a NaN or infinite product (the rounder packs neither)
                extra_flags = (f"((({self.special(pz)} == 2'd0) && !{self.is_nan(xc)}) ? "
                               f"{pk}[{FW+w-1}:{w}] : {NOFLAG})")
            elif fma is not None:
                la, lb, lc, lop, ly = fma
                blk.stmt(f"{la} = {xa}; {lb} = {xb}; {lc} = {xc}; {lop} = 3'd{FMA_OP_CODES[op]}; {tx} = {ly};")
            else:
                bxa, bxb, bxc, bnp, bnc, by = self.lib_inst[("fp_fma_behav", self.tag(i))]
                blk.stmt(f"{bxa} = {xa}; {bxb} = {xb}; {bxc} = {xc}; {bnp} = 1'b{np_}; {bnc} = 1'b{nc_}; "
                         f"{tx} = {by};")
        if extra_flags is not None and self.split == "producer":
            # the producer unit keeps the product's rounding flags: its lane module returns after writing the x
            # bus, and the unit's flag bus, which the seed ORs with the rounder unit's, carries them
            self.put_flags(r, extra_flags, set_idx)
            extra_flags = None
        self.emit_float_arith(op, set_idx, i, r, xa, xb, pa, pb, t, tx, den, xc=xc, pc=pc, prod=(zp, ps),
                              extra_flags=extra_flags)

    def emit_float_arith(self, op, set_idx, i, r, xa, xb, pa, pb, t, tx, den, xc=None, pc=None, prod=None,
                         extra_flags=None):
        """The float result of an arithmetic op: the zero sign rule, the
        invalid-operation result (NaN or the invalid_result pattern), the
        NaN payload rule and the flags. A fused multiply-add op brings its
        third operand (`xc`, `pc`), the zero and sign of its product
        (`prod`) for the zero-sign rule, and the flags of its product
        rounding under the sequential contract (`extra_flags`)."""
        p, e, fmt, blk = self.p, self.eng, self.fmt, self.blk
        core = _core(fmt)
        w = fmt.width
        XT, XW = e.XT, e.XW
        signed = core.signed
        fused = op in A.FUSED_OPS
        sa = f"{pa}[{w-1}]" if signed else "1'b0"
        sbit = f"{pb}[{w-1}]" if signed else "1'b0"
        nan_a = self.is_nan(xa)
        nan_b = self.is_nan(xb) if op != "fsqrt" else "1'b0"
        nan_c = self.is_nan(xc) if fused else "1'b0"
        nan_any = f"{nan_a} || {nan_b}" + (f" || {nan_c}" if fused else "")
        za, zb = self.is_zero(xa), self.is_zero(xb)
        inf_a = self.is_inf(xa)
        tz = self.tmp(f"{t}_z", XT)
        res_nan = self.is_nan(tz)
        # the sign of a zero result
        if fused:
            # IEEE 754 section 6.3 on the sum of the signed product and the addend: the common sign of two zeros
            # (under RDN, -0 when either is), else +0, or -0 under RDN
            zp, ps = prod
            sc = f"{pc}[{w-1}]" if signed else "1'b0"
            cs = f"({sc} ^ 1'b{A.FUSED_OPS[op][1]})"
            zs = (f"(({zp} && {self.is_zero(xc)}) ? ((rnd == 3'd2) ? ({ps} | {cs}) : ({ps} & {cs})) : "
                  f"((rnd == 3'd2) ? 1'b1 : 1'b0))")
        elif op in ("fmul", "fdiv"):
            zs = f"({sa} ^ {sbit})"
        elif op == "fsqrt":
            zs = sa
        else:
            sb_eff = f"({sbit} ^ 1'b{1 if op == 'fsub' else 0})"
            zs = (f"(({za} && {zb}) ? ((rnd == 3'd2) ? ({sa} | {sb_eff}) : ({sa} & {sb_eff})) : "
                  f"((rnd == 3'd2) ? 1'b1 : 1'b0))")
        nan_prop = self.conv.nan_payload == "propagate"
        inv_zero = self.conv.invalid_result == "zero"
        canon = self.nan_pattern(fmt) if core.has_nan else None
        maxb = core._max_finite_bits()
        if isinstance(fmt, X87Format):
            maxb = fmt._from_core(maxb)
        # invalid-operation sign: xor for mul/div (0/0 gives +), else +, sqrt of a negative: 1; a fused op's
        # invalid product (inf * 0) takes the product's sign, its opposite infinities +
        inv_sign = f"({sa} ^ {sbit})" if op in ("fmul", "fdiv") else ("1'b1" if op == "fsqrt" else "1'b0")
        if op == "fdiv":
            inv_sign = f"(({za} && {zb}) ? 1'b0 : ({sa} ^ {sbit}))"
        if fused:
            inv_sign = f"((({inf_a} && {zb}) || ({self.is_inf(xb)} && {za})) ? ({sa} ^ {sbit} ^ 1'b{A.FUSED_OPS[op][0]}) : 1'b0)"
        if self.split == "rounder":
            # the producer structure delivered the unrounded result (sign rule applied)
            blk.stmt(f"{tz} = {self.x_slice(set_idx, i)};")
        else:
            blk.stmt(f"{tz} = {{ {tx}[{XT-1}:{XT-2}], {self.is_zero(tx)} ? {zs} : {tx}[{XT-3}], {tx}[{XT-4}:0] }};")
            if not signed:
                # unsigned float: a negative result is an invalid operation
                blk.stmt(f"if ({self.special(tz)} != 2'd1 && {self.x_sign(tz)} && !{self.is_zero(tz)}) "
                         f"{tz} = {p}_mkx(2'd1, 1'b0, 0, 0, 1'b0);")
            if self.split == "producer":
                self.put_x(set_idx, i, tz)              # the rounder packs it
                return
        rd = self.library_instance("rounder", self.tag(i), op) or self.library_instance("rounder", self.tag(i), None)
        if rd is not None:
            rx, rw, rfl, rbits = rd
            blk.stmt(f"{rx} = {tz}; {rw} = {self.word(r)}; {t} = {{{rfl}, {rbits}}};")
        else:
            blk.stmt(f"{t} = {p}_pack_{self.own_tag}({tz}, rnd, {self.word(r)}, ftz);")
        out_bits = core_to_x87(t) if isinstance(fmt, X87Format) else f"{t}[{w-1}:0]"
        if signed and not core.exp_only:
            # The arithmetic producer supplies the IEEE zero sign. The generic
            # value packer may canonicalize an exact zero to positive zero.
            out_bits = f"({self.is_zero(tz)} ? {{{self.x_sign(tz)}, {w-1}'d0}} : {out_bits})"
        pw = core.width                       # the pack's pattern width (79 for fp80)
        if core.has_nan:
            nan_out = f"({nan_a} ? {pa} : {pb})" if nan_prop else canon
            if fused:
                nan_out = f"({nan_a} ? {pa} : {nan_b} ? {pb} : {pc})" if nan_prop else canon     # the order a, b, c
            if op == "fsqrt":
                nan_out = pa if nan_prop else canon
            # an invalid operation (not a NaN operand) always gives the canonical NaN
            self.put(set_idx, i, w, f"{res_nan} ? (({nan_any}) ? {nan_out} : {canon}) : {out_bits}")
        else:
            inv_out = f"{w}'d0" if inv_zero else (
                f"({{{inv_sign}, {w-1}'d{maxb & _mask(w-1)}}})" if signed else f"{w}'d{maxb}")
            self.put(set_idx, i, w, f"{res_nan} ? {inv_out} : {out_bits}")
        # flags
        fl = f"{t}[{FW+pw-1}:{pw}]"
        if extra_flags:
            fl += f" | {extra_flags}"
        # IEEE 754: invalid for a signalling NaN operand or an invalid operation; a quiet NaN propagates
        snan_a = self.is_snan(xa, pa)
        snan_b = self.is_snan(xb, pb) if op != "fsqrt" else "1'b0"
        snan_any = f"{snan_a} || {snan_b}" + (f" || {self.is_snan(xc, pc)}" if fused else "")
        inv = f"({snan_any} || ({res_nan} && !({nan_any})))"
        fl += f" | {flag_if(inv, 'invalid')}"
        if not core.has_nan:
            fl += f" | {flag_if(res_nan, 'inexact')}"
            fl = f"(({fl}) & ~{flag('nan')})"
        if op == "fdiv":
            fl += f" | {flag_if(f'{zb} && !{za} && !{inf_a}', 'div_zero')}"
        fl += f" | {flag_if(den, 'denormal')}"
        # a NaN operand: only the operand flags (nan, invalid for a signalling one, denormal); a
        # format without NaN reports invalid and inexact
        operand_flags = (f"{flag('nan')} | {flag_if(snan_any, 'invalid')}" if core.has_nan
                         else f"{flag('invalid')} | {flag('inexact')}")
        fl = f"(({nan_any}) ? (({operand_flags}) | {flag_if(den, 'denormal')}) : ({fl}))"
        self.put_flags(r, fl, set_idx)

    def _cmp_exprs(self, i, xa: str, xb: str) -> tuple:
        """(a < b, a == b, b < a) through the lane's library comparator when
        one exists (the lane module drives it in the op's arm), else the
        engine's functions."""
        lib = self.lib_inst.get(("fp_comparator", self.tag(i)))
        p = self.p
        if lib is None:
            return f"{p}_lt({xa}, {xb})", f"{p}_eq({xa}, {xb})", f"{p}_lt({xb}, {xa})"
        ca, cb, lt, eq = lib
        self.blk.stmt(f"{ca} = {xa}; {cb} = {xb};")
        return lt, eq, f"(!{lt} && !{eq})"

    # ---- conversions -------------------------------------------------------------
    def emit_cvt(self, op: str, tgt, set_idx: int, src: str, base: int):
        """cvt(<target>) from a float, posit or block mode."""
        p, e, fmt, count = self.p, self.eng, self.fmt, self.count
        size = fmt.size if self.fam == "block" else 1
        if isinstance(tgt, BlockFormat):
            self.cvt_to_block(op, tgt, set_idx, src, base, count * size,
                              den_of=lambda k: self.den(src, k))
            return
        ttag = fmt_tag(tgt)
        tw = tgt.width
        tc = _core(tgt)
        pw = tc.width
        XW = e.XW
        for i, j in [(i, j) for i in self.lanes for j in range(size)]:
            k = self.elem(i, j, size)
            xa = self.x(src, k)
            if self.split == "producer":
                self.put_x(set_idx, k, xa)              # the rounder packs into the target
                continue
            if self.split == "rounder":
                # the converter structure forwarded the unpacked source on the x
                # bus; a temporary, since the code below indexes into the value
                xa = self.tmp(f"{p}_o{self.oi}x{set_idx}_{self.tag(i)}_{j}", e.XT)
                self.blk.stmt(f"{xa} = {self.x_slice(set_idx, k)};")
            t = self.tmp(f"{p}_o{self.oi}c{set_idx}_{self.tag(i)}_{j}", FW + tw)
            r = base + k
            nan_a = self.is_nan(xa)
            den = self.den(src, k)
            cv = self.library_instance("converter", self.tag(k), tgt.name)
            if cv is not None:
                cx, cw, cfl, cbits = cv
                self.blk.stmt(f"{cx} = {xa}; {cw} = {self.word(r)}; {t} = {{{cfl}, {cbits}}};")
            else:
                self.blk.stmt(f"{t} = {p}_pack_{ttag}({xa}, rnd, {self.word(r)}, ftz);")
            out_bits = core_to_x87(t) if isinstance(tgt, X87Format) else f"{t}[{tw-1}:0]"
            if isinstance(tc, FloatFormat) and tc.signed and not tc.exp_only and self.fam in ("float", "block"):
                out_bits = f"({self.is_zero(xa)} ? {{{self.x_sign(xa)}, {tw-1}'d0}} : {out_bits})"
            fl = f"{t}[{FW+pw-1}:{pw}]"
            if isinstance(tgt, (FloatFormat, X87Format)):
                nan_prop = self.conv.nan_payload == "propagate"
                if tc.has_nan:
                    same_layout = (nan_prop and self.fam == "float" and tgt.width == fmt.width
                                   and isinstance(fmt, FloatFormat) and fmt.exp_bits == tc.exp_bits
                                   and fmt.man_bits == tc.man_bits)
                    if same_layout:
                        self.put(set_idx, k, tw, f"{nan_a} ? {self.pat(src, k)} : {out_bits}")
                    else:
                        self.put(set_idx, k, tw, out_bits)
                    # a signalling NaN source is invalid; a quiet one converts to the target's NaN in silence;
                    # a posit NaR into a float is invalid
                    snan_src = nan_a if self.fam == "posit" else self.is_snan(xa, self.pat(src, i), fmt, j * fmt.elem.width if self.fam == "block" else 0)
                    fl += f" | {flag_if(snan_src, 'invalid')}"
                else:
                    inv_zero = self.conv.invalid_result == "zero"
                    maxb = tc._max_finite_bits()
                    # the sign of the saturated invalid result is the source
                    # PATTERN's sign bit (a NaN keeps its sign bit; the
                    # unpacked X of a NaN carries none); a posit NaR counts
                    # as positive, as in the reference
                    neg = self.pattern_sign(src, i, j)
                    inv_out = f"{tw}'d0" if inv_zero else (
                        f"{{{neg}, {tw-1}'d{maxb & _mask(tw-1)}}}" if tc.signed else f"{tw}'d{maxb}")
                    res_nan = f"({t}[{FW+pw-1}:{pw}] & {flag('nan')}) != 0"
                    self.put(set_idx, k, tw, f"({res_nan}) ? {inv_out} : {out_bits}")
                    fl = f"(({res_nan}) ? ({flag('invalid')} | {flag('inexact')}) : ({fl}))"
                if not tc.signed:
                    # a negative finite value into an unsigned float is invalid
                    neg_fin = f"({self.special(xa)} != 2'd1 && {self.x_sign(xa)} && {xa}[{XW}:0] != 0)"
                    neg_inf = f"{self.is_inf(xa)} && {self.x_sign(xa)}"
                    if tc.has_nan:
                        self.blk.stmt(f"{self.guard(set_idx)}if ({neg_fin} || {neg_inf}) "
                                      f"{self.lhs(set_idx, k, tw)} = {self.nan_pattern(tgt)};")
                    fl = f"(({neg_fin} || ({neg_inf})) ? ({flag('invalid')} | {flag('nan')}) : ({fl}))"
            elif isinstance(tgt, PositFormat):
                self.put(set_idx, k, tw, out_bits)
                not_finite = f"{self.special(xa)} != 2'd0"
                fl += f" | {flag_if(not_finite, 'invalid')}"
            else:
                self.put(set_idx, k, tw, out_bits)
            fl += f" | {flag_if(den, 'denormal')}"
            self.put_flags(r, fl, set_idx)
