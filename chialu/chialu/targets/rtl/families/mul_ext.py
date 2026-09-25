"""The multiplier families beyond the partial-product trees of mul.py:

* behavioral_star: p = a * b, the structure left to synthesis;
* squarer: the folded partial-product matrix of x^2 (basic symmetry,
  Booth folding, divide and conquer over the `cross` slot's multiplier),
  signed squares by the sign bit's negative-weight terms, and a
  two-operand product from two squarers by the quarter-square identity
  4ab = (a+b)^2 - (a-b)^2 with the sum, the difference and the final
  subtraction through the `pre_adder` slot;
* truncated_fixed_width: the low columns dropped, a constant, a
  data-dependent or a two-column MMSE correction, the output rounded
  (the product's low half is zero: the ArithmeticError gate governs
  where it applies), the kept columns reduced by the `kept_tree` slot;
* logarithmic_mitchell: leading-one detection through the `lod` slot,
  the operands normalized through the `normalize_shifter` slot, the
  fractions added through the `log_adder` slot, the antilog shift
  through the `antilog_shifter` slot, with Mitchell's corrections
  (Combet's terms, operand decomposition, nearest-one rounding) and the
  exact-MSB hybrid over the `exact` slot's multiplier;
* approximate_compressor: inexact 4:2 cells in the low columns,
  underdesigned 2x2 blocks, the dynamic operand window (DRUM: the
  leading ones through `lod`, the windows through `normalize_shifter`,
  the window product through `core`) or configurable error recovery;
* segmented_grid: square or rectangular segment products through the
  `segment` slot (a segmented grid again under recursion_depth), merged
  by a chain or a tree of `merge_adder` instances or by the `merge_tree`
  reduction;
* redundant_binary_multiplier: AND rows, radix-2 Booth rows (+-a per
  multiplier bit pair) or radix-4 Booth rows as signed-digit rows, a
  binary tree of carry-free redundant adders, one converter.

Every module keeps the tree multipliers' interface:

    module fam_mul_<family>_..._w<W>_<s|u>_p<tag> (input [W-1:0] a, input [W-1:0] b, output [2W-1:0] p);
"""
from __future__ import annotations

from chialu.targets.rtl.families.mul import (Netlist, _add_const, _cols, _tag, column_depths, dedupe_modules,
                                             final_add, pp_and_array, pp_booth, reduce_family)

EXT_FAMILIES = ("behavioral_star", "squarer", "truncated_fixed_width", "logarithmic_mitchell", "approximate_compressor",
                "segmented_grid", "redundant_binary_multiplier")


def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _ipin(pins: dict, key: str, default: int) -> int:
    try:
        return int(_pin(pins, key, default))
    except (TypeError, ValueError):
        return default


def _bpin(pins: dict, key: str, default: bool = False) -> bool:
    v = _pin(pins, key, default)
    return str(v).lower() in ("true", "1", "yes")


def _sub(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _lib_inst(kind: str, family, pins: dict, width: int, signed: bool = False):
    """(instance head, text) of a library module, or (None, None)."""
    from chialu.targets.rtl import families as FAM
    if not family:
        return None, None
    m = None
    if kind == "adder":
        from .binary_cpa import adder_module
        m = adder_module(family, pins, width)
    elif kind == "mul":
        m = FAM.mul_module(family, pins, width, signed)
    elif kind == "lzc":
        m = FAM.lzc_module(family, pins, width)
    elif kind == "shifter":
        m = FAM.shifter_module(family, pins, width)
    if m is None:
        return None, None
    ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
    return f"{m.name} " + (f"#({ps}) " if ps else ""), (m.text or "")


class Mod:
    def __init__(self, name: str, w: int, comment: str, ctrl: tuple = ()):
        self.name, self.w, self.comment = name, w, comment
        self.lines: list = []
        self.extra: list = []
        self.n = 0
        self.ctrl = tuple(ctrl)          # (port name, width) the unit drives beside the operands

    def wire(self, name: str, width: int = 1, signed: bool = False, expr: str | None = None) -> str:
        wd = f"[{width-1}:0] " if width > 1 else ""
        self.lines.append(f"  logic {'signed ' if signed else ''}{wd}{name};" + (f" assign {name} = {expr};" if expr is not None else ""))
        return name

    def assign(self, lhs: str, expr: str):
        self.lines.append(f"  assign {lhs} = {expr};")

    def raw(self, text: str):
        self.lines.append(text)

    def inst(self, kind: str, family, pins: dict, width: int, conns: str, comment: str, signed: bool = False) -> bool:
        head, text = _lib_inst(kind, family, pins, width, signed)
        if head is None:
            return False
        if text:
            self.extra.append(text)
        self.n += 1
        self.lines.append(f"  // {comment}")
        self.lines.append(f"  {head}u{self.n} ({conns});")
        return True

    def add(self, fam, pins: dict, width: int, a: str, b: str, out: str, comment: str, cin: str = "1'b0", sub: bool = False) -> str:
        """out (width + 1 bits) = a + b + cin (a - b under `sub`) through the
        adder family's library module; a family without one is an error."""
        self.wire(out, width + 1)
        if sub:
            self.wire(f"{out}_nb", width, expr=f"~{b}")
            b, cin = f"{out}_nb", "1'b1"
        if not self.inst("adder", fam, pins, width, f".a({a}), .b({b}), .cin({cin}), .s({out}[{width-1}:0]), .cout({out}[{width}])", comment):
            raise ValueError(f"the adder family {fam!r} has no library module at {width} bits")
        return out

    def mul(self, fam, pins: dict, width: int, a: str, b: str, out: str, comment: str, signed: bool = False) -> str:
        """out (2 width bits) = a * b through the multiplier family; behavioral_star is the operator."""
        self.wire(out, 2 * width)
        if fam == "behavioral_star":
            self.lines.append(f"  // {comment} (behavioral_star: the operator)")
            self.assign(out, f"$signed({a}) * $signed({b})" if signed else f"{a} * {b}")
            return out
        if not self.inst("mul", fam, pins, width, f".a({a}), .b({b}), .p({out})", comment, signed):
            raise ValueError(f"the multiplier family {fam!r} has no library module at {width} bits")
        return out

    def lzc(self, fam, pins: dict, width: int, src: str, out: str, comment: str) -> str:
        """out (clog2(width+1) bits) = the leading zeros of src through the counter family."""
        self.wire(out, width.bit_length())
        if not self.inst("lzc", fam, pins, width, f".a({src}), .n({out})", comment):
            raise ValueError(f"the leading-zero counter family {fam!r} has no library module")
        return out

    def shift(self, fam, pins: dict, width: int, src: str, amt: str, op: str, out: str, comment: str) -> str:
        """out (width bits) = src shifted by amt (op: an expression, 0 left,
        1 right logical) through the shifter family (a butterfly at a
        power-of-two width: the datapath is padded to one)."""
        W = width
        if fam == "butterfly_network" and (W & (W - 1)):
            W = 1 << _clog2(W)
        self.wire(out, width)
        src_w = src if W == width else self.wire(f"{out}_x", W, expr=f"{{{{{W - width}{{1'b0}}}}, {src}}}")
        aw = _clog2(W)
        amt_w = self.wire(f"{out}_amt", aw, expr=f"{aw}'({amt})")
        y = out if W == width else self.wire(f"{out}_y", W)
        if not self.inst("shifter", fam, pins, W, f".a({src_w}), .amt({amt_w}), .op({op}), .y({y}), .sticky()", comment):
            raise ValueError(f"the shifter family {fam!r} has no library module")
        if W != width:
            self.assign(out, f"{y}[{width-1}:0]")
        return out

    def render(self) -> str:
        w = self.w
        ctrl = "".join(f"input logic {f'[{cw-1}:0] ' if cw > 1 else ''}{cn}, " for cn, cw in self.ctrl)
        head = [f"// {self.comment}",
                f"module {self.name} ({ctrl}input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);"]
        return "\n".join(head + self.lines + ["endmodule", ""]) + dedupe_modules("".join(self.extra))


def _sfx(w: int, signed: bool, pins: dict) -> str:
    return f"w{w}_{'s' if signed else 'u'}{_tag(pins)}"


# ---- behavioral_star -------------------------------------------------------------------
def behavioral_star_sv(w: int, signed: bool, name: str) -> str:
    m = Mod(name, w, "behavioral_star: p = a * b, the structure left to synthesis")
    m.assign("p", "$signed(a) * $signed(b)" if signed else "a * b")
    return m.render()


# ---- squarer ---------------------------------------------------------------------------
def square_cols(nl: Netlist, x: str, n: int, scheme: str, pins: dict, signed: bool = False) -> list:
    """The folded partial-product columns of x^2 for an n-bit x:
    basic_symmetry keeps a_i a_j once at weight 2^(i+j+1) and a_i at
    2^(2i); booth_folding recodes x into radix-4 digits first and folds
    the digit products (signed, one's complemented, one constant for the
    signs); divide_and_conquer splits x into halves whose squares fold
    recursively and whose cross product is the `cross` slot's library
    multiplier. A two's complement x contributes -x_top x_j at weight
    2^(n+j) (the complemented term with a folded constant) and x_top at
    2^(2n-2)."""
    cols = _cols(2 * n)
    if scheme == "booth_folding":
        # digits d_k = -2 x[2k+1] + x[2k] + x[2k-1] over the signed extension of x (an unsigned x gains a zero sign)
        n1 = n + (0 if signed else 1)
        K = (n1 + 1) // 2
        xe = f"xb_{x}"
        nl.assigns.append((xe, (f"{{{{{2*K - n}{{{x}[{n-1}]}}}}, {x}}}" if signed else f"{{{{{2*K - n}{{1'b0}}}}, {x}}}") if 2 * K > n else x))
        nl.widths[xe] = max(2 * K, n)
        digs = []
        for k in range(K):
            b2, b1, b0 = f"{xe}[{2*k+1}]", f"{xe}[{2*k}]", (f"{xe}[{2*k-1}]" if k > 0 else "1'b0")
            neg = nl.wire(f"{b2} & ~({b1} & {b0})", "bn")                         # the digit is negative
            one = nl.wire(f"{b1} ^ {b0}", "bo")                                    # |d| == 1
            two = nl.wire(f"({b2} & ~{b1} & ~{b0}) | (~{b2} & {b1} & {b0})", "bt")  # |d| == 2
            digs.append((neg, one, two))
        const = 0
        for i in range(K):
            for j in range(i, K):
                ni, oi, ti = digs[i]
                nj, oj, tj = digs[j]
                c = 2 * (i + j) + (1 if i != j else 0)           # weight 4^(i+j), doubled for a cross term
                # |d_i d_j| in {0, 1, 2, 4}: bits m0 (1), m1 (2), m2 (4); the sign is the xor of the signs
                m0 = nl.wire(f"{oi} & {oj}", "sq")
                m1 = nl.wire(f"({oi} & {tj}) | ({ti} & {oj})", "sq")
                m2 = nl.wire(f"{ti} & {tj}", "sq")
                s = nl.wire(f"({ni} ^ {nj}) & ({oi} | {ti}) & ({oj} | {tj})", "sq")
                # the signed value -8 s + (m2 m1 m0 xor s) + s: as ~s at the top with the constant -8 folded
                for k, mk in enumerate((m0, m1, m2)):
                    if c + k < 2 * n:
                        cols[c + k].append(nl.wire(f"{mk} ^ {s}", "sq"))
                if c < 2 * n:
                    cols[c].append(s)                          # the +1 of the two's complement
                if c + 3 < 2 * n:
                    cols[c + 3].append(nl.wire(f"~{s}", "sq"))
                const -= 1 << (c + 3)
        _add_const(cols, const)
        return cols
    if scheme == "divide_and_conquer" and n >= 4:
        h = n // 2
        hi_w = n - h
        xl, xh = f"xl_{x}", f"xh_{x}"
        nl.assigns.append((xl, f"{x}[{h-1}:0]"))
        nl.widths[xl] = h
        nl.assigns.append((xh, f"{x}[{n-1}:{h}]"))
        nl.widths[xh] = hi_w
        lo = square_cols(nl, xl, h, "basic_symmetry", pins, False)
        hi = square_cols(nl, xh, hi_w, "basic_symmetry", pins, signed)
        for c, bits in enumerate(lo):
            cols[c].extend(bits)
        for c, bits in enumerate(hi):
            if c + 2 * h < 2 * n:
                cols[c + 2 * h].extend(bits)
        # the cross product 2 xh xl at weight 2^(h+1) through the cross slot's multiplier (the high half signed
        # for a two's complement x: the multiplier runs on the wider width with xl zero-extended and xh
        # sign-extended, as a signed product)
        from chialu.targets.rtl import families as FAM
        fam = str(_pin(pins, "cross.family", "direct_pp_parallel"))
        W = max(h, hi_w) + (1 if signed else 0)
        m = FAM.mul_module(fam, _sub(pins, "cross."), W, signed)
        if m is None:
            raise ValueError(f"the cross multiplier family {fam!r} has no library module")
        pw = f"xp_{x}"
        xle = xl if W == h else f"{{{{{W - h}{{1'b0}}}}, {xl}}}"
        xhe = xh if W == hi_w else (f"{{{{{W - hi_w}{{{xh}[{hi_w-1}]}}}}, {xh}}}" if signed else f"{{{{{W - hi_w}{{1'b0}}}}, {xh}}}")
        nl.widths[pw] = 2 * W                      # declared by the render, driven by the instance
        ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
        nl.insts.append(f"  // the cross product of the halves ({fam})")
        nl.insts.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u_cross_{x} (.a({xle}), .b({xhe}), .p({pw}));")
        if m.text:
            nl.extra.append(m.text)
        # a signed cross product is sign-extended over the remaining columns: ~top with a folded constant
        top = 2 * W - 1
        const = 0
        for k in range(2 * W):
            wt = k + h + 1
            if wt >= 2 * n:
                break
            if signed and k == top:
                cols[wt].append(nl.wire(f"~{pw}[{k}]", "sq"))
                const -= 1 << wt
            else:
                cols[wt].append(f"{pw}[{k}]")
        _add_const(cols, const)
        return cols
    # basic symmetry
    top = n - 1
    const = 0
    for i in range(n):
        if signed and i == top:
            cols[2 * i].append(f"{x}[{i}]")                  # (-x_top)^2 = x_top at 2^(2n-2)
            continue
        cols[2 * i].append(f"{x}[{i}]")
        for j in range(i + 1, n):
            wt = i + j + 1
            if wt >= 2 * n:
                continue
            if signed and j == top:
                # -x_top x_i at 2^(n+i): the complemented term and the constant -2^(n+i)
                cols[wt].append(nl.wire(f"~({x}[{i}] & {x}[{j}])", "sq"))
                const -= 1 << wt
            else:
                cols[wt].append(nl.wire(f"{x}[{i}] & {x}[{j}]", "sq"))
    _add_const(cols, const)
    return cols


def _square_module(w: int, scheme: str, pins: dict, name: str, signed: bool) -> str:
    """module name (input [w-1:0] x, output [2w-1:0] p): the folded squarer."""
    nl = Netlist()
    cols = square_cols(nl, "x", w, scheme, pins, signed)
    cols = reduce_family(nl, cols, pins, "reduction")
    add_lines, add_text = final_add(nl, cols, pins, "reduction.cpa")
    kind = "two's complement" if signed else "unsigned"
    text = [f"module {name} (input logic [{w-1}:0] x, output logic [{2*w-1}:0] p);",
            f"  // squarer ({scheme}, {kind} x): {nl.fa_count} full adders, "
            f"{nl.ha_count} half adders, depth {max(column_depths(nl, cols), default=0)}"]
    text += nl.render()
    text += add_lines
    text.append("endmodule")
    return "\n".join(text) + "\n" + "".join(nl.extra) + add_text


def squarer_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """p = a * b from two squarers by the quarter-square identity: the
    sum and the difference of the operands (signed, w + 1 bits) through
    the pre_adder slot, their squares through signed folded squarers,
    (a+b)^2 - (a-b)^2 = 4ab through the pre_adder slot, the difference
    shifted down by two."""
    scheme = str(_pin(pins, "folding_scheme", "basic_symmetry"))
    afam = str(_pin(pins, "pre_adder.family", "ripple_carry"))
    apins = _sub(pins, "pre_adder.")
    n = w + 2                                   # a + b and a - b of w-bit operands, in two's complement
    sq_name = f"{name}_sq"
    sq_text = _square_module(n, scheme, pins, sq_name, True)
    m = Mod(name, w, f"squarer ({scheme}): the product from two folded squarers by the quarter-square identity "
                     f"4ab = (a+b)^2 - (a-b)^2 (a squarer alone serves x^2); the sum, the difference and the final "
                     f"subtraction through the pre_adder slot ({afam})")
    m.extra.append(sq_text)
    ae = f"{{{{2{{a[{w-1}]}}}}, a}}" if signed else "{2'b0, a}"
    be = f"{{{{2{{b[{w-1}]}}}}, b}}" if signed else "{2'b0, b}"
    m.wire("ae", n, expr=ae)
    m.wire("be", n, expr=be)
    m.add(afam, apins, n, "ae", "be", "sa", "a + b (the sign bit's carry unused)")
    m.add(afam, apins, n, "ae", "be", "da", "a - b", sub=True)
    m.wire("s2", 2 * n)
    m.wire("d2", 2 * n)
    m.raw(f"  {sq_name} u_s (.x(sa[{n-1}:0]), .p(s2));")
    m.raw(f"  {sq_name} u_d (.x(da[{n-1}:0]), .p(d2));")
    m.add(afam, apins, 2 * n, "s2", "d2", "diff", "(a+b)^2 - (a-b)^2", sub=True)
    m.assign("p", f"diff[{2*w+1}:2]")
    return m.render()


# ---- truncated_fixed_width ----------------------------------------------------------
def truncated_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """The n + k most significant partial-product columns formed (k =
    extra_columns_kept), the omitted columns compensated by a constant
    (their expected sum), by the first omitted column's bits carried
    into the kept columns (data_dependent), or by the first two omitted
    columns' bits (the second column's in pairs) with a constant fitted
    as the mean residual over random operands (variable_mmse); the kept
    columns reduced by the kept_tree slot; the sum rounded to the output
    (truncate, round_to_nearest, jam the lsb); the product's low half is
    zero."""
    from fractions import Fraction
    if isinstance(w, bool) or not isinstance(w, int) or w < 1:
        raise ValueError("truncated multiplier width must be a positive integer")
    requested = pins.get("extra_columns_kept", min(2, w))
    if isinstance(requested, bool) or not isinstance(requested, (int, str)):
        raise ValueError("extra_columns_kept must be an integer")
    try:
        k = int(requested)
    except ValueError as error:
        raise ValueError("extra_columns_kept must be an integer") from error
    if not 0 <= k <= 4 or k > w:
        raise ValueError(f"extra_columns_kept={k} must be in 0..4 and fit the actual {w}-bit multiplier")
    corr = str(_pin(pins, "correction_scheme", "constant"))
    rounding = str(_pin(pins, "output_rounding", "truncate"))
    if rounding not in ("truncate", "round_to_nearest", "force_lsb_one_jamming"):
        raise ValueError(f"output_rounding {rounding!r}")
    nl = Netlist()
    full = pp_and_array(nl, w, signed)
    first = w - k                                   # the first kept column
    cols = _cols(2 * w)
    dropped_bits = 0
    for c, bits in enumerate(full):
        if c >= first:
            cols[c].extend(bits)
        else:
            dropped_bits += sum(1 for b in bits if b != "1'b1")
    data_terms = Fraction(0)
    if corr in ("data_dependent", "variable_mmse") and first >= 1:
        # the first omitted column's bits at the kept lsb (each 1 adds 2^first, twice its own weight: the
        # expected value of the pairs below it)
        for b in full[first - 1]:
            if b != "1'b1":
                cols[first].append(b)
                data_terms += Fraction(1 << first, 4)
    pairs2 = []
    if corr == "variable_mmse" and first >= 2:
        # the second omitted column's bits in pairs (both set: 2^(first-1), rounded up to the kept lsb)
        idx2 = [(i, j) for i in range(w) for j in range(w) if i + j == first - 2]
        pairs2 = list(zip(idx2[0::2], idx2[1::2]))
        for (i1, j1), (i2, j2) in pairs2:
            cols[first].append(nl.wire(f"(a[{i1}] & b[{j1}]) & (a[{i2}] & b[{j2}])", "mm"))
            data_terms += Fraction(1 << first, 16)
    units = 0
    if corr in ("constant", "data_dependent", "variable_mmse"):
        # the constant: the expected sum of the omitted columns (a quarter of each bit's weight) less the
        # data-dependent terms' expectation; variable_mmse fits it as the mean residual over random operands
        # (the least-squares intercept of the linear correction), rounded to the kept lsb
        exp = Fraction(0)
        for c, bits in enumerate(full):
            if c < first:
                exp += Fraction((1 << c) * sum(1 for b in bits if b != "1'b1"), 4)
        exp -= data_terms
        if corr == "variable_mmse":
            import random
            rng = random.Random(1)
            tot = 0
            trials = 4096
            for _ in range(trials):
                x, y = rng.randrange(1 << w), rng.randrange(1 << w)
                xa, ya = x, y
                low = 0
                for i in range(w):
                    for j in range(w):
                        if i + j < first and (xa >> i) & 1 and (ya >> j) & 1:
                            low += 1 << (i + j)
                ones1 = sum(1 for i in range(w) for j in range(w) if i + j == first - 1 and (xa >> i) & 1 and (ya >> j) & 1)
                pair2 = sum(1 for (i1, j1), (i2, j2) in pairs2
                            if (xa >> i1) & 1 and (ya >> j1) & 1 and (xa >> i2) & 1 and (ya >> j2) & 1)
                tot += low - ones1 * (1 << first) - pair2 * (1 << first)
            exp = max(Fraction(0), Fraction(tot, trials))
        units = int(round(exp / (1 << first))) if exp > 0 else 0
        _add_const(cols, (units << first) % (1 << (2 * w)))
    if rounding == "round_to_nearest" and w >= 1:
        _add_const(cols, 1 << (w - 1))
    cols = reduce_family(nl, cols, pins, "kept_tree")
    add_lines, add_text = final_add(nl, cols, pins, "kept_tree.cpa")
    text = [f"// truncated_fixed_width: the top {w + k} columns kept, correction {corr}, output {rounding}; "
            f"{dropped_bits} partial-product bits omitted",
            f"// correction_constant_units={units}; first_kept_column={first}",
            f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);",
            f"  logic [{2*w-1}:0] full;"]
    text += nl.render()
    text += [l.replace("assign p =", "assign full =").replace(".s(p)", ".s(full)").replace("(p[", "(full[") for l in add_lines]
    if rounding == "force_lsb_one_jamming":
        text.append("  assign p = 2'b10;" if w == 1 else f"  assign p = {{full[{2*w-1}:{w+1}], 1'b1, {w}'d0}};")
    else:
        text.append(f"  assign p = {{full[{2*w-1}:{w}], {w}'d0}};")
    text.append("endmodule")
    return "\n".join(text) + "\n" + "".join(nl.extra) + add_text


# ---- logarithmic_mitchell ------------------------------------------------------------
class _Log:
    """The slot families of a logarithmic multiplier."""

    def __init__(self, pins: dict, log_add: bool = True):
        self.lod = (str(_pin(pins, "lod.family", "lzd_cell_tree")), _sub(pins, "lod."))
        self.nsh = (str(_pin(pins, "normalize_shifter.family", "barrel_mux_tree")), _sub(pins, "normalize_shifter."))
        # the log_adder and antilog_shifter slots belong to the logarithmic multiplier alone
        self.add = (str(_pin(pins, "log_adder.family", "ripple_carry")), _sub(pins, "log_adder.")) if log_add else ("", {})
        self.ash = (str(_pin(pins, "antilog_shifter.family", "barrel_mux_tree")), _sub(pins, "antilog_shifter.")) if log_add else ("", {})


def _mitchell(m: Mod, x: str, y: str, n: int, out: str, L: _Log, corr: str, tbits: int, tag: str):
    """out (2n bits) ~= x * y for unsigned n-bit x, y by Mitchell's
    algorithm: k = the leading one's position (the lod slot), the bits
    below it the fraction (the normalize_shifter slot), the fractions
    added (the log_adder slot), the antilog shift (the antilog_shifter
    slot)."""
    nw = n.bit_length()
    kw = _clog2(n)
    F = n - 1                                          # fraction bits
    for s, v in (("x", x), ("y", y)):
        m.lzc(L.lod[0], L.lod[1], n, v, f"{tag}lz{s}", f"leading-one detection of {s} ({L.lod[0]})")
        m.wire(f"{tag}k{s}", kw, expr=f"{n-1} - {tag}lz{s}")                # the characteristic
        m.shift(L.nsh[0], L.nsh[1], n, v, f"{tag}lz{s}", "3'd0", f"{tag}sh{s}", f"{s} normalized: the leading one at the top ({L.nsh[0]})")
        if corr == "nearest_one_rounding":
            # the nearest power of two: the bit below the leading one rounds the characteristic up and makes
            # the fraction negative, (x - 2^(k+1)) / 2^(k+1) = (f - 1) / 2 in two's complement {1, 1, f}
            m.wire(f"{tag}up{s}", expr=f"{tag}sh{s}[{n-2}]" if n >= 2 else "1'b0")
            fb = f"{tag}sh{s}[{n-2}:0]" if n >= 2 else "1'b0"
            m.wire(f"{tag}f{s}", F + 2, expr=f"{tag}up{s} ? {{2'b11, {fb}}} : {{1'b0, {fb}, 1'b0}}")
            m.wire(f"{tag}kk{s}", kw + 1, expr=f"{tag}k{s} + {tag}up{s}")
        else:
            m.wire(f"{tag}f{s}", F, expr=f"{tag}sh{s}[{n-2}:0]" if n >= 2 else "1'b0")
    if corr == "nearest_one_rounding":
        m.add(L.add[0], L.add[1], F + 2, f"{tag}fx", f"{tag}fy", f"{tag}fsa", f"the signed fractions added ({L.add[0]})")
        m.wire(f"{tag}fs", F + 2, expr=f"{tag}fsa[{F+1}:0]")                # in (-1, 1), two's complement
        # the antilog mantissa 1 + fs: the constant 2^(F+1) added flips the sign bit
        m.wire(f"{tag}mant", F + 2, expr=f"{{~{tag}fs[{F+1}], {tag}fs[{F}:0]}}")
        m.wire(f"{tag}K", kw + 2, expr=f"{tag}kkx + {tag}kky")
        MW = F + 2
        FS = F + 1                                                           # the mantissa's fraction bits
    else:
        m.add(L.add[0], L.add[1], F, f"{tag}fx", f"{tag}fy", f"{tag}fs", f"the fractions added ({L.add[0]})")   # carry: the sum's integer bit
        m.wire(f"{tag}c", expr=f"{tag}fs[{F}]")
        m.wire(f"{tag}mant", n, expr=f"{{1'b1, {tag}fs[{F-1}:0]}}" if F >= 1 else "1'b1")
        m.wire(f"{tag}K", kw + 2, expr=f"{tag}kx + {tag}ky + {tag}c")
        MW = n
        FS = F
    # the product: mant 2^K / 2^FS, an antilog shift of the mantissa placed at the fraction's scale
    PW = 2 * n + MW
    m.wire(f"{tag}base", PW, expr=f"{{{{({PW}-{MW}){{1'b0}}}}, {tag}mant}}")
    m.shift(L.ash[0], L.ash[1], PW, f"{tag}base", f"{tag}K", "3'd0", f"{tag}shifted", f"the antilog shift ({L.ash[0]})")
    m.wire(f"{tag}prod", 2 * n, expr=f"{tag}shifted[{FS + 2*n - 1}:{FS}]")
    if corr == "combet_error_terms":
        # the missing term of the fractions' product, from a table over their top bits at the mantissa scale
        tb = max(2, min(tbits if tbits > 0 else 4, F))
        hb = (tb + 1) // 2
        lb = tb - hb
        entries = []
        lb1 = lb if lb > 0 else 1
        for c in (0, 1):
            for i in range(1 << hb):
                for j in range(1 << lb1):
                    fa = (i + 0.5) / (1 << hb)
                    fb = (j + 0.5) / (1 << lb1)
                    term = (1 - fa) * (1 - fb) if c else fa * fb
                    entries.append(int(round(term * (1 << tb))))
        ew = tb + 1
        idxw = 1 + hb + lb1
        val = 0
        for i, e in enumerate(entries):
            val |= (e & ((1 << ew) - 1)) << (ew * i)
        ne = len(entries)
        m.raw(f"  localparam [{ne*ew-1}:0] {tag}CT = {ne*ew}'h{val:0{(ne*ew+3)//4}x};")
        m.wire(f"{tag}ci", idxw, expr=f"{{{tag}c, {tag}fx[{F-1}:{F-hb}], {tag}fy[{F-1}:{F-lb1}]}}")
        m.wire(f"{tag}ce", ew, expr=f"{tag}CT[({tag}ci) * {ew} +: {ew}]")
        # the correction at weight 2^(kx + ky) / 2^tb (the mantissa's scale is 2^K / 2^F: F - tb bits up)
        m.wire(f"{tag}cbase", PW, expr=f"{{{{({PW}-{ew}){{1'b0}}}}, {tag}ce}} << {F - tb}")
        m.wire(f"{tag}ksum", kw + 1, expr=f"{tag}kx + {tag}ky")
        m.shift(L.ash[0], L.ash[1], PW, f"{tag}cbase", f"{tag}ksum", "3'd0", f"{tag}csh", f"the correction term placed ({L.ash[0]})")
        m.wire(f"{tag}cterm", 2 * n, expr=f"{tag}csh[{F + 2*n - 1}:{F}]")
        m.add(L.add[0], L.add[1], 2 * n, f"{tag}prod", f"{tag}cterm", f"{tag}pc", f"the product plus Combet's term ({L.add[0]})")
        m.wire(out, 2 * n, expr=f"{tag}pc[{2*n-1}:0]")
    else:
        m.wire(out, 2 * n, expr=f"{tag}prod")


def logarithmic_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    corr = str(_pin(pins, "correction_scheme", "none"))
    tbits = _ipin(pins, "correction_table_bits", 4)
    hybrid = _bpin(pins, "exact_msb_hybrid", False)
    L = _Log(pins)
    m = Mod(name, w, f"logarithmic_mitchell: leading-one detection ({L.lod[0]}), the fraction as the logarithm, one add "
                     f"({L.add[0]}), the antilog shift ({L.ash[0]}); correction {corr}"
                     + ("; the top halves' product exact" if hybrid else "") + " (the ArithmeticError gate governs)")
    if signed:
        m.wire("am", w, expr=f"a[{w-1}] ? -a : a")
        m.wire("bm", w, expr=f"b[{w-1}] ? -b : b")
        m.wire("ps", expr=f"a[{w-1}] ^ b[{w-1}]")
    else:
        m.wire("am", w, expr="a")
        m.wire("bm", w, expr="b")
    m.wire("za", expr="am == 0")
    m.wire("zb", expr="bm == 0")
    if corr == "operand_decomposition":
        # x y = (x & y)(x | y) + (x & ~y)(~x & y): two Mitchell products and one add
        m.wire("oa", w, expr="am & bm")
        m.wire("ob", w, expr="am | bm")
        m.wire("oc", w, expr="am & ~bm")
        m.wire("od", w, expr="~am & bm")
        _mitchell(m, "oa", "ob", w, "p1", L, "none", tbits, "d1_")
        _mitchell(m, "oc", "od", w, "p2", L, "none", tbits, "d2_")
        m.wire("z1", expr="(oa == 0) || (ob == 0)")
        m.wire("z2", expr="(oc == 0) || (od == 0)")
        m.wire("p1z", 2 * w, expr=f"z1 ? {2*w}'d0 : p1")
        m.wire("p2z", 2 * w, expr=f"z2 ? {2*w}'d0 : p2")
        m.add(L.add[0], L.add[1], 2 * w, "p1z", "p2z", "pma", f"the two Mitchell products added ({L.add[0]})")
        m.wire("pm", 2 * w, expr=f"pma[{2*w-1}:0]")
    elif hybrid and w >= 4:
        h = w // 2
        hw = w - h
        m.wire("ah", hw, expr=f"am[{w-1}:{h}]")
        m.wire("bh", hw, expr=f"bm[{w-1}:{h}]")
        m.wire("al", h, expr=f"am[{h-1}:0]")
        m.wire("bl", h, expr=f"bm[{h-1}:0]")
        m.mul(str(_pin(pins, "exact.family", "direct_pp_parallel")), _sub(pins, "exact."), hw, "ah", "bh", "phh", "the exact product of the top halves")
        m.wire("ahe", w, expr=f"{{{{{h}{{1'b0}}}}, ah}}")
        m.wire("ble", w, expr=f"{{{{{hw}{{1'b0}}}}, bl}}")
        m.wire("ale", w, expr=f"{{{{{hw}{{1'b0}}}}, al}}")
        m.wire("bhe", w, expr=f"{{{{{h}{{1'b0}}}}, bh}}")
        c2 = corr if corr != "operand_decomposition" else "none"
        _mitchell(m, "ahe", "ble", w, "phl", L, c2, tbits, "h1_")
        _mitchell(m, "ale", "bhe", w, "plh", L, c2, tbits, "h2_")
        _mitchell(m, "ale", "ble", w, "pll", L, c2, tbits, "h3_")
        m.wire("t0", 2 * w, expr=f"{{phh, {2*h}'d0}}")
        m.wire("t1", 2 * w, expr=f"((ah == 0 || bl == 0) ? {2*w}'d0 : phl) << {h}")
        m.wire("t2", 2 * w, expr=f"((al == 0 || bh == 0) ? {2*w}'d0 : plh) << {h}")
        m.wire("t3", 2 * w, expr=f"(al == 0 || bl == 0) ? {2*w}'d0 : pll")
        m.add(L.add[0], L.add[1], 2 * w, "t0", "t1", "hy1", f"the exact and the first cross term ({L.add[0]})")
        m.add(L.add[0], L.add[1], 2 * w, f"hy1[{2*w-1}:0]", "t2", "hy2", "plus the second cross term")
        m.add(L.add[0], L.add[1], 2 * w, f"hy2[{2*w-1}:0]", "t3", "hy3", "plus the low product")
        m.wire("pm", 2 * w, expr=f"hy3[{2*w-1}:0]")
    else:
        _mitchell(m, "am", "bm", w, "pm", L, corr, tbits, "m_")
    m.wire("pz", 2 * w, expr=f"(za || zb) ? {2*w}'d0 : pm")
    if signed:
        m.assign("p", "ps ? -pz : pz")
    else:
        m.assign("p", "pz")
    return m.render()


# ---- approximate_compressor -----------------------------------------------------------
def _reduce_approx_4_2(nl: Netlist, cols: list, approx_cols: int, unbiased: bool, recovery: int) -> tuple:
    """A Dadda-style reduction whose columns below approx_cols use the
    inexact 4:2 cell (sum = the xor of the four inputs' top pair or-ed
    with the low pair, carry = an or of two ands: Momeni's design 1; the
    unbiased variant alternates the carry rule); the exact columns use
    3:2 counters. Returns (columns, error vector bits per column) where
    the error vector holds the carries the inexact cells dropped, for
    recovery."""
    from chialu.targets.rtl.families.mul import _dadda_targets
    n = len(cols)
    errs = [[] for _ in range(n)]
    h = max(len(c) for c in cols)
    targets = _dadda_targets(h)
    for target in targets:
        new = [[] for _ in range(n)]
        for c in range(n):
            bits = cols[c]
            k = 0
            while len(bits) - k + len(new[c]) > target:
                excess = len(bits) - k + len(new[c]) - target
                if c < approx_cols and len(bits) - k >= 4:
                    x1, x2, x3, x4 = bits[k:k + 4]
                    k += 4
                    # the inexact 4:2 cell: sum ~ (x1 ^ x2) | (x3 ^ x4), carry ~ (x1 & x2) | (x3 & x4)
                    s = nl.wire(f"({x1} ^ {x2}) | ({x3} ^ {x4})", "t")
                    if unbiased:
                        cy = nl.wire(f"({x1} & {x2}) | ({x3} & {x4}) | ({x1} & {x4})", "t")
                    else:
                        cy = nl.wire(f"({x1} & {x2}) | ({x3} & {x4})", "t")
                    new[c].append(s)
                    if c + 1 < n:
                        new[c + 1].append(cy)
                    errs[c].append(nl.wire(f"({x1} & {x2} & {x3}) | ({x2} & {x3} & {x4})", "t"))
                elif excess >= 2 and len(bits) - k >= 3:
                    s, cy = nl.fa(bits[k], bits[k + 1], bits[k + 2])
                    k += 3
                    new[c].append(s)
                    if c + 1 < n:
                        new[c + 1].append(cy)
                elif len(bits) - k >= 2:
                    s, cy = nl.ha(bits[k], bits[k + 1])
                    k += 2
                    new[c].append(s)
                    if c + 1 < n:
                        new[c + 1].append(cy)
                else:
                    break
            new[c].extend(bits[k:])
        cols = new
    if recovery > 0:
        # error recovery: the dropped carries' or, the top `recovery` columns of the approximate region
        # added back one column up
        for c in range(max(0, approx_cols - recovery), approx_cols):
            if errs[c] and c + 1 < n:
                cols[c + 1].append(nl.wire(" | ".join(errs[c]), "t"))
    return cols, errs


def approximate_compressor_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    technique = str(_pin(pins, "technique", "underdesigned_pp_block"))
    seg = max(2, min(_ipin(pins, "segment_width_bits", 6), w))
    unbiased = _bpin(pins, "unbiased_error", False)
    recovery = max(1, _ipin(pins, "error_recovery_stages", 1))
    if technique == "dynamic_segment":
        # DRUM: the window of `seg` bits at each operand's leading one multiplied exactly, the window's lsb set
        # to one to unbias, the product shifted back; signed operands by magnitude
        L = _Log(pins, log_add=False)
        cfam = str(_pin(pins, "core.family", "direct_pp_parallel"))
        m = Mod(name, w, f"approximate_compressor (dynamic_segment, DRUM): a {seg}-bit window at each operand's leading one "
                         f"({L.lod[0]}, {L.nsh[0]}) multiplied exactly ({cfam}), the lsb forced to one, the product shifted "
                         f"back (the ArithmeticError gate governs)")
        if signed:
            m.wire("am", w, expr=f"a[{w-1}] ? -a : a")
            m.wire("bm", w, expr=f"b[{w-1}] ? -b : b")
        else:
            m.wire("am", w, expr="a")
            m.wire("bm", w, expr="b")
        for s in ("a", "b"):
            m.lzc(L.lod[0], L.lod[1], w, f"{s}m", f"lz{s}", f"the leading one of {s} ({L.lod[0]})")
            m.shift(L.nsh[0], L.nsh[1], w, f"{s}m", f"lz{s}", "3'd0", f"sh{s}", f"{s} normalized ({L.nsh[0]})")
            # the window: the top seg bits, the lsb forced to one when bits were dropped below
            m.wire(f"win{s}", seg, expr=f"{{sh{s}[{w-1}:{w-seg+1}], (lz{s} < {w - seg}) ? 1'b1 : sh{s}[{w-seg}]}}" if seg < w else f"sh{s}")
        m.mul(cfam, _sub(pins, "core."), seg, "wina", "winb", "pw", f"the window product ({cfam})")
        SW = 2 * w + 2 * seg
        nw = w.bit_length()
        m.wire("pwe", SW, expr=f"{{{{({SW}-{2*seg}){{1'b0}}}}, pw}}")
        # the product placed back: left by (2w - 2seg) - (lza + lzb) when positive, else right by the excess
        m.wire("lzs", nw + 1, expr="lza + lzb")
        m.wire("left", expr=f"lzs <= {2*w - 2*seg}")
        m.wire("amt", nw + 1, expr=f"left ? ({2*w - 2*seg} - lzs) : (lzs - {2*w - 2*seg})")
        m.shift(L.nsh[0], L.nsh[1], SW, "pwe", "amt", "left ? 3'd0 : 3'd1", "full", f"the window product placed at its scale ({L.nsh[0]})")
        m.wire("pz", 2 * w, expr=f"(am == 0 || bm == 0) ? {2*w}'d0 : full[{2*w-1}:0]")
        if signed:
            m.assign("p", f"(a[{w-1}] ^ b[{w-1}]) ? -pz : pz")
        else:
            m.assign("p", "pz")
        return m.render()
    nl = Netlist()
    if technique == "underdesigned_pp_block":
        # 2x2 inexact blocks (3 x 3 = 7 instead of 9: the block's msb dropped) tiled over the magnitudes
        # of the operands' low `seg` bits; the exact AND array above
        cols = _cols(2 * w)
        for i in range(0, w, 2):
            for j in range(0, w, 2):
                if i + 1 < w and j + 1 < w and i < seg and j < seg and not (signed and (i + 1 == w - 1 or j + 1 == w - 1)):
                    a0, a1, b0, b1 = f"a[{i}]", f"a[{i+1}]", f"b[{j}]", f"b[{j+1}]"
                    o0 = nl.wire(f"{a0} & {b0}", "pp")
                    o1 = nl.wire(f"({a1} & {b0}) | ({a0} & {b1})", "pp")
                    o2 = nl.wire(f"{a1} & {b1}", "pp")
                    cols[i + j].append(o0)
                    cols[i + j + 1].append(o1)
                    cols[i + j + 2].append(o2)
                else:
                    for di in (0, 1):
                        for dj in (0, 1):
                            ii, jj = i + di, j + dj
                            if ii < w and jj < w:
                                invert = signed and ((ii == w - 1) != (jj == w - 1))
                                cols[ii + jj].append(nl.wire(f"{'~' if invert else ''}(a[{ii}] & b[{jj}])", "pp"))
        if signed:
            _add_const(cols, (1 << w) + (1 << (2 * w - 1)))
        cols = reduce_family(nl, cols, {}, "r")
        desc = f"underdesigned 2x2 blocks over the low {seg} bits"
    else:
        cols = pp_and_array(nl, w, signed)
        approx_cols = min(2 * w - 1, seg)
        rec = recovery if technique == "configurable_error_recovery" else 0
        cols, _errs = _reduce_approx_4_2(nl, cols, approx_cols, unbiased, rec)
        desc = f"inexact 4:2 cells in the low {approx_cols} columns" + (", unbiased" if unbiased else "") + \
            (f", {rec} recovery stage(s)" if rec else "")
    add_lines, add_text = final_add(nl, cols, pins, "cpa")
    text = [f"// approximate_compressor ({technique}): {desc} (the ArithmeticError gate governs)",
            f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);"]
    text += nl.render()
    text += add_lines
    text.append("endmodule")
    return "\n".join(text) + "\n" + "".join(nl.extra) + add_text


# ---- segmented_grid ----------------------------------------------------------------------
def segmented_grid_sv(w: int, signed: bool, pins: dict, name: str, depth_override: int | None = None) -> str:
    """The operands split into segments (square: num_seg segments of
    seg_w bits on both sides; rectangular: the multiplier operand in
    half as many segments of twice the width), one segment product per
    pair through the `segment` slot's multiplier (a segmented grid again
    while recursion_depth is above one; the pairs with the top segment
    of a signed operand signed), merged by merge_form: a carry-propagate
    chain of merge_adder instances, the merge_tree reduction over the
    product bits, or a shift-add tree of merge adders."""
    seg_w = min(_ipin(pins, "seg_w", 8), (w + 1) // 2)              # at least two segments
    num_seg = max(2, min(4, _ipin(pins, "num_seg", 2)))
    if seg_w * num_seg < w:
        seg_w = (w + num_seg - 1) // num_seg
    num_seg = (w + seg_w - 1) // seg_w
    shape = str(_pin(pins, "segment_shape", "square"))
    merge = str(_pin(pins, "merge_form", "cpa"))
    depth = depth_override if depth_override is not None else _ipin(pins, "recursion_depth", 1)
    seg_fam = str(_pin(pins, "segment.family", "direct_pp_parallel"))
    mfam = str(_pin(pins, "merge_adder.family", "ripple_carry"))
    mpins = _sub(pins, "merge_adder.")
    W = seg_w * num_seg
    # the b segments: seg_w wide (square) or 2 seg_w wide (rectangular: half as many)
    bw = seg_w if shape == "square" else 2 * seg_w
    nb = num_seg if shape == "square" else (num_seg + 1) // 2
    m = Mod(name, w, f"segmented_grid ({shape}, depth {depth}): {num_seg} x {nb} segment products of {seg_w} x {bw} bits "
                     f"({seg_fam}) merged by {merge} (merge adder {mfam})")
    m.wire("ae", W, expr=f"{{{{({W}-{w}){{a[{w-1}]}}}}, a}}" if (signed and W > w) else (f"{{{{({W}-{w}){{1'b0}}}}, a}}" if W > w else "a"))
    m.wire("be", W, expr=f"{{{{({W}-{w}){{b[{w-1}]}}}}, b}}" if (signed and W > w) else (f"{{{{({W}-{w}){{1'b0}}}}, b}}" if W > w else "b"))
    prods = []
    for i in range(num_seg):
        for j in range(nb):
            sa = signed and i == num_seg - 1
            sb = signed and j == nb - 1
            ext = sa or sb
            # a rectangular pair runs on the wider width, the narrow segment zero-extended (sign-extended when signed)
            sw = max(seg_w, bw) + (1 if ext else 0)
            ahi, alo = (i + 1) * seg_w - 1, i * seg_w
            bhi, blo = min((j + 1) * bw - 1, W - 1), j * bw
            ai = f"ae[{ahi}:{alo}]"
            bj = f"be[{bhi}:{blo}]"
            aw_, bw_ = seg_w, bhi - blo + 1
            if aw_ < sw:
                ai = f"{{{{{sw - aw_}{{{'ae[' + str(ahi) + ']' if sa else chr(49) + chr(39) + 'b0'}}}}}, {ai}}}"
            if bw_ < sw:
                bj = f"{{{{{sw - bw_}{{{'be[' + str(bhi) + ']' if sb else chr(49) + chr(39) + 'b0'}}}}}, {bj}}}"
            m.wire(f"sa{i}{j}", sw, expr=ai)
            m.wire(f"sb{i}{j}", sw, expr=bj)
            if depth > 1 and sw >= 4:
                sub_name = f"{name}_g{i}{j}"
                sub_pins = dict(pins, recursion_depth=depth - 1)
                m.extra.append(segmented_grid_sv(sw, ext, sub_pins, sub_name, depth - 1))
                m.wire(f"sp{i}{j}", 2 * sw)
                m.raw(f"  // segment product ({i}, {j}): a segmented grid of depth {depth - 1}")
                m.raw(f"  {sub_name} u_g{i}{j} (.a(sa{i}{j}), .b(sb{i}{j}), .p(sp{i}{j}));")
            else:
                m.mul(seg_fam, _sub(pins, "segment."), sw, f"sa{i}{j}", f"sb{i}{j}", f"sp{i}{j}", f"segment product ({i}, {j}) ({seg_fam})", signed=ext)
            prods.append((f"sp{i}{j}", 2 * sw, alo + blo, ext))
    PW = 2 * W + 2
    if merge == "carry_save_tree":
        nl = Netlist()
        cols = _cols(PW)
        for nm, pw, sh, ext in prods:
            for k in range(pw):
                c = sh + k
                if c < PW:
                    cols[c].append(f"{nm}[{k}]")
            if ext:
                # the signed product sign-extended: the top bit repeated above
                for c in range(sh + pw, PW):
                    cols[c].append(f"{nm}[{pw-1}]")
        cols = reduce_family(nl, cols, pins, "merge_tree")
        add_lines, add_text = final_add(nl, cols, pins, "merge_tree.cpa")
        m.lines += nl.render()
        m.wire("full", PW)
        m.lines += [l.replace("assign p =", "assign full =").replace(".s(p)", ".s(full)").replace("(p[", "(full[") for l in add_lines]
        m.extra += nl.extra
        m.extra.append(add_text)
    else:
        terms = []
        for nm, pw, sh, ext in prods:
            t = m.wire(f"t_{nm}", PW, expr=f"$signed({{{{({PW}-{pw}){{{nm}[{pw-1}]}}}}, {nm}}}) <<< {sh}" if ext else f"{{{{({PW}-{pw}){{1'b0}}}}, {nm}}} << {sh}")
            terms.append(t)
        if merge == "cpa":
            acc = terms[0]
            for k, t in enumerate(terms[1:], 1):
                m.add(mfam, mpins, PW, acc, t, f"acc{k}", f"merge adder {k}")
                acc = f"acc{k}[{PW-1}:0]"
            m.wire("full", PW, expr=acc)
        else:
            # shift_add_tree: a balanced tree of merge adders
            level = terms
            k = 0
            while len(level) > 1:
                nxt = []
                for i in range(0, len(level) - 1, 2):
                    m.add(mfam, mpins, PW, level[i], level[i + 1], f"tr{k}", f"merge tree adder {k}")
                    nxt.append(f"tr{k}[{PW-1}:0]")
                    k += 1
                if len(level) % 2:
                    nxt.append(level[-1])
                level = nxt
            m.wire("full", PW, expr=level[0])
    m.assign("p", f"full[{2*w-1}:0]")
    return m.render()


# ---- redundant_binary_multiplier ----------------------------------------------------------
# the 2-bit codes of a redundant binary digit in {-1, 0, 1}: the stored pair (w0, w1) of a digit whose
# positive and negative predicates are (pos, neg); the cells decode from the code and encode back into it
RB_CODES = {
    "plus_minus_pair": ("the pair (p, n) of the positive and negative bits", lambda w0, w1: (w0, w1),
                        lambda pos, neg: (pos, neg)),
    "sign_magnitude_2bit": ("the pair (s, a) of a sign and a magnitude bit", lambda w0, w1: (f"({w1} & ~{w0})", f"({w1} & {w0})"),
                            lambda pos, neg: (neg, f"({pos} | {neg})")),
    "np_coding": ("the pair (~p, ~n) of the complemented bits (the cells' inverters fold into the code)",
                  lambda w0, w1: (f"~{w0}", f"~{w1}"), lambda pos, neg: (f"~({pos})", f"~({neg})")),
}


def _rb_add(nl: Netlist, xp: list, xm: list, yp: list, ym: list, code: str = "plus_minus_pair") -> tuple:
    """One redundant binary adder over digit lists (plus, minus bits,
    lsb first): the carry-free two-step rule. Step 1 at each position:
    the digit sum d = x + y in {-2..2} gives an intermediate carry c and
    sum s with d = 2c + s, s in {-1, 0, 1}, c in {-1, 0, 1}, chosen so
    that s and the incoming carry never both equal one sign (the rule
    uses the lower position's signs). Step 2: digit = s + c_in.
    Returns (zp, zm) one digit longer."""
    n = max(len(xp), len(yp))
    xp = xp + ["1'b0"] * (n - len(xp)); xm = xm + ["1'b0"] * (n - len(xm))
    yp = yp + ["1'b0"] * (n - len(yp)); ym = ym + ["1'b0"] * (n - len(ym))
    _doc, dec, enc = RB_CODES[code]
    cs, ss = [], []
    for i in range(n):
        # the operands' digits decoded from their code
        XP, XM = (nl.wire(e, "rb") for e in dec(xp[i], xm[i]))
        YP, YM = (nl.wire(e, "rb") for e in dec(yp[i], ym[i]))
        if i == 0:
            low_neg = "1'b0"
        else:
            lx, ly = dec(xp[i-1], xm[i-1])[1], dec(yp[i-1], ym[i-1])[1]
            low_neg = nl.wire(f"{lx} | {ly}", "rb")               # a negative digit below: its carry is 0 or -1
        two_p = nl.wire(f"{XP} & {YP}", "rb")                     # d = 2
        two_m = nl.wire(f"{XM} & {YM}", "rb")                     # d = -2
        one_p = nl.wire(f"({XP} & ~{YP} & ~{YM}) | ({YP} & ~{XP} & ~{XM})", "rb")   # d = 1
        one_m = nl.wire(f"({XM} & ~{YP} & ~{YM}) | ({YM} & ~{XP} & ~{XM})", "rb")   # d = -1
        cp = nl.wire(f"{two_p} | ({one_p} & ~{low_neg})", "rb")
        cm = nl.wire(f"{two_m} | ({one_m} & {low_neg})", "rb")
        sp = nl.wire(f"({one_p} | {one_m}) & {low_neg}", "rb")
        sm = nl.wire(f"({one_p} | {one_m}) & ~{low_neg}", "rb")
        cs.append((cp, cm))
        ss.append((sp, sm))
    zp, zm = [], []
    for i in range(n + 1):
        sp, sm = ss[i] if i < n else ("1'b0", "1'b0")
        cp, cm = cs[i - 1] if i >= 1 else ("1'b0", "1'b0")
        pos = nl.wire(f"({sp} & ~{cm}) | ({cp} & ~{sm})", "rb")
        neg = nl.wire(f"({sm} & ~{cp}) | ({cm} & ~{sp})", "rb")
        w0, w1 = enc(pos, neg)                                    # the result digit stored in the code
        zp.append(nl.wire(w0, "rb") if w0 != pos else pos)
        zm.append(nl.wire(w1, "rb") if w1 != neg else neg)
    return zp, zm


def _rb_row(nl: Netlist, rp: list, rm: list, code: str) -> tuple:
    """A partial-product row's digits (positive and negative bits) stored in the code."""
    _doc, _dec, enc = RB_CODES[code]
    out0, out1 = [], []
    for p_, m_ in zip(rp, rm):
        w0, w1 = enc(p_, m_)
        out0.append(nl.wire(w0, "rb") if w0 != p_ else p_)
        out1.append(nl.wire(w1, "rb") if w1 != m_ else m_)
    return out0, out1


def redundant_binary_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """The partial-product rows (AND rows; radix-2 Booth rows, +-a per
    multiplier bit pair as a plus or a minus row; or radix-4 Booth rows)
    paired into signed-digit rows, a binary tree of carry-free redundant
    adders, and the final conversion to two's complement: a subtraction
    of the minus word from the plus word through the final_converter
    adder family (cpa), a carry-select adder (carry_select), or the
    on-the-fly digit conversion."""
    code = str(_pin(pins, "rb_encoding", "plus_minus_pair"))
    if code not in RB_CODES:
        raise ValueError(f"rb_encoding {code!r}: one of {tuple(RB_CODES)}")
    code_doc, code_dec, code_enc = RB_CODES[code]
    radix = str(_pin(pins, "booth_radix", "none"))
    conv = str(_pin(pins, "rbnb_converter", "cpa"))
    cfam = _pin(pins, "final_converter.family", "ripple_carry")
    cpins = _sub(pins, "final_converter.")
    nl = Netlist()
    N = 2 * w + 2
    rows = []                                  # (plus bits lsb-first, minus bits) per row, at full width
    booth_lines = []
    if radix == "4":
        # the Booth rows as signed rows: each row's magnitude bits with its neg bit as the minus digit at the lsb
        cols = pp_booth(nl, w, signed, 4, {"sign_extension": "prevention_constant"})
        plus = [[b for b in c] for c in cols] + [[] for _ in range(N - len(cols))]
        h = max(len(c) for c in plus)
        for r in range(h):
            rp = [(c[r] if len(c) > r else "1'b0") for c in plus[:N]]
            rows.append(_rb_row(nl, rp, ["1'b0"] * N, code))
    elif radix == "2":
        # Booth's original recoding: the digit d_i = b_{i-1} - b_i in {-1, 0, 1} selects +a (a plus row) or -a
        # (a minus row) at weight 2^i; a two's complement a is sign-extended, an unsigned one zero-extended
        def abit(k):
            return f"a[{k}]" if k < w else (f"a[{w-1}]" if signed else "1'b0")
        n1 = w + (0 if signed else 1)
        for i in range(n1):
            bi = f"b[{i}]" if i < w else (f"b[{w-1}]" if signed else "1'b0")
            bim1 = f"b[{i-1}]" if i >= 1 else "1'b0"
            sp = nl.wire(f"{bim1} & ~{bi}", "sel")            # d = +1
            sm = nl.wire(f"~{bim1} & {bi}", "sel")            # d = -1
            rp = ["1'b0"] * N
            rm = ["1'b0"] * N
            for k in range(N - i):
                rp[i + k] = nl.wire(f"{sp} & {abit(k)}", "pp")
                rm[i + k] = nl.wire(f"{sm} & {abit(k)}", "pp")
            rows.append(_rb_row(nl, rp, rm, code))
    else:
        for i in range(w):
            rp = ["1'b0"] * N
            rm = ["1'b0"] * N
            for j in range(w):
                bit = nl.wire(f"a[{i}] & b[{j}]", "pp")
                last_a, last_b = signed and i == w - 1, signed and j == w - 1
                if last_a != last_b:
                    rm[i + j] = bit                 # the negative cross terms of two's complement operands
                else:
                    rp[i + j] = bit
            rows.append(_rb_row(nl, rp, rm, code))
    # the binary tree of redundant adders
    level = rows
    while len(level) > 1:
        nxt = []
        for k in range(0, len(level) - 1, 2):
            (xp, xm), (yp, ym) = level[k], level[k + 1]
            zp, zm = _rb_add(nl, xp[:N], xm[:N], yp[:N], ym[:N], code)
            nxt.append((zp[:N], zm[:N]))
        if len(level) % 2:
            nxt.append(level[-1])
        level = nxt
    zp, zm = level[0]
    zp = zp + ["1'b0"] * (N - len(zp)); zm = zm + ["1'b0"] * (N - len(zm))
    zp, zm = [nl.wire(e, "rb") for e in (code_dec(p_, m_)[0] for p_, m_ in zip(zp, zm))], \
             [nl.wire(e, "rb") for e in (code_dec(p_, m_)[1] for p_, m_ in zip(zp, zm))]
    text = [f"// redundant_binary_multiplier: {'Booth radix-4' if radix == '4' else ('Booth radix-2' if radix == '2' else 'AND')} rows as "
            f"signed digits in the {code} code ({code_doc}), a {max(1, (len(rows) - 1).bit_length())}-level tree of carry-free "
            f"redundant adders, converted by {conv}",
            f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);"]
    text += nl.render()
    text.append(f"  logic [{N-1}:0] zp, zm;")
    text.append("  assign zp = {" + ", ".join(reversed(zp)) + "};")
    text.append("  assign zm = {" + ", ".join(reversed(zm)) + "};")
    extra_text = "".join(nl.extra)
    if conv == "on_the_fly":
        # MSB-first: Q and Q-1 kept, the digit appends (Q, d) or (QM, d + 2) by its sign
        text.append(f"  logic [{N-1}:0] q0, qm0;")
        text.append(f"  assign q0 = 0; assign qm0 = {{{N}{{1'b1}}}};")
        for i in range(N):
            k = N - 1 - i
            text.append(f"  logic [{N-1}:0] q{i+1}, qm{i+1};")
            text.append(f"  assign q{i+1} = zp[{k}] ? {{q{i}[{N-2}:0], 1'b1}} : (zm[{k}] ? {{qm{i}[{N-2}:0], 1'b1}} : {{q{i}[{N-2}:0], 1'b0}});")
            text.append(f"  assign qm{i+1} = zp[{k}] ? {{q{i}[{N-2}:0], 1'b0}} : (zm[{k}] ? {{qm{i}[{N-2}:0], 1'b0}} : {{qm{i}[{N-2}:0], 1'b1}});")
        text.append(f"  assign p = q{N}[{2*w-1}:0];")
    else:
        fam = "carry_select" if conv == "carry_select" else cfam
        head, t = _lib_inst("adder", fam, cpins if conv != "carry_select" else {}, N)
        if head is None:
            raise ValueError(f"the converter adder family {fam!r} has no library module")
        text.append(f"  logic [{N-1}:0] nz; assign nz = ~zm;")
        text.append(f"  logic [{N-1}:0] dif; logic co;")
        text.append(f"  // the converter: plus word less minus word through the {fam} adder")
        text.append(f"  {head}u_conv (.a(zp), .b(nz), .cin(1'b1), .s(dif), .cout(co));")
        extra_text += t
        text.append(f"  assign p = dif[{2*w-1}:0];")
    text.append("endmodule")
    return "\n".join(text) + "\n" + extra_text


def mul_ext_sv(w: int, signed: bool, family: str, pins: dict, name: str | None = None) -> tuple:
    """(name, text, summary) of one of the extension families."""
    pins = pins or {}
    name = name or f"fam_mul_{family}_{_sfx(w, signed, pins)}"
    if family == "behavioral_star":
        return name, behavioral_star_sv(w, signed, name), {}
    if family == "squarer":
        return name, squarer_sv(w, signed, pins, name), {}
    if family == "truncated_fixed_width":
        return name, truncated_sv(w, signed, pins, name), {"approximate": True}
    if family == "logarithmic_mitchell":
        return name, logarithmic_sv(w, signed, pins, name), {"approximate": True}
    if family == "approximate_compressor":
        return name, approximate_compressor_sv(w, signed, pins, name), {"approximate": True}
    if family == "segmented_grid":
        return name, segmented_grid_sv(w, signed, pins, name), {}
    if family == "redundant_binary_multiplier":
        return name, redundant_binary_sv(w, signed, pins, name), {}
    raise ValueError(f"no module for the multiplier family {family}")
