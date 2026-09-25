"""Generated checker RTL for chialu.VecDotAcc: residue on the exact
integer accumulation where the relation survives the endpoint, the
reference copy (chialu.targets.rtl.dot_seed) otherwise, the SR window
and check_flags as for the ALU checker."""
from __future__ import annotations

from chialu.targets.rtl.engine import FORCE_NONE, FORCE_RAZ, FORCE_RTZ
from chialu.targets.rtl.residue import residue_bits, residue_module
from chialu.verify.formats import BlockFormat


def _dot_residue_ok(spec, lay, m) -> bool:
    """Residue rides the accumulator when a, b, c and d are integer
    patterns in two's complement or unsigned, d wraps, the contract is
    fused and the exact sum of products cannot itself wrap d
    (w_d >= 2 w_ab + log2(products) + 1)."""
    from chialu.verify.formats import FixedFormat, IntFormat, ScaledIntFormat
    fab, fc, fd = m["fab"], m["fc"], m["fd"]

    def int_pat(f):
        return isinstance(f, IntFormat) and not isinstance(f, ScaledIntFormat) \
            and f.encoding in ("twos_complement", "unsigned")
    if not (int_pat(fab) and int_pat(fd)) or (lay["accumulate"] and not int_pat(fc)):
        return False
    if spec.get("dot_contract", "fused") != "fused" or spec.get("overflow", "wrap") != "wrap":
        return False
    if lay["accumulate"] and fc.width != fd.width:
        return False
    from chialu.verify import dot_ref as D
    n = D.n_products(m)
    return fd.width >= 2 * fab.width + n.bit_length() + 1


def dot_checker_sv(spec: dict, M: int, name: str = "dot_checker") -> tuple[str, list]:
    """The checker of a VecDotAcc spec: residue on the exact integer
    accumulation (r(d - c) = sum r(a_i) r(b_i) mod M, the wrap of d
    recovered as the signed difference) where _dot_residue_ok holds,
    the reference copy (sv_dot) otherwise; the SR window and check_flags
    as for the ALU checker."""
    from chialu.targets.rtl.dot_seed import dot_ref_module
    from chialu.verify import dot_ref as D
    spec = D.normalize_dot_spec(spec)
    lay = D.dot_layout(spec)
    modes = lay["modes"]
    d_w, v_max = lay["d_w"], lay["v_max"]
    flags = lay["flags"]
    nf = len(flags)
    check_flags = bool(spec.get("check_flags"))
    check_sr_vals = list(spec.get("check_sr") or [True])
    sr = lay["sr"]
    window_possible = sr and (False in check_sr_vals)
    window_runtime = sr and len(check_sr_vals) > 1
    mdw = max(1, (len(modes) - 1).bit_length())
    k = residue_bits(M)
    core_in = lay["core_in"]
    residue_modes = {mi for mi, m in enumerate(modes) if _dot_residue_ok(spec, lay, m) and not check_flags}
    protected = ["dot"] if residue_modes else []
    mods = [dot_ref_module(spec, f"{name}_ref", FORCE_NONE)]
    if window_possible:
        mods.append(dot_ref_module(spec, f"{name}_ref_t", FORCE_RTZ))
        mods.append(dot_ref_module(spec, f"{name}_ref_u", FORCE_RAZ))
    widths = set()
    for mi in residue_modes:
        widths.add(modes[mi]["fab"].width)
        widths.add(modes[mi]["fd"].width)
    for w in sorted(widths):
        mods.append(residue_module(f"{name}_res{w}", w, M))
    ports = [f"  input  logic [{p.width-1}:0] {p.name}" for p in core_in]
    for p in lay["chk_extra"]:
        ports.append(f"  input  logic [{p.width-1}:0] {p.name}")
    ports.append(f"  input  logic [{d_w-1}:0] d")
    if nf and check_flags:
        ports.append(f"  input  logic [{v_max*nf-1}:0] flags")
    ports.append("  output logic check_err")
    decl, body = [], []
    conns = ", ".join(f".{p.name}({p.name})" for p in core_in)
    decl.append(f"  logic [{d_w-1}:0] d_ref;")
    if nf:
        decl.append(f"  logic [{v_max*nf-1}:0] flags_ref;")
    decl.append(f"  {name}_ref u_ref ({conns}, .d(d_ref)" + (", .flags(flags_ref)" if nf else "") + ");")
    if window_possible:
        for sfx in ("t", "u"):
            decl.append(f"  logic [{d_w-1}:0] d_{sfx};")
            if nf:
                decl.append(f"  logic [{v_max*nf-1}:0] fl_{sfx}_unused;")
            decl.append(f"  {name}_ref_{sfx} u_{sfx} ({conns}, .d(d_{sfx})" + (f", .flags(fl_{sfx}_unused)" if nf else "") + ");")
        rnds = list(spec["rounding"])
        if len(rnds) > 1:
            sel_w = max(1, (len(rnds) - 1).bit_length())
            decl.append("  logic sr_now; assign sr_now = " + " || ".join(f"(rounding_sel == {sel_w}'d{i})" for i, r in enumerate(rnds) if r == "SR") + ";")
        else:
            decl.append("  logic sr_now; assign sr_now = 1'b1;")
        if window_runtime:
            decl.append(f"  logic win; assign win = sr_now && !(check_sr_sel ? 1'b{1 if check_sr_vals[1] else 0} : 1'b{1 if check_sr_vals[0] else 0});")
        else:
            decl.append("  logic win; assign win = sr_now;")
    dup = ["(d != d_ref)"] + (["(flags != flags_ref)"] if nf and check_flags else [])
    decl.append(f"  logic err_dup; assign err_dup = {' | '.join(dup)};")
    verdict = {}
    for mi in residue_modes:
        m = modes[mi]
        fab, fc, fd = m["fab"], m["fc"], m["fd"]
        wab, wd = fab.width, fd.width
        S = D.n_outputs(m)
        n = D.n_products(m)
        sa = fab.encoding == "twos_complement"
        sd = fd.encoding == "twos_complement"
        c_ab, c_d = (1 << wab) % M, (1 << wd) % M
        KW = k + 2
        errs = []
        for g in range(S):
            terms = []
            for t in range(g * n, (g + 1) * n):
                for src in ("a", "b"):
                    nm = f"r{src}{mi}_{t}"
                    decl.append(f"  logic [{k-1}:0] {nm};")
                    decl.append(f"  {name}_res{wab} u{nm} (.x({src}[{t*wab} +: {wab}]), .r({nm}));")
                if sa:
                    decl.append(f"  logic [{KW-1}:0] sa{mi}_{t}, sb{mi}_{t};")
                    decl.append(f"  assign sa{mi}_{t} = ({KW}'d{2*M} + ra{mi}_{t} - (a[{t*wab+wab-1}] ? {KW}'d{c_ab} : {KW}'d0)) % {KW}'d{M};")
                    decl.append(f"  assign sb{mi}_{t} = ({KW}'d{2*M} + rb{mi}_{t} - (b[{t*wab+wab-1}] ? {KW}'d{c_ab} : {KW}'d0)) % {KW}'d{M};")
                    terms.append(f"((sa{mi}_{t} * sb{mi}_{t}) % {2*KW}'d{M})")
                else:
                    terms.append(f"((ra{mi}_{t} * rb{mi}_{t}) % {2*KW}'d{M})")
            # P = d - c as a wd-bit signed difference (two's complement) or unsigned wrap
            decl.append(f"  logic [{wd-1}:0] pd{mi}_{g};")
            if lay["accumulate"]:
                decl.append(f"  assign pd{mi}_{g} = d[{g*wd} +: {wd}] - c[{g*wd} +: {wd}];")
            else:
                decl.append(f"  assign pd{mi}_{g} = d[{g*wd} +: {wd}];")
            decl.append(f"  logic [{k-1}:0] rp{mi}_{g};")
            decl.append(f"  {name}_res{wd} urp{mi}_{g} (.x(pd{mi}_{g}), .r(rp{mi}_{g}));")
            decl.append(f"  logic [{KW-1}:0] rps{mi}_{g}, sum{mi}_{g};")
            if sd:
                decl.append(f"  assign rps{mi}_{g} = ({KW}'d{2*M} + rp{mi}_{g} - (pd{mi}_{g}[{wd-1}] ? {KW}'d{c_d} : {KW}'d0)) % {KW}'d{M};")
            else:
                decl.append(f"  assign rps{mi}_{g} = rp{mi}_{g};")
            decl.append(f"  assign sum{mi}_{g} = (" + " + ".join(f"{{{{{KW}{{1'b0}}}}, {tm}}}" for tm in terms) + f") % {2*KW}'d{M};")
            errs.append(f"(rps{mi}_{g} != sum{mi}_{g})")
        wout = S * wd
        hi_zero = f" | (d[{d_w-1}:{wout}] != {d_w-wout}'d0)" if wout < d_w else ""
        verdict[mi] = "(" + " | ".join(errs) + f"){hi_zero}"
    body.append("  always_comb begin")
    body.append("    check_err = err_dup;")
    if len(modes) > 1:
        body.append("    case (mode)")
    for mi in range(len(modes)):
        if mi in verdict:
            expr = verdict[mi]
        elif window_possible:
            m = modes[mi]
            fd = m["fd"]
            S = D.n_outputs(m)
            terms = []
            if isinstance(fd, BlockFormat):
                we, sz, sw = fd.elem.width, fd.size, fd.scale.width
                for j in range(sz):
                    terms.append(f"!(d[{j*we} +: {we}] == d_t[{j*we} +: {we}] || d[{j*we} +: {we}] == d_u[{j*we} +: {we}])")
                terms.append(f"(d[{sz*we} +: {sw}] != d_t[{sz*we} +: {sw}])")
            else:
                for g in range(S):
                    terms.append(f"!(d[{g*fd.width} +: {fd.width}] == d_t[{g*fd.width} +: {fd.width}] || d[{g*fd.width} +: {fd.width}] == d_u[{g*fd.width} +: {fd.width}])")
            wout = fd.width
            if wout < d_w:
                terms.append(f"(d[{d_w-1}:{wout}] != {d_w-wout}'d0)")
            wv = "(" + " | ".join(terms) + ")" + (" | (flags != flags_ref)" if nf and check_flags else "")
            expr = f"win ? ({wv}) : err_dup"
        else:
            expr = "err_dup"
        if len(modes) > 1:
            body.append(f"      {mdw}'d{mi}: check_err = {expr};")
        else:
            body.append(f"    check_err = {expr};")
    if len(modes) > 1:
        body.append("      default: check_err = 1'b1;")
        body.append("    endcase")
    body.append("  end")
    L_ = list(mods) + [f"module {name} (", ",\n".join(ports), ");"] + decl + body + ["endmodule"]
    return "\n".join(L_) + "\n", protected


