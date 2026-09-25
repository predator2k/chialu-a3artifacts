"""Multiplier families as bit-level netlists: the partial products (an
AND array with the Baugh-Wooley terms or sign-extended rows, 2-bit
groups with a 3M precompute, radix-4, radix-8 and radix-16 Booth
recoding with the hard multiples from the hard_multiple_adder slot, as
short adders whose carries join the tree, or from a lookahead
specialized to a + 2^k a; the negative rows as ones' complement plus a
bit or as multiples negated through the negation_incrementer slot; the
sign extension in full, as ~s plus a folded constant, or as Roorda's
compact pattern), a reduction chosen by the reduction slot's family
(the counter tree in five geometries over 3:2, 4:2, 5:2 or 7:3 cells,
the compressor tree over 4:2, 5:2, 7:3 or symmetric-stacking 6:3
cells, the tiled CPA tree of short adders from the tile_adder slot)
and the final carry-propagate adder from the adder library (any cpa
family under `uniform`, or the arrival-driven hybrid of regions under
`hybrid_arrival_driven`); recursive Karatsuba over base multipliers
with its adds through the adder slot. Every module is unrolled
SystemVerilog

    module fam_mul_<family>_<variant>_w<W>_<s|u>_p<tag> (input [W-1:0] a, input [W-1:0] b, output [2W-1:0] p);

with the signedness fixed at generation (the two's complement product
of the patterns, or the unsigned one) and the tag a hash of the pins.

    python3 -m chialu.targets.rtl.families.mul --width 16 --family booth_recoded_parallel --pins booth_radix=4,reduction.geometry=dadda --signed
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

GEOMETRIES = ("dadda", "wallace", "reduced_area", "balanced_delay", "tdm_arrival_driven")
COUNTERS = ("3_2", "4_2", "5_2", "7_3")
COMPRESSORS = ("4_2", "5_2", "7_3", "stacking_6_3")
REDUCTION_FAMILIES = ("csa_reduction_tree", "compressor_4_2_tree", "tiled_cpa_reduction_tree")
TREE_FAMILIES = ("direct_pp_parallel", "booth_recoded_parallel", "carry_save_array")


def _tag(pins: dict) -> str:
    """A short tag of the pins for a module name (empty for none)."""
    d = {k: v for k, v in (pins or {}).items() if not str(k).startswith("_")}
    if not d:
        return ""
    # eight hex digits: a family renders thousands of pin sets, and two must never share a name
    return "_p" + hashlib.sha1(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:8]


class Netlist:
    """The assigns of a module: named wires over expressions, plus the
    library instances it holds (their lines and module texts)."""

    def __init__(self):
        self.assigns: list = []
        self.widths: dict = {}
        self.count = 0
        self.fa_count = 0
        self.ha_count = 0
        self.cell_count = 0
        self.insts: list = []           # instance lines (with their declarations)
        self.extra: list = []           # module texts of generated instances
        self.n_inst = 0
        self.arrival: dict = {}         # wire -> arrival depth in cell levels (the reduction's bookkeeping)

    def wire(self, expr: str, prefix: str = "t", width: int = 1, depth: int | None = None) -> str:
        name = f"{prefix}{self.count}"
        self.count += 1
        self.assigns.append((name, expr))
        if width > 1:
            self.widths[name] = width
        if depth is not None:
            self.arrival[name] = depth
        return name

    def t(self, x: str) -> int:
        """The arrival depth of a bit (0 for an operand bit or a constant)."""
        return self.arrival.get(x.split("[")[0], 0)

    def fa(self, x: str, y: str, z: str) -> tuple:
        self.fa_count += 1
        d = max(self.t(x), self.t(y), self.t(z)) + 1
        return (self.wire(f"{x} ^ {y} ^ {z}", depth=d), self.wire(f"({x} & {y}) | ({x} & {z}) | ({y} & {z})", depth=d))

    def ha(self, x: str, y: str) -> tuple:
        self.ha_count += 1
        d = max(self.t(x), self.t(y)) + 1
        return (self.wire(f"{x} ^ {y}", depth=d), self.wire(f"{x} & {y}", depth=d))

    def inst(self, m, conns: str, comment: str, decls: str = "") -> None:
        """A library module instance (its text collected when generated)."""
        if m.text:
            self.extra.append(m.text)
        ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
        self.n_inst += 1
        if decls:
            self.insts.append(decls)
        self.insts.append(f"  // {comment}")
        self.insts.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u_i{self.n_inst} ({conns});")

    def adder(self, fam: str, pins: dict, width: int, a: str, b: str, cin: str, s: str, cout: str, comment: str) -> None:
        """s, cout = a + b + cin through the adder family's library module
        (s and cout declared here)."""
        from .binary_cpa import adder_module
        m = adder_module(fam, pins, width)
        if m is None:
            raise ValueError(f"the adder family {fam!r} has no library module at {width} bits")
        decl = f"  logic [{width-1}:0] {s}; logic {cout};" if width > 1 else f"  logic {s}; logic {cout};"
        self.inst(m, f".a({a}), .b({b}), .cin({cin}), .s({s}), .cout({cout})", comment, decl)

    def incr(self, fam: str, pins: dict, width: int, a: str, cin: str, s: str, cout: str, comment: str) -> None:
        """s, cout = a + cin through the incrementer family's library module."""
        from chialu.targets.rtl import families as FAM
        m = FAM.incrementer_module(fam, pins, width)
        if m is None:
            raise ValueError(f"the incrementer family {fam!r} has no library module")
        decl = f"  logic [{width-1}:0] {s}; logic {cout};"
        self.inst(m, f".a({a}), .cin({cin}), .s({s}), .cout({cout})", comment, decl)

    def render(self) -> list:
        out = []
        ones = [n for n, _ in self.assigns if n not in self.widths]
        if ones:
            out.append("  logic " + ", ".join(ones) + ";")
        for n, w in self.widths.items():
            out.append(f"  logic [{w-1}:0] {n};")
        out += self.insts
        out += [f"  assign {n} = {e};" for n, e in self.assigns]
        return out


# ---- helpers ----------------------------------------------------------------------
def _pin(pins: dict, key: str, default):
    v = pins.get(key, default)
    return v if v not in (None, "") else default


def _ipin(pins: dict, key: str, default: int) -> int:
    try:
        return int(_pin(pins, key, default))
    except (TypeError, ValueError):
        return default


def _sub(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _cols(n: int) -> list:
    return [[] for _ in range(n)]


def _add_const(cols: list, value: int) -> None:
    """The bits of a constant into the columns (mod 2^len)."""
    value %= 1 << len(cols)
    for k in range(len(cols)):
        if (value >> k) & 1:
            cols[k].append("1'b1")


def _idents(expr: str) -> list:
    out, cur = [], ""
    for ch in expr:
        if ch.isalnum() or ch == "_":
            cur += ch
        else:
            if cur:
                out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


# ---- partial products ----------------------------------------------------------
def pp_and_array(nl: Netlist, w: int, signed: bool) -> list:
    """The AND array; for two's complement the Baugh-Wooley form: the
    products with exactly one sign bit are inverted and the constants
    2^w + 2^(2w-1) are added."""
    cols = _cols(2 * w)
    for i in range(w):
        for j in range(w):
            invert = signed and ((i == w - 1) != (j == w - 1))
            cols[i + j].append(nl.wire(f"{'~' if invert else ''}(a[{i}] & b[{j}])", "pp"))
    if signed:
        _add_const(cols, (1 << w) + (1 << (2 * w - 1)))
    return cols


def pp_sign_extended_rows(nl: Netlist, w: int, signed: bool) -> list:
    """Rows a_i * b sign-extended to the product width, the last row of a
    two's complement operand subtracted (inverted bits plus one)."""
    cols = _cols(2 * w)
    for i in range(w):
        last = signed and i == w - 1
        for k in range(2 * w - i):
            j = min(k, w - 1) if signed else k
            if not signed and k >= w:
                break
            bit = f"(a[{i}] & b[{j}])"
            cols[i + k].append(nl.wire(f"~{bit}" if last else bit, "pp"))
        if last:
            _add_const(cols, 1 << i)
    return cols


def _place_signed_rows(nl: Netlist, cols: list, rows: list, sign_ext: str, lg: int) -> None:
    """Place the rows of a recoded multiplier into the columns. A row is
    (base weight, bits lsb first with the top one the row's sign, neg bit
    or None); the sign is extended in full, as ~s with a folded constant
    (prevention_constant), or as Roorda's compact pattern (the first row
    ~s s..s, the others 1..1 ~s, whose excess vanishes modulo the product
    width); a neg bit enters the row's lsb column."""
    n = len(cols)
    const = 0
    for r, (base, bits, neg) in enumerate(rows):
        top = len(bits) - 1
        for j, bit in enumerate(bits[:-1]):
            if base + j < n:
                cols[base + j].append(bit)
        s = bits[-1]
        P = base + top
        if sign_ext == "full_extension":
            for k in range(P, n):
                cols[k].append(s)
        elif sign_ext == "roorda_compact":
            if r == 0:
                for k in range(P, min(P + lg, n)):
                    cols[k].append(s)
                if P + lg < n:
                    cols[P + lg].append(nl.wire(f"~{s}", "ns"))
            else:
                if P < n:
                    cols[P].append(nl.wire(f"~{s}", "ns"))
                for k in range(P + 1, min(P + lg, n)):
                    cols[k].append("1'b1")
        else:
            # the sign bit s at weight P sign-extended equals ~s at P minus 2^P
            if P < n:
                cols[P].append(nl.wire(f"~{s}", "ns"))
            const -= 1 << P
        if neg is not None and base < n:
            cols[base].append(neg)
    _add_const(cols, const)


class Multiples:
    """The multiples of the multiplicand a recoded multiplier selects
    from: k a for the odd k the radix needs, each as a list of bits (lsb
    first) at the multiple width, formed through the hard_multiple_adder
    slot (cpa_precompute), as short adders whose tile carries are extra
    bits of the multiple (partially_redundant), or by a lookahead
    specialized to the a + 2^j a pattern (specialized_3m_cpa); the even
    multiples are shifts. Under twos_complement_row the negatives are
    precomputed through the negation_incrementer slot."""

    def __init__(self, nl: Netlist, w: int, signed: bool, ext: int, pins: dict, gen: str, negatives: bool,
                 external: bool = False):
        self.nl, self.w, self.signed, self.ext = nl, w, signed, ext
        self.gen = gen
        self.hfam = str(_pin(pins, "hard_multiple_adder.family", "ripple_carry"))
        self.hpins = _sub(pins, "hard_multiple_adder.")
        # the negation_incrementer slot exists only where the negative multiples are precomputed
        self.ifam = str(_pin(pins, "negation_incrementer.family", "prefix_and_incrementer")) if negatives else ""
        self.ipins = _sub(pins, "negation_incrementer.") if negatives else {}
        self.negatives = negatives
        self.cache: dict = {}
        if external:
            # the caller declares a_ext and the hard multiple a3 at the multiple width (approx.py's approximate_booth)
            self.cache[(3, False)] = ("a3", [])
            return
        # a_ext: the multiplicand sign-extended (a zero sign for unsigned) to the multiple width
        nl.assigns.append(("a_ext", f"{{{{{ext - w}{{a[{w-1}]}}}}, a}}" if signed else f"{{{{{ext - w}{{1'b0}}}}, a}}"))
        nl.widths["a_ext"] = ext

    def bit(self, k: int, j: int, neg: bool = False) -> str:
        """Bit j of the multiple k a (or of -k a), sign-extended; the extra
        carry bits of a partially redundant multiple are in `extras`."""
        vec, _ = self.vec(k, neg)
        return f"{vec}[{j}]" if j < self.ext else f"{vec}[{self.ext - 1}]"

    def extras(self, k: int, neg: bool = False) -> list:
        """[(weight, bit)] of the tile carries of a partially redundant multiple."""
        return self.vec(k, neg)[1]

    def vec(self, k: int, neg: bool) -> tuple:
        key = (k, neg)
        if key in self.cache:
            return self.cache[key]
        nl, ext = self.nl, self.ext
        if neg:
            pos, pos_extras = self.vec(k, False)
            if pos_extras:
                raise ValueError("a partially redundant multiple has no precomputed negative")
            name = f"nm{k}"
            nl.assigns.append((f"nm{k}_i", f"~{pos}"))
            nl.widths[f"nm{k}_i"] = ext
            nl.incr(self.ifam, self.ipins, ext, f"nm{k}_i", "1'b1", name, f"nm{k}_co", f"-{k}a = ~({k}a) + 1 through the incrementer ({self.ifam})")
            self.cache[key] = (name, [])
            return self.cache[key]
        if k == 1:
            self.cache[key] = ("a_ext", [])
            return self.cache[key]
        if k & (k - 1) == 0:                          # a power of two: a shift
            sh = k.bit_length() - 1
            name = f"m{k}"
            nl.assigns.append((name, f"{{a_ext[{ext - 1 - sh}:0], {sh}'d0}}"))
            nl.widths[name] = ext
            self.cache[key] = (name, [])
            return self.cache[key]
        if k % 2 == 0:                                # an even multiple (6a): the odd one shifted, its carries with it
            sh = (k & -k).bit_length() - 1
            ov, oex = self.vec(k >> sh, False)
            name = f"m{k}"
            nl.assigns.append((name, f"{{{ov}[{ext - 1 - sh}:0], {sh}'d0}}"))
            nl.widths[name] = ext
            self.cache[key] = (name, [(wt + sh, c) for wt, c in oex])
            return self.cache[key]
        # an odd multiple: 3a = a + 2a, 5a = a + 4a, 7a = 8a - a
        if k == 7:
            x, y, sub = 8, 1, True
        else:
            x, y, sub = k - 1, 1, False
        xv, _ = self.vec(x, False)
        yv, _ = self.vec(y, False)
        name = f"m{k}"
        if self.gen == "partially_redundant":
            # K-bit tiles without carry propagation between them: the tile sums are the multiple's bits,
            # the tile carries extra bits at the tile boundaries (Bewick's partially redundant multiples)
            K = 4
            extras = []
            yy = yv
            if sub:
                nl.assigns.append((f"m{k}_ny", f"~{yv}"))
                nl.widths[f"m{k}_ny"] = ext
                yy = f"m{k}_ny"
            for t, lo in enumerate(range(0, ext, K)):
                hi = min(lo + K, ext)
                s, co = f"m{k}_t{t}", f"m{k}_c{t}"
                cin = "1'b1" if (sub and t == 0) else "1'b0"
                nl.adder(self.hfam, self.hpins, hi - lo, f"{xv}[{hi-1}:{lo}]", f"{yy}[{hi-1}:{lo}]", cin, s, co,
                         f"{k}a tile {t} ({self.hfam}, {hi - lo} bits): {x}a {'-' if sub else '+'} a without carry propagation across tiles")
                if hi < ext:
                    extras.append((hi, co))
            nl.assigns.append((name, "{" + ", ".join(f"m{k}_t{t}" for t in reversed(range((ext + K - 1) // K))) + "}"))
            nl.widths[name] = ext
            self.cache[key] = (name, extras)
            return self.cache[key]
        if self.gen == "specialized_3m_cpa":
            # a lookahead specialized to the pattern x a +- a: bit generates g_i = x_i y_i and propagates
            # p_i = x_i ^ y_i in groups of four with a group lookahead (the 3M adder of Bewick / Sam-Gupta)
            self._spec(name, xv, yv, sub)
            self.cache[key] = (name, [])
            return self.cache[key]
        # cpa_precompute: the slot's adder
        yy = yv
        if sub:
            nl.assigns.append((f"m{k}_ny", f"~{yv}"))
            nl.widths[f"m{k}_ny"] = ext
            yy = f"m{k}_ny"
        nl.adder(self.hfam, self.hpins, ext, xv, yy, "1'b1" if sub else "1'b0", name, f"m{k}_co",
                 f"the hard multiple {k}a = {x}a {'-' if sub else '+'} a through the adder ({self.hfam})")
        self.cache[key] = (name, [])
        return self.cache[key]

    def _spec(self, name: str, xv: str, yv: str, sub: bool) -> None:
        nl, ext = self.nl, self.ext
        G = 4
        yb = (lambda i: f"~{yv}[{i}]") if sub else (lambda i: f"{yv}[{i}]")
        g = [nl.wire(f"{xv}[{i}] & {yb(i)}", "hg") for i in range(ext)]
        p = [nl.wire(f"{xv}[{i}] ^ {yb(i)}", "hp") for i in range(ext)]
        c = ["1'b1" if sub else "1'b0"]
        for lo in range(0, ext, G):
            hi = min(lo + G, ext)
            # the group's carries from its generates and propagates and the group carry-in (a flat lookahead)
            cin = c[lo]
            for i in range(lo, hi):
                terms = [g[i]]
                for j in range(i - 1, lo - 1, -1):
                    terms.append("(" + " & ".join([g[j]] + p[j + 1:i + 1]) + ")")
                terms.append("(" + " & ".join(p[lo:i + 1] + [cin]) + ")")
                c.append(nl.wire(" | ".join(terms), "hc"))
        bits = [nl.wire(f"{p[i]} ^ {c[i]}", "hs") for i in range(ext)]
        nl.assigns.append((name, "{" + ", ".join(reversed(bits)) + "}"))
        nl.widths[name] = ext


def _booth_rows(nl: Netlist, w: int, signed: bool, radix: int, pins: dict, legacy: bool = False) -> tuple:
    """(rows, lg, extras, mults, const) of the Booth recoding at radix 4,
    8 or 16 over the signed extension of the operands: each row (base,
    bits, neg) is the selected multiple's magnitude as ones' complement
    with a neg bit (ones_complement_plus_neg_bit) or the precomputed
    negative multiple (twos_complement_row, neg None); the multiples
    come from Multiples. `legacy` is the contract of approx.py's
    approximate_booth: the minimal multiple width, and at radix 8 the
    caller's a_ext and a3."""
    n1 = w + (0 if signed else 1)                  # the signed operand width
    lg = {4: 2, 8: 3, 16: 4}[radix]
    ext = n1 + lg - (1 if legacy else 0)            # bits of a multiple up to 8a and its sign (one spare)
    gen = str(_pin(pins, "hard_multiple_gen", "cpa_precompute"))
    if signed and gen == "partially_redundant" and not legacy:
        # The unassimilated top tile is sign-extended separately from
        # the lower tile carries. Keep two sign bits so adding two
        # negative tiles cannot overflow that signed tile; radix 16
        # needs one more because 6a shifts the redundant 3a left once.
        top_bits = ext % 4
        sign_bits = lg - 1
        if 0 < top_bits < sign_bits:
            ext += sign_bits - top_bits
    neg_enc = str(_pin(pins, "negative_pp_encoding", "ones_complement_plus_neg_bit"))
    twos = neg_enc == "twos_complement_row"
    if twos and gen == "partially_redundant":
        raise ValueError("twos_complement_row needs assimilated multiples (hard_multiple_gen cpa_precompute or specialized_3m_cpa)")
    mults = Multiples(nl, w, signed, ext, pins, gen, twos, external=legacy and radix == 8)

    def bbit(k):
        if k < 0:
            return "1'b0"
        if k < w:
            return f"b[{k}]"
        return f"b[{w-1}]" if signed else "1'b0"

    rows = []
    extras = []
    const = 0
    n_digits = (n1 + lg - 1) // lg
    for k in range(n_digits):
        base = lg * k
        dbits = [bbit(base - 1)] + [bbit(base + t) for t in range(lg)]        # b_{base-1} .. b_{base+lg-1}
        # the digit d = -2^(lg-1) b_top + low, low = b_{base-1} + sum_{t < lg-1} 2^t b_{base+t} in [0, 2^(lg-1)]
        dw = lg
        top = dbits[-1]
        lowcat = "{" + ", ".join(reversed(dbits[1:-1])) + "}"                  # b_{base+lg-2} .. b_base
        low = nl.wire(f"{{1'b0, {lowcat}}} + {{{{{lg - 1}{{1'b0}}}}, {dbits[0]}}}", "lo", width=dw)
        neg = nl.wire(f"{top} & ~({' & '.join(dbits[:-1])})", "neg")             # negative and not the -0 code
        # the magnitude 0 .. 2^(lg-1): |d| = top ? 2^(lg-1) - low : low (the all-ones code is zero, its row all zeros)
        mag = nl.wire(f"{top} ? ({dw}'d{1 << (lg - 1)} - {low}) : {low}", "mg", width=dw)
        sels = {}
        for m in range(1, (1 << (lg - 1)) + 1):
            sels[m] = nl.wire(f"({mag} == {dw}'d{m})", "sel")
        bits = []
        for j in range(ext):
            terms = []
            for m, sel in sels.items():
                terms.append(f"({sel} & {mults.bit(m, j, neg=False)})")
            if twos:
                # the negative multiples precomputed: select -m a instead of m a
                v = nl.wire(" | ".join(terms), "pp")
                termsn = [f"({sel} & {mults.bit(m, j, neg=True)})" for m, sel in sels.items()]
                vn = nl.wire(" | ".join(termsn), "pp")
                bits.append(nl.wire(f"{neg} ? {vn} : {v}", "pp"))
            else:
                # one wire per bit, ((sel & a_j) | ...) ^ neg (approx.py's approximate_booth rewrites this shape)
                bits.append(nl.wire(f"({' | '.join(terms)}) ^ {neg}", "pp"))
        rows.append((base, bits, None if twos else neg))
        # the tile carries of partially redundant multiples: the selected multiple's carry at its weight,
        # complemented under neg; -c 2^wt = (~c) 2^wt - 2^wt, so a negative row whose multiple carries also
        # takes -2^wt: the bit ~(neg & selected) at wt with the constant -2^wt
        by_wt: dict = {}
        for m, sel in sels.items():
            for wt, cbit in mults.extras(m):
                by_wt.setdefault(wt, []).append((sel, cbit))
        for wt, terms in sorted(by_wt.items()):
            if base + wt >= 2 * w:
                continue
            for sel, cbit in terms:
                extras.append((base + wt, nl.wire(f"{sel} & ({cbit} ^ {neg})", "pp")))
            anysel = " | ".join(sel for sel, _ in terms)
            extras.append((base + wt, nl.wire(f"~({neg} & ({anysel}))", "pp")))
            const -= 1 << (base + wt)
    return rows, lg, extras, mults, const


def pp_booth(nl: Netlist, w: int, signed: bool, radix: int, pins, neg_enc: str | None = None,
             hard_adder: str | None = None):
    """The Booth partial products in columns. The older call
    (sign_ext, neg_enc, hard_adder) of approx.py's approximate_booth
    returns (columns, the extra module text) under its contract."""
    legacy = isinstance(pins, str)
    if legacy:
        pins = {"sign_extension": pins, "negative_pp_encoding": neg_enc or "ones_complement_plus_neg_bit"}
    n = 2 * w
    rows, lg, extras, mults, const = _booth_rows(nl, w, signed, radix, pins, legacy=legacy)
    cols = _cols(n)
    sign_ext = str(_pin(pins, "sign_extension", "prevention_constant"))
    _place_signed_rows(nl, cols, rows, sign_ext, lg)
    # the tile carries of partially redundant multiples and their negation constant
    for wt, bit in extras:
        cols[wt].append(bit)
    _add_const(cols, const)
    if legacy:
        return cols, "".join(nl.extra)
    return cols


def pp_groups2(nl: Netlist, w: int, signed: bool, pins: dict) -> list:
    """Non-recoded 2-bit groups: each pair of multiplier bits selects 0, a,
    2a or 3a (3a through the hard_multiple_adder slot); a signed
    multiplier's top group has the weight -2 b_top + b_below, so its
    row is the negative of the selected multiple (ones' complement plus
    a bit)."""
    n1 = w + (0 if signed else 1)
    lg = 2
    ext = n1 + 2
    # the direct family has no hard_multiple_gen choice: 3a is assimilated through the hard_multiple_adder slot
    mults = Multiples(nl, w, signed, ext, pins, "cpa_precompute", False)
    n_groups = (n1 + 1) // 2
    rows = []
    extras = []
    for k in range(n_groups):
        base = 2 * k
        b0 = f"b[{base}]" if base < w else ("1'b0")
        b1 = f"b[{base + 1}]" if base + 1 < w else (f"b[{w-1}]" if signed and base + 1 >= w else "1'b0")
        # An odd-width operand has a final group made of its sign bit
        # and one sign-extension bit. That group is negative as well.
        top_group = signed and (base + 1 >= w - 1)
        if top_group:
            # d = -2 b1 + b0: magnitude and sign
            neg = nl.wire(f"{b1} & ~{b0}", "neg")             # -2
            neg1 = nl.wire(f"{b1} & {b0}", "neg")             # -1
            negb = nl.wire(f"{neg} | {neg1}", "neg")
            sel1 = nl.wire(f"({b0} & ~{b1}) | {neg1}", "sel")
            sel2 = nl.wire(f"{neg}", "sel")
            sels = {1: sel1, 2: sel2}
        else:
            negb = None
            sels = {1: nl.wire(f"{b0} & ~{b1}", "sel"), 2: nl.wire(f"~{b0} & {b1}", "sel"), 3: nl.wire(f"{b0} & {b1}", "sel")}
        bits = []
        for j in range(ext):
            terms = [f"({sel} & {mults.bit(m, j)})" for m, sel in sels.items()]
            v = nl.wire(" | ".join(terms), "pp")
            bits.append(nl.wire(f"{v} ^ {negb}", "pp") if negb is not None else v)
        rows.append((base, bits, negb))
        for m, sel in sels.items():
            for wt, cbit in mults.extras(m):
                if base + wt < 2 * w:
                    extras.append((base + wt, nl.wire(f"{sel} & {cbit}", "pp") if negb is None else nl.wire(f"{sel} & ({cbit} ^ {negb})", "pp"), negb))
    cols = _cols(2 * w)
    sign_ext = "prevention_constant" if signed else "full_extension"
    if not signed:
        # unsigned rows: no sign, the multiples' top bit is a data bit
        for base, bits, negb in rows:
            for j, bit in enumerate(bits):
                if base + j < 2 * w:
                    cols[base + j].append(bit)
    else:
        _place_signed_rows(nl, cols, rows, sign_ext, lg)
    for wt, bit, negb in extras:
        cols[wt].append(bit)
        if negb is not None:
            cols[wt].append(negb)
    return cols


# ---- reduction -----------------------------------------------------------------
def _dadda_targets(h: int) -> list:
    seq = [2]
    while seq[-1] < h:
        seq.append(seq[-1] * 3 // 2)
    return [d for d in reversed(seq) if d < h]


def reduce_dadda(nl: Netlist, cols: list) -> list:
    n = len(cols)
    h = max((len(c) for c in cols), default=0)
    for d in _dadda_targets(h):
        new = [[] for _ in range(n)]
        carry_in: list = []
        for c in range(n):
            bits = cols[c] + carry_in
            carry_in = []
            while len(bits) > d:
                if len(bits) - d >= 2:
                    s, co = nl.fa(bits.pop(0), bits.pop(0), bits.pop(0))
                else:
                    s, co = nl.ha(bits.pop(0), bits.pop(0))
                bits.append(s)
                carry_in.append(co)
            new[c] = bits
        cols = new
    return cols


def reduce_wallace(nl: Netlist, cols: list, half_adders: bool = True) -> list:
    """Wallace: every column reduced as early as possible with full adders
    (and half adders on a leftover pair while the matrix is taller than
    three); half_adders False is Bickerstaff's reduced-area schedule:
    full adders alone until the final stage, where half adders bring the
    columns to two rows."""
    n = len(cols)
    guard = 0
    while max((len(c) for c in cols), default=0) > 2:
        guard += 1
        if guard > 64:
            return reduce_dadda(nl, cols)
        before = max(len(c) for c in cols)
        new = [[] for _ in range(n)]
        carry_in: list = []
        for c in range(n):
            bits = cols[c]
            out = list(carry_in)
            carry_in = []
            while len(bits) >= 3:
                s, co = nl.fa(bits.pop(0), bits.pop(0), bits.pop(0))
                out.append(s)
                carry_in.append(co)
            if len(bits) == 2 and ((half_adders and before > 3) or (not half_adders and before <= 3 and len(out) + len(bits) > 2)):
                s, co = nl.ha(bits.pop(0), bits.pop(0))
                out.append(s)
                carry_in.append(co)
            new[c] = out + bits
        cols = new
        if max(len(c) for c in cols) >= before:
            return reduce_dadda(nl, cols)
    return cols


def reduce_by_arrival(nl: Netlist, cols: list, tdm: bool) -> list:
    """The delay-balanced schedule: every column reduced Dadda-style
    toward the stage targets, the earliest-arriving bits combined
    first; under `tdm` the counter's own input delays count (the third
    input of a full adder is one XOR faster: the latest bit takes it,
    Oklobdzija's three-greedy assignment), else the cell is symmetric."""
    n = len(cols)
    h = max((len(c) for c in cols), default=0)
    for d in _dadda_targets(h):
        new = [[] for _ in range(n)]
        carry_in: list = []
        for c in range(n):
            bits = sorted(cols[c] + carry_in, key=nl.t)
            carry_in = []
            while len(bits) > d:
                if len(bits) - d >= 2:
                    x, y, z = bits.pop(0), bits.pop(0), bits.pop(0)
                    if tdm:
                        # the latest of the three on the fast input: the cell's output time is
                        # max(t_x + 2, t_y + 2, t_z + 1) in XOR units
                        s = nl.wire(f"{x} ^ {y} ^ {z}", depth=max(nl.t(x) + 1, nl.t(y) + 1, nl.t(z)) + 0)
                        co = nl.wire(f"({x} & {y}) | ({x} & {z}) | ({y} & {z})", depth=nl.t(s))
                        nl.fa_count += 1
                    else:
                        s, co = nl.fa(x, y, z)
                else:
                    s, co = nl.ha(bits.pop(0), bits.pop(0))
                bits.append(s)
                bits.sort(key=nl.t)
                carry_in.append(co)
            new[c] = bits
        cols = new
    return cols


def _stack6(nl: Netlist, x: list) -> list:
    """The 3-bit count of six bits by symmetric bit stacking (Fritz and
    Fam): two 3-bit stacks, merged into a 6-bit stack (t_k = at least k+1
    ones), the count read from the stack."""
    def stack3(a, b, c):
        return [nl.wire(f"{a} | {b} | {c}", "sk"), nl.wire(f"({a} & {b}) | ({a} & {c}) | ({b} & {c})", "sk"), nl.wire(f"{a} & {b} & {c}", "sk")]
    A = stack3(*x[:3])
    B = stack3(*x[3:6])
    a = ["1'b1"] + A
    b = ["1'b1"] + B
    t = []
    for k in range(1, 7):
        terms = [f"({a[i]} & {b[k - i]})" for i in range(0, 4) if 0 <= k - i <= 3]
        t.append(nl.wire(" | ".join(terms), "sk"))
    # t[k-1]: at least k ones; the count bits from the stack
    c2 = t[3]
    c1 = nl.wire(f"({t[1]} & ~{t[3]}) | {t[5]}", "sk")
    c0 = nl.wire(f"({t[0]} & ~{t[1]}) | ({t[2]} & ~{t[3]}) | ({t[4]} & ~{t[5]})", "sk")
    nl.cell_count += 1
    return [c0, c1, c2]


def _cell(nl: Netlist, kind: str, x: list) -> list:
    """[(weight offset, bit)] of one counter or compressor cell over the
    equal-weight bits x (as many as the cell takes)."""
    if kind == "4_2":
        # the 4:2 compressor: two full adders in series; the first's carry and the second's are the next weight
        s1, c1 = nl.fa(x[0], x[1], x[2])
        s, c = nl.fa(s1, x[3], "1'b0")
        nl.cell_count += 1
        return [(0, s), (1, c), (1, c1)]
    if kind == "5_2":
        # three full adders: the sum and three carries of the next weight
        s1, c1 = nl.fa(x[0], x[1], x[2])
        s2, c2 = nl.fa(s1, x[3], x[4])
        nl.cell_count += 1
        return [(0, s2), (1, c1), (1, c2)]
    if kind == "7_3":
        s1, c1 = nl.fa(x[0], x[1], x[2])
        s2, c2 = nl.fa(x[3], x[4], x[5])
        s3, c3 = nl.fa(s1, s2, x[6])
        s4, c4 = nl.fa(c1, c2, c3)
        nl.cell_count += 1
        return [(0, s3), (1, s4), (2, c4)]
    if kind == "stacking_6_3":
        c0, c1, c2 = _stack6(nl, x)
        return [(0, c0), (1, c1), (2, c2)]
    if kind == "9_2":
        # a two-level 3:2 arrangement: three sums summed again; the sum and four carries of the next weight
        s1, c1 = nl.fa(x[0], x[1], x[2])
        s2, c2 = nl.fa(x[3], x[4], x[5])
        s3, c3 = nl.fa(x[6], x[7], x[8])
        s, c = nl.fa(s1, s2, s3)
        nl.cell_count += 1
        return [(0, s), (1, c), (1, c1), (1, c2), (1, c3)]
    raise ValueError(f"no cell {kind!r}")


CELL_INPUTS = {"3_2": 3, "4_2": 4, "5_2": 5, "7_3": 7, "stacking_6_3": 6, "9_2": 9}


CELL_OUTPUTS = {"4_2": 3, "5_2": 3, "7_3": 3, "stacking_6_3": 3, "9_2": 5}


def reduce_cells(nl: Netlist, cols: list, kind: str, terminal: bool = False) -> list:
    """Column reduction by one cell kind on Dadda's stage targets: a column
    above the stage's target applies the cell where it removes at least
    the excess (k inputs into one bit of its weight and the rest above),
    a full adder where two bits must go, a half adder for the last one;
    the outputs enter the columns above within the stage. A terminal
    cell (the tiled tree's close) takes every column it shortens, its
    missing inputs zero."""
    if kind == "3_2":
        return reduce_dadda(nl, cols)
    n = len(cols)
    k = CELL_INPUTS[kind]
    least = CELL_OUTPUTS[kind] + 1 if terminal else k
    h = max((len(c) for c in cols), default=0)
    for d in _dadda_targets(h):
        new = [[] for _ in range(n + 4)]
        for c in range(n):
            bits = cols[c] + new[c]
            new[c] = []
            while len(bits) > d:
                excess = len(bits) - d
                if len(bits) >= least and (terminal or excess >= k - 1):
                    x = [bits.pop(0) for _ in range(min(k, len(bits)))]
                    x += ["1'b0"] * (k - len(x))
                    for off, bit in _cell(nl, kind, x):
                        if off == 0:
                            bits.append(bit)
                        elif c + off < n:
                            new[c + off].append(bit)
                elif excess >= 2 and len(bits) >= 3:
                    sm, co = nl.fa(bits.pop(0), bits.pop(0), bits.pop(0))
                    bits.append(sm)
                    if c + 1 < n:
                        new[c + 1].append(co)
                else:
                    sm, co = nl.ha(bits.pop(0), bits.pop(0))
                    bits.append(sm)
                    if c + 1 < n:
                        new[c + 1].append(co)
            new[c] = bits
        cols = new[:n]
    return cols


def _rows_of(cols: list) -> list:
    """The columns as rows (row r holds bit r of every column, None where a column is short)."""
    h = max((len(c) for c in cols), default=0)
    return [[(c[r] if r < len(c) else None) for c in cols] for r in range(h)]


def _cols_of(rows: list, n: int) -> list:
    cols = _cols(n)
    for row in rows:
        for c, bit in enumerate(row[:n]):
            if bit is not None:
                cols[c].append(bit)
    return cols


def reduce_tiled(nl: Netlist, cols: list, pins: dict, prefix: str) -> list:
    """The tiled CPA reduction: rows added pairwise per level by K-bit
    tiles of the tile_adder slot's family; a tile's carry-out becomes a
    bit of a carry row (extra_counter_row: the row joins the next level;
    staggered_tiling: the same, the next level's tiles offset by K/2 so
    the carries land inside a tile; terminal_compressor: the carry rows
    are held for the end); the last rows close through the terminal
    cell (a 3:2 counter tree, 4:2 or 9:2 compressors) into two rows.
    adder_width full_width is the binary tree of full-width adders."""
    n = len(cols)
    aw = str(_pin(pins, f"{prefix}.adder_width", 4))
    assim = str(_pin(pins, f"{prefix}.carry_assimilation", "extra_counter_row"))
    term = str(_pin(pins, f"{prefix}.terminal_reduction", "3_2_counter"))
    tfam = str(_pin(pins, f"{prefix}.tile_adder.family", "ripple_carry"))
    tpins = _sub(pins, f"{prefix}.tile_adder.")
    K = n if aw == "full_width" else max(2, int(aw))
    rows = _rows_of(cols)
    held: list = []
    level = 0
    t = 0
    while len(rows) > 3:
        offset = (K // 2) if (assim == "staggered_tiling" and level % 2 == 1 and K < n) else 0
        nxt = []
        carries = []
        for r in range(0, len(rows) - 1, 2):
            ra, rb = rows[r], rows[r + 1]
            srow = [None] * n
            crow = [None] * n
            lo = 0
            first = True
            while lo < n:
                hi = min(n, (offset if first and offset else lo + K))
                if hi <= lo:
                    hi = min(n, lo + K)
                first = False
                span = range(lo, hi)
                if all(ra[c] is None and rb[c] is None for c in span):
                    lo = hi
                    continue
                if all(rb[c] is None for c in span) or all(ra[c] is None for c in span):
                    # one row is empty over the tile: the other passes through
                    src = ra if all(rb[c] is None for c in span) else rb
                    for c in span:
                        srow[c] = src[c]
                    lo = hi
                    continue
                width = hi - lo
                a = "{" + ", ".join((ra[c] or "1'b0") for c in reversed(span)) + "}"
                b = "{" + ", ".join((rb[c] or "1'b0") for c in reversed(span)) + "}"
                t += 1
                s, co = f"ts{t}", f"tc{t}"
                nl.adder(tfam, tpins, width, a, b, "1'b0", s, co, f"tile {t} ({tfam}, {width} bits) at level {level}")
                d = max([nl.t(ra[c] or "1'b0") for c in span] + [nl.t(rb[c] or "1'b0") for c in span]) + 1
                for i, c in enumerate(span):
                    # Netlist.adder declares a one-bit sum as a scalar, which cannot be indexed;
                    # `staggered_tiling` opens every odd level with a tile adder_width // 2 wide,
                    # one bit when adder_width is 2 or 3
                    srow[c] = f"{s}[{i}]" if width > 1 else s
                    nl.arrival[f"{s}"] = d
                if hi < n:
                    crow[hi] = co
                    nl.arrival[co] = d
                lo = hi
            nxt.append(srow)
            if any(x is not None for x in crow):
                carries.append(crow)
        if len(rows) % 2:
            nxt.append(rows[-1])
        if assim == "terminal_compressor":
            held += carries
            rows = nxt
        else:
            rows = nxt + carries
        level += 1
    rows = rows + held
    cols2 = _cols_of(rows, n)
    cell = {"3_2_counter": "3_2", "compressor_4_2": "4_2", "compressor_9_2": "9_2"}[term]
    return reduce_cells(nl, cols2, cell, terminal=True)


def reduce_family(nl: Netlist, cols: list, pins: dict, prefix: str) -> list:
    """The reduction the slot at `prefix` names: csa_reduction_tree
    (geometry, counter_kind), compressor_4_2_tree (compressor_kind) or
    tiled_cpa_reduction_tree."""
    fam = str(_pin(pins, f"{prefix}.family", "csa_reduction_tree"))
    if fam == "compressor_4_2_tree":
        kind = str(_pin(pins, f"{prefix}.compressor_kind", "4_2"))
        if kind not in COMPRESSORS:
            raise ValueError(f"compressor_kind {kind!r}")
        return reduce_cells(nl, cols, kind)
    if fam == "tiled_cpa_reduction_tree":
        return reduce_tiled(nl, cols, pins, prefix)
    if fam != "csa_reduction_tree":
        raise ValueError(f"no reduction module for the family {fam!r}")
    geometry = str(_pin(pins, f"{prefix}.geometry", "dadda"))
    counter = str(_pin(pins, f"{prefix}.counter_kind", "3_2"))
    if geometry not in GEOMETRIES:
        raise ValueError(f"geometry {geometry!r}")
    if counter not in COUNTERS:
        raise ValueError(f"counter_kind {counter!r}")
    if counter != "3_2":
        # a wider counter: the cell reduction (the geometry orders the bits by arrival first)
        if geometry in ("balanced_delay", "tdm_arrival_driven"):
            cols = [sorted(c, key=nl.t) for c in cols]
        return reduce_cells(nl, cols, counter)
    if geometry == "wallace":
        return reduce_wallace(nl, cols)
    if geometry == "reduced_area":
        return reduce_wallace(nl, cols, half_adders=False)
    if geometry == "balanced_delay":
        return reduce_by_arrival(nl, cols, tdm=False)
    if geometry == "tdm_arrival_driven":
        return reduce_by_arrival(nl, cols, tdm=True)
    return reduce_dadda(nl, cols)


def reduce(nl: Netlist, cols: list, geometry: str, counter: str) -> list:
    """The counter-tree reduction by geometry and counter (the callers
    outside the slot plumbing)."""
    return reduce_family(nl, cols, {"r.geometry": geometry, "r.counter_kind": counter}, "r")


def column_depths(nl: Netlist, cols: list) -> list:
    """The logic depth (full-adder levels) at which each column's two
    rows are ready: the arrival profile of the final adder."""
    depth: dict = {}
    for name, expr in nl.assigns:
        deps = [d for d in _idents(expr) if d in depth or d in nl.arrival]
        base = max((max(depth.get(d, 0), nl.arrival.get(d, 0)) for d in deps), default=0)
        depth[name] = max(base + (1 if name.startswith("t") else 0), nl.arrival.get(name, 0))

    def at(b):
        base = b.split("[")[0]
        return max(depth.get(base, 0), nl.arrival.get(base, 0))
    return [max((at(b) for b in c), default=0) for c in cols]


# ---- the final adder --------------------------------------------------------------
HYBRID_MIX = {"ripple_then_select": ("ripple", "select"), "ripple_cla_select": ("ripple", "cla", "select"),
              "uniform_cla": ("cla",), "ripple_skip": ("ripple", "skip"), "ripple_skip_select": ("ripple", "skip", "select"),
              "vba_select_cla_select_vba": ("vba", "select", "cla", "select", "vba")}
HYBRID_KIND = {"ripple": ("ripple_carry", {}), "select": ("carry_select", {}), "cla": ("carry_lookahead", {"group_size": 4}),
               "skip": ("carry_skip", {}), "vba": ("carry_skip", {"block_sizing": "trapezoidal_variable"})}


def hybrid_final_add(nl: Netlist, cols: list, pins: dict, prefix: str) -> tuple:
    """The arrival-driven hybrid final adder: the columns cut into
    region_count regions by the arrival profile (measured from the tree,
    or uniform), the boundaries at the profile's crossings of evenly
    spaced thresholds or at equal widths, each region an adder of the
    mix's kind with the previous region's carry-out as its carry-in."""
    n = len(cols)
    R = max(2, min(4, _ipin(pins, f"{prefix}.region_count", 3)))
    mix = HYBRID_MIX.get(str(_pin(pins, f"{prefix}.region_adder_mix", "ripple_cla_select")))
    if mix is None:
        raise ValueError("region_adder_mix")
    model = str(_pin(pins, f"{prefix}.arrival_model", "measured_tree_profile"))
    search = str(_pin(pins, f"{prefix}.boundary_search", "arrival_profile_intersection"))
    prof = column_depths(nl, cols) if model == "measured_tree_profile" else [0] * n
    bounds = []
    if search == "arrival_profile_intersection" and max(prof) > min(prof):
        lo, hi = min(prof), max(prof)
        for k in range(1, R):
            th = lo + (hi - lo) * k / R
            b = next((i for i, v in enumerate(prof) if v >= th), None)
            if b is not None and b > (bounds[-1] if bounds else 0) and b < n:
                bounds.append(b)
    if not bounds:
        bounds = [n * k // R for k in range(1, R)]
    bounds = sorted(set(b for b in bounds if 0 < b < n))
    edges = [0] + bounds + [n]
    kinds = [mix[min(i, len(mix) - 1)] for i in range(len(edges) - 1)]
    row_s = [c[0] if len(c) > 0 else "1'b0" for c in cols]
    row_c = [c[1] if len(c) > 1 else "1'b0" for c in cols]
    lines = [f"  logic [{n-1}:0] row_s, row_c;",
             "  assign row_s = {" + ", ".join(reversed(row_s)) + "};",
             "  assign row_c = {" + ", ".join(reversed(row_c)) + "};",
             f"  // hybrid final adder: regions {edges} of kinds {kinds} on the {model} profile ({search})"]
    cin = "1'b0"
    extra = []
    notes = []
    from .binary_cpa import adder_module
    from .selection import SelectionError
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        w = hi - lo
        fam, fpins = HYBRID_KIND[kinds[i]]
        # the arrival profile cuts regions of two or three bits: a lookahead group is at most the region wide,
        # and a region narrower than its family's smallest block (carry_select below 3 bits) is a ripple
        if fam == "carry_lookahead" and w < 2:
            fam, fpins = "ripple_carry", {}
        if fam == "carry_lookahead" and w < fpins.get("group_size", 4):
            # A one-bit region has no legal selectable CLA group. Its
            # implicit default naturally constructs the one-bit tail.
            fpins = dict(fpins, group_size=w) if w >= 2 else {}
        m = None
        try:
            m = adder_module(fam, fpins, w)
        except SelectionError:
            m = None
        if m is None and fam != "ripple_carry":
            notes.append(f"region {i} ({w} bits) is too narrow for {fam}: ripple")
            fam, fpins = "ripple_carry", {}
            m = adder_module(fam, fpins, w)
        if m is None:
            raise ValueError(f"hybrid region adder {fam!r} at {w} bits")
        if m.text:
            extra.append(m.text)
        ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
        co = f"rg{i}_co"
        lines.append(f"  logic {co};")
        lines.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u_rg{i} (.a(row_s[{hi-1}:{lo}]), .b(row_c[{hi-1}:{lo}]), .cin({cin}), .s(p[{hi-1}:{lo}]), .cout({co}));")
        cin = co
    return lines, "".join(extra)


def final_add(nl: Netlist, cols: list, pins: dict, prefix: str) -> tuple:
    """(lines, extra module text): p = the sum of the two rows through the
    final_cpa slot at `prefix`: the adder library module of the
    `<prefix>.adder.family` choice under `uniform` (any cpa family), or
    the arrival-driven hybrid of regions under `hybrid_arrival_driven`."""
    from .binary_cpa import adder_module
    cpa_family = str(_pin(pins, f"{prefix}.family", "uniform"))
    if cpa_family == "hybrid_arrival_driven":
        return hybrid_final_add(nl, cols, pins, prefix)
    n = len(cols)
    row_s = [c[0] if len(c) > 0 else "1'b0" for c in cols]
    row_c = [c[1] if len(c) > 1 else "1'b0" for c in cols]
    lines = [f"  logic [{n-1}:0] row_s, row_c;",
             "  assign row_s = {" + ", ".join(reversed(row_s)) + "};",
             "  assign row_c = {" + ", ".join(reversed(row_c)) + "};"]
    adder_family = str(_pin(pins, f"{prefix}.adder.family", "parallel_prefix"))
    adder_pins = _sub(pins, f"{prefix}.adder.")
    m = adder_module(adder_family, adder_pins, n)
    if m is None:
        raise ValueError(f"the final adder family {adder_family!r} has no library module")
    ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
    lines.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + "u_cpa (.a(row_s), .b(row_c), .cin(1'b0), .s(p), .cout());")
    return lines, m.text or ""


# ---- the modules --------------------------------------------------------------------
def _reduce_pezaris(nl: Netlist, w: int, signed: bool) -> list:
    """The carry-save array with Pezaris' negative-weight cells: the
    products with one sign bit enter at weight -1, every cell keeps its
    sum at weight +-1 and its carry at weight +-2 (the carry takes the
    sign of the majority of its inputs, an input of the other sign
    entering complemented), and the final negative bits are complemented
    with a folded constant so the rows the final adder sees are positive."""
    n = 2 * w

    def cell(ins: list) -> tuple:
        """ins: [(bit, negative?)] (two or three); ((sum bit, sum negative?), (carry bit, carry negative?))."""
        if len(ins) == 2 and ins[0][1] == ins[1][1]:
            sm, co = nl.ha(ins[0][0], ins[1][0])
            return (sm, ins[0][1]), (co, ins[0][1])
        while len(ins) < 3:
            ins = ins + [("1'b0", False)]
        negs = sum(1 for _, sg in ins if sg)
        cneg = negs >= 2
        sneg = negs % 2 == 1
        x, y, z = [(b if sg == cneg else nl.wire(f"~{b}", "pz")) for b, sg in ins]
        sm = nl.wire(f"{ins[0][0]} ^ {ins[1][0]} ^ {ins[2][0]}")
        co = nl.wire(f"({x} & {y}) | ({x} & {z}) | ({y} & {z})")
        nl.fa_count += 1
        return (sm, sneg), (co, cneg)

    acc_s = [None] * n
    acc_c = [None] * n
    for i in range(w):
        new_c = [None] * n
        for c in range(n):
            ins = [v for v in (acc_s[c], acc_c[c]) if v is not None]
            j = c - i
            if 0 <= j < w:
                negw = signed and ((i == w - 1) != (j == w - 1))
                ins.append((nl.wire(f"a[{i}] & b[{j}]", "pp"), negw))
            if not ins:
                acc_s[c] = None
                continue
            if len(ins) == 1:
                acc_s[c] = ins[0]
                continue
            sv, cv = cell(ins)
            acc_s[c] = sv
            if c + 1 < n:
                new_c[c + 1] = cv
        acc_c = new_c
    cols = _cols(n)
    const = 0
    for c in range(n):
        for v in (acc_s[c], acc_c[c]):
            if v is None:
                continue
            bit, neg = v
            if neg:
                cols[c].append(nl.wire(f"~{bit}", "pz"))
                const -= 1 << c
            else:
                cols[c].append(bit)
    _add_const(cols, const)
    return cols


def reduce_array(nl: Netlist, cols: list) -> list:
    """The carry-save array: the rows (one bit per column each) added
    one after another into a sum and a carry vector."""
    n = len(cols)
    rows = max((len(c) for c in cols), default=0)
    acc_s = [None] * n
    acc_c = [None] * n
    for r in range(rows):
        new_c = [None] * n
        for c in range(n):
            ins = [x for x in (acc_s[c], acc_c[c], cols[c][r] if r < len(cols[c]) else None) if x is not None]
            if len(ins) == 3:
                s, co = nl.fa(*ins)
            elif len(ins) == 2:
                s, co = nl.ha(*ins)
            elif len(ins) == 1:
                s, co = ins[0], None
            else:
                s, co = None, None
            acc_s[c] = s
            if co is not None and c + 1 < n:
                new_c[c + 1] = co
        acc_c = new_c
    return [[x for x in (acc_s[c], acc_c[c]) if x is not None] for c in range(n)]


def tree_multiplier_sv(w: int, signed: bool, family: str, pins: dict, name: str) -> tuple:
    """(text, summary) of direct_pp_parallel, booth_recoded_parallel or
    carry_save_array at a width."""
    nl = Netlist()
    if family == "booth_recoded_parallel":
        radix = _ipin(pins, "booth_radix", 4)
        if radix not in (4, 8, 16):
            raise ValueError(f"booth radix {radix} has no module (4, 8 and 16 do)")
        cols = pp_booth(nl, w, signed, radix, pins)
        red_prefix = "reduction"
    elif family == "direct_pp_parallel":
        gb = _ipin(pins, "group_bits", 1)
        scheme = str(_pin(pins, "signed_scheme", "baugh_wooley"))
        if gb == 2:
            cols = pp_groups2(nl, w, signed, pins)
        elif signed and scheme == "sign_extension":
            cols = pp_sign_extended_rows(nl, w, signed)
        else:
            cols = pp_and_array(nl, w, signed)
        red_prefix = "reduction"
    elif family == "carry_save_array":
        scheme = str(_pin(pins, "signed_scheme", "baugh_wooley"))
        if signed and scheme == "pezaris_negative_weight":
            cols = None
        else:
            cols = pp_and_array(nl, w, signed)
        red_prefix = None
    else:
        raise ValueError(f"no tree module for {family}")
    if red_prefix is None:
        pp_bits = 0
        if cols is None:
            cols = _reduce_pezaris(nl, w, signed)
            cols = reduce_dadda(nl, cols) if max(len(c) for c in cols) > 2 else cols
        else:
            pp_bits = sum(len(c) for c in cols)
            cols = reduce_array(nl, cols)
        cpa_prefix = "cpa"
    else:
        pp_bits = sum(len(c) for c in cols)
        cols = reduce_family(nl, cols, pins, red_prefix)
        cpa_prefix = f"{red_prefix}.cpa"
    depth = max(column_depths(nl, cols), default=0)
    add_lines, add_text = final_add(nl, cols, pins, cpa_prefix)
    summary = {"pp_bits": pp_bits, "full_adders": nl.fa_count, "half_adders": nl.ha_count, "cells": nl.cell_count, "tree_depth": depth}
    text = [f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);",
            f"  // {family}: {summary}"]
    text += nl.render()
    text += add_lines
    text.append("endmodule")
    extra = "".join(nl.extra) + (add_text or "")
    return "\n".join(text) + "\n" + (extra + "\n" if extra else ""), summary


def karatsuba_sv(w: int, signed: bool, pins: dict, name: str) -> tuple:
    """(text, summary): a = a_h 2^m + a_l; p = a_h b_h 2^2m + ((a_h + a_l)(b_h + b_l)
    - a_h b_h - a_l b_l) 2^m + a_l b_l with the high parts signed for two's
    complement operands (the high product signed, the low one unsigned,
    the middle one signed over m + 2 bits), or the three-way split with
    six products; the base products are library tree multipliers (the
    base_multiplier family with the reduction pins), recursively to
    `recursion_depth`; the pre-adds, the middle terms and the
    recombination go through the adder slot."""
    depth = _ipin(pins, "recursion_depth", 1)
    base_fam = str(_pin(pins, "base_multiplier", "direct_tree"))
    split = str(_pin(pins, "split_kind", "two_way"))
    afam = str(_pin(pins, "adder.family", "ripple_carry"))
    apins = _sub(pins, "adder.")
    fam = {"array": "carry_save_array", "booth_tree": "booth_recoded_parallel", "direct_tree": "direct_pp_parallel"}.get(base_fam)
    if fam is None:
        raise ValueError(f"base_multiplier {base_fam!r}")
    parts = []
    nl = Netlist()
    from chialu.targets.rtl import families as FAM

    def base(width: int, sgn: bool, tag: str) -> str:
        sub = {k: v for k, v in pins.items() if k.startswith("reduction.")}
        if depth > 1 and width >= 8:
            sub_pins = dict(pins, recursion_depth=depth - 1)
            n0 = f"{name}_{tag}_k{width}{'s' if sgn else 'u'}"
            text, _ = karatsuba_sv(width, sgn, sub_pins, n0)
            parts.append(text)
            return n0
        n0 = f"{name}_{tag}_b{width}{'s' if sgn else 'u'}"
        text, _ = tree_multiplier_sv(width, sgn, fam, dict(sub, **({"booth_radix": 4} if fam == "booth_recoded_parallel" else {})), n0)
        parts.append(text)
        return n0

    def add(x: str, y: str, width: int, out: str, comment: str, sub: bool = False) -> str:
        """out (width bits) = x + y (or x - y) through the adder slot."""
        if sub:
            nl.assigns.append((f"{out}_ny", f"~{y}"))
            nl.widths[f"{out}_ny"] = width
            y = f"{out}_ny"
        nl.adder(afam, apins, width, x, y, "1'b1" if sub else "1'b0", out, f"{out}_co", comment)
        return out

    def sext(v: str, frm: int, to: int, sgn: bool) -> str:
        if to == frm:
            return v
        return f"{{{{{to - frm}{{{v}[{frm-1}]}}}}, {v}}}" if sgn else f"{{{{{to - frm}{{1'b0}}}}, {v}}}"

    L = [f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);"]
    PW = 2 * w
    if split == "three_way":
        m = (w + 2) // 3
        hi = w - 2 * m
        if hi < 1:
            raise ValueError("three_way needs 3 bits or more")
        summary = {"split": m, "depth": depth, "products": 6}
        L.append(f"  // recursive_karatsuba (three_way): {summary}")
        # the parts: a0, a1 (m bits, unsigned), a2 (hi bits, signed for two's complement)
        L += [f"  logic [{m-1}:0] a0, b0, a1, b1; logic [{hi-1}:0] a2, b2;",
              f"  assign a0 = a[{m-1}:0]; assign b0 = b[{m-1}:0]; assign a1 = a[{2*m-1}:{m}]; assign b1 = b[{2*m-1}:{m}];",
              f"  assign a2 = a[{w-1}:{2*m}]; assign b2 = b[{w-1}:{2*m}];"]
        # the pair sums: (a0 + a1) unsigned m+1 bits; (a0 + a2), (a1 + a2) signed over m+2 bits
        s01 = add("{1'b0, a0}", "{1'b0, a1}", m + 1, "s01", "a0 + a1")
        t01 = add("{1'b0, b0}", "{1'b0, b1}", m + 1, "t01", "b0 + b1")
        m2 = max(m, hi) + 2
        s02 = add(sext("a0", m, m2, False), sext("a2", hi, m2, signed), m2, "s02", "a0 + a2")
        t02 = add(sext("b0", m, m2, False), sext("b2", hi, m2, signed), m2, "t02", "b0 + b2")
        s12 = add(sext("a1", m, m2, False), sext("a2", hi, m2, signed), m2, "s12", "a1 + a2")
        t12 = add(sext("b1", m, m2, False), sext("b2", hi, m2, signed), m2, "t12", "b1 + b2")
        d0 = base(m, False, "d0")
        d1 = base(m, False, "d1")
        d2 = base(hi, signed, "d2")
        d01 = base(m + 1, False, "d01")
        d02 = base(m2, signed, "d02")
        d12 = base(m2, signed, "d12")
        L += [f"  logic [{2*m-1}:0] pd0, pd1; logic [{2*hi-1}:0] pd2; logic [{2*m+1}:0] pd01; logic [{2*m2-1}:0] pd02, pd12;",
              f"  {d0} u_d0 (.a(a0), .b(b0), .p(pd0));", f"  {d1} u_d1 (.a(a1), .b(b1), .p(pd1));",
              f"  {d2} u_d2 (.a(a2), .b(b2), .p(pd2));",
              f"  {d01} u_d01 (.a(s01), .b(t01), .p(pd01));",
              f"  {d02} u_d02 (.a(s02), .b(t02), .p(pd02));", f"  {d12} u_d12 (.a(s12), .b(t12), .p(pd12));"]
        # the terms at the product width: c1 = d01 - d0 - d1, c2 = d02 - d0 - d2 + d1, c3 = d12 - d1 - d2
        e = lambda v, frm, sgn: sext(v, frm, PW, sgn)  # noqa: E731
        x = add(e("pd01", 2 * m + 2, False), e("pd0", 2 * m, False), PW, "c1a", "d01 - d0", sub=True)
        c1 = add("c1a", e("pd1", 2 * m, False), PW, "c1", "- d1", sub=True)
        x = add(e("pd02", 2 * m2, True), e("pd0", 2 * m, False), PW, "c2a", "d02 - d0", sub=True)
        x = add("c2a", e("pd2", 2 * hi, signed), PW, "c2b", "- d2", sub=True)
        c2 = add("c2b", e("pd1", 2 * m, False), PW, "c2", "+ d1")
        x = add(e("pd12", 2 * m2, True), e("pd1", 2 * m, False), PW, "c3a", "d12 - d1", sub=True)
        c3 = add("c3a", e("pd2", 2 * hi, signed), PW, "c3", "- d2", sub=True)
        # p = d0 + c1 x + c2 x^2 + c3 x^3 + d2 x^4
        L.append(f"  logic [{PW-1}:0] w1, w2, w3, w4;")
        L.append(f"  assign w1 = c1 << {m}; assign w2 = c2 << {2*m}; assign w3 = c3 << {3*m}; assign w4 = {e('pd2', 2*hi, signed)} << {4*m};")
        r1 = add(e("pd0", 2 * m, False), "w1", PW, "r1", "d0 + c1 x")
        r2 = add("r1", "w2", PW, "r2", "+ c2 x^2")
        r3 = add("r2", "w3", PW, "r3", "+ c3 x^3")
        add("r3", "w4", PW, "r4", "+ d2 x^4")
        L.append("  assign p = r4;")
    else:
        m = (w + 1) // 2 if split == "two_way" else max(2, w // 3)
        hi = w - m
        summary = {"split": m, "depth": depth, "products": 3, "split_kind": split}
        L.append(f"  // recursive_karatsuba ({split}): {summary}")
        L += [f"  logic [{m-1}:0] al, bl; logic [{hi-1}:0] ah, bh;",
              f"  assign al = a[{m-1}:0]; assign bl = b[{m-1}:0]; assign ah = a[{w-1}:{m}]; assign bh = b[{w-1}:{m}];"]
        mm = max(m, hi) + 2
        asum = add(sext("al", m, mm, False), sext("ah", hi, mm, signed), mm, "asum", "a_h + a_l")
        bsum = add(sext("bl", m, mm, False), sext("bh", hi, mm, signed), mm, "bsum", "b_h + b_l")
        m_hh = base(hi, signed, "hh")
        m_ll = base(m, False, "ll")
        m_mm = base(mm, signed, "mm")
        L += [f"  logic [{2*hi-1}:0] phh; logic [{2*m-1}:0] pll; logic [{2*mm-1}:0] pmm;",
              f"  {m_hh} u_hh (.a(ah), .b(bh), .p(phh));",
              f"  {m_ll} u_ll (.a(al), .b(bl), .p(pll));",
              f"  {m_mm} u_mm (.a(asum), .b(bsum), .p(pmm));"]
        e = lambda v, frm, sgn: sext(v, frm, PW, sgn)  # noqa: E731
        x = add(e("pmm", 2 * mm, True), e("phh", 2 * hi, signed), PW, "mida", "pmm - phh", sub=True)
        mid = add("mida", e("pll", 2 * m, False), PW, "mid", "- pll", sub=True)
        L.append(f"  logic [{PW-1}:0] wh, wm;")
        L.append(f"  assign wh = {e('phh', 2*hi, signed)} << {2*m}; assign wm = mid << {m};")
        r1 = add(e("pll", 2 * m, False), "wm", PW, "r1", "pll + mid x")
        add("r1", "wh", PW, "r2", "+ phh x^2")
        L.append("  assign p = r2;")
    # The netlist's instances read the split parts and the base products that L declares (a0, al,
    # pd01, wh), and L's instances read the netlist's sums (s01, asum), so neither order of the two
    # blocks declares everything before its first use -- and yosys-slang, unlike Verilator, refuses
    # a use before the declaration. L's declarations go first, then the netlist, then the rest of L.
    body = nl.render()
    head = L[1:2] if len(L) > 1 and L[1].lstrip().startswith("//") else []    # the summary comment
    tail = L[1 + len(head):]
    decls = [l for l in tail if l.lstrip().startswith("logic ")]
    rest = [l for l in tail if not l.lstrip().startswith("logic ")]
    L = L[:1] + head + decls + body + rest
    L.append("endmodule")
    return "\n".join(L) + "\n" + "".join(nl.extra) + "\n".join(parts), summary


def dedupe_modules(text: str) -> str:
    """Strict module identity shared by every generator collection path."""
    from .module_library import dedupe_modules as collect
    return collect(text)


def mul_sv(w: int, signed: bool, family: str, pins: dict, name: str | None = None) -> tuple:
    """(module name, text, summary) of a multiplier family at a width."""
    pins = pins or {}
    tag = ("s" if signed else "u") + _tag(pins)
    if family == "recursive_karatsuba":
        if w < 4:
            raise ValueError("karatsuba needs 4 bits or more")
        name = name or f"fam_mul_karatsuba_d{_pin(pins, 'recursion_depth', 1)}_w{w}_{tag}"
        text, summ = karatsuba_sv(w, signed, pins, name)
        return name, dedupe_modules(text), summ
    if family in TREE_FAMILIES:
        if family == "carry_save_array":
            var = "array"
        else:
            geometry = str(_pin(pins, "reduction.geometry", "dadda"))
            counter = str(_pin(pins, "reduction.counter_kind", "3_2"))
            var = f"{'booth' + str(_pin(pins, 'booth_radix', 4)) if family == 'booth_recoded_parallel' else 'direct'}_{geometry}_{counter}"
        name = name or f"fam_mul_{var}_w{w}_{tag}"
        text, summ = tree_multiplier_sv(w, signed, family, pins, name)
        return name, dedupe_modules(text), summ
    raise ValueError(f"no module for the multiplier family {family}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--family", default="direct_pp_parallel")
    ap.add_argument("--pins", default="", help="key=value,... (reduction.geometry=dadda, booth_radix=4, ...)")
    ap.add_argument("--signed", action="store_true")
    ap.add_argument("--sv", default=None)
    args = ap.parse_args(argv)
    pins = dict(kv.split("=", 1) for kv in args.pins.split(",") if "=" in kv)
    try:
        name, text, summ = mul_sv(args.width, args.signed, args.family, pins)
    except ValueError as e:
        print(f"mul: {e}", file=sys.stderr)
        return 2
    if args.sv:
        open(args.sv, "w").write(text)
        print(f"{name}: {summ}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
