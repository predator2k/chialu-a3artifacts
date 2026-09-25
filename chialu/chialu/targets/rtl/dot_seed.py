"""The behavioral reference module of a chialu.VecDotAcc spec in
SystemVerilog (the seed, and the checker's duplicate). Per mode: the
operands are unpacked through the sv_engine of the mode, every product
is exact (mulx) and the fused sum lands in a wide two's-complement
accumulator whose lsb is the smallest product or c weight (a Kulisch
accumulator), then one rounding into format_d; the sequential contract
rounds every product and every addition through pack/unpack of
format_d. A block format_d quantizes the S sums with the engine's
quantizer."""
from __future__ import annotations

import re

from chialu.targets.rtl.engine import (FLAG_ORDER, FW, RND, Conventions, Engine,
                                       flag_bit, _core)
from chialu.targets.rtl.engine import FORCE_NONE, FORCE_RAZ, FORCE_RTZ, fmt_tag as _tag
from chialu.targets.rtl.families.module_library import ModuleLibrary, collect_modules, dedupe_modules
from chialu.verify import dot_ref as D
from chialu.verify.formats import (BlockFormat, FixedFormat, FloatFormat,
                                    IntFormat, PositFormat, ScaledIntFormat,
                                    X87Format, _floor_log2, _mask)

def _exp_range(fmt):
    """(lsb exponent of the smallest nonzero value, exponent of the
    largest finite value + 1) of a scalar or block format's values."""
    if isinstance(fmt, BlockFormat):
        lo_e, hi_e = _exp_range(fmt.elem)
        lo_s, hi_s = _exp_range(fmt.scale)
        return lo_e + lo_s, hi_e + hi_s
    c = _core(fmt)
    if isinstance(c, FloatFormat):
        if c.exp_only:
            return -c.bias, c._top() - c.bias + 1
        return 1 - c.bias - c.man_bits, _floor_log2(c.max_finite()) + 1
    if isinstance(c, PositFormat):
        e = (c.width - 2) << c.es
        return -e, e + 1
    F = getattr(c, "frac_bits", 0)
    return -F, c.width - F + 1


def _sw_of(fmt):
    if isinstance(fmt, BlockFormat):
        e = fmt.elem
        return (e.man_bits + 1 if isinstance(e, FloatFormat) else e.width) + fmt.scale.man_bits + 1
    c = _core(fmt)
    if isinstance(c, FloatFormat):
        return c.man_bits + 1
    if isinstance(c, PositFormat):
        return c.width
    return c.width + 1


def _ew_of(fmt):
    if isinstance(fmt, BlockFormat):
        return max(_ew_of(fmt.elem), _ew_of(fmt.scale))
    c = _core(fmt)
    if isinstance(c, FloatFormat):
        return c.exp_bits + 8
    if isinstance(c, PositFormat):
        return c.es + (c.width - 1).bit_length() + 6
    return 8 + getattr(c, "frac_bits", 0).bit_length() + c.width.bit_length()


def frame_of(fab, fc, fd, n_products: int, accumulate: bool, sr_bits: int, sr: bool, conv=None, p: str = "m0",
             precision_formats=()):
    """(engine, AW, lo): the engine of a mode and its exact accumulator
    frame: lsb 2^lo is the smallest product or c weight, AW bits cover the
    largest sum (the family library generates its dot modules for it)."""
    e = Engine(p, fab, sr_bits, sr, targets=[fd] + ([fc] if accumulate else []), conv=conv or Conventions())
    float_destination = fd.elem if isinstance(fd, BlockFormat) else _core(fd)
    if isinstance(float_destination, FloatFormat):
        # zero_sign is an integer encoding convention. Floating-point
        # results retain the IEEE zero sign computed by the dot contract.
        e.tokens["ZERO_POSITIVE"] = "0"
    if accumulate:
        e.widen(_sw_of(fc))
        e.widen_exp(_ew_of(fc))
    e.widen(_sw_of(fd))
    e.widen_exp(_ew_of(fd))
    e.widen_exp(_ew_of(fab) + 2)
    for fmt in precision_formats:
        e.widen(_sw_of(fmt))
        e.widen_exp(_ew_of(fmt) + 2)
    lo_ab, hi_ab = _exp_range(fab)
    lo, hi = 2 * lo_ab, 2 * hi_ab + n_products.bit_length() + 1
    if accumulate:
        lo_c, hi_c = _exp_range(fc)
        lo, hi = min(lo, lo_c), max(hi, hi_c + 1)
    return e, max(hi - lo + 3, 2 * e.XW + 3), lo


class DotModeGen:
    def __init__(self, spec, lay, mi, force, family=None):
        self.spec, self.lay, self.mi, self.force = spec, lay, mi, force
        m = lay["modes"][mi]
        self.m = m
        self.p = f"m{mi}"
        self.fab, self.fc, self.fd = m["fab"], m["fc"], m["fd"]
        self.acc = lay["accumulate"]
        self.S = D.n_outputs(m)
        self.n = m["elements"]
        self.np = D.n_products(m)
        self.sr_bits, self.sr = lay["sr_bits"], lay["sr"]
        self.fused = spec.get("dot_contract", "fused") != "sequential"
        self.family = family                       # the declared (family, pins) of the core, or None
        self.round_to_odd = bool(family and family[0] == "bf16_fma_datapath" and
                                 family[1].get("rounding_mode") == "round_to_odd")
        self.library_used: dict = ModuleLibrary()  # strict named SV definitions
        from chialu.targets.rtl.families.dot import internal_formats, validate_unit_binding
        if family:
            validate_unit_binding(spec, m, *family)
        precision_formats = internal_formats(*family) if family else ()
        if family and family[0] == "multi_precision_simd_fma" and family[1].get("shared_rounder", False):
            precision_formats = tuple(fmt for mode in lay["modes"] for fmt in (mode["fab"], mode["fc"], mode["fd"]) if fmt is not None)
        self.precision_formats = precision_formats
        self.shared_round_requests = []
        e, self.AW, self.acc_lo = frame_of(self.fab, self.fc, self.fd, self.np, self.acc, self.sr_bits, self.sr,
                                            Conventions.from_spec(spec), self.p, precision_formats)
        self.eng = e
        if family and family[0] == "fp8_training_datapath" and "unified_internal_format" in family[1]:
            from chialu.targets.rtl.families.fidelity import effective
            effective(family[1], "unified_internal_format", bool(family[1]["unified_internal_format"]),
                      "common e4m3/e5m2 X representation" if family[1]["unified_internal_format"] else "mode-specific X representation",
                      {"SW": e.SW, "XW": e.XW, "EW": e.EW})
        self.lib, self.decl, self.body = [], [], []

    def conv(self, k, default=None):
        return self.spec.get(k, default)

    def lib_text(self):
        e = self.eng
        parts = [e.vdecl(), e.rup_fn(), e.arith()]
        # unpack of ab, c; pack of d (and unpack of d for the sequential contract)
        def unpack(fmt, tag):
            if isinstance(fmt, BlockFormat):
                return e.unpack_block(fmt, tag)
            if isinstance(fmt, (FloatFormat, X87Format)):
                return e.unpack_float(fmt, tag)
            if isinstance(fmt, PositFormat):
                return e.unpack_posit(fmt, tag)
            return e.unpack_int(fmt, tag)

        def pack(fmt, tag):
            if isinstance(fmt, BlockFormat):
                return e.quant_block(fmt, tag)
            if isinstance(fmt, (FloatFormat, X87Format)):
                return e.pack_float(fmt, tag)
            if isinstance(fmt, PositFormat):
                return e.pack_posit(fmt, tag)
            return e.pack_int(fmt, tag)
        parts.append(unpack(self.fab, "ab"))
        if self.acc:
            parts.append(unpack(self.fc, "c"))
        parts.append(pack(self.fd, "d"))
        if not self.fused and not isinstance(self.fd, BlockFormat):
            parts.append(unpack(self.fd, "dd"))
        return "".join(parts)

    # ---- helpers on the accumulator
    def _acc_to_x(self):
        """acc (signed AW bits, lsb 2^lo) -> X: normalized magnitude, sticky."""
        e = self.eng
        p, AW, XW, EW, XT = self.p, self.AW, e.XW, e.EW, e.XT
        return f'''
  function automatic [{XT-1}:0] {p}_acc2x(input signed [{AW-1}:0] acc);
    logic s; logic [{AW-1}:0] mag; logic signed [{EW-1}:0] ex; integer k; logic st;
    s = acc < 0; mag = s ? -acc : acc; ex = {self.acc_lo} + {AW - XW};
    if (mag == 0) {p}_acc2x = {p}_mkx(2'd0, 1'b0, 0, 0, 1'b0);
    else begin
      for (k = {1 << (AW.bit_length() - 1)}; k >= 1; k = k / 2) begin
        if (k < {AW}) begin
          if ((mag >> ({AW} - k)) == 0) begin mag = mag << k; ex = ex - k; end
        end
      end
      st = (mag[{AW - XW - 1}:0] != 0);
      {p}_acc2x = {p}_mkx(2'd0, s, ex, mag[{AW-1}:{AW-XW}], st);
    end
  endfunction'''

    def _x_to_acc_term(self):
        """An exact product {sp, s, exp, sig2} -> its accumulator term."""
        e = self.eng
        p, AW, XW, EW = self.p, self.AW, e.XW, e.EW
        return f'''
  function automatic signed [{AW-1}:0] {p}_term(input s, input signed [{EW-1}:0] ex, input [{2*XW-1}:0] sig2);
    logic [{AW-1}:0] t; logic signed [{EW}:0] sh;
    sh = ex - ({self.acc_lo});
    if (sh >= 0) t = {{{{({AW}-2*{XW}){{1'b0}}}}, sig2}} << sh;
    else t = {{{{({AW}-2*{XW}){{1'b0}}}}, sig2}} >> (-sh);
    {p}_term = s ? -$signed(t) : $signed(t);
  endfunction
  function automatic signed [{AW-1}:0] {p}_termx(input [{e.XT-1}:0] x);
    logic [{AW-1}:0] t; logic signed [{EW}:0] sh;
    sh = $signed(x[{XW+EW}:{XW+1}]) - ({self.acc_lo});
    if (sh >= 0) t = {{{{({AW}-{XW}){{1'b0}}}}, x[{XW}:1]}} << sh;
    else t = {{{{({AW}-{XW}){{1'b0}}}}, x[{XW}:1]}} >> (-sh);
    {p}_termx = x[{e.XT-3}] ? -$signed(t) : $signed(t);
  endfunction'''

    def emit(self):
        L, Dd = self.body, self.decl
        p, e, m = self.p, self.eng, self.m
        fab, fc, fd = self.fab, self.fc, self.fd
        lay = self.lay
        S, n, np_ = self.S, self.n, self.np
        XT, VW, XW, EW, AW = e.XT, e.VW, e.XW, e.EW, self.AW
        d_w = lay["d_w"]
        per_out = D.roundings_per_output(m, self.spec)
        wab = fab.width
        dtag = "d"
        self.lib.append(self._acc_to_x())
        self.lib.append(self._x_to_acc_term())
        Dd.append(f"  logic [{d_w-1}:0] d_{p};")
        from chialu.verify.dot_arch_ref import extra_outputs
        extras = extra_outputs(self.spec)
        for output in extras:
            Dd.append(f"  logic [{d_w-1}:0] {output}_{p};")
            L.append(f"    {output}_{p} = '0;")
        Dd.append(f"  logic [{lay['v_max']*FW-1}:0] fl_{p};")
        L.append(f"    d_{p} = '0; fl_{p} = '0;")
        # operand values: S*n values of ab per operand (expanded elements for blocks)
        nv = S * n
        size_ab = fab.size if isinstance(fab, BlockFormat) else 1
        for src in ("a", "b"):
            for i in range(nv):
                if isinstance(fab, BlockFormat):
                    Dd.append(f"  logic [{size_ab*(VW+1)-1}:0] {p}_u{src}{i};")
                    Dd.append(f"  assign {p}_u{src}{i} = {p}_unpack_ab({src}[{i*wab} +: {wab}], daz);")
                    for j in range(size_ab):
                        k = i * size_ab + j
                        Dd.append(f"  logic [{XT-1}:0] {p}_x{src}{k}; logic {p}_den{src}{k};")
                        Dd.append(f"  assign {p}_x{src}{k} = {p}_x({p}_u{src}{i}[{j*(VW+1)} +: {VW}]);")
                        Dd.append(f"  assign {p}_den{src}{k} = {p}_u{src}{i}[{j*(VW+1)+VW}];")
                else:
                    Dd.append(f"  logic [{VW}:0] {p}_u{src}{i};")
                    arg = f"{src}[{i*wab} +: {wab}]"
                    if isinstance(fab, X87Format):
                        arg = f"{{{src}[{i*wab+79}], {src}[{i*wab+64} +: 15], {src}[{i*wab} +: 63]}}"
                    Dd.append(f"  assign {p}_u{src}{i} = {p}_unpack_ab({arg}, daz);")
                    Dd.append(f"  logic [{XT-1}:0] {p}_x{src}{i}; logic {p}_den{src}{i};")
                    Dd.append(f"  assign {p}_x{src}{i} = {p}_x({p}_u{src}{i}[{VW-1}:0]);")
                    Dd.append(f"  assign {p}_den{src}{i} = {p}_u{src}{i}[{VW}];")
        # c values: S of them
        if self.acc:
            wc = fc.width
            if isinstance(fc, BlockFormat):
                Dd.append(f"  logic [{fc.size*(VW+1)-1}:0] {p}_uc;")
                Dd.append(f"  assign {p}_uc = {p}_unpack_c(c[{fc.width-1}:0], daz);")
                for g in range(S):
                    Dd.append(f"  logic [{XT-1}:0] {p}_xc{g}; logic {p}_denc{g};")
                    Dd.append(f"  assign {p}_xc{g} = {p}_x({p}_uc[{g*(VW+1)} +: {VW}]);")
                    Dd.append(f"  assign {p}_denc{g} = {p}_uc[{g*(VW+1)+VW}];")
            else:
                for g in range(S):
                    Dd.append(f"  logic [{VW}:0] {p}_uc{g};")
                    arg = f"c[{g*wc} +: {wc}]"
                    if isinstance(fc, X87Format):
                        arg = f"{{c[{g*wc+79}], c[{g*wc+64} +: 15], c[{g*wc} +: 63]}}"
                    Dd.append(f"  assign {p}_uc{g} = {p}_unpack_c({arg}, daz);")
                    Dd.append(f"  logic [{XT-1}:0] {p}_xc{g}; logic {p}_denc{g};")
                    Dd.append(f"  assign {p}_xc{g} = {p}_x({p}_uc{g}[{VW-1}:0]);")
                    Dd.append(f"  assign {p}_denc{g} = {p}_uc{g}[{VW}];")
        # per output group
        block_d = isinstance(fd, BlockFormat)
        int_d = isinstance(fd, (IntFormat,)) and not isinstance(fd, ScaledIntFormat) or isinstance(fd, FixedFormat)
        quire_d = isinstance(fd, ScaledIntFormat) and not isinstance(fd, FixedFormat)
        wd = fd.width
        if block_d:
            Dd.append(f"  logic [{S*XT-1}:0] {p}_dxs; logic [{S*FW+wd-1}:0] {p}_dq;")
        # a module whose structure rounds every product and addition to d (the cascade styles of a one-element
        # mode) realizes the sequential contract; the other modules serve the fused contract alone
        lib = self._library_module(block_d) if self.family else None
        for g in range(S):
            terms = list(range(g * np_, (g + 1) * np_))
            wbase = g * per_out
            word = f"sr_rnd[{wbase}*{self.sr_bits} +: {self.sr_bits}]" if self.sr else f"{self.sr_bits}'d0"
            Dd.append(f"  logic signed [{AW-1}:0] {p}_acc{g};")
            Dd.append(f"  logic [1:0] {p}_sp{g}; logic {p}_inf_s{g}, {p}_nan{g}, {p}_inv{g}, {p}_den{g}, {p}_allneg{g}, {p}_anynz{g};")
            if lib is None:
                Dd.append(f"  logic [2*XW+EW+2:0] {p}_pr{g}_[0:{np_-1}];".replace("XW", str(XW)).replace("EW", str(EW)))
                for t in terms:
                    L.append(f"    {p}_pr{g}_[{t - g*np_}] = {p}_mulx({p}_xa{t}, {p}_xb{t});")
            L.append(f"    {p}_nan{g} = 1'b0; {p}_inv{g} = 1'b0; {p}_inf_s{g} = 1'b0; {p}_sp{g} = 2'd0; {p}_allneg{g} = 1'b1; {p}_anynz{g} = 1'b0;")
            L.append(f"    {p}_den{g} = " + " | ".join(f"{p}_dena{t} | {p}_denb{t}" for t in terms) + (f" | {p}_denc{g}" if self.acc else "") + ";")
            if lib is None:
                L.append(f"    {p}_acc{g} = " + (f"{p}_termx({p}_xc{g});" if self.acc else "0;"))
                # specials over the products and c
                for t in terms:
                    pr = f"{p}_pr{g}_[{t - g*np_}]"
                    top = 2 * XW + EW + 2
                    L.append(f"    if ({pr}[{top}:{top-1}] == 2'd1) begin {p}_nan{g} = 1'b1; {p}_inv{g} = {p}_inv{g} | !(({p}_xa{t}[{XT-1}:{XT-2}] == 2'd1) || ({p}_xb{t}[{XT-1}:{XT-2}] == 2'd1)); end")
                    # infinities of opposite signs: the NaN result is an invalid operation (IEEE 754 7.2)
                    L.append(f"    else if ({pr}[{top}:{top-1}] == 2'd2) begin if ({p}_sp{g} == 2'd2 && {p}_inf_s{g} != {pr}[{top-2}]) begin {p}_nan{g} = 1'b1; {p}_inv{g} = 1'b1; end {p}_sp{g} = 2'd2; {p}_inf_s{g} = {pr}[{top-2}]; end")
                    L.append(f"    else begin {p}_acc{g} = {p}_acc{g} + {p}_term({pr}[{top-2}], {pr}[{top-3}:{2*XW}], {pr}[{2*XW-1}:0]); if ({pr}[{2*XW-1}:0] != 0) {p}_anynz{g} = 1'b1; if (!{pr}[{top-2}]) {p}_allneg{g} = 1'b0; end")
            else:
                # the library module sums the finite products and c; the specials are read off the operands
                # (a NaN operand, or an infinity times a zero, is a NaN product; an infinity times a nonzero is
                # an infinite product of the signs' xor)
                self._instantiate(Dd, g, terms, lib, word)
                for output in lib[1].get("extra_outputs", ()):
                    L.append(f"    {output}_{p}[{g*fd.width} +: {fd.width}] = {p}_l_{output}{g};")
                for t in terms:
                    xa, xb = f"{p}_xa{t}", f"{p}_xb{t}"
                    spa, spb = f"{xa}[{XT-1}:{XT-2}]", f"{xb}[{XT-1}:{XT-2}]"
                    za, zb = f"({spa} == 2'd0 && {xa}[{XW}:1] == 0)", f"({spb} == 2'd0 && {xb}[{XW}:1] == 0)"
                    sgn = f"({xa}[{XT-3}] ^ {xb}[{XT-3}])"
                    L.append(f"    if ({spa} == 2'd1 || {spb} == 2'd1 || (({spa} == 2'd2 || {spb} == 2'd2) && ({za} || {zb}))) begin "
                             f"{p}_nan{g} = 1'b1; {p}_inv{g} = {p}_inv{g} | !({spa} == 2'd1 || {spb} == 2'd1); end")
                    L.append(f"    else if ({spa} == 2'd2 || {spb} == 2'd2) begin if ({p}_sp{g} == 2'd2 && {p}_inf_s{g} != {sgn}) begin {p}_nan{g} = 1'b1; {p}_inv{g} = 1'b1; end "
                             f"{p}_sp{g} = 2'd2; {p}_inf_s{g} = {sgn}; end")
                    if not lib[1].get("product_classification"):
                        L.append(f"    else begin if (!{za} && !{zb}) {p}_anynz{g} = 1'b1; if (!{sgn}) {p}_allneg{g} = 1'b0; end")
                if lib[1].get("product_classification"):
                    L.append(f"    {p}_anynz{g} = {p}_product_nonzero{g}; {p}_allneg{g} = {p}_products_negative{g};")
                L.append(f"    {p}_acc{g} = " + (f"{p}_lacc{g};" if lib[1].get("out") == "acc" else f"{p}_termx({p}_ly{g});"))
            if self.acc:
                xc = f"{p}_xc{g}"
                L.append(f"    if ({xc}[{XT-1}:{XT-2}] == 2'd1) {p}_nan{g} = 1'b1;")
                L.append(f"    else if ({xc}[{XT-1}:{XT-2}] == 2'd2) begin if ({p}_sp{g} == 2'd2 && {p}_inf_s{g} != {xc}[{XT-3}]) begin {p}_nan{g} = 1'b1; {p}_inv{g} = 1'b1; end {p}_sp{g} = 2'd2; {p}_inf_s{g} = {xc}[{XT-3}]; end")
                L.append(f"    else begin if ({xc}[{XW}:1] != 0) {p}_anynz{g} = 1'b1; if (!{xc}[{XT-3}]) {p}_allneg{g} = 1'b0; end")
            # IEEE 754: a signalling NaN operand is invalid, a quiet NaN propagates without a flag; a posit
            # NaR stays invalid; the 0 x inf case marked its invalid above
            def snan_of(src: str, fmt_, t: int, width: int, size: int) -> str:
                x = f"{p}_x{src}{t}" if src != "c" else f"{p}_xc{t}"
                is_nan = f"({x}[{XT-1}:{XT-2}] == 2'd1)"
                if isinstance(fmt_, PositFormat):
                    return is_nan
                el = fmt_.elem if isinstance(fmt_, BlockFormat) else fmt_
                core = _core(el) if isinstance(el, (FloatFormat, X87Format)) else None
                if core is None or not core.has_nan or core.man_bits == 0 or not core.has_inf:
                    return "1'b0"
                if isinstance(fmt_, BlockFormat):
                    off = (t // size) * width + (t % size) * el.width
                else:
                    off = t * width
                qbit = 62 if isinstance(el, X87Format) else core.man_bits - 1
                return f"({is_nan} && !{src}[{off + qbit}])"
            if self.acc:
                L.append(f"    if ({snan_of('c', fc, g, wc, fc.size if isinstance(fc, BlockFormat) else 1)}) {p}_inv{g} = 1'b1;")
            for t in terms:
                L.append(f"    if ({snan_of('a', fab, t, wab, size_ab)} || {snan_of('b', fab, t, wab, size_ab)}) {p}_inv{g} = 1'b1;")
            # the X of the result (fused) or the sequential chain
            Dd.append(f"  logic [{XT-1}:0] {p}_xr{g}; logic [{FW+_core(fd).width-1 if not block_d else FW+wd-1}:0] {p}_pk{g};")
            zs = f"({p}_allneg{g} || (rnd == 3'd2 && {p}_anynz{g}))"
            L.append(f"    if ({p}_nan{g}) {p}_xr{g} = {p}_mkx(2'd1, 1'b0, 0, 0, 1'b0);")
            L.append(f"    else if ({p}_sp{g} == 2'd2) {p}_xr{g} = {p}_mkx(2'd2, {p}_inf_s{g}, 0, 0, 1'b0);")
            if lib is not None and lib[1].get("out") == "y":
                # a finite zero result takes the contract's zero-sign rule (a special leaving the module keeps its sign):
                # the fused rule, or the chain's first term's sign under the sequential contract
                t0 = terms[0]
                zs_lib = zs if self.fused else (f"{p}_xc{g}[{XT-3}]" if self.acc else f"({p}_xa{t0}[{XT-3}] ^ {p}_xb{t0}[{XT-3}])")
                L.append(f"    else begin {p}_xr{g} = {p}_ly{g}; if ({p}_ly{g}[{XT-1}:{XT-2}] == 2'd0 && {p}_ly{g}[{XW}:1] == 0 && !{p}_ly{g}[0]) {p}_xr{g}[{XT-3}] = {zs_lib}; end")
            else:
                L.append(f"    else begin {p}_xr{g} = {p}_acc2x({p}_acc{g}); if ({p}_acc{g} == 0) {p}_xr{g}[{XT-3}] = {zs}; end")
            if block_d:
                L.append(f"    {p}_dxs[{g*XT} +: {XT}] = {p}_xr{g};")
                continue
            if not self.fused:
                if lib is None:
                    self._sequential(L, Dd, g, terms, zs)
            invalid_float = f"{p}_nan{g}"
            if isinstance(_core(fd), FloatFormat) and not _core(fd).signed:
                # The numeric packer has no unsigned-negative convention:
                # classify the invalid conversion before it drops the sign.
                # An exact negative zero remains representable as +0.
                xr = f"{p}_xr{g}"
                bad = f"{p}_unsigned_invalid{g}"
                Dd.append(f"  logic {bad};")
                L.append(f"    {bad} = {xr}[{XT-3}] && ({xr}[{XT-1}:{XT-2}] == 2'd2 || (|{xr}[{XW}:1]) || {xr}[0]);")
                L.append(f"    if ({bad}) begin")
                L.append(f"      {xr} = {p}_mkx(2'd1, 1'b0, 0, 0, 1'b0); {p}_inv{g} = 1'b1;")
                L.append("    end")
                invalid_float = f"({invalid_float} || {bad})"
            if int_d or quire_d:
                self._int_d(L, Dd, g, word)
                if lib is not None and lib[1].get("flags"):
                    L.append(f"    fl_{p}[{wbase}*{FW} +: {FW}] = fl_{p}[{wbase}*{FW} +: {FW}] | (({p}_nan{g} || {p}_sp{g} == 2'd2) ? {FW}'d0 : {p}_lfl{g});")
            else:
                pw = _core(fd).width
                if lib is not None and self._library_rounder(Dd, g, lib, word):
                    L.append(f"    {p}_pk{g} = {{{p}_rfl{g}, {p}_rbits{g}}};")
                else:
                    pack_ftz = "1'b0" if self.round_to_odd else "ftz"
                    L.append(f"    {p}_pk{g} = {p}_pack_d({p}_xr{g}, rnd, {word}, {pack_ftz});")
                if self.round_to_odd:
                    L.append(f"    if ({p}_pk{g}[{pw+flag_bit('inexact')}] && {p}_xr{g}[{XT-1}:{XT-2}] == 2'd0) {p}_pk{g}[0] = 1'b1;")
                    L.append(f"    if (ftz && {p}_pk{g}[{fd.man_bits} +: {fd.exp_bits}] == 0 && |{p}_pk{g}[{fd.man_bits-1}:0]) begin")
                    L.append(f"      {p}_pk{g}[{pw+flag_bit('underflow')}] = 1'b1; {p}_pk{g}[{pw+flag_bit('inexact')}] = 1'b1; {p}_pk{g}[{pw-2}:0] = '0;")
                    L.append("    end")
                out_bits = f"{p}_pk{g}[{pw-1}:0]"
                if isinstance(fd, X87Format):
                    out_bits = f"{{{p}_pk{g}[78], {p}_pk{g}[77:63], ({p}_pk{g}[77:63] != 0) ? 1'b1 : 1'b0, {p}_pk{g}[62:0]}}"
                core = _core(fd)
                if isinstance(core, FloatFormat) and not core.has_nan:
                    inv_zero = self.conv("invalid_result") == "zero"
                    maxb = core._max_finite_bits()
                    inv_out = f"{wd}'d0" if inv_zero else (f"{{1'b0, {wd-1}'d{maxb & _mask(wd-1)}}}" if core.signed else f"{wd}'d{maxb}")
                    L.append(f"    d_{p}[{g*wd} +: {wd}] = {invalid_float} ? {inv_out} : {out_bits};")
                    fl = f"({invalid_float} ? (({FW}'d1 << {flag_bit('invalid')}) | ({FW}'d1 << {flag_bit('inexact')})) : {p}_pk{g}[{FW+pw-1}:{pw}])"
                else:
                    L.append(f"    d_{p}[{g*wd} +: {wd}] = {out_bits};")
                    fl = f"{p}_pk{g}[{FW+pw-1}:{pw}]"
                fl += f" | ({p}_inv{g} ? ({FW}'d1 << {flag_bit('invalid')}) : {FW}'d0) | ({p}_den{g} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0)"
                if lib is not None and lib[1].get("flags"):
                    fl += f" | (({p}_nan{g} || {p}_sp{g} == 2'd2) ? {FW}'d0 : {p}_lfl{g})"
                if self.fused:
                    L.append(f"    fl_{p}[{wbase}*{FW} +: {FW}] = {fl};")
                else:
                    L.append(f"    fl_{p}[{wbase}*{FW} +: {FW}] = fl_{p}[{wbase}*{FW} +: {FW}] | ({fl});")
        if block_d:
            words = f"sr_rnd[0 +: {S*self.sr_bits}]" if self.sr else f"{S*self.sr_bits}'d0"
            L.append(f"    {p}_dq = {p}_quant_d({p}_dxs, rnd, {words}, ftz);")
            L.append(f"    d_{p}[{wd-1}:0] = {p}_dq[{wd-1}:0];")
            for g in range(S):
                fl = f"{p}_dq[{wd + g*FW} +: {FW}] | ({p}_inv{g} ? ({FW}'d1 << {flag_bit('invalid')}) : {FW}'d0) | ({p}_den{g} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0)"
                L.append(f"    fl_{p}[{g}*{FW} +: {FW}] = {fl};")

    # ---- the family library
    def _library_module(self, block_d: bool):
        """(name, info) of the declared core family's module for this mode,
        registered for the seed. An incompatible selection raises."""
        from chialu.targets.rtl import families as FAM
        from chialu.targets.rtl.families import dot as DOT
        fam, pins = self.family
        incompatible = {"integer_mac": ("element_op", "product"),
                        "multi_term_fused_dot": ("term_source", "products"),
                        "fused_two_term_dot": ("second_op", "dot2")}
        if fam in incompatible:
            pin, value = incompatible[fam]
            if pins.get(pin, value) != value:
                raise ValueError(f"mode {self.mi}: {fam}.{pin}={pins[pin]!r} is not the dot-product contract")
        self.library_note = ""
        dg = DOT.geom_of(self.fab, self.fc, self.fd, self.np, self.acc, self.sr_bits, self.sr,
                         Conventions.from_spec(self.spec), precision_formats=self.precision_formats)
        from chialu.verify.formats import FloatFormat, parse_format
        mixed = any(isinstance(parse_format(m.get("format_ab", m.get("format"))), (FloatFormat, BlockFormat))
                    for m in self.spec.get("modes", []))
        try:
            name, text, info = DOT.dot_sv(dg, fam, pins, block=isinstance(self.fab, BlockFormat), mixed_unit=mixed)
        except ValueError as e:
            raise ValueError(f"mode {self.mi}: requested dot family {fam} cannot be generated: {e}") from e
        info = dict(info, out=dg.out, intg=dg.intg, pins=pins, family=fam)
        wanted = self.spec.get("dot_contract", "fused")
        actual = info.get("contract") or "fused"
        from chialu.verify.truncated_multiplier_ref import APPROXIMATE_FAMILIES
        approximate_children = {path: value for path, value in pins.items()
                                if path.endswith(".family") and value in APPROXIMATE_FAMILIES}
        if approximate_children:
            actual = info["contract"] = "architecture"
            info["approximate_components"] = approximate_children
        if wanted == "fused" and actual == "architecture":
            # the last defense behind the dot_contract_architecture rules of chialu/behavior_rules.py, which remove
            # these families and members from a fused or sequential unit's menu with the reason
            raise ValueError(f"mode {self.mi}: {fam} changes intermediate values and requires an explicit architecture contract")
        if wanted == "sequential" and actual != "sequential":
            # A one-product cascade with the same fixed product and final
            # rounding implements the unit's existing sequential contract.
            cascade = fam in ("bridge_fma", "mixed_precision_cascade_fma") and actual == "architecture"
            required_mode = "RTZ" if pins.get("cascade_product_rounding") == "truncate" else "RNE"
            if not (cascade and self.spec["rounding"] == [required_mode]):
                raise ValueError(f"mode {self.mi}: requested dot family {fam} has no matching sequential rounding contract")
        for n_, t_ in FAM.module_texts(name, text).items():
            collect_modules(self.library_used, ((n_, t_),))
        self.library_note = f"mode {self.mi}: family {fam} realized by the library module {name}" + \
            (f" ({info['contract']} contract)" if info.get("contract") else "")
        return name, info

    def _instantiate(self, Dd, g, terms, lib, word):
        """The library module of one output group: its operand buses (the
        group's operand X's, or the raw operand slices of an integer mode),
        its c, its rounding inputs, and its result wire."""
        name, info = lib
        p, e, fab, fc = self.p, self.eng, self.fab, self.fc
        XT, AW = e.XT, self.AW
        np_ = self.np
        conns = []
        if info["intg"]:
            wab = fab.width
            Dd.append(f"  logic [{np_*wab-1}:0] {p}_la{g}, {p}_lb{g};")
            for k, t in enumerate(terms):
                Dd.append(f"  assign {p}_la{g}[{k*wab} +: {wab}] = a[{t*wab} +: {wab}]; assign {p}_lb{g}[{k*wab} +: {wab}] = b[{t*wab} +: {wab}];")
            conns += [f".a({p}_la{g})", f".b({p}_lb{g})"]
            if self.acc:
                wc = fc.width
                conns.append(f".c(c[{g*wc} +: {wc}])")
        else:
            Dd.append(f"  logic [{np_*XT-1}:0] {p}_lxa{g}, {p}_lxb{g};")
            for k, t in enumerate(terms):
                Dd.append(f"  assign {p}_lxa{g}[{k*XT} +: {XT}] = {p}_xa{t}; assign {p}_lxb{g}[{k*XT} +: {XT}] = {p}_xb{t};")
            conns += [f".xa({p}_lxa{g})", f".xb({p}_lxb{g})"]
            if self.acc:
                conns.append(f".xc({p}_xc{g})")
        if info.get("rnd"):
            conns.append(".rnd(rnd)")
            text = self.library_used[name]
            header = text[text.find("\nmodule "):].split(");", 1)[0]          # the port list alone
            if re.search(r"\bword\b", header):
                conns.append(f".word({word})")
        if info.get("flags"):
            Dd.append(f"  logic [{FW-1}:0] {p}_lfl{g};")
            conns.append(f".fl({p}_lfl{g})")
        if info.get("product_classification"):
            for field in ("product_nonzero", "products_negative"):
                Dd.append(f"  logic {p}_{field}{g};")
                conns.append(f".{field}({p}_{field}{g})")
        if info.get("extra_outputs"):
            conns.append(".ftz(ftz)")
            for output in info["extra_outputs"]:
                Dd.append(f"  logic [{self.fd.width-1}:0] {p}_l_{output}{g};")
                conns.append(f".{output}({p}_l_{output}{g})")
        if info["out"] == "acc":
            Dd.append(f"  logic signed [{AW-1}:0] {p}_lacc{g};")
            conns.append(f".acc({p}_lacc{g})")
        else:
            Dd.append(f"  logic [{XT-1}:0] {p}_ly{g};")
            conns.append(f".y({p}_ly{g})")
        Dd.append(f"  // core.family {info['family']}: output group {g} realized by the library module {name}")
        Dd.append(f"  {name} u_{p}_dot{g} ({', '.join(conns)});")

    def _library_rounder(self, Dd, g, lib, word) -> bool:
        """The library rounder of the family's `round` component (or of a
        module whose value leaves already rounded) packs a float d. Every
        accumulator family carries that component (`_acc_tail` in
        `chialu.spaces.fma_dot_spaces`), so the one rounding of the dot
        contract is a library module rather than the engine's pack_d; a
        block, x87 or integer destination keeps pack_d."""
        from chialu.targets.rtl import families as FAM
        from chialu.targets.rtl.families.fp import Geom
        name, info = lib
        fd = self.fd
        core = _core(fd)
        if isinstance(fd, (BlockFormat, X87Format)) or not isinstance(core, FloatFormat):
            return False
        pins = info.get("pins") or {}
        if info.get("family") == "multi_precision_simd_fma" and pins.get("shared_rounder", False):
            p = self.p
            Dd.append(f"  logic [{FW-1}:0] {p}_rfl{g}; logic [{core.width-1}:0] {p}_rbits{g};")
            self.shared_round_requests.append((g, word))
            return True
        if not (info.get("rounded") or "round.family" in pins):
            return False
        rpins = {"round.family": str(pins.get("round.family", "increment_adder"))}
        for k, v in pins.items():
            if k.startswith("round.") and k != "round.family":
                rpins[k] = v
        e = self.eng
        m = FAM.fp_module("rounder", "dedicated_per_op", rpins, Geom.of_engine(e), fmt=core, M=core.man_bits, bias=core.bias,
                          tokens=e.tokens)
        if m is None:
            raise ValueError(f"mode {self.mi}: requested dot round component {rpins['round.family']} "
                             f"has no implementation for {core.name}")
        for n_, t_ in FAM.module_texts(m.name, m.text).items():
            collect_modules(self.library_used, ((n_, t_),))
        p = self.p
        Dd.append(f"  logic [{FW-1}:0] {p}_rfl{g}; logic [{core.width-1}:0] {p}_rbits{g};")
        Dd.append(f"  // the round component ({rpins['round.family']}) of core.family {info['family']}: the library rounder packs d")
        ftz_arg = "1'b0" if self.round_to_odd else "ftz"
        Dd.append(f"  {m.name} u_{p}_round{g} (.x({p}_xr{g}), .rnd(rnd), .word({word}), .ftz({ftz_arg}), .fl({p}_rfl{g}), .bits({p}_rbits{g}));")
        return True

    def _int_d(self, L, Dd, g, word):
        """Integer, fixed or quire d: the exact sum rounded to the d lsb
        (exact for integer operands), then wrapped or saturated."""
        p, fd, AW = self.p, self.fd, self.AW
        wd = fd.width
        F = getattr(fd, "frac_bits", 0)
        quire = isinstance(fd, ScaledIntFormat) and not isinstance(fd, FixedFormat)
        sat = (self.conv("quire_overflow", "wrap") == "saturate") if quire else (self.conv("overflow", "wrap") == "saturate")
        mx, mn = fd.max_int, fd.min_int
        sh = self.acc_lo + F                       # acc * 2^lo in units of 2^-F
        sb = self.sr_bits
        if f"{p}_rshift(" not in "".join(self.lib):
            self.lib.append(f'''
  function automatic signed [{AW-1}:0] {p}_rshift(input signed [{AW-1}:0] v, input integer f, input [2:0] rnd, input [{sb-1}:0] word);
    logic s; logic [{AW-1}:0] mag, keep, rest, halfv; logic [{AW+sb}:0] fint; logic up, inexact;
    s = v < 0; mag = s ? -v : v;
    if (f <= 0) {p}_rshift = v;
    else begin
      keep = mag >> f; rest = mag & ((({AW}'d1) << f) - 1); halfv = ({AW}'d1) << (f - 1);
      inexact = rest != 0;
      fint = (f >= {sb}) ? (rest >> (f - {sb})) : (rest << ({sb} - f));
      case (rnd)
        3'd0: up = (rest > halfv) || (rest == halfv && keep[0]);
        3'd1: up = 1'b0;
        3'd2: up = inexact && s;
        3'd3: up = inexact && !s;
        3'd4: up = inexact && ({"1" if self.conv("sr_compare") == "ge" else "0"} ? (fint >= word) : (fint > word));
        default: up = inexact;
      endcase
      keep = keep + up;
      {p}_rshift = s ? -$signed(keep) : $signed(keep);
    end
  endfunction
  function automatic {p}_inexact(input signed [{AW-1}:0] v, input integer f);
    logic [{AW-1}:0] mag;
    mag = (v < 0) ? -v : v;
    {p}_inexact = (f <= 0) ? 1'b0 : ((mag & ((({AW}'d1) << f) - 1)) != 0);
  endfunction''')
        Dd.append(f"  logic signed [{AW-1}:0] {p}_q{g}; logic [{wd-1}:0] {p}_e{g}; logic {p}_ovf{g}, {p}_inx{g};")
        if sh >= 0:
            L.append(f"    {p}_q{g} = {p}_acc{g} <<< {sh}; {p}_inx{g} = 1'b0;")
        else:
            L.append(f"    {p}_q{g} = {p}_rshift({p}_acc{g}, {-sh}, rnd, {word}); {p}_inx{g} = {p}_inexact({p}_acc{g}, {-sh});")
        L.append(f"    {p}_ovf{g} = ({p}_q{g} > {AW}'sd{mx}) || ({p}_q{g} < {'-' + str(AW) + chr(39) + 'sd' + str(-mn) if mn < 0 else '0'});")
        enc = fd.encoding
        # encode: wrap (low bits) or saturate
        if sat:
            L.append(f"    {p}_q{g} = ({p}_q{g} > {AW}'sd{mx}) ? {AW}'sd{mx} : ({p}_q{g} < {'-' + str(AW) + chr(39) + 'sd' + str(-mn) if mn < 0 else '0'}) ? {'-' + str(AW) + chr(39) + 'sd' + str(-mn) if mn < 0 else '0'} : {p}_q{g};")
        if enc in ("twos_complement", "unsigned"):
            L.append(f"    {p}_e{g} = {p}_q{g}[{wd-1}:0];")
        elif enc == "ones_complement":
            L.append(f"    {p}_e{g} = ({p}_q{g} < 0) ? ~((-{p}_q{g}) & {{{wd}{{1'b1}}}}) : {p}_q{g}[{wd-1}:0];")
        elif enc == "sign_magnitude":
            L.append(f"    {p}_e{g} = ({p}_q{g} < 0) ? (((-{p}_q{g}) & {{{wd-1}{{1'b1}}}}) | ({wd}'d1 << {wd-1})) : {p}_q{g}[{wd-1}:0];")
        else:
            raise SystemExit("derived seed: a BCD d is not generated")
        # specials into an integer d: NaN -> nan_to_int (a quire: its NaR pattern), inf -> extremes
        nti = self.conv("nan_to_int", "zero")
        nan_val = mn if isinstance(fd, ScaledIntFormat) and not isinstance(fd, FixedFormat) else {"zero": 0, "max": mx, "min": mn}[nti]
        nan_pat = IntFormat.encode(fd, nan_val) if isinstance(fd, ScaledIntFormat) else fd.encode(nan_val)
        mx_pat = IntFormat.encode(fd, mx) if isinstance(fd, ScaledIntFormat) else fd.encode(mx)
        mn_pat = IntFormat.encode(fd, mn) if isinstance(fd, ScaledIntFormat) else fd.encode(mn)
        L.append(f"    d_{p}[{g*wd} +: {wd}] = {p}_nan{g} ? {wd}'d{nan_pat} : ({p}_sp{g} == 2'd2) ? ({p}_inf_s{g} ? {wd}'d{mn_pat} : {wd}'d{mx_pat}) : {p}_e{g};")
        fl = (f"(({p}_nan{g} || {p}_sp{g} == 2'd2) ? ({FW}'d1 << {flag_bit('invalid')}) : "
              f"(({p}_inx{g} ? ({FW}'d1 << {flag_bit('inexact')}) : {FW}'d0) | ({p}_ovf{g} ? (({FW}'d1 << {flag_bit('overflow')}) | ({FW}'d1 << {flag_bit('inexact')})) : {FW}'d0)))")
        fl += f" | ({p}_inv{g} ? ({FW}'d1 << {flag_bit('invalid')}) : {FW}'d0) | ({p}_den{g} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0)"
        per_out = D.roundings_per_output(self.m, self.spec)
        L.append(f"    fl_{p}[{g*per_out}*{FW} +: {FW}] = {fl};")

    def _sequential(self, L, Dd, g, terms, zs):
        """Sequential contract for a scalar (non-integer) d: products
        rounded to d, then added one at a time (c first)."""
        p, e, fd = self.p, self.eng, self.fd
        XT, XW, EW = e.XT, e.XW, e.EW
        pw = _core(fd).width
        per_out = D.roundings_per_output(self.m, self.spec)
        wbase = g * per_out
        k = 0
        Dd.append(f"  logic [{XT-1}:0] {p}_s{g}; logic [{FW+pw-1}:0] {p}_sp{g}_k; logic [{XT-1}:0] {p}_px{g}_[0:{len(terms)-1}];")
        for idx, t in enumerate(terms):
            pr = f"{p}_pr{g}_[{idx}]"
            top = 2 * XW + EW + 2
            word = f"sr_rnd[{wbase + k}*{self.sr_bits} +: {self.sr_bits}]" if self.sr else f"{self.sr_bits}'d0"
            # the exact product as an X (top XW bits + sticky)
            L.append(f"    {p}_px{g}_[{idx}] = {p}_mul({p}_xa{t}, {p}_xb{t});")
            L.append(f"    {p}_sp{g}_k = {p}_pack_d({p}_px{g}_[{idx}], rnd, {word}, ftz);")
            L.append(f"    fl_{p}[{wbase}*{FW} +: {FW}] = fl_{p}[{wbase}*{FW} +: {FW}] | {p}_sp{g}_k[{FW+pw-1}:{pw}];")
            L.append(f"    {p}_px{g}_[{idx}] = {p}_x({p}_unpack_dd({p}_sp{g}_k[{pw-1}:0], 1'b0));")
            # a zero product keeps the sign of the packed pattern (the unpack of a zero carries no sign)
            L.append(f"    if ({p}_px{g}_[{idx}][{XT-1}:{XT-2}] == 2'd0 && {p}_px{g}_[{idx}][{XW}:1] == 0 && !{p}_px{g}_[{idx}][0]) "
                     f"{p}_px{g}_[{idx}][{XT-3}] = {p}_sp{g}_k[{pw-1}];")
            k += 1
        if self.acc:
            L.append(f"    {p}_s{g} = {p}_xc{g};")
            start = 0
        else:
            L.append(f"    {p}_s{g} = {p}_px{g}_[0];")
            start = 1
        Dd.append(f"  logic {p}_zsa{g};")
        L.append(f"    {p}_zsa{g} = {p}_s{g}[{XT-3}];")
        for idx in range(start, len(terms)):
            word = f"sr_rnd[{wbase + k}*{self.sr_bits} +: {self.sr_bits}]" if self.sr else f"{self.sr_bits}'d0"
            # a zero sum carries the sign of the chain's first term (c, or the first product), as the reference does
            L.append(f"    {p}_s{g} = {p}_add({p}_s{g}, {p}_px{g}_[{idx}], 1'b0);")
            L.append(f"    if ({p}_s{g}[{XT-1}:{XT-2}] == 2'd0 && {p}_s{g}[{XW}:1] == 0 && !{p}_s{g}[0]) {p}_s{g}[{XT-3}] = {p}_zsa{g};")
            L.append(f"    {p}_sp{g}_k = {p}_pack_d({p}_s{g}, rnd, {word}, ftz);")
            L.append(f"    fl_{p}[{wbase}*{FW} +: {FW}] = fl_{p}[{wbase}*{FW} +: {FW}] | {p}_sp{g}_k[{FW+pw-1}:{pw}];")
            L.append(f"    {p}_s{g} = {p}_x({p}_unpack_dd({p}_sp{g}_k[{pw-1}:0], 1'b0));")
            L.append(f"    if ({p}_s{g}[{XT-1}:{XT-2}] == 2'd0 && {p}_s{g}[{XW}:1] == 0 && !{p}_s{g}[0]) {p}_s{g}[{XT-3}] = {p}_sp{g}_k[{pw-1}];")
            k += 1
        # a NaN or infinite operand set keeps the fused special result and its flags
        L.append(f"    if (!{p}_nan{g} && {p}_sp{g} != 2'd2) {p}_xr{g} = {p}_s{g}; else fl_{p}[{wbase}*{FW} +: {FW}] = 0;")


def dot_ref_module(spec: dict, name: str = "dot_core", force: int = FORCE_NONE, family=None) -> str:
    """The dot module of a spec; `family` is the declared (family, pins)
    of the core (`core.family`, fma_dot_spaces), None for the checker's
    reference copy."""
    spec = D.normalize_dot_spec(spec)
    if spec.get("dot_contract") == "architecture":
        from chialu.verify.dot_arch_ref import selection
        selected = selection(spec)
        if family is not None:
            from chialu.verify.dot_arch_ref import resolved_architecture
            actual = resolved_architecture({"family": family[0], "pins": dict(family[1])}) if family[0] == selected[0] else None
            if actual is None or any(actual["pins"].get(key) != val for key, val in selected[1].items()):
                raise ValueError("selected dot family/pins differ from the explicit architecture golden contract")
        if family is None:
            family = selected
    lay = D.dot_layout(spec)
    D.validate_dot_modes(lay["modes"], lay["accumulate"])
    modes = lay["modes"]
    ports = list(lay["core_in"]) + list(lay["core_out"])
    L = [f"// {name}: behavioral reference derived from the instance (chialu.VecDotAcc, "
         f"{spec['dot_contract']} contract). Every mode computes the verify layer's exact semantics."]
    if family:
        L.append(f"// core.family: {family[0]}" + (f" ({', '.join(f'{k}={v}' for k, v in family[1].items())})" if family[1] else ""))
    decl_ports = [f"  {'input ' if pt.direction == 'in' else 'output'} logic [{pt.width-1}:0] {pt.name}" for pt in ports]
    L += [f"module {name} (", ",\n".join(decl_ports), ");"]
    rnds = list(spec["rounding"])
    if len(rnds) > 1:
        L.append("  logic [2:0] rnd_sel;")
        L.append("  always_comb begin case (rounding_sel)")
        for k, mname in enumerate(rnds):
            L.append(f"    {max(1, (len(rnds)-1).bit_length())}'d{k}: rnd_sel = 3'd{RND[mname]};")
        L.append(f"    default: rnd_sel = 3'd{RND[rnds[0]]}; endcase end")
    else:
        L.append(f"  logic [2:0] rnd_sel; assign rnd_sel = 3'd{RND[rnds[0]]};")
    L.append(f"  logic [2:0] rnd; assign rnd = {'3' + chr(39) + 'd1' if force == FORCE_RTZ else '3' + chr(39) + 'd5' if force == FORCE_RAZ else 'rnd_sel'};")
    for nm, port in (("daz", "daz_in"), ("ftz", "ftz_out")):
        vals = list(spec[port])
        if len(vals) > 1:
            L.append(f"  logic {nm}; assign {nm} = {port}_sel[0] ? 1'b{1 if vals[1] else 0} : 1'b{1 if vals[0] else 0};")
        else:
            L.append(f"  logic {nm}; assign {nm} = 1'b{1 if vals[0] else 0};")
    gens = [DotModeGen(spec, lay, mi, force, family) for mi in range(len(modes))]
    for g in gens:
        lib = g.lib_text()
        g.emit()
        L.append(lib)
        L += g.lib
        L += g.decl
    if family and family[0] == "multi_precision_simd_fma":
        from chialu.targets.rtl.families.fidelity import effective, shared
        requested_sharing = family[1].get("shared_rounder", False)
        if requested_sharing:
            if len(gens) < 2 or any(len(g.shared_round_requests) != 1 for g in gens):
                raise ValueError("shared_rounder requires at least two mutually exclusive modes with scalar float outputs")
            if len({g.fd.name for g in gens}) < 2:
                raise ValueError("shared_rounder target must exercise at least two destination formats")
            from chialu.targets.rtl.families.fp_shared import shared_sv
            from chialu.targets.rtl.families.fp import Geom
            from chialu.targets.rtl import families as FAM
            geometry = Geom.of_engine(gens[0].eng)
            if any(Geom.of_engine(g.eng).tag() != geometry.tag() for g in gens):
                raise ValueError("shared_rounder modes must use one common internal X geometry")
            name_, text_, witnesses = shared_sv("rounder", [g.fd for g in gens], geometry, "shared_across_formats",
                                                {"round.family": "increment_adder"}, gens[0].eng.tokens)
            conns = [".mode(mode)"]
            for mi, gen in enumerate(gens):
                index, word = gen.shared_round_requests[0]
                conns += [f".f{mi}_x({gen.p}_xr{index})", f".f{mi}_rnd(rnd)", f".f{mi}_word({word})", f".f{mi}_ftz(ftz)",
                          f".f{mi}_fl({gen.p}_rfl{index})", f".f{mi}_bits({gen.p}_rbits{index})"]
            L.append(f"  {name_} u_dot_shared_rounder ({', '.join(conns)});")
            gens[0].library_used.update(FAM.module_texts(name_, text_))
            shared("core", "dot rounder across modes", witnesses, [f"m{mi}" for mi in range(len(gens))],
                   "selected rounding cells receive mode-multiplexed inputs")
        effective(family[1], "shared_rounder", bool(requested_sharing),
                  "physical rounding cells shared across modes" if requested_sharing else "independent mode rounders")
    library_used = ModuleLibrary()
    for g in gens:
        library_used.update(g.library_used)
    if family:
        notes = [g.library_note for g in gens if getattr(g, "library_note", "")]
        for k, note in enumerate(notes):
            L.insert(2 + k, f"// {note}")
        if library_used:
            L.insert(2 + len(notes), f"// LIBRARY: {', '.join(sorted(library_used))} (chialu.targets.rtl.families: the modules the core "
                                     f"instantiates; their text follows the core)")
    for g in gens:
        L.append("  always_comb begin")
        L += g.body
        L.append("  end")
    v_max = lay["v_max"]
    from chialu.verify.dot_arch_ref import extra_outputs
    extras = extra_outputs(spec)
    L.append(f"  logic [{v_max*FW-1}:0] fl_all;")
    if len(modes) > 1:
        mdw = max(1, (len(modes) - 1).bit_length())
        L.append("  always_comb begin")
        L.append("    case (mode)")
        for mi in range(len(modes)):
            extra_select = " ".join(f"{key} = {key}_m{mi};" for key in extras)
            L.append(f"      {mdw}'d{mi}: begin d = d_m{mi}; fl_all = fl_m{mi}; {extra_select} end")
        extra_zero = " ".join(f"{key} = '0;" for key in extras)
        L.append(f"      default: begin d = '0; fl_all = '0; {extra_zero} end")
        L.append("    endcase")
        L.append("  end")
    else:
        L.append("  assign d = d_m0;")
        L.append("  assign fl_all = fl_m0;")
        for key in extras:
            L.append(f"  assign {key} = {key}_m0;")
    flags = lay["flags"]
    if flags:
        nf = len(flags)
        for r in range(v_max):
            for j, fname in enumerate(flags):
                L.append(f"  assign flags[{r*nf+j}] = fl_all[{r*FW + flag_bit(fname)}];")
    L.append("endmodule")
    if library_used:
        L.append("// ---- the family library modules the core instantiates (chialu/targets/rtl/families; fixed text, "
                 "replaced by editing the instances)")
        L += [library_used[k] for k in sorted(library_used)]
    return dedupe_modules("\n".join(L) + "\n")


def _checked_dot_seed(function):
    from functools import wraps
    from chialu.targets.rtl.families.selection import SelectionTrace, SelectedPins, SelectionError
    from chialu.targets.rtl.families.fidelity import Audit, location

    @wraps(function)
    def checked(spec, name="dot_core", force=FORCE_NONE, family=None):
        if family is None and spec.get("dot_contract") == "architecture":
            from chialu.verify.dot_arch_ref import selection
            family = selection(spec)
        if family is None:
            return function(spec, name, force, family)
        from chialu.variant_contracts import validate_pins
        modes = D.parse_modes(spec["modes"])
        validate_pins("dot", family[0], family[1], max(m["fab"].width for m in modes))
        requested = family
        selected = (family[0], SelectedPins("core", family[1]))
        with SelectionTrace() as trace, Audit(), location("core", family[0], {"modes": spec["modes"]}):
            result = function(spec, name, force, selected)
        failures = [(owner, child, factory) for owner, child, factory in trace.failed if owner and owner.startswith("core")]
        if failures:
            raise SelectionError(f"a requested dot component failed to generate: {failures}")
        trace.check({"core": requested}, result, name)
        return result

    return checked


dot_ref_module = _checked_dot_seed(dot_ref_module)
