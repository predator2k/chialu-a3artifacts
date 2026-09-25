"""The core families whose datapath keeps a redundant or residue form
inside the op: `core.family: redundant_internal` with its
`representation` slot (redundant_spaces.signed_digit_space) and
`core.family: rns_internal` with its `channels` slot
(redundant_spaces.rns_space). The ALU converts at the op's entry and
exit, so every module keeps a lane interface the emitters already wire:

    adder       (input [W-1:0] a, input [W-1:0] b, input cin, output [W-1:0] s, output cout)
    multiplier  (input [W-1:0] a, input [W-1:0] b, output [2*W-1:0] p)
    comparator  (input [W-1:0] a, input [W-1:0] b, output lt, output eq)

Representation slot (the adder of a redundant_internal core):
* generalized_signed_digit: radix 2^k digits in [-alpha, alpha]
  (redundancy minimal alpha = r/2, intermediate, maximal alpha = r - 1;
  operands recoded by the Booth-like transfer t = [d >= r - alpha]),
  one-stage carry-free addition (needs 2 alpha >= r + 2) or the
  two-stage limited-carry rule whose transfer thresholds follow the
  sign set of the position below, digits stored in the pinned encoding
  between the stages (sign_magnitude, twos_complement, borrow_save,
  one_hot), the exit conversion by a carry-propagate adder of the
  `cpa` family over the positive and negative digit words or by the
  on-the-fly conversion (the Q / QM word pair, most significant digit
  first). The negation, overflow and zero-scan choices describe a
  datapath that keeps the redundant form across ops; here the
  complemented operand and carry-in of the lane stand for the negation
  (two_valued_transfer) and the flags come from the converted sum, as
  the module header says.
* hybrid_signed_digit: a signed digit every d-th position and binary
  runs between (Phatak-Koren): each run is a library adder of the
  interior_adder family that accepts a carry in {-1, 0, 1}, the signed
  position absorbs the run's carry and sends a transfer in {-1, 0, 1}
  to the next run, so no carry travels farther than one run; the exit
  conversion subtracts the negative digits' word.
* carry_save_datapath: the operands and the carry-in through one 3:2,
  4:2, 5:3 or 7:3 level (the unused inputs of the wider counters are
  the merged operands of a longer chain, zero here) and the
  assimilator of the `assimilator` family; carry_overflow_correction
  drops the carry word's bit above the modulus.
* redundant_binary_multiplier as a representation names the
  multiplier's redundant tree (families/mul_ext.py realizes it as the
  multiplier family; the lane's multiplier takes the representation's
  pins).

Channels slot (an rns_internal core): the moduli set follows the
channel family's pins (modulus_form pow2 or pow2_plus_1: {2^n - 1, 2^n,
2^n + 1} extended by 2^(n+1) - 1 and 2^(n-1) - 1; pow2_minus_1: 2^a - 1
with pairwise coprime a; generic: odd moduli near 2^n). An explicit n
stays fixed. The range M must exceed the largest value represented by
the operation: the raw sum, unsigned product, signed magnitude product
or comparison operand. Converter channel counts are never clipped.
* rns_forward_converter: chunk tables of 2^j mod m summed by modular
  adders (rom_per_chunk, segmented_rom_modular_add), the periodic
  folding of the word into n-bit slices with an end-around carry-save
  tree (periodic_csa_moma, the 2^n +- 1 channels), or the unrolled
  chunk Horner chain of modular multiply-adds (channel_modular_mac).
* rns_channel_arithmetic: the modular adder per channel (end-around
  carry for 2^n - 1, the low bits for 2^n, the diminished-one or normal
  adder for 2^n + 1, add and conditional subtract for a generic
  modulus) and the modular multiplier (a table for small channels, the
  rotated partial products of 2^n +- 1 with a carry-save tree, Booth
  rows with the modular correction of the negative rows, or the
  unrolled carry-save recurrence with a quotient digit estimated from
  the top remainder digits).
* rns_reverse_converter: the Chinese remainder theorem with constant
  multipliers as shift-add (adder_based) or per-channel tables (rom)
  and a final reduction below M, the mixed-radix chain, and Wang's New
  CRT-I / New CRT-II with their smaller final modulus.
* rns_scaling_comparison: the lane's comparator on residues by
  mixed-radix digits (rom_mrc), the CRT fraction estimate (exact width
  or an approximate width with an exact correction path), or Dimauro's
  diagonal function; equality is the residues' equality.
"""
from __future__ import annotations

import math
import random

from chialu.targets.rtl.families.mul import dedupe_modules

REDUNDANT_FAMILIES = {
    "representation": ("generalized_signed_digit", "hybrid_signed_digit", "carry_save_datapath", "redundant_binary_multiplier"),
    "channels": ("rns_channel_arithmetic", "rns_reverse_converter", "rns_forward_converter", "rns_scaling_comparison"),
}


def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _ipin(pins: dict, key: str, default: int) -> int:
    try:
        return int(_pin(pins, key, default))
    except (TypeError, ValueError):
        return default


def _bpin(pins: dict, key: str, default: bool) -> bool:
    v = _pin(pins, key, default)
    return v in (True, "true", "True", 1, "1")


def _sub(pins: dict, prefix: str) -> dict:
    from .selection import SelectedPins
    values = {k[len(prefix):]: v for k, v in (pins or {}).items()
              if k.startswith(prefix) and k != prefix + 'family'}
    if isinstance(pins, SelectedPins):
        return SelectedPins('.'.join(part for part in (pins.owner, prefix.rstrip('.')) if part), values)
    return values


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _lit(width: int, value: int) -> str:
    return f"{width}'d{value}"


class Mod:
    """A module text under construction: wires, assigns, raw lines,
    library adder instances (the generated dependencies collected in
    `extra`), rendered with an explicit port list."""

    def __init__(self, name: str, ports: str, comment: str, control_ports=None):
        self.name, self.ports, self.comment = name, ports, comment
        self.lines: list = []
        self.extra: list = []
        self.n = 0
        self.control_ports = {}
        self.control_sink = control_ports
        self.reduction_stats = []

    def controls(self, ports):
        for port, bits in ports:
            if port in self.control_ports and self.control_ports[port] != bits:
                raise ValueError(f"{self.name}: incompatible widths for control {port}")
            if port not in self.control_ports:
                self.ports += f", input logic [{bits-1}:0] {port}"
                self.control_ports[port] = bits
            if self.control_sink is not None:
                self.control_sink[port] = bits

    def wire(self, name: str, width: int = 1, expr: str | None = None, signed: bool = False) -> str:
        wd = f"[{width-1}:0] " if width > 1 else ""
        self.lines.append(f"  logic {'signed ' if signed else ''}{wd}{name};" + (f" assign {name} = {expr};" if expr is not None else ""))
        return name

    def assign(self, lhs: str, expr: str):
        self.lines.append(f"  assign {lhs} = {expr};")

    def raw(self, text: str):
        self.lines.append(text)

    def adder(self, fam, pins: dict, width: int, a: str, b: str, cin: str, s: str, cout: str, comment: str, module=None) -> bool:
        """s, cout = a + b + cin through the adder family's library module; the operator without one."""
        from .rns_cpa import raw_binary
        if raw_binary(self, fam, pins, width, a, b, cin, s, cout, comment, module=module):
            return True
        from chialu.targets.rtl import families as FAM
        m = module if module is not None else FAM.adder_module(fam, pins, width) if fam else None
        if m is None:
            if fam:
                raise ValueError(f"{self.name}: selected adder {fam!r} rejected width {width}")
            self.lines.append(f"  // {comment} (the operator)")
            self.assign(f"{{{cout}, {s}}}", f"{a} + {b} + {cin}")
            return False
        if m.text:
            self.extra.append(m.text)
        ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
        self.controls(m.ctrl)
        control = "".join(f", .{port}({port})" for port, _ in m.ctrl)
        self.n += 1
        self.lines.append(f"  // {comment}: {m.name}")
        self.lines.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u{self.n} (.a({a}), .b({b}), .cin({cin}), .s({s}), .cout({cout}){control});")
        return True

    def render(self) -> str:
        head = [f"// {self.comment}", f"module {self.name} ({self.ports});"]
        # Many residue channels use identical CPA definitions. Remove duplicate
        # text before concatenation so a large channel count does not create a
        # temporary string containing thousands of copies of the same module.
        return "\n".join(head + self.lines + ["endmodule", ""]) + dedupe_modules("".join(dict.fromkeys(self.extra)))


def _adder_ports(W: int) -> str:
    return f"input logic [{W-1}:0] a, input logic [{W-1}:0] b, input logic cin, output logic [{W-1}:0] s, output logic cout"


# =====================================================================================
# the representation slot: signed-digit adders
# =====================================================================================
def _alpha(r: int, redundancy: str) -> int:
    lo, hi = r // 2, r - 1
    if redundancy == "maximal":
        return hi
    if redundancy == "intermediate":
        return min(hi, lo + 1)          # radix 2 and 4 have no digit set between minimal and maximal
    return lo


def _sd_encoding(m: Mod, k: int, alpha: int, enc: str, tag: str) -> tuple:
    """The digit encoding functions `<tag>_enc` (signed value -> stored
    vector) and `<tag>_dec`; returns (stored width, value width)."""
    vw = k + 2                                                       # signed value in [-2 alpha - 1, 2 alpha + 1]
    if enc == "sign_magnitude":
        ew = k + 1
        m.raw(f'''  function automatic [{ew-1}:0] {tag}_enc(input signed [{vw-1}:0] d);
    {tag}_enc = {{d < 0, (d < 0) ? -d[{k-1}:0] : d[{k-1}:0]}};
  endfunction
  function automatic signed [{vw-1}:0] {tag}_dec(input [{ew-1}:0] e);
    {tag}_dec = e[{ew-1}] ? -$signed({{2'b0, e[{k-1}:0]}}) : $signed({{2'b0, e[{k-1}:0]}});
  endfunction''')
    elif enc == "borrow_save":
        ew = 2 * k
        m.raw(f'''  function automatic [{ew-1}:0] {tag}_enc(input signed [{vw-1}:0] d);
    {tag}_enc = (d < 0) ? {{{k}'d0, (-d[{k-1}:0])}} : {{d[{k-1}:0], {k}'d0}};
  endfunction
  function automatic signed [{vw-1}:0] {tag}_dec(input [{ew-1}:0] e);
    {tag}_dec = $signed({{2'b0, e[{ew-1}:{k}]}}) - $signed({{2'b0, e[{k-1}:0]}});
  endfunction''')
    elif enc == "one_hot":
        ew = 2 * alpha + 1
        m.raw(f'''  function automatic [{ew-1}:0] {tag}_enc(input signed [{vw-1}:0] d);
    {tag}_enc = {ew}'d1 << (d + {alpha});
  endfunction
  function automatic signed [{vw-1}:0] {tag}_dec(input [{ew-1}:0] e);
    integer i; {tag}_dec = 0;
    for (i = 0; i < {ew}; i = i + 1) if (e[i]) {tag}_dec = i - {alpha};
  endfunction''')
    else:                                                            # twos_complement
        ew = k + 1
        m.raw(f'''  function automatic [{ew-1}:0] {tag}_enc(input signed [{vw-1}:0] d);
    {tag}_enc = d[{ew-1}:0];
  endfunction
  function automatic signed [{vw-1}:0] {tag}_dec(input [{ew-1}:0] e);
    {tag}_dec = $signed({{e[{ew-1}], e}});
  endfunction''')
    return ew, vw


def sd_adder_sv(W: int, pins: dict, name: str) -> str:
    r = _ipin(pins, "radix", 2)
    if r not in (2, 4, 8, 16):
        r = 2
    k = r.bit_length() - 1
    redundancy = str(_pin(pins, "redundancy", "minimal"))
    alpha = _alpha(r, redundancy)
    enc = str(_pin(pins, "digit_encoding", "sign_magnitude"))
    scheme = str(_pin(pins, "addition_scheme", "carry_free"))
    carry_free = scheme == "carry_free" and 2 * alpha >= r + 2
    conv = str(_pin(pins, "final_conversion", "cpa"))
    cpa_fam = _pin(pins, "cpa.family", None)
    cpa_pins = _sub(pins, "cpa.")
    D = -(-W // k)
    m = Mod(name, _adder_ports(W),
            f"generalized_signed_digit: radix {r} digits in [-{alpha}, {alpha}] ({redundancy}), "
            f"{'one-stage carry-free' if carry_free else 'two-stage limited-carry'} addition"
            + (" (the minimal digit set cannot add carry-free; the two-stage rule applies)" if scheme == "carry_free" and not carry_free else "")
            + f", {enc} digits, {conv} conversion at the exit (the lane presents the complemented operand with a "
            f"carry-in and reads its flags off the converted sum)")
    ew, vw = _sd_encoding(m, k, alpha, enc, "sd")
    tw = k + 3                                                       # the position sum: [-2 alpha - 1, 2 alpha + 1]
    pad = D * k - W
    for src in ("a", "b"):
        m.wire(f"{src}x", D * k, f"{{{pad}'d0, {src}}}" if pad else src)
    # entry recoding into [-alpha, alpha]: t_{i+1} = [d_i >= r - alpha]; the top transfer is an extra digit
    beta = r - alpha
    for src in ("a", "b"):
        for i in range(D + 1):
            if i < D:
                d = f"{src}x[{i*k} +: {k}]"
                if alpha == r - 1:
                    t_out = "1'b0"
                else:
                    t_out = m.wire(f"{src}t{i+1}", 1, f"({d} >= {k}'d{beta})")
                t_in = "1'b0" if i == 0 or alpha == r - 1 else f"{src}t{i}"
                val = m.wire(f"{src}v{i}", vw, f"$signed({{2'b0, {d}}}) - ({t_out} ? {vw}'sd{r} : {vw}'sd0) + $signed({{{vw-1}'d0, {t_in}}})", signed=True)
            else:
                t_in = "1'b0" if alpha == r - 1 else f"{src}t{D}"
                val = m.wire(f"{src}v{D}", vw, f"$signed({{{vw-1}'d0, {t_in}}})", signed=True)
            m.wire(f"{src}e{i}", ew, f"sd_enc({val})")            # the stored digit
    # the addition over D + 1 digit positions (the recoding's top transfer digit included)
    N = D + 1
    for i in range(N):
        xa = m.wire(f"xa{i}", vw, f"sd_dec(ae{i})", signed=True)
        xb = m.wire(f"xb{i}", vw, f"sd_dec(be{i})", signed=True)
        p = m.wire(f"p{i}", tw, f"{xa} + {xb}" + (" + $signed({{{0}'d0, cin}})".format(tw - 1) if i == 0 else ""), signed=True)
        if carry_free:
            hi, lo = alpha, -alpha
        else:
            # the incoming transfer's sign set follows the digits below: both non-negative -> {0, 1}
            low_neg = m.wire(f"ln{i}", 1, f"(xa{i-1} < 0) | (xb{i-1} < 0)" if i > 0 else f"(xa0 < 0) | (xb0 < 0)")
            hi, lo = None, None
        if carry_free:
            t = m.wire(f"t{i+1}", vw, f"({p} >= {tw}'sd{hi}) ? {vw}'sd1 : ({p} <= -{tw}'sd{-lo}) ? -{vw}'sd1 : {vw}'sd0", signed=True)
        else:
            t = m.wire(f"t{i+1}", vw,
                       f"{low_neg} ? (({p} >= {tw}'sd{alpha+1}) ? {vw}'sd1 : ({p} <= -{tw}'sd{alpha}) ? -{vw}'sd1 : {vw}'sd0)"
                       f" : (({p} >= {tw}'sd{alpha}) ? {vw}'sd1 : ({p} <= -{tw}'sd{alpha+1}) ? -{vw}'sd1 : {vw}'sd0)", signed=True)
        w = m.wire(f"w{i}", tw, f"{p} - ({t} * {tw}'sd{r})", signed=True)
        m.wire(f"we{i}", ew, f"sd_enc({w}[{vw-1}:0])")
    for i in range(N + 1):
        w_in = f"sd_dec(we{i})" if i < N else f"{vw}'sd0"
        t_in = f"t{i}" if i > 0 else f"{vw}'sd0"
        m.wire(f"sv{i}", vw, f"{w_in} + {t_in}", signed=True)
        m.wire(f"se{i}", ew, f"sd_enc(sv{i})")
    # the exit conversion: the (N + 1)-digit signed-digit sum is the binary sum a + b + cin (< 2^(W+1))
    TW = (N + 1) * k + 1
    if conv == "on_the_fly":
        m.raw("  // on-the-fly conversion: Q and QM from the most significant digit down (Ercegovac-Lang)")
        prevq, prevqm = None, None
        for j in range(N, -1, -1):
            d = m.wire(f"od{j}", vw, f"sd_dec(se{j})", signed=True)
            dm = m.wire(f"dm{j}", k, f"{d}[{k-1}:0]")                               # d (>= 0) as a digit
            dn = m.wire(f"dn{j}", k, f"({vw}'sd{r} + {d})")                         # r + d (d < 0)
            dm1 = m.wire(f"dm1_{j}", k, f"({d} - {vw}'sd1)")                         # d - 1 (d > 0)
            dn1 = m.wire(f"dn1_{j}", k, f"({vw}'sd{r - 1} + {d})")                   # r + d - 1 (d <= 0)
            width = (N + 1 - j) * k
            if prevq is None:
                q = m.wire(f"q{j}", width, f"({d} >= 0) ? {dm} : {dn}")
                qm = m.wire(f"qm{j}", width, f"({d} > 0) ? {dm1} : {dn1}")
            else:
                q = m.wire(f"q{j}", width, f"({d} >= 0) ? {{{prevq}, {dm}}} : {{{prevqm}, {dn}}}")
                qm = m.wire(f"qm{j}", width, f"({d} > 0) ? {{{prevq}, {dm1}}} : {{{prevqm}, {dn1}}}")
            prevq, prevqm = q, qm
        m.wire("tot", TW, f"{{1'b0, {prevq}}}")
    else:
        for i in range(N + 1):
            m.wire(f"ns{i}", vw, f"-sv{i}", signed=True)
        pos = " | ".join(f"((sv{i} > 0) ? ({{{TW-k}'d0, sv{i}[{k-1}:0]}} << {i*k}) : {TW}'d0)" for i in range(N + 1))
        neg = " | ".join(f"((sv{i} < 0) ? ({{{TW-k}'d0, ns{i}[{k-1}:0]}} << {i*k}) : {TW}'d0)" for i in range(N + 1))
        m.wire("posw", TW, pos)
        m.wire("negw", TW, neg)
        m.wire("tot", TW)
        m.wire("totc", 1)
        m.adder(cpa_fam, cpa_pins, TW, "posw", "~negw", "1'b1", "tot", "totc",
                "the exit conversion P - N through the cpa family")
    m.assign("s", f"tot[{W-1}:0]")
    m.assign("cout", f"tot[{W}]")
    return m.render()


def hybrid_sd_adder_sv(W: int, pins: dict, name: str) -> str:
    d = max(1, min(8, _ipin(pins, "sd_position_spacing", 4)))
    uniform = _bpin(pins, "spacing_uniform", True)
    interior = str(_pin(pins, "interior_adder", "ripple"))
    run_fam = _pin(pins, "binary_run_adder.family", None) or {"ripple": "ripple_carry", "carry_select": "carry_select",
                                                              "prefix": "parallel_prefix"}.get(interior, "ripple_carry")
    run_pins = _sub(pins, "binary_run_adder.") or ({"topology": "kogge_stone"} if run_fam == "parallel_prefix" else {})
    cpa_fam = _pin(pins, "cpa.family", None)
    cpa_pins = _sub(pins, "cpa.")
    # the runs: [lo, hi] with the signed digit at hi; spacing d (uniform) or d, d+1, ... (nonuniform)
    runs, lo, sp = [], 0, d
    while lo < W:
        hi = min(W - 1, lo + sp - 1)
        runs.append((lo, hi))
        lo = hi + 1
        if not uniform:
            sp = min(8, sp + 1)
    m = Mod(name, _adder_ports(W),
            f"hybrid_signed_digit: a signed digit every {'%d-th' % d if uniform else 'd-th (d = %d, then growing)' % d} position, "
            f"binary runs between on the {run_fam} adder accepting a carry in {{-1, 0, 1}}; the exit conversion subtracts the negative digits' word")
    TW = W + 1
    m.wire("sb", W)                                                   # the runs' binary sum bits
    carry_p, carry_n = "cin", "1'b0"                                  # the carry into the run: +1 / -1 flags
    for ri, (lo, hi) in enumerate(runs):
        L = hi - lo                                                   # binary positions lo..hi-1, the signed digit at hi
        if L > 0:
            ra, rb = f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]"
            s0, c0 = m.wire(f"r{ri}s0", L), m.wire(f"r{ri}c0", 1)
            s1, c1 = m.wire(f"r{ri}s1", L), m.wire(f"r{ri}c1", 1)
            m.adder(run_fam, run_pins, L, ra, rb, "1'b0", s0, c0, f"run {ri} with carry-in 0")
            m.adder(run_fam, run_pins, L, ra, rb, "1'b1", s1, c1, f"run {ri} with carry-in 1")
            # a carry of -1: the run's sum without carry minus one (a borrow out when that sum is zero)
            sm = m.wire(f"r{ri}sm", L, f"{s0} - {L}'d1")
            bm = m.wire(f"r{ri}bm", 1, f"({s0} == {L}'d0)")
            m.assign(f"sb[{hi-1}:{lo}]", f"{carry_p} ? {s1} : {carry_n} ? {sm} : {s0}")
            cp = m.wire(f"r{ri}cp", 1, f"{carry_p} ? {c1} : {carry_n} ? 1'b0 : {c0}")
            cn = m.wire(f"r{ri}cn", 1, f"{carry_n} & {bm}")
        else:
            cp, cn = carry_p, carry_n
        m.assign(f"sb[{hi}]", "1'b0")
        # the signed position: v = a + b + c in [-1, 3] -> a digit in {-1, 0, 1} and a transfer in {-1, 0, 1}
        v = m.wire(f"v{ri}", 4, f"$signed({{3'b0, a[{hi}]}}) + $signed({{3'b0, b[{hi}]}}) + $signed({{3'b0, {cp}}}) - $signed({{3'b0, {cn}}})", signed=True)
        m.wire(f"dp{ri}", 1, f"({v} == 4'sd1) | ({v} == 4'sd3)")
        m.wire(f"dn{ri}", 1, f"({v} == -4'sd1)")
        tp = m.wire(f"tp{ri}", 1, f"({v} >= 4'sd2)")
        tn = m.wire(f"tn{ri}", 1, f"({v} <= -4'sd1)")
        carry_p, carry_n = tp, tn
    # the exit conversion: value = the binary sum bits + the positive digits - the negative digits + the top transfer
    posw = " | ".join([f"({{1'b0, sb}})"] + [f"({{{TW-1}'d0, dp{ri}}} << {hi})" for ri, (lo, hi) in enumerate(runs)]
                      + [f"({{{TW-1}'d0, {carry_p}}} << {W})"])
    negw = " | ".join([f"({{{TW-1}'d0, dn{ri}}} << {hi})" for ri, (lo, hi) in enumerate(runs)] + [f"({{{TW-1}'d0, {carry_n}}} << {W})"])
    m.wire("posw", TW, posw)
    m.wire("negw", TW, negw)
    m.wire("tot", TW)
    m.wire("totc", 1)
    m.adder(cpa_fam, cpa_pins, TW, "posw", "~negw", "1'b1", "tot", "totc", "the exit conversion P - N through the cpa family")
    m.assign("s", f"tot[{W-1}:0]")
    m.assign("cout", f"tot[{W}]")
    return m.render()


def carry_save_adder_sv(W: int, pins: dict, name: str, assimilator=None) -> str:
    comp = str(_pin(pins, "compressor", "3_2"))
    corr = _bpin(pins, "carry_overflow_correction", False)
    fam = _pin(pins, "assimilator.family", "ripple_carry")
    fpins = _sub(pins, "assimilator.")
    m = Mod(name, _adder_ports(W),
            f"carry_save_datapath: the operands and the carry-in through one {comp.replace('_', ':')} level, assimilated "
            f"by the assimilator family (the lane's op leaves a binary result)"
            + ("; the carry word's bit above the modulus is dropped (carry_overflow_correction)" if corr else ""))
    TW = W + 1
    if assimilator is None:
        from chialu.targets.rtl import families as FAM
        assimilator = FAM.adder_module(fam, fpins, TW)
    if assimilator is None:
        raise ValueError(f"carry_save_datapath: assimilator {fam!r} rejected its pins at width {TW}")
    m.controls(assimilator.ctrl)
    m.wire("x0", TW, f"{{1'b0, a}}")
    m.wire("x1", TW, f"{{1'b0, b}}")
    m.wire("x2", TW, f"{{{W}'d0, cin}}")
    if comp == "3_2":
        m.wire("sm", TW, "x0 ^ x1 ^ x2")
        m.wire("cy", TW, "((x0 & x1) | (x0 & x2) | (x1 & x2)) << 1")
    elif comp == "4_2":
        m.wire("x3", TW, "'0")
        m.wire("s1", TW, "x0 ^ x1 ^ x2")
        m.wire("c1", TW, "((x0 & x1) | (x0 & x2) | (x1 & x2)) << 1")
        m.wire("sm", TW, "s1 ^ c1 ^ x3")
        m.wire("cy", TW, "((s1 & c1) | (s1 & x3) | (c1 & x3)) << 1")
    else:
        # 5:3 and 7:3 counters per column: the column count (the extra inputs zero) split into sum, carry and carry2
        m.wire("x3", TW, "'0")
        m.wire("x4", TW, "'0")
        cnt = "x0[i] + x1[i] + x2[i] + x3[i] + x4[i]" if comp == "5_3" else "x0[i] + x1[i] + x2[i] + x3[i] + x4[i] + 1'b0 + 1'b0"
        m.wire("sm", TW)
        m.wire("c1w", TW)
        m.wire("c2w", TW)
        m.raw(f"  always_comb begin sm = '0; c1w = '0; c2w = '0; for (int i = 0; i < {TW}; i = i + 1) begin "
              f"logic [2:0] c; c = {cnt}; sm[i] = c[0]; c1w[i] = c[1]; c2w[i] = c[2]; end end")
        m.wire("cy", TW, "(c1w << 1) + (c2w << 2)")
    if corr:
        m.wire("cyc", TW, f"{{1'b0, cy[{W-1}:0]}}")
        m.wire("tot", TW)
        m.wire("totc", 1)
        m.adder(fam, fpins, TW, "sm", "cyc", "1'b0", "tot", "totc", "the assimilator", module=assimilator)
        m.assign("s", f"tot[{W-1}:0]")
        m.assign("cout", f"tot[{W}] | cy[{W}]")
    else:
        m.wire("tot", TW)
        m.wire("totc", 1)
        m.adder(fam, fpins, TW, "sm", "cy", "1'b0", "tot", "totc", "the assimilator", module=assimilator)
        m.assign("s", f"tot[{W-1}:0]")
        m.assign("cout", f"tot[{W}]")
    return m.render()


def _ptag(pins: dict) -> str:
    """A 48-bit tag of the pins for a module name (empty without pins)."""
    if not pins:
        return ""
    import hashlib
    return "_" + hashlib.blake2b(repr(sorted((str(k), str(v)) for k, v in pins.items())).encode(), digest_size=6).hexdigest()


def representation_adder_sv(W: int, family: str, pins: dict, name: str | None = None, assimilator=None) -> tuple:
    """(name, text) of the adder of a redundant_internal core under its
    representation family; ValueError for a family without a module."""
    pins = pins or {}
    tag = _ptag(pins)
    if family == "generalized_signed_digit":
        name = name or (f"fam_sd_adder_r{_ipin(pins, 'radix', 2)}_{str(_pin(pins, 'redundancy', 'minimal'))[:3]}_"
                        f"{str(_pin(pins, 'digit_encoding', 'sign_magnitude'))[:4]}_{'otf' if _pin(pins, 'final_conversion', 'cpa') == 'on_the_fly' else 'cpa'}_"
                        f"{'cf' if _pin(pins, 'addition_scheme', 'carry_free') == 'carry_free' else 'ts'}_w{W}{tag}")
        return name, sd_adder_sv(W, pins, name)
    if family == "hybrid_signed_digit":
        name = name or f"fam_hsd_adder_d{_ipin(pins, 'sd_position_spacing', 4)}_{'u' if _bpin(pins, 'spacing_uniform', True) else 'n'}_{str(_pin(pins, 'interior_adder', 'ripple'))[:4]}_w{W}{tag}"
        return name, hybrid_sd_adder_sv(W, pins, name)
    if family == "carry_save_datapath":
        name = name or f"fam_csd_adder_{str(_pin(pins, 'compressor', '3_2'))}{'c' if _bpin(pins, 'carry_overflow_correction', False) else ''}_w{W}{tag}"
        return name, carry_save_adder_sv(W, pins, name, assimilator=assimilator)
    if family == "redundant_binary_multiplier":
        raise ValueError("redundant_binary_multiplier names the multiplier's representation; the adder keeps its own family")
    raise ValueError(f"no module for the representation family {family}")


# =====================================================================================
# the channels slot: residue number system cores
# =====================================================================================
def _coprime(ms: list) -> bool:
    return all(math.gcd(a, b) == 1 for i, a in enumerate(ms) for b in ms[i + 1:])


def moduli_set(form: str, count: int, need_bits: int, n_pin: int = 0, *, maximum=None, n_min=3, n_max=None) -> tuple:
    """(moduli, n) whose product exceeds the largest represented value.
    The classic
    {2^n - 1, 2^n, 2^n + 1} extended by 2^(n+1) - 1 and 2^(n-1) - 1
    (even n) for pow2 / pow2_plus_1, Mersenne-like 2^a - 1 with
    pairwise coprime a for pow2_minus_1, odd moduli below 2^n for
    generic. An explicit n stays fixed; otherwise choose the first n
    that supplies the requested count and capacity. Beyond the classic
    five channels, append the smallest odd moduli coprime to the set."""
    if form not in ("pow2", "pow2_plus_1", "pow2_minus_1", "generic"):
        raise ValueError(f"unknown RNS modulus_form {form!r}")
    if not 3 <= count <= 64:
        raise ValueError(f"RNS moduli_count {count} is outside 3..64")
    if n_pin and not 3 <= n_pin <= 32:
        raise ValueError(f"RNS base exponent {n_pin} is outside 3..32")
    maximum = (1 << need_bits) - 1 if maximum is None else maximum
    n = n_pin or n_min
    while True:
        if n_max is not None and n > n_max:
            raise ValueError(f"RNS capacity cannot represent {maximum} ({need_bits} bits) with "
                             f"channel_width_n in {n_min}..{n_max}; no legal default geometry")
        if form == "pow2_minus_1":
            exps, e = [], n
            while len(exps) < count:
                if all(math.gcd(e, x) == 1 for x in exps):
                    exps.append(e)
                e += 1
            ms = [(1 << e) - 1 for e in exps]
        elif form == "generic":
            ms, c = [], (1 << n) - 1
            while len(ms) < count and c > 2:
                if c % 2 and all(math.gcd(c, x) == 1 for x in ms):
                    ms.append(c)
                c -= 2
        else:
            ms = [(1 << n) - 1, 1 << n, (1 << n) + 1]
            if count >= 4:
                ms.append((1 << (n + 1)) - 1)
            if count >= 5:
                ms.append((1 << (n - 1)) - 1)
            c = 3
            while len(ms) < count:
                if all(math.gcd(c, x) == 1 for x in ms):
                    ms.append(c)
                c += 2
        M = math.prod(ms)
        if len(ms) == count and _coprime(ms) and M > maximum:
            return tuple(ms), n
        if n_pin:
            if len(ms) != count or not _coprime(ms):
                raise ValueError(f"RNS channel_width_n={n_pin} cannot construct {count} pairwise-coprime {form} moduli")
            raise ValueError(f"RNS channel_width_n={n_pin} has capacity M={M}, but the operation can produce "
                             f"{maximum} ({need_bits} bits); require M > maximum, without increasing n")
        n += 1


def _mform(m: int) -> str:
    n = m.bit_length()
    if m == (1 << (n - 1)):
        return "pow2"
    if m == (1 << n) - 1:
        return "pow2_minus_1"
    if m == (1 << (n - 1)) + 1:
        return "pow2_plus_1"
    return "generic"


def _mn(m: int) -> int:
    """The n of a 2^n +- 1 or 2^n modulus."""
    f = _mform(m)
    return m.bit_length() if f == "pow2_minus_1" else m.bit_length() - 1


def _csd(c: int) -> list:
    """(shift, sign) terms of the canonical signed-digit form of c."""
    out, i = [], 0
    while c:
        if c & 1:
            d = 2 - (c & 3)                 # +1 or -1
            out.append((i, d))
            c -= d
        c >>= 1
        i += 1
    return out


def _rom(m: Mod, name: str, values: list, bits: int, idx: str, out: str):
    """out = values[idx] from a packed constant table (named after its
    output wire, which is unique in the module)."""
    name = f"T_{out}"
    E = len(values)
    words = "".join(f"{v:0{bits}b}" for v in reversed(values))
    # Keep every literal token bounded even when many moduli make a CRT
    # residue hundreds of bits wide. Concatenation preserves one complete
    # table; it changes neither its address nor its output width.
    literals = [f"{len(word)}'h{int(word, 2):x}"
                for offset in range(0, len(words), 4096) for word in [words[offset:offset+4096]]]
    literal = literals[0] if len(literals) == 1 else "{\n    " + ",\n    ".join(literals) + "}"
    m.raw(f"  localparam [{E*bits-1}:0] {name} = {literal};")
    m.wire(out, bits, f"{name}[({idx}) * {bits} +: {bits}]")
    return out


def _const_mul(m: Mod, x: str, xw: int, c: int, out: str, ow: int, style: str, tag: str, cfg: dict | None = None) -> str:
    """out (ow bits) = x * c: a short-input table under `rom`, otherwise
    shift-add logic through the channel's CPA. The arithmetic path uses
    the shorter expansion of the constant's CSD digits or operand bits."""
    if style == "rom" and xw <= 8:
        return _rom(m, f"T{tag}", [(v * c) & ((1 << ow) - 1) for v in range(1 << xw)], ow, x, out)
    terms = _csd(c)
    if style == "csd" and xw < len(terms):
        # A many-channel CRT has large, dense constants but narrow residue
        # operands. Expanding the operand bits needs fewer selected CPAs than
        # expanding the constant's CSD digits, while retaining shift-add logic.
        mask = (1 << ow) - 1
        rows = [m.wire(f"{out}_bit{i}", ow, f"{x}[{i}] ? {ow}'d{(c << i) & mask} : {ow}'d0")
                for i in range(xw)]
        return _sum_terms(m, rows, ow, out, cfg, f"the constant multiply by {c}: weighted operand bits")
    pos = [f"({{{{{ow-xw}{{1'b0}}}}, {x}}} << {sh})" for sh, d in terms if d > 0]
    neg = [f"({{{{{ow-xw}{{1'b0}}}}, {x}}} << {sh})" for sh, d in terms if d < 0]
    if not pos:
        p_ = m.wire(f"{out}_z", ow, f"{ow}'d0")
    else:
        p_ = _sum_terms(m, pos, ow, f"{out}_p", cfg, f"the constant multiply by {c}: its positive terms")
    if not neg:
        return m.wire(out, ow, p_)
    n_ = _sum_terms(m, neg, ow, f"{out}_n", cfg, f"the constant multiply by {c}: its negative terms") if len(neg) > 1 else neg[0]
    # the negative terms taken off through the channel's adder (its complement and carry-in)
    from chialu.targets.rtl.families.selection import copy_pins
    fam, fpins = cfg.get("adder_family") if cfg else None, copy_pins((cfg or {}).get("adder_pins"))
    if not fam:
        return m.wire(out, ow, f"{p_} - {n_}")
    nb = m.wire(f"{out}_nb", ow, f"~{n_}")
    t = m.wire(f"{out}_t", ow)
    co = m.wire(f"{out}_co", 1)
    m.adder(fam, fpins, ow, p_, nb, "1'b1", t, co, f"the constant multiply by {c}: its negative terms taken off ({fam})")
    return m.wire(out, ow, t)


def _ladder(m: Mod, s: str, sw: int, mod: int, kmax: int, out: str, ow: int) -> str:
    """out = s mod `mod` for s < kmax * mod: the conditional subtractions."""
    expr = f"{s}[{ow-1}:0]" if sw > ow else s
    if kmax > 1:
        chain = []
        for j in range(kmax - 1, 0, -1):
            chain.append(f"({s} >= {sw}'d{j*mod}) ? {s} - {sw}'d{j*mod}")
        expr = " : ".join(chain) + f" : {s}"
        t = m.wire(f"{out}_l", sw, expr)
        expr = f"{t}[{ow-1}:0]" if sw > ow else t
    return m.wire(out, ow, expr)


def _binary_mod_reduce(m: Mod, x: str, xw: int, modulus: int, out: str, cfg: dict, *, maximum=None) -> str:
    """Unsigned remainder through aligned constant subtractions by the CPA.

    This is the arithmetic CRT boundary: at most xw-modulus.bit_length()+1
    stages, with each subtraction's carry selecting its nonnegative result.
    It does not change any ROM-selected forward or reverse implementation.
    """
    width = (modulus - 1).bit_length()
    current = x
    maximum = (1 << xw) - 1 if maximum is None else maximum
    for shift in range((maximum // modulus).bit_length() - 1, -1, -1):
        value = modulus << shift
        difference = m.wire(f"{out}_d{shift}", xw)
        carry = m.wire(f"{out}_c{shift}", 1)
        m.adder(cfg["adder_family"], cfg["adder_pins"], xw, current,
                f"{xw}'d{((1 << xw) - 1) ^ value}", "1'b1", difference, carry,
                f"arithmetic CRT reduction mod {modulus}, shifted subtraction {shift}")
        current = m.wire(f"{out}_r{shift}", xw, f"{carry} ? {difference} : {current}")
    return m.wire(out, width, f"{current}[{width-1}:0]" if xw > width else current)


def _sum_terms(m: Mod, terms: list, sw: int, out: str, cfg: dict | None, comment: str) -> str:
    """The sum of the terms through the `column_reducer` slot's adder tree
    (the forward converter's periodic carry-save folding): a chain or a
    binary tree of the tree's CPA family, or a carry-save reduction of the
    terms with one CPA at the root; one expression when no family is
    declared."""
    cfg = cfg or {}
    fam = str(cfg.get("col_family") or "")
    from .selection import copy_pins
    cpins = copy_pins(cfg.get("col_pins"))
    slot = "final_cpa." if fam == "csa_tree" else "cpa."
    cfam = cpins.get(slot + "family", "ripple_carry" if fam in ("csa_tree", "binary_tree") else None)
    apins = _sub(cpins, slot)
    if not fam:
        # no column reducer declared: a chain of the channel's modular_adder family (its library module when the
        # slot names one, the operator otherwise)
        from chialu.targets.rtl.families.selection import copy_pins
        fam, cfam, apins = "linear_chain", cfg.get("adder_family"), copy_pins(cfg.get("adder_pins"))
    if len(terms) < 2:
        return m.wire(out, sw, terms[0] if terms else f"{sw}'d0")
    k = 0

    def add(x, y, name, note):
        nonlocal k
        t = m.wire(name, sw)
        c = m.wire(f"{name}_c", 1)
        m.adder(cfam, apins, sw, x, y, "1'b0", t, c, f"{comment}: {note} ({fam}" + (f", {cfam}" if cfam else "") + ")")
        k += 1
        return t

    cur = list(terms)
    if fam == "csa_tree":
        from .redundant_reduce import csa_rows
        left, right = csa_rows(m, cur, sw, out, str(cpins.get("compressor", "3:2")))
        return m.wire(out, sw, add(left, right, f"{out}_r", "the root adder"))
    if fam == "binary_tree":
        while len(cur) > 1:
            nxt = [add(cur[i], cur[i + 1], f"{out}_t{k}", f"tree adder {k}") for i in range(0, len(cur) - 1, 2)]
            if len(cur) % 2:
                nxt.append(cur[-1])
            cur = nxt
        return m.wire(out, sw, cur[0])
    acc = cur[0]
    for i in range(1, len(cur)):
        acc = add(acc, cur[i], f"{out}_a{k}", f"chain adder {k}")
    return m.wire(out, sw, acc)


def _eac(m: Mod, low: str, carry: str, n: int, out: str, cfg: dict | None, comment: str) -> str:
    """out (n + 1 bits) = low + carry: the end-around carry added back
    through the channel's adder family (its carry-in), the operator
    without one."""
    cfg = cfg or {}
    from chialu.targets.rtl.families.selection import copy_pins
    fam, fpins = cfg.get("adder_family"), copy_pins(cfg.get("adder_pins"))
    if not fam:
        return m.wire(out, n + 1, f"{{1'b0, {low}}} + {{{{{n}{{1'b0}}}}, {carry}}}")
    t = m.wire(f"{out}_t", n)
    c = m.wire(f"{out}_c", 1)
    m.adder(fam, fpins, n, low, f"{n}'d0", carry, t, c, comment)
    return m.wire(out, n + 1, f"{{{c}, {t}}}")


def _mod_reduce(m: Mod, x: str, xw: int, mod: int, out: str, style: str, tag: str, cfg: dict | None = None) -> str:
    """out = x mod `mod` for an x of xw bits: the periodic folding of a
    2^n +- 1 modulus, the low bits of 2^n, else chunk tables (the
    forward converter's `column_reducer` slot sums the folded slices
    when cfg names its family)."""
    f = _mform(mod)
    ow = (mod - 1).bit_length() if mod > 1 else 1
    n = _mn(mod)
    if f == "pow2":
        return m.wire(out, ow, f"{x}[{ow-1}:0]" if xw > ow else x)
    if f == "pow2_minus_1" and xw > n:
        # fold n-bit slices (each 2^(ni) = 1 mod m) until the sum fits n + 1 bits, then the end-around carry
        cur, cw, level = x, xw, 0
        while cw > n + 1:
            if cw >= 2 * n and n >= 3:
                # all n-bit slices at once (the sum's width shrinks below the word's)
                k = -(-cw // n)
                sw = n + (k - 1).bit_length() + 1
                terms = [f"{{{{{sw-(min(cw,(i+1)*n)-i*n)}{{1'b0}}}}, {cur}[{min(cw,(i+1)*n)-1}:{i*n}]}}" for i in range(k)]
            else:
                # the low n bits plus the rest: one bit shorter at least
                sw = max(n, cw - n) + 1
                terms = [f"{{{{{sw-n}{{1'b0}}}}, {cur}[{n-1}:0]}}", f"{{{{{sw-(cw-n)}{{1'b0}}}}, {cur}[{cw-1}:{n}]}}"]
            cur = _sum_terms(m, terms, sw, f"{out}_f{level}", cfg, f"the periodic folding mod {mod}")
            cw, level = sw, level + 1
        v = m.wire(f"{out}_v", n + 1, f"{{{{{n+1-cw}{{1'b0}}}}, {cur}}}" if cw < n + 1 else cur)
        # the end-around carry twice: all ones plus a carry reaches 2^n once more
        e = _eac(m, f"{v}[{n-1}:0]", f"{v}[{n}]", n, f"{out}_e", cfg, f"the end-around carry mod 2^{n} - 1")
        e2 = _eac(m, f"{e}[{n-1}:0]", f"{e}[{n}]", n, f"{out}_e2", cfg, f"the second end-around carry mod 2^{n} - 1")
        return m.wire(out, ow, f"({e2} == {{{n}{{1'b1}}}}) ? {n}'d0 : {e2}")
    if f == "pow2_plus_1" and xw > n:
        # 2^n = -1: the even slices add, the odd ones subtract; k*(2^n + 1) keeps the sum positive
        k = -(-xw // n)
        sw = n + 2 + (k + 1).bit_length()
        pos = " + ".join(f"{{{{{sw-(min(xw,(i+1)*n)-i*n)}{{1'b0}}}}, {x}[{min(xw,(i+1)*n)-1}:{i*n}]}}" for i in range(0, k, 2))
        neg = " - ".join(f"{{{{{sw-(min(xw,(i+1)*n)-i*n)}{{1'b0}}}}, {x}[{min(xw,(i+1)*n)-1}:{i*n}]}}" for i in range(1, k, 2))
        kodd = len(range(1, k, 2))
        expr = f"({pos}) + {sw}'d{kodd * mod}" + (f" - {neg}" if neg else "")
        s = m.wire(f"{out}_s", sw, expr)
        return _ladder(m, s, sw, mod, kodd + 2 + (k + 1) // 2, out, ow)
    if xw <= ow:
        return m.wire(out, ow, f"{{{{{ow-xw}{{1'b0}}}}, {x}}}" if xw < ow else x)
    # generic (or a short 2^n +- 1 word): chunk tables of (chunk * 2^(8i)) mod m summed, one ladder
    j = 8
    k = -(-xw // j)
    sw = ow + (k - 1).bit_length() + 1
    terms = []
    for i in range(k):
        lo, hi = i * j, min(xw, (i + 1) * j)
        cb = hi - lo
        vals = [((v << lo) % mod) for v in range(1 << cb)]
        t = _rom(m, f"T{tag}_{i}", vals, ow, f"{x}[{hi-1}:{lo}]", f"{out}_c{i}")
        terms.append(f"{{{{{sw-ow}{{1'b0}}}}, {t}}}")
    s = _sum_terms(m, terms, sw, f"{out}_s", cfg, f"the chunk tables mod {mod}")
    return _ladder(m, s, sw, mod, k, out, ow)


def _mod_add(m: Mod, a: str, b: str, cin: str, mod: int, out: str, cfg: dict, tag: str) -> str:
    """Normalize the selected binary child's actual sum to a residue."""
    from .rns_mod_add import mod_add
    return mod_add(m, a, b, cin, mod, out, cfg, tag)


def _mod_mul(m: Mod, a: str, b: str, mod: int, out: str, cfg: dict, tag: str) -> str:
    """out = a * b mod `mod` on canonical residues by the channel's
    multiplier_reduction."""
    f = _mform(mod)
    ow = (mod - 1).bit_length()
    red = cfg.get("mul_red", "csa_with_periodic_folding")
    if red not in ("rom", "csa_with_periodic_folding", "booth_modular", "iterative_carry_save_msd_estimate"):
        raise ValueError(f"RNS multiplier_reduction {red!r} is not implemented")
    if red == "rom":
        # Keep the ROM architecture when a full two-residue address is too
        # large: distributivity gives a sum of weighted digit products. Each
        # product is still a physical constant-table lookup, and the selected
        # channel CPA combines canonical table residues with modular additions.
        # Four-bit digits cap a bank at 256 entries; short channels retain the
        # single, full-address table. No multiplier or CSA replaces a bank.
        chunk = ow if 2 * ow <= 10 else 4
        rows = []
        for ai in range(0, ow, chunk):
            aw = min(chunk, ow - ai)
            for bi in range(0, ow, chunk):
                bw = min(chunk, ow - bi)
                shift = ai + bi
                weight = pow(2, shift, mod)
                if not weight:
                    # For a power-of-two modulus these product digits are
                    # identically zero, regardless of either operand.
                    continue
                lname = f"fam_rns_product_rom_m{mod}_a{aw}_b{bw}_s{shift}"
                lut = Mod(lname, f"input logic [{aw-1}:0] a, input logic [{bw-1}:0] b, output logic [{ow-1}:0] y",
                          f"ROM bank: (a * b * 2^{shift}) mod {mod}")
                lut.raw(f"  localparam integer A_BITS = {aw}, B_BITS = {bw}, OUT_BITS = {ow}, SHIFT = {shift};")
                lut.raw(f"  localparam [{ow}:0] MODULUS = {ow+1}'d{mod};")
                values = [(x * y * weight) % mod for y in range(1 << bw) for x in range(1 << aw)]
                _rom(lut, "", values, ow, "{b, a}", "value")
                lut.assign("y", "value")
                m.extra.append(lut.render())
                row = m.wire(f"{out}_rom_a{ai}_b{bi}", ow)
                m.raw(f"  {lname} u_{row} (.a({a}[{ai+aw-1}:{ai}]), .b({b}[{bi+bw-1}:{bi}]), .y({row}));")
                rows.append(row)
        level = 0
        while len(rows) > 1:
            following = []
            for i in range(0, len(rows) - 1, 2):
                following.append(_mod_add(m, rows[i], rows[i + 1], "1'b0", mod,
                                          f"{out}_rom_sum{level}_{i//2}", cfg,
                                          f"{tag} ROM bank tree level {level}, pair {i//2}"))
            if len(rows) % 2:
                following.append(rows[-1])
            rows = following
            level += 1
        return m.wire(out, ow, rows[0])
    if red == "booth_modular":
        # radix-4 Booth digits of b: rows d * a * 4^j mod m, the negative rows as m - |row|
        nd = -(-(ow + 1) // 2)
        bx = m.wire(f"{out}_bx", 2 * nd + 1, f"{{{{{2*nd+1-ow}{{1'b0}}}}, {b}, 1'b0}}")
        rows = []
        for j in range(nd):
            trip = f"{bx}[{2*j+2}:{2*j}]"
            a1 = _mod_reduce(m, m.wire(f"{out}_a1_{j}", ow + 2 * j, f"{{{{{2*j}{{1'b0}}}}, {a}}} << {2*j}" if j else a, cfg), ow + 2 * j, mod, f"{out}_r1_{j}", "csa", f"{tag}b1{j}", cfg) if j else a
            a2 = _mod_reduce(m, m.wire(f"{out}_a2_{j}", ow + 2 * j + 1, f"{{{{{2*j+1}{{1'b0}}}}, {a}}} << {2*j+1}", cfg), ow + 2 * j + 1, mod, f"{out}_r2_{j}", "csa", f"{tag}b2{j}", cfg)
            mag = m.wire(f"{out}_mg{j}", ow, f"({trip} == 3'd1 || {trip} == 3'd2) ? {a1} : ({trip} == 3'd3 || {trip} == 3'd4) ? {a2} : ({trip} == 3'd5 || {trip} == 3'd6) ? {a1} : {ow}'d0")
            neg = m.wire(f"{out}_ng{j}", 1, f"({trip} == 3'd4 || {trip} == 3'd5 || {trip} == 3'd6) && ({mag} != {ow}'d0)")
            rows.append(m.wire(f"{out}_row{j}", ow, f"{neg} ? ({ow}'d{mod} - {mag}) : {mag}"))
        sw = ow + (len(rows) - 1).bit_length() + 1
        s = _sum_terms(m, [f"{{{{{sw-ow}{{1'b0}}}}, {r}}}" for r in rows], sw, f"{out}_s", cfg, f"the modular multiply's rows mod {mod}")
        return _ladder(m, s, sw, mod, len(rows), out, ow)
    if red == "iterative_carry_save_msd_estimate":
        # the unrolled recurrence r = 2 r + a b_j - q m with q from the top remainder digits, one final subtraction
        # the estimate reads e top bits: q underestimates the true digit by at most one when the dropped
        # part is at most m / 4, so e = width - (ow - 3) = 6 at least (the pinned digits are radix-4 digits)
        e = max(6, min(10, int(cfg.get("est_digits", 4)) + 2))
        rw = ow + 1                                        # the residual stays below 2 m
        tw = ow + 3                                        # 2 r + a < 5 m
        r = m.wire(f"{out}_r0", rw, f"{rw}'d0")
        for j in range(ow - 1, -1, -1):
            t = m.wire(f"{out}_t{j}", tw, f"{{{{{tw-rw-1}{{1'b0}}}}, {r}, 1'b0}} + ({b}[{j}] ? {{{{{tw-ow}{{1'b0}}}}, {a}}} : {tw}'d0)")
            # q in 0..4 from the top e bits of t against an overestimate of m's top bits: an underestimate by at
            # most one, so t - q m stays below 2 m
            sh = max(0, tw - e)
            top = m.wire(f"{out}_tp{j}", e, f"{t}[{tw-1}:{sh}]" if sh else t)
            mt = (mod >> sh) + (1 if sh else 0)
            lim = (1 << e) - 1
            q = m.wire(f"{out}_q{j}", 3, " : ".join(f"({top} >= {e}'d{min(k*mt, lim)}) ? 3'd{k}" for k in (4, 3, 2, 1) if k * mt <= lim) + " : 3'd0")
            qm = m.wire(f"{out}_qm{j}", tw, f"{{{{{tw-3}{{1'b0}}}}, {q}}} * {tw}'d{mod}")
            rd = m.wire(f"{out}_rd{j}", tw, f"{t} - {qm}")
            r = m.wire(f"{out}_r{j+1}", rw, f"{rd}[{rw-1}:0]")
        return _ladder(m, r, rw, mod, 2, out, ow)
    # csa_with_periodic_folding: the rows a * b_j * 2^j reduced by the modulus' period, summed, one final reduction
    if f == "pow2":
        n = ow
        p = m.wire(f"{out}_p", 2 * n, f"{a} * {b}")
        return m.wire(out, ow, f"{p}[{n-1}:0]")
    if f == "pow2_minus_1":
        n = ow
        rows = [m.wire(f"{out}_row{j}", n, f"{b}[{j}] ? ({{{a}, {a}}} >> {n - j})[{n-1}:0] : {n}'d0" if j else f"{b}[0] ? {a} : {n}'d0") for j in range(n)]
        # rotated rows: {a, a} >> (n - j) takes a rotated left by j; as a slice of a concatenation it needs a wire
        for j in range(1, n):
            m.lines[-n + j] = f"  logic [{n-1}:0] {out}_rot{j}; assign {out}_rot{j} = ({{{a}, {a}}} >> {n - j});\n  logic [{n-1}:0] {out}_row{j}; assign {out}_row{j} = {b}[{j}] ? {out}_rot{j} : {n}'d0;"
        sw = n + (n - 1).bit_length() + 1
        s = _sum_terms(m, [f"{{{{{sw-n}{{1'b0}}}}, {r}}}" for r in rows], sw, f"{out}_s", cfg, f"the modular multiply's rows mod {mod}")
        return _mod_reduce(m, s, sw, mod, out, "csa", f"{tag}f", cfg)
    if f == "pow2_plus_1":
        n = ow - 1
        # a = 2^n stands for -1: the product is m - b; else the rows a 2^j = (a_lo << j) - a_hi with a_hi the wrapped bits
        rows = []
        for j in range(n + 1):
            if j == 0:
                rows.append(m.wire(f"{out}_row0", ow + 1, f"{b}[0] ? {{1'b0, {a}}} : {ow+1}'d0"))
                continue
            lo = m.wire(f"{out}_lo{j}", n, f"{a}[{n-1}:0] << {j}")
            hi = m.wire(f"{out}_hi{j}", n, f"{a}[{n-1}:0] >> {n - j}")
            rows.append(m.wire(f"{out}_row{j}", ow + 1, f"{b}[{j}] ? ({{2'b0, {lo}}} + {ow+1}'d{mod} - {{2'b0, {hi}}}) : {ow+1}'d0"))
        sw = ow + 1 + n.bit_length() + 1
        s = _sum_terms(m, [f"{{{{{sw-ow-1}{{1'b0}}}}, {r}}}" for r in rows], sw, f"{out}_s", cfg, f"the modular multiply's rows mod {mod}")
        s2 = _ladder(m, s, sw, mod, 2 * n + 3, f"{out}_pr", ow)
        neg_b = m.wire(f"{out}_nb", ow, f"({b} == {ow}'d0) ? {ow}'d0 : ({ow}'d{mod} - {b})")
        return m.wire(out, ow, f"({a} == {ow}'d{1 << n}) ? {neg_b} : {s2}")
    p = m.wire(f"{out}_p", 2 * ow, f"{a} * {b}")
    return _mod_reduce(m, p, 2 * ow, mod, out, "rom", f"{tag}g", cfg)


def _fwd(m: Mod, x: str, xw: int, mod: int, out: str, cfg: dict, tag: str) -> str:
    """out = x mod `mod` with the declared full-size word chunks."""
    from .rns_forward import forward
    return forward(m, x, xw, mod, out, cfg, tag)


def _rev(m: Mod, xs: list, ms: tuple, out: str, ow: int, cfg: dict) -> str:
    """Reconstruct canonical residues through the selected reverse algorithm."""
    from .rns_reverse import reverse
    return reverse(m, xs, ms, out, ow, cfg)


def _mrc_digits(m: Mod, xs: list, ms: tuple, tag: str, rom_steps: bool, cfg: dict | None = None) -> list:
    """Convert residues to digits with the selected ROM/arithmetic steps."""
    from .rns_reverse import mixed_radix_digits
    return mixed_radix_digits(m, xs, ms, tag, rom_steps, cfg)


def rns_cfg(family: str, pins: dict, W: int, kind: str, adder_selection=None, *, signed=False) -> dict:
    """The channel design under the declared channels family: its pins
    fill their part, the rest stands at the space defaults."""
    pins = pins or {}
    from chialu.targets.rtl.families.fidelity import effective, inactive
    if family not in REDUNDANT_FAMILIES["channels"]:
        raise ValueError(f"no implementation for RNS family {family!r}")
    if family == 'rns_scaling_comparison':
        if pins.get('method', 'rom_mrc') not in ('rom_mrc', 'crt_fraction_estimate', 'diagonal_function'):
            raise ValueError(f"RNS comparison method {pins['method']!r} has no implementation")
        if pins.get('exactness', 'exact') not in ('exact', 'approximate_with_correction'):
            raise ValueError(f"unknown RNS comparison exactness {pins['exactness']!r}")
    if family != "rns_channel_arithmetic":
        inactive(pins, "channel_width_n", "this family derives its moduli widths from the operation and channel count")
    if family not in ("rns_forward_converter", "rns_reverse_converter"):
        inactive(pins, "moduli_count", "this channels family has a three-modulus set")
    def integer_pin(key, default, lower, upper):
        value = pins.get(key, default)
        try:
            result = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"RNS {key} must be an integer in {lower}..{upper}, got {value!r}") from None
        if isinstance(value, bool) or str(result) != str(value).strip() or not lower <= result <= upper:
            raise ValueError(f"RNS {key} must be an integer in {lower}..{upper}, got {value!r}")
        return result

    if W < 1:
        raise ValueError(f"RNS operand width must be positive, got {W}")
    chunk_bits = integer_pin("chunk_bits", min(4, W), 1, 64) if family == "rns_forward_converter" else min(4, W)
    if family == "rns_forward_converter":
        from .rns_forward import chunk_layout
        chunks = chunk_layout(W, chunk_bits)
        effective(pins, "chunk_bits", max(bits for _, bits in chunks),
                  "one or more complete word chunks, followed by an optional short tail",
                  {"width": W, "chunks": [bits for _, bits in chunks], "offsets": [lo for lo, _ in chunks]})
    form = str(_pin(pins, "modulus_form", "pow2")) if family == "rns_channel_arithmetic" else "pow2"
    count = integer_pin("moduli_count", 3, 3, 64 if family == "rns_forward_converter" else 5) if family in ("rns_reverse_converter", "rns_forward_converter") else 3
    if kind == "multiplier":
        maximum = (1 << (2 * W - 2)) if signed else ((1 << W) - 1) ** 2
    elif kind == "adder":
        maximum = (1 << (W + 1)) - 1
    elif kind == "comparator":
        maximum = (1 << W) - 1
    else:
        raise ValueError(f"unknown RNS operation kind {kind!r}")
    need = maximum.bit_length()
    n_pin = integer_pin("channel_width_n", 4, 4, 32) if family == "rns_channel_arithmetic" and "channel_width_n" in pins else 0
    ms, n = moduli_set(form, count, need, n_pin, maximum=maximum,
                       n_min=4 if family == "rns_channel_arithmetic" else 3,
                       n_max=32 if family == "rns_channel_arithmetic" else None)
    geometry = {"width": W, "kind": kind, "signed": signed, "maximum": maximum,
                "capacity": math.prod(ms), "moduli": list(ms), "channel_widths": [(m - 1).bit_length() for m in ms]}
    if family == "rns_channel_arithmetic":
        effective(pins, "channel_width_n", n, "the fixed base exponent of the constructed moduli", geometry)
    elif family in ("rns_forward_converter", "rns_reverse_converter"):
        effective(pins, "moduli_count", len(ms), "one residue channel per constructed modulus", geometry)
    cfg = {"family": family, "moduli": ms, "n": n, "form": form,
           "fwd": str(_pin(pins, "implementation", "rom_per_chunk")) if family == "rns_forward_converter" else "rom_per_chunk",
           "chunk_bits": chunk_bits,
           "fwd_final": str(_pin(pins, "final_reduction", "modular_adder")) if family == "rns_forward_converter" else "modular_adder",
           "rev": str(_pin(pins, "algorithm", "crt")) if family == "rns_reverse_converter" else "crt",
           "rev_impl": str(_pin(pins, "implementation", "rom")) if family == "rns_reverse_converter" else "adder_based",
           "mul_red": str(_pin(pins, "multiplier_reduction", "rom")) if family == "rns_channel_arithmetic" else "csa_with_periodic_folding",
           "est_digits": _ipin(pins, "remainder_estimate_digits", 4) if family == "rns_channel_arithmetic" else 4,
           "dim1": str(_pin(pins, "pow2_plus_1_encoding", "normal")) == "diminished_one" if family == "rns_channel_arithmetic" else False,
           # The modular_adder family realizes channel additions, residue sums
           # and constant-multiply terms. The implicit family is ripple_carry.
           "adder_family": _pin(pins, "modular_adder.family", "ripple_carry"), "adder_pins": _sub(pins, "modular_adder."),
           "col_family": _pin(pins, "column_reducer.family", None) if family == "rns_forward_converter" else None,
           "col_pins": _sub(pins, "column_reducer.") if family == "rns_forward_converter" else {},
           "cmp_method": str(_pin(pins, "method", "rom_mrc")) if family == "rns_scaling_comparison" else "rom_mrc",
           "cmp_exact": str(_pin(pins, "exactness", "exact")) == "exact" if family == "rns_scaling_comparison" else True,
           "maximum": maximum}
    if adder_selection is not None:
        cfg["adder_family"], cfg["adder_pins"] = adder_selection
    return cfg


def _rns_header(cfg: dict, what: str) -> str:
    ms = cfg["moduli"]
    return (f"rns_internal ({cfg['family']}): {what} over the moduli {{{', '.join(str(x) for x in ms)}}} (M = {math.prod(ms)}"
            f", maximum represented value {cfg['maximum']}); forward conversion "
            f"{cfg['fwd']} (chunk_bits {cfg['chunk_bits']}), channel adders per modulus form"
            f"{' (2^n + 1 in diminished-one)' if cfg['dim1'] else ''}, reverse conversion {cfg['rev']} ({cfg['rev_impl']})")


def _render_rns(m: Mod, cfg: dict, pins: dict) -> str:
    key = 'column_reducer.compressor'
    if key in pins:
        from .fidelity import effective, inactive
        wanted = str(pins[key])
        rows = [record for record in m.reduction_stats if record['compressor'] == wanted]
        full = sum(record['full_word_cells'] for record in rows)
        if not full:
            inactive(pins, key, f'{wanted} requires at least one full compressor group; all reductions were smaller tails')
        effective(pins, key, wanted, 'full selected compressor groups; 3:2 tails do not count as 4:2 or 7:3 coverage',
                  {'full_word_cells': full, 'full_bit_cells': sum(record['full_bit_cells'] for record in rows),
                   'reductions': rows})
    return m.render()


def rns_adder_sv(W: int, family: str, pins: dict, name: str, adder_selection=None, control_ports=None) -> str:
    cfg = rns_cfg(family, pins, W, "adder", adder_selection)
    ms = cfg["moduli"]
    m = Mod(name, _adder_ports(W), _rns_header(cfg, "the lane's adder: {cout, s} = a + b + cin"), control_ports)
    xs = []
    for i, mm in enumerate(ms):
        ra = _fwd(m, "a", W, mm, f"ra{i}", cfg, f"a{i}")
        rb = _fwd(m, "b", W, mm, f"rb{i}", cfg, f"b{i}")
        xs.append(_mod_add(m, ra, rb, "cin", mm, f"rs{i}", cfg, str(i)))
    ow = (math.prod(ms) - 1).bit_length()
    x = _rev(m, xs, ms, "x", ow, cfg)
    m.assign("s", f"{x}[{W-1}:0]")
    m.assign("cout", f"{x}[{W}]")
    return _render_rns(m, cfg, pins)


def rns_mul_sv(W: int, signed: bool, family: str, pins: dict, name: str, adder_selection=None, control_ports=None) -> str:
    cfg = rns_cfg(family, pins, W, "multiplier", adder_selection, signed=signed)
    ms = cfg["moduli"]
    m = Mod(name, f"input logic [{W-1}:0] a, input logic [{W-1}:0] b, output logic [{2*W-1}:0] p",
            _rns_header(cfg, f"the lane's {'signed' if signed else 'unsigned'} multiplier on magnitudes, channel multipliers {cfg['mul_red']}"), control_ports)
    if signed:
        m.wire("ma", W, f"a[{W-1}] ? -a : a")
        m.wire("mb", W, f"b[{W-1}] ? -b : b")
        m.wire("neg", 1, f"a[{W-1}] ^ b[{W-1}]")
    else:
        m.wire("ma", W, "a")
        m.wire("mb", W, "b")
    xs = []
    for i, mm in enumerate(ms):
        ra = _fwd(m, "ma", W, mm, f"ra{i}", cfg, f"a{i}")
        rb = _fwd(m, "mb", W, mm, f"rb{i}", cfg, f"b{i}")
        xs.append(_mod_mul(m, ra, rb, mm, f"rp{i}", cfg, str(i)))
    ow = (math.prod(ms) - 1).bit_length()
    x = _rev(m, xs, ms, "x", ow, cfg)
    product = (f"{{{{{2*W-ow}{{1'b0}}}}, {x}}}" if ow < 2 * W else
               f"{x}[{2*W-1}:0]" if ow > 2 * W else x)
    m.assign("p", f"neg ? -{product} : {product}" if signed else product)
    return _render_rns(m, cfg, pins)


def rns_cmp_sv(W: int, signed: bool, family: str, pins: dict, name: str, adder_selection=None, control_ports=None) -> str:
    cfg = rns_cfg(family, pins, W, "comparator", adder_selection, signed=signed)
    ms = cfg["moduli"]
    M = math.prod(ms)
    k = len(ms)
    method = cfg["cmp_method"]
    if method not in ('rom_mrc', 'crt_fraction_estimate', 'diagonal_function'):
        raise ValueError(f'RNS comparison method {method!r} has no implementation')
    m = Mod(name, f"input logic [{W-1}:0] a, input logic [{W-1}:0] b, output logic lt, output logic eq",
            _rns_header(cfg, f"the lane's {'signed' if signed else 'unsigned'} comparator by {method}"
                        + ("" if cfg["cmp_exact"] else " (approximate estimate with an exact correction)")), control_ports)
    # unsigned order: a signed pattern is offset by 2^(W-1)
    m.wire("ua", W, (f"{{~a[{W-1}], a[{W-2}:0]}}" if W > 1 else "~a") if signed else "a")
    m.wire("ub", W, (f"{{~b[{W-1}], b[{W-2}:0]}}" if W > 1 else "~b") if signed else "b")
    xa, xb = [], []
    for i, mm in enumerate(ms):
        xa.append(_fwd(m, "ua", W, mm, f"ra{i}", cfg, f"a{i}"))
        xb.append(_fwd(m, "ub", W, mm, f"rb{i}", cfg, f"b{i}"))
    m.assign("eq", " & ".join(f"({xa[i]} == {xb[i]})" for i in range(k)))
    ws = [(mm - 1).bit_length() for mm in ms]
    if method == "diagonal_function":
        # D(X) equals sum floor(X/m_i) over 0 <= X < M. It increases
        # monotonically; within a tie interval no residue can wrap.
        SQ = sum(M // mm for mm in ms)
        try:
            ks = [(-pow(mm, -1, SQ)) % SQ for mm in ms]
        except ValueError as error:
            raise ValueError('diagonal_function requires each modulus to be invertible modulo SQ') from error
        if sum(ks) % SQ or any((ki * mi + 1) % SQ for ki, mi in zip(ks, ms)):
            raise ValueError('diagonal_function constants do not establish the exact floor-sum identity')
        sqw = (SQ - 1).bit_length()
        outs = []
        for tag, xs in (("a", xa), ("b", xb)):
            sw = sqw + (k - 1).bit_length() + 1
            terms = []
            for i in range(k):
                t = _const_mul(m, xs[i], ws[i], ks[i], f"d{tag}_t{i}", ws[i] + sqw, "csd", f"d{tag}{i}", cfg)
                terms.append(_mod_reduce(m, t, ws[i] + sqw, SQ, f"d{tag}_r{i}", "rom", f"d{tag}r{i}", cfg))
            s = _sum_terms(m, [f"{{{{{sw-sqw}{{1'b0}}}}, {t}}}" for t in terms], sw, f"d{tag}_s", cfg, "the diagonal function's terms")
            outs.append(_ladder(m, s, sw, SQ, k, f"d{tag}", sqw))
        if cfg['cmp_exact']:
            m.assign("lt", f"({outs[0]} < {outs[1]}) | (({outs[0]} == {outs[1]}) & ({xa[0]} < {xb[0]}))")
        else:
            from .rns_compare import corrected_keys
            from .fidelity import effective
            discarded = max(1, sqw // 2)
            if sum(cfg['maximum'] // mi for mi in ms) < 1 << discarded:
                raise ValueError('approximate diagonal comparison needs a nonconstant coarse key; increase operand width')
            proof = corrected_keys(m, f'{outs[0]}[{sqw-1}:{discarded}]', f'{outs[1]}[{sqw-1}:{discarded}]', sqw-discarded,
                                   f'{{{outs[0]}[{discarded-1}:0], {xa[0]}}}', f'{{{outs[1]}[{discarded-1}:0], {xb[0]}}}',
                                   discarded+ws[0], model='high diagonal bits, corrected by low bits and the residue tie key',
                                   error_units=1 << discarded)
            effective(pins, 'exactness', 'approximate_with_correction', 'coarse diagonal estimate and exact tie correction', proof)
        return _render_rns(m, cfg, pins)
    if method == "crt_fraction_estimate":
        # X / M = |sum x_i w_i / m_i|_1 with w_i = (M / m_i)^-1 mod m_i; f fraction bits: exact when the k rounding
        # errors stay below 1 / (2 M), else an approximate estimate whose ties fall to the exact width
        wsi = [pow(M // mm, -1, mm) for mm in ms]
        f_exact = (M - 1).bit_length() + (k - 1).bit_length() + 2
        f_used = f_exact if cfg["cmp_exact"] else max(4, (M - 1).bit_length() - 4)

        def frac_terms(tag, xs, f):
            terms = []
            for i in range(k):
                vals = [int(((v * wsi[i]) % ms[i]) * (1 << f) // ms[i]) if v < ms[i] else 0 for v in range(1 << ws[i])]
                if ws[i] <= 10:
                    terms.append(_rom(m, f"TF{tag}{f}_{i}", vals, f, xs[i], f"f{tag}{f}_{i}"))
                else:
                    # floor(r 2^f / m) by the constant reciprocal R = floor(2^(f+g) / m) + 1 with g = bits(m): exact for r < m
                    r = _mod_reduce(m, _const_mul(m, xs[i], ws[i], wsi[i], f"f{tag}{f}_p{i}", 2 * ws[i], "csd", f"f{tag}{i}", cfg),
                                    2 * ws[i], ms[i], f"f{tag}{f}_q{i}", "rom", f"fq{tag}{i}", cfg)
                    g = ms[i].bit_length()
                    R = (1 << (f + g)) // ms[i] + 1
                    pw = ws[i] + f + g + 1
                    prod = _const_mul(m, r, ws[i], R, f"f{tag}{f}_m{i}", pw, "csd", f"fr{tag}{i}", cfg)
                    terms.append(m.wire(f"f{tag}{f}_{i}", f, f"{prod}[{g+f-1}:{g}]"))
            sw = f + (k - 1).bit_length() + 1
            s = _sum_terms(m, [f"{{{{{sw-f}{{1'b0}}}}, {t}}}" for t in terms] + [f"{sw}'d{k}"], sw, f"f{tag}{f}_s", cfg,
                           "the CRT fraction terms")
            return m.wire(f"f{tag}{f}", f, f"{s}[{f-1}:0]")
        fa, fb = frac_terms("a", xa, f_used), frac_terms("b", xb, f_used)
        if cfg["cmp_exact"]:
            m.assign("lt", f"({fa} < {fb})")
        else:
            band = 2 * k + 2
            if W < 8:
                estimates = [(sum(((value % mi) * wi % mi) * (1 << f_used) // mi
                                  for mi, wi in zip(ms, wsi)) + k) % (1 << f_used) for value in range(1 << W)]
                if max(estimates)-min(estimates) <= band:
                    raise ValueError('approximate CRT comparison has an always-active correction at this width; use at least 7 operand bits')
            near = m.wire("near", 1, f"(({fa} > {fb}) ? ({fa} - {fb}) : ({fb} - {fa})) <= {f_used}'d{band}")
            ea, eb = frac_terms("a", xa, f_exact), frac_terms("b", xb, f_exact)
            m.assign("lt", f"near ? ({ea} < {eb}) : ({fa} < {fb})")
        return _render_rns(m, cfg, pins)
    # rom_mrc: the mixed-radix digits of both operands, compared from the most significant digit down
    digs = [_mrc_digits(m, xa, ms, "ma", True, cfg), _mrc_digits(m, xb, ms, "mb", True, cfg)]
    if not cfg['cmp_exact']:
        from .rns_compare import corrected_keys
        from .fidelity import effective
        if cfg['maximum'] < math.prod(ms[:-1]):
            raise ValueError('approximate mixed-radix comparison needs two live high digits; increase operand width')
        split = k-2
        coarse = ['{' + ', '.join(reversed(values[split:])) + '}' for values in digs]
        fine = ['{' + ', '.join(reversed(values[:split])) + '}' for values in digs]
        proof = corrected_keys(m, *coarse, sum(ws[split:]), *fine, sum(ws[:split]),
                               model='two high mixed-radix digits, corrected by the remaining low digits',
                               error_units=math.prod(ms[:split]))
        effective(pins, 'exactness', 'approximate_with_correction', 'coarse mixed-radix estimate and exact tie correction', proof)
        return _render_rns(m, cfg, pins)
    expr = "1'b0"
    for i in range(k):
        expr = f"(({digs[0][i]} < {digs[1][i]}) | (({digs[0][i]} == {digs[1][i]}) & ({expr})))"
    m.assign("lt", expr)
    return _render_rns(m, cfg, pins)


def rns_sv(kind: str, W: int, family: str, pins: dict, signed: bool = False, name: str | None = None,
           adder_selection=None, control_ports=None) -> tuple:
    """(name, text) of the lane module of an rns_internal core: kind
    adder / multiplier / comparator under the channels family."""
    if family not in REDUNDANT_FAMILIES["channels"]:
        raise ValueError(f"no module for the channels family {family}")
    pins = pins or {}
    if adder_selection is not None:
        from chialu.targets.rtl.families.selection import copy_pins
        adder_family, adder_pins = adder_selection
        selected = {"modular_adder.family": adder_family,
                    **{"modular_adder." + key: value for key, value in adder_pins.items()}}
        for key, value in selected.items():
            if key in pins and pins[key] != value:
                raise ValueError(f"RNS channel CPA disagrees on {key}")
        pins = copy_pins(pins, **selected)
    tagf = {"rns_channel_arithmetic": "chan", "rns_reverse_converter": "rev", "rns_forward_converter": "fwd", "rns_scaling_comparison": "cmp"}[family]
    if kind == "adder":
        name = name or f"fam_rns_adder_{tagf}_w{W}{_ptag(pins)}"
        return name, rns_adder_sv(W, family, pins, name, adder_selection, control_ports)
    if kind == "multiplier":
        name = name or f"fam_rns_mul_{tagf}_w{W}_{'s' if signed else 'u'}{_ptag(pins)}"
        return name, rns_mul_sv(W, signed, family, pins, name, adder_selection, control_ports)
    if kind == "comparator":
        name = name or f"fam_rns_cmp_{tagf}_w{W}_{'s' if signed else 'u'}{_ptag(pins)}"
        return name, rns_cmp_sv(W, signed, family, pins, name, adder_selection, control_ports)
    raise ValueError(f"rns_internal has no {kind} module")


from chialu.targets.rtl.families.selection import track_factory as _track_factory
representation_adder_sv = _track_factory(representation_adder_sv)
rns_sv = _track_factory(rns_sv)


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description="emit a redundant-representation or residue-number-system lane module")
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--slot", default="representation", choices=("representation", "channels"))
    ap.add_argument("--kind", default="adder", choices=("adder", "multiplier", "comparator"))
    ap.add_argument("--family", default="generalized_signed_digit")
    ap.add_argument("--pins", default="", help="k=v,k=v")
    ap.add_argument("--signed", action="store_true")
    a = ap.parse_args()
    pins = {}
    for item in a.pins.split(","):
        if not item:
            continue
        key, value = item.split("=", 1)
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
        pins[key] = value
    if a.slot == "representation":
        n, t = representation_adder_sv(a.width, a.family, pins)
    else:
        n, t = rns_sv(a.kind, a.width, a.family, pins, a.signed)
    print(t)
