"""Residue modules: r = x mod M of a pattern, by k-bit folding when
M = 2^k - 1 and by a behavioral modulo otherwise."""
from __future__ import annotations

from chialu.targets.rtl.writer import SvModule


def residue_bits(M: int) -> int:
    """The width of a residue mod M."""
    return M.bit_length() if M == (1 << M.bit_length()) - 1 else (M - 1).bit_length()


def _fold_residue_module(name: str, width: int, M: int, style: str = "csa_tree") -> str:
    """residue of a `width`-bit pattern mod M = 2^k - 1 by folding: the
    k-bit chunks reduced to the residue, the sum folded until k + 1 bits
    remain, one final subtraction of M. `style` is how the chunks are
    summed: a carry-save tree of full-adder rows with one adder at the
    root (csa_tree), a chain of end-around-carry adders (modular_ripple),
    or a table over the chunk pairs where the index fits (lut).""" 
    k = M.bit_length()
    assert M == (1 << k) - 1
    chunks = (width + k - 1) // k
    m = SvModule(name)
    m.port("x", "in", width)
    m.port("r", "out", k)
    terms = []
    for c in range(chunks):
        lo, hi = c * k, min(width, (c + 1) * k) - 1
        terms.append(f"x[{hi}:{lo}]" if hi - lo + 1 == k else
                     f"{{{{{k-(hi-lo+1)}{{1'b0}}}}, x[{hi}:{lo}]}}")
    s_w = k + (chunks - 1).bit_length() + 1
    ext = [f"{{{{{s_w-k}{{1'b0}}}}, {t}}}" for t in terms]
    m.logic("s0", s_w)
    if style == "modular_ripple" and len(terms) > 2:
        # a chain of end-around-carry adders: every step folds its own carry back, so the running value stays
        # k bits wide
        cur = terms[0]
        for i, t in enumerate(terms[1:]):
            m.logic(f"c{i}", k + 1)
            m.assign(f"c{i}", f"{{1'b0, {cur}}} + {{1'b0, {t}}}")
            m.logic(f"e{i}", k)
            m.assign(f"e{i}", f"c{i}[{k-1}:0] + {{{{{k-1}{{1'b0}}}}, c{i}[{k}]}}")
            cur = f"e{i}"
        m.assign("s0", f"{{{{{s_w-k}{{1'b0}}}}, {cur}}}")
    elif style == "lut" and 2 * k <= 12 and len(ext) > 1:
        # the chunks folded pairwise through a table of (a + b) mod M over the two k-bit chunks
        tbl = "{" + ", ".join(f"{k}'d{(((i >> k) & ((1 << k) - 1)) + (i & ((1 << k) - 1))) % M}"
                              for i in reversed(range(1 << (2 * k)))) + "}"
        m.logic("t_pair", (1 << (2 * k)) * k)
        m.assign("t_pair", tbl)
        cur, r = [t for t in terms], 0
        while len(cur) > 1:
            nxt = []
            for i in range(0, len(cur) - 1, 2):
                m.logic(f"lu{r}", k)
                m.assign(f"lu{r}", f"t_pair[({{{cur[i]}, {cur[i+1]}}}) * {k} +: {k}]")
                nxt.append(f"lu{r}")
                r += 1
            if len(cur) % 2:
                nxt.append(cur[-1])
            cur = nxt
        m.assign("s0", f"{{{{{s_w-k}{{1'b0}}}}, {cur[0]}}}")
    else:
        # a carry-save tree of the chunks, one adder at the root
        cur, r = list(ext), 0
        while len(cur) > 2:
            nxt = []
            for i in range(0, len(cur) - 2, 3):
                a_, b_, c_ = cur[i:i + 3]
                m.logic(f"fs{r}", s_w)
                m.assign(f"fs{r}", f"{a_} ^ {b_} ^ {c_}")
                m.logic(f"fc{r}", s_w)
                m.assign(f"fc{r}", f"(({a_} & {b_}) | ({a_} & {c_}) | ({b_} & {c_})) << 1")
                nxt += [f"fs{r}", f"fc{r}"]
                r += 1
            nxt += cur[len(cur) - len(cur) % 3:]
            cur = nxt
        m.assign("s0", " + ".join(cur))
    cur, cw, n = "s0", s_w, 1
    while cw > k + 1:
        nw = max(k + 1, (cw - k) + 1)
        m.logic(f"s{n}", nw)
        m.assign(f"s{n}", f"{{{{{nw-(cw-k)}{{1'b0}}}}, {cur}[{cw-1}:{k}]}} + {{{{{nw-k}{{1'b0}}}}, {cur}[{k-1}:0]}}")
        cur, cw, n = f"s{n}", nw, n + 1
    m.logic("f", k + 1)
    if cw == k + 1:
        m.assign("f", f"{{{k}'d0, {cur}[{cw-1}:{k}]}} + {{1'b0, {cur}[{k-1}:0]}}")
    else:
        m.assign("f", cur)
    m.assign("r", f"(f >= {k+1}'d{M}) ? (f - {k+1}'d{M}) : f[{k-1}:0]")
    return m.render()


def _mod_residue_module(name: str, width: int, M: int) -> str:
    """residue of a `width`-bit pattern mod M by a behavioral modulo. The
    modulo is computed in `max(width, M.bit_length())` bits, because a
    modulus literal sized to a narrower lane is truncated and the channel
    then returns a constant."""
    k = (M - 1).bit_length()
    mw = max(width, M.bit_length())
    m = SvModule(name)
    m.port("x", "in", width)
    m.port("r", "out", k)
    m.assign("r", f"x % {mw}'d{M}")
    return m.render()


def residue_module(name: str, width: int, M: int, style: str = "csa_tree") -> str:
    if M == (1 << M.bit_length()) - 1:
        return _fold_residue_module(name, width, M, style)
    return _mod_residue_module(name, width, M)
