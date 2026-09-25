"""The unit-level sharing families: one datapath serving every lane
packing of a unit.

* fam_mul_twin_precision: one W x W partial-product matrix whose
  cross-lane products are gated off by the mode select, Baugh-Wooley
  (or Booth-recoded) per lane and mode, a carry-save reduction whose
  carries are killed at the lane boundaries the mode names, and a
  lane-partitioned final adder; the packed products of the selected
  mode leave on one 2W-bit bus (lane l of a w-bit mode at
  [2w(l+1)-1 : 2wl]).

    module fam_mul_twin_precision_... (input [W-1:0] a, b, input [S-1:0] sel, output [2W-1:0] p);

* fam_add_partitioned: one W-bit adder, in segments of the served lanes' declared adder family, whose
  carry chain is cut at the lane boundaries of the selected mode
  (carry_kill_gate, carry_select_mux, or guard_bit_insertion), a
  carry-in per finest lane and a carry-out per finest lane, so every
  lane's add-class op runs on it at once.

    module fam_add_partitioned_... (input [W-1:0] a, b, input [L-1:0] cin, input [S-1:0] sel, output [W-1:0] s, output [L-1:0] cout);

Both take the served modes as a list of lane widths (one entry per
mode, W divisible by each); sel indexes that list.
"""
from __future__ import annotations

from chialu.targets.rtl.families.mul import Netlist, _cols, _dadda_targets, dedupe_modules


def _pin_tag(pins: dict) -> str:
    """A 48-bit tag of the pins that change the text, for the module name:
    the lane widths and the sign handling are spelled out in the name, and
    every other pin reaches it through this tag."""
    keep = {k: v for k, v in (pins or {}).items()
            if not str(k).startswith("_") and str(k) != "per_lane_signed"}
    if not keep:
        return ""
    import hashlib
    return "_" + hashlib.blake2b(repr(sorted((str(k), str(v)) for k, v in keep.items())).encode(),
                                 digest_size=6).hexdigest()

def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _sub(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _boundaries(W: int, lane_w: int) -> list:
    """The bit positions that begin a lane (above 0)."""
    return list(range(lane_w, W, lane_w))


def twin_precision_sv(W: int, lane_widths: list, signed: list, pins: dict, name: str | None = None) -> tuple:
    """(name, text) of the twin-precision multiplier over the served modes."""
    pins = pins or {}
    per_lane_signed = str(_pin(pins, "per_lane_signed", "True")).lower() in ("true", "1", "yes")
    modes = list(zip(lane_widths, signed))
    S = _clog2(max(2, len(modes)))
    name = name or (f"fam_mul_twin_precision_w{W}_" + "_".join(f"{lw}{'s' if sg else 'u'}" for lw, sg in modes)
                    + ("" if per_lane_signed else "_mag") + _pin_tag(pins))
    if not per_lane_signed and any(sg for _lw, sg in modes):
        # the sign handled outside the matrix: the lanes' magnitudes into an unsigned matrix, each lane's
        # product negated back when the operand signs differ (per mode, selected by sel)
        inner_name = name + "_u"
        _n, inner = twin_precision_sv(W, lane_widths, [False] * len(modes), dict(pins, per_lane_signed="True"), name=inner_name)
        text = [f"// twin_precision_subword (baugh_wooley, signs outside the matrix): the lanes' magnitudes through an unsigned "
                f"gated matrix, each lane's product negated back by the operand signs",
                f"module {name} (input logic [{W-1}:0] a, input logic [{W-1}:0] b, input logic [{S-1}:0] sel, output logic [{2*W-1}:0] p);",
                f"  logic [{W-1}:0] am, bm; logic [{2*W-1}:0] pu, pn;"]
        for mi, (lw, sg) in enumerate(modes):
            L = W // lw
            if sg:
                am = ", ".join(f"(a[{(l+1)*lw-1}] ? -a[{(l+1)*lw-1}:{l*lw}] : a[{(l+1)*lw-1}:{l*lw}])" for l in reversed(range(L)))
                bm = ", ".join(f"(b[{(l+1)*lw-1}] ? -b[{(l+1)*lw-1}:{l*lw}] : b[{(l+1)*lw-1}:{l*lw}])" for l in reversed(range(L)))
                pn = ", ".join(f"((a[{(l+1)*lw-1}] ^ b[{(l+1)*lw-1}]) ? -pu[{2*(l+1)*lw-1}:{2*l*lw}] : pu[{2*(l+1)*lw-1}:{2*l*lw}])" for l in reversed(range(L)))
            else:
                am, bm, pn = "a", "b", "pu"
            text.append(f"  logic [{W-1}:0] am{mi}, bm{mi}; logic [{2*W-1}:0] pn{mi};")
            text.append(f"  assign am{mi} = {{{am}}}; assign bm{mi} = {{{bm}}}; assign pn{mi} = {{{pn}}};")
        text.append("  assign am = " + " : ".join(f"(sel == {S}'d{mi}) ? am{mi}" for mi in range(len(modes))) + " : a;")
        text.append("  assign bm = " + " : ".join(f"(sel == {S}'d{mi}) ? bm{mi}" for mi in range(len(modes))) + " : b;")
        text.append(f"  {inner_name} u_mat (.a(am), .b(bm), .sel(sel), .p(pu));")
        text.append("  assign p = " + " : ".join(f"(sel == {S}'d{mi}) ? pn{mi}" for mi in range(len(modes))) + " : pu;")
        text.append("endmodule")
        return name, "\n".join(text) + "\n" + inner
    nl = Netlist()
    cols = _cols(2 * W)
    # per mode: the lane of a bit, whether it is the lane's sign position
    def lane(mi, k):
        return k // lane_widths[mi]

    def top(mi, k):
        return (k % lane_widths[mi]) == lane_widths[mi] - 1

    sel = [nl.wire(f"sel == {S}'d{mi}", "ms") for mi in range(len(modes))]
    # the partial product a_i b_j is kept when i and j share a lane in the selected mode, inverted when
    # exactly one of them is its lane's sign bit in a signed mode (Baugh-Wooley per lane)
    for i in range(W):
        for j in range(W):
            keep = [mi for mi in range(len(modes)) if lane(mi, i) == lane(mi, j)]
            if not keep:
                continue
            inv = [mi for mi in keep if modes[mi][1] and per_lane_signed and (top(mi, i) != top(mi, j))]
            en = " | ".join(sel[mi] for mi in keep) if len(keep) < len(modes) else "1'b1"
            g = nl.wire(f"a[{i}] & b[{j}]", "pp")
            if inv:
                iv = " | ".join(sel[mi] for mi in inv)
                g = nl.wire(f"{g} ^ ({iv})" if len(inv) < len(modes) else f"~{g}", "pp")
            if en != "1'b1":
                g = nl.wire(f"{g} & ({en})", "pp")
            cols[i + j].append(g)
    # the Baugh-Wooley constants per lane and mode, mode-selected: for a w-bit signed lane at offset o the
    # constant 2^(2o + w) + 2^(2o + 2w - 1) mod 2^(2o + 2w) (the lane's own range)
    for mi, (lw, sg) in enumerate(modes):
        if not (sg and per_lane_signed):
            continue
        const = 0
        for l in range(W // lw):
            o = 2 * l * lw
            const += (1 << (o + lw)) + (1 << (o + 2 * lw - 1))
        for k in range(2 * W):
            if (const >> k) & 1:
                cols[k].append(sel[mi] if len(modes) > 1 else "1'b1")
    # the boundaries where a carry must not cross in some mode, with the kill condition
    kills = {}
    for mi, (lw, sg) in enumerate(modes):
        for b in _boundaries(2 * W, 2 * lw):
            kills.setdefault(b - 1, []).append(sel[mi])
    kill_at = {c: (" | ".join(v) if len(v) < len(modes) else "1'b1") for c, v in kills.items()}
    # the reduction with gated carries at the boundary columns
    n = 2 * W
    h = max(len(c) for c in cols)
    for target in _dadda_targets(h):
        new = [[] for _ in range(n)]
        for c in range(n):
            bits = cols[c]
            k = 0
            gate = kill_at.get(c)
            while len(bits) - k + len(new[c]) > target:
                excess = len(bits) - k + len(new[c]) - target
                if excess >= 2 and len(bits) - k >= 3:
                    s_, cy = nl.fa(bits[k], bits[k + 1], bits[k + 2])
                    k += 3
                elif len(bits) - k >= 2:
                    s_, cy = nl.ha(bits[k], bits[k + 1])
                    k += 2
                else:
                    break
                new[c].append(s_)
                if c + 1 < n:
                    new[c + 1].append(nl.wire(f"{cy} & ~({gate})", "kc") if gate and gate != "1'b1" else ("1'b0" if gate == "1'b1" else cy))
            new[c].extend(bits[k:])
        cols = new
    # the lane-partitioned final adder over the finest boundaries: segments between consecutive kill
    # columns, the carry into a segment killed by the mode
    row_s = [c[0] if len(c) > 0 else "1'b0" for c in cols]
    row_c = [c[1] if len(c) > 1 else "1'b0" for c in cols]
    text = [f"// twin_precision_subword (baugh_wooley{', per-lane signed' if per_lane_signed else ''}): one partial-product matrix "
            f"gated by the mode ({', '.join(f'{W // lw} x {lw}' for lw, _ in modes)}), carries killed at the lane boundaries, "
            f"the packed products on one bus",
            f"module {name} (input logic [{W-1}:0] a, input logic [{W-1}:0] b, input logic [{S-1}:0] sel, output logic [{2*W-1}:0] p);",
            f"  logic [{S-1}:0] sel_u; assign sel_u = sel;"]
    text += nl.render()
    text += [f"  logic [{n-1}:0] row_s, row_c;",
             "  assign row_s = {" + ", ".join(reversed(row_s)) + "};",
             "  assign row_c = {" + ", ".join(reversed(row_c)) + "};"]
    from chialu.targets.rtl import families as FAM
    cpa_fam = str(_pin(pins, "lane_cpa.family", "ripple_carry"))
    cpa_pins = _sub(pins, "lane_cpa.")
    bounds = sorted(kill_at)
    segs = []
    lo = 0
    for c in bounds:
        segs.append((lo, c + 1))
        lo = c + 1
    if lo < n:
        segs.append((lo, n))
    extra = ""
    text.append(f"  logic [{len(segs)}:0] cc; assign cc[0] = 1'b0;")
    for si, (lo, hi) in enumerate(segs):
        wdt = hi - lo
        kill = kill_at.get(lo - 1, "1'b0") if lo > 0 else "1'b1"
        text.append(f"  logic ci{si}; assign ci{si} = cc[{si}] & ~({kill});")
        # through the binary contract, as every other binary CPA slot: a lane CPA may be declared an
        # end_around_carry adder, whose native module adds modulo 2^n-1 / 2^n+1 / p
        from .binary_cpa import adder_module as binary_adder
        m = binary_adder(cpa_fam, cpa_pins, wdt)
        if m is None:
            text.append(f"  assign {{cc[{si+1}], p[{hi-1}:{lo}]}} = row_s[{hi-1}:{lo}] + row_c[{hi-1}:{lo}] + ci{si};")
        else:
            ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
            text.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u_cpa{si} (.a(row_s[{hi-1}:{lo}]), .b(row_c[{hi-1}:{lo}]), .cin(ci{si}), .s(p[{hi-1}:{lo}]), .cout(cc[{si+1}]));")
            if m.text:
                extra += m.text
    text.append("endmodule")
    return name, "\n".join(text) + "\n" + dedupe_modules(extra)


def partitioned_adder_sv(W: int, lane_widths: list, pins: dict, name: str | None = None, segment=None) -> tuple:
    """(name, text) of the lane-partitioned adder: segments of the finest
    lane width, each an adder of `segment` = (family, pins), which is the
    adder family the served lanes declare (`core.adder.m*`; ripple_carry
    when none is given), the carry between segments killed
    (carry_kill_gate), replaced by the lane's carry-in (carry_select_mux)
    or absorbed by a guard bit (guard_bit_insertion) where the selected
    mode has a boundary; a carry-in and a carry-out per finest lane."""
    pins = pins or {}
    mech = str(_pin(pins, "boundary_mechanism", "carry_kill_gate"))
    bfam, bpins = (str(segment[0]), dict(segment[1] or {})) if segment else ("ripple_carry", {})
    fine = min(lane_widths)
    L = W // fine
    S = _clog2(max(2, len(lane_widths)))
    tag = ""
    if pins or segment:
        import hashlib
        key = sorted((str(k), str(v)) for k, v in pins.items()) + [("segment", bfam)] + sorted((str(k), str(v)) for k, v in bpins.items())
        tag = "_" + hashlib.blake2b(repr(key).encode(), digest_size=6).hexdigest()
    name = name or f"fam_add_partitioned_w{W}_" + "_".join(str(lw) for lw in lane_widths) + f"_{mech}{tag}"
    from chialu.targets.rtl import families as FAM
    text = [f"// partitioned_carry_chain ({mech}, {bfam} segments of {fine} bits): one adder for the lane packings "
            f"{', '.join(f'{W // lw} x {lw}' for lw in lane_widths)}, the carry cut at the selected mode's lane boundaries",
            f"module {name} (input logic [{W-1}:0] a, input logic [{W-1}:0] b, input logic [{L-1}:0] cin, input logic [{S-1}:0] sel, "
            f"output logic [{W-1}:0] s, output logic [{L-1}:0] cout);"]
    # per segment boundary k (the start of finest lane k > 0): a boundary in mode m when k * fine % lw == 0
    text.append(f"  logic [{L}:0] c;")
    extra = ""
    for k in range(L):
        lo, hi = k * fine, (k + 1) * fine
        if k == 0:
            text.append("  assign c[0] = cin[0];")
        else:
            cond = " | ".join(f"(sel == {S}'d{mi})" for mi, lw in enumerate(lane_widths) if (lo % lw) == 0)
            cond = cond or "1'b0"
            text.append(f"  logic bnd{k}; assign bnd{k} = {cond};")
            if mech == "guard_bit_insertion":
                # a guard bit per boundary absorbs the crossing carry: the lower segment adds one extra bit
                # whose sum is discarded and whose carry does not enter the upper segment
                text.append(f"  assign c[{k}] = bnd{k} ? cin[{k}] : cg{k-1};")
            elif mech == "carry_select_mux":
                text.append(f"  assign c[{k}] = bnd{k} ? cin[{k}] : co{k-1};")
            else:
                # carry_kill_gate: the crossing carry killed at a boundary, the lane's carry-in inserted
                text.append(f"  assign c[{k}] = (co{k-1} & ~bnd{k}) | (cin[{k}] & bnd{k});")
        n = hi - lo
        m = FAM.adder_module(bfam, bpins, n + (1 if mech == "guard_bit_insertion" and k + 1 < L else 0))
        if mech == "guard_bit_insertion" and k + 1 < L:
            # the segment widened by the guard bit: the guard position adds a zero, its carry is the crossing carry
            text.append(f"  logic [{n}:0] sg{k}; logic cg{k}; logic cgu{k};")
            if m is None:
                text.append(f"  assign {{cgu{k}, sg{k}}} = {{1'b0, a[{hi-1}:{lo}]}} + {{1'b0, b[{hi-1}:{lo}]}} + c[{k}];")
            else:
                ps = ", ".join(f".{kk}({v})" for kk, v in m.params.items())
                text.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u{k} (.a({{1'b0, a[{hi-1}:{lo}]}}), .b({{1'b0, b[{hi-1}:{lo}]}}), .cin(c[{k}]), .s(sg{k}), .cout(cgu{k}));")
                if m.text:
                    extra += m.text
            text.append(f"  assign s[{hi-1}:{lo}] = sg{k}[{n-1}:0]; assign cg{k} = sg{k}[{n}]; assign co{k} = sg{k}[{n}];" if False else
                        f"  assign s[{hi-1}:{lo}] = sg{k}[{n-1}:0]; assign cg{k} = sg{k}[{n}];")
            text.append(f"  logic co{k}; assign co{k} = sg{k}[{n}];")
        else:
            text.append(f"  logic co{k};")
            if m is None:
                text.append(f"  assign {{co{k}, s[{hi-1}:{lo}]}} = a[{hi-1}:{lo}] + b[{hi-1}:{lo}] + c[{k}];")
            else:
                ps = ", ".join(f".{kk}({v})" for kk, v in m.params.items())
                text.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u{k} (.a(a[{hi-1}:{lo}]), .b(b[{hi-1}:{lo}]), .cin(c[{k}]), .s(s[{hi-1}:{lo}]), .cout(co{k}));")
                if m.text:
                    extra += m.text
        text.append(f"  assign cout[{k}] = co{k};")
    text.append(f"  assign c[{L}] = co{L-1};")
    text.append("endmodule")
    return name, "\n".join(text) + "\n" + dedupe_modules(extra)
