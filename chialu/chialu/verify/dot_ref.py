"""chialu.VecDotAcc on modes (docs/formats-and-options.md section 6):
the layout of the ports and the exact reference of one vector.

A mode is {elements, format_ab, format_c, format_d}. The unit computes
vecD = vecC + vecA . vecB: with a scalar format_d one reduction over
`elements` values of a and b (each a block of `size` products when
format_ab is a block); with a block format_d of size S, S reductions,
group g of a and b (elements values each) with c value g, whose outputs
form the block. Ports: a, b, c (absent without accumulate), mode,
sr_rnd, <option>_sel, d, flags, and check_en / check_err on the wrapper.
"""
from __future__ import annotations

from fractions import Fraction

from chialu.verify.alu_ref import (CONVENTION_NAMES, RUNTIME_OPTIONS, _fp2,
                                    _read, default_sr_bits, family_of)
from chialu.verify.formats import (NAN, NAR, NINF, PINF, BlockFormat,
                                    FixedFormat, FloatFormat, IntFormat,
                                    PositFormat, ScaledIntFormat, Special,
                                    X87Format, _mask, parse_format)
from chialu.verify.rounding import Rounder, flag_word, is_subnormal

DOT_DEFAULTS = {"rounding": ["RNE"], "daz_in": [False], "ftz_out": [False],
                "flags": [], "overflow": "wrap", "dot_contract": "fused",
                "accumulate": True, "check_sr": [True],
                "nan_payload": "canonical", "invalid_result": "saturate",
                "nan_to_int": "zero", "minmax_nan": "propagate",
                "tininess": "after", "int_div_zero": "riscv",
                "zero_sign": "positive", "quire_overflow": "wrap",
                "block_scale_rounding": "nearest",
                "block_element_overflow": "saturate", "sr_compare": "gt",
                "check_flags": False}
DOT_RUNTIME = ("rounding", "daz_in", "ftz_out")


def normalize_dot_spec(spec: dict) -> dict:
    out = dict(spec)
    for k, v in DOT_DEFAULTS.items():
        out.setdefault(k, list(v) if isinstance(v, list) else v)
    for k in DOT_RUNTIME + ("check_sr",):
        if not isinstance(out[k], (list, tuple)):
            out[k] = [out[k]]
        out[k] = list(out[k])
    modes = parse_modes(out["modes"])
    if not out.get("sr_bits"):
        fm = []
        for m in modes:
            fm += [(1, m["fab"]), (1, m["fc"]), (1, m["fd"])]
        out["sr_bits"] = default_sr_bits(fm)
    if out.get("dot_contract") == "architecture":
        from chialu.verify.dot_arch_ref import selection
        selection(out)
    return out


def parse_modes(modes):
    out = []
    for m in modes:
        fab = parse_format(str(m["format_ab"]))
        fc = parse_format(str(m["format_c"])) if m.get("format_c") else None
        fd = parse_format(str(m["format_d"]))
        elements = int(m["elements"])
        if m.get("scale_ab"):
            scale = parse_format(str(m["scale_ab"]))
            if not isinstance(scale, FloatFormat) or isinstance(fab, (BlockFormat, X87Format)):
                raise ValueError("scale_ab requires a floating-point scale and a scalar format_ab")
            # A and B each carry one scale after their element vector.
            # This also represents a scaled scalar FMA without pretending
            # that it contains two products to satisfy a block-size parser.
            fab = BlockFormat(scale, fab, elements, f"blks{scale.name}e{fab.name}s{elements}")
            elements = 1
        out.append({"elements": elements, "fab": fab, "fc": fc, "fd": fd})
    return out


def n_outputs(m) -> int:
    return m["fd"].size if isinstance(m["fd"], BlockFormat) else 1


def n_products(m) -> int:
    """Scalar products of one reduction."""
    fab = m["fab"]
    return m["elements"] * (fab.size if isinstance(fab, BlockFormat) else 1)


def c_width(m, accumulate) -> int:
    if not accumulate or m["fc"] is None:
        return 0
    S = n_outputs(m)
    if isinstance(m["fc"], BlockFormat):
        return m["fc"].width
    return S * m["fc"].width


def roundings_per_output(m, spec) -> int:
    """The V_max term of one output: one rounding under the fused
    contract; every product and every addition under the sequential one."""
    if spec.get("dot_contract", "fused") != "sequential":
        return 1
    n = n_products(m)
    return n + (n if spec.get("accumulate", True) else n - 1)


def dot_layout(spec: dict) -> dict:
    from chialu.verify.ports import Port
    spec = normalize_dot_spec(spec)
    modes = parse_modes(spec["modes"])
    acc = bool(spec.get("accumulate", True))
    ab_w = max(n_outputs(m) * m["elements"] * m["fab"].width for m in modes)
    c_w = max(c_width(m, acc) for m in modes)
    d_w = max(m["fd"].width for m in modes)
    v_max = max(n_outputs(m) * roundings_per_output(m, spec) for m in modes)
    sr = "SR" in spec["rounding"]
    sr_bits = int(spec["sr_bits"])
    flags = list(spec.get("flags") or ())
    core_in = [Port("a", "in", ab_w), Port("b", "in", ab_w)]
    if c_w:
        core_in.append(Port("c", "in", c_w))
    if len(modes) > 1:
        core_in.append(Port("mode", "in", max(1, (len(modes) - 1).bit_length())))
    if sr:
        core_in.append(Port("sr_rnd", "in", v_max * sr_bits))
    controls = {}
    for name in DOT_RUNTIME:
        vals = list(spec.get(name) or [])
        if len(vals) > 1:
            core_in.append(Port(f"{name}_sel", "in", max(1, (len(vals) - 1).bit_length())))
            controls[name] = vals
    chk_extra = []
    if len(spec.get("check_sr") or []) > 1:
        chk_extra.append(Port("check_sr_sel", "in", 1))
    core_out = [Port("d", "out", d_w)]
    from chialu.verify.dot_arch_ref import extra_outputs
    for name in extra_outputs(spec):
        core_out.append(Port(name, "out", d_w))
    if flags:
        core_out.append(Port("flags", "out", v_max * len(flags)))
    return {"modes": modes, "core_in": core_in, "core_out": core_out,
            "chk_extra": chk_extra, "ab_w": ab_w, "c_w": c_w, "d_w": d_w,
            "v_max": v_max, "sr": sr, "sr_bits": sr_bits, "controls": controls,
            "flags": flags, "accumulate": acc}


def validate_dot_modes(modes, accumulate=True):
    """Section 6: format_ab and format_c are integer, fixed, float,
    posit or block; format_c may be a quire; format_d any of those; a
    quire d (or c) matches format_ab's posit; a block c matches the
    block d's size."""
    for m in modes:
        fab, fc, fd = m["fab"], m["fc"], m["fd"]
        if isinstance(fab, ScaledIntFormat) and not isinstance(fab, FixedFormat):
            raise ValueError(f"format_ab {fab.name}: a quire is not an operand format")
        for f, nm in ((fc, "format_c"), (fd, "format_d")):
            if f is None:
                continue
            if isinstance(f, ScaledIntFormat) and not isinstance(f, FixedFormat):
                if not isinstance(fab, PositFormat) or f.name != f"quire{fab.width}_{fab.es}":
                    raise ValueError(f"{nm} {f.name}: a quire must be the quire of "
                                     f"format_ab's posit ({fab.name})")
        if accumulate and fc is None:
            raise ValueError("a mode needs format_c when accumulate is true")
        S = n_outputs(m)
        if accumulate and isinstance(fc, BlockFormat) and fc.size != S:
            raise ValueError(f"format_c {fc.name}: a block c has the size of the "
                             f"block d ({S})")
        if isinstance(fd, BlockFormat) and isinstance(fd.elem, PositFormat):
            raise ValueError(f"format_d {fd.name}: block elements are floats or integers")


# ------------------------------------------------------------- reference --

def _decode(fmt, bits, daz):
    """(value, sign bit, denormal flag) of one scalar operand."""
    if isinstance(fmt, (FloatFormat, X87Format)):
        return _read(fmt, bits, daz)
    v = fmt.decode(bits)
    return v, (1 if (not isinstance(v, Special) and v < 0) else 0), False


def _snan_of(fmt, bits, count) -> list:
    """Per value of `_values_of`: whether the operand pattern is a
    signalling NaN (IEEE 754's invalid case) or a posit NaR."""
    from chialu.verify.alu_ref import _is_snan
    out = []
    w = fmt.width
    for i in range(count):
        p = (bits >> (i * w)) & _mask(w)
        if isinstance(fmt, BlockFormat):
            elems, _sb = fmt.split(p)
            out += [_is_snan(fmt.elem, eb) for eb in elems]
        elif isinstance(fmt, PositFormat):
            out.append(fmt.decode(p) is NAR)
        else:
            out.append(_is_snan(fmt, p))
    return out


def _values_of(fmt, bits, count, daz):
    """The `count` values packed in `bits` (each a block's elements
    expanded): list of (value, sign, denormal)."""
    out = []
    w = fmt.width
    for i in range(count):
        p = (bits >> (i * w)) & _mask(w)
        if isinstance(fmt, BlockFormat):
            elems, sb = fmt.split(p)
            sc = fmt.scale.decode(sb)
            for eb in elems:
                v = fmt.elem.decode(eb)
                signed = fmt.elem.encoding != "unsigned" if isinstance(fmt.elem, IntFormat) else getattr(fmt.elem, "signed", True)
                s = (eb >> (fmt.elem.width - 1)) & 1 if signed else 0
                den = is_subnormal(fmt.elem, eb) if isinstance(fmt.elem, FloatFormat) else False
                if daz and den:
                    v = Fraction(0)
                out.append((v if isinstance(v, Special) else v * sc, s, den))
        else:
            out.append(_decode(fmt, p, daz))
    return out


def _round_d(fd, v, sign, rounder, word, spec):
    """One value into format_d per the section 6 table; returns (bits, flags)."""
    fl = set()
    overflow = spec.get("overflow", "wrap")
    if isinstance(fd, (FloatFormat, X87Format)):
        if v is NAN or v is NAR:
            from chialu.verify.alu_ref import _nan_result
            b, f = _nan_result(fd, spec, [], invalid_sign=sign)
            return b, fl | f
        core = fd.core if isinstance(fd, X87Format) else fd
        if not core.signed and ((v is NINF) or (not isinstance(v, Special) and v < 0)):
            from chialu.verify.alu_ref import _nan_result
            b, f = _nan_result(fd, spec, [], invalid_sign=1)
            return b, fl | f | {"invalid"}
        return rounder.float(fd, v, word, sign)
    if isinstance(fd, PositFormat):
        return rounder.posit(fd, v)
    # integer, fixed, quire
    if isinstance(v, Special):
        fl.add("invalid")
        if v is NAN or v is NAR:
            val = {"zero": 0, "max": fd.max_int, "min": fd.min_int}[spec.get("nan_to_int", "zero")]
            if isinstance(fd, ScaledIntFormat) and not isinstance(fd, FixedFormat):
                val = fd.min_int                          # the quire's NaR pattern
        else:
            val = fd.max_int if v is PINF else fd.min_int
        return IntFormat.encode(fd, val) if isinstance(fd, ScaledIntFormat) else fd.encode(val), fl
    quire = isinstance(fd, ScaledIntFormat) and not isinstance(fd, FixedFormat)
    if quire:
        sat = spec.get("quire_overflow", "wrap") == "saturate"
    else:
        sat = overflow == "saturate"
    return rounder.scalar(fd, v, word, sign, saturate=sat)


def dot_expected(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words):
    """Expected (d, flags) of one vector of mode mi."""
    if spec.get("dot_contract") == "architecture":
        from chialu.verify.dot_arch_ref import expected
        return expected(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words)
    m = lay["modes"][mi]
    fab, fc, fd = m["fab"], m["fc"], m["fd"]
    acc = lay["accumulate"]
    n = m["elements"]
    S = n_outputs(m)
    rounder = Rounder(ctrl.get("rounding", "RNE"), spec["sr_bits"], spec.get("sr_compare", "gt"),
                      spec.get("tininess", "after"), ftz=bool(ctrl.get("ftz_out", False)))
    if isinstance(fd, PositFormat):
        rounder.ftz = False
    daz = bool(ctrl.get("daz_in", False))
    per_out = roundings_per_output(m, spec)
    fused = spec.get("dot_contract", "fused") == "fused"
    words = words or [0] * lay["v_max"]
    outs, oflags = [], []
    a_vals = _values_of(fab, a_bits, S * n, daz)
    b_vals = _values_of(fab, b_bits, S * n, daz)
    a_snan = _snan_of(fab, a_bits, S * n)
    b_snan = _snan_of(fab, b_bits, S * n)
    np_ = n_products(m)
    if acc:
        if isinstance(fc, BlockFormat):
            c_vals = _values_of(fc, c_bits, 1, daz)
            c_snan = _snan_of(fc, c_bits, 1)
        else:
            c_vals = _values_of(fc, c_bits, S, daz)
            c_snan = _snan_of(fc, c_bits, S)
    for g in (range(S) if not isinstance(fd, BlockFormat) else ()):
        fl = set()
        av = a_vals[g * np_:(g + 1) * np_]
        bv = b_vals[g * np_:(g + 1) * np_]
        cv = c_vals[g] if acc else (Fraction(0), 0, False)
        if any(x[2] for x in av + bv) or (acc and cv[2]):
            fl.add("denormal")
        wbase = g * per_out
        # specials: NaN/NaR anywhere -> NaN; infinities combine
        specials = [x[0] for x in av + bv + ([cv] if acc else []) if isinstance(x[0], Special)]
        nan = any(x is NAN or x is NAR for x in specials)
        prods = []
        for (va, sa, _), (vb, sb, _) in zip(av, bv):
            if isinstance(va, Special) or isinstance(vb, Special):
                if va is NAR or vb is NAR or va is NAN or vb is NAN:
                    prods.append((NAN, 0))
                    continue
                r = _fp2("fmul", va, vb)
                if r is NAN:
                    nan = True
                    fl.add("invalid")
                    prods.append((NAN, 0))
                else:
                    prods.append((NINF if (sa ^ sb) else PINF, sa ^ sb))
            else:
                prods.append((va * vb, sa ^ sb))
        if nan:
            # IEEE 754: invalid for a signalling NaN operand (or a NaR), not for a quiet NaN; the invalid
            # operation 0 x inf marked its flag above
            if any(a_snan[g * np_:(g + 1) * np_]) or any(b_snan[g * np_:(g + 1) * np_]) or (acc and c_snan[g]):
                fl.add("invalid")
            posit = isinstance(fd, PositFormat) or (isinstance(fd, ScaledIntFormat) and not isinstance(fd, FixedFormat) and isinstance(fab, PositFormat))
            b, f = _round_d(fd, NAR if posit else NAN, 0, rounder, 0, spec)
            outs.append(b)
            oflags.append(fl | f)
            continue
        infs = [p for p in prods if isinstance(p[0], Special)] + ([cv] if acc and isinstance(cv[0], Special) else [])
        if infs:
            signs = {p[0] for p in infs}
            if len(signs) > 1:
                fl.add("invalid")
                b, f = _round_d(fd, NAN, 0, rounder, 0, spec)
            else:
                b, f = _round_d(fd, infs[0][0], 0, rounder, 0, spec)
            outs.append(b)
            oflags.append(fl | f)
            continue
        if fused:
            total = sum((p[0] for p in prods), Fraction(0)) + (cv[0] if acc else 0)
            zs = 0
            if total == 0:
                # the sign of an exact zero sum: all terms zero with the same sign keeps it
                term_signs = {p[1] for p in prods if True} | ({cv[1]} if acc else set())
                zs = 1 if term_signs == {1} else (1 if rounder.mode == "RDN" and (
                    any(p[0] != 0 for p in prods) or (acc and cv[0] != 0)) else 0)
            b, f = _round_d(fd, total, zs, rounder, words[wbase], spec)
            outs.append(b)
            oflags.append(fl | f)
            continue
        # sequential: products rounded to format_d, then added one at a time
        k = 0
        rp = []
        for (pv, ps) in prods:
            b, f = _round_d(fd, pv, ps, rounder, words[wbase + k], spec)
            k += 1
            fl |= f
            rp.append(fd.decode(b) if not isinstance(fd, BlockFormat) else None)
        # (block d handled below: the sequential contract rounds into the element format)
        s_val = cv[0] if acc else rp[0]
        start = 0 if acc else 1
        s_sign = cv[1] if acc else prods[0][1]
        b = None
        for i in range(start, len(rp)):
            if isinstance(s_val, Special) or isinstance(rp[i], Special):
                s_val = _fp2("fadd", s_val, rp[i])
                if s_val is NAN:
                    fl.add("invalid")
            else:
                s_val = s_val + rp[i]
            b, f = _round_d(fd, s_val, s_sign if s_val == 0 else 0, rounder, words[wbase + k], spec)
            k += 1
            fl |= f
            s_val = fd.decode(b)
        if b is None:                                   # a single product without c
            b, f = _round_d(fd, s_val, prods[0][1], rounder, words[wbase], spec)
            fl |= f
        outs.append(b)
        oflags.append(fl)
    if isinstance(fd, BlockFormat):
        # the S outputs of the fused contract form one block (the per-output
        # roundings above are replaced by the block quantizer)
        vals = []
        signs = []
        fls = []
        for g in range(S):
            av = a_vals[g * np_:(g + 1) * np_]
            bv = b_vals[g * np_:(g + 1) * np_]
            cv = c_vals[g] if acc else (Fraction(0), 0, False)
            f = set()
            if any(x[2] for x in av + bv) or (acc and cv[2]):
                f.add("denormal")
            nan = False
            total = Fraction(0)
            inf = None
            for (va, sa, _), (vb, sb, _) in zip(av, bv):
                if isinstance(va, Special) or isinstance(vb, Special):
                    r = _fp2("fmul", va, vb)
                    if r is NAN:
                        nan = True
                    elif inf is not None and inf is not r:
                        nan = True
                    else:
                        inf = r
                else:
                    total += va * vb
            if acc:
                if isinstance(cv[0], Special):
                    if cv[0] is NAN or (inf is not None and inf is not cv[0]):
                        nan = True
                    else:
                        inf = cv[0]
                else:
                    total += cv[0]
            if nan:
                f.add("invalid")
                vals.append(NAN)
            elif inf is not None:
                vals.append(inf)
            else:
                vals.append(total)
            # the sign of an exact zero sum: every term a negative zero keeps it
            term_signs = {sa ^ sb for (_va, sa, _), (_vb, sb, _) in zip(av, bv)} | ({cv[1]} if acc else set())
            any_nz = any(not isinstance(x[0], Special) and x[0] != 0 for x in av + bv + ([cv] if acc else []))
            signs.append(1 if (total == 0 and (term_signs == {1} or (rounder.mode == "RDN" and any_nz))) else 0)
            fls.append(f)
        wds = [words[g] for g in range(S)]
        bits, ef = rounder.block(fd, vals, wds, spec, signs)
        flags_out = 0
        names = lay["flags"]
        if names:
            nf = len(names)
            for g in range(S):
                flags_out |= flag_word(fls[g] | ef[g], names) << (g * nf)
        return bits, flags_out
    d = 0
    for g, b in enumerate(outs):
        d |= (b & _mask(fd.width)) << (g * fd.width)
    flags_out = 0
    names = lay["flags"]
    if names:
        nf = len(names)
        for g in range(S):
            flags_out |= flag_word(oflags[g], names) << (g * per_out * nf)
    return d & _mask(lay["d_w"]), flags_out


def vector_ctrl(spec, meta_ctrl):
    ctrl = {}
    for name in DOT_RUNTIME:
        vals = list(spec.get(name) or [])
        if vals:
            ctrl[name] = vals[0]
    ctrl.update(meta_ctrl or {})
    return ctrl


def dot_outputs(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words):
    if spec.get("dot_contract") == "architecture":
        from chialu.verify.dot_arch_ref import outputs
        return outputs(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words)
    d, flags = dot_expected(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words)
    return {"d": d, "flags": flags}
