"""Decimal (packed BCD 8421) families as combinational modules: the
adders, the parallel multiplier and the dividers of a BCD mode.

Every adder computes s = (a + b + cin) mod 10^D with cout the decimal
carry out, or under `sub` s = (a - b - cin) mod 10^D with cout = 1 when
no borrow leaves (the tens' complement convention: the ALU's carry flag
of a subtraction is ~cout):

    module fam_bcd_add_<family>_..._d<D> (input [4D-1:0] a, input [4D-1:0] b, input sub, input cin,
                                          output [4D-1:0] s, output cout);
    module fam_bcd_mul_..._d<D>          (input [4D-1:0] a, input [4D-1:0] b, output [8D-1:0] p);
    module fam_bcd_div_..._d<D>          (input [4D-1:0] a, input [4D-1:0] b, output [4D-1:0] q, output [4D-1:0] r);

The families:

* bcd_direct_addition: 4-bit digit adders (the `digit_adder` component
  from the binary adder library) with the +6 correction before or after
  the digit sum or a decimal carry computed from the digit's own
  generate and propagate (`correction_placement`), the carries rippled,
  looked ahead per 4-digit group or over the whole word (`carry_scheme`),
  the digits in BCD 8421 or excess-3 (`digit_code`: excess-3 complements
  by bit inversion), the subtraction by the tens' complement, by the
  nines' complement with the end-around carry (its increment and the
  tens' complement correction of a negative difference coincide under
  the modular contract) or by a separate borrow chain (`subtraction`),
  and the complement digits by 9 - d, by the digitwise bit formula or by
  the trailing-zero scan that yields the tens' complement directly
  (`complement_generation`).
* speculative_decimal_addition: +6 speculated on every digit of one
  operand, one binary carry network over the whole word (the
  `carry_network` component), the digits corrected after the sum or
  both candidates of every digit selected by its carry
  (`recovery`); with the rounding increment as the speculation target
  the sum and the incremented sum come from a compound adder and the
  carry-in selects.
* redundant_decimal_addition: the operands recoded into a redundant
  digit set (Svoboda's -6..6, RBCD -7..7, the maximally redundant
  -9..9, or the overloaded 0..15), one carry-free two-step addition
  (interim digit and transfer), and the final conversion to BCD by a
  carry-propagate borrow adder or by the two-candidate digit select
  over a borrow prefix (the on-the-fly Q/QM pair evaluated in parallel).
* decimal_multioperand_addition: the two operands and the carry-in
  word as three operands through one decimal 3:2 level with the
  correction per level or at the root, or through binary column
  counters converted at the root, or decimal 4:2 compressors, or
  binary compressors on digits recoded to 4221 with the carry word
  doubled through the 5211 code; the root adder is a decimal
  carry-propagate adder over the `root_adder` family.
* parallel_decimal_multiplication: all partial products at once from
  the multiplicand's multiples (doubling and quintupling are digitwise
  and carry-free, 3x by one addition), the multiplier digits as they are
  (multiples 1x to 9x), recoded to signed digits -5..5 or split into a
  radix-5 and a radix-2 part (`multiplier_recoding`), the rows summed
  in BCD 8421 by decimal carry-save adders, in 4221 or 5211 by binary
  compressors with the carry word doubled by the code switch, in
  excess-3 with overloaded digits or as signed digits -8..8 with
  posibit/negabit weights (`internal_digit_code`), then one decimal
  carry-propagate adder (`final_adder`).
* decimal_digit_recurrence: one radix-10 quotient digit per unrolled
  stage: the nonredundant digits by comparison against the divisor's
  multiples (split into a radix-2 and a radix-5 comparison under
  `digit_split`), the redundant sets -5..5 and -7..7 by rounding the
  residual estimate after the divisor is prescaled near one (a factor
  from its leading digits), the signed quotient digits converted at the
  end and the remainder from the back-multiplied quotient.
* decimal_newton: the reciprocal seed from a table over the normalized
  divisor's leading digits (`seed_digits`, capped at three), the
  iterations x(2 - bx) on decimal multipliers with their count sized by
  the seed's error bound, the quotient estimate a*x and the remainder
  a - q*b with the back-multiply correction (`final_round`).

    python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind adder --family bcd_direct_addition --pins carry_scheme=full_lookahead
"""
from __future__ import annotations

import argparse
import sys
from fractions import Fraction

DECIMAL_FAMILIES = {"adder": ("bcd_direct_addition", "speculative_decimal_addition", "redundant_decimal_addition",
                              "decimal_multioperand_addition"),
                    "multiplier": ("parallel_decimal_multiplication",),
                    "divider": ("decimal_digit_recurrence", "decimal_newton")}
# the 4221 and 5211 codes of the digits 0..9 (one code word per digit)
CODE_4221 = (0b0000, 0b0001, 0b0010, 0b0011, 0b1000, 0b1001, 0b1100, 0b1101, 0b1110, 0b1111)
CODE_5211 = (0b0000, 0b0001, 0b0011, 0b0101, 0b0111, 0b1000, 0b1001, 0b1011, 0b1101, 0b1111)
W_4221 = (4, 2, 2, 1)
W_5211 = (5, 2, 1, 1)


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
    if isinstance(v, str):
        return v.lower() in ("1", "true", "yes")
    return bool(v)


def _sub_pins(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _ptag(pins: dict) -> str:
    """A 48-bit tag of the pins for the module name (empty without pins)."""
    if not pins:
        return ""
    import hashlib
    return "_" + hashlib.blake2b(repr(sorted((str(k), str(v)) for k, v in pins.items())).encode(), digest_size=6).hexdigest()


def _sfx(v) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(v))


def dig(x: str, i: int) -> str:
    """Digit i of a packed BCD word."""
    return f"{x}[{4*i+3}:{4*i}]"


def bcd_const(value: int, D: int) -> str:
    """A D-digit BCD literal of a nonnegative value below 10^D."""
    v = 0
    for i in range(D):
        v |= (value % 10) << (4 * i)
        value //= 10
    return f"{4*D}'h{v:0{D}x}"


class Mod:
    """A module under construction: ports, declarations, body lines,
    the texts of the library modules it instantiates."""

    def __init__(self, name: str, comment: str):
        self.name, self.comment = name, comment
        self.ports: list = []
        self.lines: list = []
        self.extra: list = []
        self.tables: set = set()
        self.fns: set = set()
        self.n = 0
        self.k = 0

    def port(self, direction: str, name: str, width: int = 1):
        w = f"[{width-1}:0] " if width > 1 else ""
        self.ports.append(f"{direction} logic {w}{name}")

    def wire(self, name: str, width: int = 1, signed: bool = False, expr: str | None = None) -> str:
        w = f"[{width-1}:0] " if width > 1 else ""
        self.lines.append(f"  logic {'signed ' if signed else ''}{w}{name};" + (f" assign {name} = {expr};" if expr is not None else ""))
        return name

    def fresh(self, base: str) -> str:
        self.k += 1
        return f"{base}_{self.k}"

    def assign(self, lhs: str, expr: str):
        self.lines.append(f"  assign {lhs} = {expr};")

    def raw(self, text: str):
        self.lines.append(text)

    def comment_line(self, text: str):
        self.lines.append(f"  // {text}")

    def lib(self, kind: str, family, pins: dict, width: int, conns: str, comment: str) -> bool:
        """Instantiate a library module of a kind; False (nothing emitted)
        when no family is declared or the family has no module."""
        from chialu.targets.rtl import families as FAM
        if not family:
            return False
        m = None
        if kind == "adder":
            # Decimal correction consumes a binary digit sum and its carry.
            # Decode a selected modular CPA before applying that correction.
            from .binary_cpa import adder_module
            m = adder_module(family, pins, width)
        elif kind == "cmp":
            m = FAM.comparator_module(family, pins, width, False)
        if m is None:
            return False
        if m.text:
            self.extra.append(m.text)
        ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
        self.n += 1
        self.lines.append(f"  // {comment}")
        self.lines.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u{self.n} ({conns});")
        return True

    def add(self, fam, pins: dict, width: int, a: str, b: str, out: str, comment: str, cin: str = "1'b0") -> str:
        """out (width + 1 bits) = a + b + cin through the binary adder family or the operator."""
        self.wire(out, width + 1)
        if not self.lib("adder", fam, pins, width, f".a({a}), .b({b}), .cin({cin}), .s({out}[{width-1}:0]), .cout({out}[{width}])", comment):
            self.assign(out, f"{a} + {b} + {cin}")
        return out

    def table(self, name: str, entries: list, ew: int, comment: str):
        """A packed constant table of ew-bit entries (entry 0 at the low
        end), read as name[(index) * ew +: ew]."""
        ne = len(entries)
        val = 0
        for i, e in enumerate(entries):
            val |= (int(e) & ((1 << ew) - 1)) << (ew * i)
        digits = (ne * ew + 3) // 4
        self.tables.add(name)
        self.lines.append(f"  // {comment}: {ne} entries of {ew} bits")
        self.lines.append(f"  localparam [{ne*ew-1}:0] {name} = {ne*ew}'h{val:0{digits}x};")

    def rom(self, name: str, entries: list, ew: int, index: str, out: str, comment: str):
        """A packed constant table read at an index: out = entries[index]."""
        self.table(name, entries, ew, comment)
        self.wire(out, ew, expr=f"{name}[({index}) * {ew} +: {ew}]")

    def render(self) -> str:
        from chialu.targets.rtl.families.mul import dedupe_modules
        head = [f"// {self.comment}", f"module {self.name} (", ",\n".join("  " + p for p in self.ports), ");"]
        return "\n".join(head + self.lines + ["endmodule", ""]) + dedupe_modules("".join(self.extra))


# ---- digit-level pieces ----------------------------------------------------------------
def nines_digit(d: str, how: str) -> str:
    """9 - d of a BCD digit: by the subtraction (subtract_from_power) or
    by the digitwise bit formula (nines_digitwise_plus_one)."""
    if how == "nines_digitwise_plus_one":
        return f"{{~{d}[3] & ~{d}[2] & ~{d}[1], {d}[2] ^ {d}[1], {d}[1], ~{d}[0]}}"
    return f"(4'd9 - {d})"


def _complement(m: Mod, D: int, pins: dict, b: str, sub: str, cin: str, xs3: bool, eac: bool = False) -> tuple:
    """(bx, c0): the operand b as it enters the digit adders and the carry
    into the lowest digit: b itself for an addition (c0 = cin); for a
    subtraction its nines' complement with c0 = ~cin (tens' complement
    convention), or under trailing_zero_scan its tens' complement (the
    first nonzero digit complemented to 10 - d, the digits above to
    9 - d, the zeros below kept) with c0 = 0, the scan disabled by cin
    (a - b - 1 = a + nines(b)). In excess-3 the nines' complement is the
    bit inversion of the excess-3 digit. Under the end-around carry
    (`eac`) the +1 of a - b is no carry-in: the recirculated carry
    supplies it (c0 = 0 for a subtraction). The third value is the carry
    the complement itself produces: the tens' complement of zero is 10^D,
    which the scan cannot hold (1'b0 otherwise)."""
    how = str(_pin(pins, "complement_generation", "subtract_from_power"))
    bx = m.wire("bx", 4 * D)
    if xs3:
        # excess-3 digits: b + 3 per digit; the nines' complement is the bitwise inversion
        for i in range(D):
            x3 = m.wire(m.fresh("b3"), 4, expr=f"{dig(b, i)} + 4'd3")
            m.assign(dig(bx, i), f"{sub} ? ~{x3} : {x3}")
        c0 = m.wire("c0", 1, expr=f"{sub} ? ~{cin} : {cin}")
        return bx, c0, "1'b0"
    if how == "trailing_zero_scan":
        # nz_i: a nonzero digit below digit i (a prefix or over the digits); the scan runs only for a - b
        nz = m.wire("nz", D + 1)
        m.assign(f"{nz}[0]", "1'b0")
        for i in range(D):
            m.assign(f"{nz}[{i+1}]", f"{nz}[{i}] | ({dig(b, i)} != 4'd0)")
        scan = m.wire("scan", 1, expr=f"{sub} & ~{cin}")
        for i in range(D):
            n9 = nines_digit(dig(b, i), "subtract_from_power")
            ten = f"(4'd10 - {dig(b, i)})"
            m.assign(dig(bx, i), f"~{sub} ? {dig(b, i)} : (~{scan}) ? {n9} : {nz}[{i}] ? {n9} : ({dig(b, i)} == 4'd0) ? 4'd0 : {ten}")
        c0 = m.wire("c0", 1, expr=f"~{sub} & {cin}")
        cx = m.wire("cx", 1, expr=f"{scan} & ~{nz}[{D}]")
        return bx, c0, cx
    for i in range(D):
        bd = m.wire(m.fresh("bd"), 4, expr=dig(b, i))
        m.assign(dig(bx, i), f"{sub} ? {nines_digit(bd, how)} : {bd}")
    c0 = m.wire("c0", 1, expr=f"~{sub} & {cin}" if eac else f"{sub} ? ~{cin} : {cin}")
    return bx, c0, "1'b0"


def _digit_gp(m: Mod, D: int, a: str, bx: str, xs3: bool) -> tuple:
    """(g, p) per digit: the digit sum a_i + b_i generates a decimal
    carry (>= 10) or propagates one (== 9); in excess-3 the pair sums to
    6 + (a + b), so the tests are >= 16 and == 15 on the raw sum."""
    g, p = m.wire("g", D), m.wire("p", D)
    for i in range(D):
        t = m.wire(m.fresh("gp"), 5, expr=f"{{1'b0, {dig(a, i)}}} + {{1'b0, {dig(bx, i)}}}")
        if xs3:
            m.assign(f"{g}[{i}]", f"{t} >= 5'd16")
            m.assign(f"{p}[{i}]", f"{t} == 5'd15")
        else:
            m.assign(f"{g}[{i}]", f"{t} >= 5'd10")
            m.assign(f"{p}[{i}]", f"{t} == 5'd9")
    return g, p


def _lookahead(m: Mod, D: int, g: str, p: str, c0: str, scheme: str, name: str = "c") -> str:
    """The carry vector c[0..D] from the digits' (g, p): flat over the
    whole word (full_lookahead) or flat inside 4-digit groups with the
    groups rippled (digit_group_lookahead)."""
    c = m.wire(name, D + 1)
    m.assign(f"{c}[0]", c0)
    G = D if scheme == "full_lookahead" else 4
    for i in range(D):
        base = (i // G) * G
        terms = [f"{g}[{i}]"]
        for j in range(i - 1, base - 1, -1):
            terms.append(" & ".join([f"{p}[{k}]" for k in range(i, j, -1)] + [f"{g}[{j}]"]))
        terms.append(" & ".join([f"{p}[{k}]" for k in range(i, base - 1, -1)] + [f"{c}[{base}]"]))
        m.assign(f"{c}[{i+1}]", " | ".join(f"({t})" for t in terms))
    return c


# ---- bcd_direct_addition -----------------------------------------------------------------
def _direct_sv(D: int, pins: dict, name: str | None) -> tuple:
    code = str(_pin(pins, "digit_code", "bcd8421"))
    place = str(_pin(pins, "correction_placement", "presum_plus6"))
    scheme = str(_pin(pins, "carry_scheme", "ripple"))
    subtr = str(_pin(pins, "subtraction", "tens_complement_discard_carry"))
    dfam = _pin(pins, "digit_adder.family", None)
    dpins = _sub_pins(pins, "digit_adder.")
    xs3 = code == "excess3"
    name = name or f"fam_bcd_add_direct_{_sfx(code)}_{_sfx(place)[:7]}_{_sfx(scheme)[:6]}_{_sfx(subtr)[:5]}_d{D}{_ptag(pins)}"
    m = Mod(name, f"bcd_direct_addition: {code} digits, correction {place}, carries {scheme}, subtraction {subtr}, "
                  f"complement {_pin(pins, 'complement_generation', 'subtract_from_power')}; s = a +/- b +/- cin mod 10^{D}")
    for pn, w in (("a", 4 * D), ("b", 4 * D), ("sub", 1), ("cin", 1)):
        m.port("input", pn, w)
    m.port("output", "s", 4 * D)
    m.port("output", "cout", 1)
    borrow_chain = subtr == "direct_borrow_subtracter"
    if borrow_chain:
        # the adder path sees b and cin; the subtracter is its own borrow chain (below)
        bx = m.wire("bx", 4 * D, expr="b")
        c0 = m.wire("c0", 1, expr="cin")
        eac, cx = False, "1'b0"
    else:
        eac = subtr == "nines_complement_end_around_carry" and not xs3 \
            and str(_pin(pins, "complement_generation", "")) != "trailing_zero_scan"
        bx, c0, cx = _complement(m, D, pins, "b", "sub", "cin", xs3, eac=eac)
    ax = "a"
    if xs3:
        ax = m.wire("ax", 4 * D)
        for i in range(D):
            m.assign(dig(ax, i), f"{dig('a', i)} + 4'd3")
    # the carries: from the digit adders (ripple) or from the digits' (g, p) (lookahead)
    if scheme == "ripple":
        c = m.wire("c", D + 1)
        m.assign(f"{c}[0]", c0)
    else:
        g, p = _digit_gp(m, D, ax, bx, xs3)
        c = _lookahead(m, D, g, p, c0, scheme)
    r = m.wire("r", 4 * D)
    for i in range(D):
        ai, bi, ci = dig(ax, i), dig(bx, i), f"{c}[{i}]"
        if xs3:
            # excess-3: t = (a+3) + (b+3) + c; a carry means t - 3 (the sum is 6 over), else t + 3 - 6 (3 under... the
            # classical rule: carry: add 3; no carry: subtract 3), the result digit back in excess-3, then -3 to BCD
            t = m.add(dfam, dpins, 4, ai, bi, m.fresh("t"), f"digit {i}: the excess-3 digit sum through the digit adder", cin=ci)
            if scheme == "ripple":
                m.assign(f"{c}[{i+1}]", f"{t}[4]")
            x = m.wire(m.fresh("x"), 4, expr=f"{c}[{i+1}] ? ({t}[3:0] + 4'd3) : ({t}[3:0] - 4'd3)")
            m.assign(dig(r, i), f"{x} - 4'd3")
        elif place == "presum_plus6":
            a6 = m.wire(m.fresh("a6"), 4, expr=f"{ai} + 4'd6")
            t = m.add(dfam, dpins, 4, a6, bi, m.fresh("t"), f"digit {i}: a + 6 + b + c through the digit adder", cin=ci)
            if scheme == "ripple":
                m.assign(f"{c}[{i+1}]", f"{t}[4]")
            m.assign(dig(r, i), f"{c}[{i+1}] ? {t}[3:0] : ({t}[3:0] - 4'd6)")
        elif place == "postsum_plus6":
            t = m.add(dfam, dpins, 4, ai, bi, m.fresh("t"), f"digit {i}: a + b + c through the digit adder", cin=ci)
            if scheme == "ripple":
                m.assign(f"{c}[{i+1}]", f"{t}[4] | ({t}[3] & ({t}[2] | {t}[1]))")
            m.assign(dig(r, i), f"{c}[{i+1}] ? ({t}[3:0] + 4'd6) : {t}[3:0]")
        else:   # direct_decimal_carry_logic: the carry from the digit's generate/propagate, the sum corrected under it
            if scheme == "ripple":
                gi = m.wire(m.fresh("g"), 1, expr=f"({{1'b0, {ai}}} + {{1'b0, {bi}}}) >= 5'd10")
                pi = m.wire(m.fresh("p"), 1, expr=f"({{1'b0, {ai}}} + {{1'b0, {bi}}}) == 5'd9")
                m.assign(f"{c}[{i+1}]", f"{gi} | ({pi} & {ci})")
            t = m.add(dfam, dpins, 4, ai, bi, m.fresh("t"), f"digit {i}: a + b + c through the digit adder", cin=ci)
            m.assign(dig(r, i), f"{c}[{i+1}] ? ({t}[3:0] + 4'd6) : {t}[3:0]")
    cD = f"{c}[{D}]"
    if eac:
        # the nines' complement subtraction: the sum is formed without the +1 (c0 = 0 for a - b), the carry out
        # recirculates as an increment; a difference that leaves no carry is negative in nines' complement form
        # (its minus zero included) and the modular contract wants its tens' complement: the same increment.
        m.comment_line("end-around carry: the recirculated carry and the tens' complement correction of a "
                       "negative difference are one increment (sub & ~cin) under the modular contract")
        inc = m.wire("inc", 1, expr=f"sub & ~cin & ({cD} | ~{cD})")
        s_inc = m.wire("s_inc", 4 * D)
        ic = m.wire("ic", D + 1)
        m.assign(f"{ic}[0]", inc)
        for i in range(D):
            m.assign(dig(s_inc, i), f"({dig(r, i)} == 4'd9 && {ic}[{i}]) ? 4'd0 : ({dig(r, i)} + {ic}[{i}])")
            m.assign(f"{ic}[{i+1}]", f"{ic}[{i}] & ({dig(r, i)} == 4'd9)")
        m.assign("s", s_inc)
        # cout: the sum a + nines(b) + 1 carries out iff a >= b (+cin); the plain sum with the recirculated carry
        m.assign("cout", f"sub ? ({cD} | (~cin & ({ic}[{D}]))) : {cD}")
        return name, m.render()
    if borrow_chain:
        bw = m.wire("bw", D + 1)
        m.assign(f"{bw}[0]", "cin")
        d = m.wire("d", 4 * D)
        for i in range(D):
            t = m.wire(m.fresh("db"), 5, expr=f"{{1'b0, {dig('a', i)}}} - {{1'b0, {dig('b', i)}}} - {{4'b0, {bw}[{i}]}}")
            m.assign(f"{bw}[{i+1}]", f"{t}[4]")
            m.assign(dig(d, i), f"{t}[4] ? ({t}[3:0] + 4'd10) : {t}[3:0]")
        m.assign("s", f"sub ? {d} : {r}")
        m.assign("cout", f"sub ? ~{bw}[{D}] : {cD}")
        return name, m.render()
    m.assign("s", r)
    m.assign("cout", f"{cD} | {cx}")
    return name, m.render()


# ---- speculative_decimal_addition ------------------------------------------------------
def _speculative_sv(D: int, pins: dict, name: str | None) -> tuple:
    target = str(_pin(pins, "speculation_target", "digit_correction"))
    recovery = str(_pin(pins, "recovery", "late_correction_stage"))
    fused = _bpin(pins, "fused_ieee_rounding", False)
    nfam = _pin(pins, "carry_network.family", "parallel_prefix")
    npins = _sub_pins(pins, "carry_network.")
    incr = target in ("rounding_increment", "both") or fused
    W = 4 * D
    name = name or f"fam_bcd_add_spec_{_sfx(target)[:8]}_{_sfx(recovery)[:4]}_d{D}{_ptag(pins)}"
    m = Mod(name, f"speculative_decimal_addition: +6 speculated on every digit of a, one binary carry network "
                  f"({nfam}) over the word, recovery {recovery}, speculation target {target}"
                  + ("; the increment (cin) speculated as the compound sum" if incr else ""))
    for pn, w in (("a", W), ("b", W), ("sub", 1), ("cin", 1)):
        m.port("input", pn, w)
    m.port("output", "s", W)
    m.port("output", "cout", 1)
    bx, c0, cx = _complement(m, D, pins, "b", "sub", "cin", False)
    a6 = m.wire("a6", W)
    for i in range(D):
        m.assign(dig(a6, i), f"{dig('a', i)} + 4'd6")

    def network(tag: str, cin_expr: str) -> tuple:
        """(sum, carries per digit boundary) of a6 + bx + cin_expr through the carry network."""
        t = m.add(nfam, npins, W, a6, bx, f"bn{tag}", f"the binary carry network over a + 6... + b ({tag})", cin=cin_expr)
        c = m.wire(f"cn{tag}", D + 1)
        m.assign(f"{c}[0]", cin_expr)
        for i in range(1, D):
            m.assign(f"{c}[{i}]", f"{a6}[{4*i}] ^ {bx}[{4*i}] ^ {t}[{4*i}]")
        m.assign(f"{c}[{D}]", f"{t}[{W}]")
        return t, c

    if not incr:
        t, c = network("", c0)
        cands = [(t, c, None)]
    else:
        # the sum and the incremented sum (the increment speculated), the carry-in selects
        m.comment_line("the rounding increment speculated: both a + b and a + b + 1 are formed, the carry-in selects")
        t0, cc0 = network("0", "1'b0")
        t1, cc1 = network("1", "1'b1")
        cands = [(t0, cc0, f"~{c0}"), (t1, cc1, c0)]
    outs = []
    for t, c, sel in cands:
        r = m.wire(m.fresh("r"), W)
        for i in range(D):
            if recovery == "dual_path_select":
                # both candidates of the digit (its carry-in 0 or 1) corrected in parallel, the carry selects
                u0 = m.wire(m.fresh("u0"), 5, expr=f"{{1'b0, {dig(a6, i)}}} + {{1'b0, {dig(bx, i)}}}")
                u1 = m.wire(m.fresh("u1"), 5, expr=f"{{1'b0, {dig(a6, i)}}} + {{1'b0, {dig(bx, i)}}} + 5'd1")
                v0 = m.wire(m.fresh("v0"), 4, expr=f"{u0}[4] ? {u0}[3:0] : ({u0}[3:0] - 4'd6)")
                v1 = m.wire(m.fresh("v1"), 4, expr=f"{u1}[4] ? {u1}[3:0] : ({u1}[3:0] - 4'd6)")
                m.assign(dig(r, i), f"{c}[{i}] ? {v1} : {v0}")
            else:
                # late correction: the digit's binary sum loses 6 when no decimal carry left it
                m.assign(dig(r, i), f"{c}[{i+1}] ? {dig(t, i)} : ({dig(t, i)} - 4'd6)")
        outs.append((r, f"{c}[{D}]", sel))
    if len(outs) == 1:
        m.assign("s", outs[0][0])
        m.assign("cout", f"{outs[0][1]} | {cx}")
    else:
        m.assign("s", f"{c0} ? {outs[1][0]} : {outs[0][0]}")
        m.assign("cout", f"({c0} ? {outs[1][1]} : {outs[0][1]}) | {cx}")
    return name, m.render()


# ---- redundant_decimal_addition --------------------------------------------------------
DIGIT_SETS = {"svoboda_signed_digit": 6, "rbcd_m7_p7": 7, "maximally_redundant_m9_p9": 9, "overloaded_0_15": None}


def _sd(m: Mod, name: str, D: int) -> str:
    """A word of D signed digits, five bits each (two's complement)."""
    return m.wire(name, 5 * D)


def sdig(x: str, i: int) -> str:
    return f"{x}[{5*i+4}:{5*i}]"


def _recode_sd(m: Mod, D: int, src: str, out: str, negate: bool) -> str:
    """BCD digits into the signed-digit set: a digit of 6 or more becomes
    d - 10 with a transfer of one into the next digit (carry-free: every
    digit receives at most the transfer of its lower neighbor), the
    digits then in [-4, 6]; `negate` negates the recoded digits. Returns
    the transfer out of the top digit (0 or 1)."""
    t = m.wire(m.fresh("rt"), D + 1)
    m.assign(f"{t}[0]", "1'b0")
    for i in range(D):
        d = dig(src, i)
        m.assign(f"{t}[{i+1}]", f"{d} >= 4'd6")
        raw = f"($signed({{1'b0, {d}}}) - ({t}[{i+1}] ? 5'sd10 : 5'sd0) + $signed({{4'b0, {t}[{i}]}}))"
        m.assign(sdig(out, i), f"-{raw}" if negate else raw)
    return f"{t}[{D}]"


def _redundant_sv(D: int, pins: dict, name: str | None) -> tuple:
    ds = str(_pin(pins, "digit_set", "svoboda_signed_digit"))
    both = str(_pin(pins, "operands_redundant", "one")) == "both"
    conv = str(_pin(pins, "final_conversion", "carry_propagate_adder"))
    amax = DIGIT_SETS.get(ds, 6)
    W = 4 * D
    name = name or f"fam_bcd_add_redund_{_sfx(ds)[:8]}_{'both' if both else 'one'}_{_sfx(conv)[:5]}_d{D}{_ptag(pins)}"
    m = Mod(name, f"redundant_decimal_addition: digit set {ds}, {'both operands' if both else 'one operand'} redundant, "
                  f"carry-free two-step addition (interim digit and transfer), final conversion {conv}")
    for pn, w in (("a", W), ("b", W), ("sub", 1), ("cin", 1)):
        m.port("input", pn, w)
    m.port("output", "s", W)
    m.port("output", "cout", 1)
    if amax is None:
        # overloaded digits 0..15: the operands enter as they are (a subtraction adds the nines' complement and the
        # tens' complement +1 as the transfer into digit 0); a digit sum of 10 or more hands a transfer of one up,
        # the interim digit plus the incoming transfer stays within 0..10
        bx, c0, cx = _complement(m, D, pins, "b", "sub", "cin", False)
        t = m.wire("t", D + 1)
        m.assign(f"{t}[0]", c0)
        sd = []
        for i in range(D):
            u = m.wire(m.fresh("u"), 5, expr=f"{{1'b0, {dig('a', i)}}} + {{1'b0, {dig(bx, i)}}}")
            m.assign(f"{t}[{i+1}]", f"{u} >= 5'd10")
            w = m.wire(m.fresh("w"), 5, expr=f"{u} - ({t}[{i+1}] ? 5'd10 : 5'd0)")
            sd.append(m.wire(f"sd{i}", 5, expr=f"{w} + {{4'b0, {t}[{i}]}}"))
        # the conversion to BCD: a digit of 10 or more sends a carry up
        g, p = m.wire("g", D), m.wire("p", D)
        for i in range(D):
            m.assign(f"{g}[{i}]", f"{sd[i]} >= 5'd10")
            m.assign(f"{p}[{i}]", f"{sd[i]} == 5'd9")
        if conv == "on_the_fly":
            m.comment_line("on-the-fly form: both candidates of every digit (carry-in 0 or 1) selected by a carry prefix")
            c = _lookahead(m, D, g, p, "1'b0", "full_lookahead")
            for i in range(D):
                d0 = f"({g}[{i}] ? ({sd[i]}[3:0] - 4'd10) : {sd[i]}[3:0])"
                d1 = f"(({g}[{i}] | {p}[{i}]) ? ({sd[i]}[3:0] - 4'd9) : ({sd[i]}[3:0] + 4'd1))"
                m.assign(dig("s", i), f"{c}[{i}] ? {d1} : {d0}")
            m.assign("cout", f"{t}[{D}] | {c}[{D}] | {cx}")
        else:
            c = m.wire("c", D + 1)
            m.assign(f"{c}[0]", "1'b0")
            for i in range(D):
                v = m.wire(m.fresh("v"), 5, expr=f"{sd[i]} + {{4'b0, {c}[{i}]}}")
                m.assign(f"{c}[{i+1}]", f"{v} >= 5'd10")
                m.assign(dig("s", i), f"{c}[{i+1}] ? ({v}[3:0] - 4'd10) : {v}[3:0]")
            m.assign("cout", f"{t}[{D}] | {c}[{D}] | {cx}")
        return name, m.render()
    # a signed digit set -amax..amax
    x = _sd(m, "x", D)
    y = _sd(m, "y", D)
    ta = _recode_sd(m, D, "a", x, False)
    if both:
        yp = _sd(m, "yp", D)
        tb = _recode_sd(m, D, "b", yp, False)
        for i in range(D):
            m.assign(sdig(y, i), f"sub ? -$signed({sdig(yp, i)}) : $signed({sdig(yp, i)})")
        tb_expr = f"(sub ? -$signed({{4'b0, {tb}}}) : $signed({{4'b0, {tb}}}))"
    else:
        for i in range(D):
            m.assign(sdig(y, i), f"sub ? -$signed({{1'b0, {dig('b', i)}}}) : $signed({{1'b0, {dig('b', i)}}})")
        tb_expr = "5'sd0"
    # the carry-free addition: transfer +1 when the digit sum reaches amax, -1 when it reaches -amax
    t = m.wire("t", 5 * (D + 1), signed=False)
    m.assign(sdig(t, 0), "sub ? -$signed({4'b0, cin}) : $signed({4'b0, cin})")
    sd = []
    for i in range(D):
        u = m.wire(m.fresh("u"), 6, signed=True, expr=f"$signed({sdig(x, i)}) + $signed({sdig(y, i)})")
        ti = m.wire(m.fresh("ti"), 5, signed=True, expr=f"({u} >= 6'sd{amax}) ? 5'sd1 : ({u} <= -6'sd{amax}) ? -5'sd1 : 5'sd0")
        m.assign(sdig(t, i + 1), ti)
        w = m.wire(m.fresh("w"), 5, signed=True, expr=f"{u}[4:0] - ({ti} * 5'sd10)")
        sd.append(m.wire(f"sd{i}", 5, signed=True, expr=f"{w} + $signed({sdig(t, i)})"))
    # the conversion of the signed digits to BCD (their value modulo 10^D) and the sign of the raw value
    neg = m.wire("neg", 1)
    if conv == "on_the_fly":
        m.comment_line("on-the-fly form: the digit and the digit less one (the Q/QM pair) selected by a borrow prefix")
        g, p = m.wire("g", D), m.wire("p", D)
        for i in range(D):
            m.assign(f"{g}[{i}]", f"{sd[i]} < 5'sd0")
            m.assign(f"{p}[{i}]", f"{sd[i]} == 5'sd0")
        bw = _lookahead(m, D, g, p, "1'b0", "full_lookahead")
        for i in range(D):
            v = sd[i]
            d0 = f"({g}[{i}] ? ({v}[3:0] + 4'd10) : {v}[3:0])"
            d1 = f"(({g}[{i}] | {p}[{i}]) ? ({v}[3:0] + 4'd9) : ({v}[3:0] - 4'd1))"
            m.assign(dig("s", i), f"{bw}[{i}] ? {d1} : {d0}")
        m.assign(neg, f"{bw}[{D}]")
    else:
        m.comment_line("carry-propagate conversion: the positive digits less the negative digits through a borrow chain")
        bw = m.wire("bw", D + 1)
        m.assign(f"{bw}[0]", "1'b0")
        for i in range(D):
            v = sd[i]
            pp = f"({v}[4] ? 5'd0 : {v})"
            nn = f"({v}[4] ? (5'd0 - {v}) : 5'd0)"
            tt = m.wire(m.fresh("cv"), 5, expr=f"{pp} - {nn} - {{4'b0, {bw}[{i}]}}")
            m.assign(f"{bw}[{i+1}]", f"{tt}[4]")
            m.assign(dig("s", i), f"{tt}[4] ? ({tt}[3:0] + 4'd10) : {tt}[3:0]")
        m.assign(neg, f"{bw}[{D}]")
    # the top transfers: the addition's, the recodings' (the negated one under sub), less the conversion's borrow
    top = m.wire("top", 5, signed=True,
                 expr=f"$signed({sdig(t, D)}) + $signed({{4'b0, {ta}}}) + {tb_expr} - $signed({{4'b0, {neg}}})")
    m.assign("cout", f"sub ? ({top} >= 5'sd0) : ({top} >= 5'sd1)")
    return name, m.render()


# ---- decimal_multioperand_addition -----------------------------------------------------
def _root_adder(m: Mod, D: int, pins: dict, x: str, y: str, s: str, cout: str, comment: str):
    """s, cout = x + y through a decimal carry-propagate adder generated
    over the `root_adder` (or `final_adder`) family: a prefix or
    lookahead family gives the word-level lookahead over the digits'
    generate and propagate, the others the digit adders rippled."""
    fam = str(_pin(pins, "family", "ripple_carry"))
    scheme = "full_lookahead" if fam in ("parallel_prefix", "ling_prefix", "compound_flagged_prefix", "sparse_prefix_hybrid",
                                         "carry_lookahead", "prefix_synthesis_nonuniform_arrival") else "ripple"
    dp = {"correction_placement": "postsum_plus6", "carry_scheme": scheme, "digit_adder.family": fam}
    dp.update({f"digit_adder.{k}": v for k, v in pins.items() if k != "family"})
    n, text = _direct_sv(D, dp, None)
    m.extra.append(text)
    m.n += 1
    m.comment_line(f"{comment}: the decimal carry-propagate adder over the {fam} digit adders ({scheme} carries)")
    m.raw(f"  {n} u{m.n} (.a({x}), .b({y}), .sub(1'b0), .cin(1'b0), .s({s}), .cout({cout}));")


def _multioperand_sv(D: int, pins: dict, name: str | None) -> tuple:
    style = str(_pin(pins, "reduction_style", "bcd_csa_per_level_correction"))
    arity = str(_pin(pins, "compressor_arity", "3_to_2"))
    place = str(_pin(pins, "correction_placement", "per_level"))
    rpins = _sub_pins(pins, "root_adder.")
    W = 4 * D
    name = name or f"fam_bcd_add_multiop_{_sfx(style)[:8]}_{_sfx(arity)[:4]}_{_sfx(place)[:5]}_d{D}{_ptag(pins)}"
    m = Mod(name, f"decimal_multioperand_addition: the operands a, b (or its nines' complement) and the carry-in word "
                  f"reduced by {style} ({arity} compressors, correction {place}), then the root adder")
    for pn, w in (("a", W), ("b", W), ("sub", 1), ("cin", 1)):
        m.port("input", pn, w)
    m.port("output", "s", W)
    m.port("output", "cout", 1)
    bx, c0, cx = _complement(m, D, pins, "b", "sub", "cin", False)
    k = m.wire("k", W, expr=f"{{{{{W-1}{{1'b0}}}}, {c0}}}")
    S = m.wire("S", W)
    C = m.wire("C", W)          # the carry word, one digit up
    lost = cx
    root_cout = m.wire("rc", 1)
    if style == "signed_digit_binary_compressors":
        # the digits in 4221 code: binary 3:2 compressors serve, the carry word doubled through the 5211 code
        m.comment_line("4221-coded digits: a bitwise 3:2 compressor; the carry word doubled by the 4221 -> 5211 recoding and one shift")
        x4, y4, k4 = m.wire("x4", W), m.wire("y4", W), m.wire("k4", W)
        m.table("T4221", list(CODE_4221) + [0] * 6, 4, "the 4221 code per digit value")
        for i in range(D):
            for src, dst in (("a", x4), (bx, y4), (k, k4)):
                m.assign(dig(dst, i), f"T4221[({dig(src, i)}) * 4 +: 4]")
        s4 = m.wire("s4", W, expr=f"{x4} ^ {y4} ^ {k4}")
        c4 = m.wire("c4", W, expr=f"({x4} & {y4}) | ({x4} & {k4}) | ({y4} & {k4})")
        # 4221 -> 5211 per digit (by value), then the word shifted left by one bit: the doubled value in 4221
        c5 = m.wire("c5", W)
        vals = [sum(w for w, bit in zip(W_4221, (c >> 3 & 1, c >> 2 & 1, c >> 1 & 1, c & 1)) if bit) for c in range(16)]
        m.table("T4to5", [CODE_5211[v] for v in vals], 4, "4221 pattern -> the 5211 code of its value")
        m.table("V4221", vals, 4, "4221 pattern -> its value")
        for i in range(D):
            m.assign(dig(c5, i), f"T4to5[({dig(c4, i)}) * 4 +: 4]")
        c2 = m.wire("c2", W, expr=f"{{{c5}[{W-2}:0], 1'b0}}")
        lost = f"{c5}[{W-1}]"
        for i in range(D):
            m.assign(dig(S, i), f"V4221[({dig(s4, i)}) * 4 +: 4]")
            m.assign(dig(C, i), f"V4221[({dig(c2, i)}) * 4 +: 4]")
        _root_adder(m, D, rpins, S, C, "s", root_cout, "the root adder over the sum and the doubled carry words")
        m.assign("cout", f"{root_cout} | {lost}")
        return name, m.render()
    if style == "binary_tree_then_convert" or (style == "decimal_compressors" and arity == "higher") \
            or (style == "bcd_csa_per_level_correction" and place == "at_root"):
        # binary column sums (no carry crosses a digit boundary), one decimal conversion chain at the root; under the
        # binary tree `column_sum` picks the per-digit form: two two-input adders, or a 3:2 compressor and one adder
        csum = str(_pin(pins, "column_sum", "two_input_adders"))
        two_input = style == "binary_tree_then_convert" and csum == "two_input_adders"
        how = "two-input binary adders" if two_input else "a 3:2 compressor and a binary adder"
        m.comment_line(f"binary column sums per digit ({how}), the decimal correction at the root")
        u = m.wire("u", 5 * D)
        for i in range(D):
            xa, xb, xk = dig("a", i), dig(bx, i), dig(k, i)
            if two_input:
                t1 = m.wire(m.fresh("t1"), 5, expr=f"{{1'b0, {xa}}} + {{1'b0, {xb}}}")
                m.assign(sdig(u, i), f"{t1} + {{1'b0, {xk}}}")
            else:
                cs = m.wire(m.fresh("cs"), 4, expr=f"{xa} ^ {xb} ^ {xk}")
                cc = m.wire(m.fresh("cc"), 4, expr=f"({xa} & {xb}) | ({xa} & {xk}) | ({xb} & {xk})")
                m.assign(sdig(u, i), f"{{1'b0, {cs}}} + {{{cc}, 1'b0}}")
        cy = m.wire("cy", 2 * (D + 1))
        m.assign(f"{cy}[1:0]", "2'd0")
        for i in range(D):
            v = m.wire(m.fresh("v"), 5, expr=f"{sdig(u, i)} + {{3'b0, {cy}[{2*i+1}:{2*i}]}}")
            m.assign(f"{cy}[{2*i+3}:{2*i+2}]", f"({v} >= 5'd20) ? 2'd2 : ({v} >= 5'd10) ? 2'd1 : 2'd0")
            m.assign(dig("s", i), f"({v} >= 5'd20) ? ({v}[3:0] - 4'd4) : ({v} >= 5'd10) ? ({v}[3:0] - 4'd10) : {v}[3:0]")
        m.assign("cout", f"{cy}[{2*D}] | {cx}")
        return name, m.render()
    if style == "decimal_compressors" and arity == "4_to_2":
        # a decimal 4:2 per digit (the fourth input zero): the horizontal carry leaves when the four inputs reach 20,
        # the vertical carry when the rest plus the incoming horizontal carry reaches 10
        m.comment_line("decimal 4:2 compressors: a horizontal carry between the digits' compressors, a vertical carry word")
        h = m.wire("h", D + 1)
        m.assign(f"{h}[0]", "1'b0")
        m.assign(dig(C, 0), "4'd0")
        for i in range(D):
            f4 = m.wire(m.fresh("f"), 6, expr=f"{{2'b0, {dig('a', i)}}} + {{2'b0, {dig(bx, i)}}} + {{2'b0, {dig(k, i)}}}")
            m.assign(f"{h}[{i+1}]", f"{f4} >= 6'd20")
            rem = m.wire(m.fresh("rm"), 6, expr=f"{f4} - ({h}[{i+1}] ? 6'd20 : 6'd0) + {{5'b0, {h}[{i}]}}")
            cv = m.wire(m.fresh("cv"), 2, expr=f"({rem} >= 6'd20) ? 2'd2 : ({rem} >= 6'd10) ? 2'd1 : 2'd0")
            m.assign(dig(S, i), f"({rem} >= 6'd20) ? ({rem}[3:0] - 4'd4) : ({rem} >= 6'd10) ? ({rem}[3:0] - 4'd10) : {rem}[3:0]")
            if i + 1 < D:
                m.assign(dig(C, i + 1), f"{{2'b0, {cv}}}")
            else:
                lost = f"(({cv} != 2'd0) | {h}[{D}])"
        _root_adder(m, D, rpins, S, C, "s", root_cout, "the root adder over the sum and carry words")
        m.assign("cout", f"{root_cout} | {lost}")
        return name, m.render()
    # a decimal 3:2 per digit with the correction in the level: the digit sum split into a BCD sum digit and a
    # carry digit of 0, 1 or 2 at the next position
    m.comment_line("decimal 3:2 compressors with the correction per level: sum digit 0..9, carry digit 0..2 one position up")
    m.assign(dig(C, 0), "4'd0")
    for i in range(D):
        f3 = m.wire(m.fresh("f"), 5, expr=f"{{1'b0, {dig('a', i)}}} + {{1'b0, {dig(bx, i)}}} + {{1'b0, {dig(k, i)}}}")
        cd = m.wire(m.fresh("cd"), 2, expr=f"({f3} >= 5'd20) ? 2'd2 : ({f3} >= 5'd10) ? 2'd1 : 2'd0")
        m.assign(dig(S, i), f"({f3} >= 5'd20) ? ({f3}[3:0] - 4'd4) : ({f3} >= 5'd10) ? ({f3}[3:0] - 4'd10) : {f3}[3:0]")
        if i + 1 < D:
            m.assign(dig(C, i + 1), f"{{2'b0, {cd}}}")
        else:
            lost = f"({cd} != 2'd0)"
    _root_adder(m, D, rpins, S, C, "s", root_cout, "the root adder over the sum and carry words")
    m.assign("cout", f"{root_cout} | {lost}")
    return name, m.render()


# ---- entry points --------------------------------------------------------------------------
def bcd_adder_sv(D: int, family: str, pins: dict, name: str | None = None) -> tuple:
    """(module name, text) of a decimal adder family at D digits."""
    pins = pins or {}
    if family == "bcd_direct_addition":
        return _direct_sv(D, pins, name)
    if family == "speculative_decimal_addition":
        return _speculative_sv(D, pins, name)
    if family == "redundant_decimal_addition":
        return _redundant_sv(D, pins, name)
    if family == "decimal_multioperand_addition":
        return _multioperand_sv(D, pins, name)
    raise ValueError(f"decimal adder family {family!r}: one of {DECIMAL_FAMILIES['adder']}")


# ---- parallel_decimal_multiplication -----------------------------------------------------
def _bcd_adder_inst(m: Mod, digits: int, pins: dict, x: str, y: str, out: str, comment: str, sub: str = "1'b0") -> str:
    """out (4 digits + 1 carry bit... as `out` of 4*digits bits, the carry
    in `out_c`) = x + y (or x - y under sub) through a generated direct
    BCD adder over the `family` of pins (ripple digit adders by default)."""
    fam = str(_pin(pins, "family", "ripple_carry"))
    scheme = "full_lookahead" if fam in ("parallel_prefix", "ling_prefix", "compound_flagged_prefix", "sparse_prefix_hybrid",
                                         "carry_lookahead", "prefix_synthesis_nonuniform_arrival") else "ripple"
    dp = {"correction_placement": "postsum_plus6", "carry_scheme": scheme, "digit_adder.family": fam}
    dp.update({f"digit_adder.{k}": v for k, v in pins.items() if k != "family"})
    n, text = _direct_sv(digits, dp, None)
    m.extra.append(text)
    m.n += 1
    m.wire(out, 4 * digits)
    m.wire(f"{out}_c", 1)
    m.comment_line(f"{comment}: a decimal carry-propagate adder over {fam} digit adders ({scheme} carries)")
    m.raw(f"  {n} u{m.n} (.a({x}), .b({y}), .sub({sub}), .cin(1'b0), .s({out}), .cout({out}_c));")
    return out


def _dbl(m: Mod, src: str, digits: int, out: str) -> str:
    """out (digits + 1 digits) = 2 * src, digitwise: a digit of 5 or more
    carries one into the next digit, whose doubled value is even and
    absorbs it."""
    m.wire(out, 4 * (digits + 1))
    for i in range(digits + 1):
        d = dig(src, i) if i < digits else "4'd0"
        lo = f"(({d} >= 4'd5) ? (({d} << 1) - 4'd10) : ({d} << 1))" if i < digits else "4'd0"
        cy = f"({dig(src, i - 1)} >= 4'd5)" if i > 0 else "1'b0"
        m.assign(dig(out, i), f"{lo} + {{3'b0, {cy}}}")
    return out


def _quint(m: Mod, src: str, digits: int, out: str) -> str:
    """out (digits + 1 digits) = 5 * src, digitwise: 5 d = 10 floor(d/2)
    + 5 (d mod 2), so digit i takes 5 (d_i mod 2) plus floor(d_{i-1}/2)."""
    m.wire(out, 4 * (digits + 1))
    ds = [m.wire(m.fresh("qd"), 4, expr=dig(src, i)) for i in range(digits)]
    for i in range(digits + 1):
        lo = f"({ds[i]}[0] ? 4'd5 : 4'd0)" if i < digits else "4'd0"
        cy = f"{{1'b0, {ds[i-1]}[3:1]}}" if i > 0 else "4'd0"
        m.assign(dig(out, i), f"{lo} + {cy}")
    return out


def _multiples(m: Mod, src: str, digits: int, need, apins: dict, pre: str) -> dict:
    """{k: wire} of k * src (digits + 1 digits each) for the needed k:
    doubling and quintupling digitwise (carry-free), 10x a digit shift,
    the rest by one decimal addition each."""
    mult = {}
    if not need:
        return mult
    m.comment_line("the multiples of the multiplicand: doubling and quintupling digitwise (carry-free), the rest by one addition each")
    mult[1] = m.wire(f"{pre}x1", 4 * (digits + 1), expr=f"{{4'd0, {src}}}")
    if {2, 4, 8, 6} & set(need):
        mult[2] = _dbl(m, src, digits, f"{pre}x2")
    for k, half in ((4, 2), (8, 4)):
        if {k, 8} & set(need) if k == 4 else k in need:
            w = _dbl(m, mult[half], digits + 1, f"{pre}x{k}w")
            mult[k] = m.wire(f"{pre}x{k}", 4 * (digits + 1), expr=f"{w}[{4*(digits+1)-1}:0]")
    if 5 in need:
        mult[5] = _quint(m, src, digits, f"{pre}x5")
    if 10 in need:
        mult[10] = m.wire(f"{pre}x10", 4 * (digits + 1), expr=f"{{{src}, 4'd0}}")
    if 3 in need:
        mult[3] = _bcd_adder_inst(m, digits + 1, apins, mult[2], mult[1], f"{pre}x3", "3x = 2x + x")
    if 6 in need:
        w = _dbl(m, mult[3], digits + 1, f"{pre}x6w")
        mult[6] = m.wire(f"{pre}x6", 4 * (digits + 1), expr=f"{w}[{4*(digits+1)-1}:0]")
    if 7 in need:
        mult[7] = _bcd_adder_inst(m, digits + 1, apins, mult[5], mult[2], f"{pre}x7", "7x = 5x + 2x")
    if 9 in need:
        mult[9] = _bcd_adder_inst(m, digits + 1, apins, mult[8], mult[1], f"{pre}x9", "9x = 8x + x")
    return mult


def _mul_core(m: Mod, x: str, DA: int, y: str, DB: int, pins: dict, out: str, pre: str = "") -> str:
    """out (DA + DB digits) = x (DA digits) * y (DB digits) inside module
    m, as parallel_decimal_multiplication builds it: the multiples of x,
    the multiplier digits recoded, one row per (recoded) digit, the rows
    reduced in the internal digit code, one final decimal adder."""
    rec = str(_pin(pins, "multiplier_recoding", "sd_radix10_m5_p5"))
    code = str(_pin(pins, "internal_digit_code", "bcd8421"))
    ppg = str(_pin(pins, "pp_generation", "precomputed_multiples_mux"))
    tree = str(_pin(pins, "reduction_tree.family", "linear_chain"))
    comp = str(_pin(pins, "reduction_tree.compressor", "3:2"))
    fpins = _sub_pins(pins, "final_adder.")
    tpins = _sub_pins(pins, "reduction_tree.cpa.") or _sub_pins(pins, "reduction_tree.final_cpa.")
    DD = DA + DB
    sd_code = code == "sd_m8_p8_posibit_negabit"
    xs3 = code == "xs3_odds"
    coded = code in ("bcd4221", "bcd5211")
    dw = 5 if sd_code else 4            # bits per digit inside the tree
    m.comment_line(f"{pre or 'the'} decimal multiplier ({DA} x {DB} digits): recoding {rec}, partial products by {ppg}, "
                   f"the rows in {code}, reduced by a {tree} ({comp})")
    # ---- the multiples of x (DA + 1 digits each)
    need = {"none": (1, 2, 3, 4, 5, 6, 7, 8, 9), "sd_radix10_m5_p5": (1, 2, 3, 4, 5), "radix4_radix5_split": (1, 2, 5, 10)}[rec]
    if ppg == "digit_by_digit":
        need = ()
    mult = _multiples(m, x, DA, need, fpins, pre)
    # ---- the multiplier digits after recoding: (position, magnitude wire (4 bits), sign wire, magnitude set)
    digs = []
    if rec == "none":
        for i in range(DB):
            digs.append((i, m.wire(f"{pre}y{i}", 4, expr=dig(y, i)), "1'b0", tuple(range(10))))
    elif rec == "sd_radix10_m5_p5":
        m.comment_line("signed-digit recoding of the multiplier: a digit of 6 or more (or 5 with an incoming carry) becomes d - 10 "
                       "with a carry into the next digit; a prefix over the digits' (>= 6, == 5) gives the carries")
        g, p = m.wire(f"{pre}rg", DB), m.wire(f"{pre}rp", DB)
        for i in range(DB):
            m.assign(f"{g}[{i}]", f"{dig(y, i)} >= 4'd6")
            m.assign(f"{p}[{i}]", f"{dig(y, i)} == 4'd5")
        c = _lookahead(m, DB, g, p, "1'b0", "full_lookahead", name=f"{pre}rc")
        for i in range(DB):
            v = m.wire(f"{pre}yv{i}", 5, signed=True, expr=f"$signed({{1'b0, {dig(y, i)}}}) + $signed({{4'b0, {c}[{i}]}}) - ({c}[{i+1}] ? 5'sd10 : 5'sd0)")
            s = m.wire(f"{pre}ys{i}", 1, expr=f"{v}[4]")
            mag = m.wire(f"{pre}y{i}", 4, expr=f"{s} ? (4'd0 - {v}[3:0]) : {v}[3:0]")
            digs.append((i, mag, s, (0, 1, 2, 3, 4, 5)))
        digs.append((DB, m.wire(f"{pre}y{DB}", 4, expr=f"{{3'b0, {c}[{DB}]}}"), "1'b0", (0, 1)))
    else:   # radix4_radix5_split: y_i = 5 u + l, l recoded to -2..2 with its carry into u
        m.comment_line("radix-5 x radix-2 split of every multiplier digit: d = 5u + l, l in -2..2 with its carry into u (0, 1 or 2)")
        for i in range(DB):
            d = m.wire(f"{pre}yd{i}", 4, expr=dig(y, i))
            r5 = m.wire(f"{pre}yr{i}", 4, expr=f"{d} % 4'd5")
            u = m.wire(f"{pre}yu{i}", 2, expr=f"{{1'b0, ({d} >= 4'd5)}} + {{1'b0, ({r5} >= 4'd3)}}")
            lv = m.wire(f"{pre}ylv{i}", 5, signed=True, expr=f"$signed({{1'b0, {r5}}}) - (({r5} >= 4'd3) ? 5'sd5 : 5'sd0)")
            s = m.wire(f"{pre}yls{i}", 1, expr=f"{lv}[4]")
            mag = m.wire(f"{pre}yl{i}", 4, expr=f"{s} ? (4'd0 - {lv}[3:0]) : {lv}[3:0]")
            digs.append((i, mag, s, (0, 1, 2)))
            digs.append((i, m.wire(f"{pre}yu5{i}", 4, expr=f"({u} == 2'd2) ? 4'd10 : ({u} == 2'd1) ? 4'd5 : 4'd0"), "1'b0", (0, 5, 10)))
    # ---- the digit tables of the internal code (once per module)
    vals4 = [sum(w for w, bit in zip(W_4221, (c >> 3 & 1, c >> 2 & 1, c >> 1 & 1, c & 1)) if bit) for c in range(16)]
    vals5 = [sum(w for w, bit in zip(W_5211, (c >> 3 & 1, c >> 2 & 1, c >> 1 & 1, c & 1)) if bit) for c in range(16)]
    if code == "bcd4221" and "T4221" not in m.tables:
        m.table("T4221", list(CODE_4221) + [0] * 6, 4, "the 4221 code per digit value")
        m.table("V4221", vals4, 4, "4221 pattern -> its value")
        m.table("T4to5", [CODE_5211[v] for v in vals4], 4, "4221 pattern -> the 5211 code of its value")
    if code == "bcd5211" and "T5211" not in m.tables:
        m.table("T5211", list(CODE_5211) + [0] * 6, 4, "the 5211 code per digit value")
        m.table("V5211", vals5, 4, "5211 pattern -> its value")
        m.table("T4to5b", [CODE_5211[v] for v in vals4], 4, "4221 pattern -> the 5211 code of its value")

    def to_code(d: str) -> str:
        """A BCD digit expression into the internal code."""
        if code == "bcd4221":
            return f"T4221[({d}) * 4 +: 4]"
        if code == "bcd5211":
            return f"T5211[({d}) * 4 +: 4]"
        if xs3:
            return f"({d} + 4'd3)"
        return d
    # ---- the rows (DD digits of dw bits): the multiple (or the digit products) at the digit's position, a negative
    #      row as the complement in the code (or the negated digits) plus one in the units word at its start
    rows = []
    unit_sign = {}                  # position -> the signs of the negated rows starting there (the +1 of each tens' complement)
    zero_d = "5'd0" if sd_code else ("4'd3" if xs3 else "4'd0")   # the code word of a zero digit in a row
    tree_zero = "5'd0" if sd_code else "4'd0"                     # a zero digit inside the tree (plain values)

    def cell(w: str, i: int) -> str:
        return f"{w}[{dw*i+dw-1}:{dw*i}]"

    def neg_cell(expr: str) -> str:
        """The digit of a negated row: the nines' complement in the code (bit inversion for the self-complementing
        codes and excess-3, 9 - d in BCD), the negated digit for signed digits."""
        if sd_code:
            return f"(-$signed({expr}))"
        if coded or xs3:
            return f"(~{expr})"
        return f"(4'd9 - {expr})"

    biased_rows = 0
    for k, (pos, mag, sgn, magset) in enumerate(digs):
        if ppg == "digit_by_digit":
            # the digit products |y| * x_j as (tens, units) pairs from a table, two rows per digit
            tbl = f"{pre}DP{k}"
            entries = []
            for yv in range(16):
                for av in range(16):
                    pr = yv * av if (yv in magset and av <= 9) else 0
                    entries.append(((pr // 10) << 4) | (pr % 10))
            m.table(tbl, entries, 8, f"digit products of the multiplier digit {k} (magnitudes {magset}) by a digit: tens, units")
            for half in ("lo", "hi"):
                start = pos + (1 if half == "hi" else 0)
                r = m.wire(f"{pre}row{k}{half}", dw * DD)
                for i in range(DD):
                    j = i - start
                    if 0 <= j < DA:
                        e = m.wire(m.fresh("dp"), 8, expr=f"{tbl}[({{{mag}, {dig(x, j)}}}) * 8 +: 8]")
                        dexpr = f"{e}[3:0]" if half == "lo" else f"{e}[7:4]"
                        cd = m.wire(m.fresh("cd"), dw, expr=(f"{{1'b0, {to_code(dexpr)}}}" if sd_code else to_code(dexpr)))
                    else:
                        cd = m.wire(m.fresh("cd"), dw, expr=zero_d)
                    m.assign(cell(r, i), f"{sgn} ? {neg_cell(cd)} : {cd}" if i >= start else cd)
                rows.append(r)
                biased_rows += 1
                if sgn != "1'b0" and not sd_code and start < DD:
                    unit_sign[start] = unit_sign.get(start, []) + [sgn]
            continue
        r = m.wire(f"{pre}row{k}", dw * DD)
        for i in range(DD):
            j = i - pos
            if 0 <= j <= DA:
                arms = " : ".join(f"({mag} == 4'd{v}) ? {to_code(dig(mult[v], j))}" for v in magset if v != 0)
                sel = m.wire(m.fresh("sl"), 4, expr=f"{arms} : {zero_d if not sd_code else '4' + chr(39) + 'd0'}")
                cd = m.wire(m.fresh("cd"), dw, expr=(f"{{1'b0, {sel}}}" if sd_code else sel))
            else:
                cd = m.wire(m.fresh("cd"), dw, expr=zero_d)
            m.assign(cell(r, i), f"{sgn} ? {neg_cell(cd)} : {cd}" if i >= pos else cd)
        rows.append(r)
        biased_rows += 1
        if sgn != "1'b0" and not sd_code:
            unit_sign[pos] = unit_sign.get(pos, []) + [sgn]
    if not sd_code and unit_sign:
        u = m.wire(f"{pre}uw", dw * DD)
        for i in range(DD):
            terms = unit_sign.get(i, [])
            m.assign(cell(u, i), " + ".join(f"{{3'b0, {t}}}" for t in terms) if terms else "4'd0")
        rows.append(u)
    if xs3:
        rep = (10 ** DD - 1) // 9
        kval = (-3 * biased_rows * rep) % (10 ** DD)
        kw = m.wire(f"{pre}kw", 4 * DD, expr=bcd_const(kval, DD))
        m.comment_line(f"the excess-3 bias of the {biased_rows} rows removed by the constant row {kval}")
        rows.append(kw)
    # ---- the reduction: the domain's 3:2 (4:2 as two of them, 7:3 as a column counter where the code allows)
    lvl = [0]

    def csa32(x_: str, y_: str, z_: str) -> tuple:
        lvl[0] += 1
        s = m.wire(f"{pre}s{lvl[0]}", dw * DD)
        c = m.wire(f"{pre}c{lvl[0]}", dw * DD)
        if coded:
            m.assign(s, f"{x_} ^ {y_} ^ {z_}")
            cm = m.wire(f"{pre}cm{lvl[0]}", 4 * DD, expr=f"({x_} & {y_}) | ({x_} & {z_}) | ({y_} & {z_})")
            if code == "bcd4221":
                c5 = m.wire(f"{pre}c5_{lvl[0]}", 4 * DD)
                for i in range(DD):
                    m.assign(dig(c5, i), f"T4to5[({dig(cm, i)}) * 4 +: 4]")
                m.assign(c, f"{{{c5}[{4*DD-2}:0], 1'b0}}")            # the doubled carry word, back in 4221
            else:
                c4 = m.wire(f"{pre}c4_{lvl[0]}", 4 * DD, expr=f"{{{cm}[{4*DD-2}:0], 1'b0}}")   # 5211 shifted: 4221
                for i in range(DD):
                    m.assign(dig(c, i), f"T4to5b[({dig(c4, i)}) * 4 +: 4]")
            return s, c
        m.assign(cell(c, 0), tree_zero)
        for i in range(DD):
            if sd_code:
                f = m.wire(m.fresh("f"), 7, signed=True, expr=f"$signed({cell(x_, i)}) + $signed({cell(y_, i)}) + $signed({cell(z_, i)})")
                t = m.wire(m.fresh("t"), 5, signed=True,
                           expr=f"({f} >= 7'sd25) ? 5'sd3 : ({f} >= 7'sd15) ? 5'sd2 : ({f} >= 7'sd5) ? 5'sd1 : "
                                f"({f} > -7'sd5) ? 5'sd0 : ({f} > -7'sd15) ? -5'sd1 : ({f} > -7'sd25) ? -5'sd2 : -5'sd3")
                m.assign(cell(s, i), f"{f}[4:0] - ({t} * 5'sd10)")
                if i + 1 < DD:
                    m.assign(cell(c, i + 1), t)
            elif xs3:
                f = m.wire(m.fresh("f"), 6, expr=f"{{2'b0, {cell(x_, i)}}} + {{2'b0, {cell(y_, i)}}} + {{2'b0, {cell(z_, i)}}}")
                cd = m.wire(m.fresh("cd"), 4, expr=f"({f} >= 6'd40) ? 4'd4 : ({f} >= 6'd30) ? 4'd3 : ({f} >= 6'd20) ? 4'd2 : ({f} >= 6'd10) ? 4'd1 : 4'd0")
                m.assign(cell(s, i), f"{f}[3:0] - ({cd} * 4'd10)")
                if i + 1 < DD:
                    m.assign(cell(c, i + 1), cd)
            else:
                f = m.wire(m.fresh("f"), 5, expr=f"{{1'b0, {cell(x_, i)}}} + {{1'b0, {cell(y_, i)}}} + {{1'b0, {cell(z_, i)}}}")
                cd = m.wire(m.fresh("cd"), 2, expr=f"({f} >= 5'd20) ? 2'd2 : ({f} >= 5'd10) ? 2'd1 : 2'd0")
                m.assign(cell(s, i), f"({f} >= 5'd20) ? ({f}[3:0] - 4'd4) : ({f} >= 5'd10) ? ({f}[3:0] - 4'd10) : {f}[3:0]")
                if i + 1 < DD:
                    m.assign(cell(c, i + 1), f"{{2'b0, {cd}}}")
        return s, c

    def counter(group: list) -> tuple:
        lvl[0] += 1
        s = m.wire(f"{pre}s{lvl[0]}", dw * DD)
        c = m.wire(f"{pre}c{lvl[0]}", dw * DD)
        m.assign(cell(c, 0), tree_zero)
        for i in range(DD):
            f = m.wire(m.fresh("f"), 7, expr=" + ".join(f"{{3'b0, {cell(r, i)}}}" for r in group))
            cd = m.wire(m.fresh("cd"), 4, expr=f"{f} / 7'd10")
            m.assign(cell(s, i), f"{f}[3:0] - ({cd} * 4'd10)")
            if i + 1 < DD:
                m.assign(cell(c, i + 1), cd)
        return s, c

    def to_bcd_word(w: str, name: str) -> str:
        o = m.wire(name, 4 * DD)
        for i in range(DD):
            if code == "bcd4221":
                m.assign(dig(o, i), f"V4221[({cell(w, i)}) * 4 +: 4]")
            elif code == "bcd5211":
                m.assign(dig(o, i), f"V5211[({cell(w, i)}) * 4 +: 4]")
            else:
                m.assign(dig(o, i), cell(w, i))
        return o

    if tree == "binary_tree" and not (sd_code or xs3):
        m.comment_line("a binary tree of decimal carry-propagate adders over the rows" + (" (converted to BCD)" if coded else ""))
        cur = [to_bcd_word(r, f"{pre}rb{k}") if coded else r for k, r in enumerate(rows)]
        k = 0
        while len(cur) > 1:
            nxt = []
            for j in range(0, len(cur) - 1, 2):
                k += 1
                nxt.append(_bcd_adder_inst(m, DD, tpins or fpins, cur[j], cur[j + 1], f"{pre}bt{k}", f"tree adder {k}"))
            if len(cur) % 2:
                nxt.append(cur[-1])
            cur = nxt
        m.wire(out, 4 * DD, expr=cur[0])
        return out
    if tree == "binary_tree":
        m.comment_line("the signed-digit and excess-3 rows have no carry-propagate form of their own: a chain of 3:2 compressors")
        tree = "linear_chain"
    if len(rows) == 1:
        rows.append(m.wire(f"{pre}zrow", dw * DD, expr="{" + f"{DD}{{{tree_zero}}}" + "}"))
    if tree == "linear_chain":
        m.comment_line("a linear chain of the domain's 3:2 compressors (the carry-save array)")
        s, c = rows[0], rows[1]
        for r in rows[2:]:
            s, c = csa32(s, c, r)
        final = [s, c]
    else:
        m.comment_line(f"a carry-save tree of {comp} compressors over the rows, level by level")
        cur = list(rows)
        while len(cur) > 2:
            nxt = []
            if comp == "7:3" and not (coded or sd_code):
                while len(cur) >= 3:
                    grp, cur = cur[:7], cur[7:]
                    nxt += list(counter(grp))
                nxt += cur
            elif comp == "4:2":
                while len(cur) >= 4:
                    x_, y_, z_, w_, cur = cur[0], cur[1], cur[2], cur[3], cur[4:]
                    s1, c1 = csa32(x_, y_, z_)
                    nxt += list(csa32(s1, c1, w_))
                if len(cur) == 3:
                    nxt += list(csa32(*cur))
                    cur = []
                nxt += cur
            else:
                while len(cur) >= 3:
                    x_, y_, z_, cur = cur[0], cur[1], cur[2], cur[3:]
                    nxt += list(csa32(x_, y_, z_))
                nxt += cur
            cur = nxt
        final = cur
    xw, yw = final
    if sd_code:
        m.comment_line("the final chain over signed digits: a carry of -2..1 per digit, the digits reduced to 0..9")
        cc = m.wire(f"{pre}fc", 5 * (DD + 1))
        o = m.wire(out, 4 * DD)
        m.assign(f"{cc}[4:0]", "5'd0")
        for i in range(DD):
            v = m.wire(m.fresh("fv"), 7, signed=True, expr=f"$signed({cell(xw, i)}) + $signed({cell(yw, i)}) + $signed({cc}[{5*i+4}:{5*i}])")
            cq = m.wire(m.fresh("fq"), 5, signed=True, expr=f"({v} >= 7'sd10) ? 5'sd1 : ({v} >= 7'sd0) ? 5'sd0 : ({v} >= -7'sd10) ? -5'sd1 : -5'sd2")
            m.assign(f"{cc}[{5*i+9}:{5*i+5}]", cq)
            m.assign(dig(o, i), f"{v}[3:0] - ({cq}[3:0] * 4'd10)")
        return out
    if xs3:
        m.comment_line("the final chain over overloaded digits: a carry of 0..3 per digit")
        cc = m.wire(f"{pre}fc", 2 * (DD + 1))
        o = m.wire(out, 4 * DD)
        m.assign(f"{cc}[1:0]", "2'd0")
        for i in range(DD):
            v = m.wire(m.fresh("fv"), 6, expr=f"{{2'b0, {cell(xw, i)}}} + {{2'b0, {cell(yw, i)}}} + {{4'b0, {cc}[{2*i+1}:{2*i}]}}")
            cq = m.wire(m.fresh("fq"), 2, expr=f"({v} >= 6'd30) ? 2'd3 : ({v} >= 6'd20) ? 2'd2 : ({v} >= 6'd10) ? 2'd1 : 2'd0")
            m.assign(f"{cc}[{2*i+3}:{2*i+2}]", cq)
            m.assign(dig(o, i), f"{v}[3:0] - ({{2'b0, {cq}}} * 4'd10)")
        return out
    if coded:
        xw, yw = to_bcd_word(xw, f"{pre}fx"), to_bcd_word(yw, f"{pre}fy")
    _bcd_adder_inst(m, DD, tpins or fpins, xw, yw, out, "the final adder" + (" (the reduction tree's CPA)" if tpins else ""))
    return out


def _mul_sv(D: int, pins: dict, name: str | None) -> tuple:
    rec = str(_pin(pins, "multiplier_recoding", "sd_radix10_m5_p5"))
    code = str(_pin(pins, "internal_digit_code", "bcd8421"))
    ppg = str(_pin(pins, "pp_generation", "precomputed_multiples_mux"))
    tree = str(_pin(pins, "reduction_tree.family", "linear_chain"))
    W = 4 * D
    name = name or f"fam_bcd_mul_{_sfx(rec)[:9]}_{_sfx(code)[:7]}_{_sfx(ppg)[:5]}_{_sfx(tree)[:6]}_d{D}{_ptag(pins)}"
    m = Mod(name, f"parallel_decimal_multiplication: multiplier recoding {rec}, partial products by {ppg}, "
                  f"the rows in {code}, reduced by a {tree} ({_pin(pins, 'reduction_tree.compressor', '3:2')}), "
                  f"final adder {_pin(pins, 'final_adder.family', 'ripple_carry')}")
    m.port("input", "a", W)
    m.port("input", "b", W)
    m.port("output", "p", 2 * W)
    _mul_core(m, "a", D, "b", D, pins, "pf")
    m.assign("p", "pf")
    return name, m.render()


def bcd_mul_sv(D: int, family: str, pins: dict, name: str | None = None) -> tuple:
    """(module name, text) of a decimal multiplier family at D digits."""
    pins = pins or {}
    if family == "parallel_decimal_multiplication":
        return _mul_sv(D, pins, name)
    raise ValueError(f"decimal multiplier family {family!r}: parallel_decimal_multiplication")


# ---- the dividers -------------------------------------------------------------------------
def _normalize_digits(m: Mod, D: int, src: str, pre: str) -> tuple:
    """(bn, k): src shifted left by its k leading zero digits (src != 0),
    k as a binary count."""
    KW = _clog2(D + 1)
    arms = " : ".join(f"({dig(src, D - 1 - i)} != 4'd0) ? {KW}'d{i}" for i in range(D - 1))
    k = m.wire(f"{pre}k", KW, expr=f"{arms} : {KW}'d{D-1}" if D > 1 else f"{KW}'d0")
    bn = m.wire(f"{pre}bn", 4 * D, expr=f"{src} << {{{k}, 2'b00}}")
    return bn, k


def _bcd_to_bin(m: Mod, digits: list, out: str, width: int) -> str:
    """out = the binary value of a few BCD digits (digits[0] the units)."""
    terms = [f"({width}'({d}) * {width}'d{10 ** i})" for i, d in enumerate(digits)]
    return m.wire(out, width, expr=" + ".join(terms))


def _sd_to_bcd_chain(m: Mod, n: int, sd: list, borrow_in: str, out: str) -> str:
    """out (n digits) = (sum of the signed digits sd[i] 10^i - borrow_in)
    through a borrow-propagate chain (the positive part less the negative
    part); the result is taken nonnegative."""
    bw = m.wire(m.fresh("qbw"), n + 1)
    m.assign(f"{bw}[0]", borrow_in)
    o = m.wire(out, 4 * n)
    for i in range(n):
        v = sd[i]
        pp = f"({v}[4] ? 5'd0 : {v})"
        nn = f"({v}[4] ? (5'd0 - {v}) : 5'd0)"
        tt = m.wire(m.fresh("qcv"), 5, expr=f"{pp} - {nn} - {{4'b0, {bw}[{i}]}}")
        m.assign(f"{bw}[{i+1}]", f"{tt}[4]")
        m.assign(dig(o, i), f"{tt}[4] ? ({tt}[3:0] + 4'd10) : {tt}[3:0]")
    return o


def _beh_mul_fn(m: Mod, DA: int, DB: int) -> str:
    """A behavioral decimal product function (DA x DB digits): the digit
    products summed per column, the columns carried; the structure is
    left to synthesis, as the operator is for the binary functional
    dividers whose multiplier component is undeclared."""
    N = DA + DB
    name = f"bmul_{DA}x{DB}"
    if name in m.fns:
        return name
    m.fns.add(name)
    m.raw(f"""  // the multiplier component undeclared: a behavioral decimal product ({DA} x {DB} digits: the digit products
  // summed per column, the columns carried), its structure left to synthesis
  function automatic [{4*N-1}:0] {name}(input [{4*DA-1}:0] x, input [{4*DB-1}:0] y);
    logic [{12*N-1}:0] acc; logic [11:0] tot; integer i, j, k;
    acc = 0;
    for (i = 0; i < {DB}; i = i + 1) for (j = 0; j < {DA}; j = j + 1)
      acc[12*(i+j) +: 12] = acc[12*(i+j) +: 12] + x[4*j +: 4] * y[4*i +: 4];
    tot = 0;
    for (k = 0; k < {N}; k = k + 1) begin
      tot = tot + acc[12*k +: 12];
      {name}[4*k +: 4] = tot % 12'd10; tot = tot / 12'd10;
    end
  endfunction""")
    return name


def _mul_inst(m: Mod, x: str, DA: int, y: str, DB: int, pins: dict, out: str, pre: str) -> str:
    """out (DA + DB digits) = x * y: through the decimal multiplier of the
    declared multiplier pins (`multiplier.*`: parallel_decimal_multiplication's
    choices), else the behavioral decimal product (the netlist of a
    partial-product tree per multiply would dominate the divider and its
    simulation)."""
    if not pins:
        fn = _beh_mul_fn(m, DA, DB)
        return m.wire(out, 4 * (DA + DB), expr=f"{fn}({x}, {y})")
    return _mul_core(m, x, DA, y, DB, pins, out, pre=pre)


def _recurrence_sv(D: int, pins: dict, name: str | None, mpins: dict) -> tuple:
    qset = str(_pin(pins, "quotient_digit_set", "nonredundant_0_9"))
    split = str(_pin(pins, "digit_split", "none")) == "radix2_times_radix5"
    W = 4 * D
    name = name or f"fam_bcd_div_recur_{_sfx(qset)[:9]}_{'split' if split else 'whole'}_d{D}{_ptag(pins)}"
    redundant = qset != "nonredundant_0_9"
    m = Mod(name, f"decimal_digit_recurrence: quotient digits {qset}, digit split {'radix-2 x radix-5' if split else 'none'}, "
                  + ("the divisor prescaled near one (the redundant digit sets select by rounding the residual estimate"
                     + (", the digit split is not applied to the rounding selection" if split else "") + ")"
                     if redundant else "digits by comparison against the divisor's multiples"))
    m.port("input", "a", W)
    m.port("input", "b", W)
    m.port("output", "q", W)
    m.port("output", "r", W)
    if not redundant:
        need = (1, 2, 3, 4, 5) if split else tuple(range(1, 10))
        mult = _multiples(m, "b", D, need, {}, "d")
        wcur = m.wire("w0", 4 * (D + 1), expr=f"{4*(D+1)}'d0")
        for j in range(D):
            t = m.wire(f"t{j}", 4 * (D + 1), expr=f"{{{wcur}[{4*D-1}:0], {dig('a', D - 1 - j)}}}")
            if split:
                h = m.wire(f"h{j}", 1, expr=f"{t} >= {mult[5]}")
                t2 = _bcd_adder_inst(m, D + 1, {}, t, mult[5], f"t2_{j}", f"stage {j}: the radix-2 part (less 5b when it fits)", sub="1'b1")
                tt = m.wire(f"tt{j}", 4 * (D + 1), expr=f"{h} ? {t2} : {t}")
                ge = [m.wire(f"ge{j}_{k}", 1, expr=f"{tt} >= {mult[k]}") for k in (1, 2, 3, 4)]
                l = m.wire(f"l{j}", 4, expr=" + ".join(f"{{3'b0, {g}}}" for g in ge))
                m.assign(dig("q", D - 1 - j), f"({h} ? 4'd5 : 4'd0) + {l}")
                sel = m.wire(f"sel{j}", 4 * (D + 1),
                             expr=" : ".join(f"({l} == 4'd{k}) ? {mult[k]}" for k in (1, 2, 3, 4)) + f" : {4*(D+1)}'d0")
                wn = _bcd_adder_inst(m, D + 1, {}, tt, sel, f"w{j+1}", f"stage {j}: the residual less the radix-5 multiple", sub="1'b1")
            else:
                ge = [m.wire(f"ge{j}_{k}", 1, expr=f"{t} >= {mult[k]}") for k in range(1, 10)]
                qd = m.wire(f"qd{j}", 4, expr=" + ".join(f"{{3'b0, {g}}}" for g in ge))
                m.assign(dig("q", D - 1 - j), qd)
                sel = m.wire(f"sel{j}", 4 * (D + 1),
                             expr=" : ".join(f"({qd} == 4'd{k}) ? {mult[k]}" for k in range(1, 10)) + f" : {4*(D+1)}'d0")
                wn = _bcd_adder_inst(m, D + 1, {}, t, sel, f"w{j+1}", f"stage {j}: the residual less the selected multiple", sub="1'b1")
            wcur = wn
        m.assign("r", f"{wcur}[{W-1}:0]")
        return name, m.render()
    # ---- the redundant digit sets: prescaling, then selection by rounding of the residual estimate
    amax = 5 if qset == "minimally_redundant_m5_p5" else 7
    stages = 2 if amax == 5 else 1
    tfrac = 2 if amax == 5 else 1
    bn, k = _normalize_digits(m, D, "b", "n")
    # stage 1: the factor from the two leading digits d = d1 d2 (>= 10): f1 = 10^4 / d (rounded up for the two-stage
    # scaling, so the scaled divisor starts at 1.0; down for the single stage)
    m.comment_line("prescaling stage 1: a factor of two fraction digits from the two leading digits of the normalized divisor")
    f1 = []
    for pat in range(256):
        d1, d2 = pat >> 4, pat & 15
        d = 10 * d1 + d2
        if d1 == 0 or d1 > 9 or d2 > 9:
            f1.append(0)
        else:
            fi = (10 ** 4 + d - 1) // d if stages == 2 else 10 ** 4 // d
            v = 0
            for i in range(4):
                v |= (fi % 10) << (4 * i)
                fi //= 10
            f1.append(v)
    m.rom("F1", f1, 16, f"{{{dig(bn, D - 1)}, {dig(bn, D - 2) if D > 1 else chr(52) + chr(39) + 'd0'}}}", "f1", "the stage-1 factors (BCD, 4 digits)")
    b1 = _mul_inst(m, bn, D, "f1", 4, mpins, "b1", "s1b_")
    a1 = _mul_inst(m, "a", D, "f1", 4, mpins, "a1", "s1a_")
    Ftot = 2
    bs, as_ = b1, a1
    if stages == 2:
        # stage 2: the scaled divisor is 1.xyz...: a factor from the three digits after the leading one
        m.comment_line("prescaling stage 2: a factor of three fraction digits from the three digits after the leading one")
        idx = _bcd_to_bin(m, [dig(b1, D - 1), dig(b1, D), dig(b1, D + 1)], "idx2", 8)
        f2 = []
        for i in range(128):
            fi = 10 ** 6 // (1000 + i) if i <= 111 else 0
            v = 0
            for j in range(4):
                v |= (fi % 10) << (4 * j)
                fi //= 10
            f2.append(v)
        m.rom("F2", f2, 16, "idx2[6:0]", "f2", "the stage-2 factors (BCD, 4 digits)")
        bs = _mul_inst(m, b1, D + 4, "f2", 4, mpins, "b2", "s2b_")
        as_ = _mul_inst(m, a1, D + 4, "f2", 4, mpins, "a2", "s2a_")
        Ftot = 5
    # the scaled operands: b'' = 10 b' (the leading quotient digit's weight), P digits in tens' complement
    P = D + Ftot + 3
    bpp = m.wire("bpp", 4 * (P - 1), expr=f"{{{bs}[{4*(D+Ftot+1)-1}:0], 4'd0}}")   # D+Ftot+2 digits = P-1
    v0 = m.wire("v0", 4 * P, expr=f"{{{{{4*(P-(D+Ftot+1))}{{1'b0}}}}, {as_}[{4*(D+Ftot+1)-1}:0]}}")
    mult = _multiples(m, bpp, P - 1, tuple(range(1, amax + 1)), {}, "r")
    m.comment_line(f"the recurrence: {D + 2} quotient digits in -{amax}..{amax} by rounding the residual's top {2 + tfrac} digits "
                   f"(tens' complement), the residual v' = 10 (v - q b'')")
    lo = D + Ftot + 1 - tfrac                     # the residual digit position of the estimate's lowest digit
    ne = P - lo
    sdq = []
    vcur = v0
    EW = 16
    for j in range(D + 2):
        est = _bcd_to_bin(m, [dig(vcur, lo + i) for i in range(ne)], f"est{j}", EW)
        sv = m.wire(f"sv{j}", EW, signed=True, expr=f"({dig(vcur, P - 1)} >= 4'd5) ? $signed({est}) - {EW}'sd{10 ** ne} : $signed({est})")
        half = 5 * 10 ** (tfrac - 1)
        hv = m.wire(f"hv{j}", EW, signed=True, expr=f"{sv} + {EW}'sd{half}")
        qf = m.wire(f"qf{j}", EW, signed=True,
                    expr=f"({hv} >= {EW}'sd0) ? ({hv} / {EW}'sd{10 ** tfrac}) : -((-{hv} + {EW}'sd{10 ** tfrac - 1}) / {EW}'sd{10 ** tfrac})")
        qc = m.wire(f"qc{j}", 5, signed=True, expr=f"({qf} > {EW}'sd{amax}) ? 5'sd{amax} : ({qf} < -{EW}'sd{amax}) ? -5'sd{amax} : {qf}[4:0]")
        sdq.append(qc)
        sgn = m.wire(f"qs{j}", 1, expr=f"{qc}[4]")
        mag = m.wire(f"qm{j}", 4, expr=f"{sgn} ? (4'd0 - {qc}[3:0]) : {qc}[3:0]")
        sel = m.wire(f"rsel{j}", 4 * P, expr=" : ".join(f"({mag} == 4'd{kk}) ? {mult[kk]}" for kk in range(1, amax + 1)) + f" : {4*P}'d0")
        vs = _bcd_adder_inst(m, P, {}, vcur, sel, f"vs{j}", f"step {j}: v -/+ |q| b''", sub=f"~{sgn}")
        vcur = m.wire(f"v{j+1}", 4 * P, expr=f"{{{vs}[{4*(P-1)-1}:0], 4'd0}}")
    neg_last = m.wire("neg_last", 1, expr=f"{dig(vcur, P - 1)} >= 4'd5")
    # the quotient digits (the first at the highest weight) to BCD, less one for a negative final residual
    qd = _sd_to_bcd_chain(m, D + 2, list(reversed(sdq)), neg_last, "qd")
    # Q = floor(Q_D / 10^(D - k)): a digit shift right by D - k
    KW = _clog2(D + 1)
    sh = m.wire("qsh", KW + 1, expr=f"{KW+1}'d{D} - {{1'b0, {k}}}")
    qshift = m.wire("qshift", 4 * (D + 2), expr=f"{qd} >> {{{sh}, 2'b00}}")
    m.assign("q", f"{qshift}[{W-1}:0]")
    # the remainder by the back-multiplied quotient
    qb = _mul_inst(m, "q", D, "b", D, mpins, "qb", "bm_")
    rr = _bcd_adder_inst(m, D, {}, "a", f"qb[{W-1}:0]", "rr", "the remainder a - q b", sub="1'b1")
    m.assign("r", rr)
    return name, m.render()


def _newton_sv(D: int, pins: dict, name: str | None, mpins: dict) -> tuple:
    s_pin = _ipin(pins, "seed_digits", 2)
    s = max(1, min(3, D, s_pin))
    n_pin = _ipin(pins, "iterations", 2)
    fr = str(_pin(pins, "final_round.family", "back_multiply_remainder"))
    exclusion = fr in ("exclusion_zone_proof", "extra_precision_quotient")
    P = (2 * D + 3) if exclusion else (D + 3)
    # the iteration count from the seed's error bound: e0 <= 10^-(s-1) relative, e' = e^2 + 11 10^-P per step
    e = Fraction(1, 10 ** (s - 1)) + Fraction(1, 10 ** P)
    target = Fraction(1, 10 ** (D + 1)) if not exclusion else Fraction(1, 2 * 10 ** (2 * D + 1))
    errs = [e]
    while errs[-1] > target and len(errs) < 8:
        errs.append(errs[-1] ** 2 + Fraction(11, 10 ** P))
    n_need = len(errs) - 1
    n = n_pin if (n_pin < len(errs) and errs[n_pin] <= target) or n_pin >= n_need else n_need
    W = 4 * D
    name = name or f"fam_bcd_div_newton_s{s}_i{n}_{_sfx(fr)[:5]}_d{D}{_ptag(pins)}"
    m = Mod(name, f"decimal_newton: reciprocal seed from the {s} leading digits of the normalized divisor"
                  + (f" (the pin asks for {s_pin}: capped at 3 and at the digit count)" if s_pin != s else "")
                  + f", {n} iterations x(2 - bx) on decimal multipliers at {P} fraction digits"
                  + (f" (the pin asks for {n_pin}: the seed's error bound 10^-{s-1} needs {n_need})" if n != n_pin else "")
                  + f", quotient estimate a x, final rounding {fr}")
    m.port("input", "a", W)
    m.port("input", "b", W)
    m.port("output", "q", W)
    m.port("output", "r", W)
    bn, k = _normalize_digits(m, D, "b", "n")
    idx = _bcd_to_bin(m, [dig(bn, D - 1 - i) for i in reversed(range(s))], "sidx", 4 * s)
    XD = P + 2                      # the digits of the reciprocal (units of 10^-P, value up to 10)
    seed = []
    for d in range(10 ** s):
        if d < 10 ** (s - 1):
            seed.append(0)
            continue
        x0 = 10 ** (P + s) // d
        v = 0
        for i in range(XD):
            v |= (x0 % 10) << (4 * i)
            x0 //= 10
        seed.append(v)
    m.rom("SEED", seed, 4 * XD, f"sidx", "x0", f"the reciprocal seed table over the {s} leading digits ({XD} BCD digits)")
    x = "x0"
    two = m.wire("two", 4 * XD, expr=bcd_const(2 * 10 ** P, XD))
    for i in range(n):
        m.comment_line(f"iteration {i}: t = b x, u = 2 - t, x = x u, each product truncated to {P} fraction digits")
        t = _mul_inst(m, bn, D, x, XD, mpins, f"tn{i}", f"it{i}t_")
        tp = m.wire(f"tp{i}", 4 * XD, expr=f"{t}[{4*(D+XD)-1}:{4*D}]")
        u = _bcd_adder_inst(m, XD, {}, two, tp, f"un{i}", f"iteration {i}: 2 - t", sub="1'b1")
        xu = _mul_inst(m, x, XD, u, XD, mpins, f"xu{i}", f"it{i}x_")
        x = m.wire(f"x{i+1}", 4 * XD, expr=f"{xu}[{4*(P+XD)-1}:{4*P}]")
    # the quotient estimate: floor(a x 10^k / 10^(D+P)); the exclusion-zone families bias the estimate up by two units
    # of the (D+1)th fraction digit, which covers the estimate's downward error and stays inside the gap between the
    # quotient's exact fractions (multiples of 1/b) and the next integer
    y = _mul_inst(m, "a", D, x, XD, mpins, "y", "q_")
    KW = _clog2(D + 1)
    if exclusion:
        G = D + 1
        sh = m.wire("ysh", KW + 3, expr=f"{KW+3}'d{P - 1} - {{3'b0, {k}}}")
        ye = m.wire("ye", 4 * (D + XD), expr=f"{y} >> {{{sh}, 2'b00}}")
        yb = _bcd_adder_inst(m, D + G, {}, f"ye[{4*(D+G)-1}:0]", bcd_const(2, D + G), "yb", "the estimate biased up by two units")
        m.assign("q", f"{yb}[{4*(D+G)-1}:{4*G}]")
    else:
        sh = m.wire("ysh", KW + 3, expr=f"{KW+3}'d{D + P} - {{3'b0, {k}}}")
        ye = m.wire("ye", 4 * (D + XD), expr=f"{y} >> {{{sh}, 2'b00}}")
        qe = m.wire("qe", W, expr=f"{ye}[{W-1}:0]")
    qsrc = "q" if exclusion else "qe"
    qb = _mul_inst(m, qsrc, D, "b", D, mpins, "qb", "bm_")
    rr = _bcd_adder_inst(m, D, {}, "a", f"qb[{W-1}:0]", "rr", "the remainder a - q b (tens' complement)", sub="1'b1")
    if exclusion:
        m.assign("r", rr)
        return name, m.render()
    # the back-multiply correction: a negative remainder gives q - 1 and r + b, one of b or more q + 1 and r - b
    m.comment_line("the back-multiply correction: a negative remainder -> q - 1, r + b; a remainder of b or more -> q + 1, r - b")
    neg = m.wire("rneg", 1, expr="~rr_c")
    rp = _bcd_adder_inst(m, D, {}, "rr", "b", "rp", "r + b")
    rm = _bcd_adder_inst(m, D, {}, "rr", "b", "rm", "r - b", sub="1'b1")
    big = m.wire("rbig", 1, expr="rm_c & ~rneg")
    one = m.wire("one", W, expr=bcd_const(1, D))
    qm1 = _bcd_adder_inst(m, D, {}, "qe", "one", "qm1", "q - 1", sub="1'b1")
    qp1 = _bcd_adder_inst(m, D, {}, "qe", "one", "qp1", "q + 1")
    m.assign("q", f"{neg} ? {qm1} : {big} ? {qp1} : qe")
    m.assign("r", f"{neg} ? {rp} : {big} ? {rm} : rr")
    return name, m.render()


def bcd_div_sv(D: int, family: str, pins: dict, name: str | None = None) -> tuple:
    """(module name, text) of a decimal divider family at D digits; the
    multiplications inside (prescaling, the Newton steps, the back-multiply)
    go through parallel_decimal_multiplication's structure when `multiplier.*`
    pins name its choices (`multiplier.family` alone selects its defaults),
    else through a behavioral decimal product left to synthesis."""
    pins = pins or {}
    # the multiplications go through the decimal multiplier of the `multiplier` slot when the slot names its family
    # (its pins follow), else through the behavioral decimal product: a partial-product tree per multiply dominates
    # the divider's netlist, and a Newton divider instantiates several (the binary functional dividers' rule,
    # families/div.py `umul`); the module comment records which
    mpins = {}
    if _pin(pins, "multiplier.family", None):
        mpins = {k: v for k, v in _sub_pins(pins, "multiplier.").items() if k != "family"} or {"pp_generation": "precomputed_multiples_mux"}
    if family == "decimal_digit_recurrence":
        return _recurrence_sv(D, pins, name, mpins)
    if family == "decimal_newton":
        return _newton_sv(D, pins, name, mpins)
    raise ValueError(f"decimal divider family {family!r}: one of {DECIMAL_FAMILIES['divider']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="emit a decimal family module")
    ap.add_argument("--digits", type=int, required=True)
    ap.add_argument("--kind", default="adder", choices=("adder", "multiplier", "divider"))
    ap.add_argument("--family", default=None)
    ap.add_argument("--pins", default="", help="k=v,k=v")
    ap.add_argument("--sv", default=None)
    args = ap.parse_args(argv)
    pins = {}
    for kv in [x for x in args.pins.split(",") if x]:
        k, v = kv.split("=", 1)
        pins[k] = v
    family = args.family or DECIMAL_FAMILIES[args.kind][0]
    gen = {"adder": bcd_adder_sv, "multiplier": bcd_mul_sv, "divider": bcd_div_sv}[args.kind]
    name, text = gen(args.digits, family, pins)
    if args.sv:
        open(args.sv, "w").write(text)
    else:
        sys.stdout.write(text)
    sys.stderr.write(f"{name}: {len(text)} chars\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
