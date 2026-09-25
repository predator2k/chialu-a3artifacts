"""Block-format modes of the ALU seed: the elements of a block decoded
exactly (element x scale) into X values, the arithmetic ops per element,
one re-quantization of the block through the engine's section 2.6
quantizer, the sign ops and comparisons on the element patterns, and
conversions to and from scalar formats."""
from __future__ import annotations

from chialu.targets.rtl.alu_float import FloatModeEmitter
from chialu.targets.rtl.alu_mode import NOFLAG, flag, flag_if
from chialu.targets.rtl.engine import FW
from chialu.targets.rtl.writer import cmp_flags
from chialu.verify import alu_ref as A
from chialu.verify.formats import NAN, FloatFormat

ELEMENTWISE_ROUNDED = ("fadd", "fsub", "fmul", "fdiv", "fsqrt", "fmin", "fmax")


class BlockModeEmitter(FloatModeEmitter):

    def declare_values(self):
        multiplier = self.family_for("fp_multiplier")
        if multiplier and multiplier[0] == "round_fused_in_reduction" and any(op == "fmul" for _, op in self.ops):
            # The selected scale is determined from the exact products. Keep it
            # fixed while packing the products rounded inside their multiplier.
            source = self.eng.quant_block(self.fmt, self.own_tag)
            marker = f"  function automatic [{self.fmt.size * FW + self.fmt.width - 1}:0] {self.p}_quant_{self.own_tag}("
            function = source[source.index(marker):]
            function = function.replace(f"{self.p}_quant_{self.own_tag}", f"{self.p}_quant_fixed_{self.own_tag}")
            function = function.replace("input ftz);", f"input ftz, input [{self.fmt.scale.width-1}:0] selected_scale);")
            begin = function.index("    have = 1'b0;")
            end = function.index("    vs = ", begin)
            function = function[:begin] + "    blk = 0; fls = 0; sb = selected_scale;\n" + function[end:]
            self.lib.function(function)
        self.lib_inst = {}
        self.declare_unpacked()
        e = self.eng
        guard = e.XW - e.SW
        self.lib.function(f'''
  function automatic [{e.XT-1}:0] {self.p}_family_operand(input [{e.XT-1}:0] value);
    logic [{e.XT-1}:0] normalized;
    logic signed [{e.EW-1}:0] exponent;
    logic [{e.XW-1}:0] significand;
    normalized = {self.p}_norm(value);
    exponent = $signed(normalized[{e.XW+e.EW}:{e.XW+1}]) + {e.EW}'sd{guard};
    significand = normalized[{e.XW}:1] >> {guard};
    {self.p}_family_operand = {{normalized[{e.XT-1}:{e.XT-3}], exponent, significand, normalized[0]}};
  endfunction
''')
        lanes = self.lanes
        try:
            self.lanes = [self.elem(i, j, self.fmt.size) for i in lanes for j in range(self.fmt.size)]
            self.declare_library()
            self.declare_secondary_library()
        finally:
            self.lanes = lanes
        self.declare_sign_library()

    def _cmp_exprs(self, i, xa, xb):
        if ("fp_comparator", self.tag(i)) in self.lib_inst:
            xa, xb = f"{self.p}_family_operand({xa})", f"{self.p}_family_operand({xb})"
        return super()._cmp_exprs(i, xa, xb)

    def register_op(self, op: str):
        for i in self.lanes:
            self.structure(op, i)
            if op in ELEMENTWISE_ROUNDED:
                self.structure(op, i, kind="quantizer")

    def emit_op(self, op: str):
        count = self.count
        tgt = A.cvt_target(op)
        for set_idx, src, oth in self.result_sets(op):
            self.set_idx = set_idx
            base = 0 if set_idx == 0 else A.n_results(self.fmt, count, op)
            if tgt is not None:
                self.emit_cvt(op, tgt, set_idx, src, base)
                continue
            self.emit_block_op(op, set_idx, src, oth, base)

    def emit_block_op(self, op: str, set_idx: int, src: str, oth: str, base: int):
        p, e, fmt, blk = self.p, self.eng, self.fmt, self.blk
        w, size = fmt.width, fmt.size
        el, sc = fmt.elem, fmt.scale
        we = el.width
        XT, XW = e.XT, e.XW
        fl_el = isinstance(el, FloatFormat)
        nan_prop = self.conv.nan_payload == "propagate"
        el_nan = el.encode_special(NAN) if (fl_el and el.has_nan) else 0
        for i in self.lanes:
            pa, pb = self.pat(src, i), self.pat(oth, i)
            if op in ("fabs", "fneg"):
                raw_gate = self.lib_inst.get(("raw_sign", self.tag(i), set_idx))
                sign_gate = self.lib_inst.get(("sign_logic", self.tag(i), set_idx))
                gated_word = None
                if raw_gate or sign_gate:
                    if fl_el:
                        sign_mask = sum(1 << (j * we + we - 1) for j in range(size)) if el.signed else 0
                        mask = ((1 << w) - 1) ^ sign_mask if op == "fabs" else sign_mask
                        opcode = 0 if op == "fabs" else 2
                    else:
                        mask = (1 << (we * size)) - 1
                        opcode = 3
                    if raw_gate:
                        ga, gb, propagate, generate, _total, cin = raw_gate
                        blk.stmt(f"{ga} = {pa}; {gb} = {w}'d{mask}; {cin} = 1'b0;")
                        gated_word = generate if opcode == 0 else propagate
                    else:
                        ga, gb, go, gated_word = sign_gate
                        blk.stmt(f"{ga} = {pa}; {gb} = {w}'d{mask}; {go} = 2'd{opcode};")
                    word = self.tmp(f"{p}_block_sign{set_idx}_{self.tag(i)}", w)
                    blk.stmt(f"{word} = {gated_word};")
                    gated_word = word
                for j in range(size):
                    eb = f"{pa}[{j*we} +: {we}]"
                    if fl_el and el.signed:
                        top = f"({we}'d1 << {we-1})"
                        body = f"({eb} & ~{top})" if op == "fabs" else f"({eb} ^ {top})"
                    elif fl_el:
                        body = eb
                    elif el.encoding == "unsigned":
                        # integer elements: magnitude / negation, wrapped
                        body = eb if op == "fabs" else f"(-{eb})"
                    else:
                        body = f"({pa}[{j*we+we-1}] ? (-{eb}) : {eb})" if op == "fabs" else f"(-{eb})"
                    if gated_word is not None:
                        selected = self.tmp(f"{p}_sign_result{set_idx}_{self.tag(i)}_e{j}", we)
                        part = f"{gated_word}[{j*we} +: {we}]"
                        if fl_el:
                            blk.stmt(f"{selected} = {part};")
                        else:
                            negative = f"({part} + 1'b1)"
                            value = (eb if el.encoding == "unsigned" else f"({pa}[{j*we+we-1}] ? {negative} : {eb})") if op == "fabs" else negative
                            blk.stmt(f"{selected} = {value};")
                        body = selected
                    if fl_el and el.has_nan:
                        nan_e = self.is_nan(self.x(src, self.elem(i, j, size)))
                        nan_out = eb if nan_prop else f"{we}'d{el_nan}"
                        body = f"({nan_e} ? {nan_out} : {body})"
                        self.put_flags(base + i * size + j, flag_if(nan_e, "nan"), set_idx)
                    self.put(set_idx, i, w, body, off=j * we, width=we)
                self.put(set_idx, i, w, f"{pa}[{size*we} +: {sc.width}]", off=size * we, width=sc.width)
                continue
            if op == "fcmp":
                for j in range(size):
                    k = self.elem(i, j, size)
                    xa, xb = self.x(src, k), self.x(oth, k)
                    nan_a, nan_b = self.is_nan(xa), self.is_nan(xb)
                    lt, eq, gt = self._cmp_exprs(k, xa, xb)
                    code = cmp_flags(we, f"({gt})", f"({eq})", f"({lt})")
                    expr = f"({nan_a} || {nan_b}) ? {we}'d0 : {code}"
                    self.put(set_idx, i, w, expr, off=j * we, width=we)
                    snan = f"({self.is_snan(xa, pa, fmt, j * we)} || {self.is_snan(xb, self.pat(oth, i), fmt, j * we)})"
                    self.put_flags(base + k, flag_if(f"{nan_a} || {nan_b}", "unordered") + f" | {flag_if(snan, 'invalid')}", set_idx)
                self.put(set_idx, i, w, "0", off=size * we, width=sc.width)
                continue
            # elementwise arithmetic then quantization
            t = f"{p}_o{self.oi}q{set_idx}_{self.tag(i)}"
            txs = self.tmp(f"{t}_xs", size * XT)
            self.tmp(t, size * FW + w)
            tpf = self.tmp(f"{t}_pf", size * FW)
            blk.stmt(f"{tpf} = 0;")
            feedback = op == "fmul" and ("fp_multiplier_scale", self.tag(self.elem(i, 0, size))) in self.lib_inst
            if feedback:
                rawxs = self.tmp(f"{t}_raw", size * XT)
                scale_probe = self.tmp(f"{t}_scale_probe", size * FW + w)
                selected_scale = f"{scale_probe}[{size*we} +: {sc.width}]"
            for j in range(size):
                k = self.elem(i, j, size)
                xa, xb = self.x(src, k), self.x(oth, k)
                nan_a, nan_b = self.is_nan(xa), self.is_nan(xb)
                den = f"({self.den(src, k)})" if op == "fsqrt" else f"({self.den(src, k)} | {self.den(oth, k)})"
                za, zb = self.is_zero(xa), self.is_zero(xb)
                inf_a = self.is_inf(xa)
                elem = f"{txs}[{j*XT} +: {XT}]"
                if op in ("fmin", "fmax"):
                    prop = self.conv.minmax_nan == "propagate"
                    nan_x = f"{p}_mkx(2'd1, 1'b0, 0, 0, 1'b0)"
                    lt, eq, gt = self._cmp_exprs(k, xa, xb)
                    pick_a = f"({lt} || {eq})" if op == "fmin" else f"({gt} || {eq})"
                    if prop:
                        expr = f"({nan_a} || {nan_b}) ? {nan_x} : ({pick_a} ? {xa} : {xb})"
                    else:
                        expr = (f"({nan_a} && {nan_b}) ? {nan_x} : {nan_a} ? {xb} : {nan_b} ? {xa} : "
                                f"({pick_a} ? {xa} : {xb})")
                    blk.stmt(f"{elem} = {expr};")
                    snan = f"({self.is_snan(xa, pa, fmt, j * we)} || {self.is_snan(xb, self.pat(oth, i), fmt, j * we)})"
                    blk.stmt(f"{tpf}[{j*FW} +: {FW}] = {flag_if(f'{nan_a} || {nan_b}', 'unordered')} | "
                             f"{flag_if(snan, 'invalid')} | {flag_if(den, 'denormal')};")
                    continue
                xexpr = {"fadd": f"{p}_add({xa}, {xb}, 1'b0)", "fsub": f"{p}_add({xa}, {xb}, 1'b1)",
                         "fmul": f"{p}_mul({xa}, {xb})", "fdiv": f"{p}_div({xa}, {xb})",
                         "fsqrt": f"{p}_sqrt({xa})"}[op]
                sa_e, sb_e = self.x_sign(xa), self.x_sign(xb)
                if op in ("fmul", "fdiv"):
                    zs = f"({sa_e} ^ {sb_e})"
                elif op == "fsqrt":
                    zs = sa_e
                else:
                    sb_eff = f"({sb_e} ^ 1'b{1 if op == 'fsub' else 0})"
                    zs = (f"(({za} && {zb}) ? ((rnd == 3'd2) ? ({sa_e} | {sb_eff}) : ({sa_e} & {sb_eff})) : "
                          f"((rnd == 3'd2) ? 1'b1 : 1'b0))")
                xt = self.tmp(f"{t}_x{j}", XT)
                kind = "fp_adder" if op in ("fadd", "fsub") else "fp_multiplier" if op == "fmul" else "fp_sqrt" if op == "fsqrt" else "fp_divider"
                component = self.library_instance(kind, self.tag(k)) if op == "fsqrt" else self.lib_inst.get((kind, self.tag(k)))
                fxa, fxb = f"{p}_family_operand({xa})", f"{p}_family_operand({xb})"
                if component is None:
                    blk.stmt(f"{xt} = {xexpr};")
                elif op in ("fadd", "fsub"):
                    ca, cb, sub, result = component
                    blk.stmt(f"{ca} = {fxa}; {cb} = {fxb}; {sub} = 1'b{int(op == 'fsub')}; {xt} = {result};")
                elif op == "fsqrt":
                    ca, result = component
                    blk.stmt(f"{ca} = {fxa}; {xt} = {result};")
                else:
                    ca, cb, result = component
                    blk.stmt(f"{ca} = {fxa}; {cb} = {fxb}; {xt} = {result};")
                if feedback:
                    scale_input, raw_output = self.lib_inst[("fp_multiplier_scale", self.tag(k))]
                    blk.stmt(f"{rawxs}[{j*XT} +: {XT}] = {raw_output};")
                blk.stmt(f"{elem} = {{ {xt}[{XT-1}:{XT-2}], {self.is_zero(xt)} ? {zs} : {xt}[{XT-3}], {xt}[{XT-4}:0] }};")
                if feedback:
                    blk.stmt(f"if ({xt}[{XT-1}:{XT-2}] == 2'd3) {elem} = {{2'd0, {xt}[{XT-3}:1], 1'b0}};")
                sp_j = f"{txs}[{j*XT+XT-2} +: 2]"
                res_nan = f"({sp_j} == 2'd1)"
                fl = flag_if(den, "denormal")
                # IEEE 754: invalid for a signalling NaN operand or an invalid operation; a quiet NaN propagates
                snan_a = self.is_snan(xa, pa, fmt, j * we)
                snan_b = self.is_snan(xb, self.pat(oth, i), fmt, j * we) if op != "fsqrt" else "1'b0"
                fl += f" | {flag_if(f'{snan_a} || {snan_b} || ({res_nan} && !({nan_a} || {nan_b}))', 'invalid')}"
                if op == "fdiv":
                    fl += f" | {flag_if(f'{zb} && !{za} && !{inf_a} && !{nan_a} && !{nan_b}', 'div_zero')}"
                if op == "fsqrt":
                    sticky_only = (f"!{res_nan} && {sp_j} == 2'd0 && {txs}[{j*XT} +: {XW+1}] != 0 "
                                   f"&& {txs}[{j*XT}]")
                    fl += f" | {flag_if(sticky_only, 'inexact')}"
                if feedback:
                    fl += f" | (({xt}[{XT-1}:{XT-2}] == 2'd3) ? ({flag('inexact')} | ({xt}[0] ? {flag('underflow')} : 0)) : 0)"
                blk.stmt(f"{tpf}[{j*FW} +: {FW}] = {fl};")
            if feedback:
                blk.stmt(f"{scale_probe} = {p}_quant_{self.own_tag}({rawxs}, rnd, {self.words(base + i*size, size)}, ftz);")
                for j in range(size):
                    scale_input, _ = self.lib_inst[("fp_multiplier_scale", self.tag(self.elem(i, j, size)))]
                    if ("fp_multiplier_fractional_scale", self.tag(self.elem(i, j, size))) not in self.lib_inst:
                        blk.stmt(f"{scale_input} = $signed({{{{{e.EW-sc.width}{{1'b0}}}}, {selected_scale}}}) - {e.EW}'sd{sc.bias};")
                    else:
                        decoded_scale = self.tmp(f"{t}_decoded_scale{j}", e.VW + 1)
                        scale_sig, scale_sp, word = self.lib_inst[("fp_multiplier_fractional_scale", self.tag(self.elem(i, j, size)))]
                        blk.stmt(f"{decoded_scale} = {p}_unpack_{self.own_tag}_sd({selected_scale}, 1'b0); "
                                 f"{scale_input} = {decoded_scale}[{e.SW+e.EW-1}:{e.SW}]; "
                                 f"{scale_sig} = {decoded_scale}[{sc.man_bits}:0]; "
                                 f"{scale_sp} = {decoded_scale}[{e.VW-1}:{e.VW-2}]; {word} = {self.word(base+i*size+j)};")
                blk.stmt(f"{t} = {p}_quant_fixed_{self.own_tag}({txs}, rnd, {self.words(base + i*size, size)}, ftz, {selected_scale});")
            else:
                blk.stmt(f"{t} = {p}_quant_{self.own_tag}({txs}, rnd, {self.words(base + i*size, size)}, ftz);")
            self.put(set_idx, i, w, f"{t}[{w-1}:0]")
            for j in range(size):
                if fl_el and el.signed:
                    exact_zero = f"({txs}[{j*XT} +: {XW+1}] == 0 && {txs}[{j*XT+XT-2} +: 2] == 0)"
                    zero = f"{{{txs}[{j*XT+XT-3}], {we-1}'d0}}"
                    self.put(set_idx, i, w, f"{exact_zero} ? {zero} : {t}[{j*we} +: {we}]", off=j*we, width=we)
                # the quantizer's flags, minus inexact for a NaN element (the
                # reference reports invalid+nan only)
                qf = f"{t}[{w + j*FW} +: {FW}]"
                if not fl_el:
                    qf = f"({txs}[{j*XT+XT-2} +: 2] == 0 ? ({qf} & ~{flag('invalid')}) : {qf})"
                if feedback:
                    # Overflow is a comparison before rounding: a product just
                    # beyond maxfinite may round back onto maxfinite. The scale
                    # prepass retains that range event alongside its scale.
                    range_flags = f"{scale_probe}[{w+j*FW} +: {FW}] & ({flag('overflow')} | {flag('inexact')} | {flag('underflow')})"
                    qf = f"({qf} | ({range_flags}))"
                pf = f"{tpf}[{j*FW} +: {FW}]"
                nan_j = f"({txs}[{j*XT+XT-2} +: 2] == 2'd1)"
                if fl_el and el.has_nan:
                    expr = f"({nan_j} ? (({pf} | {qf}) & ~{flag('inexact')}) : ({pf} | {qf}))"
                else:
                    expr = f"({pf} | {qf})"
                self.put_flags(base + i * size + j, expr, set_idx)
