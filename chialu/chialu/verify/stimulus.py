"""Vector plans: corners x corners + op-aware directed + seeded random.

A plan is a list of dicts {port_name: bits} plus a parallel meta list
(op name / fn name / combo per vector) for the reference layer. The
plan depends only on formats and op sets; freeze() hashes the packed
vectors so a plan can be pinned and reproduced anywhere.
"""

from __future__ import annotations

import hashlib

from chialu.verify.formats import (BCDFormat, BlockFormat, FloatFormat,
                                    IntFormat)


class Rng:
    """xorshift64* — deterministic across platforms/versions."""

    def __init__(self, seed):
        self.s = (seed or 0x9E3779B97F4A7C15) & ((1 << 64) - 1)

    def next(self):
        s = self.s
        s ^= (s >> 12)
        s ^= (s << 25) & ((1 << 64) - 1)
        s ^= (s >> 27)
        self.s = s
        return (s * 0x2545F4914F6CDD1D) & ((1 << 64) - 1)

    def bits(self, w):
        out = 0
        for _ in range((w + 63) // 64):
            out = (out << 64) | self.next()
        return out & ((1 << w) - 1)

    def below(self, n):
        return self.next() % n

    def choice(self, seq):
        return seq[self.below(len(seq))]


CORNER_PAIR_CAP = 1024
"""The ceiling on the corner product of a two-operand plan. Every format
of this package holds at most 30 corners, so the product is at most 900
and the ceiling never bites. A format above the ceiling is sampled
without replacement, and the plan then depends on the seed."""


def _pair_cap(pairs, cap, rng):
    """At most `cap` pairs, each one distinct. A product at or below the
    cap is kept whole in its own order. A larger product is sampled
    without replacement by a partial Fisher-Yates shuffle, so no pair is
    drawn twice and the kept count equals the cap."""
    pairs = list(pairs)
    if len(pairs) <= cap:
        return pairs
    for i in range(cap):
        j = i + rng.below(len(pairs) - i)
        pairs[i], pairs[j] = pairs[j], pairs[i]
    return pairs[:cap]


def _fp_bits(fmt, sign, e, m):
    """The finite pattern of a float format from its sign, exponent
    field and mantissa field. A magnitude above the largest finite
    pattern is clamped to it, so a format whose top exponent field holds
    an infinity or a NaN never receives one here by accident."""
    mag = min(((e & ((1 << fmt.exp_bits) - 1)) << fmt.man_bits)
              | (m & ((1 << fmt.man_bits) - 1)), fmt._max_finite_bits())
    return ((sign << (fmt.width - 1)) if fmt.signed else 0) | mag


def _fp_normal(fmt, rng, lo=1, hi=None):
    """A random normal pattern of a float format, its exponent field
    drawn from the range lo to hi and clamped to the format's own."""
    top = fmt._top()
    lo = max(1, min(lo, top))
    hi = top if hi is None else max(lo, min(hi, top))
    return _fp_bits(fmt, rng.below(2) if fmt.signed else 0,
                    lo + rng.below(hi - lo + 1), rng.bits(fmt.man_bits))


def _cancellation_pairs(fmt, rng, flip):
    """`a` and the pattern k ulp away from it, for a k of every bit
    length below the mantissa width. The exact difference of such a pair
    is k ulp, so the normalization shift of the result runs over 1 to
    man_bits and the normalizer is driven at every shift amount. `flip`
    inverts the second sign, which turns the addition of an op into an
    effective subtraction."""
    mb = fmt.man_bits
    out = []
    for j in range(mb):
        k = (1 << j) | (rng.bits(j) if j else 0)     # k has bit length j + 1
        low = rng.below((1 << mb) - k)
        s = rng.below(2) if fmt.signed else 0
        e = 1 + rng.below(max(1, fmt._top()))
        out.append((_fp_bits(fmt, s, e, low + k),
                    _fp_bits(fmt, s ^ flip, e, low)))
    return out


def _exponent_delta_pairs(fmt, rng):
    """`a` and a pattern d binades below it, for d from 0 to p + 4 where
    p is the significand width. The window covers the alignment shifts
    at which the second operand leaves the significand and reaches the
    guard bit, the round bit and the sticky bit. The four deltas around
    p also appear with the operands exchanged, because the alignment
    path of a unit that swaps its operands is not symmetric."""
    p = fmt.man_bits + 1
    top = fmt._top()
    out = []
    for d in range(0, p + 5):
        lo = min(top, d + 1)
        e = lo + rng.below(max(1, top - lo + 1))
        a = _fp_bits(fmt, rng.below(2) if fmt.signed else 0, e,
                     rng.bits(fmt.man_bits))
        b = _fp_bits(fmt, rng.below(2) if fmt.signed else 0, max(1, e - d),
                     rng.bits(fmt.man_bits))
        out.append((a, b))
        if p - 1 <= d <= p + 2:
            out.append((b, a))
    return out


def _subnormal_boundary_pairs(fmt, rng):
    """A subnormal operand and a power of two whose product sits at the
    boundary between the subnormal and the normal range. The three
    exponents around the boundary place the product below it, on it and
    above it, which drives the rounder's tininess and underflow path."""
    top = fmt._top()
    mb = fmt.man_bits
    out = []
    for _ in range(3):
        m = 1 + rng.below(max(1, (1 << mb) - 1))
        t0 = fmt.bias + mb - (m.bit_length() - 1)
        for dt in (-1, 0, 1):
            t = max(1, min(top, t0 + dt))
            out.append((_fp_bits(fmt, rng.below(2) if fmt.signed else 0, 0, m),
                        _fp_bits(fmt, rng.below(2) if fmt.signed else 0, t, 0)))
    return out


def directed_pairs(op, fmt, rng, budget=64):
    """Op-aware adversarial (a, b) bit pairs. The random families are
    capped at `budget`. The float alignment, cancellation and subnormal
    families are kept whole, because each of their entries stands for one
    shift amount or one boundary position, and a sample would leave some
    of those uncovered."""
    out, keep = [], []
    cs = fmt.corners()
    if op in ("div", "quot", "rem", "mod", "fdiv"):
        near = [fmt.encode(v) for v in (0, 1)] if isinstance(fmt, (IntFormat, BCDFormat)) \
            else [0, fmt.round(1), fmt.round(-1) if not isinstance(fmt, BCDFormat) else 0]
        for b in near:
            for a in cs[: budget // max(len(near), 1)]:
                out.append((a, b))
    if op in ("add", "sub", "fadd", "fsub", "add_sat", "sub_sat"):
        for _ in range(budget // 2):
            a = fmt.sample(rng)
            out.append((a, a))                       # cancellation twins
            if isinstance(fmt, FloatFormat):
                out.append((a, a ^ (1 << (fmt.width - 1))))    # a + (-a)
            elif isinstance(fmt, IntFormat) and fmt.encoding != "unsigned":
                try:
                    out.append((a, fmt.encode(fmt.wrap(-fmt.decode(a)))))
                except AssertionError:
                    pass
    if op in ("fmul", "mul", "mul_wide", "mul_high", "mul_sat"):
        big = cs[-4:]
        for a in big:
            for b in big:
                out.append((a, b))
    if isinstance(fmt, FloatFormat) and op.startswith("f") and not fmt.exp_only:
        keep += _exponent_delta_pairs(fmt, rng)
        if op in ("fadd", "fsub"):
            keep += _cancellation_pairs(fmt, rng, 1 if op == "fadd" else 0)
        if op == "fmul":
            keep += _subnormal_boundary_pairs(fmt, rng)
    return _pair_cap(out, budget, rng) + keep


def directed_triples(op, fmt, rng, budget=64):
    """Op-aware (a, b, c) bit triples of a fused multiply-add on a float
    format: the adder's directed pairs as (a, 1.0, c) and the multiplier's
    as (a, b, 0 or random), the exact cancellation of the product by the
    addend and its two neighbors (the result is zero, or one ulp of the
    product, so the normalizer runs over its whole range), and the addend
    at every exponent distance from the product."""
    from fractions import Fraction
    from chialu.verify.alu_ref import FUSED_OPS
    from chialu.verify.formats import Special
    if not isinstance(fmt, FloatFormat) or fmt.exp_only:
        return []
    neg_p, neg_c = FUSED_OPS[op]
    one = fmt.round(Fraction(1))
    out = []
    for a, c in directed_pairs("fadd", fmt, rng, budget):
        out.append((a, one, c))
    for a, b in directed_pairs("fmul", fmt, rng, budget):
        out.append((a, b, 0 if rng.below(2) else fmt.sample(rng)))
    top = max(1, fmt._top())
    limit = 1 << (fmt.width - 1) if fmt.signed else 1 << fmt.width
    for _ in range(budget // 2):
        a = fmt.sample(rng)
        b = _fp_bits(fmt, rng.below(2) if fmt.signed else 0, 1 + rng.below(top), 0)     # a power of two
        va, vb = fmt.decode(a), fmt.decode(b)
        if isinstance(va, Special) or isinstance(vb, Special) or va == 0:
            continue
        prod = va * vb * (-1 if neg_p else 1)
        target = prod if neg_c else -prod             # (-1)^nc * c = -product
        if target < 0 and not fmt.signed:
            continue
        cb = fmt.round(target)
        if fmt.decode(cb) != target:
            continue                                  # the product is not representable: no exact cancellation
        out.append((a, b, cb))
        for delta in (1, -1):
            n = cb + delta
            if 0 <= n < (1 << fmt.width) and (n & (limit - 1)) != 0 and (n ^ cb) < limit \
                    and not isinstance(fmt.decode(n), Special):
                out.append((a, b, n))
    for e in range(1, top + 1, max(1, top // 16)):
        out.append((fmt.sample(rng), fmt.sample(rng),
                    _fp_bits(fmt, rng.below(2) if fmt.signed else 0, e, rng.bits(fmt.man_bits))))
    return out


def _lane_format(fmt, lw):
    """The per-lane format of a subword mode: the same integer encoding
    at the lane width (subword lanes exist for integer units only)."""
    if isinstance(fmt, IntFormat):
        return IntFormat(lw, fmt.encoding)
    if isinstance(fmt, BCDFormat):
        return BCDFormat(lw)
    raise ValueError(f"subword lanes need an integer format, not {fmt.name}")


def plan_binary(fmt, out_fmt, ops, n_random, seed, lanes=(1,)):
    """Vectors for unit class 1. Ports: a, b [, op][, lane_mode].
    Lanes > 1 pack independent per-lane streams into a/b: lane i of an
    n-lane mode occupies bits [i*w/n +: w/n] of a and b, its pairs drawn
    (corners, directed, random) from the lane-width format."""
    rng = Rng(seed)
    vecs, meta = [], []
    cs = fmt.corners()
    max_lane = max(lanes)

    def pack(pairs_per_lane, lw):
        a = b = 0
        for i, (pa, pb) in enumerate(pairs_per_lane):
            a |= pa << (i * lw)
            b |= pb << (i * lw)
        return a, b

    def pairs_for(op, f):
        ps = _pair_cap(((a, b) for a in f.corners() for b in f.corners()),
                       CORNER_PAIR_CAP, rng)
        ps += directed_pairs(op, f, rng)
        ps += [(f.sample(rng), f.sample(rng)) for _ in range(n_random)]
        return ps

    for oi, op in enumerate(ops):
        pairs = _pair_cap(((a, b) for a in cs for b in cs),
                          CORNER_PAIR_CAP, rng)
        pairs += directed_pairs(op, fmt, rng)
        pairs += [(fmt.sample(rng), fmt.sample(rng))
                  for _ in range(n_random)]
        for li, lane_n in enumerate(lanes):
            lw = fmt.width // lane_n
            lf = fmt if lane_n == 1 else _lane_format(fmt, lw)
            lane_pairs_src = pairs if lane_n == 1 else pairs_for(op, lf)
            for pa, pb in lane_pairs_src:
                lane_pairs = [(pa, pb)] + \
                    [(lf.sample(rng), lf.sample(rng))
                     for _ in range(lane_n - 1)]
                v = {"a": 0, "b": 0}
                v["a"], v["b"] = pack(lane_pairs, lw)
                if len(ops) > 1:
                    v["op"] = oi
                if len(lanes) > 1:
                    v["lane_mode"] = li
                vecs.append(v)
                meta.append({"op": op, "lane_n": lane_n,
                             "lane_pairs": lane_pairs})
            if lane_n == max_lane == 1:
                break
    return vecs, meta


def _combos(controls):
    """The runtime option combinations of a plan: the Cartesian product
    of every control with more than one provisioned value, as dicts."""
    import itertools
    names = [n for n, vs in (controls or {}).items() if len(vs) > 1]
    if not names:
        return [{}]
    return [dict(zip(names, vals))
            for vals in itertools.product(*[controls[n] for n in names])]


def plan_alu(modes, ops, legal, n_random, seed, controls=None, sr=None,
             exhaustive=False, unary=None, ternary=None):
    """Vectors for chialu.ALU over its modes: for every legal (mode, op)
    pair, corners x corners (capped), directed pairs and n_random random
    pairs of the mode's format, packed `count` values per operand (value
    i at [i*w +: w]). Ports: a, b [, c][, op][, mode][, sr_rnd][, <name>_sel].

    controls: {name: [values]} of the runtime-selectable options; the
    corner and directed pairs are replicated over every combination when
    there are at most 4, cycled otherwise; random pairs draw a random
    combination. sr = (v_max, sr_bits) adds the PRBS-31 words of
    `sr_rnd`. exhaustive: unary ops of scalar formats of at most 16 bits
    in a count-1 mode see every pattern of a. ternary: the ops that read
    the third operand c (the fused multiply-add): their corner pairs take
    a corner c, their directed triples come from directed_triples, and
    their random vectors draw three values; a vector's meta lists the
    lanes' operand tuples under lane_pairs."""
    from chialu.verify.rounding import PRBS31
    rng = Rng(seed)
    prbs = PRBS31(seed) if sr else None
    combos = _combos(controls)
    cnames = [n for n in (controls or {}) if len(controls[n]) > 1]
    vecs, meta = [], []
    unary = unary or set()
    ternary = ternary or set()
    for mi, (count, fmt) in enumerate(modes):
        w = fmt.width
        cs = fmt.corners()
        for oi, op in enumerate(ops):
            if (mi, op) not in legal:
                continue
            fixed = _pair_cap(((a, b) for a in cs for b in cs),
                              CORNER_PAIR_CAP, rng)
            if op in ternary:
                fixed = [(a, b, rng.choice(cs)) for a, b in fixed]
                try:
                    fixed += directed_triples(op, fmt, rng)
                except Exception:  # noqa: BLE001 — no directed plan for this op
                    pass
                randoms = [(fmt.sample(rng), fmt.sample(rng), fmt.sample(rng)) for _ in range(n_random)]
            else:
                try:
                    fixed += directed_pairs(op, fmt, rng)
                except Exception:  # noqa: BLE001 — no directed plan for this op
                    pass
                if exhaustive and count == 1 and w <= 16 and (op in unary or op.startswith("cvt(")) \
                        and not isinstance(fmt, BlockFormat):
                    fixed = [(a, fmt.sample(rng)) for a in range(1 << w) if fmt.valid(a)]
                    randoms = []
                else:
                    randoms = [(fmt.sample(rng), fmt.sample(rng)) for _ in range(n_random)]
            plan = []
            if len(combos) <= 4:
                for c in combos:
                    plan += [(operands, c) for operands in fixed]
            else:
                plan += [(operands, combos[k % len(combos)]) for k, operands in enumerate(fixed)]
            plan += [(operands, rng.choice(combos)) for operands in randoms]
            names = ("a", "b", "c")[:len(fixed[0]) if fixed else (3 if op in ternary else 2)]
            for operands, c in plan:
                lane_pairs = [tuple(operands)] + [tuple(fmt.sample(rng) for _ in names)
                                                  for _ in range(count - 1)]
                v = {"a": 0, "b": 0}
                for i, lane in enumerate(lane_pairs):
                    for name, bits in zip(names, lane):
                        v[name] = v.get(name, 0) | (bits << (i * w))
                if len(ops) > 1:
                    v["op"] = oi
                if len(modes) > 1:
                    v["mode"] = mi
                words = None
                if sr:
                    v_max, sr_bits = sr
                    words = [prbs.word(sr_bits) for _ in range(v_max)]
                    packed = 0
                    for k, wd in enumerate(words):
                        packed |= wd << (k * sr_bits)
                    v["sr_rnd"] = packed
                for n in cnames:
                    v[f"{n}_sel"] = controls[n].index(c[n])
                vecs.append(v)
                meta.append({"op": op, "mode": mi, "count": count,
                             "lane_pairs": lane_pairs, "ctrl": c,
                             "words": words})
    return vecs, meta


def plan_sfu(lay, n_random, seed, controls=None, sr=None, exhaustive=False):
    """Vectors for chialu.VecSFU over its modes (sfu_ref.sfu_layout): per
    mode and function or slot, corners, directed points near the domain
    boundaries and random patterns for the first value, random patterns
    for the other values (exhaustive: every pattern of a one-value scalar
    mode of at most 16 bits). Slot tables are loaded once before the
    vectors from the same seed: returns (vecs, meta, tables, preload)
    with tables[slot][k] = coefficient patterns and preload the
    (we_mask, addr, data) writes."""
    from chialu.verify.rounding import PRBS31
    from chialu.verify.sfu_ref import coeff_words
    rng = Rng(seed)
    prbs = PRBS31(seed) if sr else None
    combos = _combos(controls)
    cnames = [n for n in (controls or {}) if len(controls[n]) > 1]
    modes, fns, slots = lay["modes"], lay["functions"], lay["slots"]
    total = lay["total"]
    w_max = lay["w_max"]
    # slot tables: random coefficient patterns of the widest format
    wide = max((f for _, f in modes), key=lambda f: f.width)
    tables, preload = [], []
    for si, slot in enumerate(slots):
        nc = coeff_words(slot)
        tbl = []
        for k in range(slot["segments"]):
            cs = tuple(wide.sample(rng) for _ in range(nc))
            tbl.append(cs)
            data = 0
            for j, c in enumerate(cs):
                data |= c << (j * w_max)
            preload.append((1 << si, k, data))
        tables.append(tbl)
    vecs, meta = [], []
    for mi, (count, fmt) in enumerate(modes):
        w = fmt.width
        cs = fmt.corners()
        extra = []
        if not isinstance(fmt, BlockFormat):
            for v in (1, -1, 2, -2):
                try:
                    extra.append(fmt.round(v if not hasattr(fmt, "signed") or fmt.signed or v > 0 else -v))
                except Exception:  # noqa: BLE001
                    pass
        for fi in range(total):
            if exhaustive and count == 1 and w <= 16 and not isinstance(fmt, BlockFormat):
                xs = [(x, combos[k % len(combos)]) for k, x in enumerate(range(1 << w)) if fmt.valid(x)]
            else:
                fixed = list(cs) + extra
                xs = [(x, c) for c in (combos if len(combos) <= 4 else [combos[0]]) for x in fixed]
                xs += [(fmt.sample(rng), rng.choice(combos)) for _ in range(n_random)]
            for x, c in xs:
                vals = [x] + [fmt.sample(rng) for _ in range(count - 1)]
                packed = 0
                for i, lx in enumerate(vals):
                    packed |= lx << (i * w)
                v = {"x": packed}
                if total > 1:
                    v["fn_sel"] = fi
                if len(modes) > 1:
                    v["mode"] = mi
                words = None
                if sr:
                    v_max, sr_bits = sr
                    words = [prbs.word(sr_bits) for _ in range(v_max)]
                    pk = 0
                    for k, wd in enumerate(words):
                        pk |= wd << (k * sr_bits)
                    v["sr_rnd"] = pk
                for n in cnames:
                    v[f"{n}_sel"] = controls[n].index(c[n])
                vecs.append(v)
                meta.append({"mode": mi, "fn": fi, "x": packed, "ctrl": c, "words": words,
                             "exact": fi >= len(fns)})
    return vecs, meta, tables, preload


def _dot_directed(m, acc, rng, S):
    """Directed element vectors of one float dot mode, as (a_vals,
    b_vals, c_bits) triples over the mode's S x elements value slots.
    c_bits is None where the mode carries no addend. Each family fills
    group 0, leaves the other groups random, and reaches a case that
    corner pairs and random pairs do not:

    * `a1 b1 = -(a0 b0)` cancels two products exactly, and a `b1` moved
      k ulp off `b0` cancels them at depths spread from the significand
      width down to a few bits;
    * an addend at the rounded `-(product sum)`, and at the two patterns
      one ulp from it, cancels the sum the products reach;
    * an addend d binades from the largest product, for d from p - 1 to
      p + 3 on each side, holds the far operand at the sticky boundary
      of the alignment window.

    A mode whose operands or addend are not scalar floats takes no
    directed family, because the constructions above are stated on the
    exponent and the significand of one value.
    """
    from fractions import Fraction
    from chialu.verify.formats import Special, _floor_log2
    fab, fc = m["fab"], m["fc"]
    n = m["elements"]
    if not isinstance(fab, FloatFormat) or fab.exp_only:
        return []
    if acc and not (isinstance(fc, FloatFormat) and not fc.exp_only):
        return []
    mb, p = fab.man_bits, fab.man_bits + 1
    nvals = S * n
    sign_mask = (1 << (fab.width - 1)) if fab.signed else 0
    exp_one = fab.bias      # the exponent field of a value in [1, 2)
    out = []

    def normals(k, lo=1, hi=None):
        return [_fp_normal(fab, rng, lo, hi) for _ in range(k)]

    def value_vectors(g0_a, g0_b):
        return (list(g0_a) + normals(nvals - n),
                list(g0_b) + normals(nvals - n))

    def pack_c(x):
        """The addend x in group 0, a random addend in the other groups."""
        if not acc:
            return None
        cv = x & ((1 << fc.width) - 1)
        for g in range(1, S):
            cv |= fc.sample(rng) << (g * fc.width)
        return cv

    if n >= 2:
        # the addend is zero, so the reduction's own cancellation is the
        # whole result rather than a term the addend hides
        for live in (False, True):    # the pair alone, then in a live sum
            tail = normals(n - 2, exp_one, exp_one) if live else [0] * (n - 2)
            a0, b0 = _fp_normal(fab, rng), _fp_normal(fab, rng, exp_one, exp_one)
            out.append(value_vectors([a0, a0 ^ sign_mask] + tail,
                                     [b0, b0] + tail) + (pack_c(0),))
        for j in range(0, mb, max(1, mb // 5)):
            a0 = _fp_normal(fab, rng)
            s = rng.below(2) if fab.signed else 0
            e = 1 + rng.below(max(1, fab._top()))
            k = (1 << j) | (rng.bits(j) if j else 0)
            low = rng.below((1 << mb) - k)
            out.append(value_vectors([a0, a0 ^ sign_mask] + [0] * (n - 2),
                                     [_fp_bits(fab, s, e, low + k),
                                      _fp_bits(fab, s, e, low)]
                                     + [0] * (n - 2)) + (pack_c(0),))
    if not acc:
        return out

    def neighbour(bits, step):
        half = fc.width - 1
        s = (bits >> half) & 1 if fc.signed else 0
        mag = bits & ((1 << half) - 1) if fc.signed else bits
        mag = max(0, min(fc._max_finite_bits(), mag + step))
        return ((s << half) if fc.signed else 0) | mag

    def products(a_vals, b_vals):
        return [fab.decode(x) * fab.decode(y)
                for x, y in zip(a_vals[:n], b_vals[:n])]

    # the products stay in [1, 4) so every addend of the two families
    # below is representable and the window is never clamped away
    a_vals, b_vals = value_vectors(normals(n, exp_one, exp_one),
                                   normals(n, exp_one, exp_one))
    total = sum(products(a_vals, b_vals), Fraction(0))
    base = fc.round(-total, "RNE")
    if not isinstance(fc.decode(base), Special):
        for nb in (base, neighbour(base, 1), neighbour(base, -1)):
            out.append((a_vals, b_vals, pack_c(nb)))
    for d in range(p - 1, p + 4):
        for side in (1, -1):
            a_vals, b_vals = value_vectors(normals(n, exp_one, exp_one),
                                           normals(n, exp_one, exp_one))
            nz = [x for x in products(a_vals, b_vals) if x != 0]
            if not nz:
                continue
            emax = max(_floor_log2(abs(x)) for x in nz)
            e = max(1, min(fc._top(), emax + side * d + fc.bias))
            out.append((a_vals, b_vals,
                        pack_c(_fp_bits(fc, rng.below(2) if fc.signed else 0,
                                        e, rng.bits(fc.man_bits)))))
    return out


def plan_dot(lay, n_random, seed, controls=None, sr=None):
    """Vectors for chialu.VecDotAcc over its modes (dot_ref.dot_layout):
    per mode, the first (a, b) value pair from corners x corners (capped)
    then random pairs, the other values random, c from corners a quarter
    of the time; a few all-extreme vectors stress the accumulation, and
    the directed families of _dot_directed drive product cancellation,
    addend cancellation and the far-addend sticky window.
    Ports: a, b [, c][, mode][, sr_rnd][, <name>_sel]."""
    from chialu.verify.dot_ref import n_outputs
    from chialu.verify.rounding import PRBS31
    rng = Rng(seed)
    prbs = PRBS31(seed) if sr else None
    combos = _combos(controls)
    cnames = [n for n in (controls or {}) if len(controls[n]) > 1]
    vecs, meta = [], []
    acc = lay["accumulate"]
    for mi, m in enumerate(lay["modes"]):
        fab, fc, fd = m["fab"], m["fc"], m["fd"]
        S = n_outputs(m)
        nvals = S * m["elements"]
        w = fab.width
        cs = fab.corners()
        pairs = _pair_cap(((x, y) for x in cs for y in cs), 128, rng)
        cases = [(pa, pb, c) for c in (combos if len(combos) <= 4 else [combos[0]]) for pa, pb in pairs]
        cases += [(fab.sample(rng), fab.sample(rng), rng.choice(combos)) for _ in range(n_random)]
        extremes = [(cs[-1], cs[-1]), (cs[-1], cs[0]), (cs[0], cs[0])]
        for k in range(min(8, len(extremes) * 3)):
            pa, pb = extremes[k % len(extremes)]
            cases.append((pa, pb, rng.choice(combos), "all"))
        plans = []
        for case in cases:
            pa, pb, c = case[0], case[1], case[2]
            fill_all = len(case) > 3
            a_vals = [pa] + ([pa] * (nvals - 1) if fill_all else [fab.sample(rng) for _ in range(nvals - 1)])
            b_vals = [pb] + ([pb] * (nvals - 1) if fill_all else [fab.sample(rng) for _ in range(nvals - 1)])
            plans.append((a_vals, b_vals, None, c))
        for a_vals, b_vals, c_bits in _dot_directed(m, acc, rng, S):
            plans.append((a_vals, b_vals, c_bits, rng.choice(combos)))
        for a_vals, b_vals, c_fixed, c in plans:
            a = b = 0
            for i, (xa, xb) in enumerate(zip(a_vals, b_vals)):
                a |= xa << (i * w)
                b |= xb << (i * w)
            v = {"a": a, "b": b}
            cval = None
            if acc:
                if c_fixed is not None:
                    cval = c_fixed
                elif isinstance(fc, BlockFormat):
                    cval = fc.sample(rng) if rng.below(4) else rng.choice(fc.corners())
                else:
                    cval = 0
                    for g in range(S):
                        x = fc.sample(rng) if rng.below(4) else rng.choice(fc.corners())
                        cval |= x << (g * fc.width)
                v["c"] = cval
            if len(lay["modes"]) > 1:
                v["mode"] = mi
            words = None
            if sr:
                v_max, sr_bits = sr
                words = [prbs.word(sr_bits) for _ in range(v_max)]
                packed = 0
                for k, wd in enumerate(words):
                    packed |= wd << (k * sr_bits)
                v["sr_rnd"] = packed
            for n in cnames:
                v[f"{n}_sel"] = controls[n].index(c[n])
            vecs.append(v)
            meta.append({"mode": mi, "a": a, "b": b, "c": cval, "ctrl": c, "words": words})
    return vecs, meta


def freeze(vecs, port_order):
    h = hashlib.sha256()
    for v in vecs:
        for p in port_order:
            h.update(str(v.get(p, 0)).encode())
        h.update(b";")
    return h.hexdigest()
