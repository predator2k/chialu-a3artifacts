"""The behavioral seed of a chialu.VecSFU spec in SystemVerilog.

Named functions: a full ROM of the reference for scalar formats of at
most ROM_BITS bits (bit-exact), a piecewise-linear evaluator with PWL_SEGS
segments over the value-ordered pattern index otherwise (its coefficients
come from the reference at the segment ends, so the seed is a starting
point that generally misses the max_ulp bound). Reconfigurable slots are
their own evaluator: a table register file written on posedge clk through
tbl_we / tbl_addr / tbl_data, the datapath combinational from x and the
table registers. Block modes apply the function per element and
re-quantize each block; slots take scalar modes only."""
from __future__ import annotations

from fractions import Fraction

from chialu.targets.rtl.engine import FW, RND, Conventions, Engine, flag_bit, _core
from chialu.targets.rtl.engine import fmt_tag as _tag
from chialu.targets.rtl.families.module_library import ModuleLibrary, collect_modules, dedupe_modules
from chialu.verify import sfu_ref as S
from chialu.verify.formats import (NAN, NAR, NINF, PINF, BlockFormat,
                                    FloatFormat, PositFormat, Special,
                                    X87Format, _mask)
from chialu.verify.rounding import Rounder

ROM_BITS = 12
PWL_SEGS = 256          # the default; pwl_segments() scales it with the format


def pwl_segments(fmt) -> int:
    """Segments of the piecewise-linear seed: a sixteenth of a binade for
    floats (2^(E+5)), 2^(n-6) for posits, between 64 and 4096."""
    c = fmt.core if isinstance(fmt, X87Format) else fmt
    if isinstance(c, PositFormat):
        k = 1 << max(c.width - 6, 6)
    else:
        k = 1 << (c.exp_bits + 5)
    return max(64, min(4096, k))


def _special_outputs(fn, fmt):
    """(NaN pattern, +inf result pattern, -inf result pattern) of a
    function for the pwl seed's special inputs."""
    from chialu.verify.rounding import Rounder
    r = Rounder("RNE", 1)
    posit = isinstance(fmt, PositFormat)
    outs = []
    for sp in (NAN, PINF, NINF):
        if posit:
            outs.append(fmt._nar)
            continue
        val, _ = S.fn_value(fn, fmt, sp, 1 if sp is NINF else 0)
        b, _ = S.resolve(fmt, val, r, 0)
        outs.append(b)
    return outs


def _scalar_invalid_result(fmt, spec):
    """An invalid scalar result under the project's NaN/no-NaN contract."""
    if isinstance(fmt, PositFormat):
        return fmt._nar, {"invalid", "nan"}
    core = _core(fmt)
    if core.has_nan:
        bits, _ = Rounder("RNE", 1).float(fmt, NAN)
        return bits, {"invalid", "nan"}
    bits = 0 if (spec or {}).get("invalid_result", "saturate") == "zero" else core._max_finite_bits()
    return bits, {"invalid", "inexact"}


def _scalar_infinity_result(fn, fmt, negative, spec):
    """Exact endpoint values; these are independent of the function evaluator."""
    if isinstance(fmt, PositFormat):
        return fmt._nar, {"invalid", "nan"}
    endpoints = {
        "exp2": (PINF, Fraction(0)), "exp": (PINF, Fraction(0)),
        "log2": (PINF, None), "log": (PINF, None),
        "sin": (None, None), "cos": (None, None),
        "tanh": (Fraction(1), Fraction(-1)), "erf": (Fraction(1), Fraction(-1)),
        "sigmoid": (Fraction(1), Fraction(0)), "recip": (Fraction(0), Fraction(0)),
        "rsqrt": (Fraction(0), None), "sqrt": (PINF, None),
        "gelu": (PINF, Fraction(0)), "silu": (PINF, Fraction(0)), "softplus": (PINF, Fraction(0))}
    value = endpoints[fn][int(negative)]
    if value is None or (not _core(fmt).signed and not isinstance(value, Special) and value < 0):
        return _scalar_invalid_result(fmt, spec)
    zero_sign = int(negative and fn in ("sin", "tanh", "erf", "gelu", "silu", "sqrt"))
    return Rounder("RNE", 1).float(fmt, value, zero_sign=zero_sign)


def _flag_constant(names):
    return sum(1 << flag_bit(name) for name in names)


def _fn_rom(fn, fmt, spec):
    """Every pattern's reference result (RNE, no daz/ftz) for a ROM."""
    rounder = Rounder("RNE", spec["sr_bits"], spec.get("sr_compare", "gt"), spec.get("tininess", "after"))
    out = []
    for xb in range(1 << fmt.width):
        if not fmt.valid(xb):
            out.append(0)
            continue
        v, s, den = S._read(fmt, xb, False) if not isinstance(fmt, PositFormat) else (fmt.decode(xb), 0, False)
        val, fl = S.fn_value(fn, fmt, v, s)
        b, _f = S.resolve(fmt, val, rounder, 0, s if fn in ("sin", "tanh", "erf", "gelu", "silu", "sqrt") else 0)
        out.append(b)
    return out


def _pwl_coeffs(fn, fmt, spec, K):
    """(x_k, c0, c1) per segment over the value-ordered index, in the
    mode's format: c0 = f(x_k), c1 = (f(x_next) - f(x_k)) / (x_next - x_k)."""
    from chialu.verify.sfu_ref import segment_start_value
    rounder = Rounder("RNE", spec["sr_bits"], spec.get("sr_compare", "gt"), spec.get("tininess", "after"))
    coeffs = []
    for k in range(K):
        xk = segment_start_value(fmt, k, K)
        xn = segment_start_value(fmt, k + 1, K) if k + 1 < K else None
        if xk is None:
            coeffs.append((None, 0, 0))
            continue
        fk, _ = S.fn_value(fn, fmt, xk, 1 if xk < 0 else 0)
        bk, _ = S.resolve(fmt, fk, rounder, 0)
        yk = fmt.decode(bk)
        if xn is None or isinstance(yk, Special):
            coeffs.append((xk, bk, 0))
            continue
        fn_, _ = S.fn_value(fn, fmt, xn, 1 if xn < 0 else 0)
        bn, _ = S.resolve(fmt, fn_, rounder, 0)
        yn = fmt.decode(bn)
        if isinstance(yn, Special) or isinstance(yk, Special) or xn == xk:
            c1 = 0
        else:
            c1 = rounder.scalar(fmt, (yn - yk) / (xn - xk), 0)[0] if not isinstance(fmt, PositFormat) \
                else fmt.round((yn - yk) / (xn - xk))
        coeffs.append((xk, bk, c1))
    return coeffs


class SfuSeedText(str):
    """Generated text with its structural fidelity evidence."""


def sfu_ref_module(spec: dict, name: str = "sfu_core", family=None) -> str:
    if not family:
        return _sfu_ref_module(spec, name, family)
    from chialu.targets.rtl.families.selection import SelectedPins, SelectionTrace
    from chialu.targets.rtl.families.fidelity import location
    selected = (family[0], SelectedPins("core", family[1]))
    with SelectionTrace() as trace, location("core", selected[0], {"modes": spec.get("modes", [])}):
        text = _sfu_ref_module(spec, name, selected)
    trace.check({"core": selected}, text, name)
    result = SfuSeedText(text)
    result.fidelity = trace.report()
    return result


def _sfu_ref_module(spec: dict, name: str = "sfu_core", family=None) -> str:
    """The SFU module of a spec; `family` is the declared (family, pins)
    of the core (`core.family`, sfu_spaces)."""
    spec = S.normalize_sfu_spec(spec)
    lay = S.sfu_layout(spec)
    modes, fns, slots = lay["modes"], lay["functions"], lay["slots"]
    S.validate_sfu_modes(modes, spec)
    if any(fn not in S.FUNCTIONS for fn in fns):
        raise ValueError(f"unknown SFU functions: {sorted(set(fns) - set(S.FUNCTIONS))}")
    if any(count < 1 for count, _ in modes):
        raise ValueError("SFU mode counts must be positive")
    total = lay["total"]
    ports = list(lay["core_in"]) + list(lay["core_out"])
    x_w, w_max, v_max = lay["x_w"], lay["w_max"], lay["v_max"]
    sr, sb = lay["sr"], lay["sr_bits"]
    L = [f"// {name}: behavioral seed derived from the instance (chialu.VecSFU): "
         f"ROM or piecewise-linear evaluators for the named functions, table evaluators for the slots."]
    library_used: dict = ModuleLibrary()  # strict named SV definitions, in order of use
    lib_fam = None
    if family:
        if not fns:
            raise ValueError("an explicit SFU family requires at least one named function")
        L.append(f"// core.family: {family[0]}" + (f" ({', '.join(f'{k}={v}' for k, v in family[1].items())})" if family[1] else ""))
        from chialu.targets.rtl.families.sfu import SFU_FAMILIES, validate_sfu_pins
        sharing = str(family[1].get("sharing", "datapath_per_fn"))
        if family[0] in SFU_FAMILIES["core"]:
            for _, mode_format in modes:
                validate_sfu_pins(family[0], family[1], mode_format, fns)
            lib_fam = family
            from chialu.spaces.sfu_spaces import SHARINGS
            if sharing not in SHARINGS:
                raise ValueError(f"unknown SFU sharing {sharing!r}")
            if sharing != "datapath_per_fn" and len(fns) < 2:
                raise ValueError(f"sharing={sharing} requires two or more named functions")
        else:
            raise ValueError(f"requested SFU family {family[0]!r} has no generator")
    header_at = len(L)
    decl_ports = [f"  {'input ' if pt.direction == 'in' else 'output'} logic [{pt.width-1}:0] {pt.name}" for pt in ports]
    L += [f"module {name} (", ",\n".join(decl_ports), ");"]
    rnds = list(spec["rounding"])
    if len(rnds) > 1:
        L.append("  logic [2:0] rnd;")
        L.append("  always_comb begin case (rounding_sel)")
        for k, mname in enumerate(rnds):
            L.append(f"    {max(1, (len(rnds)-1).bit_length())}'d{k}: rnd = 3'd{RND[mname]};")
        L.append(f"    default: rnd = 3'd{RND[rnds[0]]}; endcase end")
    else:
        L.append(f"  logic [2:0] rnd; assign rnd = 3'd{RND[rnds[0]]};")
    for nm, port in (("daz", "daz_in"), ("ftz", "ftz_out")):
        vals = list(spec[port])
        if len(vals) > 1:
            L.append(f"  logic {nm}; assign {nm} = {port}_sel[0] ? 1'b{1 if vals[1] else 0} : 1'b{1 if vals[0] else 0};")
        else:
            L.append(f"  logic {nm}; assign {nm} = 1'b{1 if vals[0] else 0};")
    # slot tables
    if slots:
        for si, sl in enumerate(slots):
            nc = S.coeff_words(sl)
            L.append(f"  logic [{nc*w_max-1}:0] tbl{si} [0:{sl['segments']-1}];")
            L.append(f"  always_ff @(posedge clk) if (tbl_we[{si}]) tbl{si}[tbl_addr] <= tbl_data[{nc*w_max-1}:0];")
    fsw = max(1, (total - 1).bit_length())
    conv = Conventions.from_spec(spec)
    bodies = []
    for mi, (count, fmt) in enumerate(modes):
        p = f"m{mi}"
        w = fmt.width
        block = isinstance(fmt, BlockFormat)
        base = fmt.elem if block else fmt
        size = fmt.size if block else 1
        wf = None
        if block:
            # the working float of the decoded elements (elem x scale exactly)
            el, sc = fmt.elem, fmt.scale
            m_e = el.man_bits if isinstance(el, FloatFormat) else el.width
            wf = FloatFormat(f"wf{mi}", max(sc.exp_bits, getattr(el, "exp_bits", 2)) + 2,
                             m_e + sc.man_bits + 1, True, True)
        e = Engine(p, fmt, sb, sr, targets=[fmt] + ([wf] if wf else []), conv=conv)
        lib = [e.vdecl(), e.rup_fn(), e.arith()]
        ftag = _tag(fmt)
        if block:
            lib.append(e.unpack_block(fmt, "s"))
            lib.append(e.quant_block(fmt, ftag))
            lib.append(e.unpack_float(wf, "wf"))
            lib.append(e.pack_float(wf, "wf"))
        elif isinstance(fmt, PositFormat):
            lib.append(e.unpack_posit(fmt, "s"))
            lib.append(e.pack_posit(fmt, ftag))
        else:
            lib.append(e.unpack_float(fmt, "s"))
            lib.append(e.pack_float(fmt, ftag))
        L.append("".join(lib))
        XT, VW, XW = e.XT, e.VW, e.XW
        D_, B_ = [], []
        D_.append(f"  logic [{x_w-1}:0] y_{p}; logic [{v_max*FW-1}:0] fl_{p};")
        B_.append(f"    y_{p} = '0; fl_{p} = '0;")
        # operand values as X (per element for blocks) and their patterns
        nv = count * size
        for i in range(count):
            if block:
                D_.append(f"  logic [{size*(VW+1)-1}:0] {p}_u{i}; assign {p}_u{i} = {p}_unpack_s(x[{i*w} +: {w}], daz);")
                for j in range(size):
                    k = i * size + j
                    D_.append(f"  logic [{XT-1}:0] {p}_x{k}; assign {p}_x{k} = {p}_x({p}_u{i}[{j*(VW+1)} +: {VW}]);")
                    D_.append(f"  logic {p}_den{k}; assign {p}_den{k} = {p}_u{i}[{j*(VW+1)+VW}];")
            else:
                arg = f"x[{i*w} +: {w}]"
                if isinstance(fmt, X87Format):
                    arg = f"{{x[{i*w+79}], x[{i*w+64} +: 15], x[{i*w} +: 63]}}"
                D_.append(f"  logic [{VW}:0] {p}_u{i}; assign {p}_u{i} = {p}_unpack_s({arg}, daz);")
                D_.append(f"  logic [{XT-1}:0] {p}_x{i}; assign {p}_x{i} = {p}_x({p}_u{i}[{VW-1}:0]);")
                D_.append(f"  logic {p}_den{i}; assign {p}_den{i} = {p}_u{i}[{VW}];")
        # per function/slot
        shared_module = None
        if lib_fam and sharing != "datapath_per_fn":
            from chialu.targets.rtl.families.fp import Geom
            shared_module = _shared_family_module(fns, wf if block else fmt, Geom.of_engine(e),
                                                  lib_fam, count * size, spec)
        if total > 1:
            B_.append("    case (fn_sel)")
        for fi in range(total):
            if total > 1:
                B_.append(f"      {fsw}'d{fi}: begin")
            if fi < len(fns):
                fn = fns[fi]
                lib_done = False
                if lib_fam and block:
                    lib_done = _emit_block_family(B_, D_, p, e, fmt, wf, count, fi, fn, lib_fam,
                                                  sr, sb, ftag, library_used, shared_module)
                elif lib_fam and fn not in S.VECTOR_FNS:
                    lib_done = _emit_family(B_, D_, p, e, fmt, count, fi, fn, lib_fam, sr, sb, ftag, w, library_used, L,
                                           shared_module, spec)
                elif lib_fam and not block:
                    lib_done = _emit_vector_family(B_, D_, p, e, fmt, count, fi, fn, lib_fam, sr, sb, ftag, w, library_used, L,
                                                  shared_module)
                if lib_done:
                    pass
                elif fn in S.VECTOR_FNS:
                    default_vector = ("softmax_layernorm", {"layernorm_support": True})
                    if block:
                        _emit_block_family(B_, D_, p, e, fmt, wf, count, fi, fn, default_vector,
                                           sr, sb, ftag, library_used)
                    else:
                        _emit_vector_family(B_, D_, p, e, fmt, count, fi, fn, default_vector,
                                            sr, sb, ftag, w, library_used, L)
                elif not block and base.width <= ROM_BITS:
                    rom = _fn_rom(fn, fmt, spec)
                    D_.append(f"  logic [{w-1}:0] {p}_rom{fi} [0:{(1 << w)-1}];")
                    D_.append(f"  initial begin")
                    for xb, yb in enumerate(rom):
                        D_.append(f"    {p}_rom{fi}[{xb}] = {w}'d{yb};")
                    D_.append("  end")
                    for i in range(count):
                        B_.append(f"        y_{p}[{i*w} +: {w}] = {p}_rom{fi}[x[{i*w} +: {w}]];")
                else:
                    self_fmt = wf if block else base
                    K = pwl_segments(self_fmt)
                    coeffs = _pwl_coeffs(fn, self_fmt, spec, K)
                    sp_nan, sp_pinf, sp_ninf = _special_outputs(fn, self_fmt)
                    D_.append(f"  localparam [{self_fmt.width-1}:0] {p}_sp{fi}_nan = {self_fmt.width}'d{sp_nan}, "
                              f"{p}_sp{fi}_pinf = {self_fmt.width}'d{sp_pinf}, {p}_sp{fi}_ninf = {self_fmt.width}'d{sp_ninf};")
                    D_.append(f"  logic [{3*self_fmt.width-1}:0] {p}_pwl{fi} [0:{K-1}];   // {{x_k, c1, c0}}")
                    D_.append("  initial begin")
                    for k, (xk, c0, c1) in enumerate(coeffs):
                        xkb = 0 if xk is None else (self_fmt.encode(xk) if not isinstance(self_fmt, PositFormat) else self_fmt.round(xk))
                        if isinstance(self_fmt, X87Format):
                            xkb = self_fmt.encode(xk) if xk is not None else 0
                        D_.append(f"    {p}_pwl{fi}[{k}] = {{{self_fmt.width}'d{xkb}, {self_fmt.width}'d{c1}, {self_fmt.width}'d{c0}}};")
                    D_.append("  end")
                    _emit_pwl(B_, D_, p, e, fmt, self_fmt, block, count, size, fi, K, sr, sb, ftag, w)
            else:
                sl = slots[fi - len(fns)]
                si = fi - len(fns)
                _emit_slot(B_, D_, p, e, fmt, count, si, sl, sr, sb, ftag, w, w_max)
            if total > 1:
                B_.append("      end")
        if total > 1:
            B_.append("      default: ;")
            B_.append("    endcase")
        L += D_
        bodies.append(B_)
    for B_ in bodies:
        L.append("  always_comb begin")
        L += B_
        L.append("  end")
    L.append(f"  logic [{v_max*FW-1}:0] fl_all;")
    if len(modes) > 1:
        mdw = max(1, (len(modes) - 1).bit_length())
        L.append("  always_comb begin case (mode)")
        for mi in range(len(modes)):
            L.append(f"    {mdw}'d{mi}: begin y = y_m{mi}; fl_all = fl_m{mi}; end")
        L.append("    default: begin y = '0; fl_all = '0; end endcase end")
    else:
        L.append("  assign y = y_m0; assign fl_all = fl_m0;")
    flags = lay["flags"]
    if flags:
        nf = len(flags)
        for r in range(v_max):
            for j, fname in enumerate(flags):
                L.append(f"  assign flags[{r*nf+j}] = fl_all[{r*FW + flag_bit(fname)}];")
    L.append("endmodule")
    if library_used:
        L.insert(header_at, f"// LIBRARY: {', '.join(sorted(library_used))} (chialu.targets.rtl.families: the modules of "
                            f"the declared family the lanes instantiate; their text follows the generated module)")
        L.append("// ---- the family library modules the lanes instantiate (chialu/targets/rtl/families; fixed text, "
                 "replaced by editing the instances)")
        L += [library_used[k] for k in sorted(library_used)]
    if lib_fam and sharing == "datapath_per_fn":
        from chialu.targets.rtl.families.fidelity import effective
        effective(lib_fam[1], "sharing", "datapath_per_fn", "separate function instances in every mode",
                  {"functions": len(fns), "modes": len(modes)})
    return dedupe_modules("\n".join(L) + "\n")


def _shared_family_module(functions, fmt, geom, family, count, spec=None):
    """Construct one selector-controlled module from the chosen family's cores."""
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.sfu_sharing import SharedNet
    if family[0] in SF.PATTERN_FAMILIES:
        from chialu.targets.rtl.families.sfu_control_table import controlled_table
        return controlled_table(functions, fmt, family, spec)
    vector = [fn in S.VECTOR_FNS for fn in functions]
    if any(vector) and not all(vector):
        raise ValueError("a shared SFU evaluator requires matching scalar or vector function interfaces")
    fam, pins = family
    nets = [(SF.vector_sv(fn, fmt, geom, count, fam, pins) if all(vector)
             else SF.sfu_sv(fn, fmt, geom, fam, pins))[2] for fn in functions]
    name = SF.sfu_module_name("_".join(functions), fmt, fam, pins) + f"_shared_n{count}"
    net = SharedNet(name, nets, str(pins["sharing"]))
    from chialu.targets.rtl.families.fidelity import effective, shared
    effective(pins, "sharing", str(pins["sharing"]), "selector-controlled sharing of compatible physical operations",
              {"functions": len(functions), "lanes": count})
    shared("core", str(pins["sharing"]), [name], ["core"] + [f"core.fn.{fn}" for fn in functions],
           detail=str(net.stats), origin_modules=[n.name for n in nets])
    if fam == "cordic" and pins.get("coordinate_set") == "unified":
        domains = sorted(SF.sfu_coordinate_domains(functions))
        if len(domains) < 2 or net.stats["merged_evaluator_operations"] == 0:
            raise ValueError("unified CORDIC needs active coordinate domains sharing arithmetic through fn_sel")
        effective(pins, "coordinate_set", "unified", "fn_sel controls shared arithmetic across coordinate domains",
                  {"domains": domains, "selector": "fn_sel", "shared_operations": net.stats["merged_evaluator_operations"]})
    return FAM.Module(name, {}, net.render())


def _emit_family(B_, D_, p, e, fmt, count, fi, fn, family, sr, sb, ftag, w, library_used, L, shared=None, spec=None) -> bool:
    """One library instance per lane of the declared family's module for
    the function: X in from the lane's unpacked operand, X out packed by
    the engine under the run's rounding, the specials handled here; the
    full-value table families return the pattern. False when the library
    has no module for the function (the seed keeps its own evaluator)."""
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.fp import Geom
    from chialu.targets.rtl.families.sfu import PATTERN_FAMILIES
    pattern = family[0] in PATTERN_FAMILIES
    if pattern:
        from chialu.targets.rtl.families.sfu_control_table import controlled_table
        m = shared or controlled_table([fn], fmt, family, spec)
    else:
        m = shared or FAM.sfu_module(fn, fmt, Geom.of_engine(e), family[0], family[1])
    if m is None:
        raise ValueError(f"requested SFU family {family[0]} cannot generate {fn} on {fmt.name}")
    for n_, t_ in FAM.module_texts(m.name, m.text).items():
        collect_modules(library_used, ((n_, t_),))
    XT = e.XT
    D_.append(f"  // structure core: family {family[0]} realized by the library module {m.name} ({fn})")
    for i in range(count):
        tmp = f"{p}_shared_{i}" if shared else f"{p}_f{fi}_{i}"
        declare = not shared or fi == 0
        sel = ".fn_sel(fn_sel), " if shared else ""
        if pattern:
            if declare:
                D_.append(f"  logic [{w-1}:0] {tmp}_yb;")
                D_.append(f"  logic [{FW-1}:0] {tmp}_flags;")
                word = f"sr_rnd[{i*sb} +: {sb}]" if sr else f"{sb}'d0"
                D_.append(f"  {m.name} u_{tmp} ({sel}.x(x[{i*w} +: {w}]), .rnd(rnd), .daz(daz), .ftz(ftz), "
                          f".word({word}), .y({tmp}_yb), .flags({tmp}_flags));")
            B_.append(f"        y_{p}[{i*w} +: {w}] = {tmp}_yb;")
            B_.append(f"        fl_{p}[{i*FW} +: {FW}] = {tmp}_flags;")
            continue
        if declare:
            D_.append(f"  logic [{XT-1}:0] {tmp}_yx; logic {tmp}_inv, {tmp}_dz; logic [{FW+_core(fmt).width-1}:0] {tmp}_pk;")
            D_.append(f"  {m.name} u_{tmp} ({sel}.x({p}_x{i}), .y({tmp}_yx), .inv({tmp}_inv), .dz({tmp}_dz));")
        word = f"sr_rnd[{i*sb} +: {sb}]" if sr else f"{sb}'d0"
        B_.append(f"        {tmp}_pk = {p}_pack_{ftag}({tmp}_yx, rnd, {word}, ftz);")
        pw = _core(fmt).width
        out = f"{tmp}_pk[{pw-1}:0]"
        if isinstance(fmt, X87Format):
            out = f"{{{tmp}_pk[78], {tmp}_pk[77:63], ({tmp}_pk[77:63] != 0) ? 1'b1 : 1'b0, {tmp}_pk[62:0]}}"
        sp = f"{p}_x{i}[{XT-1}:{XT-2}]"
        sg = f"{p}_x{i}[{XT-3}]"
        target_y, target_fl = f"y_{p}[{i*w} +: {w}]", f"fl_{p}[{i*FW} +: {FW}]"
        den = f"({p}_den{i} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0)"
        B_.append(f"        {target_y} = {out};")
        B_.append(f"        {target_fl} = {tmp}_pk[{FW+pw-1}:{pw}]"
                  f" | ({tmp}_inv ? ({FW}'d1 << {flag_bit('invalid')}) : {FW}'d0)"
                  f" | ({tmp}_dz ? ({FW}'d1 << {flag_bit('div_zero')}) : {FW}'d0) | {den};")
        output_sp = f"{tmp}_yx[{XT-1}:{XT-2}]"
        if not isinstance(fmt, PositFormat) and _core(fmt).signed and not _core(fmt).exp_only:
            # zero_sign is an integer-encoding convention. Preserve the
            # sign of an exact floating zero supplied by the SFU program.
            B_.append(f"        if ({output_sp} == 2'd0 && {tmp}_yx[{e.XW}:0] == 0) "
                      f"{target_y} = {tmp}_yx[{XT-3}] ? {w}'d{1 << (w-1)} : {w}'d0;")
        if fn in ("sin", "cos"):
            # A nonzero finite binary argument has an irrational sine or
            # cosine. An exactly representable approximation is still
            # inexact relative to that function value.
            finite_nonzero = f"({sp} == 2'd0 && {p}_x{i}[{e.XW}:0] != 0)"
            B_.append(f"        if {finite_nonzero} begin fl_{p}[{i*FW+flag_bit('inexact')}] = 1'b1;")
            if not isinstance(fmt, PositFormat) and not _core(fmt).exp_only:
                c = _core(fmt)
                exponent_offset = c.man_bits + (1 if isinstance(fmt, X87Format) else 0)
                if (spec or {}).get("tininess", "after") == "after":
                    B_.append(f"          fl_{p}[{i*FW+flag_bit('underflow')}] = (y_{p}[{i*w+exponent_offset} +: {c.exp_bits}] == 0);")
                elif fn == "sin":
                    exponent = f"x[{i*w+exponent_offset} +: {c.exp_bits}]"
                    mantissa = f"x[{i*w} +: {c.man_bits}]"
                    B_.append(f"          if ({exponent} == 0 || ({exponent} == 1 && {mantissa} == 0)) "
                              f"fl_{p}[{i*FW+flag_bit('underflow')}] = 1'b1;")
            B_.append("        end")
        invalid_bits, invalid_flags = _scalar_invalid_result(fmt, spec)
        B_.append(f"        if ({output_sp} == 2'd1) begin {target_y} = {w}'d{invalid_bits}; "
                  f"{target_fl} = {FW}'d{_flag_constant(invalid_flags)} | {den}; end")
        nan_expr = f"x[{i*w} +: {w}]" if (spec or {}).get("nan_payload") == "propagate" else f"{w}'d{invalid_bits}"
        positive_bits, positive_flags = _scalar_infinity_result(fn, fmt, False, spec)
        negative_bits, negative_flags = _scalar_infinity_result(fn, fmt, True, spec)
        B_.append(f"        if ({sp} == 2'd1) begin {target_y} = {nan_expr}; "
                  f"{target_fl} = {FW}'d{_flag_constant(invalid_flags)} | {den}; end")
        B_.append(f"        else if ({sp} == 2'd2) begin {target_y} = {sg} ? {w}'d{negative_bits} : {w}'d{positive_bits}; "
                  f"{target_fl} = ({sg} ? {FW}'d{_flag_constant(negative_flags)} : {FW}'d{_flag_constant(positive_flags)}) | {den}; end")
    return True


def _emit_vector_family(B_, D_, p, e, fmt, count, fi, fn, family, sr, sb, ftag, w, library_used, L, shared=None) -> bool:
    """One library instance per mode of the softmax_layernorm family's
    module for a vector function: every lane's X in, every lane's X out
    packed by the engine, a special operand making every lane NaN with
    the invalid flag."""
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.fp import Geom
    m = shared or FAM.sfu_vector_module(fn, fmt, Geom.of_engine(e), count, family[0], family[1])
    if m is None:
        raise ValueError(f"requested SFU family {family[0]} cannot generate {fn} over {count} lanes of {fmt.name}")
    for n_, t_ in FAM.module_texts(m.name, m.text).items():
        collect_modules(library_used, ((n_, t_),))
    XT = e.XT
    tmp = f"{p}_shared" if shared else f"{p}_f{fi}"
    declare = not shared or fi == 0
    D_.append(f"  // structure core: family {family[0]} realized by the library module {m.name} ({fn} over {count} lanes)")
    conns = ", ".join(f".x{i}({p}_x{i}), .y{i}({tmp}_yx{i})" for i in range(count))
    if declare:
        D_.append(f"  logic [{XT-1}:0] " + ", ".join(f"{tmp}_yx{i}" for i in range(count)) + f"; logic {tmp}_inv;")
        D_.append(f"  {m.name} u_{tmp} (" + (".fn_sel(fn_sel), " if shared else "") + f"{conns}, .inv({tmp}_inv));")
    sp_nan, _pinf, _ninf = _special_outputs(fn if fn not in S.VECTOR_FNS else "exp2", fmt)
    pw = _core(fmt).width
    for i in range(count):
        if declare:
            D_.append(f"  logic [{FW+pw-1}:0] {tmp}_pk{i};")
        word = f"sr_rnd[{i*sb} +: {sb}]" if sr else f"{sb}'d0"
        B_.append(f"        {tmp}_pk{i} = {p}_pack_{ftag}({tmp}_yx{i}, rnd, {word}, ftz);")
        out = f"{tmp}_pk{i}[{pw-1}:0]"
        if isinstance(fmt, X87Format):
            out = f"{{{tmp}_pk{i}[78], {tmp}_pk{i}[77:63], ({tmp}_pk{i}[77:63] != 0) ? 1'b1 : 1'b0, {tmp}_pk{i}[62:0]}}"
        B_.append(f"        y_{p}[{i*w} +: {w}] = {tmp}_inv ? {w}'d{sp_nan} : {out};")
        B_.append(f"        fl_{p}[{i*FW} +: {FW}] = ({tmp}_inv ? ({FW}'d1 << {flag_bit('invalid')}) : {tmp}_pk{i}[{FW+pw-1}:{pw}])"
                  f" | ({p}_den{i} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0);")
    return True


def _emit_block_family(B_, D_, p, e, fmt, working, count, fi, fn, family,
                       sr, sb, ftag, library_used, shared=None):
    """Evaluate decoded block elements with the selected family, then quantize once."""
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.fp import Geom
    from chialu.targets.rtl.families.sfu import PATTERN_FAMILIES
    vector = fn in S.VECTOR_FNS
    size, width, XT = fmt.size, fmt.width, e.XT
    lanes = count * size
    if family[0] in PATTERN_FAMILIES:
        raise ValueError("pattern-indexed SFU tables require a scalar format; decoded block values have a shared scale")
    module = shared or (FAM.sfu_vector_module(fn, working, Geom.of_engine(e), lanes, family[0], family[1])
                        if vector else FAM.sfu_module(fn, working, Geom.of_engine(e), family[0], family[1]))
    if module is None:
        raise ValueError(f"requested SFU family {family[0]} cannot generate {fn} on block format {fmt.name}")
    for name, text in FAM.module_texts(module.name, module.text).items():
        collect_modules(library_used, ((name, text),))
    tmp = f"{p}_shared" if shared else f"{p}_f{fi}"
    declare = not shared or fi == 0
    sel = ".fn_sel(fn_sel), " if shared else ""
    if declare:
        for lane in range(lanes):
            D_.append(f"  logic [{XT-1}:0] {tmp}_yx{lane};")
        if vector:
            D_.append(f"  logic {tmp}_inv;")
            conns = ", ".join(f".x{i}({p}_x{i}), .y{i}({tmp}_yx{i})" for i in range(lanes))
            D_.append(f"  {module.name} u_{tmp} ({sel}{conns}, .inv({tmp}_inv));")
        else:
            for lane in range(lanes):
                D_.append(f"  logic {tmp}_inv{lane}, {tmp}_dz{lane};")
                D_.append(f"  {module.name} u_{tmp}_{lane} ({sel}.x({p}_x{lane}), .y({tmp}_yx{lane}), "
                          f".inv({tmp}_inv{lane}), .dz({tmp}_dz{lane}));")
        for i in range(count):
            D_.append(f"  logic [{size*XT-1}:0] {tmp}_xs{i}; logic [{width+size*FW-1}:0] {tmp}_q{i};")
    nan, pinf, ninf = _special_outputs("exp2" if vector else fn, working)
    for i in range(count):
        for j in range(size):
            lane = i * size + j
            sp, sg = f"{p}_x{lane}[{XT-1}:{XT-2}]", f"{p}_x{lane}[{XT-3}]"
            if vector:
                value = f"{tmp}_inv ? {p}_mkx(2'd1, 1'b0, 0, 0, 1'b0) : {tmp}_yx{lane}"
            else:
                value = (f"({sp} == 2'd1) ? {p}_x({p}_unpack_wf({working.width}'d{nan}, 1'b0)) : "
                         f"({sp} == 2'd2) ? {p}_x({p}_unpack_wf({sg} ? {working.width}'d{ninf} : "
                         f"{working.width}'d{pinf}, 1'b0)) : {tmp}_yx{lane}")
            B_.append(f"        {tmp}_xs{i}[{j*XT} +: {XT}] = {value};")
        words = f"sr_rnd[{i*size*sb} +: {size*sb}]" if sr else f"{size*sb}'d0"
        B_.append(f"        {tmp}_q{i} = {p}_quant_{ftag}({tmp}_xs{i}, rnd, {words}, ftz);")
        B_.append(f"        y_{p}[{i*width} +: {width}] = {tmp}_q{i}[{width-1}:0];")
        for j in range(size):
            lane = i * size + j
            invalid = f"{tmp}_inv" if vector else f"{tmp}_inv{lane}"
            dz = "1'b0" if vector else f"{tmp}_dz{lane}"
            B_.append(f"        fl_{p}[{lane*FW} +: {FW}] = {tmp}_q{i}[{width+j*FW} +: {FW}] "
                      f"| ({invalid} ? ({FW}'d1 << {flag_bit('invalid')}) : {FW}'d0) "
                      f"| ({dz} ? ({FW}'d1 << {flag_bit('div_zero')}) : {FW}'d0) "
                      f"| ({p}_den{lane} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0);")
    return True


def _seg_index_expr(fmt, xb, K, D_=None, tmp=None):
    """SV expression of the segment of pattern xb: the value-ordered index
    scaled by K / 2^w (the index goes through a declared temporary)."""
    w = fmt.width
    if isinstance(fmt, PositFormat):
        u = f"({xb} ^ ({w}'d1 << {w-1}))"                       # two's complement + 2^(w-1)
    else:
        core = fmt.core if isinstance(fmt, X87Format) else fmt
        if getattr(core, "signed", True):
            u = f"({xb}[{w-1}] ? (({w}'d1 << {w-1}) - 1 - ({xb} & (({w}'d1 << {w-1}) - 1))) : (({w}'d1 << {w-1}) | {xb}))"
        else:
            u = xb
    if D_ is not None:
        D_.append(f"  logic [{w-1}:0] {tmp}_u; assign {tmp}_u = {u};")
        u = f"{tmp}_u"
    return f"(({{{{{K.bit_length()}{{1'b0}}}}, {u}}} * {K}) >> {w})"


def _emit_pwl(B_, D_, p, e, fmt, base, block, count, size, fi, K, sr, sb, ftag, w):
    """y = c0 + c1 * (x - x_k) through the engine, rounded once."""
    XT = e.XT
    bw = base.width
    kw = K.bit_length()
    for i in range(count):
        if block:
            # per element: the decoded value packed into the working float, the
            # segment looked up on that pattern, the polynomial through the engine
            tmp = f"{p}_f{fi}_{i}"
            ww = base.width                      # the working float's width
            D_.append(f"  logic [{size*XT-1}:0] {tmp}_xs; logic [{size*FW+w-1}:0] {tmp}_q;")
            for j in range(size):
                k = i * size + j
                D_.append(f"  logic [{FW+ww-1}:0] {tmp}_wp{j}; assign {tmp}_wp{j} = {p}_pack_wf({p}_x{k}, 3'd0, {sb}'d0, 1'b0);")
                D_.append(f"  logic [{ww-1}:0] {tmp}_eb{j}; assign {tmp}_eb{j} = {tmp}_wp{j}[{ww-1}:0];")
                eb = f"{tmp}_eb{j}"
                seg = _seg_index_expr(base, eb, K, D_, f"{tmp}_e{j}")
                D_.append(f"  logic [{kw+ww-1}:0] {tmp}_k{j}; assign {tmp}_k{j} = {seg};")
                D_.append(f"  logic [{kw-1}:0] {tmp}_ki{j}; assign {tmp}_ki{j} = {tmp}_k{j}[{kw-1}:0];")
                D_.append(f"  logic [{3*ww-1}:0] {tmp}_c{j}; assign {tmp}_c{j} = {p}_pwl{fi}[{tmp}_ki{j}];")
                D_.append(f"  logic [{XT-1}:0] {tmp}_px_{j}, {tmp}_p1_{j}, {tmp}_p0_{j}, {tmp}_pr_{j};")
                D_.append(f"  assign {tmp}_px_{j} = {p}_x({p}_unpack_wf({tmp}_c{j}[{3*ww-1}:{2*ww}], 1'b0));")
                D_.append(f"  assign {tmp}_p1_{j} = {p}_x({p}_unpack_wf({tmp}_c{j}[{2*ww-1}:{ww}], 1'b0));")
                D_.append(f"  assign {tmp}_p0_{j} = {p}_x({p}_unpack_wf({tmp}_c{j}[{ww-1}:0], 1'b0));")
                B_.append(f"        {tmp}_pr_{j} = {p}_add({tmp}_p0_{j}, {p}_mul({tmp}_p1_{j}, {p}_add({p}_x{k}, {tmp}_px_{j}, 1'b1)), 1'b0);")
                sp = f"{p}_x{k}[{XT-1}:{XT-2}]"
                sg = f"{p}_x{k}[{XT-3}]"
                B_.append(f"        {tmp}_xs[{j*XT} +: {XT}] = ({sp} == 2'd1) ? {p}_x({p}_unpack_wf({p}_sp{fi}_nan, 1'b0)) : "
                          f"({sp} == 2'd2) ? {p}_x({p}_unpack_wf({sg} ? {p}_sp{fi}_ninf : {p}_sp{fi}_pinf, 1'b0)) : {tmp}_pr_{j};")
            words = f"sr_rnd[{i*size*sb} +: {size*sb}]" if sr else f"{size*sb}'d0"
            B_.append(f"        {tmp}_q = {p}_quant_{ftag}({tmp}_xs, rnd, {words}, ftz);")
            B_.append(f"        y_{p}[{i*w} +: {w}] = {tmp}_q[{w-1}:0];")
            for j in range(size):
                B_.append(f"        fl_{p}[{(i*size+j)*FW} +: {FW}] = {tmp}_q[{w + j*FW} +: {FW}] | ({p}_den{i*size+j} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0);")
            continue
        tmp = f"{p}_f{fi}_{i}"
        D_.append(f"  logic [{w-1}:0] {tmp}_xb; assign {tmp}_xb = x[{i*w} +: {w}];")
        xb = f"{tmp}_xb"
        seg = _seg_index_expr(fmt, xb, K, D_, tmp)
        D_.append(f"  logic [{kw+w-1}:0] {tmp}_k; assign {tmp}_k = {seg};")
        D_.append(f"  logic [{kw-1}:0] {tmp}_ki; assign {tmp}_ki = {tmp}_k[{kw-1}:0];")
        D_.append(f"  logic [{3*w-1}:0] {tmp}_c; assign {tmp}_c = {p}_pwl{fi}[{tmp}_ki];")
        D_.append(f"  logic [{XT-1}:0] {tmp}_r; logic [{FW+_core(fmt).width-1}:0] {tmp}_pk;")

        def unp(sl):
            if isinstance(fmt, X87Format):
                return f"{p}_x({p}_unpack_s({{{sl}[79], {sl}[78:64], {sl}[62:0]}}, 1'b0))"
            return f"{p}_x({p}_unpack_s({sl}, 1'b0))"
        xk = unp(f"{tmp}_c[{3*w-1}:{2*w}]")
        c1 = unp(f"{tmp}_c[{2*w-1}:{w}]")
        c0 = unp(f"{tmp}_c[{w-1}:0]")
        word = f"sr_rnd[{i*sb} +: {sb}]" if sr else f"{sb}'d0"
        B_.append(f"        {tmp}_r = {p}_add({c0}, {p}_mul({c1}, {p}_add({p}_x{i}, {xk}, 1'b1)), 1'b0);")
        B_.append(f"        {tmp}_pk = {p}_pack_{ftag}({tmp}_r, rnd, {word}, ftz);")
        pw = _core(fmt).width
        out = f"{tmp}_pk[{pw-1}:0]"
        if isinstance(fmt, X87Format):
            out = f"{{{tmp}_pk[78], {tmp}_pk[77:63], ({tmp}_pk[77:63] != 0) ? 1'b1 : 1'b0, {tmp}_pk[62:0]}}"
        sp = f"{p}_x{i}[{XT-1}:{XT-2}]"
        sg = f"{p}_x{i}[{XT-3}]"
        B_.append(f"        y_{p}[{i*w} +: {w}] = ({sp} == 2'd1) ? {p}_sp{fi}_nan : ({sp} == 2'd2) ? ({sg} ? {p}_sp{fi}_ninf : {p}_sp{fi}_pinf) : {out};")
        B_.append(f"        fl_{p}[{i*FW} +: {FW}] = (({sp} != 2'd0) ? {FW}'d0 : {tmp}_pk[{FW+pw-1}:{pw}]) | ({p}_den{i} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0);")


def _emit_slot(B_, D_, p, e, fmt, count, si, sl, sr, sb, ftag, w, w_max):
    """The slot evaluator on its table: exact polynomial through the
    engine, one rounding; a NaN / NaR / infinite x or x_k gives NaN."""
    XT, XW = e.XT, e.XW
    K = sl["segments"]
    nc = S.coeff_words(sl)
    kw = max(1, (K - 1).bit_length())
    posit = isinstance(fmt, PositFormat)
    for i in range(count):
        tmp = f"{p}_s{si}_{i}"
        D_.append(f"  logic [{w-1}:0] {tmp}_xb; assign {tmp}_xb = x[{i*w} +: {w}];")
        xb = f"{tmp}_xb"
        seg = _seg_index_expr(fmt, xb, K, D_, tmp)
        D_.append(f"  logic [{K.bit_length()+w-1}:0] {tmp}_k; assign {tmp}_k = {seg};")
        D_.append(f"  logic [{kw-1}:0] {tmp}_ki; assign {tmp}_ki = {tmp}_k[{kw-1}:0];")
        D_.append(f"  logic [{nc*w_max-1}:0] {tmp}_c; assign {tmp}_c = tbl{si}[{tmp}_ki];")
        # x_k: the first pattern of the segment k (a constant per segment)
        D_.append(f"  logic [{w-1}:0] {tmp}_xk;")
        D_.append("  always_comb begin")
        D_.append(f"    case ({tmp}_ki)")
        for k in range(K):
            xk = S.segment_start_value(fmt, k, K)
            if xk is None:
                pat = None
            else:
                pat = fmt.encode(xk) if not posit else fmt.round(xk)
            D_.append(f"      {kw}'d{k}: {tmp}_xk = {w}'d{pat if pat is not None else 0};")
        D_.append(f"      default: {tmp}_xk = {w}'d0;")
        D_.append("    endcase")
        D_.append("  end")
        invalid_xk = " || ".join(f"({tmp}_ki == {kw}'d{k})" for k in range(K) if S.segment_start_value(fmt, k, K) is None) or "1'b0"

        def unp(sl_):
            if isinstance(fmt, X87Format):
                return f"{p}_x({p}_unpack_s({{{sl_}[79], {sl_}[78:64], {sl_}[62:0]}}, 1'b0))"
            return f"{p}_x({p}_unpack_s({sl_}, 1'b0))"
        D_.append(f"  logic [{XT-1}:0] {tmp}_r, {tmp}_d, {tmp}_c0x, {tmp}_c1x, {tmp}_c2x, {tmp}_xkx; logic [{FW+_core(fmt).width-1}:0] {tmp}_pk; logic {tmp}_bad;")
        D_.append(f"  assign {tmp}_c0x = {unp(f'{tmp}_c[{w-1}:0]')};")
        D_.append(f"  assign {tmp}_c1x = {unp(f'{tmp}_c[{w_max + w - 1}:{w_max}]')};")
        if nc == 3:
            D_.append(f"  assign {tmp}_c2x = {unp(f'{tmp}_c[{2*w_max + w - 1}:{2*w_max}]')};")
        else:
            D_.append(f"  assign {tmp}_c2x = '0;")
        D_.append(f"  assign {tmp}_xkx = {unp(tmp + '_xk')};")
        c0, c1, c2 = f"{tmp}_c0x", f"{tmp}_c1x", f"{tmp}_c2x"
        word = f"sr_rnd[{i*sb} +: {sb}]" if sr else f"{sb}'d0"
        B_.append(f"        {tmp}_d = {p}_add({p}_x{i}, {tmp}_xkx, 1'b1);")
        if nc == 3:
            B_.append(f"        {tmp}_r = {p}_add({p}_add({c0}, {p}_mul({c1}, {tmp}_d), 1'b0), {p}_mul({c2}, {p}_mul({tmp}_d, {tmp}_d)), 1'b0);")
        else:
            B_.append(f"        {tmp}_r = {p}_add({c0}, {p}_mul({c1}, {tmp}_d), 1'b0);")
        # invalid: x special, x_k special, or a special coefficient
        bad = f"({p}_x{i}[{XT-1}:{XT-2}] != 2'd0) || ({invalid_xk})"
        for cexpr in ([c0, c1] + ([c2] if nc == 3 else [])):
            bad += f" || ({cexpr}[{XT-1}:{XT-2}] != 2'd0)"
        B_.append(f"        {tmp}_bad = {bad};")
        B_.append(f"        if ({tmp}_bad) {tmp}_r = {p}_mkx(2'd1, 1'b0, 0, 0, 1'b0);")
        B_.append(f"        {tmp}_pk = {p}_pack_{ftag}({tmp}_r, rnd, {word}, ftz);")
        pw = _core(fmt).width
        out = f"{tmp}_pk[{pw-1}:0]"
        if isinstance(fmt, X87Format):
            out = f"{{{tmp}_pk[78], {tmp}_pk[77:63], ({tmp}_pk[77:63] != 0) ? 1'b1 : 1'b0, {tmp}_pk[62:0]}}"
        core = _core(fmt)
        if not posit and not core.has_nan:
            inv_zero = "1" if False else "0"
            maxb = core._max_finite_bits()
            B_.append(f"        y_{p}[{i*w} +: {w}] = {tmp}_bad ? {w}'d{maxb} : {out};")
        else:
            B_.append(f"        y_{p}[{i*w} +: {w}] = {out};")
        B_.append(f"        fl_{p}[{i*FW} +: {FW}] = ({tmp}_bad ? (({FW}'d1 << {flag_bit('invalid')}) | {tmp}_pk[{FW+pw-1}:{pw}]) : {tmp}_pk[{FW+pw-1}:{pw}]) | ({p}_den{i} ? ({FW}'d1 << {flag_bit('denormal')}) : {FW}'d0);")
