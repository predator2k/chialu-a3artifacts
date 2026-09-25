"""Integer, fixed-point and BCD modes of the ALU seed: the pattern ops as
language operators on a signed exact value (two's complement and
unsigned patterns directly, a value decode for ones' complement,
sign-magnitude and BCD), wrap/saturate encoders of the mode's format,
rounding of fixed-point products and quotients, and conversions through
the engine."""
from __future__ import annotations

from chialu.targets.rtl.alu_mode import (NOFLAG, ModeEmitter, core_to_x87,
                                          flag, flag_if)
from chialu.targets.rtl.engine import FW, fmt_tag, _core
from chialu.targets.rtl.writer import ones
from chialu.verify import alu_ref as A
from chialu.verify.formats import BCDFormat, BlockFormat, FloatFormat, IntFormat, X87Format


ADDER_OPS = ("add", "sub", "adc", "sbb", "neg", "abs", "add_sat", "sub_sat")
MUL_OPS = ("mul", "mul_wide", "mul_high", "mul_sat")
DIV_OPS = ("div", "quot", "rem", "mod")
SHIFT_OPS = {"shl": 0, "shr_logical": 1, "shr_arith": 2, "rol": 3, "ror": 4}   # the library's op codes
LIBRARY_ENCODINGS = ("twos_complement", "unsigned")   # the encodings whose add/compare the library's binary adder serves


class IntModeEmitter(ModeEmitter):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        fmt = self.fmt
        self.w = fmt.width
        self.F = getattr(fmt, "frac_bits", 0)
        self.enc = fmt.encoding
        self.EWI = 2 * self.w + 3            # the exact value's width
        self.pint = A._pattern_int(fmt)
        self.bcd = isinstance(fmt, BCDFormat)
        self.value_encoded = self.enc in ("ones_complement", "sign_magnitude")
        self.lib_inst: dict = {}             # (kind or op, lane tag) -> the wires of a library instance

    # ---- literals of the exact width ---------------------------------------------
    def sd(self, v: int) -> str:
        """A signed literal of the exact width (a negative v is written as
        a negated magnitude, as the reference encodes it)."""
        return f"-{self.EWI}'sd{-v}" if v < 0 else f"{self.EWI}'sd{v}"

    def min_lit(self) -> str:
        mn = self.pint.min_int
        return self.sd(mn) if mn < 0 else "0"

    def zero_pat(self, sign_expr: str, width: int | None = None) -> str:
        """The signed zero pattern of ones' complement / sign-magnitude
        under zero_sign: preserve, for the given sign."""
        w = width or self.w
        if self.enc == "ones_complement":
            return f"({sign_expr} ? {ones(w)} : {w}'d0)"
        return f"({sign_expr} ? {{1'b1, {{{w-1}{{1'b0}}}}}} : {w}'d0)"

    # ---- operand decode ---------------------------------------------------------
    def declare_values(self):
        mod, p, e, fmt, w, count = self.mod, self.p, self.eng, self.fmt, self.w, self.count
        XT = e.XT
        for src in ("a", "b"):
            mod.logic(f"{p}_x{src}", XT, dims=f" [0:{count-1}]")
        for i in self.lanes:
            for src in ("a", "b"):
                mod.assign(self.x(src, i), f"{p}_x({p}_unpack_s({self.pat(src, i)}, 1'b0))")
        VWI = w + 1
        for i in self.lanes:
            for src in ("a", "b"):
                pa = self.pat(src, i)
                v = mod.logic(f"{p}_v{src}{self.tag(i)}", VWI, signed=True)
                if self.enc == "unsigned":
                    mod.assign(v, f"{{1'b0, {pa}}}")
                elif self.enc == "twos_complement":
                    mod.assign(v, f"{{{pa}[{w-1}], {pa}}}")
                elif self.enc == "ones_complement":
                    mod.assign(v, f"{pa}[{w-1}] ? -$signed({{1'b0, ~{pa}}}) : $signed({{1'b0, {pa}}})")
                elif self.enc == "sign_magnitude":
                    mod.assign(v, f"{pa}[{w-1}] ? -$signed({{2'b0, {pa}[{w-2}:0]}}) : $signed({{1'b0, {pa}}})")
                else:                                        # BCD digits
                    b = mod.logic(f"{p}_bin{src}{self.tag(i)}", w)
                    mod.raw(f"  always_comb begin {b} = 0; for (int k = {fmt.digits-1}; k >= 0; k = k - 1) "
                            f"{b} = {b} * 10 + {pa}[4*k +: 4]; end")
                    mod.assign(v, f"{{1'b0, {b}}}")
        self.helpers()
        self.declare_library()

    # ---- the family library ---------------------------------------------------------
    def xs(self, kind: str) -> bool:
        """Whether the unit shares this kind's library instance across modes
        (alu_seed: a group of one integer kind over two modes or more): the
        lane module then drives the operands onto the unit's xs_ buses and
        reads the result back instead of instantiating the module itself."""
        return f"xs_{kind}" in self.shared

    def xs_lane(self, kind: str, t: str, outs: dict, ins: dict) -> dict:
        """The lane's side of a unit-level shared instance: each operand
        (`outs`: {signal: (expression, width)}) on its slice of the mode's
        xs_<kind>_<signal> bus, the other lanes' slices 0 (the unit ORs its
        lane modules' buses), and each result (`ins`: {signal: width}) a
        wire off its slice of the bus the unit returns. {signal: wire}."""
        mod, bus = self.mod, self.bus
        if len(self.lanes) != 1:
            raise ValueError(f"core.{kind}.m{self.mi}: a {kind} shared across modes is realized in a lane module")
        i = self.lanes[0]
        for name, (expr, width) in outs.items():
            n = self.count * width
            if n == 1:
                mod.assign(f"xs_{kind}_{name}_{bus}", expr)
                continue
            padded = f"{{{{{n - width}{{1'b0}}}}, {expr}}}" if n > width else expr
            mod.assign(f"xs_{kind}_{name}_{bus}", f"{padded} << (({i})*{width})" if n > width else padded)
        out = {}
        for name, width in ins.items():
            wire = mod.logic(f"{self.p}_xs_{kind}_{name}{t}", width)
            mod.assign(wire, f"xs_{kind}_{name}_{bus}" if self.count * width == 1 else
                       f"xs_{kind}_{name}_{bus}[({i})*{width} +: {width}]")
            out[name] = wire
        return out

    def declare_library(self):
        """One library instance per lane for every structure kind of the
        module whose declared family the library realizes: the adder
        (two's complement and unsigned patterns; the add-class ops set
        its operands and carry-in per op and read the exact result and
        the flags off its sum and carry), the comparator (a comparator
        module, or the adder as a subtractor when the family is an
        adder's, shared with the add ops when the module has them), the
        shifter, and one counter per bit-count op."""
        from chialu.targets.rtl import families as FAM
        mod, p, w, mi = self.mod, self.p, self.w, self.mi
        ops = {op for _o, op in self.ops}
        binary = self.enc in LIBRARY_ENCODINGS and not self.bcd
        arithmetic = binary or self.value_encoded
        # a unary op of a dual unit writes two result sets in one op arm (from a, and from
        # b), so the kinds with unary ops get one instance per set and lane
        nsets = max((len(self.result_sets(op)) for _o, op in self.ops), default=1)
        lane_sets = [(i, self.tag(i) + (f"_s{si}" if si else ""), si) for i in self.lanes for si in range(nsets)]

        def inst(name, params, port_conns, comment):
            ps = ", ".join(f".{k}({v})" for k, v in params.items())
            mod.raw(f"  // {comment}")
            mod.raw(f"  {name} " + (f"#({ps}) " if ps else "") + port_conns)

        adder = self.family_for("adder") if ops & set(ADDER_OPS) else None
        pg_fused = (self.family_for("logic") or ("", {}))[0] == "alu_pg_fused" and bool(ops & {"and", "or", "xor", "not"})
        if pg_fused and (not arithmetic or (adder and adder[0] == "end_around_carry")):
            raise ValueError("alu_pg_fused requires a binary carry-propagate adder in its lane module")
        if pg_fused and adder is None:
            adder = ("ripple_carry", {})
        core_mods = self.core_modules(w, binary, adder)     # a redundant_internal / rns_internal core's lane modules
        if adder and self.enc == "ones_complement" and adder[0] == "end_around_carry":
            # the ones'-complement add class on the end-around-carry adder: its sum is the pattern the
            # `_eac` reference gives (the double-zero convention), the exact value stays behavioral for the flags
            from chialu.targets.rtl.families.selection import SelectionError, copy_pins
            asked = (adder[1] or {}).get("modulus", "mod_2n_minus_1")
            if asked != "mod_2n_minus_1":
                # the ones'-complement word is its own modulus, 2^n - 1; another modulus is a request the
                # lane cannot realize, refused rather than overwritten
                raise SelectionError(f"core.adder: end_around_carry modulus {asked!r} under a ones'-complement "
                                     "format, whose add is modulo 2^n - 1 (modulus 'mod_2n_minus_1')")
            eac_mod = FAM.adder_module("end_around_carry", copy_pins(adder[1], modulus="mod_2n_minus_1"), w)
            if eac_mod:
                name = self.library_module(eac_mod)
                for i, t, si in lane_sets:
                    a, b, cin = self.tmp(f"{p}_eac_a{t}", w), self.tmp(f"{p}_eac_b{t}", w), self.tmp(f"{p}_eac_cin{t}", 1)
                    s_, cout = mod.logic(f"{p}_eac_s{t}", w), mod.logic(f"{p}_eac_cout{t}", 1)
                    inst(name, eac_mod.params, f"u_{p}_eac{t} (.a({a}), .b({b}), .cin({cin}), .s({s_}), .cout({cout}));",
                         f"structure core.adder.m{mi}: family end_around_carry realized by the library module {name}"
                         + (f" (result set {si})" if si else ""))
                    self.lib_inst[("eac", self.tag(i), si)] = (a, b, cin, s_, cout)
        cmp_fam = self.family_for("comparator") if ops & {"min", "max", "cmp"} else None
        # An RNS core supplies its own comparator even when the ordinary
        # binary-comparator slot is absent from this architecture.
        cmp_mod = core_mods.get("comparator") if ops & {"min", "max", "cmp"} else None
        cmp_owner = core_mods.get("comparator_owner") if cmp_mod else f"family {cmp_fam[0]}" if cmp_fam else ""
        if cmp_mod is None:
            # a BCD lane's comparator is the binary one on the patterns (packed BCD orders as unsigned binary)
            cmp_mod = FAM.comparator_module(cmp_fam[0], cmp_fam[1], w, self.enc != "unsigned" and not self.bcd) \
                if cmp_fam and (arithmetic or self.bcd) else None
        # the adder: its own family, or the comparator's adder family as a subtractor (the end-around-carry
        # adder serves the ones'-complement add class above and is no plain adder)
        adder_mod = core_mods.get("adder") if adder or (core_mods.get("owns_adder") and ops & set(ADDER_OPS)) else None
        adder_owner = f"core.adder.m{mi}: {core_mods.get('adder_owner')}" if adder_mod else ""
        if adder_mod is None:
            # a BCD lane's adder is the decimal library's (declare_bcd_library): the binary factory is not probed with a decimal family
            adder_mod = FAM.adder_module(adder[0], adder[1], w) if adder and arithmetic and not self.bcd and adder[0] != "end_around_carry" else None
            adder_owner = f"core.adder.m{mi}: family {adder[0]}" if adder_mod else ""
        if adder_mod is None and cmp_fam and cmp_mod is None and arithmetic and not self.bcd:
            adder_mod = FAM.adder_module(cmp_fam[0], cmp_fam[1], w)
            adder_owner = f"core.comparator.m{mi}: family {cmp_fam[0]} (a subtractor)"
        if "raw_pg" in self.shared and binary:
            for i, _t, si in lane_sets:
                index = f"(({i})+{si*self.count})"
                a, b = (f"pg_{arg}_{self.bus}[{index}*{w} +: {w}]" for arg in ("a", "b"))
                cin = f"pg_cin_{self.bus}[{index}]"
                result = mod.logic(f"{p}_rawpg_s{_t}", w)
                carry = mod.logic(f"{p}_rawpg_c{_t}")
                mod.assign(result, f"pg_sum_{self.bus}[{index}*{w} +: {w}]")
                mod.assign(carry, f"pg_cout_{self.bus}[{index}]")
                self.lib_inst[("adder", self.tag(i), si)] = (a, b, cin, result, carry)
                if pg_fused:
                    self.lib_inst[("pg_logic", self.tag(i), si)] = (a, b, cin,
                        f"pg_p_{self.bus}[{index}*{w} +: {w}]", f"pg_g_{self.bus}[{index}*{w} +: {w}]")
            lane_sets_adder = []
            adder_mod = None
        elif "adder" in self.shared and binary:
            # the unit's lane-partitioned adder (subword partitioned_carry_chain): this lane's slices of its
            # operand, carry-in, sum and carry-out buses stand for the lane's adder (result set 0)
            lpf = max(1, w // int(self.shared["adder"].get("fine", w)))
            mod.raw(f"  // structure core.adder.m{mi}: the unit's shared partitioned adder (subword partitioned_carry_chain)")
            for i in self.lanes:
                t = self.tag(i)
                s_l, co_l = mod.logic(f"{p}_add_s{t}", w), mod.logic(f"{p}_add_cout{t}", 1)
                mod.assign(s_l, f"pc_s_{self.bus}[({i})*{w} +: {w}]")
                mod.assign(co_l, f"pc_co_{self.bus}[({i}+1)*{lpf}-1]")
                self.lib_inst[("adder", t, 0)] = (f"pc_a_{self.bus}[({i})*{w} +: {w}]", f"pc_b_{self.bus}[({i})*{w} +: {w}]",
                                                   f"pc_cin_{self.bus}[({i})*{lpf}]", s_l, co_l)
                if pg_fused:
                    from chialu.targets.rtl.families.alu_pg import terms_module
                    terms = terms_module(w, f"core.logic.m{mi}")
                    name = self.library_module(terms)
                    a, b = self.tmp(f"{p}_pg_a{t}", w), self.tmp(f"{p}_pg_b{t}", w)
                    propagate, generate = mod.logic(f"{p}_pg_p{t}", w), mod.logic(f"{p}_pg_g{t}", w)
                    inst(name, {}, f"u_{p}_pg{t} (.a({a}), .b({b}), .p({propagate}), .g({generate}));",
                         "PG terms shared by logic and the lane-partitioned adder")
                    pa, pb, cin, result, carry = self.lib_inst[("adder", t, 0)]
                    # The shift is lane-local: its discarded high generate bit
                    # contributes to this lane's carry, never its neighbour's sum.
                    if not hasattr(self, "pg_partition_terms"):
                        self.pg_partition_terms = []
                    self.pg_partition_terms.append((pa, pb, propagate, generate))
                    co = mod.logic(f"{p}_pg_cout{t}")
                    mod.assign(co, f"{carry} | {generate}[{w-1}]")
                    self.lib_inst[("adder", t, 0)] = (a, b, cin, result, co)
                    self.lib_inst[("pg_logic", t, 0)] = (a, b, cin, propagate, generate)
            lane_sets_adder = [(i, t, si) for i, t, si in lane_sets if si > 0]
        elif self.xs("adder") and binary:
            # the unit's adder shared across modes (one library instance per lane position at the widest served
            # width, its operands muxed by the mode): this lane's operands out, its sum and carry-out back
            if pg_fused or adder_mod is None or core_mods.get("adder") is not None:
                raise ValueError(f"core.adder.m{mi}: an adder shared across modes needs a library adder family "
                                 "of its own (no alu_pg_fused row, no representation core)")
            for i in self.lanes:
                t = self.tag(i)
                a, b, cin = self.tmp(f"{p}_add_a{t}", w), self.tmp(f"{p}_add_b{t}", w), self.tmp(f"{p}_add_cin{t}", 1)
                got = self.xs_lane("adder", t, {"a": (a, w), "b": (b, w), "cin": (cin, 1)}, {"s": w, "co": 1})
                mod.raw(f"  // structure {adder_owner}: the unit's adder shared across modes")
                self.lib_inst[("adder", t, 0)] = (a, b, cin, got["s"], got["co"])
            lane_sets_adder = [(i, t, si) for i, t, si in lane_sets if si > 0]
        else:
            lane_sets_adder = lane_sets
        if adder_mod and (lane_sets_adder or not pg_fused):
            if pg_fused:
                from chialu.targets.rtl.families.alu_pg import fused_module
                adder_mod = fused_module(adder_mod, w, f"core.logic.m{mi}")
            name = self.library_module(adder_mod)
            for i, t, si in lane_sets_adder:
                a, b, cin = self.tmp(f"{p}_add_a{t}", w), self.tmp(f"{p}_add_b{t}", w), self.tmp(f"{p}_add_cin{t}", 1)
                s, cout = mod.logic(f"{p}_add_s{t}", w), mod.logic(f"{p}_add_cout{t}", 1)
                pg_connections = ""
                if pg_fused:
                    propagate = mod.logic(f"{p}_pg_p{t}", w)
                    generate = mod.logic(f"{p}_pg_g{t}", w)
                    pg_connections = f", .pg_p({propagate}), .pg_g({generate})"
                    self.lib_inst[("pg_logic", self.tag(i), si)] = (a, b, cin, propagate, generate)
                inst(name, adder_mod.params,
                     f"u_{p}_adder{t} (.a({a}), .b({b}), .cin({cin}), .s({s}), .cout({cout})"
                     f"{self.ctrl_conns(adder_mod)}{pg_connections});",
                     f"structure {adder_owner} realized by the library module {name}" + (f" (result set {si})" if si else ""))
                self.lib_inst[("adder", self.tag(i), si)] = (a, b, cin, s, cout)
        if self.xs("comparator"):
            if cmp_mod is None or core_mods.get("comparator") is not None or not binary:
                raise ValueError(f"core.comparator.m{mi}: a comparator shared across modes needs a library comparator "
                                 "family on a binary integer format")
            for i in self.lanes:
                t = self.tag(i)
                a, b = self.tmp(f"{p}_cmp_a{t}", w), self.tmp(f"{p}_cmp_b{t}", w)
                got = self.xs_lane("comparator", t, {"a": (a, w), "b": (b, w)}, {"lt": 1, "eq": 1})
                mod.raw(f"  // structure core.comparator.m{mi}: the unit's comparator shared across modes")
                self.lib_inst[("comparator", t, 0)] = (a, b, got["lt"], got["eq"])
            cmp_mod = None
        if cmp_mod and pg_fused and binary and adder:
            # A triple group consumes the same subtractor as the add and PG
            # operations. Refuse conflicting physical choices on direct API
            # calls; plans normalize the declaration to this common CPA.
            pins = cmp_fam[1]
            subpins = {k[len("subtractor."):]: v for k, v in pins.items()
                       if k.startswith("subtractor.") and k != "subtractor.family"}
            if cmp_fam[0] != "subtractor_comparator" or pins.get("subtractor.family", "ripple_carry") != adder[0] \
                    or any(adder[1].get(k) != v for k, v in subpins.items()):
                raise ValueError(f"core.comparator.m{mi}: PG sharing requires subtractor_comparator with "
                                 f"subtractor.family={adder[0]} and the lane adder's pins")
            from chialu.targets.rtl.families.selection import register_origin
            from chialu.targets.rtl.families.fidelity import shared
            owner = f"core.comparator.m{mi}"
            register_origin(owner, cmp_fam[0], pins, mod.name)
            shared(owner, "comparator_via_pg_adder", [mod.name], [owner, f"core.adder.m{mi}"],
                   "Comparison drives a + ~b + 1 through the lane's PG/CPA and reads carry and equality.",
                   origin_modules=[cmp_mod.name])
            self.cmp_zero_detect = pins.get("zero_detect", "sum_or_tree")
            cmp_mod = None
        if cmp_mod:
            name = self.library_module(cmp_mod)
            for i in self.lanes:
                t = self.tag(i)
                a, b = self.tmp(f"{p}_cmp_a{t}", w), self.tmp(f"{p}_cmp_b{t}", w)
                lt, eq = mod.logic(f"{p}_cmp_lt{t}", 1), mod.logic(f"{p}_cmp_eq{t}", 1)
                inst(name, cmp_mod.params, f"u_{p}_cmp{t} (.a({a}), .b({b}), .lt({lt}), .eq({eq}));",
                     f"structure core.comparator.m{mi}: {cmp_owner} realized by the library module {name}"
                     + (" (packed BCD compares as unsigned binary)" if self.bcd else ""))
                self.lib_inst[("comparator", t, 0)] = (a, b, lt, eq)
        if self.bcd:
            self.declare_bcd_library(ops, lane_sets, inst)
        mult = self.family_for("multiplier") if ops & set(MUL_OPS) else None
        # A representation/RNS core owns its multiplier independently of the
        # ordinary core.multiplier slot (which is inactive for an RNS core).
        mul_mod = core_mods.get("multiplier") if ops & set(MUL_OPS) else None
        mul_owner = core_mods.get("multiplier_owner") if mul_mod else f"family {mult[0]}" if mult else ""
        if mul_mod is None:
            mul_mod = FAM.mul_module(mult[0], mult[1], w, self.enc != "unsigned") if mult and arithmetic and not self.bcd else None
        if "multiplier" in self.shared and binary:
            # the unit's twin-precision multiplier: this lane's product slice of its packed bus
            mod.raw(f"  // structure core.multiplier.m{mi}: family twin_precision_subword realized by the unit's shared "
                    f"twin-precision multiplier {self.shared['multiplier'].get('module', '')}")
            for i in self.lanes:
                t = self.tag(i)
                a, b = self.tmp(f"{p}_mul_a{t}", w), self.tmp(f"{p}_mul_b{t}", w)
                prod = mod.logic(f"{p}_mul_p{t}", 2 * w)
                mod.assign(prod, f"tp_p_{self.bus}[({i})*{2*w} +: {2*w}]")
                self.lib_inst[("multiplier", t, 0)] = (a, b, prod)
            mul_mod = None
        if self.xs("multiplier"):
            if mul_mod is None or core_mods.get("multiplier") is not None or not binary:
                raise ValueError(f"core.multiplier.m{mi}: a multiplier shared across modes needs a library multiplier "
                                 "family on a binary integer format")
            for i in self.lanes:
                t = self.tag(i)
                a, b = self.tmp(f"{p}_mul_a{t}", w), self.tmp(f"{p}_mul_b{t}", w)
                got = self.xs_lane("multiplier", t, {"a": (a, w), "b": (b, w)}, {"p": 2 * w})
                mod.raw(f"  // structure core.multiplier.m{mi}: the unit's multiplier shared across modes")
                self.lib_inst[("multiplier", t, 0)] = (a, b, got["p"])
            mul_mod = None
        if mul_mod:
            name = self.library_module(mul_mod)
            for i in self.lanes:
                t = self.tag(i)
                a, b = self.tmp(f"{p}_mul_a{t}", w), self.tmp(f"{p}_mul_b{t}", w)
                prod = mod.logic(f"{p}_mul_p{t}", 2 * w)
                inst(name, mul_mod.params,
                     f"u_{p}_mul{t} (.a({a}), .b({b}), .p({prod}){self.ctrl_conns(mul_mod)});",
                     f"structure core.multiplier.m{mi}: {mul_owner} realized by the library module {name}")
                self.lib_inst[("multiplier", t, 0)] = (a, b, prod)
        divf = self.family_for("divider") if ops & set(DIV_OPS) else None
        F = self.F
        # a fixed-point mode's quotient divides the dividend shifted by the fraction bits, its remainder the
        # dividend itself: one divider over the widened dividend, the op sets the shift
        div_mod = FAM.div_module(divf[0], divf[1], w + F, w, w + F) if divf and arithmetic and not self.bcd else None
        if div_mod:
            name = self.library_module(div_mod)
            for i in self.lanes:
                t = self.tag(i)
                a, b = self.tmp(f"{p}_div_a{t}", w + F), self.tmp(f"{p}_div_b{t}", w)
                q, r = mod.logic(f"{p}_div_q{t}", w + F), mod.logic(f"{p}_div_r{t}", w)
                inst(name, div_mod.params,
                     f"u_{p}_div{t} (.a({a}), .b({b}), .q({q}), .r({r}){self.ctrl_conns(div_mod)});",
                     f"structure core.divider.m{mi}: family {divf[0]} realized by the library module {name}"
                     + (f" (the dividend widened by the {F} fraction bits)" if F else ""))
                self.lib_inst[("divider", t, 0)] = (a, b, q, r)
        shifter = self.family_for("shifter") if ops & set(SHIFT_OPS) else None
        sh_mod = FAM.shifter_module(shifter[0], shifter[1], w) if shifter and w >= 2 else None
        if self.xs("shifter"):
            if sh_mod is None:
                raise ValueError(f"core.shifter.m{mi}: a shifter shared across modes needs a library shifter family")
            aw = max(1, (w - 1).bit_length())
            for i in self.lanes:
                t = self.tag(i)
                a, amt, opc = self.tmp(f"{p}_sh_a{t}", w), self.tmp(f"{p}_sh_amt{t}", aw), self.tmp(f"{p}_sh_op{t}", 3)
                got = self.xs_lane("shifter", t, {"a": (a, w), "amt": (amt, aw), "op": (opc, 3)}, {"y": w})
                mod.raw(f"  // structure core.shifter.m{mi}: the unit's shifter shared across modes")
                self.lib_inst[("shifter", t, 0)] = (a, amt, opc, got["y"])
            sh_mod = None
        if sh_mod:
            name = self.library_module(sh_mod)
            aw = max(1, (w - 1).bit_length())
            for i in self.lanes:
                t = self.tag(i)
                a, amt, opc = self.tmp(f"{p}_sh_a{t}", w), self.tmp(f"{p}_sh_amt{t}", aw), self.tmp(f"{p}_sh_op{t}", 3)
                y = mod.logic(f"{p}_sh_y{t}", w)
                inst(name, sh_mod.params, f"u_{p}_shifter{t} (.a({a}), .amt({amt}), .op({opc}), .y({y}), .sticky());",
                     f"structure core.shifter.m{mi}: family {shifter[0]} realized by the library module {name}")
                self.lib_inst[("shifter", t, 0)] = (a, amt, opc, y)
        logic_fam = self.family_for("logic") if ops & {"and", "or", "xor", "not"} else None
        logic_mod = FAM.logic_module(logic_fam[0], logic_fam[1], w) if logic_fam and not pg_fused else None
        if self.xs("logic"):
            if logic_mod is None:
                raise ValueError(f"core.logic.m{mi}: a gate row shared across modes needs a library logic family")
            for i, t, si in lane_sets:
                a, b, opc = self.tmp(f"{p}_lg_a{t}", w), self.tmp(f"{p}_lg_b{t}", w), self.tmp(f"{p}_lg_op{t}", 2)
                if si:
                    # a dual unit's second result set keeps a row of its own in the lane
                    y = mod.logic(f"{p}_lg_y{t}", w)
                    name = self.library_module(logic_mod)
                    inst(name, logic_mod.params, f"u_{p}_logic{t} (.a({a}), .b({b}), .op({opc}), .y({y}));",
                         f"structure core.logic.m{mi}: family {logic_fam[0]} realized by the library module {name} (result set {si})")
                else:
                    y = self.xs_lane("logic", t, {"a": (a, w), "b": (b, w), "op": (opc, 2)}, {"y": w})["y"]
                    mod.raw(f"  // structure core.logic.m{mi}: the unit's gate row shared across modes")
                self.lib_inst[("logic", self.tag(i), si)] = (a, b, opc, y)
            logic_mod = None
        if logic_mod:
            name = self.library_module(logic_mod)
            for i, t, si in lane_sets:
                a, b, opc = self.tmp(f"{p}_lg_a{t}", w), self.tmp(f"{p}_lg_b{t}", w), self.tmp(f"{p}_lg_op{t}", 2)
                y = mod.logic(f"{p}_lg_y{t}", w)
                inst(name, logic_mod.params, f"u_{p}_logic{t} (.a({a}), .b({b}), .op({opc}), .y({y}));",
                     f"structure core.logic.m{mi}: family {logic_fam[0]} realized by the library module {name}"
                     + (f" (result set {si})" if si else ""))
                self.lib_inst[("logic", self.tag(i), si)] = (a, b, opc, y)
        counts = self.family_for("bitcount") if ops & {"popcount", "clz", "ctz"} else None
        if counts:
            for op, fn in (("popcount", FAM.popcount_module), ("clz", FAM.lzc_module), ("ctz", FAM.tzc_module)):
                m = fn(counts[0], counts[1], w) if op in ops else None
                if not m:
                    continue                     # no library counter: the op stays behavioral in the lane
                if self.xs("bitcount"):
                    nb = w.bit_length()
                    for i, t, si in lane_sets:
                        a = self.tmp(f"{p}_{op}_a{t}", w)
                        if si:
                            n = mod.logic(f"{p}_{op}_n{t}", nb)
                            name = self.library_module(m)
                            inst(name, m.params, f"u_{p}_{op}{t} (.a({a}), .n({n}));",
                                 f"structure core.bitcount.m{mi}: family {counts[0]} realized by the library module {name} "
                                 f"({op}) (result set {si})")
                        else:
                            n = self.xs_lane("bitcount", t, {f"{op}_a": (a, w)}, {f"{op}_n": nb})[f"{op}_n"]
                            mod.raw(f"  // structure core.bitcount.m{mi}: the unit's {op} counter shared across modes")
                        self.lib_inst[(op, self.tag(i), si)] = (a, n)
                    continue
                name = self.library_module(m)
                for i, t, si in lane_sets:
                    a = self.tmp(f"{p}_{op}_a{t}", w)
                    n = mod.logic(f"{p}_{op}_n{t}", w.bit_length())
                    inst(name, m.params, f"u_{p}_{op}{t} (.a({a}), .n({n}));",
                         f"structure core.bitcount.m{mi}: family {counts[0]} realized by the library module {name} ({op})"
                         + (f" (result set {si})" if si else ""))
                    self.lib_inst[(op, self.tag(i), si)] = (a, n)
        from chialu.targets.rtl.families.fp import Geom
        for op in sorted(ops):
            target = A.cvt_target(op)
            if target is None or isinstance(target, BlockFormat):
                continue
            family = self.family_for("converter", target=target.name)
            if not family:
                continue
            core = _core(target)
            # the name carries the engine geometry rather than the mode prefix: two modes of one
            # geometry converting into the same target render the same text, and a mode prefix
            # gave that one text several names (docs/issues.md, "One module text receives several
            # names"). The geometry is what the text actually varies with, so it stays in the name.
            geom = Geom.of_engine(self.eng)
            module = FAM.fp_module("converter", family[0], family[1], geom,
                                   fmt=core, tokens=self.eng.tokens,
                                   name=f"fam_int_cvt_{family[0]}_{fmt_tag(target)}_{geom.tag()}")
            if module is None:
                continue
            name = self.library_module(module)
            for i, t, si in lane_sets:
                x = self.tmp(f"{p}_cv_x{t}_{fmt_tag(target)}", self.eng.XT)
                word = self.tmp(f"{p}_cv_word{t}_{fmt_tag(target)}", self.sr_bits)
                fl = mod.logic(f"{p}_cv_fl{t}_{fmt_tag(target)}", FW)
                bits = mod.logic(f"{p}_cv_bits{t}_{fmt_tag(target)}", core.width)
                inst(name, module.params,
                     f"u_{p}_cvt{t}_{fmt_tag(target)} (.x({x}), .rnd(rnd), .word({word}), .ftz(ftz), .fl({fl}), .bits({bits}));",
                     f"structure core.converter.m{mi}.{target.name}: family {family[0]}")
                self.lib_inst[("converter", self.tag(i), si, target.name)] = (x, word, fl, bits)

    def core_modules(self, w: int, binary: bool, adder) -> dict:
        """The lane modules a core family imposes on a binary integer lane
        (families/redundant.py): under `redundant_internal` the adder of
        the representation slot's family (its exit conversion through the
        lane's own adder family) and, for the redundant_binary_multiplier
        representation, that multiplier; under `rns_internal` the adder,
        multiplier and comparator of the channels slot's family. {kind:
        Module, kind_owner: the comment's text}; empty for the other cores."""
        from chialu.targets.rtl import families as FAM
        from chialu.targets.rtl.families import Module
        from chialu.targets.rtl.families import redundant as RED
        core = self.families.get("core")
        out: dict = {}
        if not core or not binary:
            return out
        signed = self.enc == "twos_complement"
        if core[0] == "redundant_internal":
            rep = self.families.get("core.representation")
            if not rep:
                return out
            fam, pins = rep
            if fam == "carry_save_datapath":
                from chialu.targets.rtl.families.selection import copy_pins, register_origin
                prefix = "assimilator."
                rep_family = pins.get(prefix + "family")
                rep_pins = {key[len(prefix):]: value for key, value in pins.items()
                            if key.startswith(prefix) and key != prefix + "family"}
                selected_family = adder[0] if adder else rep_family or "ripple_carry"
                if adder and rep_family is not None and rep_family != selected_family:
                    raise ValueError(f"core.adder.m{self.mi} and core.representation.assimilator select different families for the same exit")
                selected_pins = copy_pins(adder[1] if adder else rep_pins)
                for key, value in rep_pins.items():
                    if key in selected_pins and selected_pins[key] != value:
                        raise ValueError(f"core.adder.m{self.mi} and core.representation.assimilator disagree on {key}")
                    selected_pins[key] = value
                assimilator = FAM.adder_module(selected_family, selected_pins, w + 1)
                if assimilator is None:
                    raise ValueError(f"carry_save_datapath: selected exit adder {selected_family!r} rejected width {w+1}")
                resolved = copy_pins(pins)
                resolved[prefix + "family"] = selected_family
                resolved.update({prefix + key: value for key, value in selected_pins.items()})
                name, text = RED.representation_adder_sv(w, fam, resolved, assimilator=assimilator)
                register_origin("core.representation", fam, pins, name, text)
                out["adder"] = Module(name, {}, text, assimilator.ctrl)
                out["owns_adder"] = True
                out["adder_owner"] = f"the carry_save_datapath core's {selected_family} assimilator"
                return out
            if fam == "redundant_binary_multiplier":
                m = FAM.mul_module("redundant_binary_multiplier", pins, w, signed)
                if m:
                    out["multiplier"] = m
                    out["multiplier_owner"] = "the redundant_internal core's representation redundant_binary_multiplier"
                return out
            from chialu.targets.rtl.families.selection import copy_pins
            cpa = copy_pins(pins)
            if adder:
                cpa["cpa.family"] = adder[0]
                cpa.update({f"cpa.{k}": v for k, v in adder[1].items()})
            try:
                name, text = RED.representation_adder_sv(w, fam, cpa)
            except ValueError:
                return out
            out["adder"] = Module(name, {}, text)
            uses_cpa = adder and (fam != "generalized_signed_digit" or pins.get("final_conversion", "cpa") != "on_the_fly")
            out["adder_owner"] = f"the redundant_internal core's representation {fam}" + (f" (family {adder[0]} converts at the exit)" if uses_cpa else "")
            return out
        if core[0] == "rns_internal":
            chan = self.families.get("core.channels")
            if not chan:
                return out
            fam, pins = chan
            from chialu.targets.rtl.families.selection import copy_pins
            lane_adder = self.family_for("adder") if any((self.mi, op) in self.lay["legal"] for op in ADDER_OPS) else None
            prefix = "modular_adder."
            channel_family = pins.get(prefix + "family")
            channel_pins = {key[len(prefix):]: value for key, value in pins.items()
                            if key.startswith(prefix) and key != prefix + "family"}
            selected_family = lane_adder[0] if lane_adder else channel_family or "ripple_carry"
            if lane_adder and channel_family is not None and channel_family != selected_family:
                raise ValueError(f"core.adder.m{self.mi} and core.channels.modular_adder select different families for the same channel CPA")
            selected_pins = copy_pins(lane_adder[1] if lane_adder else channel_pins)
            for key, value in channel_pins.items():
                if key in selected_pins and selected_pins[key] != value:
                    raise ValueError(f"core.adder.m{self.mi} and core.channels.modular_adder disagree on {key}")
                selected_pins[key] = value
            resolved = copy_pins(pins)
            resolved[prefix + "family"] = selected_family
            resolved.update({prefix + key: value for key, value in selected_pins.items()})
            needed = {op for _, op in self.ops}
            operations = {"adder": set(ADDER_OPS), "multiplier": set(MUL_OPS), "comparator": {"cmp", "min", "max"}}
            for kind in ("adder", "multiplier", "comparator"):
                if not needed & operations[kind]:
                    continue
                controls = {}
                name, text = RED.rns_sv(kind, w, fam, resolved, signed,
                                        adder_selection=(selected_family, selected_pins), control_ports=controls)
                out[kind] = Module(name, {}, text, tuple(controls.items()))
                out[f"{kind}_owner"] = f"the rns_internal core's channels {fam}"
                if kind == "adder":
                    out["owns_adder"] = True
            return out
        return out
    def declare_bcd_library(self, ops: set, lane_sets: list, inst):
        """One decimal library instance per lane for the structures of a
        BCD lane whose declared family the library realizes: the decimal
        adder (a, b, sub, cin -> s, cout; the add class drives it per op),
        the decimal multiplier (the double-length product) and the decimal
        divider (quotient and remainder digits)."""
        from chialu.targets.rtl import families as FAM
        mod, p, w, mi = self.mod, self.p, self.w, self.mi
        D_ = self.fmt.digits
        adder = self.family_for("adder") if ops & set(ADDER_OPS) else None
        mod_ = FAM.bcd_adder_module(adder[0], adder[1], D_) if adder else None
        if mod_:
            name = self.library_module(mod_)
            for i, t, si in lane_sets:
                a, b = self.tmp(f"{p}_bad_a{t}", w), self.tmp(f"{p}_bad_b{t}", w)
                sub, cin = self.tmp(f"{p}_bad_sub{t}", 1), self.tmp(f"{p}_bad_cin{t}", 1)
                s, cout = mod.logic(f"{p}_bad_s{t}", w), mod.logic(f"{p}_bad_cout{t}", 1)
                inst(name, mod_.params, f"u_{p}_bcd_adder{t} (.a({a}), .b({b}), .sub({sub}), .cin({cin}), .s({s}), .cout({cout}));",
                     f"structure core.adder.m{mi}: family {adder[0]} realized by the library module {name}"
                     + (f" (result set {si})" if si else ""))
                self.lib_inst[("bcd_adder", self.tag(i), si)] = (a, b, sub, cin, s, cout)
        mult = self.family_for("multiplier") if ops & set(MUL_OPS) else None
        mod_ = FAM.bcd_mul_module(mult[0], mult[1], D_) if mult else None
        if mod_:
            name = self.library_module(mod_)
            for i in self.lanes:
                t = self.tag(i)
                a, b = self.tmp(f"{p}_bmul_a{t}", w), self.tmp(f"{p}_bmul_b{t}", w)
                prod = mod.logic(f"{p}_bmul_p{t}", 2 * w)
                inst(name, mod_.params, f"u_{p}_bcd_mul{t} (.a({a}), .b({b}), .p({prod}));",
                     f"structure core.multiplier.m{mi}: family {mult[0]} realized by the library module {name}")
                self.lib_inst[("bcd_mul", t, 0)] = (a, b, prod)
        divf = self.family_for("divider") if ops & set(DIV_OPS) else None
        if divf:
            # the divider's inner multiplications stay behavioral (a partial-product tree per multiply would
            # dominate the divider): the divider's own pins alone reach the generator
            mod_ = FAM.bcd_div_module(divf[0], divf[1], D_)
            if mod_:
                name = self.library_module(mod_)
                for i in self.lanes:
                    t = self.tag(i)
                    a, b = self.tmp(f"{p}_bdiv_a{t}", w), self.tmp(f"{p}_bdiv_b{t}", w)
                    q, r = mod.logic(f"{p}_bdiv_q{t}", w), mod.logic(f"{p}_bdiv_r{t}", w)
                    inst(name, mod_.params, f"u_{p}_bcd_div{t} (.a({a}), .b({b}), .q({q}), .r({r}));",
                         f"structure core.divider.m{mi}: family {divf[0]} realized by the library module {name}")
                    self.lib_inst[("bcd_div", t, 0)] = (a, b, q, r)

    def emit_bcd_op(self, op: str, i, r: int, pa: str, pb: str, set_idx: int, lhs_w: int) -> bool:
        """An add-class or multiply-class op of a BCD lane on its library
        decimal adder or multiplier: the patterns go in, the result
        pattern comes out; the flags read off the carry (an unsigned
        format: overflow and int_overflow are the carry out of an
        addition, the missing carry of a subtraction or a negation; carry
        as the reference defines it; a saturating op clamps at all nines
        or zero). False when the lane has no library instance for the op."""
        blk, w = self.blk, self.w
        t = self.tag(i)
        nines = "{" + f"{self.fmt.digits}{{4'd9}}" + "}"
        if op in ADDER_OPS:
            inst = self.lib_inst.get(("bcd_adder", t, set_idx))
            if inst is None:
                return False
            a, b, sub, cin, s, cout = inst
            xa, xb, xs, xc = {"add": (pa, pb, 0, 0), "adc": (pa, pb, 0, 1), "sub": (pa, pb, 1, 0), "sbb": (pa, pb, 1, 1),
                              "neg": (f"{w}'d0", pa, 1, 0), "abs": (pa, f"{w}'d0", 0, 0),
                              "add_sat": (pa, pb, 0, 0), "sub_sat": (pa, pb, 1, 0)}[op]
            blk.stmt(f"{a} = {xa}; {b} = {xb}; {sub} = 1'b{xs}; {cin} = 1'b{xc};")
            fl = []
            if op in ("add", "adc", "add_sat"):
                fl += [flag_if(cout, "int_overflow"), flag_if(cout, "overflow")]
                if op != "add_sat":
                    fl.append(flag_if(cout, "carry"))
                res = f"{cout} ? {nines} : {s}" if op == "add_sat" else s
            elif op in ("sub", "sbb", "sub_sat", "neg"):
                fl += [flag_if(f"~{cout}", "int_overflow"), flag_if(f"~{cout}", "overflow")]
                if op in ("sub", "sbb"):
                    fl.append(flag_if(f"~{cout}", "carry"))
                res = f"{cout} ? {s} : {w}'d0" if op == "sub_sat" else s
            else:
                res = s
            self.put(set_idx, i, lhs_w, res)
            if fl:
                self.put_flags(r, " | ".join(fl), set_idx)
            return True
        if op in MUL_OPS:
            inst = self.lib_inst.get(("bcd_mul", t, 0))
            if inst is None:
                return False
            a, b, prod = inst
            blk.stmt(f"{a} = {pa}; {b} = {pb};")
            if op == "mul_wide":
                self.put(set_idx, i, lhs_w, prod)
                return True
            hi_nz = f"({prod}[{2*w-1}:{w}] != {w}'d0)"
            res = {"mul": f"{prod}[{w-1}:0]", "mul_high": f"{prod}[{2*w-1}:{w}]",
                   "mul_sat": f"{hi_nz} ? {nines} : {prod}[{w-1}:0]"}[op]
            self.put(set_idx, i, lhs_w, res)
            self.put_flags(r, " | ".join([flag_if(hi_nz, "int_overflow"), flag_if(hi_nz, "overflow")]), set_idx)
            return True
        return False

    def emit_add_library(self, op: str, inst: tuple, pa: str, pb: str, sa: str, sbit: str, ex: str, fl: list):
        """An add-class op on the lane's library adder: s = a' + b' + cin
        with (a', b', cin) = (a, b, 0) add, (a, ~b, 1) sub, (a, b, 1)
        adc, (a, ~b, 0) sbb, (0, ~a, 1) neg and abs; the exact value is
        {ext, s} with ext = a'_s ^ b'_s ^ cout (two's complement), or
        {cout, s} / {~cout, s} (unsigned add / subtract); int_overflow is
        the signed view's ext ^ s_msb, the carry flag cout or ~cout."""
        blk, w, enc = self.blk, self.w, self.enc
        a, b, cin, s, cout = inst
        if self.value_encoded:
            # Ones' complement and sign-magnitude patterns first become signed
            # binary values. The selected CPA supplies the result before the
            # format's existing wrap/saturate encoder is applied.
            aa = self.tmp(f"{a}_value", w)
            bb = self.tmp(f"{b}_value", w)
            blk.stmt(f"{aa} = {self.value_pattern(pa)}; {bb} = {self.value_pattern(pb)};")
            neg = op in ("neg", "abs")
            subtract = op in ("sub", "sbb", "sub_sat")
            blk.stmt(f"{a} = {'0' if neg else aa}; {b} = {'~' + aa if neg else ('~' if subtract else '') + bb}; "
                     f"{cin} = 1'b{int(neg or op in ('adc', 'sub', 'sub_sat'))};")
            ext = f"({a}[{w-1}] ^ {b}[{w-1}] ^ {cout})"
            value = f"$signed({{{ext}, {s}}})"
            if op == "abs":
                value = f"({sa} ? {value} : $signed({aa}))"
            blk.stmt(f"{ex} = {value};")
            ta, tb = f"$signed({{{sa}, {pa}}})", f"$signed({{{sbit}, {pb}}})"
            pattern_expr = {"add": f"{ta}+{tb}", "adc": f"{ta}+{tb}+1", "add_sat": f"{ta}+{tb}",
                            "sub": f"{ta}-{tb}", "sbb": f"{ta}-{tb}-1", "sub_sat": f"{ta}-{tb}",
                            "neg": f"-{ta}", "abs": f"({ta}<0 ? -{ta} : {ta})"}[op]
            sx = self.tmp(f"{a}_pattern_sum", self.EWI, signed=True)
            blk.stmt(f"{sx} = {pattern_expr};")
            fl.append(flag_if(f"{sx} > {self.sd((1 << (w-1))-1)} || {sx} < {self.sd(-(1 << (w-1)))}", "int_overflow"))
            fl.append(flag_if(f"{ex} > {self.sd(self.pint.max_int)} || {ex} < {self.min_lit()}", "overflow"))
            if op in ("add", "adc"):
                fl.append(flag_if(f"(({{1'b0, {pa}}} + {{1'b0, {pb}}} + {int(op == 'adc')}) >> {w}) != 0", "carry"))
            elif op in ("sub", "sbb"):
                fl.append(flag_if(f"{{1'b0, {pa}}} < {{1'b0, {pb}}} + {int(op == 'sbb')}", "carry"))
            elif op == "neg":
                fl.append(flag_if(f"{pa} != 0", "carry"))
            return
        neg = op in ("neg", "abs")
        sub = op in ("sub", "sbb", "sub_sat")
        if neg:
            blk.stmt(f"{a} = {w}'d0; {b} = ~{pa}; {cin} = 1'b1;")
            a_s, b_s = "1'b0", f"~{sa}"
        else:
            blk.stmt(f"{a} = {pa}; {b} = {'~' if sub else ''}{pb}; {cin} = 1'b{1 if op in ('adc', 'sub', 'sub_sat') else 0};")
            a_s, b_s = sa, (f"~{sbit}" if sub else sbit)
        ext = f"({a_s} ^ {b_s} ^ {cout})"
        int_ovf = f"({ext} ^ {s}[{w-1}])"
        if enc == "twos_complement":
            val = f"$signed({{{ext}, {s}}})"
            if op == "abs":
                val = f"({sa} ? {val} : $signed({{1'b0, {pa}}}))"
                int_ovf = f"({sa} & {int_ovf})"
            blk.stmt(f"{ex} = {val};")
            fl.append(flag_if(int_ovf, "int_overflow"))
            fl.append(flag_if(int_ovf, "overflow"))
        else:
            if op in ("add", "adc", "add_sat"):
                blk.stmt(f"{ex} = $signed({{1'b0, {cout}, {s}}});")
                fl.append(flag_if(cout, "overflow"))
            else:                                    # sub, sbb, neg: {~cout, s} is the (negative or not) difference
                blk.stmt(f"{ex} = $signed({{~{cout}, {s}}});")
                fl.append(flag_if(f"~{cout}", "overflow"))
            fl.append(flag_if(int_ovf, "int_overflow"))
        if op in ("add", "adc"):
            fl.append(flag_if(cout, "carry"))
        elif op in ("sub", "sbb"):
            fl.append(flag_if(f"~{cout}", "carry"))
        elif op == "neg":
            fl.append(flag_if(f"{pa} != 0", "carry"))

    def emit_eac_library(self, op: str, inst: tuple, pa: str, pb: str, sa: str, ex: str) -> str:
        """The ones'-complement result pattern of an add-class op from the
        lane's end-around-carry adder: (a, b, 0) add, (a, ~b, 0) sub,
        (a, b, 1) adc, (0, ~a, 0) neg; abs selects the negation by the
        sign; sbb takes the borrow's minus one as a decrement after the
        adder (a zero sum decrements to the minus-one pattern). The
        adder's minus zero stands only for an exact zero: a sum that
        overflows to a multiple of the modulus wraps to plus zero, as
        the reference's modular wrap does."""
        blk, w = self.blk, self.w
        a, b, cin, s, cout = inst
        m1 = (1 << w) - 2                       # the pattern of minus one
        ones = f"{{{w}{{1'b1}}}}"
        if op in ("neg", "abs"):
            blk.stmt(f"{a} = {w}'d0; {b} = ~{pa}; {cin} = 1'b0;")
            return f"({sa} ? {s} : {pa})" if op == "abs" else s
        blk.stmt(f"{a} = {pa}; {b} = {'~' if op in ('sub', 'sbb') else ''}{pb}; {cin} = 1'b{1 if op == 'adc' else 0};")
        if op == "sbb":
            # the minus one as an end-around addition of its pattern: +0 - 1 = -1, 1 - 1 = -0, else s - 1
            dec = f"(({s} == 0) ? {w}'d{m1} : ({s} == {w}'d1) ? {ones} : ({s} - 1'b1))"
            return f"(({dec} == {ones} && {ex} != 0) ? {w}'d0 : {dec})"
        return f"(({s} == {ones} && {ex} != 0) ? {w}'d0 : {s})"

    def emit_mul_library(self, inst: tuple, pa: str, pb: str, va: str, vb: str, sa: str, sbit: str,
                         ex: str, fl: list, set_idx: int) -> str:
        """The exact product from the lane's library multiplier (the
        two's complement or unsigned product of the patterns, extended to
        the exact width); int_overflow from the signed view of the
        product, which for an unsigned format is the product less the
        sign-weighted operands rather than a second multiplier. Returns
        the expression of the exact product for the rounding paths."""
        blk, w, EWI, enc, p = self.blk, self.w, self.EWI, self.enc, self.p
        a, b, prod = inst
        blk.stmt(f"{a} = {self.value_pattern(pa)}; {b} = {self.value_pattern(pb)};")
        if enc == "twos_complement" or self.value_encoded:
            blk.stmt(f"{ex} = $signed({{{{{EWI - 2 * w}{{{prod}[{2*w-1}]}}}}, {prod}}});")
            sx = ex
            if self.value_encoded:
                sx = self.tmp(f"{a}_pattern_product", EWI, signed=True)
                blk.stmt(f"{sx} = $signed({{{sa}, {pa}}}) * $signed({{{sbit}, {pb}}});")
        else:
            blk.stmt(f"{ex} = $signed({{{{{EWI - 2 * w}{{1'b0}}}}, {prod}}});")
            sx = self.tmp(f"{p}_o{self.oi}sx{set_idx}_{a[len(p) + 7:]}", EWI, signed=True)     # the lane tag after m<i>_mul_a
            # (a - 2^w a_s)(b - 2^w b_s) = ab - 2^w (a_s b + b_s a) + 2^2w a_s b_s
            blk.stmt(f"{sx} = {ex} - ({sa} ? ($signed({vb}) <<< {w}) : {EWI}'sd0) - ({sbit} ? ($signed({va}) <<< {w}) : {EWI}'sd0)"
                     f" + (({sa} & {sbit}) ? {EWI}'sd{1 << (2 * w)} : {EWI}'sd0);")
        fl.append(flag_if(f"{sx} > {EWI}'sd{(1 << (w-1)) - 1} || {sx} < -{EWI}'sd{1 << (w-1)}", "int_overflow"))
        return ex

    def value_pattern(self, pattern: str) -> str:
        """A signed binary value at the arithmetic family's unchanged width."""
        w = self.w
        if self.enc == "ones_complement":
            return f"({pattern}[{w-1}] ? -$signed(~{pattern}) : $signed({pattern}))"
        if self.enc == "sign_magnitude":
            return f"({pattern}[{w-1}] ? -$signed({{1'b0, {pattern}[{w-2}:0]}}) : $signed({pattern}))"
        return pattern

    def cmp_wires(self, i, pa: str, pb: str, sa: str, sbit: str):
        """(lt, eq) of the lane's comparator instance, or of its adder as a
        subtractor (lt the sign of the exact difference, eq a zero sum),
        after driving the operands; None without a library instance."""
        t = self.tag(i)
        w, blk = self.w, self.blk
        if ("comparator", t, 0) in self.lib_inst:
            a, b, lt, eq = self.lib_inst[("comparator", t, 0)]
            blk.stmt(f"{a} = {self.value_pattern(pa)}; {b} = {self.value_pattern(pb)};")
            return lt, eq
        if ("adder", t, 0) in self.lib_inst:
            a, b, cin, s, cout = self.lib_inst[("adder", t, 0)]
            blk.stmt(f"{a} = {self.value_pattern(pa)}; {b} = ~{self.value_pattern(pb)}; {cin} = 1'b1;")
            lt = f"({sa} ^ ~{sbit} ^ {cout})" if self.enc == "twos_complement" else \
                 f"({a}[{w-1}] ^ {b}[{w-1}] ^ {cout})" if self.value_encoded else f"(~{cout})"
            eq = f"({pa} == {pb})" if getattr(self, "cmp_zero_detect", None) == "operand_xnor" else f"({s} == {w}'d0)"
            return lt, eq
        return None

    def helpers(self):
        """wrap / saturate / encode functions of the mode's format on a
        signed exact value, the fixed-point rounding shift and the SR word
        of a division."""
        p, w, EWI, enc = self.p, self.w, self.EWI, self.enc
        mx, mn = self.fmt.max_int, self.fmt.min_int
        mod = self.lib
        if enc == "bcd":
            D_ = self.fmt.digits
            mod.function(f'''
  function automatic [{w-1}:0] {p}_enc(input signed [{EWI-1}:0] v);
    logic [{EWI-1}:0] t; integer i;
    t = v; for (i = 0; i < {D_}; i = i + 1) begin {p}_enc[4*i +: 4] = t % 10; t = t / 10; end
  endfunction
  function automatic [{w-1}:0] {p}_wrap(input signed [{EWI-1}:0] v);
    logic signed [{EWI-1}:0] r;
    r = v % {EWI}'sd{10 ** D_}; if (r < 0) r = r + {EWI}'sd{10 ** D_};
    {p}_wrap = {p}_enc(r);
  endfunction
  function automatic [{w-1}:0] {p}_sat(input signed [{EWI-1}:0] v);
    {p}_sat = (v > {EWI}'sd{mx}) ? {p}_enc({EWI}'sd{mx}) : (v < 0) ? {p}_enc(0) : {p}_enc(v);
  endfunction''')
        elif enc == "ones_complement":
            m = (1 << w) - 1
            mod.function(f'''
  function automatic [{w-1}:0] {p}_enc(input signed [{EWI-1}:0] v);
    {p}_enc = (v < 0) ? ~((-v) & {{{w}{{1'b1}}}}) : v[{w-1}:0];
  endfunction
  function automatic [{w-1}:0] {p}_wrap(input signed [{EWI-1}:0] v);
    logic signed [{EWI-1}:0] r;
    r = v % {EWI}'sd{m}; if (r < 0) r = r + {EWI}'sd{m};
    if (r > {EWI}'sd{mx}) r = r - {EWI}'sd{m};
    {p}_wrap = {p}_enc(r);
  endfunction
  function automatic [{w-1}:0] {p}_sat(input signed [{EWI-1}:0] v);
    {p}_sat = (v > {EWI}'sd{mx}) ? {p}_enc({EWI}'sd{mx}) : (v < -{EWI}'sd{-mn}) ? {p}_enc(-{EWI}'sd{-mn}) : {p}_enc(v);
  endfunction''')
        elif enc == "sign_magnitude":
            mod.function(f'''
  function automatic [{w-1}:0] {p}_enc(input signed [{EWI-1}:0] v);
    logic [{EWI-1}:0] mag;
    mag = (v < 0) ? -v : v;
    {p}_enc = {{(v < 0), mag[{w-2}:0]}};
  endfunction
  function automatic [{w-1}:0] {p}_wrap(input signed [{EWI-1}:0] v);
    logic [{EWI-1}:0] mag;
    mag = ((v < 0) ? -v : v) & {{{w-1}{{1'b1}}}};
    {p}_wrap = {{(v < 0) && (mag != 0), mag[{w-2}:0]}};
  endfunction
  function automatic [{w-1}:0] {p}_sat(input signed [{EWI-1}:0] v);
    {p}_sat = (v > {EWI}'sd{mx}) ? {p}_enc({EWI}'sd{mx}) : (v < -{EWI}'sd{-mn}) ? {p}_enc(-{EWI}'sd{-mn}) : {p}_enc(v);
  endfunction''')
        elif enc == "unsigned":
            mod.function(f'''
  function automatic [{w-1}:0] {p}_enc(input signed [{EWI-1}:0] v); {p}_enc = v[{w-1}:0]; endfunction
  function automatic [{w-1}:0] {p}_wrap(input signed [{EWI-1}:0] v); {p}_wrap = v[{w-1}:0]; endfunction
  function automatic [{w-1}:0] {p}_sat(input signed [{EWI-1}:0] v);
    {p}_sat = (v > {EWI}'sd{mx}) ? {{{w}{{1'b1}}}} : (v < 0) ? {w}'d0 : v[{w-1}:0];
  endfunction''')
        else:
            mod.function(f'''
  function automatic [{w-1}:0] {p}_enc(input signed [{EWI-1}:0] v); {p}_enc = v[{w-1}:0]; endfunction
  function automatic [{w-1}:0] {p}_wrap(input signed [{EWI-1}:0] v); {p}_wrap = v[{w-1}:0]; endfunction
  function automatic [{w-1}:0] {p}_sat(input signed [{EWI-1}:0] v);
    {p}_sat = (v > {EWI}'sd{mx}) ? {{1'b0, {{{w-1}{{1'b1}}}}}} : (v < -{EWI}'sd{-mn}) ? {{1'b1, {{{w-1}{{1'b0}}}}}} : v[{w-1}:0];
  endfunction''')
        sb = self.sr_bits
        srge = "1" if self.conv.sr_compare == "ge" else "0"
        mod.function(f'''
  // round v / 2^f under rnd (the SR word applies to the fraction bits)
  function automatic signed [{EWI-1}:0] {p}_rshift(input signed [{EWI-1}:0] v, input integer f, input [2:0] rnd, input [{sb-1}:0] word);
    logic s; logic [{EWI-1}:0] mag, keep, rest, halfv; logic [{EWI+sb}:0] fint; logic up, inexact;
    s = v < 0; mag = s ? -v : v;
    if (f <= 0) {p}_rshift = v;
    else begin
      keep = mag >> f; rest = mag & ((({EWI}'d1) << f) - 1); halfv = ({EWI}'d1) << (f - 1);
      inexact = rest != 0;
      fint = (f >= {sb}) ? (rest >> (f - {sb})) : (rest << ({sb} - f));
      case (rnd)
        3'd0: up = (rest > halfv) || (rest == halfv && keep[0]);
        3'd1: up = 1'b0;
        3'd2: up = inexact && s;
        3'd3: up = inexact && !s;
        3'd4: up = inexact && ({srge} ? (fint >= word) : (fint > word));
        default: up = inexact;
      endcase
      keep = keep + up;
      {p}_rshift = s ? -$signed(keep) : $signed(keep);
    end
  endfunction
  // the SR word of a division: floor(|r| * 2^sb / |b|)
  function automatic [{sb-1}:0] {p}_divfrac(input [{EWI-1}:0] r, input [{EWI-1}:0] b);
    logic [{EWI+sb}:0] t;
    t = ({{{{{sb+1}{{1'b0}}}}, r}} << {sb}) / {{{{{sb+1}{{1'b0}}}}, b}};
    {p}_divfrac = t[{sb-1}:0];
  endfunction''')

    # ---- ops ----------------------------------------------------------------------
    def emit_op(self, op: str):
        blk, p, w, F, enc, EWI = self.blk, self.p, self.w, self.F, self.enc, self.EWI
        count = self.count
        tgt = A.cvt_target(op)
        preserve = self.conv.zero_sign == "preserve" and enc in ("ones_complement", "sign_magnitude")
        div_zero_zero = self.conv.int_div_zero == "zero"
        qs = list(self.spec.get("quotient_semantics") or ["truncate_zero"])
        floor_q = A._floor_division(op, qs)
        mx = self.pint.max_int
        for set_idx, src, oth in self.result_sets(op):
            self.set_idx = set_idx
            base = 0 if set_idx == 0 else count
            if tgt is not None:
                self.emit_cvt(op, tgt, set_idx, src, base)
                continue
            for i in self.lanes:
                r = base + i
                pa, pb = self.pat(src, i), self.pat(oth, i)
                va, vb = f"{p}_v{src}{self.tag(i)}", f"{p}_v{oth}{self.tag(i)}"
                sa, sbit = f"{pa}[{w-1}]", f"{pb}[{w-1}]"
                lhs_w = 2 * w if op == "mul_wide" else w
                ex = self.tmp(f"{p}_o{self.oi}ex{set_idx}_{self.tag(i)}", EWI, signed=True)
                fl = []
                tw_a = f"$signed({{{pa}[{w-1}], {pa}}})"      # two's complement view for int_overflow
                tw_b = f"$signed({{{pb}[{w-1}], {pb}}})"
                if self.bcd and self.emit_bcd_op(op, i, r, pa, pb, set_idx, lhs_w):
                    continue
                if op in A.ARITH_EXACT:
                    adder = self.lib_inst.get(("adder", self.tag(i), set_idx)) if op in ADDER_OPS else None
                    mult = self.lib_inst.get(("multiplier", self.tag(i), 0)) if op in MUL_OPS else None
                    prod_expr = f"{va} * {vb}"          # the exact product the rounding paths reuse
                    if adder is not None and not (op == "abs" and enc == "unsigned"):
                        self.emit_add_library(op, adder, pa, pb, sa, sbit, ex, fl)
                    else:
                        if mult is not None:
                            prod_expr = self.emit_mul_library(mult, pa, pb, va, vb, sa, sbit, ex, fl, set_idx)
                        else:
                            exact = {"add": f"{va} + {vb}", "sub": f"{va} - {vb}", "adc": f"{va} + {vb} + 1",
                                     "sbb": f"{va} - {vb} - 1", "neg": f"-{va}", "abs": f"({va} < 0) ? -{va} : {va}",
                                     "add_sat": f"{va} + {vb}", "sub_sat": f"{va} - {vb}",
                                     "mul": f"{va} * {vb}", "mul_sat": f"{va} * {vb}", "mul_high": f"{va} * {vb}",
                                     "mul_wide": f"{va} * {vb}"}[op]
                            blk.stmt(f"{ex} = {exact};")
                            s_exact = {"add": f"{tw_a} + {tw_b}", "sub": f"{tw_a} - {tw_b}", "adc": f"{tw_a} + {tw_b} + 1",
                                       "sbb": f"{tw_a} - {tw_b} - 1", "neg": f"-{tw_a}", "abs": f"(({tw_a} < 0) ? -{tw_a} : {tw_a})",
                                       "add_sat": f"{tw_a} + {tw_b}", "sub_sat": f"{tw_a} - {tw_b}",
                                       "mul": f"{tw_a} * {tw_b}", "mul_sat": f"{tw_a} * {tw_b}", "mul_high": f"{tw_a} * {tw_b}",
                                       "mul_wide": f"{tw_a} * {tw_b}"}[op]
                            if not self.bcd:
                                sx = self.tmp(f"{p}_o{self.oi}sx{set_idx}_{self.tag(i)}", EWI, signed=True)
                                blk.stmt(f"{sx} = {s_exact};")
                                fl.append(flag_if(f"{sx} > {EWI}'sd{(1 << (w-1)) - 1} || {sx} < -{EWI}'sd{1 << (w-1)}",
                                                  "int_overflow"))
                            else:
                                fl.append(flag_if(f"{ex} > {EWI}'sd{mx} || {ex} < 0", "int_overflow"))
                        if op == "mul_wide":
                            fl = []                       # exact: no overflow flags
                        else:
                            fl.append(flag_if(f"{ex} > {EWI}'sd{mx} || {ex} < {self.min_lit()}", "overflow"))
                        # carry
                        if self.bcd:
                            top = 10 ** self.fmt.digits
                            if op in ("add", "adc"):
                                fl.append(flag_if(f"({va} + {vb} + {1 if op == 'adc' else 0}) >= {EWI}'sd{top}", "carry"))
                            elif op in ("sub", "sbb"):
                                fl.append(flag_if(f"{va} < {vb} + {1 if op == 'sbb' else 0}", "carry"))
                        else:
                            if op in ("add", "adc"):
                                fl.append(flag_if(f"(({{1'b0, {pa}}} + {{1'b0, {pb}}} + {1 if op == 'adc' else 0}) >> {w}) != 0", "carry"))
                            elif op in ("sub", "sbb"):
                                fl.append(flag_if(f"{{1'b0, {pa}}} < {{1'b0, {pb}}} + {1 if op == 'sbb' else 0}", "carry"))
                            elif op == "neg":
                                fl.append(flag_if(f"{pa} != 0", "carry"))
                    # the result
                    if op == "mul_wide":
                        res = self.wide_result(ex, sa, sbit, preserve)
                        self.put(set_idx, i, lhs_w, res)
                    elif op == "mul_high":
                        if self.bcd:
                            res = f"{p}_enc(({ex} / {EWI}'sd{10 ** self.fmt.digits}) % {EWI}'sd{10 ** self.fmt.digits})"
                        else:
                            res = f"{p}_wrap({ex} >>> {w})"
                        if preserve:
                            res = f"(({ex} == 0) ? {self.zero_pat(f'({sa} ^ {sbit})')} : {res})"
                        self.put(set_idx, i, lhs_w, res)
                    elif op in ("add_sat", "sub_sat", "mul_sat"):
                        res = f"{p}_sat({ex})"
                        if preserve and op == "mul_sat":
                            res = f"(({ex} == 0) ? {self.zero_pat(f'({sa} ^ {sbit})')} : {res})"
                        self.put(set_idx, i, lhs_w, res)
                    elif op == "mul" and F:
                        # fixed point: round the product to F fraction bits then wrap
                        pr = self.tmp(f"{p}_o{self.oi}pr{set_idx}_{self.tag(i)}", EWI, signed=True)
                        blk.stmt(f"{pr} = {prod_expr};")
                        blk.stmt(f"{ex} = {p}_rshift({pr}, {F}, rnd, {self.word(r)});")
                        self.put(set_idx, i, lhs_w, f"{p}_wrap({ex})")
                        fl.append(flag_if(f"{p}_rshift({pr}, {F}, 3'd1, 0) * {EWI}'sd{1 << F} != {pr}", "inexact"))
                        fl.append(f"(({ex} > {EWI}'sd{mx} || {ex} < {self.min_lit()}) ? ({flag('overflow')} | {flag('inexact')}) : {NOFLAG})")
                    else:
                        res = f"{p}_wrap({ex})"
                        if preserve:
                            res = self.preserved(op, pa, pb, ex, res)
                        eac = self.lib_inst.get(("eac", self.tag(i), set_idx)) if op in ("add", "sub", "adc", "sbb", "neg", "abs") else None
                        if eac is not None:
                            res = self.emit_eac_library(op, eac, pa, pb, sa, ex)
                        self.put(set_idx, i, lhs_w, res)
                    if op == "mul_sat" and F:
                        pr = self.tmp(f"{p}_o{self.oi}pr{set_idx}_{self.tag(i)}", EWI, signed=True)
                        blk.stmt(f"{pr} = {prod_expr};")
                        blk.stmt(f"{ex} = {p}_rshift({pr}, {F}, rnd, {self.word(r)});")
                        self.put(set_idx, i, lhs_w, f"{p}_sat({ex})")
                        fl.append(flag_if(f"{p}_rshift({pr}, {F}, 3'd1, 0) * {EWI}'sd{1 << F} != {pr}", "inexact"))
                        fl.append(flag_if(f"{ex} > {EWI}'sd{mx} || {ex} < {self.min_lit()}", "inexact"))
                elif op in ("div", "quot", "rem", "mod"):
                    self.emit_div(op, i, r, pa, pb, va, vb, set_idx, fl, floor_q, div_zero_zero, preserve)
                elif op in ("min", "max"):
                    lib = self.cmp_wires(i, pa, pb, sa, sbit)
                    if lib is not None:
                        lt, eq = lib
                        cmp = f"({lt} | {eq})" if op == "min" else f"(~{lt})"
                    else:
                        cmp = f"({va} <= {vb})" if op == "min" else f"({va} >= {vb})"
                    self.put(set_idx, i, lhs_w, f"{cmp} ? {pa} : {pb}")
                elif op == "cmp":
                    lib = self.cmp_wires(i, pa, pb, sa, sbit)
                    if lib is not None:
                        lt, eq = lib
                        self.put(set_idx, i, lhs_w, f"{{{{{w-3}{{1'b0}}}}, (~{lt} & ~{eq}), {eq}, {lt}}}")
                    else:
                        self.put(set_idx, i, lhs_w, f"{{{{{w-3}{{1'b0}}}}, ({va} > {vb}), ({va} == {vb}), ({va} < {vb})}}")
                elif op in SHIFT_OPS:
                    lib = self.lib_inst.get(("shifter", self.tag(i), 0))
                    if lib is not None:
                        a, amt, opc, y = lib
                        aw = max(1, (w - 1).bit_length())
                        blk.stmt(f"{a} = {pa}; {amt} = {aw}'({pb} % {w}'d{w}); {opc} = 3'd{SHIFT_OPS[op]};")
                        self.put(set_idx, i, lhs_w, y)
                    else:
                        sh = f"({pb} % {w}'d{w})"
                        res = {"shl": f"{pa} << {sh}", "shr_logical": f"{pa} >> {sh}",
                               "shr_arith": f"$signed({pa}) >>> {sh}",
                               "rol": f"({pa} << {sh}) | ({pa} >> ({w}'d{w} - {sh}))",
                               "ror": f"({pa} >> {sh}) | ({pa} << ({w}'d{w} - {sh}))"}[op]
                        self.put(set_idx, i, lhs_w, res)
                elif op in ("and", "or", "xor", "not"):
                    lib = self.lib_inst.get(("logic", self.tag(i), set_idx))
                    if lib is not None:
                        a, b, opc, y = lib
                        blk.stmt(f"{a} = {pa}; {b} = {pb}; {opc} = 2'd{('and', 'or', 'xor', 'not').index(op)};")
                        res = y
                    elif ("pg_logic", self.tag(i), set_idx) in self.lib_inst:
                        a, b, cin, propagate, generate = self.lib_inst[("pg_logic", self.tag(i), set_idx)]
                        blk.stmt(f"{a} = {pa}; {b} = " + (f"{ones(w)}" if op == "not" else pb) + f"; {cin} = 1'b0;")
                        res = {"and": generate, "or": f"({propagate} | {generate})",
                               "xor": propagate, "not": propagate}[op]
                    else:
                        res = {"and": f"{pa} & {pb}", "or": f"{pa} | {pb}", "xor": f"{pa} ^ {pb}", "not": f"~{pa}"}[op]
                    self.put(set_idx, i, lhs_w, res)
                elif op in ("popcount", "clz", "ctz") and (op, self.tag(i), set_idx) in self.lib_inst:
                    a, n = self.lib_inst[(op, self.tag(i), set_idx)]
                    blk.stmt(f"{a} = {pa};")
                    nw = w.bit_length()
                    self.put(set_idx, i, lhs_w, f"{{{{{w - nw}{{1'b0}}}}, {n}}}" if w > nw else n)
                elif op == "popcount":
                    self.put(set_idx, i, lhs_w, " + ".join(f"{pa}[{k}]" for k in range(w)))
                elif op == "clz":
                    self.put(set_idx, i, lhs_w,
                             " ".join(f"{pa}[{k}] ? {w}'d{w-1-k} :" for k in range(w - 1, -1, -1)) + f" {w}'d{w}")
                elif op == "ctz":
                    self.put(set_idx, i, lhs_w,
                             " ".join(f"{pa}[{k}] ? {w}'d{k} :" for k in range(w)) + f" {w}'d{w}")
                if fl:
                    self.put_flags(r, " | ".join(fl), set_idx)

    def wide_result(self, ex: str, sa: str, sbit: str, preserve: bool) -> str:
        """The double-width pattern of an exact product."""
        p, w, EWI, enc = self.p, self.w, self.EWI, self.enc
        if self.bcd:
            D_ = self.fmt.digits
            self.lib.function(f'''
  function automatic [{2*w-1}:0] {p}_encw(input signed [{EWI-1}:0] v);
    logic [{EWI-1}:0] t; integer i;
    t = v; for (i = 0; i < {2*D_}; i = i + 1) begin {p}_encw[4*i +: 4] = t % 10; t = t / 10; end
  endfunction''')
            res = f"{p}_encw({ex})"
        elif enc == "ones_complement":
            res = f"(({ex} < 0) ? ~((-{ex}) & {{{2*w}{{1'b1}}}}) : {ex}[{2*w-1}:0])"
        elif enc == "sign_magnitude":
            res = f"(({ex} < 0) ? (((-{ex}) & {{{2*w-1}{{1'b1}}}}) | ({2*w}'d1 << {2*w-1})) : {{1'b0, {ex}[{2*w-2}:0]}})"
        else:
            res = f"{ex}[{2*w-1}:0]"
        if preserve:
            res = f"(({ex} == 0 && ({sa} ^ {sbit})) ? {self.zero_pat(f'({sa} ^ {sbit})', 2 * w)} : {res})"
        return res

    def preserved(self, op: str, pa: str, pb: str, ex: str, res: str) -> str:
        """zero_sign: preserve for ones' complement and sign-magnitude: the
        zero result carries the sign the exact computation gives it (an
        end-around-carry adder's zero for ones' complement sums)."""
        p, w, enc = self.p, self.w, self.enc
        sa, sbit = f"{pa}[{w-1}]", f"{pb}[{w-1}]"
        m = (1 << w) - 1
        if op in ("add", "sub", "adc", "sbb"):
            if enc == "ones_complement":
                s = {"add": f"({{1'b0, {pa}}} + {{1'b0, {pb}}})", "sub": f"({{1'b0, {pa}}} + {{1'b0, ~{pb}}})",
                     "adc": f"({{1'b0, {pa}}} + {{1'b0, {pb}}} + 1)",
                     "sbb": f"({{1'b0, {pa}}} + {{1'b0, ~{pb}}} + {{1'b0, {w}'d{m - 1}}})"}[op]
                self.lib.function(f'''
  function automatic [{w-1}:0] {p}_eac(input [{w+1}:0] s);
    logic [{w+1}:0] r;
    if (s == 0) {p}_eac = 0;
    else begin r = s % {w+2}'d{m}; {p}_eac = (r == 0) ? {{{w}{{1'b1}}}} : r[{w-1}:0]; end
  endfunction''')
                return f"(({ex} == 0) ? {p}_eac({s}) : {res})"
            return f"(({ex} == 0) ? {self.zero_pat(sa)} : {res})"
        if op == "neg":
            if enc == "ones_complement":
                return f"(({ex} == 0) ? ~{pa} : {res})"
            return f"(({ex} == 0) ? {self.zero_pat(f'!{sa}')} : {res})"
        if op in ("mul", "mul_high", "mul_sat"):
            return f"(({ex} == 0) ? {self.zero_pat(f'({sa} ^ {sbit})')} : {res})"
        return res

    def emit_div(self, op, i, r, pa, pb, va, vb, set_idx, fl, floor_q, dz_zero, preserve):
        blk, p, w, F, EWI = self.blk, self.p, self.w, self.F, self.EWI
        mx = self.pint.max_int
        sa, sbit = f"{pa}[{w-1}]", f"{pb}[{w-1}]"
        q = self.tmp(f"{p}_q{self.tag(i)}", EWI, signed=True)
        rm = self.tmp(f"{p}_r{self.tag(i)}", EWI, signed=True)
        lhs_w = w
        fl.append(flag_if(f"{vb} == 0", "div_zero"))
        dz = f"{w}'d0" if dz_zero else (ones(w) if op in ("div", "quot") else pa)
        if self.bcd and ("bcd_div", self.tag(i), 0) in self.lib_inst:
            # the decimal divider takes the digit patterns and gives the quotient and remainder digits
            la, lb, lq, lr = self.lib_inst[("bcd_div", self.tag(i), 0)]
            blk.stmt(f"{la} = {pa}; {lb} = {pb};")
            self.put(set_idx, i, lhs_w, f"({vb} == 0) ? {dz} : {lq if op in ('div', 'quot') else lr}")
            return
        lib = self.lib_inst.get(("divider", self.tag(i), 0))
        if lib is not None:
            # the library divider takes the magnitudes (the dividend with the mode's fraction bits shifted in);
            # the quotient truncated toward zero takes the signs' xor, the remainder the dividend's sign
            la, lb, lq, lr = lib
            neg_a, neg_b = f"({va} < 0)", f"({vb} < 0)"
            shift = f" <<< {F}" if F and op in ("div", "quot") else ""
            blk.stmt(f"{la} = ({neg_a} ? -{va} : {va}){shift}; {lb} = {neg_b} ? -{vb} : {vb};")
            qm = f"$signed({{{{({EWI}-{w + F}){{1'b0}}}}, {lq}}})"
            rmag = f"$signed({{{{({EWI}-{w}){{1'b0}}}}, {lr}}})"
            blk.stmt(f"{q} = ({vb} == 0) ? 0 : (({neg_a} ^ {neg_b}) ? -{qm} : {qm});")
            blk.stmt(f"{rm} = ({vb} == 0) ? 0 : ({neg_a} ? -{rmag} : {rmag});")
        if op in ("div", "quot") and F:
            # fixed point: the exact quotient rounded to F fraction bits, saturated
            if lib is None:
                blk.stmt(f"{q} = ({va} * {EWI}'sd{1 << F}) / {vb};")
                blk.stmt(f"{rm} = ({va} * {EWI}'sd{1 << F}) % {vb};")
            t = self.tmp(f"{p}_o{self.oi}dq{set_idx}_{self.tag(i)}", EWI, signed=True)
            sb = self.sr_bits
            srge = "1" if self.conv.sr_compare == "ge" else "0"
            blk.stmt(f"{t} = {q} + {p}_divround({q}, {rm}, {vb}, rnd, {self.word(r)});")
            self.lib.function(f'''
  // the rounding increment of a truncated quotient q with remainder r (sign of the dividend)
  function automatic signed [{EWI-1}:0] {p}_divround(input signed [{EWI-1}:0] q, input signed [{EWI-1}:0] r, input signed [{EWI-1}:0] b, input [2:0] rnd, input [{sb-1}:0] word);
    logic s; logic [{EWI-1}:0] ar, ab; logic up, inexact;
    s = (r < 0) != (b < 0); if (r == 0) s = q < 0;
    ar = (r < 0) ? -r : r; ab = (b < 0) ? -b : b; inexact = ar != 0;
    case (rnd)
      3'd0: up = (2 * ar > ab) || (2 * ar == ab && q[0]);
      3'd1: up = 1'b0;
      3'd2: up = inexact && s;
      3'd3: up = inexact && !s;
      3'd4: up = inexact && ({srge} ? ({p}_divfrac(ar, ab) >= word) : ({p}_divfrac(ar, ab) > word));
      default: up = inexact;
    endcase
    {p}_divround = up ? (s ? -{EWI}'sd1 : {EWI}'sd1) : {EWI}'sd0;
  endfunction''')
            self.put(set_idx, i, lhs_w, f"({vb} == 0) ? {dz} : {p}_sat({t})")
            fl.append(flag_if(f"{vb} != 0 && {rm} != 0", "inexact"))
            fl.append(f"(({vb} != 0 && ({t} > {EWI}'sd{mx} || {t} < {self.min_lit()})) ? "
                      f"({flag('overflow')} | {flag('inexact')}) : {NOFLAG})")
            return
        # integer quotient and remainder (truncating operators; floor by correction)
        if lib is None:
            blk.stmt(f"{q} = ({vb} == 0) ? 0 : {va} / {vb};")
            blk.stmt(f"{rm} = ({vb} == 0) ? 0 : {va} % {vb};")
        if floor_q:
            blk.stmt(f"if ({rm} != 0 && (({rm} < 0) != ({vb} < 0))) begin {q} = {q} - 1; {rm} = {rm} + {vb}; end")
        if op in ("div", "quot"):
            res = f"{p}_wrap({q})"
            fl.append(f"(({vb} != 0 && ({q} > {EWI}'sd{mx} || {q} < {self.min_lit()})) ? "
                      f"({flag('overflow')} | {flag('int_overflow')}) : {NOFLAG})")
        else:
            res = f"{p}_enc({rm})"
            if preserve:
                res = f"(({rm} == 0) ? {self.zero_pat(f'({sa} ^ {sbit})')} : {res})"
        self.put(set_idx, i, lhs_w, f"({vb} == 0) ? {dz} : {res}")

    # ---- conversions ------------------------------------------------------------------
    def emit_cvt(self, op: str, tgt, set_idx: int, src: str, base: int):
        """cvt from an integer or fixed mode: through the engine (X from
        the magnitude, then the target pack); block targets group values."""
        p, count = self.p, self.count
        if isinstance(tgt, BlockFormat):
            self.cvt_to_block(op, tgt, set_idx, src, base, count)
            return
        ttag = fmt_tag(tgt)
        tw = tgt.width
        for i in self.lanes:
            r = base + i
            t = self.tmp(f"{p}_o{self.oi}c{set_idx}_{self.tag(i)}", FW + tw)
            converter = self.lib_inst.get(("converter", self.tag(i), set_idx, tgt.name))
            if converter:
                x, word, flags, bits = converter
                self.blk.stmt(f"{x} = {self.x(src, i)}; {word} = {self.word(r)}; {t} = {{{flags}, {bits}}};")
            else:
                self.blk.stmt(f"{t} = {p}_pack_{ttag}({self.x(src, i)}, rnd, {self.word(r)}, ftz);")
            out_bits = core_to_x87(t) if isinstance(tgt, X87Format) else f"{t}[{tw-1}:0]"
            core = _core(tgt)
            pw = core.width
            fl = f"{t}[{FW+pw-1}:{pw}]"
            if isinstance(core, FloatFormat) and not core.signed:
                negative = f"({p}_v{src}{self.tag(i)} < 0)"
                invalid = self.nan_pattern(tgt) if core.has_nan else f"{tw}'d{0 if self.conv.invalid_result == 'zero' else core._max_finite_bits()}"
                out_bits = f"{negative} ? {invalid} : {out_bits}"
                invalid_flags = flag('invalid') + " | " + flag('nan' if core.has_nan else 'inexact')
                fl = f"{negative} ? ({invalid_flags}) : ({fl})"
            self.put(set_idx, i, tw, out_bits)
            self.put_flags(r, fl, set_idx)
