"""Special-function families on the engine's X representation: the
approximation families of chialu.VecSFU (sfu_spaces.sfu_approx_space)
with their range-reduction, evaluation-datapath and segmentation
component families, generated per (function, format, engine geometry)
and verified by a bit-accurate Python model of the same datapath.

A family module takes one lane's operand as X ({special, sign, exp,
sig[XW], sticky}, the seed's unpacked value) and returns the function's
value as an X before the engine's pack (the seed packs it under the
run's rounding and keeps its own special-value handling); the
full-value tables (direct_lut, compressed_lut) take the pattern and
return the pattern. Every module is built from one fixed-point netlist
(`Net`) that evaluates in Python and renders to SystemVerilog, so the
model and the module agree bit for bit; the generator sizes the
internal fraction bits from the format's significand plus guard bits
and measures the model's error in ulps against the verify layer's
reference (exhaustively for formats of at most 16 bits, sampled above),
which the module header reports.

Every function is decomposed into a range reduction, one or two cores
on a bounded domain and a reconstruction; the declared family supplies
the core evaluator:
  exp2     2^x = 2^n * 2^f (n integer, f in [0,1)): core exp2c(f)
  exp      2^(x log2 e) through exp2
  log2     x = 2^E' m', m' in [0.75, 1.5): E' + d g(d), d = m' - 1,
           g(d) = log2(1+d)/d (the E' = 0 case keeps d normalized, so a
           result near zero keeps its relative precision)
  log      log2(x) ln 2
  recip    2^-E / m: core 1/(1+u) on u = m - 1
  sqrt     2^(E/2) sqrt(m) with E made even: core sqrt(1+w), w in [0,2)
  rsqrt    the same with 1/sqrt
  sin cos  x = (q + u) pi/2 (Cody-Waite or Payne-Hanek), sin(pi u/2) =
           u h(u) with h = sin(pi u/2)/u, the quadrant selects u or 1-u
           and the sign
  tanh     x t(x), t = tanh(x)/x on [0, T), 1 - tiny beyond T
  sigmoid  1/(1 + 2^(-x log2 e)): exp2c and the reciprocal core
  silu     x sigmoid(x)
  softplus log2(1 + 2^(x log2 e)) ln 2: exp2c and the log core
  erf      x e(x), e = erf(x)/x on [0, T), 1 - tiny beyond T
  gelu     x >= 0: x/2 (1 + x e(x)); x < 0: x/2 erfc(t) with t = |x|/sqrt2
           and erfc(t) = 2^(-t^2 log2 e) r(t), r = erfc(t) e^(t^2): exp2c
           and the core r on [0, T)
  softmax  the lanes as fixed-point values, the maximum subtracted, the
           exponential core, a reduction tree, the normalization by a
           divider, a reciprocal multiply or the log-domain subtraction
  layernorm the exact mean and variance, the rsqrt core, one multiply per lane
The core evaluators of the families:
  segmented polynomials (piecewise_poly, pwl, single_poly, lut_plus_poly,
  mixed_degree, region_dependent, pwl_residual_lut, gpu_multifunction_
  interpolator, sigmoid_tanh_pwl, transformer_activation_lut) over the
  segmenter families with the evaluator families and the coefficient
  encodings; table methods (direct_lut, compressed_lut, bipartite, stam,
  multipartite, add_table_add); rational_approximation with the divider
  slot; table_factor_refinement (Wong-Goto); logarithmic_converters
  (Mitchell with corrections); cordic and redundant_high_radix_cordic
  unrolled; digit_recurrence_exp_log unrolled; newton_raphson and
  goldschmidt over a seed table for recip/rsqrt/sqrt. A family whose
  engine does not cover a required core raises a generation error.
  The activation families
  (sigmoid_tanh_pwl, transformer_activation_lut) and the direct cores of
  the CORDIC, digit-recurrence and logarithmic engines return the
  function's value rather than the factored ratio, so a result near
  zero carries the engine's absolute rather than relative precision;
  the measured error reports it. The value tables (direct_lut,
  compressed_lut) serve formats of at most PATTERN_MAX_BITS bits. The
  reference of softplus is taken exactly above 4 (the verify layer's
  tail surrogate returns +huge there, which is exp's asymptote).
"""
from __future__ import annotations

import math
from fractions import Fraction
from functools import lru_cache, wraps
from contextvars import ContextVar

import mpmath

from chialu.targets.rtl.families.fp import Geom
from chialu.verify.formats import FloatFormat, PositFormat, X87Format, _mask

# ---- what the library realizes -----------------------------------------------------
SFU_FAMILIES = {"core": ("direct_lut", "compressed_lut", "bipartite", "stam", "multipartite", "add_table_add",
                         "pwl", "pwl_residual_lut", "piecewise_poly", "single_poly", "rational_approximation",
                         "lut_plus_poly", "table_factor_refinement", "region_dependent", "mixed_degree",
                         "gpu_multifunction_interpolator", "logarithmic_converters", "cordic",
                         "redundant_high_radix_cordic", "digit_recurrence_exp_log", "newton_raphson",
                         "goldschmidt", "sigmoid_tanh_pwl", "transformer_activation_lut", "softmax_layernorm")}
PATTERN_FAMILIES = ("direct_lut", "compressed_lut")      # pattern in, pattern out (the value tables)
PATTERN_MAX_BITS = 12                                     # a value table's widest format (4096 entries)
PROFILE_BITS = 60     # the working precision of the real-valued reference in mpmath (bits)


# ---- fixed-point netlist: Python evaluation and SystemVerilog from one description ------------
def _wrap(v: int, w: int, s: bool) -> int:
    v &= (1 << w) - 1
    if s and (v >> (w - 1)):
        v -= 1 << w
    return v


class Ref:
    __slots__ = ("name", "w", "s")

    def __init__(self, name: str, w: int, s: bool):
        self.name, self.w, self.s = name, w, s

    def __repr__(self):
        return f"{self.name}[{self.w}{'s' if self.s else ''}]"


class Net:
    """A combinational module: wires with a SystemVerilog expression and a
    Python evaluation each, ROMs, and the library modules it instantiates."""

    LIB_MIN_BITS = 4               # a primitive narrower than this stays the language's operator

    def __init__(self, name: str, comment: str, bind: dict | None = None):
        self.name, self.comment = name, comment
        self.ports: list = []          # (dir, Ref)
        self.decls: list = []          # SV lines in order
        self.evals: list = []          # (name, fn(env) -> int) in order
        self.extra: list = []          # texts of library modules instantiated
        self.extra_names: set = set()
        from .module_library import ModuleLibrary
        self._extra_library = ModuleLibrary()
        self.notes: list = []          # header notes (measured error, fallbacks)
        self.k = 0
        self.rom_bits = 0
        # the slot binding: kind ("multiplier", "adder", "shifter", "lzc") -> (family, pins); a bound primitive
        # renders through the library module of the family, its Python evaluation unchanged
        self.bind: dict = dict(bind or {})
        self.lib_uses: dict = {}
        # Structured construction records support selector-controlled resource
        # sharing without parsing Verilog or replacing the selected arithmetic.
        self.events: list = []
        self.stage = "range"
        self.core_index = 0
        self.memory_banks = {}
        self.refinement_stages = []
        self.algorithm_contracts = []

    def _bound(self, kind: str, w: int):
        """(family, pins) of a bound kind for a primitive of w bits, else None."""
        b = self.bind.get(kind)
        if not b or w < self.LIB_MIN_BITS:
            return None
        return b

    def _use(self, kind: str, module) -> None:
        self.lib_uses[kind] = self.lib_uses.get(kind, 0) + 1

    # -- naming / declaration
    def _nm(self, base: str) -> str:
        self.k += 1
        return f"{base}{self.k}"

    def wire(self, w: int, s: bool, sv: str, fn, base: str = "n") -> Ref:
        r = Ref(self._nm(base), w, s)
        rng = f"[{w-1}:0] " if w > 1 else ""
        self.decls.append(f"  logic {'signed ' if s else ''}{rng}{r.name}; assign {r.name} = {sv};")
        self.evals.append((r.name, fn))
        self.events.append(("wire", self.stage, r, sv))
        return r

    def port_in(self, name: str, w: int, s: bool = False) -> Ref:
        r = Ref(name, w, s)
        self.ports.append(("input", r))
        return r

    def port_out(self, name: str, src: Ref):
        r = Ref(name, src.w, src.s)
        self.ports.append(("output", r))
        self.decls.append(f"  assign {name} = {src.name};")
        self.evals.append((name, lambda env, a=src: env[a.name]))
        self.events.append(("output", self.stage, r, src))
        return r

    # -- constants and bit selection
    def const(self, v: int, w: int, s: bool = False) -> Ref:
        if w < 1:
            raise ValueError(f"SFU constant width must be positive, got {w}")
        low, high = (-(1 << (w - 1)), (1 << (w - 1)) - 1) if s else (0, (1 << w) - 1)
        if not low <= v <= high:
            raise ValueError(f"SFU constant {v} does not fit {'signed' if s else 'unsigned'} {w} bits; "
                             "constant truncation would change the requested circuit")
        v = _wrap(v, w, s)
        raw = v & ((1 << w) - 1)
        sv = f"{w}'d{raw}"
        if s:
            sv = f"$signed({sv})"
        return self.wire(w, s, sv, lambda env, v=v: v, "c")

    def bits(self, a: Ref, hi: int, lo: int = 0) -> Ref:
        assert 0 <= lo <= hi < a.w, (a, hi, lo)
        w = hi - lo + 1
        if a.w == 1:
            sv = a.name
        elif w == 1:
            sv = f"{a.name}[{hi}]"
        else:
            sv = f"{a.name}[{hi}:{lo}]"
        return self.wire(w, False, sv, lambda env, a=a, lo=lo, m=(1 << w) - 1, aw=a.w: ((env[a.name] & ((1 << aw) - 1)) >> lo) & m, "b")

    def bit(self, a: Ref, k: int) -> Ref:
        """One bit."""
        return self.bits(a, k, k)

    def cat(self, *refs: Ref) -> Ref:
        w = sum(r.w for r in refs)
        sv = "{" + ", ".join(r.name for r in refs) + "}"

        def fn(env, refs=refs):
            v = 0
            for r in refs:
                v = (v << r.w) | (env[r.name] & ((1 << r.w) - 1))
            return v
        return self.wire(w, False, sv, fn, "t")

    def ext(self, a: Ref, w: int) -> Ref:
        """a widened to w bits (sign- or zero-extended by its signedness)."""
        if w == a.w:
            return a
        assert w > a.w, (a, w)
        if a.s:
            top = f"{a.name}[{a.w-1}]" if a.w > 1 else a.name
            sv = f"$signed({{{{{w - a.w}{{{top}}}}}, {a.name}}})"
        else:
            sv = f"{{{{{w - a.w}{{1'b0}}}}, {a.name}}}"
        return self.wire(w, a.s, sv, lambda env, a=a: env[a.name], "x")

    def sgn(self, a: Ref) -> Ref:
        """An unsigned value as a signed one (one more bit)."""
        if a.s:
            return a
        return self.wire(a.w + 1, True, f"$signed({{1'b0, {a.name}}})", lambda env, a=a: env[a.name], "x")

    def as_signed(self, a: Ref) -> Ref:
        """The bits of an unsigned value read as a two's complement number."""
        if a.s:
            return a
        return self.wire(a.w, True, f"$signed({a.name})", lambda env, a=a, w=a.w: _wrap(env[a.name], w, True), "x")

    def uns(self, a: Ref) -> Ref:
        """The raw bits of a signed value."""
        if not a.s:
            return a
        return self.wire(a.w, False, f"$unsigned({a.name})", lambda env, a=a, m=(1 << a.w) - 1: env[a.name] & m, "x")

    # -- arithmetic
    def _same(self, a: Ref, b: Ref):
        if a.s != b.s:
            a, b = (self.sgn(a) if not a.s else a), (self.sgn(b) if not b.s else b)
        return a, b

    def _addsub(self, a: Ref, b: Ref, w: int | None, sub: bool) -> Ref:
        a, b = self._same(a, b)
        w = w or max(a.w, b.w) + 1
        op = "-" if sub else "+"
        fn = (lambda env, a=a, b=b, w=w, s=a.s: _wrap(env[a.name] - env[b.name], w, s)) if sub else \
             (lambda env, a=a, b=b, w=w, s=a.s: _wrap(env[a.name] + env[b.name], w, s))
        bound = self._bound("adder", w)
        if bound:
            from .binary_cpa import adder_module
            fam, pins = bound
            mod = adder_module(str(fam), pins, w)
            if mod is None:
                raise ValueError(f"SFU adder slot {fam!r} cannot generate {w} bits with pins {pins!r}")
            if mod is not None:
                fit = lambda x: self.ext(x, w) if x.w < w else (self.trunc(x, w) if x.w > w else x)
                ax, bx = fit(a), fit(b)
                if sub:
                    # a - b = a + ~b + 1 (the carry-in)
                    bx = self.wire(w, a.s, f"~{bx.name}", lambda env, x=bx, m=(1 << w) - 1: (~env[x.name]) & m, "l")
                out = self.declare(w, a.s, fn, "a")
                self.inst(mod, {"a": ax.name, "b": bx.name, "cin": "1'b1" if sub else "1'b0", "s": out.name, "cout": ""},
                          f"the adder slot: {a.name} {op} {b.name} through the library module {mod.name}")
                self._use("adder", mod)
                return out
        return self.wire(w, a.s, f"{a.name} {op} {b.name}", fn, "a")

    def add(self, a: Ref, b: Ref, w: int | None = None) -> Ref:
        return self._addsub(a, b, w, False)

    def sub(self, a: Ref, b: Ref, w: int | None = None) -> Ref:
        return self._addsub(a, b, w, True)

    def mul(self, a: Ref, b: Ref, lib: bool = True) -> Ref:
        a, b = self._same(a, b)
        w = a.w + b.w
        fn = lambda env, a=a, b=b, w=w, s=a.s: _wrap(env[a.name] * env[b.name], w, s)
        bound = self._bound("multiplier", min(a.w, b.w)) if lib else None
        if bound:
            from chialu.targets.rtl import families as FAM
            fam, pins = bound
            W = max(a.w, b.w)
            mod = FAM.mul_module(str(fam), pins, W, a.s)
            if mod is None:
                raise ValueError(f"SFU multiplier slot {fam!r} cannot generate {W} bits with pins {pins!r}")
            if mod is not None:
                ax, bx = self.ext(a, W), self.ext(b, W)
                pw = 2 * W
                pr = self.declare(pw, a.s, lambda env, a=a, b=b, pw=pw, s=a.s: _wrap(env[a.name] * env[b.name], pw, s), "m")
                self.inst(mod, {"a": ax.name, "b": bx.name, "p": pr.name},
                          f"the multiplier slot: {a.name} * {b.name} through the library module {mod.name}")
                self._use("multiplier", mod)
                return self.trunc(pr, w) if pw > w else pr
        return self.wire(w, a.s, f"{a.name} * {b.name}", fn, "m")

    def mulc(self, a: Ref, c: int, cw: int) -> Ref:
        """a times a constant of cw bits (signed when the constant is negative or a is signed); a constant
        multiplication stays the language's operator (synthesis folds it into shifts and adds)."""
        s = a.s or c < 0
        k = self.const(c, cw, s)
        return self.mul(a if a.s == s else self.sgn(a), k, lib=False)

    def neg(self, a: Ref) -> Ref:
        a = self.sgn(a)
        w = a.w + 1
        return self.wire(w, True, f"-{a.name}", lambda env, a=a, w=w: _wrap(-env[a.name], w, True), "a")

    def shl(self, a: Ref, k: int) -> Ref:
        if k == 0:
            return a
        w = a.w + k
        sv = f"{{{a.name}, {k}'d0}}"
        if a.s:
            sv = f"$signed({sv})"
        return self.wire(w, a.s, sv, lambda env, a=a, k=k: env[a.name] << k, "s")

    def shr(self, a: Ref, k: int) -> Ref:
        """The value floored by 2^k (an arithmetic shift): the top bits."""
        if k == 0:
            return a
        if k >= a.w:
            if not a.s:
                return self.const(0, 1, False)
            return self.wire(1, True, f"$signed({a.name}[{a.w-1}])", lambda env, a=a: -1 if env[a.name] < 0 else 0, "s")
        w = a.w - k
        sv = f"{a.name}[{a.w-1}:{k}]" if w > 1 else f"{a.name}[{a.w-1}]"
        if a.s:
            sv = f"$signed({sv})"
        return self.wire(w, a.s, sv, lambda env, a=a, k=k: env[a.name] >> k, "s")

    def _shift_lib(self, a: Ref, amt: Ref, w: int, opcode: int, fn, fill: str, comment: str):
        """a shifted by amt through the bound shifter (None when unbound): the amount clamped to the
        module's range, a shift by w or more giving the fill (zeros, or the sign for an arithmetic shift)."""
        bound = self._bound("shifter", w)
        if not bound:
            return None
        from chialu.targets.rtl import families as FAM
        from chialu.targets.rtl.families.fp import _clog2
        fam, pins = bound
        f = str(fam)
        if f == "butterfly_network" and w & (w - 1):
            raise ValueError(f"SFU shifter slot butterfly_network requires a power-of-two width; got {w}")
        mod = FAM.shifter_module(f, pins, w)
        if mod is None:
            raise ValueError(f"SFU shifter slot {f!r} cannot generate {w} bits with pins {pins!r}")
        aw = _clog2(w)
        if (1 << amt.w) > w:
            big = self.wire(1, False, f"({amt.name} >= {w})", lambda env, amt=amt, w=w: 1 if env[amt.name] >= w else 0, "f")
            am = self.wire(aw, False, f"{big.name} ? {aw}'d0 : {amt.name}[{aw-1}:0]" if amt.w > aw else f"{big.name} ? {aw}'d0 : {amt.name}",
                           lambda env, amt=amt, w=w, m=(1 << aw) - 1: 0 if env[amt.name] >= w else env[amt.name] & m, "s")
        else:
            big = None
            am = self.ext(amt, aw) if amt.w < aw else amt
        out = self.declare(w, a.s, fn, "s")
        self.inst(mod, {"a": a.name, "amt": am.name, "op": f"3'd{opcode}", "y": out.name, "sticky": ""}, comment)
        self._use("shifter", mod)
        if big is None:
            return out
        return self.wire(w, a.s, f"{big.name} ? {fill} : {out.name}", fn, "s")

    def shlv(self, a: Ref, amt: Ref, w: int) -> Ref:
        """a << amt into w bits (the high bits fall off)."""
        assert not amt.s
        a2 = self.ext(a, w) if a.w < w else a
        fn = lambda env, a=a, amt=amt, w=w, s=a.s: _wrap(env[a.name] << env[amt.name], w, s)
        lib = self._shift_lib(a2, amt, w, 0, fn, f"{w}'d0", f"the shifter slot: {a2.name} << {amt.name} through the library shifter")
        if lib is not None:
            return lib
        sv = f"{a2.name} << {amt.name}" if not a.s else f"{a2.name} <<< {amt.name}"
        return self.wire(w, a.s, sv, fn, "s")

    def shrv(self, a: Ref, amt: Ref) -> Ref:
        assert not amt.s
        fn = lambda env, a=a, amt=amt: env[a.name] >> env[amt.name]
        fill = f"{{{a.w}{{{a.name}[{a.w-1}]}}}}" if a.s else f"{a.w}'d0"
        lib = self._shift_lib(a, amt, a.w, 2 if a.s else 1, fn, fill, f"the shifter slot: {a.name} >> {amt.name} through the library shifter")
        if lib is not None:
            return lib
        sv = f"{a.name} >> {amt.name}" if not a.s else f"{a.name} >>> {amt.name}"
        return self.wire(a.w, a.s, sv, fn, "s")

    def trunc(self, a: Ref, w: int) -> Ref:
        """The low w bits, keeping the signedness (a value known to fit)."""
        if w == a.w:
            return a
        assert w < a.w
        sv = f"{a.name}[{w-1}:0]" if w > 1 else f"{a.name}[0]"
        if a.s:
            sv = f"$signed({sv})"
        return self.wire(w, a.s, sv, lambda env, a=a, w=w, s=a.s: _wrap(env[a.name], w, s), "b")

    # -- compare, select, logic
    def _cmp(self, op: str, a: Ref, b: Ref, py) -> Ref:
        a, b = self._same(a, b)
        return self.wire(1, False, f"({a.name} {op} {b.name})", lambda env, a=a, b=b, py=py: 1 if py(env[a.name], env[b.name]) else 0, "f")

    def eq(self, a, b): return self._cmp("==", a, b, lambda x, y: x == y)
    def ne(self, a, b): return self._cmp("!=", a, b, lambda x, y: x != y)
    def lt(self, a, b): return self._cmp("<", a, b, lambda x, y: x < y)
    def le(self, a, b): return self._cmp("<=", a, b, lambda x, y: x <= y)
    def gt(self, a, b): return self._cmp(">", a, b, lambda x, y: x > y)
    def ge(self, a, b): return self._cmp(">=", a, b, lambda x, y: x >= y)

    def eqc(self, a: Ref, c: int) -> Ref:
        return self.eq(a, self.const(c, a.w, a.s))

    def mux(self, c: Ref, a: Ref, b: Ref) -> Ref:
        """c ? a : b (a and b brought to one width and signedness)."""
        assert c.w == 1
        a, b = self._same(a, b)
        w = max(a.w, b.w)
        a, b = self.ext(a, w), self.ext(b, w)
        return self.wire(w, a.s, f"{c.name} ? {a.name} : {b.name}",
                         lambda env, c=c, a=a, b=b: env[a.name] if env[c.name] else env[b.name], "u")

    def land(self, *rs: Ref) -> Ref:
        rs = [r for r in rs if r is not None]
        return self.wire(1, False, "(" + " && ".join(r.name for r in rs) + ")",
                         lambda env, rs=rs: 1 if all(env[r.name] for r in rs) else 0, "f")

    def lor(self, *rs: Ref) -> Ref:
        rs = [r for r in rs if r is not None]
        return self.wire(1, False, "(" + " || ".join(r.name for r in rs) + ")",
                         lambda env, rs=rs: 1 if any(env[r.name] for r in rs) else 0, "f")

    def lnot(self, a: Ref) -> Ref:
        return self.wire(1, False, f"!{a.name}", lambda env, a=a: 0 if env[a.name] else 1, "f")

    def bor(self, a: Ref, b: Ref) -> Ref:
        assert a.w == b.w and not a.s and not b.s
        return self.wire(a.w, False, f"({a.name} | {b.name})", lambda env, a=a, b=b: env[a.name] | env[b.name], "l")

    def band(self, a: Ref, b: Ref) -> Ref:
        assert a.w == b.w and not a.s and not b.s
        return self.wire(a.w, False, f"({a.name} & {b.name})", lambda env, a=a, b=b: env[a.name] & env[b.name], "l")

    def bxor(self, a: Ref, b: Ref) -> Ref:
        assert a.w == b.w and not a.s and not b.s
        return self.wire(a.w, False, f"({a.name} ^ {b.name})", lambda env, a=a, b=b: env[a.name] ^ env[b.name], "l")

    def bnot(self, a: Ref) -> Ref:
        assert not a.s
        return self.wire(a.w, False, f"~{a.name}", lambda env, a=a, m=(1 << a.w) - 1: (~env[a.name]) & m, "l")

    def ror(self, a: Ref) -> Ref:
        """The OR of all bits."""
        a = self.uns(a)
        return self.wire(1, False, f"(|{a.name})", lambda env, a=a: 1 if env[a.name] else 0, "f")

    def nz(self, a: Ref) -> Ref:
        return self.ror(a)

    # -- tables
    def rom(self, table: list, idx: Ref, w: int, s: bool = False, base: str = "rom", bank=None) -> Ref:
        """table[idx] (0 beyond the table), an initial-block memory."""
        assert not idx.s
        n = len(table)
        name = self._nm(base)
        m = (1 << w) - 1
        vals = [_wrap(v, w, s) for v in table]
        rng = f"[{w-1}:0] " if w > 1 else ""
        if bank is not None and bank in self.memory_banks:
            memory, previous, width = self.memory_banks[bank]
            if previous != vals or width != w:
                raise ValueError(f"SFU memory bank {bank!r} has inconsistent contents or width")
        else:
            memory = f"{name}_t"
            self.decls.append(f"  logic {rng}{memory} [0:{n-1}];")
            self.decls.append("  initial begin " + " ".join(f"{memory}[{i}]={w}'d{v & m};" for i, v in enumerate(vals)) + " end")
            self.rom_bits += n * w
            if bank is not None:
                self.memory_banks[bank] = (memory, vals, w)
        full = n >= (1 << idx.w)
        rd = f"{memory}[{idx.name}]" if full else f"(({idx.name} < {idx.w}'d{n}) ? {memory}[{idx.name}] : {w}'d0)"
        if s:
            rd = f"$signed({rd})"
        r = Ref(name, w, s)
        self.decls.append(f"  logic {'signed ' if s else ''}{rng}{name}; assign {name} = {rd};")
        self.evals.append((name, lambda env, t=vals, idx=idx: t[env[idx.name]] if env[idx.name] < len(t) else 0))
        self.events.append(("rom", self.stage, r, (vals, idx, bank)))
        return r

    # -- leading zeros: a recursive doubling tree of the netlist itself
    def lzc(self, a: Ref) -> Ref:
        """The leading-zero count of a (unsigned), clog2(w+1) bits; a zero word counts w."""
        a = self.uns(a)
        w = a.w
        nw = w.bit_length()
        if w == 1:
            return self.lnot(a)
        bound = self._bound("lzc", w)
        if bound:
            from chialu.targets.rtl import families as FAM
            fam, pins = bound
            mod = FAM.lzc_module(str(fam), pins, w)
            if mod is None:
                raise ValueError(f"SFU lzc slot {fam!r} cannot generate {w} bits with pins {pins!r}")
            if mod is not None:
                def fn(env, a=a, w=w):
                    v = env[a.name] & ((1 << w) - 1)
                    return w - v.bit_length()
                out = self.declare(nw, False, fn, "z")
                self.inst(mod, {"a": a.name, "n": out.name}, f"the lzc slot: the leading zeros of {a.name} through the library module {mod.name}")
                self._use("lzc", mod)
                return out
        h = 1 << (w.bit_length() - 1)
        if h == w:
            h //= 2
        hi, lo = self.bits(a, w - 1, w - h), self.bits(a, w - h - 1, 0)
        hz = self.eqc(hi, 0)
        chi, clo = self.lzc(hi), self.lzc(lo)
        off = self.const(h, nw)
        return self.mux(hz, self.add(off, self.ext(clo, nw), nw), self.ext(chi, nw))

    # -- library modules
    def inst(self, module, conns: dict, comment: str) -> None:
        """Instantiate a library Module (its text joins this module's)."""
        from chialu.targets.rtl import families as FAM
        for n_, t_ in FAM.module_texts(module.name, module.text).items():
            self._extra_library[n_] = t_
            if n_ not in self.extra_names:
                self.extra_names.add(n_)
                self.extra.append(t_)
        ps = ", ".join(f".{k}({v})" for k, v in module.params.items())
        cs = ", ".join(f".{k}({v})" for k, v in conns.items())
        self.k += 1
        self.decls.append(f"  // {comment}")
        self.decls.append(f"  {module.name} " + (f"#({ps}) " if ps else "") + f"u_lib{self.k} ({cs});")
        self.events.append(("instance", self.stage, None, (module, dict(conns))))

    def declare(self, w: int, s: bool, fn, base: str = "w") -> Ref:
        """A wire another construct drives (a library instance): declared here, evaluated by fn."""
        r = Ref(self._nm(base), w, s)
        rng = f"[{w-1}:0] " if w > 1 else ""
        self.decls.append(f"  logic {'signed ' if s else ''}{rng}{r.name};")
        self.evals.append((r.name, fn))
        self.events.append(("declare", self.stage, r, None))
        return r

    # -- evaluation and rendering
    def run(self, inputs: dict) -> dict:
        """Evaluate every output (and what it depends on) for the input
        values: the wires resolve on demand, in dependency order."""
        import sys
        fns = dict(self.evals)

        class LazyEnv(dict):
            def __missing__(self_, name):
                v = fns[name](self_)
                self_[name] = v
                return v
        env = LazyEnv(inputs)
        if sys.getrecursionlimit() < 20000:
            sys.setrecursionlimit(20000)
        for d, r in self.ports:
            if d == "output":
                env[r.name]
        for name, _fn in self.evals:
            env[name]
        return env

    def render(self) -> str:
        from chialu.targets.rtl.families.mul import dedupe_modules
        head = [f"// {self.comment}"] + [f"// {n}" for n in self.notes]
        ports = []
        for d, r in self.ports:
            rng = f"[{r.w-1}:0] " if r.w > 1 else ""
            ports.append(f"  {d} logic {'signed ' if r.s else ''}{rng}{r.name}")
        text = "\n".join(head + [f"module {self.name} (", ",\n".join(ports), ");"] + self.decls + ["endmodule", ""])
        return dedupe_modules(text + "".join(self.extra))


# ---- the real-valued cores ----------------------------------------------------------------
class Core:
    """A smooth function g on [0, L) (L = 1 or 2) that a family's engine
    approximates: `f` evaluates it in mpmath at PROFILE_BITS, `lo`/`hi`
    bound the used part of the domain (the segments outside it are never
    indexed), `gmin`/`gmax` bound the values (the integer bits of the
    result and the extra fraction bits a small value needs for its
    relative precision)."""

    def __init__(self, name: str, f, L: float = 1.0, lo: float = 0.0, hi: float | None = None, even_in=None):
        self.name, self.f, self.L, self.lo = name, f, Fraction(L), Fraction(lo)
        self.hi = Fraction(L if hi is None else hi)
        self.even_in = even_in           # the variable the function is even in (an odd function's f(x)/x)
        self.T = 1.0                     # the argument scale of the x-domain cores
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            xs = [mpmath.mpf(self.lo) + (mpmath.mpf(self.hi) - self.lo) * i / 512 for i in range(512)]
            xs.append(mpmath.mpf(self.hi) - mpmath.mpf(2) ** -40)
            ys = [self.f(x) for x in xs]
        self.gmin, self.gmax = float(min(ys)), float(max(ys))

    def ibits(self) -> int:
        """Integer bits of the result (the values are positive)."""
        return max(1, int(math.floor(math.log2(self.gmax * 1.0001))) + 1)

    def extra_frac(self) -> int:
        """Fraction bits beyond the guard a result near gmin needs to keep its relative precision."""
        return max(0, int(math.ceil(-math.log2(max(self.gmin, 1e-30)))))


def _mp(x):
    return mpmath.mpf(x)


def core_of(kind: str, T: float = 1.0) -> Core:
    """The named core; T scales the argument of the x-domain cores."""
    pi = mpmath.pi
    if kind == "exp2c":
        return Core("exp2c", lambda u: mpmath.power(2, u))
    if kind == "log2c":     # g(d) = log2(1+d)/d on d = u - 1/4, u in [0, 3/4)
        def g(u):
            d = u - mpmath.mpf(1) / 4
            return (mpmath.log(1 + d, 2) / d) if d != 0 else 1 / mpmath.log(2)
        return Core("log2c", g, 1.0, 0.0, 0.75)
    if kind == "recipc":
        return Core("recipc", lambda u: 1 / (1 + u))
    if kind == "sqrtc":     # sqrt(1+w) below 1, sqrt(2w) from 1
        return Core("sqrtc", lambda w: mpmath.sqrt(1 + w) if w < 1 else mpmath.sqrt(2 * w), 2.0)
    if kind == "rsqrtc":
        return Core("rsqrtc", lambda w: 1 / mpmath.sqrt(1 + w) if w < 1 else 1 / mpmath.sqrt(2 * w), 2.0)
    if kind == "sinc":      # sin(pi u/2) / (pi u/2)
        def g(u):
            return (mpmath.sin(pi * u / 2) / (pi * u / 2)) if u != 0 else mpmath.mpf(1)
        return Core("sinc", g, 1.0, 0.0, 1.0, even_in="u")
    if kind == "tanhc":     # tanh(T u) / (T u)
        def g(u):
            return (mpmath.tanh(T * u) / (T * u)) if u != 0 else mpmath.mpf(1)
        c = Core("tanhc", g, 1.0, 0.0, 1.0, even_in="u"); c.T = T
        return c
    if kind == "erfe":      # erf(T u) / (T u)
        def g(u):
            return (mpmath.erf(T * u) / (T * u)) if u != 0 else 2 / mpmath.sqrt(pi)
        c = Core("erfe", g, 1.0, 0.0, 1.0, even_in="u"); c.T = T
        return c
    if kind == "gelue":     # erf(T u / sqrt2) / (T u): 1 + x E(x) = 1 + erf(x/sqrt2)
        def g(u):
            x = T * u
            return (mpmath.erf(x / mpmath.sqrt(2)) / x) if u != 0 else mpmath.sqrt(2 / pi)
        c = Core("gelue", g, 1.0, 0.0, 1.0, even_in="u"); c.T = T
        return c
    if kind == "gelur":     # erfc(x/sqrt2) e^(x^2/2), x = T u
        def g(u):
            x = T * u
            return mpmath.erfc(x / mpmath.sqrt(2)) * mpmath.exp(x * x / 2)
        c = Core("gelur", g, 1.0, 0.0, 1.0); c.T = T
        return c
    if kind == "expm1c":    # (2^u - 1) / u
        def g(u):
            return ((mpmath.power(2, u) - 1) / u) if u != 0 else mpmath.log(2)
        return Core("expm1c", g)
    # the direct cores of the activation families (the function itself over the scaled argument)
    if kind == "sigd":      # sigmoid(T u), u in [0, 1)
        c = Core("sigd", lambda u: 1 / (1 + mpmath.exp(-T * u)))
    elif kind == "sigd2":   # sigmoid(T (2u - 1))
        c = Core("sigd2", lambda u: 1 / (1 + mpmath.exp(-T * (2 * u - 1))))
    elif kind == "tanhd":   # tanh(T u)
        c = Core("tanhd", lambda u: mpmath.tanh(T * u))
    elif kind == "tanhd2h":  # (1 + tanh(T (2u - 1))) / 2
        c = Core("tanhd2h", lambda u: (1 + mpmath.tanh(T * (2 * u - 1))) / 2)
    elif kind == "erfd":    # erf(T u)
        c = Core("erfd", lambda u: mpmath.erf(T * u))
    elif kind == "gelud":   # erf(T u / sqrt2)
        c = Core("gelud", lambda u: mpmath.erf(T * u / mpmath.sqrt(2)))
    elif kind == "spd":     # softplus(T (2u - 1))
        c = Core("spd", lambda u: mpmath.log(1 + mpmath.exp(T * (2 * u - 1))))
    else:
        raise ValueError(kind)
    c.T = T
    return c


_fit_precision = ContextVar("sfu_coefficient_work_precision", default=PROFILE_BITS)


def _fraction_of_mp(value):
    sign, mantissa, exponent, _ = value._mpf_
    exact = Fraction(int(mantissa)) * Fraction(2) ** int(exponent)
    return -exact if sign else exact


def _polynomial_precision(function):
    @wraps(function)
    def build(self, *args, **kwargs):
        precision = max(PROFILE_BITS, 2 * (self.coeff_frac or self.Fint) + self.Fu + 32)
        self.coefficient_work_precision = precision
        token = _fit_precision.set(precision)
        try:
            return function(self, *args, **kwargs)
        finally:
            _fit_precision.reset(token)
    return build


# ---- polynomial fits ---------------------------------------------------------------------
def _fit_poly(g, a, b, d: int, basis: str, precision=None) -> list:
    """Fit with arbitrary precision, returning exact fractions of the computed coefficients."""
    bits = max(PROFILE_BITS, int(precision or _fit_precision.get()))
    with mpmath.workprec(bits):
        left, right = _mp(a), _mp(b)
        h = right - left
        if h <= 0:
            return [_fraction_of_mp(g(left))] + [Fraction(0)] * d
        if basis == "taylor":
            mid = left + h / 2
            local = mpmath.taylor(g, mid, d)
            coefficients = [mpmath.mpf(0)] * (d + 1)
            for k, value in enumerate(local):
                for j in range(k + 1):
                    coefficients[j] += value * mpmath.binomial(k, j) * (-h / 2) ** (k - j)
            return [_fraction_of_mp(value) for value in coefficients]
        coefficients = list(reversed(mpmath.chebyfit(lambda t: g(left + t), [0, h], d + 1)))
        if basis != "minimax_remez" or d == 0:
            return [_fraction_of_mp(value) for value in coefficients]
        count = d + 2
        nodes = [h / 2 * (1 - mpmath.cos(mpmath.pi * i / (count - 1))) for i in range(count)]
        grid = [h * i / 2048 for i in range(2049)]
        truth = [g(left + t) for t in grid]
        for _ in range(12):
            matrix = mpmath.matrix([[t ** k for k in range(d + 1)] + [(-1) ** i]
                                    for i, t in enumerate(nodes)])
            rhs = mpmath.matrix([g(left + t) for t in nodes])
            try:
                solution = mpmath.lu_solve(matrix, rhs)
            except (ZeroDivisionError, ValueError):
                break
            coefficients = list(solution[:d + 1])
            errors = [value - sum(c * t ** k for k, c in enumerate(coefficients)) for t, value in zip(grid, truth)]
            extrema = []
            for i, error in enumerate(errors):
                before = errors[i - 1] if i else error
                after = errors[i + 1] if i + 1 < len(errors) else error
                if (error >= before and error >= after and error > 0) or (error <= before and error <= after and error < 0):
                    if extrema and (extrema[-1][1] > 0) == (error > 0):
                        if abs(error) > abs(extrema[-1][1]):
                            extrema[-1] = (grid[i], error)
                    else:
                        extrema.append((grid[i], error))
            if len(extrema) < count:
                break
            while len(extrema) > count:
                extrema.pop(0 if abs(extrema[0][1]) < abs(extrema[-1][1]) else -1)
            updated = [point for point, _ in extrema]
            if max(abs(x - y) for x, y in zip(updated, nodes)) < h * mpmath.power(2, -min(bits // 2, 64)):
                break
            nodes = updated
        return [_fraction_of_mp(value) for value in coefficients]


def _quantize(c: float, fbits: int) -> int:
    return int(round(c * (1 << fbits)))


def _csd(v: int, fbits: int, width: int) -> list:
    """The canonical signed-digit form of an integer v (|v| < 2^width): [(sign, position)] of the nonzero digits, position = the bit weight."""
    digits = []
    x = v
    p = 0
    while x != 0:
        if x & 1:
            d = 2 - (x & 3)          # 1 -> +1, 3 -> -1
            digits.append((1 if d < 0 else 0, p))
            x -= d
        x >>= 1
        p += 1
    return digits


def _po2(c: float) -> tuple:
    """(sign, exponent) of the power of two nearest to c (0 -> a zero flag)."""
    if c == 0:
        return (0, None)
    from chialu.verify.formats import _floor_log2
    value = abs(Fraction(c))
    e = _floor_log2(value)
    lower = Fraction(2) ** e
    if value * value >= 2 * lower * lower:
        e += 1
    return (1 if c < 0 else 0, e)


def _sample_err(g, coeffs: list, a: float, b: float, fq: list, scale: float, n: int = 65) -> float:
    """The max |p(t) - g(a + t)| over n points of [0, b - a] with the coefficients quantized at fq fraction bits each (scale: t-domain scale)."""
    with mpmath.workprec(max(_fit_precision.get(), max(fq) + 32)):
        worst = mpmath.mpf(0)
        left, right = _mp(a), _mp(b)
        h = right - left
        for i in range(n + 1):
            t = h * i / n
            p = sum((_mp(cq) / (1 << fb)) * t ** k for k, (cq, fb) in enumerate(zip(coeffs, fq)))
            e = abs(g(left + t) - p)
            worst = max(worst, e)
        return _fraction_of_mp(worst)


# ---- segmenters: the segment index and the local variable of u ------------------------------
class Segments:
    """A partition of [0, L) into K segments: `starts` on the u grid of Fu
    fraction bits (integers, ascending, starts[0] = 0), `ends`, and per
    segment the shift that brings the local variable u - start into
    [0, 1) as a fraction (width * 2^shift <= 1)."""

    def __init__(self, Fu: int, L: float, starts: list, ends: list, shifts: list):
        self.Fu, self.L, self.starts, self.ends, self.shifts = Fu, L, starts, ends, shifts

    @property
    def K(self):
        return len(self.starts)

    def bounds(self, k: int) -> tuple:
        """(a, b) of segment k in u units."""
        return Fraction(self.starts[k], 1 << self.Fu), Fraction(self.ends[k], 1 << self.Fu)


def _uniform(Fu: int, L: float, K: int) -> Segments:
    """Exactly K equal-width segments, quantized onto the argument grid."""
    n = int(round(L * (1 << Fu)))
    if not 1 <= K <= n:
        raise ValueError(f"{K} segments require at least {K} distinct argument values; geometry has {n}")
    starts = [(k * n + K - 1) // K for k in range(K)]
    ends = starts[1:] + [n]
    return Segments(Fu, L, starts, ends, _shifts_of(Fu, starts, ends))


def _po2_segments(Fu: int, L: float, K: int, near_zero: bool = True) -> Segments:
    """Log-spaced boundaries at 2^-i (K - 1 of them) with the residue near
    zero as the last segment: the segments shrink toward 0."""
    n = int(round(L * (1 << Fu)))
    if L > 1:
        # [1, 2) is one segment, the power-of-two ladder below 1
        starts = [0]
        bnds = [n >> (i + 1) for i in range(K - 2, -1, -1)]          # 2^-(K-1) L ... L/2
        starts = [0] + bnds
    else:
        starts = [0] + [n >> (K - 1 - i) for i in range(K - 1)]
    starts = sorted(set(s for s in starts if s < n))
    if len(starts) != K:
        raise ValueError(f"power-of-two segmentation requested {K} segments but {Fu} fraction bits allow "
                         f"only {len(starts)} distinct segments; increase the target precision")
    ends = starts[1:] + [n]
    return Segments(Fu, L, starts, ends, _shifts_of(Fu, starts, ends))


def _shifts_of(Fu: int, starts: list, ends: list) -> list:
    """Per segment the largest shift with width * 2^shift <= 2^Fu."""
    shifts = []
    for s, e in zip(starts, ends):
        w = e - s
        sh = 0
        while (w << (sh + 1)) <= (1 << Fu):
            sh += 1
        shifts.append(sh)
    return shifts


def _curvature_split(g, Fu: int, L: float, K: int, lo: float, hi: float, d: int, basis: str, grid_bits: int,
                     method: str) -> Segments:
    """Nonuniform boundaries on a grid of 2^grid_bits cells: greedy
    (split the segment with the largest fit error), dynamic programming
    (the partition of the grid cells minimizing the largest error, by a
    bisection on the error bound) or analytic curvature (cell widths
    proportional to |g''|^(-1/2) for degree 1, |g'''|^(-1/3) for 2)."""
    n = int(round(L * (1 << Fu)))
    cells = 1 << grid_bits
    cw = n // cells
    used = max(1, min(cells, int(math.ceil(hi / L * cells))))
    fold = cells // 2 if L > 1 else None            # the root cores fold at w = 1: a segment never spans it
    with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
        def seg_err(c0, c1):
            if fold is not None and c0 < fold < c1:
                return float("inf")
            a, b = c0 * cw / (1 << Fu), c1 * cw / (1 << Fu)
            c = _fit_poly(g, a, b, d, basis)
            return _sample_err(g, [_quantize(x, 40) for x in c], a, b, [40] * (d + 1), 1.0, 24)
        if method == "quantile":
            # boundaries at the quantiles of a standard normal over the argument T u (denser near zero)
            Tq = getattr(g, "T", 1.0) if not callable(g) else 1.0
            bounds = [0]
            for kq in range(1, K):
                q = mpmath.erfinv(mpmath.mpf(kq) / K)            # P(|X| < x) = kq / K for X ~ N(0, 1)
                x = float(q * mpmath.sqrt(2)) / Tq
                cell = int(x / (hi / used) ) if hi > 0 else 0
                cell = max(bounds[-1] + 1, min(used - 1, cell))
                if cell < used:
                    bounds.append(cell)
            bounds = sorted(set(bounds))
        elif method == "analytic_curvature":
            k = d + 1
            ws = []
            for i in range(used):
                a = (i + 0.5) * cw / (1 << Fu)
                dk = abs(float(mpmath.diff(g, _mp(a), k))) + 1e-12
                ws.append(dk ** (1.0 / k))
            total = sum(ws)
            # cumulative weight split into K parts
            bounds = [0]
            acc = 0.0
            for i, w in enumerate(ws):
                acc += w
                while len(bounds) < K and acc >= total * len(bounds) / K and i + 1 not in bounds and i + 1 < used:
                    bounds.append(i + 1)
            if fold is not None:
                bounds.append(fold)
            bounds = sorted(set(bounds))[:K]
        elif method == "dynamic_programming":
            # bisection on the error bound: the fewest segments covering [0, used) under the bound
            errs = {}

            def E(i, j):
                if (i, j) not in errs:
                    errs[(i, j)] = seg_err(i, j)
                return errs[(i, j)]
            lo_e, hi_e = 0.0, max(seg_err(0, fold), seg_err(fold, used)) if fold is not None else seg_err(0, used)
            best = None
            for _ in range(14):
                mid = (lo_e + hi_e) / 2
                # greedy longest segments under the bound is optimal for a count objective on an interval
                bounds, i = [0], 0
                ok = True
                while i < used:
                    j = used
                    while j > i + 1 and E(i, j) > mid:
                        j -= 1
                    if E(i, j) > mid and j == i + 1:
                        pass
                    bounds.append(j)
                    i = j
                    if len(bounds) > K + 1:
                        ok = False
                        break
                if ok:
                    best = bounds
                    hi_e = mid
                else:
                    lo_e = mid
            bounds = best[:-1] if best else [i * used // K for i in range(K)]
            if fold is not None and fold not in bounds:
                bounds = sorted(set(bounds + [fold]))[:K]
        else:   # greedy_error_driven
            bounds = [0, used] if fold is None else [0, fold, used]
            while len(bounds) - 1 < K:
                worst, wi = -1.0, 0
                for i in range(len(bounds) - 1):
                    if bounds[i + 1] - bounds[i] < 2:
                        continue
                    e = seg_err(bounds[i], bounds[i + 1])
                    if e > worst:
                        worst, wi = e, i
                if worst < 0:
                    break
                a, b = bounds[wi], bounds[wi + 1]
                bounds.insert(wi + 1, (a + b) // 2)
            bounds = bounds[:-1]
    starts = [b * cw for b in bounds]
    ends = starts[1:] + [n]
    return Segments(Fu, L, starts, ends, _shifts_of(Fu, starts, ends))


# ---- the segmented-polynomial engine -----------------------------------------------------------
_EVALUATORS = ("horner", "estrin", "parallel_monomial", "factored", "coefficient_adapted", "shift_add_coeff",
               "fma_based")
_SEGMENTERS = ("uniform_high_bit_decode", "nonuniform", "hierarchical", "power_of_two", "ralut")


def _pin(pins: dict, key: str, default):
    v = (pins or {}).get(key, default)
    return default if v in (None, "") else v


def _smooth_root_argument(net, core, argument, fraction_bits):
    """Give a single root approximator a smooth domain (m-1)/4 in [0,3/4).

    The engine's conventional root argument w describes m as 1+w below
    one and 2w above one. That representation is continuous but has a
    derivative discontinuity at one, so a single Taylor fit cannot use it.
    """
    if core.name not in ("sqrtc", "rsqrtc") or core.L != 2:
        return core, argument, fraction_bits
    upper = net.bit(argument, fraction_bits)
    width = fraction_bits + 2
    original = net.ext(argument, width)
    doubled = net.shl(original, 1)
    shifted = net.sub(doubled, net.const(1 << fraction_bits, doubled.w), doubled.w)
    mapped = net.mux(upper, net.trunc(shifted, width), original)
    function = (lambda value: mpmath.sqrt(1 + 4 * value)) if core.name == "sqrtc" else \
        (lambda value: 1 / mpmath.sqrt(1 + 4 * value))
    return Core(core.name, function, 1.0, 0.0, 0.75), mapped, fraction_bits + 2


class PolyEngine:
    """A core evaluated by segmented polynomials: the segmenter family
    yields the segment index and the local variable, coefficient ROMs
    hold the fitted, quantized and encoded coefficients, the evaluator
    family forms the polynomial. `build(u)` takes u (Fu fraction bits,
    the value u/2^Fu in [0, L)) and returns R with Fo fraction bits."""

    def __init__(self, net: Net, core: Core, Fu: int, Fo: int, *, K: int = 8, degree: int = 1, basis: str = "taylor",
                 encoding: str = "plain", segmenter: str = "uniform_high_bit_decode", evaluator: str = "horner",
                 addressing: str = "direct_address_bits", boundary_search: str = "greedy_error_driven",
                 coeff_frac: int | None = None, x_frac: int | None = None, mixed_max_degree: int | None = None,
                 joint_search: bool = False, mult_shape: str = "full_square", residual_bits: int = 0,
                 label: str = ""):
        self.net, self.core, self.Fu, self.Fo = net, core, Fu, Fo
        self.K, self.degree, self.basis, self.encoding = K, degree, basis, encoding
        self.segmenter, self.evaluator, self.addressing, self.boundary_search = segmenter, evaluator, addressing, boundary_search
        self.coeff_frac = coeff_frac
        self.x_frac = x_frac
        self.mixed_max_degree = mixed_max_degree
        self.joint_search = joint_search
        self.mult_shape = mult_shape
        self.residual_bits = residual_bits
        self.label = label
        self.Fint = Fo + 2                       # internal fraction bits of the evaluation
        self.notes: list = []
        self.table_bits = 0

    # -- the partition
    def _segments(self) -> Segments:
        Fu, L, K = self.Fu, self.core.L, self.K
        g = self.core.f
        if self.segmenter == "uniform_high_bit_decode":
            return _uniform(Fu, L, K)
        if self.segmenter == "power_of_two":
            return _po2_segments(Fu, L, K)
        if self.segmenter == "hierarchical":
            # a coarse split of 4 regions, each subdivided uniformly with a count from its fit error
            coarse = 4 if K >= 8 else 2
            base = _uniform(Fu, L, coarse)
            errs = []
            for r in range(coarse):
                a, b = base.bounds(r)
                if a >= self.core.hi:
                    errs.append(0.0)
                    continue
                c = _fit_poly(g, a, min(b, self.core.hi), self.degree, self.basis)
                errs.append(_sample_err(g, [_quantize(x, 40) for x in c], a, min(b, self.core.hi), [40] * (self.degree + 1), 1.0, 24))
            # Allocate exactly K segments, with at least one per region.
            k = self.degree + 1
            ws = [max(e, 1e-30) ** (1.0 / k) for e in errs]
            tot = sum(ws)
            quotas = [(K - coarse) * weight / tot for weight in ws]
            counts = [1 + int(quota) for quota in quotas]
            for region in sorted(range(coarse), key=lambda r: (quotas[r] - int(quotas[r]), -r), reverse=True)[:K - sum(counts)]:
                counts[region] += 1
            starts, ends = [], []
            for r in range(coarse):
                sub = counts[r]
                a, b = base.starts[r], base.ends[r]
                if sub > b - a:
                    raise ValueError(f"hierarchical segmentation needs {sub} cells in region {r}; target precision is too small")
                for i in range(sub):
                    starts.append(a + (i * (b - a) + sub - 1) // sub)
                    ends.append(a + ((i + 1) * (b - a) + sub - 1) // sub)
            return Segments(Fu, L, starts, ends, _shifts_of(Fu, starts, ends))
        # nonuniform and ralut: a boundary search on a grid
        grid_bits = min(Fu, max(2, (K - 1).bit_length() + 2))
        if self.addressing == "power_of_two_cascade" and self.segmenter == "nonuniform":
            return _po2_segments(Fu, L, K)
        return _curvature_split(g, Fu, L, K, self.core.lo, self.core.hi, self.degree, self.basis, grid_bits,
                                self.boundary_search)

    # -- the index and the local variable
    def _index(self, u: Ref, seg: Segments) -> tuple:
        """(k: segment index Ref, t: local variable Ref with Ft fraction bits over [0, 1))."""
        n = self.net
        Fu = self.Fu
        K = seg.K
        kw = max(1, (K - 1).bit_length())
        if K == 1:
            return n.const(0, 1), u, Fu
        uniform = all(seg.shifts[i] == seg.shifts[0] for i in range(K)) and all(
            seg.starts[i] == i * (seg.ends[0] - seg.starts[0]) for i in range(K)) and (K & (K - 1)) == 0 or K == 1
        if self.segmenter in ("uniform_high_bit_decode", "hierarchical") and uniform:
            j = seg.shifts[0]
            ub = u.w
            if K == 1:
                k = n.const(0, 1)
                return k, u, Fu
            # the top kw bits index, the rest is the local variable (none left: a full table)
            kw = min(kw, ub)
            k = n.bits(u, ub - 1, ub - kw)
            Ft = ub - kw
            if Ft <= 0:
                return k, n.const(0, 1), 1
            t = n.bits(u, Ft - 1, 0)
            return k, t, Ft
        if self.segmenter == "power_of_two" or (self.segmenter == "nonuniform" and self.addressing == "power_of_two_cascade"):
            # the leading-one position selects the segment; the bits below it are the local variable
            ub = u.w
            lz = n.lzc(u)
            # segment k for a leading one at position ub-1-lz: k = K-1-lz for lz < K-1, else 0 (the residue near zero)
            lzw = lz.w
            kk = n.sub(n.const(K - 1, lzw + 1), n.ext(lz, lzw + 1))
            small = n.ge(lz, n.const(K - 1, lzw))
            k = n.trunc(n.mux(small, n.const(0, lzw + 1), n.uns(kk)), kw) if kw <= lzw + 1 else n.ext(n.mux(small, n.const(0, lzw + 1), n.uns(kk)), kw)
            # local variable: drop the leading one, shift the rest to the top (u << (lz+1)); the residue keeps u << (K-1)
            sh = n.mux(small, n.const(K - 1, lzw), n.add(lz, n.const(1, lzw), lzw))
            t = n.shlv(u, sh, ub)
            return k, t, ub
        if self.segmenter == "hierarchical":
            coarse = 4 if K >= 8 else 2
            cb = coarse.bit_length() - 1
            ub = u.w
            region = n.bits(u, ub - 1, ub - cb)
            # Per-region scale and base index retain arbitrary segment counts.
            base_idx, counts = [], []
            i = 0
            rw = ub - cb
            for r in range(coarse):
                cnt = sum(1 for s in seg.starts if (s >> rw) == r)
                base_idx.append(i)
                counts.append(cnt)
                i += cnt
            cw = max(1, max(counts).bit_length())
            scale = n.rom(counts, region, cw)
            bi = n.rom(base_idx, region, kw)
            rest = n.bits(u, rw - 1, 0)
            sub = n.shr(n.mul(rest, scale), rw)
            sub = n.bits(sub, kw - 1, 0) if sub.w > kw else n.ext(sub, kw)
            k = n.add(bi, sub, kw)
            st = n.rom(seg.starts, k, ub)
            sh = n.rom(seg.shifts, k, max(1, max(seg.shifts).bit_length()))
            diff = n.sub(u, st, ub)
            t = n.shlv(diff, sh, ub)
            return k, n.bits(t, Fu - 1, 0) if ub > Fu else t, Fu
        # nonuniform / ralut: boundaries as constants
        ub = u.w
        starts = seg.starts
        shifts = seg.shifts
        if self.segmenter == "uniform_high_bit_decode":
            # For non-power-of-two counts, a constant scale retains every
            # requested segment instead of silently rounding the count down.
            scale = n.mulc(u, K, max(1, K.bit_length()))
            index = n.shr(scale, ub)
            k = n.bits(index, kw - 1, 0) if index.w > kw else n.ext(index, kw)
        elif self.segmenter == "ralut" or self.addressing in ("priority_encoder", "comparator_tree"):
            if self.addressing == "comparator_tree" and self.segmenter != "ralut":
                # a binary search: each level compares against the boundary its prefix selects
                levels = kw
                bits = []
                for lvl in range(levels):
                    # candidate boundary index = prefix bits followed by 1 then zeros
                    prefix_w = lvl
                    cand = []
                    for pfx in range(1 << prefix_w):
                        idx = (pfx << (levels - prefix_w)) | (1 << (levels - prefix_w - 1))
                        cand.append(starts[idx] if idx < K else (1 << ub))       # beyond the last: never reached
                    if prefix_w:
                        pref = n.cat(*bits) if len(bits) > 1 else bits[0]
                        bnd = n.rom(cand, pref, ub + 1)
                    else:
                        bnd = n.const(cand[0], ub + 1)
                    bits.append(n.ge(n.ext(u, ub + 1), bnd))
                k = n.cat(*bits) if len(bits) > 1 else bits[0]
            else:
                # one comparator per boundary, the index is the count of boundaries at or below u
                flags = [n.ge(u, n.const(starts[i], ub)) for i in range(1, K)]
                acc = n.const(0, kw)
                for f in flags:
                    acc = n.add(acc, n.ext(f, kw), kw)
                k = acc
        else:   # direct_address_bits: a small table from the top grid bits to the segment
            gb = min(ub, max(1, (K - 1).bit_length() + 2))
            top = n.bits(u, ub - 1, ub - gb)
            table = []
            for c in range(1 << gb):
                pos = c << (ub - gb)
                kk = max(i for i in range(K) if starts[i] <= pos)
                table.append(kk)
            k0 = n.rom(table, top, kw)
            # A boundary can lie inside a decoded cell. Compare against that
            # cell's boundaries so its low argument bits remain significant.
            candidates = [[i for i in range(1, K)
                           if (c << (ub - gb)) < starts[i] < ((c + 1) << (ub - gb))]
                          for c in range(1 << gb)]
            k = k0
            for j in range(max(map(len, candidates), default=0)):
                bnds = [starts[row[j]] if j < len(row) else 1 << ub for row in candidates]
                boundary = n.rom(bnds, top, ub + 1)
                crossed = n.ge(n.ext(u, ub + 1), boundary)
                k = n.add(k, n.ext(crossed, kw), kw)
        st = n.rom(starts, k, ub)
        sh = n.rom(shifts, k, max(1, max(shifts).bit_length()))
        diff = n.uns(n.trunc(n.sub(n.ext(u, ub + 1), n.ext(st, ub + 1), ub + 1), ub))
        t = n.shlv(diff, sh, ub)
        if ub > Fu:
            t = n.bits(t, Fu - 1, 0)                                   # the scaled local variable is below one
        return k, t, Fu

    # -- the coefficient tables
    def _coefficients(self, seg: Segments, Ft: int) -> tuple:
        """Per segment the quantized coefficients: (list of [c_i ints], [Fc_i], [Wc_i], [d_k]) with the
        encoding applied (power_of_two rounds every coefficient to a power of two, csd/plain keep the
        value, shared fixes the top coefficient across the segments, per_coeff_width narrows each
        coefficient by the joint search)."""
        g = self.core.f
        K = seg.K
        d = self.degree
        Fc = self.coeff_frac or self.Fint
        degs = [d] * K
        fits = []
        with mpmath.workprec(_fit_precision.get()):
            for k in range(K):
                a, b = seg.bounds(k)
                sh = seg.shifts[k]
                if a >= self.core.hi:
                    fits.append(None)
                    continue
                b = min(b, self.core.hi)
                # the polynomial in the local variable t' = (u - a) 2^sh, t' in [0, (b-a) 2^sh]
                scale = 1 << sh
                gl = (lambda t, a=a, scale=scale: g(_mp(a) + t / scale))
                dk = d
                if self.mixed_max_degree is not None:
                    # the lowest degree meeting the target, up to the maximum
                    target = 2.0 ** -(self.Fint - 1)
                    for dd in range(0, self.mixed_max_degree + 1):
                        c = _fit_poly(gl, 0.0, (b - a) * scale, dd, self.basis)
                        e = _sample_err(gl, [_quantize(x, Fc) for x in c], 0.0, (b - a) * scale, [Fc] * (dd + 1), 1.0, 32)
                        dk = dd
                        if e <= target:
                            break
                    degs[k] = dk
                c = _fit_poly(gl, 0.0, (b - a) * scale, dk, self.basis)
                fits.append((c, gl, (b - a) * scale))
        # fill the unused segments with their neighbour's fit
        last = None
        for k in range(K):
            if fits[k] is None:
                fits[k] = last if last is not None else ([0.0] * (d + 1), None, 0.0)
            else:
                last = fits[k]
        dmax = max(degs)
        self.raw = [list(c) + [0.0] * (dmax + 1 - len(c)) for c, _gl, _w in fits]
        # fraction bits per coefficient
        fq = [Fc] * (dmax + 1)
        if self.joint_search or self.encoding == "per_coeff_width":
            # narrow each coefficient from the top degree down while the sampled error stays within the target
            target = 2.0 ** -(self.Fint - 1)
            for i in range(dmax, -1, -1):
                for fb in range(2, Fc + 1):
                    trial = list(fq)
                    trial[i] = fb
                    ok = True
                    for k in range(K):
                        c, gl, w = fits[k]
                        if gl is None:
                            continue
                        cq = [_quantize(x, trial[j]) for j, x in enumerate(c)]
                        if _sample_err(gl, cq, 0.0, w, trial, 1.0, 16) > target:
                            ok = False
                            break
                    if ok:
                        fq[i] = fb
                        break
        tables = []
        for k in range(K):
            c, gl, w = fits[k]
            c = list(c) + [0.0] * (dmax + 1 - len(c))
            if self.encoding in ("power_of_two", "po2_pair"):
                q = []
                for i, x in enumerate(c):
                    s, e = _po2(x)
                    first = Fraction(0) if e is None else (-1 if s else 1) * Fraction(2) ** e
                    value = first
                    if self.encoding == "po2_pair":
                        sign2, exponent2 = _po2(x - first)
                        if exponent2 is not None:
                            value += (-1 if sign2 else 1) * Fraction(2) ** exponent2
                    q.append(_quantize(value, fq[i]))
                if gl is not None and dmax >= 1 and w > 0:
                    # the top coefficients rounded: the constant term refitted to the residual's midpoint
                    with mpmath.workprec(_fit_precision.get()):
                        res = []
                        for j in range(33):
                            tt = _mp(w) * j / 32
                            res.append(gl(tt) - sum((_mp(q[i]) / (1 << fq[i])) * tt ** i for i in range(1, dmax + 1)))
                        q[0] = _quantize(_fraction_of_mp((max(res) + min(res)) / 2), fq[0])
                tables.append(q)
            else:
                tables.append([_quantize(x, fq[i]) for i, x in enumerate(c)])
        if self.encoding == "shared" and K > 1 and dmax >= 1:
            # one top coefficient for every segment (the mean), the lower ones refitted per segment
            top = round(Fraction(sum(t[dmax] for t in tables), K))
            for k in range(K):
                c, gl, w = fits[k]
                if gl is None:
                    tables[k][dmax] = top
                    continue
                with mpmath.workprec(_fit_precision.get()):
                    ct = _mp(top) / (1 << fq[dmax])
                    gr = (lambda t, gl=gl, ct=ct: gl(t) - ct * t ** dmax)
                    c2 = _fit_poly(gr, 0.0, w, dmax - 1, self.basis)
                tables[k] = [_quantize(x, fq[i]) for i, x in enumerate(c2)] + [top]
        widths = []
        for i in range(dmax + 1):
            mx = max(abs(t[i]) for t in tables) if tables else 0
            widths.append(max(2, mx.bit_length() + 1))
        return tables, fq, widths, degs

    # -- the evaluation datapath
    def _coeff_mul(self, c: Ref, t: Ref, k: Ref, seg_k: int | None, i: int, fq_i: int, tables: list,
                   fraction_bits: int | None = None) -> Ref:
        """c_i * t^i for the monomial forms under the coefficient encoding: a multiplier (plain,
        per_coeff_width, shared), a shift (power_of_two), a shift-add over the CSD digits (csd)."""
        n = self.net
        precision = t.w if fraction_bits is None else fraction_bits
        if self.encoding == "power_of_two" or self.evaluator == "shift_add_coeff":
            # the table holds (zero, sign, exponent): t^i >> e
            K = len(tables)
            zs, ss, es = [], [], []
            for tk in tables:
                v = tk[i]
                if v == 0:
                    zs.append(1); ss.append(0); es.append(0)
                else:
                    zs.append(0); ss.append(1 if v < 0 else 0)
                    es.append(fq_i - (abs(v).bit_length() - 1))
            left = max(0, -min(es))
            es = [e + left for e in es]
            ew = max(1, max(es).bit_length())
            z = n.rom(zs, k, 1); s = n.rom(ss, k, 1); e = n.rom(es, k, ew)
            tt = n.shl(t, left)
            sh = n.shrv(tt, e)                      # t * 2^-e' with t's fraction bits kept: result fraction = Ft
            val = n.mux(z, n.const(0, tt.w), sh)
            out = n.mux(s, n.neg(val), n.sgn(val))
            return out, precision
        if self.encoding in ("csd", "po2_pair"):
            # the nonzero CSD digits of the coefficient: (valid, sign, position) each, summed as shifted copies of t^i
            digs = [_csd(tk[i], fq_i, 64) for tk in tables]
            nd = max([len(x) for x in digs] + [1])
            tw = t.w
            acc = None
            coefficient_bits = max(abs(row[i]).bit_length() for row in tables)
            wsum = tw + coefficient_bits + 3 + nd.bit_length()
            for j in range(nd):
                vs, ss, ps = [], [], []
                for dg in digs:
                    if j < len(dg):
                        vs.append(1); ss.append(dg[j][0]); ps.append(dg[j][1])
                    else:
                        vs.append(0); ss.append(0); ps.append(0)
                pw = max(1, max(ps).bit_length())
                v = n.rom(vs, k, 1); s = n.rom(ss, k, 1); p = n.rom(ps, k, pw)
                term = n.shlv(n.ext(t, wsum), p, wsum)               # t * 2^p (fraction bits Ft + fq_i in the sum's frame)
                term = n.mux(v, term, n.const(0, wsum))
                term = n.mux(s, n.neg(n.sgn(term)), n.sgn(term))
                acc = term if acc is None else n.add(acc, term, wsum + 2)
            return acc, precision + fq_i
        return n.mul(c, n.sgn(t)), precision + fq_i

    @_polynomial_precision
    def build(self, u: Ref) -> Ref:
        n = self.net
        Fu = self.Fu
        self.source_width, self.source_fraction_bits = u.w, Fu
        self.smooth_root = self.K == 1 and self.core.name in ("sqrtc", "rsqrtc") and self.core.L == 2
        self.input_shift = 0
        self.residual_table = None
        if self.K == 1:
            self.core, u, self.Fu = _smooth_root_argument(n, self.core, u, Fu)
            Fu = self.Fu
        if self.x_frac is not None and self.x_frac < u.w:
            # the local variable is truncated to x_frac bits (pwl's x_frac_bits)
            self.input_shift = u.w - self.x_frac
            u = n.bits(u, u.w - 1, self.input_shift)
            self.Fu = Fu = u.w if self.core.L <= 1 else u.w - 1
        seg = self._segments()
        k, t, Ft = self._index(u, seg)
        tables, fq, widths, degs = self._coefficients(seg, Ft)
        dmax = max(degs)
        Fint = self.Fint
        K = seg.K
        if self.mult_shape == "truncated" and Ft > 6:
            t = n.bits(t, Ft - 1, 4)
            Ft -= 4
            self.notes.append("truncated multiplier: the local variable drops its 4 low bits")
        self.local_fraction_bits = Ft
        self.evaluation_input_width = u.w
        # coefficient ROMs
        cs = [self._encoded_coefficient([tk[i] for tk in tables], k, widths[i], fq[i])
              if self.encoding in ("csd", "po2_pair")
              else n.rom([tk[i] for tk in tables], k, widths[i], True)
              for i in range(dmax + 1)]
        self.table_bits = sum(K * w for w in widths)
        ev = self.evaluator
        if ev == "coefficient_adapted":
            r = self._adapted_general(t, Ft, k, tables, fq, dmax)
        elif ev in ("parallel_monomial", "shift_add_coeff") or self.encoding in ("power_of_two", "csd", "po2_pair") and dmax <= 1 and ev == "horner":
            r = self._monomial(cs, fq, t, Ft, tables, k, dmax)
        elif ev == "estrin":
            r = self._estrin(cs, fq, t, Ft, dmax)
        elif ev == "factored":
            r = self._factored(cs, fq, t, Ft, dmax)
        else:
            r = self._horner(cs, fq, t, Ft, dmax, exact=(ev == "fma_based"))
        # r: signed, Fint fraction bits -> R unsigned with Fo fraction bits, clamped at 0
        rr = n.shr(r, Fint - self.Fo) if r.w > Fint - self.Fo else r
        ib = self.core.ibits()
        R = _clamp_result(n, rr, self.Fo + ib)
        keep = R.w
        if self.residual_bits:
            # pwl_residual_lut: a residual correction table over residual_bits more bits of u
            rb = self.residual_bits
            kw = max(1, (K - 1).bit_length())
            idx = n.bits(u, u.w - 1, max(0, u.w - kw - rb))
            table = []
            with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                for c in range(1 << idx.w):
                    uu = (c << (u.w - idx.w)) + (1 << max(0, u.w - idx.w - 1))
                    env = n.run({}) if False else None
                    # the residual g(u) - p(u) at the cell centre, from the model of the polynomial part
                    val = float(self.core.f(_mp(uu) / (1 << Fu))) if uu / (1 << Fu) < self.core.hi else 0.0
                    table.append(val)
            # the polynomial's value at the centres, by evaluating the table path in Python
            res = []
            for c, val in enumerate(table):
                uu = (c << (u.w - idx.w)) + (1 << max(0, u.w - idx.w - 1))
                pv = self._model_poly(seg, tables, fq, degs, uu, Fu, Ft)
                res.append(int(round((val - pv) * (1 << self.Fo))))
            mx = max(abs(x) for x in res) if res else 0
            rw = max(2, mx.bit_length() + 1)
            corr = n.rom(res, idx, rw, True)
            R2 = n.add(n.sgn(R), n.ext(corr, R.w + 1))
            R = _clamp_result(n, R2, keep)
            self.residual_table = {"values": res, "index_bits": idx.w}
        self.seg, self.tables, self.fq, self.degs = seg, tables, fq, degs
        return R

    def _model_poly(self, seg, tables, fq, degs, uu: int, Fu: int, Ft: int) -> float:
        """The polynomial part's value at u = uu / 2^Fu (real arithmetic on the quantized coefficients)."""
        k = max(i for i in range(seg.K) if seg.starts[i] <= uu)
        tl = (uu - seg.starts[k]) << seg.shifts[k]
        t = tl / (1 << Fu)
        return sum((c / (1 << fq[i])) * t ** i for i, c in enumerate(tables[k]))

    def _encoded_coefficient(self, values, index, width, fraction_bits):
        """Read signed-digit coefficient fields and reconstruct the exact integer."""
        n = self.net
        digits = [_csd(value, fraction_bits, max(64, width + 2)) for value in values]
        count = max(1, max(map(len, digits)))
        result = n.const(0, width + 2, True)
        for di in range(count):
            valid = [int(di < len(row)) for row in digits]
            signs = [row[di][0] if di < len(row) else 0 for row in digits]
            positions = [row[di][1] if di < len(row) else 0 for row in digits]
            used = n.rom(valid, index, 1)
            sign = n.rom(signs, index, 1)
            position = n.rom(positions, index, max(1, max(positions).bit_length()))
            magnitude = n.shlv(n.const(1, width + 2), position, width + 2)
            term = n.mux(sign, n.neg(magnitude), n.sgn(magnitude))
            term = n.mux(used, term, n.const(0, term.w, True))
            result = n.add(result, term, width + 2)
        self.notes.append(f"{self.encoding}: {count} signed-digit fields per coefficient")
        return n.trunc(result, width)

    def _align(self, c: Ref, fc: int, F: int) -> Ref:
        """A coefficient (fc fraction bits) brought to F fraction bits."""
        return self.net.shl(c, F - fc) if F > fc else (self.net.shr(c, fc - F) if fc > F else c)

    def _horner(self, cs, fq, t, Ft, d, exact=False):
        n = self.net
        F = self.Fint
        acc = self._align(cs[d], fq[d], F)
        facc = F
        for i in range(d - 1, -1, -1):
            prod = n.mul(acc, n.sgn(t))                                  # facc + Ft fraction bits
            if exact:
                # chained fused multiply-adds: no truncation between the stages, one at the end
                facc += Ft
                acc = n.add(self._align(cs[i], fq[i], facc), prod)
            else:
                acc = n.add(self._align(cs[i], fq[i], F), n.shr(prod, Ft))
        if facc > F:
            acc = n.shr(acc, facc - F)
        return acc

    def _estrin(self, cs, fq, t, Ft, d):
        n = self.net
        F = self.Fint
        a = [self._align(cs[i], fq[i], F) for i in range(d + 1)]
        t2 = n.shr(n.mul(n.sgn(t), n.sgn(t)), Ft)                       # Ft fraction bits
        # pairs (c_{2j} + c_{2j+1} t), then combined by powers of t^2
        pairs = []
        for j in range(0, d + 1, 2):
            if j + 1 <= d:
                pairs.append(n.add(a[j], n.shr(n.mul(a[j + 1], n.sgn(t)), Ft)))
            else:
                pairs.append(a[j])
        # Horner in t^2 over the pairs
        acc = pairs[-1]
        for p in reversed(pairs[:-1]):
            acc = n.add(p, n.shr(n.mul(acc, n.sgn(t2)), Ft))
        return acc

    def _monomial(self, cs, fq, t, Ft, tables, k, d):
        n = self.net
        F = self.Fint
        powers = [None, t]
        for i in range(2, d + 1):
            powers.append(n.shr(n.mul(powers[i - 1], t), Ft))
        acc = self._align(cs[0], fq[0], F)
        for i in range(1, d + 1):
            term, fbits = self._coeff_mul(cs[i], powers[i], k, None, i, fq[i], tables, Ft)
            acc = n.add(acc, self._align(term, fbits, F))
        return acc

    def _factored(self, cs, fq, t, Ft, d):
        """Detrey-de Dinechin: the inner factors use the truncated local variable t_h (one rectangular multiplier)."""
        n = self.net
        F = self.Fint
        if d == 0:
            return self._align(cs[0], fq[0], F)
        th_bits = max(2, (Ft + 1) // 2 + 2)
        th = n.bits(t, Ft - 1, Ft - th_bits) if th_bits < Ft else t
        Fth = th.w
        acc = self._align(cs[d], fq[d], F)
        for i in range(d - 1, 0, -1):
            acc = n.add(self._align(cs[i], fq[i], F), n.shr(n.mul(acc, n.sgn(th)), Fth))
        return n.add(self._align(cs[0], fq[0], F), n.shr(n.mul(acc, n.sgn(t)), Ft))

    def _adapted_ok(self, tables, fq, d) -> bool:
        """Whether every segment's adapted constants (from the unquantized fit) stay finite and below 2^40:
        a leading coefficient below the precision blows them up, and then Horner stands."""
        for c in self.raw:
            lead = c[d]
            if abs(lead) < 2.0 ** -(self.Fint + 6):
                self.notes.append("coefficient_adapted: a segment's leading coefficient is below the precision; Horner stands")
                return False
            p = [x / lead for x in c]
            if any(abs(x) > 2.0 ** 40 or x != x for x in p):
                self.notes.append("coefficient_adapted: the adapted constants exceed 2^40; Horner stands")
                return False
        return True

    def _adapted_general(self, t, Ft, index, tables, fq, degree):
        """Shifted even/odd coefficient adaptation for every declared degree.

        P(t) becomes E((t+c)^2) + (t+c) O((t+c)^2). The coefficient
        of degree d-1 is eliminated exactly before quantization. Extra
        working bits follow the shift magnitude so a small leading
        coefficient does not trigger a different evaluator.
        """
        n = self.net
        raw = [[Fraction(value, 1 << fq[i]) for i, value in enumerate(row)] for row in tables]
        shifts, transformed = [], []
        for row in raw:
            d = degree
            while d > 0 and row[d] == 0:
                d -= 1
            shift = row[d - 1] / (d * row[d]) if d else Fraction(0)
            shifts.append(shift)
            transformed.append([sum((row[j] * math.comb(j, i) * (-shift) ** (j - i)
                                     for j in range(i, degree + 1)), Fraction(0))
                                for i in range(degree + 1)])
        magnitude_bits = max((max(0, abs(value.numerator).bit_length() - value.denominator.bit_length() + 1)
                              for value in shifts), default=0)
        fraction = self.Fint + (degree + 1) * magnitude_bits + 12
        def coefficient(values):
            integers = [_quantize(value, fraction) for value in values]
            width = max(2, max(abs(value) for value in integers).bit_length() + 1)
            if self.encoding in ("csd", "po2_pair"):
                return self._encoded_coefficient(integers, index, width, fraction)
            return n.rom(integers, index, width, True)
        centre = coefficient(shifts)
        variable = n.add(self._align(n.sgn(t), Ft, fraction), centre)
        square = n.shr(n.mul(variable, variable), fraction)
        coefficients = [coefficient([row[i] for row in transformed]) for i in range(degree + 1)]
        def evaluate(indices):
            while len(indices) > 1 and all(row[indices[-1]] == 0 for row in transformed):
                indices.pop()
            if not indices:
                return n.const(0, 2, True)
            result = coefficients[indices[-1]]
            for i in reversed(indices[:-1]):
                result = n.add(coefficients[i], n.shr(n.mul(result, square), fraction))
            return result
        even = evaluate(list(range(0, degree + 1, 2)))
        odd = evaluate(list(range(1, degree + 1, 2)))
        result = n.add(even, n.shr(n.mul(variable, odd), fraction))
        self.notes.append(f"coefficient_adapted: shifted even/odd evaluation at {fraction} fraction bits, degree {degree}")
        return n.shr(result, fraction - self.Fint)

    def _adapted(self, cs, fq, t, Ft, tables, k, d, widths):
        """Knuth's adapted forms: degree 3 as c3 ((t + a)(t^2 + b) + c), degree 4 as
        c4 ((z + t + c) z + d) with z = (t + a) t + b; the constants from the monic polynomial."""
        n = self.net
        F = self.Fint
        K = len(tables)
        consts = []
        for c in self.raw:
            lead = c[d]
            p = [x / lead for x in c]
            if d == 3:
                a, b = p[2], p[1]
                cc = p[0] - a * b
                consts.append((a, b, cc, 0.0, lead))
            else:
                a = (p[3] - 1) / 2
                b = p[1] - a * (p[2] - a * a - a)
                cc = p[2] - a * a - 2 * b - a
                dd = p[0] - b * b - b * cc
                consts.append((a, b, cc, dd, lead))
        big = max([abs(c) for cst in consts for c in cst[:4]] + [1.0])
        Fa = max(F + 4 + int(math.ceil(math.log2(big))) + 2, Ft + 2)   # the constants' magnitude costs fraction bits
        roms = []
        for i in range(5):
            vals = [_quantize(cst[i], Fa) for cst in consts]
            w = max(2, max(abs(v) for v in vals).bit_length() + 1)
            roms.append(n.rom(vals, k, w, True))
        ts = n.sgn(t)
        tf = n.shl(ts, Fa - Ft)                                       # t at Fa fraction bits
        if d == 3:
            f1 = n.add(tf, roms[0])                                    # t + a
            t2 = n.shr(n.mul(ts, ts), Ft)                             # t^2 at Ft
            f2 = n.add(n.shl(t2, Fa - Ft), roms[1])                    # t^2 + b
            q = n.add(n.shr(n.mul(f1, f2), Fa), roms[2])               # (t+a)(t^2+b) + c
        else:
            z = n.add(n.shr(n.mul(n.add(tf, roms[0]), ts), Ft), roms[1])       # (t + a) t + b
            w = n.add(n.add(z, tf), roms[2])                                     # z + t + c
            q = n.add(n.shr(n.mul(w, z), Fa), roms[3])                           # (z + t + c) z + d
        r = n.shr(n.mul(q, roms[4]), Fa)                                          # times the leading coefficient
        return n.shr(r, Fa - F)


# ---- format facts -----------------------------------------------------------------------
def _fmt_core(fmt):
    return fmt.core if isinstance(fmt, X87Format) else fmt


def fmt_facts(fmt) -> dict:
    """SW (significand bits), the exponent range of the leading one [emin, emax]
    (subnormals included), the smallest positive value's exponent, and
    whether the format is a posit."""
    c = _fmt_core(fmt)
    if isinstance(c, PositFormat):
        emax = (c.width - 2) << c.es
        return {"SW": c.width, "emin": -emax, "emax": emax, "posit": True, "M": c.width - 1}
    M = c.man_bits
    return {"SW": M + 1, "emin": 1 - c.bias - M, "emax": c._top() - c.bias, "posit": False, "M": M}


def saturation_T(fn: str, facts: dict) -> int:
    """The power of two T beyond which an x-domain core saturates for the
    format: tanh/erf/gelu(+) within 2^-(SW+2) of their limit, gelu(-)
    below half the smallest positive value."""
    SW = facts["SW"]
    thr = 2.0 ** -(SW + 2)
    with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
        if fn == "tanh":
            x = float(mpmath.atanh(1 - thr))
        elif fn == "erf":
            x = float(mpmath.erfinv(1 - thr))
        elif fn == "gelu":
            # the positive side saturates when erfc(x/sqrt2) < thr; the negative side underflows below 2^emin / 2
            xp = float(mpmath.sqrt(2) * mpmath.erfinv(1 - thr))
            lo = 2.0 ** (facts["emin"] - 2)
            xn = 1.0
            while float(xn / 2 * mpmath.erfc(xn / mpmath.sqrt(2))) > lo:
                xn *= 1.05
            x = max(xp, xn)
        else:
            raise ValueError(fn)
    k = 0
    while (1 << k) <= x:
        k += 1
    return 1 << k


# ---- the lane: X in, reduction, cores, reconstruction, X out ---------------------------------
class Lane:
    """The datapath of one function on one format for one engine: X in
    (the seed's unpacked operand), X out (before the pack), plus the
    invalid and divide-by-zero flags of the singular points."""

    def __init__(self, net: Net, g: Geom, fmt, fn: str, engine, guard: int = 3, pins: dict | None = None):
        self.n, self.g, self.fmt, self.fn, self.engine = net, g, fmt, fn, engine
        self.G = guard
        self.pins = pins or {}
        self.facts = fmt_facts(fmt)
        self.SW = self.facts["SW"]
        self.XW, self.EW, self.XT = g.XW, g.EW, g.XT
        self.BIG = 1 << (g.EW - 2)
        self.notes: list = []
        self.exact_cases = 0
        self.thr_e = max(8, (self.SW + 1) // 2 + 3)      # the series threshold of the direct odd functions

    # -- X fields
    def unpack(self, name: str = "x"):
        n, XT, XW, EW = self.n, self.XT, self.XW, self.EW
        x = n.port_in(name, XT)
        self.x = x
        self.sp = n.bits(x, XT - 1, XT - 2)
        self.s = n.bit(x, XT - 3)
        e_raw = n.bits(x, XW + EW, XW + 1)
        self.e = n.wire(EW, True, f"$signed({e_raw.name})", lambda env, a=e_raw, w=EW: _wrap(env[a.name], w, True), "e")
        self.sig = n.bits(x, XW, 1)
        self.st_in = n.bit(x, 0)
        self.zero = n.eqc(self.sig, 0)
        lz = n.lzc(self.sig)
        self.sign = n.shlv(self.sig, lz, XW)                       # the leading one at XW-1
        en = n.sub(self.e, n.ext(lz, EW))                          # exponent of bit 0 of sign
        self.E = n.add(en, n.const(XW - 1, EW + 1, True))          # exponent of the leading one
        self.f = n.bits(self.sign, XW - 2, 0)                      # the fraction below the leading one

    def small_series(self, c, k: int) -> tuple:
        """(sig, e) of c x (1 - x^2 / k) from the operand's normalized significand and
        exponent: the first two terms of an odd function's series, for |x| below 2^-thr_e
        (the next term is below the X lsb there)."""
        n, XW, EW = self.n, self.XW, self.EW
        sig = self.sign                                           # x = sig 2^(E - XW + 1), the leading one at XW-1
        sq = n.bits(n.shr(n.mul(sig, sig), XW - 2), XW + 1, 0)   # m^2 at XW fraction bits, m = sig / 2^(XW-1)
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            kq = int(mpmath.floor(mpmath.mpf(1) / k * (1 << XW) + mpmath.mpf("0.5")))
        r = n.shr(n.mul(sq, n.const(kq, kq.bit_length())), XW)  # m^2 / k at XW fraction bits
        neg2e = n.neg(n.shl(self.E, 1))                          # -2E >= 2 thr_e
        big = n.gt(neg2e, n.const(XW + 2, neg2e.w, True))
        amt = n.uns(n.trunc(n.mux(big, n.const(XW + 2, neg2e.w, True), neg2e), max(1, (XW + 2).bit_length() + 1)))
        rr = n.shrv(r, amt)                                       # x^2 / k at XW fraction bits
        corr = n.shr(n.mul(sig, rr), XW)                         # sig x^2 / k
        sig2 = n.uns(n.trunc(n.sub(n.sgn(sig), n.sgn(corr)), XW + 1))
        if c == 1:
            sigo, st, adj = self.fit(sig2)
            return sigo, self.eadj(self.E, -(XW - 1), adj)
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            cq = int(mpmath.floor(mpmath.mpf(c) * (1 << (XW + 2)) + mpmath.mpf("0.5")))
        P = n.mul(sig2, n.const(cq, cq.bit_length()))
        sigo, st, adj = self.fit(P)
        return sigo, self.eadj(self.E, -(XW - 1) - (XW + 2), adj)

    def small_arg(self) -> Ref:
        """|x| below 2^-thr_e (and not zero)."""
        n = self.n
        return n.land(n.le(self.E, n.const(-self.thr_e, self.E.w, True)), n.lnot(self.zero))

    # -- fixed-point conversion of a normalized significand
    def to_fixed(self, sig: Ref, E: Ref, I: int, F: int) -> tuple:
        """floor(sig 2^(E - (w-1)) 2^F) for a significand with its leading one
        at bit w-1: (mag with I+F bits, lost: bits shifted out nonzero,
        ovf: the value is 2^I or more)."""
        n = self.n
        w = sig.w
        Wf = max(w, I + F)
        ew = E.w + 2
        shl = n.add(n.ext(E, ew), n.const(F - (w - 1), ew, True), ew)
        left = n.ge(shl, n.const(0, ew, True))
        ovf = n.ge(E, n.const(I, E.w, True))
        aw = max(1, (Wf).bit_length())
        big_l = n.ge(shl, n.const(Wf, ew, True))
        la = n.mux(big_l, n.const(Wf, aw), n.trunc(n.uns(shl), aw) if aw <= ew else n.ext(n.uns(shl), aw))
        la = n.mux(left, la, n.const(0, aw))
        ml = n.shlv(n.ext(sig, Wf) if Wf > w else sig, la, Wf)
        ra_s = n.neg(shl)
        big_r = n.ge(ra_s, n.const(w, ra_s.w, True))
        raw_ = max(1, w.bit_length())
        ra = n.mux(big_r, n.const(w, raw_), n.trunc(n.uns(ra_s), raw_) if raw_ <= ra_s.w else n.ext(n.uns(ra_s), raw_))
        ra = n.mux(left, n.const(0, raw_), ra)
        mr = n.shrv(sig, ra)
        back = n.sub(n.const(w, raw_ + 1), n.ext(ra, raw_ + 1), raw_ + 1)
        lost = n.nz(n.shlv(sig, n.uns(n.trunc(back, raw_ + 1)), w))
        lost = n.land(n.lnot(left), lost)
        mag = n.mux(left, n.bits(ml, I + F - 1, 0) if ml.w > I + F else n.ext(ml, I + F),
                    n.bits(mr, I + F - 1, 0) if mr.w > I + F else n.ext(mr, I + F))
        return mag, lost, ovf

    def fitw(self, R: Ref, w: int) -> Ref:
        """An unsigned engine result brought to w bits: extended, or saturated at 2^w - 1."""
        n = self.n
        R = n.uns(R)
        if R.w <= w:
            return n.ext(R, w)
        over = n.nz(n.bits(R, R.w - 1, w))
        return n.mux(over, n.const((1 << w) - 1, w), n.bits(R, w - 1, 0))

    def fixed_signed(self, mag: Ref, lost: Ref, s: Ref) -> Ref:
        """The floor of the signed value: -(mag + lost) when negative."""
        n = self.n
        neg = n.sub(n.neg(mag), n.ext(lost, 2))
        return n.mux(s, neg, n.sgn(mag))

    # -- assembling the output
    def fit(self, P: Ref) -> tuple:
        """(sig of XW bits, extra sticky, exponent adjustment as a signed
        wire) of a product: normalized (its leading one at the top), the
        top XW bits kept, the rest folded into the sticky."""
        n, XW, EW = self.n, self.XW, self.EW
        P = n.uns(P)
        lz = n.lzc(P)
        Pn = n.shlv(P, lz, P.w)
        aw = EW + 4
        if P.w <= XW:
            adj = n.neg(n.ext(lz, aw - 1))
            return n.ext(Pn, XW), n.const(0, 1), n.trunc(adj, aw)
        adj = n.sub(n.const(P.w - XW, aw, True), n.ext(lz, aw), aw)
        return n.bits(Pn, P.w - 1, P.w - XW), n.nz(n.bits(Pn, P.w - XW - 1, 0)), adj

    def eadj(self, e: Ref, k: int, adj: Ref) -> Ref:
        """e + k + adj as a signed wire of EW + 4 bits."""
        n, aw = self.n, self.EW + 4
        e = n.sgn(e) if not e.s else e
        e = n.ext(e, aw) if e.w < aw else n.trunc(e, aw)
        return n.add(n.add(e, n.const(k, aw, True), aw), n.ext(adj, aw) if adj.w < aw else adj, aw)

    def x_out(self, sp: Ref, s: Ref, e: Ref, sig: Ref, st: Ref) -> Ref:
        n, EW, XW = self.n, self.EW, self.XW
        e = n.sgn(e) if not e.s else e
        ew = max(e.w, EW + 2)
        e = n.ext(e, ew)
        hi, lo = n.const(self.BIG, ew, True), n.const(-self.BIG, ew, True)
        e = n.mux(n.gt(e, hi), hi, n.mux(n.lt(e, lo), lo, e))
        e = n.uns(n.trunc(e, EW))
        sig = n.uns(sig)
        sig = n.ext(sig, XW) if sig.w < XW else (n.bits(sig, XW - 1, 0) if sig.w > XW else sig)
        return n.cat(sp, s, e, sig, st)

    def scale_x(self, sig: Ref, e: Ref, C: Fraction, Fk: int) -> tuple:
        """(sig, e, st) of a significand times a positive constant C (Fk fraction bits)."""
        n = self.n
        cq = int(round(C * (1 << Fk)))
        P = n.mul(sig, n.const(cq, cq.bit_length()))
        sig2, st2, adj = self.fit(P)
        return sig2, self.eadj(e, -Fk, adj), st2

    def const_e(self, v: int, w: int | None = None) -> Ref:
        return self.n.const(v, w or (self.EW + 4), True)

    # -- the exp-type reduction: y = x C (C = 1 for exp2), n = floor(y), f = frac(y)
    def exp_reduce(self, C: Fraction | None, I: int, F: int, negate: bool = False, sig: Ref | None = None,
                   E: Ref | None = None, s: Ref | None = None) -> tuple:
        """(n: signed I+1 bits, f: F bits, hi: y >= 2^(I-1), lo: y < -2^(I-1), lost)."""
        n = self.n
        sig = sig if sig is not None else self.sign
        E = E if E is not None else self.E
        s = s if s is not None else self.s
        if negate:
            s = n.lnot(s)
        if C is not None:
            Fk = F + I + 4
            cq = int(round(C * (1 << Fk)))
            P = n.mul(sig, n.const(cq, cq.bit_length()))
            w2 = P.w
            top = n.bit(P, w2 - 1)
            sig2 = n.mux(top, P, n.shlv(P, n.const(1, 1), w2))
            # the leading one at w2-1: value = sig2 2^(E - (w-1) - Fk + (w2-1) - (w2-1)) with a one-bit adjust
            E2 = n.add(n.ext(E, E.w + 2), n.const(-Fk + (w2 - sig.w) - (0), E.w + 2, True), E.w + 2)
            E2 = n.mux(top, E2, n.sub(E2, n.const(1, E.w + 2, True), E.w + 2))
            # keep the top sig.w + 2 bits of the product for the shifter
            keep = sig.w + 2
            sig3 = n.bits(sig2, w2 - 1, w2 - keep)
            lost0 = n.nz(n.bits(sig2, w2 - keep - 1, 0))
            mag, lost, ovf = self.to_fixed(sig3, E2, I, F)
            lost = n.lor(lost, lost0)
        else:
            mag, lost, ovf = self.to_fixed(sig, E, I, F)
        mag = n.mux(self.zero, n.const(0, mag.w), mag)
        lost = n.land(lost, n.lnot(self.zero))
        ovf = n.land(ovf, n.lnot(self.zero))
        y = self.fixed_signed(mag, lost, s)                      # I+F+1 bits signed
        nn = n.shr(y, F)                                          # floor(y)
        f = n.bits(y, F - 1, 0)
        hi = n.land(ovf, n.lnot(s))
        lo = n.land(ovf, s)
        return nn, f, hi, lo, lost

    def eng_has(self, core_name: str) -> bool:
        cov = getattr(self.engine, "covers", None)
        return True if cov is None else core_name in cov

    def eng_direct(self, core_name: str) -> bool:
        return core_name in getattr(self.engine, "direct", ())

    # -- programs -------------------------------------------------------------------------
    def build(self) -> None:
        n = self.n
        self.unpack()
        fn = self.fn
        prog = {"exp2": self.p_exp, "exp": self.p_exp, "log2": self.p_log, "log": self.p_log, "recip": self.p_recip,
                "sqrt": self.p_sqrt, "rsqrt": self.p_rsqrt, "sin": self.p_sincos, "cos": self.p_sincos,
                "tanh": self.p_tanh, "erf": self.p_tanh, "sigmoid": self.p_sigmoid, "silu": self.p_sigmoid,
                "softplus": self.p_softplus, "gelu": self.p_gelu}[fn]
        direct_cov = getattr(self.engine, "covers", None) or set()
        if fn in ("sigmoid", "silu") and "sigd" in direct_cov:
            prog = self.p_sigmoid_direct
        elif fn == "gelu" and "gelud" in direct_cov:
            prog = self.p_gelu_direct
        elif fn == "softplus" and "spd" in direct_cov:
            prog = self.p_softplus_direct
        sp, s, e, sig, st, inv, dz = prog()
        st = n.land(st, n.nz(sig))                                 # a zero result is exact
        y = self.x_out(sp if sp is not None else n.const(0, 2), s, e, sig, st)
        n.port_out("y", y)
        n.port_out("inv", inv if inv is not None else n.const(0, 1))
        n.port_out("dz", dz if dz is not None else n.const(0, 1))

    def _special(self, kind: int, s):
        """An X of a special: 1 NaN, 2 infinity; kind 3 = a tiny positive value below every subnormal, 4 = just below 1."""
        n = self.n
        if kind in (1, 2):
            return n.const(kind, 2), (s if kind == 2 else n.const(0, 1)), n.const(0, 4, True), n.const(0, self.XW), n.const(0, 1)
        if kind == 3:
            return n.const(0, 2), s, n.const(-self.BIG, self.EW + 2, True), n.const(1, self.XW), n.const(1, 1)
        return n.const(0, 2), s, n.const(-self.XW, self.EW + 2, True), n.const((1 << self.XW) - 1, self.XW), n.const(1, 1)

    def _select(self, conds: list, default: tuple) -> tuple:
        """A priority selection over (cond, (sp, s, e, sig, st)) tuples."""
        n = self.n
        out = list(default)
        for cond, vals in reversed(conds):
            out = [n.mux(cond, a, b) for a, b in zip(vals, out)]
        return tuple(out)

    def p_exp(self):
        n, XW, SW, G = self.n, self.XW, self.SW, self.G
        I = max(3, (self.facts["emax"] + 2 * SW + 8).bit_length() + 1)
        F = SW + G + 2
        Fo = SW + G
        C = None if self.fn == "exp2" else self._log2e()
        nn, f, hi, lo, lost = self.exp_reduce(C, I, F)
        core = core_of("exp2c")
        R = self.engine(n, core, f, F, Fo, "exp2c")
        self.dbg = {"n": nn, "f": f, "hi": hi, "lo": lo, "lost": lost, "R": R}
        exact = n.land(n.eqc(f, 0), n.lnot(lost)) if self.fn == "exp2" else self.zero
        one = n.const(1 << Fo, Fo + 1)
        R = n.mux(exact, one, self.fitw(R, Fo + 1))
        st = n.lnot(exact)
        e = n.sub(n.ext(nn, self.EW + 2), n.const(Fo, self.EW + 2, True), self.EW + 2)
        zero_s = n.const(0, 1)
        sp0 = n.const(0, 2)
        big = n.const(self.BIG, self.EW + 2, True)
        out = self._select([(hi, (sp0, zero_s, big, n.const(1 << (XW - 1), XW), n.const(1, 1))),
                            (lo, self._special(3, zero_s))],
                           (sp0, zero_s, e, n.ext(R, XW), st))
        return (None,) + out[1:] + (None, None)

    def p_log(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        F = SW + G + 2
        Fo = SW + G
        # centering: m in [1.5, 2) -> m/2, E+1; d = m' - 1 in [-1/4, 1/2) exactly as a signed fixed value of F bits
        half = n.bit(self.f, XW - 2)
        fF = n.bits(self.f, XW - 2, XW - 1 - F) if XW - 1 > F else n.shl(self.f, F - (XW - 1))
        d_pos = n.sgn(fF)                                              # m - 1 when m < 1.5
        d_neg = n.sub(n.sgn(n.shr(fF, 1)), n.const(1 << (F - 1), F + 1, True))   # m/2 - 1 when m >= 1.5
        d = n.mux(half, d_neg, d_pos)                                  # F fraction bits, signed
        Ep = n.add(n.ext(self.E, EW + 3), n.ext(half, EW + 3), EW + 3)
        u = n.uns(n.trunc(n.add(d, n.const(1 << (F - 2), F + 1, True)), F))     # d + 1/4 in [0, 3/4)
        core = core_of("log2c")
        if self.eng_direct("log2c"):
            Fo = 2 * SW + G + 1                                        # log2(1 + d) itself, down to d = the mantissa lsb
        gR = self.engine(n, core, u, F, Fo, "log2c")                  # log2(1+d)/d, Fo fraction bits (or log2(1+d) directly)
        dneg = n.lt(d, n.const(0, d.w, True))
        dabs = n.uns(n.trunc(n.mux(dneg, n.neg(d), d), F))
        dz0 = n.eqc(dabs, 0)
        Fo2 = SW + G + 2
        if self.eng_direct("log2c"):
            # the engine's value is log2(1 + d) itself (signed, Fo fraction bits): no relative-precision product
            gS = gR if gR.s else n.sgn(gR)
            lneg = n.lt(gS, n.const(0, gS.w, True))
            gabs = n.uns(n.mux(lneg, n.neg(gS), gS))
            sig0, st0, adj0 = self.fit(gabs)
            e0 = self.eadj(n.const(0, 2, True), -Fo, adj0)
            dneg = lneg
            Ps = n.shl(gS, Fo2 - Fo) if Fo2 > Fo else n.shr(gS, Fo - Fo2)
            self.notes.append("log: the engine returns log2(1 + d) directly; a result near zero has the engine's absolute precision")
        else:
            lzd = n.lzc(dabs)
            dn = n.shlv(dabs, lzd, F)
            P = n.mul(dn, gR)                                              # |d| g scaled by 2^(F + Fo + lzd)
            # E' == 0: the product itself, exponent -(F + Fo + lzd)
            sig0, st0, adj0 = self.fit(P)
            e0 = self.eadj(n.neg(n.ext(lzd, EW + 3)), -F - Fo, adj0)
            # E' != 0: L = E' + d g in a frame of Fo2 fraction bits
            Pq = n.shrv(n.ext(P, P.w + 1), n.ext(lzd, lzd.w + 1) if lzd.w < P.w.bit_length() else lzd)
            Pq = n.shr(Pq, F + Fo - Fo2)                                   # d g at Fo2 fraction bits (unsigned magnitude)
            Pq = n.bits(Pq, min(Pq.w, Fo2 + 2) - 1, 0)
            Ps = n.mux(dneg, n.neg(Pq), n.sgn(Pq))
        Lw = max(Ep.w + Fo2, Ps.w + 2)
        L = n.add(n.ext(n.shl(Ep, Fo2), Lw), n.ext(Ps, Lw))
        Lneg = n.lt(L, n.const(0, L.w, True))
        Labs = n.uns(n.mux(Lneg, n.neg(L), L))
        sig1, st1, adj1 = self.fit(Labs)
        e1 = self.eadj(n.const(0, 2, True), -Fo2, adj1)
        Ez = n.eqc(Ep, 0)
        sig = n.mux(Ez, sig0, sig1)
        e = n.mux(Ez, e0, e1)
        s = n.mux(Ez, dneg, Lneg)
        st = n.lnot(dz0)                                               # log2 of a power of two is exact
        if self.fn == "log":
            with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                ln2 = Fraction(str(mpmath.nstr(mpmath.log(2), 40)))
            sig, e, st2 = self.scale_x(sig, e, ln2, XW + 2)
            st = n.lor(st, st2, n.lnot(dz0))
            st = n.lor(st, n.nz(sig))
        inv = n.land(self.s, n.lnot(self.zero))
        sp0 = n.const(0, 2)
        out = self._select([(inv, self._special(1, n.const(0, 1))),
                            (self.zero, self._special(2, n.const(1, 1)))],
                           (sp0, s, e, sig, st))
        return out + (inv, self.zero)

    def p_recip(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        F = SW + G + 2
        Fo = SW + G + 1
        u = n.bits(self.f, XW - 2, XW - 1 - F) if XW - 1 > F else n.shl(self.f, F - (XW - 1))
        R = self.engine(n, core_of("recipc"), u, F, Fo, "recipc")
        exact = n.eqc(u, 0)
        R = n.mux(exact, n.const(1 << Fo, Fo + 1), self.fitw(R, Fo + 1))
        e = n.sub(n.neg(n.ext(self.E, EW + 3)), n.const(Fo, EW + 4, True), EW + 4)
        st = n.lnot(exact)
        out = self._select([(self.zero, self._special(2, self.s))], (n.const(0, 2), self.s, e, n.ext(R, XW), st))
        return out + (None, self.zero)

    def _sqrt_w(self, F):
        n, XW = self.n, self.XW
        par = n.bit(n.uns(self.E), 0)
        fF = n.bits(self.f, XW - 2, XW - 1 - F) if XW - 1 > F else n.shl(self.f, F - (XW - 1))
        return par, n.cat(par, fF), fF

    def p_sqrt(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        F = SW + G + 2
        Fo = SW + G
        par, w, fF = self._sqrt_w(F)
        R = self.engine(n, core_of("sqrtc"), w, F, Fo, "sqrtc")
        exact = n.land(n.eqc(fF, 0), n.lnot(par))
        R = n.mux(exact, n.const(1 << Fo, Fo + 1), self.fitw(R, Fo + 1))
        half = n.shr(self.E, 1)
        e = n.sub(n.ext(half, EW + 3), n.const(Fo, EW + 3, True), EW + 3)
        st = n.lnot(exact)
        inv = n.land(self.s, n.lnot(self.zero))
        out = self._select([(inv, self._special(1, n.const(0, 1))),
                            (self.zero, (n.const(0, 2), self.s, n.const(0, 4, True), n.const(0, XW), n.const(0, 1)))],
                           (n.const(0, 2), n.const(0, 1), e, n.ext(R, XW), st))
        return out + (inv, None)

    def p_rsqrt(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        F = SW + G + 2
        Fo = SW + G + 1
        par, w, fF = self._sqrt_w(F)
        R = self.engine(n, core_of("rsqrtc"), w, F, Fo, "rsqrtc")
        exact = n.land(n.eqc(fF, 0), n.lnot(par))
        R = n.mux(exact, n.const(1 << Fo, Fo + 1), self.fitw(R, Fo + 1))
        q = n.shr(self.E, 1)
        e = n.sub(n.neg(n.ext(q, EW + 3)), n.const(Fo, EW + 4, True), EW + 4)
        st = n.lnot(exact)
        inv = n.land(self.s, n.lnot(self.zero))
        # the infinity at zero carries the operand's sign: IEEE 754-2019 section 9.2.1 gives
        # rSqrt(+0) = +inf and rSqrt(-0) = -inf, since sqrt(-0) is -0 and 1/(-0) is -inf. A
        # negative operand that is not zero is invalid and gives NaN, which `inv` selects first.
        out = self._select([(inv, self._special(1, n.const(0, 1))),
                            (self.zero, self._special(2, self.s))],
                           (n.const(0, 2), n.const(0, 1), e, n.ext(R, XW), st))
        return out + (inv, self.zero)

    # -- x-domain cores: tanh, erf (odd, x t(x)); the fixed argument u = |x| / T
    def _u_of_T(self, T: int, Fu: int) -> tuple:
        """u = |x| / T as Fu fraction bits, and the saturation flag |x| >= T."""
        n = self.n
        k = T.bit_length() - 1
        mag, lost, ovf = self.to_fixed(self.sign, self.E, k, Fu - k)
        mag = n.mux(self.zero, n.const(0, mag.w), mag)
        ovf = n.land(ovf, n.lnot(self.zero))
        return mag, ovf

    def p_tanh(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        T = self._clip(self.fn, saturation_T(self.fn, self.facts))
        k = T.bit_length() - 1
        Fu = SW + G + 2 + k
        Fo = SW + G + k + 1
        u, sat = self._u_of_T(T, Fu)
        dname = "tanhd" if self.fn == "tanh" else "erfd"
        rname = "tanhc" if self.fn == "tanh" else "erfe"
        core = core_of(dname, T) if self.eng_has(dname) and not self.eng_has(rname) else core_of(rname, T)
        if core.name == dname or self.eng_direct(core.name):
            Fo = SW + G + k + 1 + min(24, max(0, -self.facts["emin"]))   # the value itself, down to the smallest x
        R = self.engine(n, core, u, Fu, Fo, core.name)
        if core.name == dname or self.eng_direct(core.name):
            # the function's value itself (absolute precision); below 2^-thr_e the series x (1 - x^2 / 3)
            # (times 2 / sqrt(pi) for erf) stands in
            sigd, st_x, adj = self.fit(R)
            ed = self.eadj(n.const(0, 2, True), -Fo, adj)
            with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                cser = 1 if self.fn == "tanh" else mpmath.mpf(2) / mpmath.sqrt(mpmath.pi)
            sigs, es = self.small_series(cser, 3)
            small = self.small_arg()
            sig, e = n.mux(small, sigs, sigd), n.mux(small, es, ed)
            self.notes.append(f"{self.fn}: the engine returns the value directly; below 2^-{self.thr_e} the series stands in")
        else:
            P = n.mul(self.sign, R)
            sig, st_x, adj = self.fit(P)
            e = self.eadj(self.E, -(XW - 1) - Fo, adj)
        out = self._select([(sat, self._special(4, self.s))], (n.const(0, 2), self.s, e, sig, n.const(1, 1)))
        return out + (None, None)

    # -- the direct activation programs: the function over the folded, bounded argument
    def _sat_T(self, fn: str) -> int:
        SW = self.SW
        thr = 2.0 ** -(SW + 2)
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            if fn in ("sigmoid", "silu"):
                x = float(mpmath.log((1 - thr) / thr))
            elif fn == "softplus":
                x = float(mpmath.log(1 / thr))
            else:
                x = float(saturation_T(fn, self.facts))
        k = 0
        while (1 << k) <= x:
            k += 1
        return 1 << k

    def _fold(self, fn: str, T: int, Fu: int, folded: bool) -> tuple:
        """(u, sat): u = |x|/T (folded) or (x + T)/(2T) (unfolded) as Fu bits."""
        n = self.n
        u, sat = self._u_of_T(T, Fu)
        if folded:
            return u, sat
        half = n.const(1 << (Fu - 1), Fu + 1)
        uh = n.shr(u, 1)
        u2 = n.mux(self.s, n.sub(half, n.ext(uh, Fu + 1)), n.add(half, n.ext(uh, Fu + 1), Fu + 1))
        return n.bits(n.uns(u2), Fu - 1, 0), sat

    def _clip(self, fn: str, T: int) -> int:
        prim = getattr(self.engine, "primary", None)
        return prim.clip_T(fn, T) if prim is not None and hasattr(prim, "clip_T") else T

    def p_sigmoid_direct(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        T = self._clip("sigmoid", self._sat_T("sigmoid"))
        k = T.bit_length() - 1
        Fu = SW + G + 2 + k
        Fo = SW + G + 1 + min(24, int(T * 1.4427) + 1)              # down to sigmoid(-T) = e^-T
        folded = bool(_pin(self.pins, "symmetry_folding", True)) if self.engine.primary.family == "sigmoid_tanh_pwl" else True
        u, sat = self._fold("sigmoid", T, Fu, folded)
        core = core_of("sigd" if folded else "sigd2", T)
        R = self.engine(n, core, u, Fu, Fo, core.name)
        R = self.fitw(R, Fo)                                           # below one: 1 - R stays positive
        if folded:
            S = n.mux(self.s, n.sub(n.const(1 << Fo, Fo + 2), n.ext(R, Fo + 2)), n.ext(R, Fo + 2))
        else:
            S = R
        if self.fn == "sigmoid":
            sig, st_x, adj = self.fit(n.uns(S))
            e = self.eadj(n.const(0, 2, True), -Fo, adj)
            out = self._select([(n.land(sat, self.s), self._special(3, n.const(0, 1))), (sat, self._special(4, n.const(0, 1)))],
                               (n.const(0, 2), n.const(0, 1), e, sig, n.const(1, 1)))
            return out + (None, None)
        P = n.mul(self.sign, n.uns(S))
        sig, st_x, adj = self.fit(P)
        e = self.eadj(self.E, -(XW - 1) - Fo, adj)
        xself = (n.const(0, 2), self.s, n.sub(n.ext(self.E, EW + 4), n.const(XW - 1, EW + 4, True), EW + 4), self.sign, n.const(1, 1))
        out = self._select([(n.land(sat, self.s), self._special(3, self.s)), (sat, xself)],
                           (n.const(0, 2), self.s, e, sig, n.const(1, 1)))
        return out + (None, None)

    def p_gelu_direct(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        T = self._clip("gelu", self._sat_T("gelu"))
        k = T.bit_length() - 1
        Fu = SW + G + 2 + k
        Fo = SW + G + 2 + min(40, int(T * T / 2 * 1.4427) + 1)      # down to erfc(T / sqrt2) ~ e^(-T^2 / 2)
        u, sat = self._u_of_T(T, Fu)
        core = core_of("gelud", T)
        R = self.engine(n, core, u, Fu, Fo, "gelud")                    # erf(|x| / sqrt2) in [0, 1)
        R = self.fitw(R, Fo)                                           # below one: 1 - R stays positive
        S = n.mux(self.s, n.sub(n.const(1 << Fo, Fo + 2), n.ext(R, Fo + 2)), n.add(n.const(1 << Fo, Fo + 2), n.ext(R, Fo + 2), Fo + 2))
        P = n.mul(self.sign, n.uns(S))
        sig, st_x, adj = self.fit(P)
        e = self.eadj(self.E, -(XW - 1) - Fo - 1, adj)
        xself = (n.const(0, 2), n.const(0, 1), n.sub(n.ext(self.E, EW + 4), n.const(XW - 1, EW + 4, True), EW + 4), self.sign, n.const(1, 1))
        out = self._select([(n.land(sat, self.s), self._special(3, n.const(1, 1))), (sat, xself)],
                           (n.const(0, 2), self.s, e, sig, n.const(1, 1)))
        return out + (None, None)

    def p_softplus_direct(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        T = self._clip("softplus", self._sat_T("softplus"))
        k = T.bit_length() - 1
        Fu = SW + G + 2 + k
        Fo = SW + G + 2 + min(24, int(T * 1.4427) + 1)              # down to softplus(-T) ~ e^-T
        u, sat = self._fold("softplus", T, Fu, False)
        core = core_of("spd", T)
        R = self.engine(n, core, u, Fu, Fo, "spd")
        sig, st_x, adj = self.fit(R)
        e = self.eadj(n.const(0, 2, True), -Fo, adj)
        xself = (n.const(0, 2), n.const(0, 1), n.sub(n.ext(self.E, EW + 4), n.const(XW - 1, EW + 4, True), EW + 4), self.sign, n.const(1, 1))
        out = self._select([(n.land(sat, self.s), self._special(3, n.const(0, 1))), (sat, xself)],
                           (n.const(0, 2), n.const(0, 1), e, sig, n.const(1, 1)))
        return out + (None, None)

    # -- sigmoid, silu: 1 / (1 + 2^(-x log2 e))
    def _log2e(self):
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            return Fraction(str(mpmath.nstr(1 / mpmath.log(2), 40)))

    def p_sigmoid(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        I = max(4, (SW + G + 8).bit_length() + 1)
        F = SW + G + 2
        Fo = SW + G
        NADD = SW + G + 2
        nn, f, hi, lo, lost = self.exp_reduce(self._log2e(), I, F, negate=True)       # y = -x log2 e
        c = self.engine(n, core_of("exp2c"), f, F, Fo, "exp2c")                       # 2^f in [1, 2)
        c = self.fitw(c, Fo + 1)
        cx = n.mux(n.land(n.eqc(f, 0), n.lnot(lost)), n.const(1 << Fo, Fo + 1), c)
        # D = 1 + c 2^n in a frame of Fd fraction bits and NADD + 1 integer bits (n <= NADD)
        Fd = Fo
        WD = NADD + 2 + Fd
        npos = n.ge(nn, n.const(0, nn.w, True))
        nbig = n.gt(nn, n.const(NADD, nn.w, True))
        sh_l = n.uns(n.trunc(n.mux(nbig, n.const(NADD, nn.w, True), nn), max(1, NADD.bit_length() + 1)))
        neg_n = n.neg(nn)
        sh_r = n.uns(n.trunc(n.mux(n.gt(neg_n, n.const(Fd + 1, neg_n.w, True)), n.const(Fd + 1, neg_n.w, True), neg_n),
                             max(1, (Fd + 1).bit_length() + 1)))
        term = n.mux(npos, n.shlv(n.ext(cx, WD), sh_l, WD), n.ext(n.shrv(cx, sh_r), WD))
        D = n.add(term, n.const(1 << Fd, WD), WD)
        lzD = n.lzc(D)
        Dn = n.shlv(D, lzD, WD)
        # exponent of the leading one: (WD - 1 - lzD) - Fd
        nd = n.sub(n.const(WD - 1 - Fd, lzD.w + 2, True), n.ext(n.sgn(lzD), lzD.w + 2), lzD.w + 2)
        u_small = n.bits(Dn, WD - 2, WD - 1 - F)
        # n > NADD: D ~ c 2^n
        u_big = n.bits(cx, Fo - 1, Fo - F) if Fo >= F else n.cat(n.bits(cx, Fo - 1, 0), n.const(0, F - Fo))
        u = n.mux(nbig, u_big, u_small)
        ndx = n.mux(nbig, n.ext(nn, nd.w) if nn.w < nd.w else n.trunc(nn, nd.w), nd)
        R = self.engine(n, core_of("recipc"), u, F, Fo + 1, "recipc")
        Fr = Fo + 1
        R = self.fitw(R, Fr + 1)
        exact = n.land(n.eqc(u, 0), n.lnot(lost), n.eqc(f, 0))
        R = n.mux(exact, n.const(1 << Fr, Fr + 1), R)
        if self.fn == "sigmoid":
            e = n.sub(n.neg(n.ext(ndx, EW + 4)), n.const(Fr, EW + 4, True), EW + 4)
            out = self._select([(hi, self._special(3, n.const(0, 1))), (lo, self._special(4, n.const(0, 1)))],
                               (n.const(0, 2), n.const(0, 1), e, n.ext(R, XW), n.lnot(exact)))
            return out + (None, None)
        # silu = x sigma(x)
        P = n.mul(self.sign, R)
        sig, st_x, adj = self.fit(P)
        e = n.sub(self.eadj(self.E, -(XW - 1) - Fr, adj), n.ext(ndx, EW + 4), EW + 4)
        # x >> 0: x itself (just below); x << 0: a tiny negative value
        xself = (n.const(0, 2), self.s, n.ext(self.E, EW + 4) if False else n.sub(n.ext(self.E, EW + 4), n.const(XW - 1, EW + 4, True), EW + 4), self.sign, n.const(1, 1))
        out = self._select([(hi, self._special(3, self.s)), (lo, xself)],
                           (n.const(0, 2), self.s, e, sig, n.const(1, 1)))
        return out + (None, None)

    def p_softplus(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        I = max(4, (SW + G + 8).bit_length() + 1)
        F = SW + G + 2
        Fo = SW + G
        NADD = SW + G + 2
        nn, f, hi, lo, lost = self.exp_reduce(self._log2e(), I, F)                     # y = x log2 e
        c = self.engine(n, core_of("exp2c"), f, F, Fo, "exp2c")
        c = self.fitw(c, Fo + 1)
        cx = n.mux(n.land(n.eqc(f, 0), n.lnot(lost)), n.const(1 << Fo, Fo + 1), c)
        core_l = core_of("log2c")
        Fol = Fo
        if self.eng_direct("log2c"):
            Fol = SW + G + 1 + min(24, max(0, -self.facts["emin"]))    # log2(1 + T) itself, down to the smallest T
        # the fixed form: D = 1 + c 2^n (n >= -1), normalized and centred
        Fd = Fo
        WD = NADD + 2 + Fd
        npos = n.ge(nn, n.const(0, nn.w, True))
        nbig = n.gt(nn, n.const(NADD, nn.w, True))
        sh_l = n.uns(n.trunc(n.mux(nbig, n.const(NADD, nn.w, True), nn), max(1, NADD.bit_length() + 1)))
        neg_n = n.neg(nn)
        sh_r = n.uns(n.trunc(n.mux(n.gt(neg_n, n.const(Fd + 1, neg_n.w, True)), n.const(Fd + 1, neg_n.w, True), neg_n),
                             max(1, (Fd + 1).bit_length() + 1)))
        term = n.mux(npos, n.shlv(n.ext(cx, WD), sh_l, WD), n.ext(n.shrv(cx, sh_r), WD))
        D = n.add(term, n.const(1 << Fd, WD), WD)
        lzD = n.lzc(D)
        Dn = n.shlv(D, lzD, WD)                                        # leading one at WD-1
        nd = n.sub(n.const(WD - 1 - Fd, lzD.w + 2, True), n.ext(n.sgn(lzD), lzD.w + 2), lzD.w + 2)
        frac = n.bits(Dn, WD - 2, WD - 1 - F)                          # F bits of dn - 1
        half = n.bit(frac, F - 1)
        d_pos = n.sgn(frac)
        d_neg = n.sub(n.sgn(n.shr(frac, 1)), n.const(1 << (F - 1), F + 1, True))
        d = n.mux(half, d_neg, d_pos)
        ndp = n.add(nd, n.ext(half, nd.w), nd.w)
        u_fix = n.uns(n.trunc(n.add(d, n.const(1 << (F - 2), F + 1, True)), F))
        Fl = F + (SW + G + 3) if self.eng_direct("log2c") else F     # the log core's argument frame
        if Fl > F:
            u_fix = n.cat(u_fix, n.const(0, Fl - F))
        # the float form (T < 1/2, n <= -2): d = T itself, u = T + 1/4
        small = n.lt(nn, n.const(-1, nn.w, True))
        # T = c 2^n at F fraction bits (c carries Fo fraction bits): the core's argument of the float form
        shr_T = n.uns(n.trunc(n.mux(n.gt(neg_n, n.const(Fl + 2, neg_n.w, True)), n.const(Fl + 2, neg_n.w, True), neg_n), max(1, (Fl + 2).bit_length() + 1)))
        T_fix = n.shrv(n.shl(cx, Fl + 2), shr_T)                      # T at Fo + Fl + 2 fraction bits
        T_F = n.bits(n.shr(T_fix, Fo + 2), Fl - 1, 0)                 # Fl fraction bits (T < 1/2)
        u_flt = n.uns(n.trunc(n.add(n.sgn(T_F), n.const(1 << (Fl - 2), Fl + 2, True)), Fl))
        u = n.mux(small, u_flt, u_fix)
        gR = self.engine(n, core_l, u, Fl, Fol, "log2c")
        Fo2 = SW + G + 2
        dneg = n.lt(d, n.const(0, d.w, True))
        dabs = n.uns(n.trunc(n.mux(dneg, n.neg(d), d), F))
        if self.eng_direct("log2c"):
            # the engine's value is log2(1 + d) itself (signed, Fol bits): the fixed form adds it to nd'; the
            # float form (T small) takes it as the result, and below the core's argument resolution
            # (T < 2^-(F/2)) the series log2 e (T - T^2 / 2) from the exponential core's c and n
            gS = gR if gR.s else n.sgn(gR)
            Ps = n.shl(gS, Fo2 - Fol) if Fo2 > Fol else n.shr(gS, Fol - Fo2)
            gpos = n.uns(n.mux(n.lt(gS, n.const(0, gS.w, True)), n.const(0, gS.w, True), gS))
            sigc, stc, adjc = self.fit(gpos)
            ec = self.eadj(n.const(0, 2, True), -Fol, adjc)
            tiny = n.lt(nn, n.const(-(Fl // 2), nn.w, True))
            sq = n.shr(n.mul(cx, cx), Fo)                                  # T^2 / 2^(2 nn) at Fo bits
            shq = n.uns(n.trunc(n.mux(n.gt(neg_n, n.const(Fo + 1, neg_n.w, True)), n.const(Fo + 1, neg_n.w, True), neg_n), max(1, (Fo + 1).bit_length() + 1)))
            corr = n.shrv(n.shr(sq, 1), shq)                               # T^2 / 2 in T's frame (2^nn, Fo bits)
            vser = n.uns(n.trunc(n.sub(n.sgn(cx), n.sgn(corr)), Fo + 1))   # T - T^2 / 2, positive
            Fk = Fo + 4
            lq = int(round(self._log2e() * (1 << Fk)))
            Pser = n.mul(vser, n.const(lq, lq.bit_length()))
            sigs, sts, adjs = self.fit(Pser)
            es = self.eadj(nn, -Fo - Fk, adjs)
            sig0 = n.mux(tiny, sigs, sigc)
            e0 = n.mux(tiny, es, ec)
            self.notes.append("softplus: the engine returns log2(1 + d) directly; below 2^-(F/2) the series stands in")
        else:
            # fixed form value: L = nd' + d g at Fo2 bits
            Pf = n.mul(dabs, gR)                                           # F + Fo fraction bits
            Pq = n.shr(Pf, F + Fo - Fo2)
            Ps = n.mux(dneg, n.neg(Pq), n.sgn(Pq))
            # float form value: T g(T): c g with exponent n - Fo - Fo
            Pt = n.mul(cx, gR)
            sig0, st0, adj0 = self.fit(Pt)
            e0 = self.eadj(nn, -2 * Fo, adj0)
        Lw = max(ndp.w + 2 + Fo2, Ps.w + 2)
        L = n.add(n.ext(n.shl(n.ext(ndp, ndp.w + 2), Fo2), Lw), n.ext(Ps, Lw))
        Labs = n.uns(n.mux(n.lt(L, n.const(0, L.w, True)), n.const(0, L.w, True), L))
        sig1, st1, adj1 = self.fit(Labs)
        e1 = self.eadj(n.const(0, 2, True), -Fo2, adj1)
        sig = n.mux(small, sig0, sig1)
        e = n.mux(small, e0, e1)
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            ln2 = Fraction(str(mpmath.nstr(mpmath.log(2), 40)))
        sig, e, st2 = self.scale_x(sig, e, ln2, XW + 2)
        xself = (n.const(0, 2), n.const(0, 1), n.sub(n.ext(self.E, EW + 4), n.const(XW - 1, EW + 4, True), EW + 4), self.sign, n.const(1, 1))
        # beyond n = NADD the sum 1 + c 2^n is c 2^n within the precision: softplus(x) = x
        out = self._select([(n.lor(hi, nbig), xself), (lo, self._special(3, n.const(0, 1)))],
                           (n.const(0, 2), n.const(0, 1), e, sig, n.const(1, 1)))
        return out + (None, None)

    def p_gelu(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        T = saturation_T("gelu", self.facts)
        k = T.bit_length() - 1
        Fu = SW + G + 2 + k
        Fo_e = SW + G + k + 1
        u, sat = self._u_of_T(T, Fu)
        # x >= 0: x/2 (1 + x E(x))
        Ecore = core_of("gelue", T)
        Ev = self.engine(n, Ecore, u, Fu, Fo_e, "gelue")
        P1 = n.mul(self.sign, Ev)                                      # x E(x) 2^(XW-1+Fo_e-E)
        top = n.bit(P1, P1.w - 1)
        P1n = n.mux(top, P1, n.shlv(P1, n.const(1, 1), P1.w))
        E1 = n.add(n.ext(self.E, EW + 4), n.const(P1.w - XW - Fo_e, EW + 4, True), EW + 4)
        E1 = n.mux(top, E1, n.sub(E1, n.const(1, EW + 4, True), EW + 4))
        keep = XW + 2
        P1k = n.bits(P1n, P1.w - 1, P1.w - keep)
        Fo2 = SW + G + 2
        xe, lost1, ovf1 = self.to_fixed(P1k, E1, 1, Fo2)              # x E(x) in [0, 1] at Fo2 bits
        xe = n.mux(self.zero, n.const(0, xe.w), xe)
        S = n.add(n.const(1 << Fo2, Fo2 + 2), n.ext(xe, Fo2 + 2), Fo2 + 2)
        Pp = n.mul(self.sign, S)
        sigp, stp, adjp = self.fit(Pp)
        ep = self.eadj(self.E, -(XW - 1) - Fo2 - 1, adjp)
        # x < 0: x/2 2^(-x^2 log2e/2) r(x)
        sq = n.mul(self.sign, self.sign)
        tops = n.bit(sq, 2 * XW - 1)
        sqn = n.mux(tops, sq, n.shlv(sq, n.const(1, 1), 2 * XW))
        E2 = n.add(n.shl(n.ext(self.E, EW + 4), 1), n.const(1, EW + 4, True), EW + 4)   # 2E + 1 when the top bit is set
        E2 = n.mux(tops, E2, n.sub(E2, n.const(1, EW + 4, True), EW + 4))
        sqk = n.bits(sqn, 2 * XW - 1, XW)
        I = max(4, (SW + G + 8).bit_length() + 1)
        F = SW + G + 2
        Fo = SW + G
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            C = Fraction(str(mpmath.nstr(1 / (2 * mpmath.log(2)), 40)))
        nn, f, hi, lo, lost = self.exp_reduce(C, I, F, negate=True, sig=sqk, E=E2, s=n.const(0, 1))
        c = self.engine(n, core_of("exp2c"), f, F, Fo, "exp2c")
        c = self.fitw(c, Fo + 1)
        rcore = core_of("gelur", T)
        Fo_r = SW + G + k + 1
        rv = self.engine(n, rcore, u, Fu, Fo_r, "gelur")
        Pa = n.mul(self.sign, c)
        siga, sta, adja = self.fit(Pa)
        Pb = n.mul(siga, rv)
        sigb, stb, adjb = self.fit(Pb)
        en = n.add(self.eadj(n.add(n.ext(self.E, EW + 4), n.ext(nn, EW + 4), EW + 4), -(XW - 1) - Fo - Fo_r - 1, adja),
                   n.ext(adjb, EW + 4), EW + 4)
        xself = (n.const(0, 2), n.const(0, 1), n.sub(n.ext(self.E, EW + 4), n.const(XW - 1, EW + 4, True), EW + 4), self.sign, n.const(1, 1))
        pos = self._select([(sat, xself)], (n.const(0, 2), n.const(0, 1), ep, sigp, n.const(1, 1)))
        negv = self._select([(n.lor(sat, lo), self._special(3, n.const(1, 1)))], (n.const(0, 2), n.const(1, 1), en, sigb, n.const(1, 1)))
        out = tuple(n.mux(self.s, a, b) for a, b in zip(negv, pos))
        return out + (None, None)

    # -- sin, cos
    def p_sincos(self):
        n, XW, SW, G, EW = self.n, self.XW, self.SW, self.G, self.EW
        facts = self.facts
        method = str(_pin(self.pins, "range_reducer.method", "cody_waite"))
        terms = int(_pin(self.pins, "range_reducer.split_constant_terms", 2))
        dual = str(_pin(self.pins, "range_reducer.path_structure", "single")) == "dual_close_far"
        cbits = self._cancellation_bits()
        Fu = SW + G + 3 + cbits
        Fo = SW + G + 1
        with mpmath.workprec(PROFILE_BITS + 200):
            two_over_pi = 2 / mpmath.pi
            half_pi = mpmath.pi / 2
            emin, emax = facts["emin"], facts["emax"]
            if method in ("payne_hanek",):
                Fr = Fu + SW + 4
                entries = []
                for E in range(emin, emax + 1):
                    v = mpmath.fmod(two_over_pi * mpmath.power(2, E - (SW - 1)), 4)
                    entries.append(int(mpmath.floor(v * (1 << Fr))))
                idx_w = max(1, (emax - emin).bit_length())
                Eoff = n.sub(n.ext(self.E, EW + 3), n.const(emin, EW + 3, True), EW + 3)
                Eoff = n.mux(n.lt(Eoff, n.const(0, EW + 3, True)), n.const(0, EW + 3, True), Eoff)
                idx = n.bits(n.uns(Eoff), idx_w - 1, 0)
                ent = n.rom(entries, idx, Fr + 2)
                sig_top = n.bits(self.sign, XW - 1, XW - SW)
                P = n.mul(sig_top, ent)                                # 2 + Fr fraction bits carry the quadrant and u
                q = n.bits(P, Fr + 1, Fr)
                u = n.bits(P, Fr - 1, Fr - Fu)
                self.notes.append(f"range reduction payne_hanek: {len(entries)} windows of 2/pi by exponent, {Fr + 2} bits each")
            else:
                # the fixed image of |x|: Kb integer bits (a cap), Fr fraction bits
                Kb = min(24, max(2, emax + 1))
                Fr = Fu + 6
                Ff = Fr + Kb + 2                                       # the frame of the products
                xm, lostx, ovfx = self.to_fixed(self.sign, self.E, Kb, Ff)
                xm = n.mux(self.zero, n.const(0, xm.w), xm)
                if method == "cody_waite":
                    # k = floor(x 2/pi) from the top bits, r = x - k (C1 + ... + C_T), each product exact
                    xt = n.bits(xm, Kb + Ff - 1, Ff - 6)               # Kb + 6 bits of x
                    cs = int(mpmath.floor(two_over_pi * (1 << (Kb + 8))))
                    kp = n.mul(xt, n.const(cs, cs.bit_length()))
                    k = n.bits(kp, kp.w - 1, Kb + 8 + 6)               # the integer part
                    k = n.bits(k, Kb - 1, 0) if k.w > Kb else n.ext(k, Kb)
                    B = -(-(Ff + 2) // terms)
                    rem = half_pi
                    r = n.sgn(xm)
                    for i in range(terms):
                        ci = int(mpmath.floor(rem * (1 << Ff)))
                        # the term keeps B significant bits below the previous ones
                        keep_from = Ff - B * (i + 1)
                        if keep_from > 0:
                            ci = (ci >> keep_from) << keep_from
                        rem = rem - mpmath.mpf(ci) / (1 << Ff)
                        if ci == 0:
                            continue
                        r = n.sub(r, n.sgn(n.mul(k, n.const(ci, ci.bit_length()))))
                    rq = n.shr(r, Ff - Fr)                             # r at Fr fraction bits (floor)
                    # u = r 2/pi at Fu bits, then the fix-up into [0, 1)
                    c2 = int(mpmath.floor(two_over_pi * (1 << (Fr + 4))))
                    up = n.mul(rq, n.const(c2, c2.bit_length()))
                    uq = n.shr(up, Fr + 4 + Fr - Fu)                   # signed, Fu fraction bits
                    uneg = n.lt(uq, n.const(0, uq.w, True))
                    uhi = n.ge(uq, n.const(1 << Fu, uq.w, True))
                    uf = n.mux(uneg, n.add(uq, n.const(1 << Fu, uq.w, True), uq.w),
                               n.mux(uhi, n.sub(uq, n.const(1 << Fu, uq.w, True), uq.w), uq))
                    u = n.bits(n.uns(uf), Fu - 1, 0)
                    kq = n.bits(k, 1, 0)
                    q = n.trunc(n.uns(n.mux(uneg, n.sub(n.sgn(kq), n.const(1, 3, True)), n.mux(uhi, n.add(n.sgn(kq), n.const(1, 3, True)), n.sgn(kq)))), 2)
                    self.notes.append(f"range reduction cody_waite: {terms} split constants of pi/2, exact below 2^{Kb}; beyond it the reduction wraps")
                else:
                    # modular / table-augmented: every integer bit (or group of 4) of x contributes 2^i 2/pi mod 4 from a table
                    grp = 4 if method == "table_augmented" else 1
                    frac_bits = n.bits(xm, Ff - 1, Ff - Fr)
                    c2 = int(mpmath.floor(two_over_pi * (1 << (Fr + 2))))
                    acc = n.shr(n.mul(frac_bits, n.const(c2, c2.bit_length())), Fr + 2)   # (frac x)(2/pi) at Fr bits
                    accw = Fr + 4 + Kb.bit_length()
                    acc = n.ext(acc, accw) if acc.w < accw else n.bits(acc, accw - 1, 0)
                    for i0 in range(0, Kb, grp):
                        gb = min(grp, Kb - i0)
                        sel = n.bits(xm, Ff + i0 + gb - 1, Ff + i0)
                        tab = []
                        for v in range(1 << gb):
                            val = mpmath.mpf(0)
                            for j in range(gb):
                                if (v >> j) & 1:
                                    val += mpmath.fmod(two_over_pi * mpmath.power(2, i0 + j), 4)
                            tab.append(int(mpmath.floor(mpmath.fmod(val, 4) * (1 << Fr))))
                        tv = n.rom(tab, sel, Fr + 2)
                        acc = n.add(acc, n.ext(tv, accw), accw)
                    q = n.bits(acc, Fr + 1, Fr)
                    u = n.bits(acc, Fr - 1, Fr - Fu)
                    self.notes.append(f"range reduction {method}: {(Kb + grp - 1) // grp} tables of 2^i (2/pi) mod 4 over the integer bits of x (cap 2^{Kb})")
        if self.fn == "cos":
            q = n.trunc(n.add(q, n.const(1, 2), 2), 2)
        odd = n.bit(q, 0)
        negq = n.bit(q, 1)
        one_m_u = n.uns(n.trunc(n.sub(n.const(1 << Fu, Fu + 2, True), n.sgn(u)), Fu + 1))   # 1 - u in (0, 1]
        vfull = n.mux(odd, one_m_u, n.ext(u, Fu + 1))
        v_is_one = n.bit(vfull, Fu)
        v = n.bits(vfull, Fu - 1, 0)
        core = core_of("sinc")
        if self.eng_direct("sinc"):
            Fo = SW + G + 1 + min(24, max(0, -self.facts["emin"]))     # sin(pi v/2) itself, down to the smallest x
        paired = getattr(self.engine, "paired_sincos", False)
        evaluated = self.engine(n, core, u if paired else v, Fu, Fo, "sincos" if paired else "sinc")
        h2 = n.mux(odd, evaluated[1], evaluated[0]) if paired else evaluated
        h2 = self.fitw(h2, Fo + 1)
        if self.eng_direct("sinc"):
            sigd, std, adjd = self.fit(h2)
            ed = self.eadj(n.const(0, 2, True), -Fo, adjd)
            # below 2^-thr_e in v: (pi/2) v (1 - (pi v / 2)^2 / 6), v normalized for its relative precision
            sqv = n.shr(n.mul(v, v), Fu)
            cq6 = int(mpmath.floor(mpmath.pi ** 2 / 24 * (1 << (Fo + 2)) + mpmath.mpf("0.5")))
            t6 = n.shr(n.mul(sqv, n.const(cq6, cq6.bit_length())), Fu + 2)
            h2s = n.uns(n.trunc(n.sub(n.const(1 << Fo, Fo + 2), n.ext(t6, Fo + 2)), Fo + 1))
            lzv = n.lzc(v)
            vn = n.shlv(v, lzv, Fu)
            Ps = n.mul(vn, h2s)
            cpi = int(mpmath.floor(half_pi * (1 << (Fo + 2))))
            Ps2 = n.mul(Ps, n.const(cpi, cpi.bit_length()))
            sigs, sts, adjs = self.fit(Ps2)
            es = self.eadj(n.neg(n.ext(lzv, EW + 3)), -Fu - Fo - (Fo + 2), adjs)
            small_v = n.land(n.lt(v, n.const(1 << max(0, Fu - self.thr_e), Fu)), n.nz(v))
            sigf, ef = n.mux(small_v, sigs, sigd), n.mux(small_v, es, ed)
            dual = False
            self.notes.append(f"sin/cos: the engine returns sin(pi v/2) directly; no close path, below 2^-{self.thr_e} the series stands in")
        else:
            # the fixed form: (pi/2) v h2(v), v normalized for its relative precision
            lzv = n.lzc(v)
            vn = n.shlv(v, lzv, Fu)
            P = n.mul(vn, h2)
            cpi = int(mpmath.floor(half_pi * (1 << (Fo + 2))))
            P2 = n.mul(P, n.const(cpi, cpi.bit_length()))
            sigf, stf, adjf = self.fit(P2)
            ef = self.eadj(n.neg(n.ext(lzv, EW + 3)), -Fu - Fo - (Fo + 2), adjf)
        sigf = n.mux(v_is_one, n.const(1 << (XW - 1), XW), sigf)
        ef = n.mux(v_is_one, n.const(-(XW - 1), EW + 4, True), ef)
        stf = n.lnot(v_is_one)
        # the close path (sin, q = 0): x h2(u)
        Pc = n.mul(self.sign, h2)
        sigc, stc, adjc = self.fit(Pc)
        ec = self.eadj(self.E, -(XW - 1) - Fo, adjc)
        close = n.land(n.eqc(q, 0), n.const(1 if (dual and self.fn == "sin") else 0, 1))
        sig = n.mux(close, sigc, sigf)
        e = n.mux(close, ec, ef)
        st = n.mux(close, n.const(1, 1), stf)
        s = n.bxor(negq, self.s) if self.fn == "sin" else negq
        # x = 0: sin 0 = 0 with x's sign, cos 0 = 1
        if self.fn == "sin":
            out = self._select([(self.zero, (n.const(0, 2), self.s, n.const(0, 4, True), n.const(0, XW), n.const(0, 1)))],
                               (n.const(0, 2), s, e, sig, st))
        else:
            out = self._select([(self.zero, (n.const(0, 2), n.const(0, 1), n.const(-(XW - 1), EW + 4, True), n.const(1 << (XW - 1), XW), n.const(0, 1)))],
                               (n.const(0, 2), s, e, sig, st))
        infinity = n.eqc(self.sp, 2)
        special = n.lor(n.eqc(self.sp, 1), infinity)
        out = self._select([(special, self._special(1, n.const(0, 1)))], out)
        return out + (infinity, None)

    def _cancellation_bits(self) -> int:
        """The leading zeros of the reduced argument's distance to the
        nearest quadrant boundary, over the format (exhaustive up to 16
        bits, a conservative SW + 6 above)."""
        fmt = self.fmt
        if fmt.width > 16:
            return self.SW + 6
        worst = 0.0
        with mpmath.workprec(PROFILE_BITS + 100):
            two_over_pi = 2 / mpmath.pi
            for b in range(1 << fmt.width):
                if not fmt.valid(b):
                    continue
                v = fmt.decode(b)
                if not isinstance(v, Fraction) or v <= 0:
                    continue
                if v < 0.78:
                    continue
                p = mpmath.mpf(v.numerator) / v.denominator * two_over_pi
                u = p - mpmath.floor(p)
                d = min(u, 1 - u)
                if d > 0:
                    worst = max(worst, float(-mpmath.log(d, 2)))
        return int(math.ceil(worst)) + 1


def _clamp_result(n: Net, r: Ref, keep: int) -> Ref:
    """A signed result clamped into [0, 2^keep - 1] as an unsigned value of keep bits."""
    r = n.sgn(r) if not r.s else r
    neg = n.lt(r, n.const(0, r.w, True))
    over = n.ge(r, n.const(1 << keep, max(r.w, keep + 2), True))
    R = n.uns(n.mux(neg, n.const(0, r.w, True), r))
    R = n.bits(R, keep - 1, 0) if R.w > keep else n.ext(R, keep)
    return n.mux(over, n.const((1 << keep) - 1, keep), R)


# ---- table methods: bipartite, STAM, multipartite, add-table-add ---------------------------------
TABLE_FAMILIES = ("bipartite", "stam", "multipartite", "add_table_add")


class TableEngine:
    """A core evaluated by table addition: the argument split into
    chunks, one table of values over the leading chunks and offset
    tables (or central differences of the value table) over the lower
    ones, summed without a coefficient multiplier."""

    def __init__(self, net: Net, core: Core, Fu: int, Fo: int, family: str, pins: dict, label: str = ""):
        self.net, self.core, self.Fu, self.Fo, self.family, self.pins, self.label = net, core, Fu, Fo, family, pins, label
        self.notes: list = []
        self.table_bits = 0

    def _g(self, uu: int, Fu: int) -> float:
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            u = mpmath.mpf(uu) / (1 << Fu)
            if u >= self.core.hi:
                u = mpmath.mpf(self.core.hi) - mpmath.mpf(1) / (1 << Fu)
            return self.core.f(u)

    def _dg(self, uu: int, Fu: int) -> float:
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            u = mpmath.mpf(uu) / (1 << Fu)
            if u >= self.core.hi:
                u = mpmath.mpf(self.core.hi) - mpmath.mpf(1) / (1 << Fu)
            return mpmath.diff(self.core.f, u)

    def build(self, u: Ref) -> Ref:
        n = self.net
        fam = self.family
        Fo = self.Fo
        ub = u.w                                   # Fu (+1 for a domain of length 2)
        ib = self.core.ibits()
        if fam in ("bipartite", "stam", "multipartite"):
            return self._partite(u)
        return self._ata(u)

    def _slot(self, name):
        family = self.pins.get(f"{name}.family")
        if family is None:
            return None
        sub = {key[len(name) + 1:]: value for key, value in self.pins.items()
               if key.startswith(name + ".") and key != f"{name}.family"}
        if hasattr(self.pins, "owner"):
            from chialu.targets.rtl.families.selection import SelectedPins
            sub = SelectedPins(f"{self.pins.owner}.{name}", sub)
        return str(family), sub

    def _address_add(self, a, b):
        n = self.net
        selected = self._slot("address_adder")
        if selected is None:
            return n.add(a, b)
        previous = n.bind.get("adder")
        n.bind["adder"] = selected
        try:
            result = n.add(a, b)
        finally:
            if previous is None:
                n.bind.pop("adder", None)
            else:
                n.bind["adder"] = previous
        from chialu.targets.rtl.families.fidelity import effective
        effective(self.pins, "address_adder.family", selected[0], "pre-lookup bank address adders",
                  {"width": result.w})
        return result

    def _reduce(self, terms, form):
        n = self.net
        family = str(_pin(self.pins, "final_adder.family", "linear_chain" if form == "adder_chain" else "binary_tree"))
        if (family == "linear_chain") != (form == "adder_chain"):
            raise ValueError(f"final_reduction={form} conflicts with final_adder.family={family}")
        width = max(t.w for t in terms) + (len(terms) - 1).bit_length() + 2
        rows = [n.ext(n.sgn(t), width) for t in terms]
        previous = n.bind.get("adder")
        selected = self._slot("final_adder.cpa" if family == "binary_tree" else "final_adder.final_cpa")
        if selected is not None:
            n.bind["adder"] = selected
        def csa3(a, b, c):
            a, b, c = n.uns(a), n.uns(b), n.uns(c)
            summ = n.bxor(n.bxor(a, b), c)
            carry = n.bor(n.bor(n.band(a, b), n.band(a, c)), n.band(b, c))
            return [n.as_signed(summ), n.as_signed(n.trunc(n.shl(carry, 1), width))]
        def csa7(group):
            columns = []
            for bit in range(width):
                bits = [n.ext(n.bit(n.uns(row), bit), 3) for row in group]
                acc = bits[0]
                for item in bits[1:]:
                    acc = n.add(acc, item, 3)
                columns.append(acc)
            result = []
            for carry in range(3):
                word = n.cat(*(n.bit(col, carry) for col in reversed(columns)))
                result.append(n.as_signed(n.trunc(n.shl(word, carry), width) if carry else word))
            return result
        try:
            if family == "csa_tree":
                compressor = str(_pin(self.pins, "final_adder.compressor", "3:2"))
                fanin = {"3:2": 3, "4:2": 4, "7:3": 7}.get(compressor)
                if fanin is None or len(rows) < fanin:
                    raise ValueError(f"compressor={compressor} needs at least {fanin} live terms; this ATA has {len(rows)}")
                while len(rows) >= fanin:
                    group, rows = rows[:fanin], rows[fanin:]
                    if fanin == 7:
                        reduced = csa7(group)
                    elif fanin == 4:
                        a, b = csa3(*group[:3])
                        reduced = csa3(a, b, group[3])
                    else:
                        reduced = csa3(*group)
                    rows = reduced + rows
                while len(rows) > 2:
                    rows = csa3(*rows[:3]) + rows[3:]
                result = n.add(rows[0], rows[1], width)
            elif family == "binary_tree":
                while len(rows) > 1:
                    rows = [n.add(rows[i], rows[i + 1], width) if i + 1 < len(rows) else rows[i]
                            for i in range(0, len(rows), 2)]
                result = rows[0]
            elif family == "linear_chain":
                result = rows[0]
                for row in rows[1:]:
                    result = n.add(result, row, width)
            else:
                raise ValueError(f"unknown ATA final_adder family {family!r}")
        finally:
            if previous is None:
                n.bind.pop("adder", None)
            else:
                n.bind["adder"] = previous
        from chialu.targets.rtl.families.fidelity import effective
        effective(self.pins, "final_adder.family", family, "reduction of all live finite-difference terms",
                  {"operands": len(terms), "width": width})
        return result

    # -- bipartite / STAM / multipartite
    def _partite(self, u: Ref) -> Ref:
        n, Fo, fam, P = self.net, self.Fo, self.family, self.pins
        ub = u.w
        ib = self.core.ibits()
        m = int(_pin(P, "tables", 2)) if fam != "bipartite" else 2
        m = max(2, min(m, 6)) + 1                  # chunks: the value table's two and one per offset table
        hier = bool(_pin(P, "hierarchical", False)) if fam == "multipartite" else False
        sym = bool(_pin(P, "symmetric", False)) if fam == "bipartite" else True
        guard = 2 if fam == "multipartite" and str(_pin(P, "accuracy_target", "faithful_1ulp")) == "sub_ulp_guard_bits" else 0
        Fo = Fo + guard                                  # the tables at the guarded precision, the result shifted back
        # the used bits: about Fo + 1 fraction bits; the chunks: the value table over the top n0+n1,
        # each offset table over (a prefix of) the top n0 bits and one lower chunk
        used = min(ub, Fo + 2)
        k = m                                       # chunks: u0, u1 (value table), u2..um (offsets)
        n0 = max(1, -(-(used) // 3) + (1 if m > 2 else 0))
        rest = used - n0
        n_low = max(1, rest // k)
        chunks = [n0] + [n_low] * (k - 1)
        chunks[1] += rest - n_low * (k - 1)         # the value chunk takes the remainder
        # bit positions (from the top of the used field)
        pos = []
        top = ub
        for c in chunks:
            pos.append((top - 1, top - c))
            top -= c
        fields = [n.bits(u, hi, lo) for hi, lo in pos]
        # value table T0[u0, u1] = g(u0 + u1 + the midpoints of the lower chunks)
        idx0 = n.cat(fields[0], fields[1])
        w01 = chunks[0] + chunks[1]
        lows_mid = sum(1 << (pos[j][1] + chunks[j] - 1) for j in range(2, k)) if k > 2 else 0
        # lows below the used field: their midpoint too
        below = (1 << (ub - used - 1)) if ub > used else 0
        Ft = Fo
        t0 = []
        for a in range(1 << w01):
            uu = (a << (ub - w01)) + lows_mid + below
            t0.append(int(round(self._g(uu, self.Fu) * (1 << Ft))))
        w0 = max(2, max(abs(v) for v in t0).bit_length() + 1)
        T0 = n.rom(t0, idx0, w0, True)
        self.table_bits += len(t0) * w0
        acc = T0
        # offset tables: Ti[prefix, ui] = g'(prefix + mid) (ui - mid_i)
        for j in range(2, k):
            pre_bits = chunks[0] if not hier else max(1, chunks[0] - (j - 2))
            pre = n.bits(u, ub - 1, ub - pre_bits)
            cj = chunks[j]
            hi_j, lo_j = pos[j]
            uj = fields[j]
            if sym:
                # store half the table: the offset is odd around the chunk's midpoint; the top bit of the
                # chunk selects the sign and the lower bits, complemented, the magnitude
                tb = n.bit(uj, cj - 1)
                low = n.bits(uj, cj - 2, 0) if cj > 1 else None
                mag = n.bxor(low, n.bnot(n.ext(tb, low.w)) if False else n.ext(tb, low.w)) if low is not None else None
                # magnitude index: tb ? low : ~low  (distance from the midpoint minus a half step)
                mag = n.mux(tb, low, n.bnot(low)) if low is not None else None
                idx = n.cat(pre, mag) if mag is not None else pre
                tab = []
                for a in range(1 << pre_bits):
                    for q in range(1 << (cj - 1)) if cj > 1 else [0]:
                        upre = (a << (ub - pre_bits)) + (1 << (ub - pre_bits - 1))
                        off = Fraction(2 * q + 1, 2) * (1 << lo_j) if cj > 1 else Fraction(1 << lo_j, 2)
                        tab.append(int(round(self._dg(upre, self.Fu) * _mp(off) / (1 << self.Fu) * (1 << Ft))))
                wj = max(2, max(abs(v) for v in tab).bit_length() + 1)
                Tj = n.rom(tab, idx, wj, True)
                self.table_bits += len(tab) * wj
                term = n.mux(tb, Tj, n.neg(Tj))
            else:
                idx = n.cat(pre, uj)
                tab = []
                mid = (1 << (cj - 1)) * (1 << lo_j)
                for a in range(1 << pre_bits):
                    for q in range(1 << cj):
                        upre = (a << (ub - pre_bits)) + (1 << (ub - pre_bits - 1))
                        off = q * (1 << lo_j) - mid
                        tab.append(int(round(self._dg(upre, self.Fu) * off / (1 << self.Fu) * (1 << Ft))))
                wj = max(2, max(abs(v) for v in tab).bit_length() + 1)
                Tj = n.rom(tab, idx, wj, True)
                self.table_bits += len(tab) * wj
                term = Tj
            acc = n.add(acc, term)
        self.notes.append(f"{fam}: chunks {chunks} bits, {self.table_bits} table bits" + (" (symmetric offsets)" if sym and k > 2 else "")
                          + (f", {guard} guard bits" if guard else ""))
        return _clamp_result(n, n.shr(acc, guard) if guard else acc, self.Fo + ib)

    # -- add-table-add: a value table read at the address and its neighbours, central differences times the low chunk
    def _ata(self, u: Ref) -> Ref:
        n, Fo, pins = self.net, self.Fo, self.pins
        ub, ib = u.w, self.core.ibits()
        order = int(_pin(pins, "truncation_order", 1))
        chunk = int(_pin(pins, "input_chunk_bits", 4))
        if not 1 <= order <= 4 or not 4 <= chunk <= 8:
            raise ValueError("ATA requires truncation_order in 1..4 and input_chunk_bits in 4..8")
        access = str(_pin(pins, "table_access", "parallel_banks"))
        reduction = str(_pin(pins, "final_reduction", "adder_chain"))
        split = str(_pin(pins, "offset_partitioning", "none")) == "split_subwords"
        symmetric = bool(_pin(pins, "symmetry", False))
        used = min(ub, Fo + 2)
        if used <= chunk:
            raise ValueError(f"ATA chunk {chunk} needs an address field in addition to its offset; argument has {used} used bits")
        high_bits = used - chunk
        high = n.bits(u, ub - 1, ub - high_bits)
        offset = n.bits(u, ub - high_bits - 1, ub - high_bits - chunk)
        nodes = tuple(range(-order, order + 1)) if symmetric else tuple(range(2 * order + 1))
        reads = len(nodes)
        ports = {"parallel_banks": 1, "dual_port": 2}.get(access)
        if ports is None:
            raise ValueError(f"unknown ATA table_access {access!r}")
        banks = int(_pin(pins, "table_bank_count", (reads + ports - 1) // ports))
        if not (reads + ports - 1) // ports <= banks <= reads:
            raise ValueError(f"ATA {reads} live reads with {ports} ports per bank requires "
                             f"{(reads + ports - 1) // ports}..{reads} live banks, got {banks}")
        if "table_bank_count" in pins and not 2 <= banks <= 6:
            raise ValueError("ATA table_bank_count must be in 2..6")
        entries = (1 << high_bits) + 2 * order
        frac = Fo + 8
        first = nodes[0]
        table = []
        for address in range(entries):
            argument = max(0, min((address + first) << (ub - high_bits), (1 << ub) - 1))
            table.append(int(round(self._g(argument, self.Fu) * (1 << frac))))
        table_width = max(2, max(abs(value) for value in table).bit_length() + 1)
        address_width = max(1, (entries - 1).bit_length())
        values = {}
        bank_prefix = f"{self.label}_{n.core_index}_ata"
        for ri, node in enumerate(nodes):
            address = self._address_add(n.ext(high, address_width), n.const(node - first, address_width))
            values[node] = n.rom(table, address, table_width, True, bank=f"{bank_prefix}_{ri % banks}")
        # Coefficients of each Lagrange basis polynomial provide an exact
        # rational finite-difference stencil over all provisioned reads.
        weights = {}
        for node in nodes:
            poly = [Fraction(1)]
            denominator = Fraction(1)
            for other in nodes:
                if node == other:
                    continue
                result = [Fraction(0)] * (len(poly) + 1)
                for degree, coefficient in enumerate(poly):
                    result[degree] -= other * coefficient
                    result[degree + 1] += coefficient
                poly = result
                denominator *= node - other
            weights[node] = [value / denominator for value in poly]
        terms = [values[0]]
        power = offset
        for degree in range(1, order + 1):
            if degree > 1:
                power = n.shr(n.mul(power, offset), chunk)
            for node in nodes:
                coefficient = weights[node][degree]
                if coefficient == 0:
                    continue
                weighted = n.shr(_const_mul(n, values[node], abs(coefficient), frac + 4), frac + 4)
                if split:
                    low_bits = chunk // 2
                    hi = n.bits(power, power.w - 1, low_bits)
                    lo = n.bits(power, low_bits - 1, 0)
                    product = n.add(n.shl(n.mul(weighted, hi), low_bits), n.mul(weighted, lo))
                else:
                    product = n.mul(weighted, power)
                term = n.shr(product, chunk)
                terms.append(n.neg(term) if coefficient < 0 else term)
        result = n.shr(self._reduce(terms, reduction), frac - Fo)
        self.table_bits = banks * entries * table_width
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "truncation_order", order, "live finite-difference orders")
        effective(pins, "table_bank_count", banks, "physical tables with live read ports",
                  {"reads": reads, "ports_per_bank": ports})
        effective(pins, "table_access", access, "parallel bank read circuit")
        effective(pins, "input_chunk_bits", offset.w, "offset bits entering the finite-difference evaluator")
        effective(pins, "final_reduction", reduction, "final sum topology")
        self.notes.append(f"add_table_add: order {order}, chunk {chunk} bits, {reads} reads over {banks} banks, "
                          f"{ports} ports per bank, {len(terms)} live sum terms, {self.table_bits} table bits")
        return _clamp_result(n, result, Fo + ib)


def table_engine(family: str, pins: dict):
    def eng(net: Net, core: Core, u: Ref, Fu: int, Fo: int, label: str) -> Ref:
        te = TableEngine(net, core, Fu, Fo, family, pins, label)
        R = te.build(u)
        net.notes += [f"{label}: {x}" for x in te.notes]
        return R
    return eng


# ---- shared helpers of the iterative engines ----------------------------------------------------
def _const_mul(n: Net, a: Ref, C, fbits: int, cw: int | None = None) -> Ref:
    """a times a positive real constant C held to cw bits (fraction fbits of the product's frame)."""
    with mpmath.workprec(max(PROFILE_BITS, fbits + 32)):
        cq = int(mpmath.floor(mpmath.mpf(C) * (1 << fbits) + mpmath.mpf("0.5")))
    return n.mul(a, n.const(cq, cw or max(1, cq.bit_length())))


def _table_square(n, value, fraction_bits):
    """Square a normalized eight-bit residual mantissa and restore its scale."""
    negative = n.lt(value, n.const(0, value.w, True)) if value.s else n.const(0, 1)
    magnitude = n.uns(n.trunc(n.mux(negative, n.neg(value), n.sgn(value)), value.w))
    width = magnitude.w
    if width < 8:
        raise ValueError("table-square residual needs at least eight varying bits")
    leading = n.lzc(magnitude)
    normalized = n.shlv(magnitude, leading, width)
    index = n.bits(normalized, width - 1, width - 8)
    squared = n.rom([i * i for i in range(256)], index, 16)
    distance_width = (2 * width + fraction_bits + 1).bit_length() + 2
    distance = n.add(n.shl(n.sgn(leading), 1),
                     n.const(fraction_bits - 2 * (width - 8), distance_width, True), distance_width)
    right = n.ge(distance, n.const(0, distance_width, True))
    right_amount = n.uns(n.mux(right, distance, n.const(0, distance_width, True)))
    left_amount = n.uns(n.mux(right, n.const(0, distance_width + 1, True), n.neg(distance)))
    result_width = max(16, 2 * width - fraction_bits + 2)
    extended = n.ext(squared, result_width)
    return n.mux(right, n.shrv(extended, right_amount), n.shlv(extended, left_amount, result_width))


def _eval_coeffs(n: Net, cs: list, fq: list, t: Ref, Ft: int, F: int, evaluator: str) -> Ref:
    """A polynomial over the local variable t (Ft fraction bits) with the
    coefficient refs cs (fq_i fraction bits each) at F fraction bits."""
    pe = PolyEngine.__new__(PolyEngine)
    pe.net, pe.Fint, pe.encoding = n, F, "plain"
    pe.notes = []
    d = len(cs) - 1
    if evaluator == "coefficient_adapted":
        memories = {r.name: payload for kind, _, r, payload in n.events if kind == "rom"}
        if any(c.name not in memories for c in cs):
            raise ValueError("coefficient adaptation requires coefficient tables with known contents")
        columns = [memories[c.name][0] for c in cs]
        index = memories[cs[0].name][1]
        rows = [list(row) for row in zip(*columns)]
        pe.encoding = "plain"
        return pe._adapted_general(t, Ft, index, rows, fq, d)
    if evaluator == "estrin":
        return pe._estrin(cs, fq, t, Ft, d)
    if evaluator == "factored":
        return pe._factored(cs, fq, t, Ft, d)
    if evaluator == "parallel_monomial":
        pe.evaluator = "parallel_monomial"
        return pe._monomial(cs, fq, t, Ft, [[0] * (d + 1)], n.const(0, 1), d)
    if evaluator == "shift_add_coeff":
        memories = {r.name: payload for kind, _, r, payload in n.events if kind == "rom"}
        if any(c.name not in memories for c in cs):
            raise ValueError("shift-add evaluation requires coefficient tables with known contents")
        rows = [list(row) for row in zip(*(memories[c.name][0] for c in cs))]
        pe.evaluator = "shift_add_coeff"
        return pe._monomial(cs, fq, t, Ft, rows, memories[cs[0].name][1], d)
    if evaluator in ("horner", "fma_based"):
        return pe._horner(cs, fq, t, Ft, d, exact=(evaluator == "fma_based"))
    raise ValueError(f"unknown polynomial evaluator {evaluator!r}")


class _Engine:
    """An engine: `covers` the cores it evaluates, `direct` the cores it
    returns as the function's value rather than the factored ratio, and
    `build` the datapath."""
    covers: set = set()
    direct: set = set()

    def __init__(self, family: str, pins: dict):
        self.family, self.pins = family, pins

    def P(self, key, default):
        return _pin(self.pins, key, default)

    def __call__(self, net: Net, core: Core, u: Ref, Fu: int, Fo: int, label: str) -> Ref | tuple[Ref, Ref]:
        token = _fit_precision.set(max(_fit_precision.get(), 2 * Fo + Fu + 32))
        try:
            R, notes = self.build(net, core, u, Fu, Fo)
        finally:
            _fit_precision.reset(token)
        net.notes += [f"{label}: {x}" for x in notes]
        return R


# ---- rational approximation --------------------------------------------------------------------
class RationalEngine(_Engine):
    covers = {"exp2c", "log2c", "recipc", "sqrtc", "rsqrtc", "sinc", "tanhc", "erfe", "gelue", "gelur", "expm1c"}

    def _fit(self, g, a, b, dn: int, dd: int, construction: str, relative: bool) -> tuple:
        """High-precision Padé or weighted rational least-squares coefficients."""
        bits = max(PROFILE_BITS, _fit_precision.get())
        with mpmath.workprec(bits):
            left, right = _mp(a), _mp(b)
            h = right - left
            if construction == "pade":
                middle = left + h / 2
                series = mpmath.taylor(g, middle, dn + dd)
                numerator, denominator = mpmath.pade(series, dn, dd)
                def shift(coefficients):
                    output = [mpmath.mpf(0)] * len(coefficients)
                    for k, coefficient in enumerate(coefficients):
                        for j in range(k + 1):
                            output[j] += coefficient * mpmath.binomial(k, j) * (-h / 2) ** (k - j)
                    return output
                numerator, denominator = shift(list(numerator)), shift(list(denominator))
                scale = denominator[0]
                return ([_fraction_of_mp(value / scale) for value in numerator],
                        [_fraction_of_mp(value / scale) for value in denominator])
            count = 4 * (dn + dd + 2)
            points = [h / 2 * (1 - mpmath.cos(mpmath.pi * (2 * i + 1) / (2 * count))) for i in range(count)]
            values = [g(left + point) for point in points]
            weights = [mpmath.mpf(1)] * count
            for _ in range(8 if construction == "minimax_remez" else 1):
                matrix = mpmath.matrix(count, dn + dd + 1)
                rhs = mpmath.matrix(count, 1)
                for i, (point, value) in enumerate(zip(points, values)):
                    weight = weights[i] / (abs(value) if relative else 1)
                    for k in range(dn + 1):
                        matrix[i, k] = weight * point ** k
                    for k in range(1, dd + 1):
                        matrix[i, dn + k] = -weight * value * point ** k
                    rhs[i] = weight * value
                try:
                    solution, _ = mpmath.qr_solve(matrix, rhs)
                except (ValueError, ZeroDivisionError):
                    # A lower-degree exact rational function can make the
                    # requested system rank-deficient. Its pseudoinverse is
                    # still the same least-squares construction.
                    u, singular, v = mpmath.svd(matrix, full_matrices=False)
                    cutoff = max(singular) * mpmath.power(2, -(bits - 24))
                    projected = u.T * rhs
                    scaled = mpmath.matrix([projected[i] / value if value > cutoff else 0
                                            for i, value in enumerate(singular)])
                    solution = v.T * scaled
                numerator = list(solution[:dn + 1])
                denominator = [mpmath.mpf(1)] + list(solution[dn + 1:])
                errors = []
                for point, value in zip(points, values):
                    pv = sum(c * point ** k for k, c in enumerate(numerator))
                    qv = sum(c * point ** k for k, c in enumerate(denominator))
                    errors.append(abs(pv / qv - value) / (abs(value) if relative else 1))
                maximum = max(errors)
                if maximum == 0:
                    break
                weights = [weight * (mpmath.mpf("0.5") + error / maximum)
                           for weight, error in zip(weights, errors)]
            return ([_fraction_of_mp(value) for value in numerator],
                    [_fraction_of_mp(value) for value in denominator])

    def _factored_polynomial(self, n, rows, index, t, Ft, F, evaluator):
        """Real linear/quadratic factors, each evaluated by its selected datapath."""
        import numpy as np
        degree = len(rows[0]) - 1
        count = (degree + 1) // 2
        factorizations = []
        bits = max(_fit_precision.get(), 2 * F + 64)
        with mpmath.workprec(bits):
            for row in rows:
                actual = list(row)
                while len(actual) > 1 and actual[-1] == 0:
                    actual.pop()
                if len(actual) > 1:
                    # Binary64 roots are initial guesses only. Every factor
                    # is refined against the full-precision coefficients.
                    initial = list(np.polynomial.polynomial.polyroots([float(value) for value in actual]))
                    roots = list(mpmath.polyroots([_mp(value) for value in reversed(actual)],
                                                 roots_init=initial, maxsteps=500, extraprec=bits))
                else:
                    roots = []
                factors = []
                real_tolerance = mpmath.power(2, -(bits // 2))
                while roots:
                    root = roots.pop(0)
                    if abs(root.imag) > real_tolerance:
                        partner = min(range(len(roots)), key=lambda i: abs(roots[i] - root.conjugate()))
                        other = roots.pop(partner)
                        factors.append([_fraction_of_mp((root * other).real),
                                        _fraction_of_mp(-(root + other).real), Fraction(1)])
                    elif roots:
                        real = next((i for i, other in enumerate(roots) if abs(other.imag) <= real_tolerance), None)
                        if real is None:
                            factors.append([-_fraction_of_mp(root.real), Fraction(1), Fraction(0)])
                        else:
                            other = roots.pop(real)
                            factors.append([_fraction_of_mp((root * other).real),
                                            _fraction_of_mp(-(root + other).real), Fraction(1)])
                    else:
                        factors.append([-_fraction_of_mp(root.real), Fraction(1), Fraction(0)])
                if not factors:
                    factors = [[Fraction(1), Fraction(0), Fraction(0)]]
                factors[0] = [coefficient * actual[-1] for coefficient in factors[0]]
                factors += [[Fraction(1), Fraction(0), Fraction(0)] for _ in range(count - len(factors))]
                if len(factors) != count:
                    raise ValueError("rational factorization has an inconsistent degree")
                # Reconstruct coefficients to verify the root refinement;
                # never silently emit binary64 factors into a wider ROM.
                reconstructed = [Fraction(1)]
                for factor in factors:
                    product = [Fraction(0)] * (len(reconstructed) + 2)
                    for i, a in enumerate(reconstructed):
                        for j, b in enumerate(factor):
                            product[i + j] += a * b
                    reconstructed = product
                bound = max(Fraction(1), *(abs(value) for value in row)) * Fraction(2) ** -(F + 32)
                for i, value in enumerate(row):
                    if abs(reconstructed[i] - value) > bound:
                        raise ValueError("rational factor refinement does not preserve the requested coefficient precision")
                factorizations.append(factors)
        smallest = min((abs(value) for row in factorizations for factor in row for value in factor if value), default=1.0)
        # A small leading factor is multiplied back by large later factors.
        # Preserve its relative precision until the product tree completes.
        from chialu.verify.formats import _floor_log2
        extra = max(0, -_floor_log2(smallest)) + 12
        working = F + extra
        values = []
        for factor in range(count):
            coefficients = []
            for power in range(3):
                table = [_quantize(row[factor][power], working) for row in factorizations]
                width = max(2, max(abs(value) for value in table).bit_length() + 1)
                coefficients.append(n.rom(table, index, width, True))
            values.append(_eval_coeffs(n, coefficients, [working] * 3, t, Ft, working, evaluator))
        while len(values) > 1:
            values = [n.shr(n.mul(values[i], values[i + 1]), working) if i + 1 < len(values) else values[i]
                      for i in range(0, len(values), 2)]
        return n.shr(values[0], extra)

    def build(self, n: Net, core: Core, u: Ref, Fu: int, Fo: int) -> tuple:
        dn, dd = int(self.P("numerator_degree", 1)), int(self.P("denominator_degree", 1))
        K = int(self.P("segments", 1))
        if K == 1:
            core, u, Fu = _smooth_root_argument(n, core, u, Fu)
        construction = str(self.P("construction", "minimax_remez"))
        relative = str(self.P("objective_norm", "absolute_minimax")) == "relative_minimax"
        form = str(self.P("expression_form", "direct_fraction"))
        odd = str(self.P("symmetry_form", "unrestricted")) == "odd" and core.even_in is not None
        if self.P("symmetry_form", "unrestricted") == "odd" and not odd:
            raise ValueError(f"symmetry_form=odd does not apply to the {core.name} core")
        evn, evd = str(self.P("numerator.family", "horner")), str(self.P("denominator.family", "horner"))
        segf = str(self.P("segmenter.family", "uniform_high_bit_decode"))
        notes = []
        if K == 1 and segf != "uniform_high_bit_decode":
            raise ValueError(f"segmenter.family={segf} requires at least two live rational approximation segments")
        # the index and the local variable through a polynomial engine's segmenter
        pe = PolyEngine(n, core, Fu, Fo, K=K, degree=dn, segmenter=segf, basis="chebyshev",
                        addressing=str(self.P("segmenter.addressing", "direct_address_bits")),
                        boundary_search=str(self.P("segmenter.boundary_search", "greedy_error_driven")))
        seg = pe._segments()
        k, t, Ft = pe._index(u, seg)
        if odd:
            # the fit in the square of the local variable (the function is even in it)
            t2 = n.bits(n.shr(n.mul(t, t), Ft), Ft - 1, 0)
            tv, Ftv = t2, Ft
        else:
            tv, Ftv = t, Ft
        F = Fo + 3
        ptab, qtab = [], []
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            for kk in range(seg.K):
                a, b = seg.bounds(kk)
                if a >= core.hi:
                    ptab.append(ptab[-1] if ptab else [0.0] * (dn + 1)); qtab.append(qtab[-1] if qtab else [1.0] + [0.0] * dd)
                    continue
                b = min(b, core.hi)
                sc = 1 << seg.shifts[kk]
                if odd:
                    gl = (lambda v, a=a, sc=sc: core.f(_mp(a) + mpmath.sqrt(_mp(v)) / sc))
                    p, q = self._fit(gl, 0.0, ((b - a) * sc) ** 2, dn, dd, construction, relative)
                else:
                    gl = (lambda v, a=a, sc=sc: core.f(_mp(a) + _mp(v) / sc))
                    p, q = self._fit(gl, 0.0, (b - a) * sc, dn, dd, construction, relative)
                ptab.append(p); qtab.append(q)
        if form == "decomposed" and dn >= dd and dd >= 1:
            # p/q = c(t) + p'(t)/q(t): the polynomial part by long division
            ctab, rtab = [], []
            for p, q in zip(ptab, qtab):
                if q[-1] == 0:
                    raise ValueError("the selected denominator degree is absent from the fitted polynomial")
                quotient = [Fraction(0)] * (dn - dd + 1)
                remainder = list(p)
                for power in range(dn - dd, -1, -1):
                    coefficient = remainder[power + dd] / q[dd]
                    quotient[power] = coefficient
                    for j in range(dd + 1):
                        remainder[power + j] -= coefficient * q[j]
                ctab.append(quotient)
                rtab.append(remainder[:dd])
            notes.append("expression_form decomposed: the polynomial part separated, the remainder divided")
        else:
            ctab = None
            if form == "decomposed":
                notes.append("expression_form decomposed needs a numerator degree at least the denominator's; direct fraction")
        Fq = F
        pq = [_quantize(x, Fq) for row in ptab for x in row]
        qq = [_quantize(x, Fq) for row in qtab for x in row]
        for key, degree, rows in (("numerator_degree", dn, ptab), ("denominator_degree", dd, qtab)):
            if key in self.pins and not any(_quantize(row[degree], Fq) for row in rows):
                raise ValueError(f"{key}={degree} has no nonzero leading coefficient at {Fq} fraction bits; "
                                 "the target must use enough precision to exercise this degree")
        wp = max(2, max(abs(v) for v in pq).bit_length() + 1)
        wq = max(2, max(abs(v) for v in qq).bit_length() + 1)
        pcs = [n.rom([_quantize(row[i], Fq) for row in ptab], k, wp, True) for i in range(dn + 1)]
        qcs = [n.rom([_quantize(row[i], Fq) for row in qtab], k, wq, True) for i in range(dd + 1)]
        if form == "factored":
            pv = self._factored_polynomial(n, ptab, k, tv, Ftv, F, evn)
            qv = self._factored_polynomial(n, qtab, k, tv, Ftv, F, evd)
        else:
            pv = _eval_coeffs(n, pcs, [Fq] * (dn + 1), tv, Ftv, F, evn)
            qv = _eval_coeffs(n, qcs, [Fq] * (dd + 1), tv, Ftv, F, evd)
        if ctab is not None:
            rq = [_quantize(x, Fq) for row in rtab for x in row] or [0]
            cq_ = [_quantize(x, Fq) for row in ctab for x in row] or [0]
            wr = max(2, max(abs(v) for v in rq).bit_length() + 1)
            wc = max(2, max(abs(v) for v in cq_).bit_length() + 1)
            rcs = [n.rom([_quantize(row[i], Fq) for row in rtab], k, wr, True) for i in range(dd)]
            ccs = [n.rom([_quantize(row[i], Fq) for row in ctab], k, wc, True) for i in range(dn - dd + 1)]
            pv = _eval_coeffs(n, rcs, [Fq] * dd, tv, Ftv, F, evn)
            cv = _eval_coeffs(n, ccs, [Fq] * (dn - dd + 1), tv, Ftv, F, evn)
        # the division: (|p| << Fo) / q with q positive, the sign restored (a decomposed remainder can be
        # negative); a library divider when the slot names one
        pneg = n.lt(pv, n.const(0, pv.w, True))
        pabs = n.uns(n.trunc(n.mux(pneg, n.neg(pv), pv), pv.w))
        qabs = n.uns(n.mux(n.lt(qv, n.const(1, qv.w, True)), n.const(1, qv.w, True), qv))
        ib = core.ibits()
        num = n.shl(pabs, Fo + 1)
        Qw = num.w
        quot = self._divide(n, num, qabs, Qw, notes)
        r = n.shr(quot, 1)                                             # |p|/q at Fo fraction bits
        r = n.mux(pneg, n.neg(r), n.sgn(r))
        if ctab is not None:
            r = n.add(r, n.shr(cv, F - Fo))
        if form == "factored":
            notes.append("expression_form factored: real linear/quadratic numerator and denominator factors, balanced products, one division")
        from chialu.targets.rtl.families.fidelity import effective
        effective(self.pins, "segments", seg.K, "distinct rational approximation intervals", {"fraction_bits": Fu})
        effective(self.pins, "numerator_degree", dn, "active numerator degree")
        effective(self.pins, "denominator_degree", dd, "active denominator degree")
        effective(self.pins, "expression_form", form, "rational expression circuit")
        effective(self.pins, "evaluation_format", "fixed_point", "fixed-point polynomial and division arithmetic")
        effective(self.pins, "numerator.family", evn, "numerator evaluator circuit")
        effective(self.pins, "denominator.family", evd, "denominator evaluator circuit")
        notes.append(f"rational {dn}/{dd} {construction} over {seg.K} segment(s)" + (" (odd form in t^2)" if odd else ""))
        return _clamp_result(n, r, Fo + ib), notes

    def _divide(self, n: Net, a: Ref, b: Ref, Qw: int, notes: list) -> Ref:
        fam = self.P("divider.family", None)
        if fam and fam != "behavioral_star":
            from chialu.targets.rtl import families as FAM
            sub = {k[len("divider."):]: v for k, v in self.pins.items() if k.startswith("divider.") and k != "divider.family"}
            m = FAM.div_module(str(fam), sub, a.w, b.w, Qw)
            if m is not None:
                q = n.declare(Qw, False, lambda env, a=a, b=b, m_=(1 << Qw) - 1: (env[a.name] // max(1, env[b.name])) & m_)
                rr = n.declare(b.w, False, lambda env, a=a, b=b: env[a.name] % max(1, env[b.name]))
                n.inst(m, {"a": a.name, "b": b.name, "q": q.name, "r": rr.name}, f"the divider slot: family {fam} realized by the library module {m.name}")
                notes.append(f"division by the divider slot's {fam}")
                return q
            raise ValueError(f"requested SFU divider slot {fam!r} cannot generate {a.w}/{b.w} -> {Qw} bits")
        else:
            notes.append("division by the / operator (the divider slot undeclared)")
        return n.wire(Qw, False, f"{a.name} / {b.name}", lambda env, a=a, b=b, m_=(1 << Qw) - 1: (env[a.name] // max(1, env[b.name])) & m_, "q")


# ---- Wong-Goto table-factor refinement -------------------------------------------------------------
class WongGotoEngine(_Engine):
    covers = {"recipc", "rsqrtc", "sqrtc", "exp2c", "log2c"}
    direct = {"log2c"}

    def build(self, n: Net, core: Core, u: Ref, Fu: int, Fo: int) -> tuple:
        fb = int(self.P("factor_bits", 8))
        stages = int(self.P("residual_stages", 1))
        tail = str(self.P("terminal_correction", "truncated_taylor"))
        tdeg = int(self.P("tail_degree", 1))
        notes = []
        F = Fo + 4
        ub = u.w
        if core.name in ("recipc", "rsqrtc", "sqrtc"):
            # m = 1 + w (w < 1) or 2 w (w >= 1) as a fixed value at F bits
            if core.L > 1:
                hi_bit = n.bit(u, ub - 1)
                frac = n.bits(u, ub - 2, 0)
                m = n.mux(hi_bit, n.cat(n.const(1, 1), frac, n.const(0, 1)), n.cat(n.const(0, 1), n.const(1, 1), frac))   # 2 (1 + f) or 1 + f
                Fm = Fu                                                       # fraction bits of m (2 integer bits)
            else:
                m = n.cat(n.const(1, 1), u)
                Fm = Fu
            m = n.shl(m, F - Fm) if F > Fm else n.shr(m, Fm - F)
            # the seed table over the top fb bits of the fraction
            from chialu.targets.rtl.families.fidelity import effective
            fb = effective(self.pins, "factor_bits", min(fb, ub), "factor table address width", {"argument_bits": ub})
            idx = n.bits(u, ub - 1, ub - fb)
            tab = []
            with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                for a in range(1 << fb):
                    uu = (a << (ub - fb)) + ((1 << (ub - fb - 1)) if ub > fb else 0)
                    g = core.f(mpmath.mpf(uu) / (1 << Fu)) if core.name != "sqrtc" else 1 / mpmath.sqrt(_mval(uu, Fu, core.L))
                    tab.append(int(mpmath.floor(g * (1 << (fb + 2)) + mpmath.mpf("0.5"))))
            y = n.rom(tab, idx, fb + 3)                                       # fb+2 fraction bits
            y = n.shl(y, F - (fb + 2))
            rsq = core.name in ("rsqrtc", "sqrtc")
            # the residual r = m y (recip) or m y^2 (rsqrt): 1 + e
            for st in range(stages):
                if rsq:
                    y2 = n.shr(n.mul(y, y), F)
                    r = n.shr(n.mul(m, y2), F)
                else:
                    r = n.shr(n.mul(m, y), F)
                e = n.sub(n.sgn(r), n.const(1 << F, F + 2, True))                 # the residual e, small
                # the factor 1 - e (recip) or 1 - e/2 (rsqrt) from the residual's top significant bits (a short operand)
                eb = min(F, fb * (st + 1) + 2)                                     # significant bits kept
                lo_e = F - min(F, fb * (st + 1) * 2 + 4)                           # the residual's magnitude is below 2^-(fb (st+1))
                es = n.shr(e, max(0, lo_e))                                        # short residual
                if rsq:
                    es = n.shr(es, 1)
                fac = n.sub(n.const(1 << (F - max(0, lo_e)), F - max(0, lo_e) + 2, True), es)    # 1 - e (short)
                y = n.shr(n.mul(y, fac), F - max(0, lo_e))                          # a rectangular multiply
                y = n.bits(n.uns(y), F + 1, 0) if y.w > F + 2 else n.uns(y)
            # the tail: (1 + e)^-1 or (1 + e)^-1/2 as a truncated Taylor series in the last residual, or e^2 from a table
            if rsq:
                y2 = n.shr(n.mul(y, y), F)
                r = n.shr(n.mul(m, y2), F)
            else:
                r = n.shr(n.mul(m, y), F)
            e = n.sub(n.sgn(r), n.const(1 << F, F + 2, True))
            corr = n.neg(e) if not rsq else n.neg(n.shr(e, 1))                 # -e or -e/2
            if tdeg >= 2 or tail == "table_square":
                if tail == "table_square":
                    e2 = _table_square(n, e, F)
                else:
                    e2 = n.shr(n.mul(e, e), F)
                corr = n.add(corr, e2 if not rsq else n.add(n.shr(e2, 2), n.shr(e2, 3)))   # + e^2 (recip), + 3 e^2 / 8 (rsqrt)
                power = e2
                for degree in range(3, tdeg + 1):
                    power = n.shr(n.mul(power, e), F)
                    coefficient = Fraction(5, 16) if degree == 3 else Fraction(35, 128)
                    term = n.shr(_const_mul(n, power, coefficient, F + 2), F + 2) if rsq else power
                    corr = n.sub(corr, term) if degree & 1 else n.add(corr, term)
            one = n.const(1 << F, F + 2, True)
            yf = n.shr(n.mul(y, n.add(one, corr)), F)
            if core.name == "sqrtc":
                yf = n.shr(n.mul(yf, m), F)                                        # sqrt(m) = m rsqrt(m)
            R = n.shr(yf, F - Fo)
            notes.append(f"table_factor_refinement: {fb}-bit factor table, {stages} refinement stage(s), {tail} tail of degree {tdeg}")
            return _clamp_result(n, R, Fo + core.ibits()), notes
        if core.name == "exp2c":
            # 2^f = product of 2^(chunk_i) from tables over fb-bit chunks, a Taylor tail on the last residual
            chunks = []
            pos = ub
            acc = None
            i = 0
            while pos > 0 and i < stages + 1:
                cb = min(fb, pos)
                sel = n.bits(u, pos - 1, pos - cb)
                tab = []
                with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                    for a in range(1 << cb):
                        tab.append(int(mpmath.floor(mpmath.power(2, mpmath.mpf(a << (pos - cb)) / (1 << Fu)) * (1 << F) + mpmath.mpf("0.5"))))
                tv = n.rom(tab, sel, F + 2)
                acc = tv if acc is None else n.shr(n.mul(acc, tv), F)
                pos -= cb
                i += 1
            if pos > 0:
                # the tail residual eps = the remaining bits: 2^eps ~ 1 + eps ln2 + (eps ln2)^2 / 2
                eps = n.bits(u, pos - 1, 0)
                epsF = n.shl(eps, F - Fu) if F > Fu else n.shr(eps, Fu - F)
                l = _const_mul(n, epsF, mpmath.log(2), F + 2)
                l = n.shr(l, F + 2)
                tailv = n.add(n.const(1 << F, F + 2), n.ext(l, F + 2), F + 3)
                if tdeg >= 2:
                    power = _table_square(n, l, F) if tail == "table_square" else n.shr(n.mul(l, l), F)
                    tailv = n.add(tailv, n.shr(power, 1))
                    for degree in range(3, tdeg + 1):
                        power = n.shr(n.mul(power, l), F)
                        term = n.shr(_const_mul(n, power, Fraction(1, math.factorial(degree)), F + 2), F + 2)
                        tailv = n.add(tailv, term)
                acc = n.shr(n.mul(acc, tailv), F)
            R = n.shr(acc, F - Fo)
            notes.append(f"table_factor_refinement: {stages + 1} factor tables of {fb} bits, a Taylor tail of degree {tdeg}")
            return _clamp_result(n, R, Fo + core.ibits()), notes
        # log2c, direct: m' = 1 + d in [0.75, 1.5); each stage reads the residual's top bits t_i, multiplies by
        # the table's 1 / (1 + t_i) (a rectangular multiply: the factor has fb + 3 significant bits) and adds
        # log2(1 + t_i); the residual shrinks by 2^-fb per stage
        d = n.sub(n.sgn(u), n.const(1 << (Fu - 2), Fu + 1, True))                # d = u - 1/4
        r = n.add(n.shl(n.const(1, 1), F), n.shl(d, F - Fu) if F > Fu else d)   # 1 + d at F bits (signed)
        L = n.const(0, 2, True)
        for st in range(stages + 1):
            e = n.sub(r, n.const(1 << F, F + 2, True))
            lo = F - (fb * (st + 1) + 1)
            if lo < 0:
                lo = 0
            fbw = fb + 3
            es_ = n.shr(e, lo)
            tsel = n.trunc(es_, fbw) if es_.w > fbw else es_                   # the residual's significant bits, signed
            tw = tsel.w
            tab, fac_t = [], []
            with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                for a in range(1 << tw):
                    tval = _wrap(a, tw, True) * (1 << lo) / mpmath.mpf(1 << F)
                    if tval <= -0.999:
                        tval = mpmath.mpf("-0.999")
                    tab.append(int(mpmath.floor(mpmath.log(1 + tval, 2) * (1 << F) + mpmath.mpf("0.5"))))
                    fac_t.append(int(mpmath.floor((1 << F) / (1 + tval) + mpmath.mpf("0.5"))))
            lt = n.rom(tab, n.uns(tsel), F + 3, True)
            fac = n.rom(fac_t, n.uns(tsel), F + 3)
            r = n.shr(n.mul(r, fac), F)
            L = n.add(L, lt)
            r = n.trunc(r, F + 3) if r.w > F + 3 else r
        e = n.sub(r, n.const(1 << F, F + 2, True))
        tl = _const_mul(n, e, 1 / mpmath.log(2), F + 2)
        tl = n.shr(tl, F + 2)
        if tdeg >= 2:
            e2 = _table_square(n, e, F) if tail == "table_square" else n.shr(n.mul(e, e), F)
            tl = n.sub(tl, n.shr(_const_mul(n, e2, 1 / (2 * mpmath.log(2)), F + 2), F + 2))
            power = e2
            for degree in range(3, tdeg + 1):
                power = n.shr(n.mul(power, e), F)
                term = n.shr(_const_mul(n, power, 1 / (degree * mpmath.log(2)), F + 2), F + 2)
                tl = n.add(tl, term) if degree & 1 else n.sub(tl, term)
        L = n.add(L, tl)
        notes.append(f"table_factor_refinement: {stages + 1} factor stages of {fb} bits (log), a Taylor tail of degree {tdeg}")
        return n.shr(L, F - Fo), notes


def _mval(uu: int, Fu: int, L: float):
    """m of the sqrt cores: 1 + w below 1, 2 w from 1."""
    w = mpmath.mpf(uu) / (1 << Fu)
    return 1 + w if w < 1 else 2 * w


# ---- logarithmic (Mitchell) converters ---------------------------------------------------------
class LnsEngine(_Engine):
    covers = {"exp2c", "log2c", "recipc", "sqrtc", "rsqrtc"}
    direct = {"log2c"}

    def _corr(self, n: Net, core_fn, u: Ref, Fu: int, F: int, notes: list) -> Ref:
        """The correction term c(u) of a Mitchell identity (signed, F fraction bits)."""
        corr = str(self.P("correction", "none"))
        regions = int(self.P("regions", 1))
        if corr == "none":
            return n.const(0, 2, True)
        if corr == "rom_free_shift_add":
            # c(u) ~ u (1 - u) k with k = 1/4 + 1/16 + 1/32 = 0.34375 (three shifts), signed by the identity's side
            um = n.sub(n.const(1 << Fu, Fu + 2), n.ext(u, Fu + 2))
            p = n.shr(n.mul(n.sgn(u), n.sgn(um)), Fu)
            p = n.shl(p, F - Fu) if F > Fu else n.shr(p, Fu - F)
            k = n.add(n.add(n.shr(p, 2), n.shr(p, 4)), n.shr(p, 5))
            sgn = -1 if core_fn == "exp2c" else 1
            notes.append("rom_free correction u (1 - u) (1/4 + 1/16 + 1/32)")
            return n.neg(k) if sgn < 0 else k
        K = regions
        if not 1 <= K <= 8:
            raise ValueError(f"logarithmic correction regions must be in 1..8, got {K}")
        kw = max(1, (K - 1).bit_length())
        scaled = n.mulc(u, K, max(1, K.bit_length()))
        high = n.shr(scaled, Fu)
        idx = n.bits(high, kw - 1, 0) if high.w > kw else n.ext(high, kw)
        Ft = Fu
        t = n.bits(scaled, Fu - 1, 0)
        from chialu.targets.rtl.families.fidelity import effective
        effective(self.pins, "regions", K, "exact correction-table region count", {"argument_bits": u.w})
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            if corr == "constant_per_region":
                tab = []
                for kk in range(K):
                    a, b = Fraction(kk, K), Fraction(kk + 1, K)
                    vals = [core_fn_val(core_fn, _mp(a) + _mp(b - a) * i / 32) for i in range(33)]
                    tab.append(int(round(sum(vals) / len(vals) * (1 << F))))
                w = max(2, max(abs(v) for v in tab).bit_length() + 1)
                notes.append(f"constant correction per region ({K})")
                return n.rom(tab, idx, w, True)
            c0s, c1s = [], []
            for kk in range(K):
                a, b = Fraction(kk, K), Fraction(kk + 1, K)
                c = _fit_poly(lambda x: core_fn_val(core_fn, x), a, b, 1, "chebyshev")
                c0s.append(_quantize(c[0], F)); c1s.append(_quantize(c[1] / K, F))
            w0 = max(2, max(abs(v) for v in c0s).bit_length() + 1)
            w1 = max(2, max(abs(v) for v in c1s).bit_length() + 1)
            c0 = n.rom(c0s, idx, w0, True)
            c1 = n.rom(c1s, idx, w1, True)
            notes.append(f"piecewise-linear correction over {K} region(s)")
            return n.add(c0, n.shr(n.mul(c1, n.sgn(t)), Ft))

    def build(self, n: Net, core: Core, u: Ref, Fu: int, Fo: int) -> tuple:
        notes = []
        F = Fo + 2
        if core.name == "exp2c":
            base = n.add(n.const(1 << F, F + 2), n.ext(n.shl(u, F - Fu) if F > Fu else n.shr(u, Fu - F), F + 2), F + 3)
            R = n.add(n.sgn(base), self._corr(n, "exp2c", u, Fu, F, notes))
            notes.append("Mitchell antilog 2^f ~ 1 + f")
            return _clamp_result(n, n.shr(R, F - Fo), Fo + 1), notes
        if core.name == "log2c":
            # log2(1 + d) ~ d + c(d) for d >= 0; a negative d goes through 2 m' = 1 + d2 with d2 = 2 d + 1 and a -1
            d = n.sub(n.sgn(u), n.const(1 << (Fu - 2), Fu + 1, True))
            dneg = n.lt(d, n.const(0, d.w, True))
            d2 = n.add(n.shl(d, 1), n.const(1 << Fu, Fu + 3, True))
            dd = n.uns(n.trunc(n.mux(dneg, d2, n.ext(d, d2.w)), Fu))
            c = self._corr(n, "log2c", dd, Fu, F, notes)
            dF = n.shl(n.sgn(dd), F - Fu) if F > Fu else n.shr(n.sgn(dd), Fu - F)
            R = n.add(dF, c)
            R = n.mux(dneg, n.sub(R, n.const(1 << F, F + 3, True)), n.ext(R, R.w + 1))
            notes.append("Mitchell log log2(1 + d) ~ d")
            return n.shr(R, F - Fo), notes
        # recip, sqrt, rsqrt through the log and antilog converters (lns_full_alu)
        if not bool(self.P("lns_full_alu", False)):
            raise ValueError("lns_full_alu false: the reciprocal and root cores are not in the log domain")
        ub = u.w
        if core.L > 1:
            hi_bit = n.bit(u, ub - 1)
            frac = n.bits(u, ub - 2, 0)
            lg_f = n.add(n.ext(n.shl(frac, F - Fu) if F > Fu else frac, F + 3), self._corr(n, "log2c", frac, Fu, F, notes), F + 4)   # log2(1 + f)
            lg = n.add(n.sgn(lg_f), n.mux(hi_bit, n.const(1 << F, F + 2, True), n.const(0, F + 2, True)))                 # log2 m in [0, 2)
        else:
            lg = n.sgn(n.add(n.ext(n.shl(u, F - Fu) if F > Fu else u, F + 3), self._corr(n, "log2c", u, Fu, F, notes), F + 4))
        # the scaled logarithm: -lg (recip), lg/2 (sqrt), -lg/2 (rsqrt); result = 2^(that) = 2^n 2^frac
        if core.name == "recipc":
            s = n.neg(lg)
        elif core.name == "sqrtc":
            s = n.shr(lg, 1)
        else:
            s = n.neg(n.shr(lg, 1))
        fl = n.bits(n.uns(s), F - 1, 0)                                          # frac of the scaled log
        nn = n.shr(s, F)                                                          # floor
        anti = n.add(n.const(1 << F, F + 2), n.ext(fl, F + 2), F + 3)
        anti = n.add(n.sgn(anti), self._corr(n, "exp2c", fl, F, F, notes))
        # 2^nn: nn in {-2..1}: a shift
        sh = n.uns(n.trunc(n.add(nn, n.const(2, nn.w, True)), 3))                 # nn + 2 in 0..3
        R = n.shrv(n.shl(n.uns(anti), 2), n.uns(n.trunc(n.sub(n.const(4, 4), n.ext(sh, 4)), 3)))   # anti 2^nn = (anti << 2) >> (2 - nn)
        notes.append("the log domain: log and antilog converters around a shift")
        return _clamp_result(n, n.shr(R, F - Fo), Fo + core.ibits()), notes


def core_fn_val(kind: str, x):
    """The correction a Mitchell identity needs at x: 2^x - 1 - x (antilog), log2(1 + x) - x (log)."""
    x = mpmath.mpf(x)
    if kind == "exp2c":
        return mpmath.power(2, x) - 1 - x
    return mpmath.log(1 + x, 2) - x


# ---- CORDIC, unrolled -------------------------------------------------------------------------------
class CordicEngine(_Engine):
    covers = {"sinc", "exp2c", "log2c", "recipc", "sqrtc", "rsqrtc", "tanhc"}
    direct = {"sinc", "log2c", "tanhc"}

    def __init__(self, family, pins):
        super().__init__(family, pins)
        self.redundant = family == "redundant_high_radix_cordic"
        self.trace: list = []                    # (i, x, y, sig_pos, zero_sel, est) per micro-rotation, for the harness

    def _iters(self, Fo: int) -> int:
        it = int(self.P("iterations", 16)) if not self.redundant else Fo + 3
        from chialu.targets.rtl.families.fidelity import effective
        return effective(self.pins, "iterations", max(4, min(64, it)), "unrolled micro-rotation count")

    def _scale_set(self, target: float, F: int) -> list:
        """(sign, k) factors (1 + sign 2^-k) whose product approximates the target (scaling iterations)."""
        out = []
        with mpmath.workprec(max(PROFILE_BITS, F + 32)):
            cur = mpmath.mpf(1)
            for _ in range(max(12, F)):
                best = None
                for k in range(1, F):
                    for s in (-1, 1):
                        v = cur * (1 + s * mpmath.power(2, -k))
                        if best is None or abs(v - target) < abs(best[0] - target):
                            best = (v, s, k)
                if abs(best[0] - target) >= abs(cur - target):
                    break
                cur = best[0]
                out.append((best[1], best[2]))
                if abs(cur - target) < mpmath.power(2, -(F - 1)):
                    break
        return out

    def _rot(self, n: Net, x, y, z, mode: str, N: int, F: int, angles: list, sched: list, notes: list, vectoring=False):
        """The micro-rotations: mode circular/hyperbolic/linear; sched the iteration indices (with repeats)."""
        inputs = (x, y, z)
        coordinate = self.P("coordinate_set", mode)
        if coordinate not in (mode, "unified"):
            raise ValueError(f"coordinate_set={coordinate} cannot implement the required {mode} CORDIC operation")
        operation = "vectoring" if vectoring else "rotation"
        selected_mode = self.P("mode", operation)
        if selected_mode not in (operation, "both"):
            raise ValueError(f"mode={selected_mode} cannot implement the required {operation} CORDIC operation")
        redundant = self.redundant
        resid = str(self.P("residual_arithmetic", "carry_save")) if redundant else "cpa"
        if resid == "conventional_cpa":
            resid = "cpa"
        scale_mode = str(self.P("scale_handling", "double_rotation")) if redundant else None
        est_bits = 4
        zs, zc = (z, n.const(0, z.w, True)) if resid == "carry_save" else (None, None)
        zp, zm = (n.uns(n.mux(n.lt(z, n.const(0, z.w, True)), n.const(0, z.w, True), z)),
                  n.uns(n.trunc(n.mux(n.lt(z, n.const(0, z.w, True)), n.neg(z), n.const(0, z.w, True)), z.w))) if resid == "signed_digit" else (None, None)
        for step, i in enumerate(sched):
            ang = n.const(angles[i], z.w, True)
            zero_sel = est = None
            if mode == "linear":
                sig_pos = n.lt(y, n.const(0, y.w, True)) if vectoring else n.ge(z, n.const(0, z.w, True))
            elif resid == "cpa":
                if redundant and scale_mode == "double_rotation":
                    residual = n.neg(y) if vectoring else z
                    half = n.const(1 << max(0, F - i - 1), residual.w, True)
                    sig_pos = n.ge(residual, half)
                    zero_sel = n.land(n.lt(residual, half), n.gt(residual, n.neg(half)))
                else:
                    sig_pos = n.lt(y, n.const(0, y.w, True)) if vectoring else n.ge(z, n.const(0, z.w, True))
            else:
                # the estimate: a window of the residual (the angle in rotation, y in vectoring) around the
                # angle's weight 2^-i (bit F - i), est_bits below it and three above; the window's sum
                # (carry-save) or difference (signed digit) taken modulo its width reads as the residual's own
                # window (the digits above cancel), within one lsb
                lo = max(0, F - i - est_bits)
                hi = min(z.w - 1, F - i + 3)
                kw_ = hi - lo + 1
                if vectoring:
                    est = n.neg(n.as_signed(n.bits(n.uns(y), hi, lo)))     # one bit wider: -(-2^(kw-1)) stays positive
                elif resid == "carry_save":
                    est = n.as_signed(n.add(n.bits(n.uns(zs), hi, lo), n.bits(n.uns(zc), hi, lo), kw_))
                else:
                    est = n.as_signed(n.sub(n.bits(zp, hi, lo), n.bits(zm, hi, lo), kw_))
                half = n.const(1 << max(0, min(est_bits - 1, kw_ - 2)), kw_, True)
                if scale_mode == "double_rotation":
                    sig_pos = n.ge(est, half)
                    zero_sel = n.land(n.lt(est, half), n.gt(est, n.neg(half)))
                else:
                    sig_pos = n.ge(est, n.const(0, kw_, True))
                    zero_sel = None
            xs, ys = n.shr(x, i) if i else x, n.shr(y, i) if i else y
            if mode == "circular":
                xn_p, xn_m = n.sub(x, ys), n.add(x, ys)
            elif mode == "hyperbolic":
                xn_p, xn_m = n.add(x, ys), n.sub(x, ys)
            else:
                xn_p = xn_m = x
            yn_p, yn_m = n.add(y, xs), n.sub(y, xs)
            if scale_mode == "double_rotation" and zero_sel is not None:
                # two micro-rotations per step: (+, +), (-, -) or (+, -) for sigma = 0, so the scale stays constant
                def rot(xx, yy, plus):
                    xs_, ys_ = (n.shr(xx, i) if i else xx), (n.shr(yy, i) if i else yy)
                    if mode == "circular":
                        xo = n.sub(xx, ys_) if plus else n.add(xx, ys_)
                    else:
                        xo = n.add(xx, ys_) if plus else n.sub(xx, ys_)
                    yo = n.add(yy, xs_) if plus else n.sub(yy, xs_)
                    return xo, yo
                xa, ya = rot(x, y, True)
                xaa, yaa = rot(xa, ya, True)
                xb, yb = rot(x, y, False)
                xbb, ybb = rot(xb, yb, False)
                x0, y0 = rot(xa, ya, False)
                x_new = n.mux(zero_sel, x0, n.mux(sig_pos, xaa, xbb))
                y_new = n.mux(zero_sel, y0, n.mux(sig_pos, yaa, ybb))
                ang = n.shl(ang, 1)
            else:
                x_new, y_new = n.mux(sig_pos, xn_p, xn_m), n.mux(sig_pos, yn_p, yn_m)
            x, y = n.trunc(x_new, z.w + 2) if x_new.w > z.w + 2 else x_new, n.trunc(y_new, z.w + 2) if y_new.w > z.w + 2 else y_new
            self.trace.append((i, x, y, sig_pos, zero_sel, est))
            # the angle accumulator
            if resid == "cpa":
                zn = n.mux(sig_pos, n.sub(z, ang), n.add(z, ang))
                if zero_sel is not None:
                    zn = n.mux(zero_sel, z, zn)
                z = n.trunc(zn, z.w) if zn.w > z.w else zn
            elif resid == "carry_save":
                addend = n.mux(sig_pos, n.neg(ang), ang)
                if zero_sel is not None:
                    addend = n.mux(zero_sel, n.const(0, addend.w, True), addend)
                a_, b_, c_ = n.uns(n.trunc(zs, z.w)), n.uns(n.trunc(zc, z.w)), n.uns(n.trunc(addend, z.w))
                s_ = n.bxor(n.bxor(a_, b_), c_)
                cy = n.bor(n.bor(n.band(a_, b_), n.band(a_, c_)), n.band(b_, c_))
                zs = n.wire(z.w, True, f"$signed({s_.name})", lambda env, s_=s_, w=z.w: _wrap(env[s_.name], w, True), "zs")
                zc = n.wire(z.w, True, f"$signed({{{cy.name}[{z.w-2}:0], 1'b0}})", lambda env, cy=cy, w=z.w: _wrap(env[cy.name] << 1, w, True), "zc")
            else:
                # signed-digit residual: the (plus, minus) pair plus the angle's digits by the carry-free rule
                addend = n.mux(sig_pos, n.neg(ang), ang)
                if zero_sel is not None:
                    addend = n.mux(zero_sel, n.const(0, addend.w, True), addend)
                ap = n.uns(n.mux(n.lt(addend, n.const(0, addend.w, True)), n.const(0, addend.w, True), addend))
                am = n.uns(n.mux(n.lt(addend, n.const(0, addend.w, True)), n.neg(addend), n.const(0, addend.w, True)))
                zp, zm = self._sd_add(n, zp, zm, n.trunc(ap, z.w) if ap.w > z.w else n.ext(ap, z.w), n.trunc(am, z.w) if am.w > z.w else n.ext(am, z.w))
        if resid == "carry_save":
            z = n.trunc(n.add(zs, zc), z.w)                     # the pair was kept modulo 2^w: so is its sum
        elif resid == "signed_digit":
            z = n.trunc(n.sub(n.sgn(zp), n.sgn(zm)), z.w)
        if redundant:
            notes.append(f"redundant residual ({resid}), sigma from a {est_bits}-bit estimate, scale handling {scale_mode}")
        n.algorithm_contracts.append({"kind": "cordic_rotation", "family": self.family,
            "coordinate": mode, "vectoring": bool(vectoring), "residual_arithmetic": resid,
            "scale_handling": scale_mode, "fraction_bits": F, "estimate_bits": est_bits,
            "angle_fraction_bits": angles[0].bit_length() - 1 if mode == "linear" else F,
            "schedule": list(sched), "angles": list(angles),
            "inputs": [value.name for value in inputs], "input_widths": [value.w for value in inputs],
            "input_signed": [value.s for value in inputs], "outputs": [value.name for value in (x, y, z)],
            "output_widths": [value.w for value in (x, y, z)],
            "primitive_assumption": "exact arithmetic components",
            "bound_arithmetic": {kind: {"family": binding[0], "pins": dict(binding[1])} for kind, binding in n.bind.items()}})
        return x, y, z

    def _sd_add(self, n: Net, xp: Ref, xm: Ref, yp: Ref, ym: Ref) -> tuple:
        """The carry-free signed-digit addition of two (plus, minus) pairs (the redundant-binary rule)."""
        w = xp.w
        low_neg = n.bor(n.cat(n.bits(xm, w - 2, 0), n.const(0, 1)), n.cat(n.bits(ym, w - 2, 0), n.const(0, 1)))   # from the position below
        two_p, two_m = n.band(xp, yp), n.band(xm, ym)
        one_p = n.bor(n.band(n.band(xp, n.bnot(yp)), n.bnot(ym)), n.band(n.band(yp, n.bnot(xp)), n.bnot(xm)))
        one_m = n.bor(n.band(n.band(xm, n.bnot(yp)), n.bnot(ym)), n.band(n.band(ym, n.bnot(xp)), n.bnot(xm)))
        cp = n.bor(two_p, n.band(one_p, n.bnot(low_neg)))
        cm = n.bor(two_m, n.band(one_m, low_neg))
        sp = n.band(n.bor(one_p, one_m), low_neg)
        sm = n.band(n.bor(one_p, one_m), n.bnot(low_neg))
        cp_in = n.cat(n.bits(cp, w - 2, 0), n.const(0, 1))
        cm_in = n.cat(n.bits(cm, w - 2, 0), n.const(0, 1))
        zp = n.bor(n.band(sp, n.bnot(cm_in)), n.band(cp_in, n.bnot(sm)))
        zm = n.bor(n.band(sm, n.bnot(cp_in)), n.band(cm_in, n.bnot(sp)))
        return zp, zm

    def build(self, n: Net, core: Core, u: Ref, Fu: int, Fo: int) -> tuple:
        notes = []
        N = self._iters(Fo)
        from chialu.targets.rtl.families.fidelity import effective
        effective(self.pins, "topology", "unrolled_combinational", "a combinational micro-rotation chain")
        F = max(Fo + max(3, N.bit_length() + 2), N + 8)
        W = F + 4
        scale = str(self.P("scale_compensation", "constant_multiplier"))
        coarse = bool(self.P("coarse_fine_hybrid", False)) if self.redundant else False
        with mpmath.workprec(max(PROFILE_BITS, F + 32)):
            atan = [int(mpmath.atan(mpmath.mpf(2) ** -i) * (1 << F) + 0.5) for i in range(N + 2)]
            atanh = [int(mpmath.atanh(mpmath.mpf(2) ** -i) * (1 << F) + 0.5) if i >= 1 else 0 for i in range(N + 2)]
            lin = [(1 << F) >> i for i in range(N + 2)]
            hyp_sched = []
            i, nxt = 1, 4
            while len(hyp_sched) < N:
                hyp_sched.append(i)
                if i == nxt:
                    hyp_sched.append(i)
                    nxt = 3 * nxt + 1
                i += 1
            hyp_sched = hyp_sched[:N]
            Kc = mpmath.fprod(mpmath.sqrt(1 + mpmath.mpf(2) ** (-2 * i)) for i in range(N))
            Kh = mpmath.fprod(mpmath.sqrt(1 - mpmath.mpf(2) ** (-2 * i)) for i in hyp_sched)
        circ_sched = list(range(N))
        double = False
        if self.redundant and str(self.P("scale_handling", "double_rotation")) == "correcting_iterations":
            circ_sched = sorted(circ_sched + [i for i in range(3, N, 4)])
            hyp_sched = sorted(hyp_sched + [i for i in range(3, N, 4)])
        if self.redundant and str(self.P("scale_handling", "double_rotation")) == "double_rotation":
            double = True                                    # every step rotates twice
            circ_sched = list(range(1, N + 1))
        if self.redundant and str(self.P("scale_handling", "double_rotation")) in ("online_scale_computation", "virtually_scaling_free", "differential_constant_scale"):
            raise ValueError(f"CORDIC scale_handling={self.P('scale_handling', '')} has no generator")
        with mpmath.workprec(max(PROFILE_BITS, F + 32)):
            Kc = mpmath.fprod(mpmath.sqrt(1 + mpmath.mpf(2) ** (-2 * i)) for i in circ_sched)
            Kh = mpmath.fprod(mpmath.sqrt(1 - mpmath.mpf(2) ** (-2 * i)) for i in hyp_sched)
            if double:
                Kc, Kh = Kc * Kc, Kh * Kh
        if any(atan[i] == 0 for i in circ_sched) or any(atanh[i] == 0 for i in hyp_sched):
            raise ValueError("CORDIC iteration schedule contains a statically zero angle; increase working precision")
        effective(self.pins, "iterations", N, "nonzero angles and nonempty shift operands in every scheduled iteration",
                  {"fraction_bits": F, "datapath_bits": W, "last_iteration": max(circ_sched + hyp_sched)})
        if self.redundant and int(self.P("radix", 2)) != 2:
            raise ValueError("redundant_high_radix_cordic radix=4 has no generator")

        def init_scale(Kv, mode_name):
            """(x0 value, post factor or None) for the scale compensation."""
            if scale == "none":
                with mpmath.workprec(max(PROFILE_BITS, F + 32)):
                    return int((1 << F) / Kv + mpmath.mpf("0.5")), None
            return 1 << F, Kv

        def apply_scale(xv, Kv):
            with mpmath.workprec(max(PROFILE_BITS, F + 32)):
                inverse = 1 / mpmath.mpf(Kv)
            if scale == "constant_multiplier" or (scale == "none" and False):
                return n.shr(_const_mul(n, xv, inverse, F + 2), F + 2)
            if scale == "scaling_iterations":
                for s, k in self._scale_set(inverse, F):
                    xv = n.add(xv, n.shr(xv, k)) if s > 0 else n.sub(xv, n.shr(xv, k))
                    xv = n.trunc(xv, W + 2) if xv.w > W + 2 else xv
                return xv
            return xv
        Kfix = float(Kc)
        if core.name == "sinc":
            # sin(pi u / 2): a circular rotation by theta = u pi/2 (the coarse-fine hybrid rotates by a table first)
            theta = n.shr(_const_mul(n, u, mpmath.pi / 2, F + 2), Fu + 2)         # F fraction bits
            theta = n.sgn(n.bits(theta, min(theta.w, F + 2) - 1, 0)) if theta.w > F + 2 else n.sgn(theta)
            sched = circ_sched
            cb = 3
            if coarse:
                sched = [i for i in sched if i >= cb - 1]
                with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                    Kc = float(mpmath.fprod(mpmath.sqrt(1 + mpmath.mpf(2) ** (-2 * i)) for i in sched))
                    if double:
                        Kc = Kc * Kc
            x0v, K_post = init_scale(Kc, "circular")
            x = n.const(x0v, W, True)
            y = n.const(0, W, True)
            z = n.ext(theta, W)
            if coarse:
                ci = n.bits(u, Fu - 1, Fu - cb)
                with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
                    cs = [int(mpmath.cos(mpmath.mpf(a) / (1 << cb) * mpmath.pi / 2) * x0v + 0.5) for a in range(1 << cb)]
                    sn = [int(mpmath.sin(mpmath.mpf(a) / (1 << cb) * mpmath.pi / 2) * x0v + 0.5) for a in range(1 << cb)]
                    th = [int(mpmath.mpf(a) / (1 << cb) * mpmath.pi / 2 * (1 << F) + 0.5) for a in range(1 << cb)]
                x = n.rom(cs, ci, W, True); y = n.rom(sn, ci, W, True)
                z = n.sub(n.ext(theta, W), n.ext(n.rom(th, ci, W, True), W), W)
                notes.append(f"coarse-fine hybrid: a {cb}-bit rotation table, then the fine iterations")
            x, y, z = self._rot(n, x, y, z, "circular", N, F, atan, sched, notes)
            if K_post:
                y = apply_scale(y, K_post)
            R = n.uns(n.mux(n.lt(y, n.const(0, y.w, True)), n.const(0, y.w, True), y))
            notes.append(f"circular rotation, {len(sched)} iterations, scale {scale}")
            return _clamp_result(n, n.shr(R, F - Fo), Fo + 1), notes
        if core.name == "exp2c":
            t = n.shr(_const_mul(n, u, mpmath.log(2), F + 2), Fu + 2)              # f ln2 at F bits
            x0v, K_post = init_scale(Kh, "hyperbolic")
            x = n.const(x0v, W, True); y = n.const(0, W, True); z = n.sgn(n.bits(t, min(t.w, F + 1) - 1, 0))
            z = n.ext(z, W)
            x, y, z = self._rot(n, x, y, z, "hyperbolic", N, F, atanh, hyp_sched, notes)
            e = n.add(x, y)
            if K_post:
                e = apply_scale(e, K_post)
            notes.append(f"hyperbolic rotation (cosh + sinh), {len(hyp_sched)} iterations, scale {scale}")
            return _clamp_result(n, n.shr(e, F - Fo), Fo + 1), notes
        if core.name == "log2c":
            # ln(m') = 2 atanh((m' - 1) / (m' + 1)) by hyperbolic vectoring on x0 = m' + 1, y0 = m' - 1
            d = n.sub(n.sgn(u), n.const(1 << (Fu - 2), Fu + 1, True))
            dF = n.shl(d, F - Fu) if F > Fu else n.shr(d, Fu - F)
            # x0 = 1 + d/2, y0 = d/2 (the ratio d / (2 + d) unchanged, x near one for the direction estimate)
            x = n.add(n.const(1 << F, W, True), n.ext(n.shr(dF, 1), W), W)
            y = n.ext(n.shr(dF, 1), W)
            z = n.const(0, W, True)
            x, y, z = self._rot(n, x, y, z, "hyperbolic", N, F, atanh, hyp_sched, notes, vectoring=True)
            L = n.shr(_const_mul(n, n.shl(z, 1), 1 / mpmath.log(2), F + 2), F + 2)
            notes.append(f"hyperbolic vectoring (atanh), {len(hyp_sched)} iterations")
            return n.shr(L, F - Fo), notes
        if core.name == "recipc":
            # 1 / (1 + u) by linear vectoring: z += sigma 2^-i, y -= sigma x 2^-i
            m = n.add(n.const(1 << F, W, True), n.ext(n.shl(u, F - Fu) if F > Fu else n.shr(u, Fu - F), W), W)
            x, y, z = m, n.const(1 << F, W, True), n.const(0, W, True)
            x, y, z = self._rot(n, x, y, z, "linear", N, F, lin, list(range(1, N + 1)), notes, vectoring=True)
            notes.append(f"linear vectoring (division), {N} iterations")
            return _clamp_result(n, n.shr(z, F - Fo), Fo + 1), notes
        if core.name in ("sqrtc", "rsqrtc"):
            # sqrt(m) = K_h^-1 sqrt((m + 1/4)^2 - (m - 1/4)^2) by hyperbolic vectoring; m in [1, 2) (twice for m in [2, 4))
            ub = u.w
            hi_bit = n.bit(u, ub - 1)
            frac = n.bits(u, ub - 2, 0)
            mF = n.add(n.const(1 << F, W, True), n.ext(n.shl(frac, F - Fu) if F > Fu else frac, W), W)     # 1 + frac
            q = n.const(1 << (F - 2), W, True)
            # x0 = (m + 1/4) / 2, y0 = (m - 1/4) / 2: sqrt(x0^2 - y0^2) = sqrt(m) / 2, x near one for the estimate
            x = n.shr(n.add(mF, q, W + 1), 1); y = n.shr(n.sub(mF, q, W + 1), 1); z = n.const(0, W, True)
            x, y, z = self._rot(n, x, y, z, "hyperbolic", N, F, atanh, hyp_sched, notes, vectoring=True)
            r = n.shr(_const_mul(n, n.shl(x, 1), 1 / mpmath.mpf(Kh), F + 2), F + 2)   # sqrt(1 + frac)
            r = n.mux(hi_bit, n.shr(_const_mul(n, r, mpmath.sqrt(2), F + 2), F + 2), n.ext(r, r.w + 2))   # sqrt(2 (1 + frac)) for the upper half
            if core.name == "sqrtc":
                notes.append(f"hyperbolic vectoring (root), {len(hyp_sched)} iterations")
                return _clamp_result(n, n.shr(r, F - Fo), Fo + core.ibits()), notes
            # 1 / sqrt: a linear vectoring division after the root
            rW = n.ext(r, W + 2) if r.w < W + 2 else n.trunc(r, W + 2)
            x2, y2, z2 = rW, n.const(1 << F, W + 2, True), n.const(0, W + 2, True)
            x2, y2, z2 = self._rot(n, x2, y2, z2, "linear", N, F, lin, list(range(1, N + 1)), notes, vectoring=True)
            notes.append(f"hyperbolic vectoring (root) then linear vectoring (reciprocal), {len(hyp_sched)} + {N} iterations")
            return _clamp_result(n, n.shr(z2, F - Fo), Fo + core.ibits()), notes
        # tanh(T u), direct: e^(2t) by hyperbolic rotation over its fraction, then (E - 1)/(E + 1) by linear vectoring
        Tk = int(round(math.log2(core.T)))
        y2 = n.shl(u, Tk + 1)                                                    # 2 T u with Fu fraction bits (Tk+1 integer bits)
        y2 = n.uns(y2)
        yl = n.shr(_const_mul(n, y2, 1 / mpmath.log(2), F + 2), Fu + 2)         # 2 T u log2 e at F bits
        nn = n.bits(yl, yl.w - 1, F) if yl.w > F else n.const(0, 1)
        fl = n.bits(yl, F - 1, 0)
        t = n.shr(_const_mul(n, fl, mpmath.log(2), F + 2), F + 2)
        x0v, K_post = init_scale(Kh, "hyperbolic")
        x = n.const(x0v, W, True); yy = n.const(0, W, True); z = n.ext(n.sgn(t), W)
        x, yy, z = self._rot(n, x, yy, z, "hyperbolic", N, F, atanh, hyp_sched, notes)
        c = n.add(x, yy)
        if K_post:
            c = apply_scale(c, K_post)
        # E = c 2^nn: nn up to 2 T log2e + 1; the ratio (E - 1)/(E + 1) = 1 - 2/(E + 1): E + 1 big -> 1
        nmax = int(2 * (1 << Tk) * 1.45) + 2
        Wd = F + nmax + 3
        E = n.shlv(n.ext(n.uns(n.trunc(c, F + 2)), Wd), n.bits(nn, min(nn.w, nmax.bit_length()) - 1, 0) if nn.w > 1 else nn, Wd)
        den = n.add(E, n.const(1 << F, Wd), Wd + 1)
        num = n.sub(n.sgn(E), n.const(1 << F, Wd + 1, True))
        # normalize the denominator and the numerator each to its leading one at the same bit (the numerator
        # then halved, so the ratio the linear vectoring resolves stays below one), the quotient's exponent
        # from the difference of the two leading-zero counts: a small tanh keeps its relative precision
        W2 = max(den.w, num.w) + 1
        den2 = n.ext(den, W2)
        nabs = n.uns(n.trunc(n.mux(n.lt(num, n.const(0, num.w, True)), n.const(0, num.w, True), num), num.w))
        nabs2 = n.ext(nabs, W2)
        lz = n.lzc(den2)
        lzn = n.lzc(nabs2)
        dn_ = n.shlv(den2, lz, W2)                                              # the leading one at W2-1
        nm_ = n.shlv(nabs2, lzn, W2)
        xv = n.sgn(dn_)
        yv = n.sgn(n.shr(nm_, 1))
        zv = n.const(0, xv.w, True)
        Fz = W2 - 2
        xv, yv, zv = self._rot(n, xv, yv, zv, "linear", N, F, [(1 << Fz) >> i for i in range(N + 2)], list(range(1, N + 1)), notes, vectoring=True)
        zq = n.uns(n.mux(n.lt(zv, n.const(0, zv.w, True)), n.const(0, zv.w, True), zv))
        Rw = n.shr(zq, Fz - Fo - 1) if Fz - Fo - 1 > 0 else n.shl(zq, Fo + 1 - Fz)      # 2 z at Fo bits (the halved numerator)
        sh = n.uns(n.trunc(n.sub(n.ext(lzn, lzn.w + 2), n.ext(lz, lzn.w + 2), lzn.w + 2), lzn.w + 1))
        R = n.shrv(Rw, sh)
        notes.append(f"tanh by a hyperbolic rotation (e^2t) and a linear vectoring division, {len(hyp_sched)} + {N} iterations")
        return _clamp_result(n, R, Fo + 1), notes


def _bkm_leading_count(n, magnitude):
    """Keep the native LZC tree, emitting its definition once per binding/width."""
    if n._bound("lzc", magnitude.w):
        return n.lzc(magnitude)
    import hashlib
    import json
    from chialu.targets.rtl import families as FAM
    tag = hashlib.sha256(json.dumps(n.bind, sort_keys=True, default=str).encode()).hexdigest()[:12]
    name = f"bkm_native_lzc_w{magnitude.w}_{tag}"
    # Build on every call so selected descendant factories and ownership
    # audits still run. Net.inst deduplicates only immutable module text.
    local = Net(name, "the unchanged native recursive-doubling LZC", bind=n.bind)
    argument = local.port_in("a", magnitude.w)
    count = local.lzc(argument)
    local.port_out("n", count)
    module = FAM.Module(name, {}, local.render())
    result = n.declare(count.w, False,
        lambda env, magnitude=magnitude: magnitude.w - (env[magnitude.name] & ((1 << magnitude.w) - 1)).bit_length(), "bkm_lzc")
    n.inst(module, {"a": magnitude.name, "n": result.name}, "native recursive LZC with an independent physical instance")
    n._use("lzc", module)
    for kind, uses in local.lib_uses.items():
        n.lib_uses[kind] = n.lib_uses.get(kind, 0) + uses
    return result


def _bkm_first_nonzero(n, residual, fraction, iterations, coordinate, bank_prefix=None, radix=2):
    """One component's first nonzero prefix digit: LZC plus three exact thresholds."""
    if coordinate not in ("real", "imag") or not residual.s:
        raise ValueError("BKM index selection needs a signed real/imaginary residual")
    if radix not in (2, 4):
        raise ValueError("unsupported BKM index radix")
    rb = radix.bit_length() - 1
    one = 1 << fraction
    negative = n.lt(residual, n.const(0, residual.w, True))
    # Unsigned magnitude also represents abs(the most negative signed word).
    magnitude = n.uns(n.mux(negative, n.neg(residual), residual))
    leading = _bkm_leading_count(n, magnitude)
    iw = max(leading.w, (iterations + 3).bit_length())
    leading = n.ext(leading, iw) if leading.w < iw else leading
    offset = magnitude.w - fraction + 1
    raw = n.sub(leading, n.const(offset, iw), iw)
    base = n.mux(n.le(leading, n.const(offset, iw)), n.const(1, iw), raw)
    if rb == 2:
        base = n.shr(n.add(base, n.const(1, iw)), 1)
    base = n.mux(n.gt(base, n.const(iterations + 1, iw)), n.const(iterations + 1, iw), base)
    positives, negatives = [0], [0]
    for index in range(1, iterations + 1):
        scale = radix ** index
        if radix == 4:
            positives.append(-(-one // (2 * scale)))
            negatives.append(one // (2 * scale) + 1)
            continue
        positives.append(-(-(3 * one) // (8 * scale)) if coordinate == "real" else -(-(13 * one) // (16 * scale)))
        negatives.append(one // (2 * scale) + 1 if coordinate == "real" else (3 * one) // (4 * scale) + 1)
    first = n.const(iterations + 1, iw)
    for delta in (2, 1, 0):
        candidate = n.add(base, n.const(delta, iw), iw) if delta else base
        threshold = n.mux(negative,
            n.rom(negatives, candidate, magnitude.w, bank=f"{bank_prefix}_zero_{coordinate}_neg" if bank_prefix else None),
            n.rom(positives, candidate, magnitude.w, bank=f"{bank_prefix}_zero_{coordinate}_pos" if bank_prefix else None))
        take = n.land(n.le(candidate, n.const(iterations, iw)), n.ge(magnitude, threshold))
        first = n.mux(take, candidate, first)
    return first


def _bkm_prefix_digit(n, residual, index, fraction, iterations, coordinate, bank_prefix=None, radix=2, shift=None):
    """The original clipped-prefix selector, with either a static or live index."""
    if coordinate not in ("real", "imag"):
        raise ValueError("unknown BKM prefix coordinate")
    if radix not in (2, 4):
        raise ValueError("unsupported BKM prefix radix")
    rb = radix.bit_length() - 1
    fractional, negative, positive = (3, -5, 3) if coordinate == "real" else (4, -13, 13)
    if isinstance(index, Ref):
        # index<=iterations+1. This width preserves the entire signed shift
        # before the fixed binary-point truncation and prefix saturation.
        amount = shift if shift is not None else (n.shl(index, 1) if rb == 2 else index)
        shifted = n.shlv(residual, amount, residual.w + rb * (iterations + 1))
        prefix = n.shr(shifted, fraction - fractional)
    else:
        remaining = fraction - rb * index - fractional
        prefix = n.shr(residual, remaining) if remaining > 0 else n.shl(residual, -remaining)
    bits = fractional + 2
    lower, upper = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    prefix = n.mux(n.lt(prefix, n.const(lower, prefix.w, True)), n.const(lower, prefix.w, True), prefix)
    prefix = n.mux(n.gt(prefix, n.const(upper, prefix.w, True)), n.const(upper, prefix.w, True), prefix)
    address = n.uns(n.trunc(prefix, bits)) if prefix.w > bits else n.uns(n.ext(prefix, bits))
    if radix == 4:
        table = [max(-2, min(2, (_wrap(raw, bits, True) + (1 << (fractional - 1))) >> fractional)) for raw in range(1 << bits)]
        return n.rom(table, address, 3, True, bank=f"{bank_prefix}_prefix_{coordinate}" if bank_prefix else None)
    table = [-1 if _wrap(raw, bits, True) <= negative else 1 if _wrap(raw, bits, True) >= positive else 0
             for raw in range(1 << bits)]
    return n.rom(table, address, 2, True, bank=f"{bank_prefix}_prefix_{coordinate}" if bank_prefix else None)


# ---- digit recurrence (exp/log by normalization), unrolled ---------------------------------------
class DigitRecEngine(_Engine):
    covers = {"exp2c", "log2c"}
    direct = {"log2c"}

    def __init__(self, family, pins):
        super().__init__(family, pins)
        self.paired_sincos = str(self.P("state_domain", "real")) == "complex_bkm"
        if self.paired_sincos:
            self.covers, self.direct = {"sinc"}, {"sinc"}

    def complex_build(self, n, core, u, Fu, Fo, radix, digits, selection, term, advance, normalization):
        """BKM E-mode on a quarter angle, followed by two complex squarings."""
        if core.name != "sinc":
            raise ValueError("complex_bkm currently implements the sine/cosine E-mode pair")
        if digits != "signed_redundant":
            raise ValueError("scale-free complex BKM on the unit circle needs signed real correction digits; "
                             "nonnegative real/imaginary digits cannot cancel the magnitude gain")
        if radix not in (2, 4):
            raise ValueError("complex BKM radix-16 selection and convergence contract is not implemented")
        if selection != "table_lookup":
            raise ValueError("complex BKM rounded selection is not implemented; the published prefix selector uses a table")
        if advance not in ("sequential", "leading_bit_skip"):
            raise ValueError("unknown complex BKM index advancement")
        skipping = advance == "leading_bit_skip"
        if u.w != Fu:
            raise ValueError("the complex BKM sine/cosine core requires an unsigned argument in [0,1)")
        F, W = Fo + 10, Fo + 14
        rb = radix.bit_length() - 1
        alpha, dw = (1, 2) if radix == 2 else (2, 3)
        full = (F + rb - 1) // rb
        N = full if term == "iterate_to_full_precision" else (full + 1) // 2 + 1
        additive = normalization == "additive"
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get(), 2 * F + 32)):
            nearest = lambda value: int(mpmath.floor(value + mpmath.mpf("0.5")))
            pi_eighth = nearest((mpmath.pi / 8) * (1 << (F + 4)))
            real_tables, imag_tables = [], []
            for index in range(1, N + 1):
                real_row, imag_row = [], []
                step = mpmath.mpf(radix) ** -index
                for raw in range(1 << (2 * dw)):
                    dx, dy = _wrap(raw >> dw, dw, True), _wrap(raw & ((1 << dw) - 1), dw, True)
                    if not -alpha <= dx <= alpha or not -alpha <= dy <= alpha:
                        real_row.append(0); imag_row.append(0)
                        continue
                    a, b = 1 + dx * step, dy * step
                    real_row.append(nearest(mpmath.log(a * a + b * b) * (1 << F) / 2))
                    imag_row.append(nearest(mpmath.atan(b / a) * (1 << F)))
                real_tables.append(real_row); imag_tables.append(imag_row)
        x = n.const(0 if additive else 1 << F, W, True)
        y = n.const(0, W, True)
        er = n.const(0, W, True)
        ei = n.ext(n.sgn(n.shr(n.mul(u, n.const(pi_eighth, pi_eighth.bit_length())), Fu + 4)), W)
        states, digit_pairs, schedule = [], [], []
        def snapshot(label):
            states.append({"label": label, "signals": [value.name for value in (x, y, er, ei)],
                           "widths": [value.w for value in (x, y, er, ei)]})
        snapshot("initial")
        # Read-only data are stored once per core, with independent live
        # read ports at every slot. The invocation ordinal is unique within
        # a Net and stable across functions, so requested inter-function
        # sharing can identify compatible bank roles without conflating cores.
        bank_scope = f"bkm_core{len(n.algorithm_contracts)}" if skipping else None
        following = n.const(1, (N + 3).bit_length()) if skipping else None
        for physical in range(1, N + 1):
            if skipping:
                real_first = _bkm_first_nonzero(n, er, F, N, "real", bank_scope, radix)
                imag_first = _bkm_first_nonzero(n, ei, F, N, "imag", bank_scope, radix)
                first = n.mux(n.lt(real_first, imag_first), real_first, imag_first)
                index = n.mux(n.lt(first, following), following, first)
                active = n.le(index, n.const(N, index.w))
                previous_following = following
                following = n.mux(active, n.add(index, n.const(1, index.w), index.w), index)
                amount = n.shl(index, 1) if rb == 2 else index
                schedule.append({"slot": physical,
                    "signals": [real_first.name, imag_first.name, first.name, previous_following.name, index.name, following.name, amount.name],
                    "widths": [real_first.w, imag_first.w, first.w, previous_following.w, index.w, following.w, amount.w]})
            else:
                index = physical
                amount = rb * index
            dx, dy = _bkm_prefix_digit(n, er, index, F, N, "real", bank_scope, radix, amount), _bkm_prefix_digit(n, ei, index, F, N, "imag", bank_scope, radix, amount)
            if skipping:
                dx = n.mux(active, dx, n.const(0, dw, True))
                dy = n.mux(active, dy, n.const(0, dw, True))
                digit_pairs.append({"slot": physical, "signals": [dx.name, dy.name]})
            else:
                digit_pairs.append({"index": index, "signals": [dx.name, dy.name]})
            address = n.cat(n.uns(dx), n.uns(dy))
            if skipping:
                address = n.cat(index, address)
                cr = n.rom([0] * (1 << (2 * dw)) + [value for row in real_tables for value in row], address, W, True, bank=f"{bank_scope}_real_factors")
                ci = n.rom([0] * (1 << (2 * dw)) + [value for row in imag_tables for value in row], address, W, True, bank=f"{bank_scope}_imag_factors")
            else:
                cr = n.rom(real_tables[index - 1], address, W, True)
                ci = n.rom(imag_tables[index - 1], address, W, True)
            correction_x = n.sub(n.mul(x, dx), n.mul(y, dy))
            correction_y = n.add(n.mul(y, dx), n.mul(x, dy))
            if additive:
                correction_x = n.add(correction_x, n.shl(dx, F))
                correction_y = n.add(correction_y, n.shl(dy, F))
            if skipping:
                x, y = n.mux(active, n.add(x, n.shrv(correction_x, amount), W), x), n.mux(active, n.add(y, n.shrv(correction_y, amount), W), y)
                er, ei = n.mux(active, n.sub(er, cr, W), er), n.mux(active, n.sub(ei, ci, W), ei)
            else:
                x, y = n.add(x, n.shr(correction_x, amount), W), n.add(y, n.shr(correction_y, amount), W)
                er, ei = n.sub(er, cr, W), n.sub(ei, ci, W)
            snapshot(f"slot_{physical}" if skipping else f"iteration_{index}")
        if term == "linear_extrapolation":
            correction_x = n.sub(n.mul(x, er), n.mul(y, ei))
            correction_y = n.add(n.mul(y, er), n.mul(x, ei))
            if additive:
                correction_x = n.add(correction_x, n.shl(er, F))
                correction_y = n.add(correction_y, n.shl(ei, F))
            x, y = n.add(x, n.shr(correction_x, F), W), n.add(y, n.shr(correction_y, F), W)
        snapshot("tail")
        if additive:
            x = n.add(x, n.const(1 << F, W, True), W)
        snapshot("one_centered_output")
        for index in (1, 2):
            real_product = n.sub(n.mul(x, x), n.mul(y, y))
            imag_product = n.shl(n.mul(x, y), 1)
            x, y = n.trunc(n.shr(real_product, F), W), n.trunc(n.shr(imag_product, F), W)
            snapshot(f"square_{index}")
        sine = _clamp_result(n, n.shr(y, F - Fo), Fo + 1)
        cosine = _clamp_result(n, n.shr(x, F - Fo), Fo + 1)
        n.algorithm_contracts.append({"kind": "complex_bkm_e", "family": self.family, "core": "sincos_pair",
            "state_domain": "complex_bkm", "radix": radix, "digit_set": digits, "selection": selection,
            "index_advance": advance, "normalization": normalization, "termination": term,
            "input": u.name, "input_width": u.w, "input_fraction_bits": Fu,
            "fraction_bits": F, "state_width": W, "output_fraction_bits": Fo, "iterations": N,
            "pi_eighth": pi_eighth, "pi_eighth_fraction_bits": F + 4, "angle_divisor": 4,
            "real_log_factors": real_tables, "imag_log_factors": imag_tables,
            "states": states, "digits": digit_pairs,
            "outputs": {"sin": {"signal": sine.name, "width": sine.w}, "cos": {"signal": cosine.name, "width": cosine.w}},
            "source": "Bajard, Kla and Muller BKM E-mode, nine signed complex digits; prefix selection p_real=3,p_imag=4",
            "primitive_assumption": "exact integer arithmetic; approximate children require a composed contract"})
        if radix == 4:
            n.algorithm_contracts[-1].update(algorithm_version="complex_bkm_r4_nearest_rom_v1", digit_min=-2, digit_max=2,
                digit_width=3, radix_bits=2, selector_contract="nearest signed digit from actual clipped-prefix ROMs",
                source="project radix-4 BKM E-mode completion: 25 signed complex factors and nearest-prefix lookup")
        if skipping:
            n.algorithm_contracts[-1].update(schedule_version="complex_bkm_zero_skip_v1" if radix == 2 else "complex_bkm_zero_skip_r4_v1", physical_stages=N,
                terminal_index=N + 1, schedule=schedule,
                schedule_fields=["real_first", "imag_first", "first_nonzero", "following_before", "index", "following_after", "shift"],
                omission_rule="both prefix digits must be zero; min(component first indices), max(following)")
        from chialu.targets.rtl.families.fidelity import effective
        effective(self.pins, "state_domain", "complex_bkm", "coupled complex E-mode states and two complex squarings")
        effective(self.pins, "radix", radix, "binary complex factors" if radix == 2 else "true 4^-index complex factors with two-bit shift stride", {"iterations": N, "fraction_bits": F})
        effective(self.pins, "digit_set", "signed_redundant", "each real and imaginary digit is in {-1,0,1}" if radix == 2 else "each real and imaginary digit is in {-2,-1,0,1,2}")
        effective(self.pins, "selection", "table_lookup", "published real/imaginary prefix selector tables" if radix == 2 else "nearest signed digit implemented by actual prefix ROMs")
        effective(self.pins, "index_advance", advance,
                  "two real LZCs, three-cell threshold correction, variable factor ROM address and complex-product shifts"
                  if skipping else ("successive binary complex factors" if radix == 2 else "successive radix-4 complex factors"))
        effective(self.pins, "normalization", normalization, "complex delta and separate digit biases" if additive else "one-centered complex product")
        effective(self.pins, "termination", term, "full E-mode or a shorter E-mode with complex linear residual correction")
        if radix == 4:
            return (sine, cosine), [f"complex BKM radix4 E-mode: {N} 4^-index factors on pi*u/8, 25 complex digits, two complex squarings; {normalization} states; {advance}"]
        return (sine, cosine), [f"complex BKM E-mode: {N} binary iterations on pi*u/8, two complex squarings; {normalization} states"
                                + ("; simultaneous-zero leading-bit advancement" if skipping else "")]

    def build(self, n: Net, core: Core, u: Ref, Fu: int, Fo: int) -> tuple:
        notes = []
        radix = int(self.P("radix", 2))
        digits = str(self.P("digit_set", "nonredundant"))
        selection = str(self.P("selection", "table_lookup"))
        term = str(self.P("termination", "iterate_to_full_precision"))
        advance = str(self.P("index_advance", "sequential"))
        normalization = str(self.P("normalization", "multiplicative"))
        if normalization not in ("multiplicative", "additive"):
            raise ValueError("unknown digit-recurrence normalization")
        additive = normalization == "additive"
        if radix not in (2, 4, 16):
            raise ValueError("digit_recurrence_exp_log radix must be 2, 4, or 16")
        if digits not in ("nonredundant", "signed_redundant") or \
                selection not in ("table_lookup", "rounding_of_scaled_residual") or \
                term not in ("iterate_to_full_precision", "linear_extrapolation"):
            raise ValueError("unknown digit-recurrence digit set, selection, or termination")
        state_domain = str(self.P("state_domain", "real"))
        if state_domain == "complex_bkm":
            return self.complex_build(n, core, u, Fu, Fo, radix, digits, selection, term, advance, normalization)
        if state_domain != "real":
            raise ValueError("unknown digit-recurrence state domain")
        if advance not in ("sequential", "leading_bit_skip"):
            raise ValueError(f"unknown digit-recurrence index_advance={advance}")
        rb = max(1, radix.bit_length() - 1)
        F = Fo + 6
        Ntot = -(-(F) // rb)
        N = Ntot if term == "iterate_to_full_precision" else (Ntot + 1) // 2 + 1
        exponential = core.name == "exp2c"
        bootstrap = digits == "signed_redundant" and radix == 16
        if selection == "rounding_of_scaled_residual" and N < 3:
            raise ValueError(f"{core.name} rounded selection needs at least three main indices; increase output fraction bits to 3")
        physical_stages = N + int(bootstrap)
        dmax = 1 if digits == "nonredundant" and radix == 2 else (radix - 1 if digits == "nonredundant" else radix // 2 if radix > 2 else 1)
        dset = list(range(0, dmax + 1)) if digits == "nonredundant" else list(range(-dmax, dmax + 1))
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            lnT = {(i, d): int(mpmath.floor(mpmath.log(1 + mpmath.mpf(d) * mpmath.mpf(radix) ** -i) * (1 << F) + mpmath.mpf("0.5"))) if 1 + d * radix ** -i > 0 else 0
                   for i in range(1, N + 1) for d in dset}
            ln2 = int(mpmath.floor(mpmath.log(2) * (1 << (F + 2)) + mpmath.mpf("0.5")))
            inv_ln2 = int(mpmath.floor((1 << (F + 2)) / mpmath.log(2) + mpmath.mpf("0.5")))
        if exponential and term == "linear_extrapolation" and N == Ntot:
            # This only occurs at F<=12. Exhaust every integer initial log
            # residual (a superset of every input geometry), using the live
            # quantized factors, to prove whether the unshortened tail is
            # identically zero. Never infer inactivity from sampled inputs.
            extent = -(-ln2 // (4 if digits == "nonredundant" else 8))
            residuals = range(0 if digits == "nonredundant" else -extent, extent)
            schedule = ([1] if bootstrap else []) + list(range(1, N + 1))
            terminal = set()
            for initial in residuals:
                residual = initial
                for index in schedule:
                    if selection == "table_lookup" or index <= 2:
                        if digits == "nonredundant":
                            digit = max(d for d in dset if lnT[index, d] <= residual)
                        else:
                            digit = dset[0]
                            for d in dset[1:]:
                                if 2 * residual >= lnT[index, d - 1] + lnT[index, d]:
                                    digit = d
                    else:
                        digit = max(dset[0], min(dset[-1], (2 * residual * radix ** index + (1 << F)) // (2 << F)))
                        if digits == "nonredundant" and lnT[index, digit] > residual:
                            digit -= 1
                    residual -= lnT[index, digit]
                terminal.add(residual)
            if terminal == {0}:
                minimum = max(0, 3 * rb - 5)
                raise ValueError(f"linear_extrapolation has an identically zero tail and no shorter schedule at Fo={Fo}; "
                                 f"radix {radix} needs at least {minimum} output fraction bits to activate this termination")
        digit_refs = []
        index_refs = []
        shift_refs = []
        state_refs = []
        residual_refs = []
        accumulator_refs = []
        correction_products = []
        manifest = {"kind": "digit_recurrence", "family": self.family, "core": core.name,
                    "input": u.name, "input_width": u.w, "input_fraction_bits": Fu,
                    "domain_lo": int(core.lo * (1 << Fu)),
                    "domain_hi_exclusive": min(1 << u.w, int(core.hi * (1 << Fu))),
                    "output_fraction_bits": Fo, "working_fraction_bits": F,
                    "radix": radix, "digit_set": digits, "selection": selection,
                    "termination": term, "index_advance": advance, "normalization": normalization,
                    "stages": physical_stages, "digit_min": min(dset), "digit_max": max(dset),
                    "ln2": ln2, "inv_ln2": inv_ln2,
                    "coefficient_source": "mpmath log factors, nearest integer; independently recomputed by the reference",
                    "primitive_assumption": "exact integer primitives; approximate children need a composed contract",
                    "bound_arithmetic": {kind: {"family": value[0], "pins": dict(value[1])} for kind, value in n.bind.items()}}
        if exponential:
            manifest.update(initial_range_convention="exp2_convergent_start_v1", main_stages=N,
                            bootstrap_indices=[1] if bootstrap else [], startup_table_through_index=2,
                            sequential_indices=([1] if bootstrap else []) + list(range(1, N + 1)),
                            initial_product="upper_half_two_lower_half_one" if digits == "signed_redundant" else "one",
                            minimum_active_output_fraction_bits=max(3 if radix == 16 and selection == "rounding_of_scaled_residual" else 0,
                                max(0, 3 * rb - 5) if term == "linear_extrapolation" else 0))
        else:
            manifest.update(initial_range_convention="log2_convergent_start_v1", main_stages=N,
                            bootstrap_indices=[1] if bootstrap else [], startup_table_through_index=2,
                            sequential_indices=([1] if bootstrap else []) + list(range(1, N + 1)),
                            initial_product="centered_significand_fold_above_one" if digits == "nonredundant" else "centered_significand",
                            minimum_active_output_fraction_bits=3 if radix == 16 and selection == "rounding_of_scaled_residual" else 0)
        def finish(result, constants):
            manifest.update(output=result.name, output_width=result.w, output_signed=result.s,
                            log_factors=[[constants[i, d] for d in dset] for i in range(1, N + 1)],
                            digit_signals=[r.name for r in digit_refs],
                            digit_widths=[r.w for r in digit_refs], digit_signed=[r.s for r in digit_refs],
                            index_signals=[r.name for r in index_refs], index_widths=[r.w for r in index_refs],
                            shift_signals=[r.name for r in shift_refs], shift_widths=[r.w for r in shift_refs],
                            state_signals=[r.name for r in state_refs], state_widths=[r.w for r in state_refs],
                            state_signed=[r.s for r in state_refs],
                            state_origin="zero_centered_delta" if additive else "one_centered_value",
                            correction_products=correction_products)
            if residual_refs:
                manifest.update(residual_signals=[r.name for r in residual_refs],
                                residual_widths=[r.w for r in residual_refs], residual_signed=[r.s for r in residual_refs])
            if accumulator_refs:
                manifest.update(accumulator_signals=[r.name for r in accumulator_refs],
                                accumulator_widths=[r.w for r in accumulator_refs], accumulator_signed=[r.s for r in accumulator_refs])
            n.algorithm_contracts.append(manifest)
            from chialu.targets.rtl.families.fidelity import effective
            effective(self.pins, "digit_set", digits, "live digit selector and factor-table domain",
                      {"minimum_digit": min(dset), "maximum_digit": max(dset)})
            effective(self.pins, "selection", selection, "factor thresholds or rounded residual (indices 1 and 2 use table startup), with nonredundant safety correction")
            effective(self.pins, "termination", term, "full recurrence or shorter recurrence with a final linear correction",
                      {"stages": N, "working_fraction_bits": F})
            effective(self.pins, "radix", radix, "radix-dependent factors and index advance", {"stages": N})
            effective(self.pins, "normalization", normalization,
                      "zero-centered state times digit plus a separate digit bias; no one-centered state inside the recurrence"
                      if additive else "one-centered state times the selected normalization factor")
            effective(self.pins, "index_advance", advance,
                      "leading-zero detector, adjacent-threshold correction, variable ROM address and barrel shift"
                      if advance == "leading_bit_skip" else "successive constant recurrence indices",
                      {"physical_stages": physical_stages, "terminal_index": N + 1})
            return result, notes
        def round_scaled(value, shift):
            remaining = F - shift
            if remaining > 0:
                return n.shr(n.add(value, n.const(1 << (remaining - 1), value.w, True)), remaining)
            return n.shl(value, -remaining)
        def additive_update(state, digit, shift):
            # The multiplier consumes the stored delta. The digit bias is
            # a separate operand, combined before the one quantization.
            product = n.mul(state, digit)
            bias = n.shl(n.sgn(digit), F)
            correction = n.add(product, bias)
            increment = n.shrv(correction, shift) if isinstance(shift, Ref) else n.shr(correction, shift)
            result = n.add(state, increment, state.w)
            correction_products.append({"state": state.name, "digit": digit.name, "product": product.name,
                                        "bias": bias.name, "correction": correction.name, "result": result.name})
            return result
        iw = (F + 2).bit_length()
        next_index = n.const(1, iw) if advance == "leading_bit_skip" else None
        def skip_index(magnitude, following, thresholds):
            # For 2^k <= magnitude < 2^(k+1), the first admissible
            # radix factor is at j=ceil((F-k)/rb) or j-1. Both
            # ln(1+radix^-i) and ceil(2^F/(radix^i+1)) bracket it.
            # An exact adjacent comparison resolves it. Earlier indices
            # are therefore zero digits, with no residual/state update.
            leading = n.lzc(n.uns(magnitude))
            leading = n.ext(leading, iw) if leading.w < iw else leading
            candidate = n.sub(leading, n.const(magnitude.w - F - 1, leading.w), leading.w)
            if rb > 1:
                candidate = n.shr(n.add(candidate, n.const(rb - 1, candidate.w)), rb.bit_length() - 1)
            candidate = n.mux(n.gt(candidate, n.const(N + 1, candidate.w)),
                              n.const(N + 1, candidate.w), candidate)
            previous = n.sub(candidate, n.const(1, candidate.w), candidate.w)
            boundary = n.rom([0] + thresholds, previous, F + 3)
            earlier = n.land(n.gt(candidate, n.const(1, candidate.w)), n.ge(magnitude, boundary))
            candidate = n.mux(earlier, previous, candidate)
            current = n.rom([0] + thresholds, candidate, F + 3)
            # Zero exp residual can still select a nonzero digit when a
            # partial final radix stage has quantized log factors of zero.
            # Zero log gap cannot select any positive digit (threshold>=1).
            candidate = n.mux(n.ge(magnitude, current), candidate, n.const(N + 1, candidate.w))
            index = n.mux(n.lt(candidate, following), following, candidate)
            active = n.le(index, n.const(N, index.w))
            following = n.mux(active, n.add(index, n.const(1, index.w), index.w), index)
            index_refs.append(index)
            return index, active, following
        def signed_skip_index(residual, following, constants, logarithm=False):
            negative = n.lt(residual, n.const(0, residual.w, True))
            magnitude = n.mux(negative, n.neg(residual), residual)
            leading = n.lzc(n.uns(magnitude))
            leading = n.ext(leading, iw) if leading.w < iw else leading
            # A signed digit first becomes nonzero near half a radix step.
            # The leading bit brackets it within the preceding/current/
            # following radix index; exact sign-dependent thresholds
            # resolve the nonlinear factors and the asymmetric ties.
            candidate = n.sub(leading, n.const(magnitude.w - F, leading.w), leading.w)
            candidate = n.mux(n.lt(candidate, n.const(1, candidate.w)), n.const(1, candidate.w), candidate)
            if rb > 1:
                candidate = n.shr(n.add(candidate, n.const(rb - 1, candidate.w)), rb.bit_length() - 1)
            candidate = n.mux(n.gt(candidate, n.const(N + 1, candidate.w)), n.const(N + 1, candidate.w), candidate)
            if selection == "rounding_of_scaled_residual":
                positives = [0] + [max(1, -(-(1 << F) // (2 * radix ** j))) for j in range(1, N + 1)]
                negatives = [0] + [(1 << F) // (2 * radix ** j) + 1 for j in range(1, N + 1)]
            elif logarithm:
                positives = [0] + [(1 << F) // (2 * radix ** j + 1) + 1 for j in range(1, N + 1)]
                negatives = [0] + [-(-(1 << F) // (2 * radix ** j - 1)) for j in range(1, N + 1)]
            else:
                positives = [0] + [(constants[j, 1] + 1) // 2 for j in range(1, N + 1)]
                negatives = [0] + [(-constants[j, -1]) // 2 + 1 for j in range(1, N + 1)]
            if selection == "rounding_of_scaled_residual":
                for j in range(1, min(2, N) + 1):
                    positives[j] = (1 << F) // (2 * radix ** j + 1) + 1 if logarithm else (constants[j, 1] + 1) // 2
                    negatives[j] = -(-(1 << F) // (2 * radix ** j - 1)) if logarithm else (-constants[j, -1]) // 2 + 1
            def threshold_at(address):
                return n.mux(negative, n.rom(negatives, address, F + 3), n.rom(positives, address, F + 3))
            previous = n.sub(candidate, n.const(1, candidate.w), candidate.w)
            earlier = n.land(n.gt(candidate, n.const(1, candidate.w)), n.ge(magnitude, threshold_at(previous)))
            candidate = n.mux(earlier, previous, candidate)
            threshold = threshold_at(candidate)
            candidate = n.mux(n.ge(magnitude, threshold), candidate, n.add(candidate, n.const(1, candidate.w), candidate.w))
            index = n.mux(n.lt(candidate, following), following, candidate)
            active = n.le(index, n.const(N, index.w))
            following = n.mux(active, n.add(index, n.const(1, index.w), index.w), index)
            index_refs.append(index)
            return index, active, following
        def raw_skip_digit(index, active, residual, constants, logarithm=False, selector=None):
            selector = selection if selector is None else selector
            amount = n.shl(index, rb.bit_length() - 1)
            shift_refs.append(amount)
            if selector == "rounding_of_scaled_residual":
                # round(residual * radix^index) at F fractional bits.
                # A variable left shift followed by a fixed binary point
                # keeps partial final stages exact, including index*rb>F.
                magnitude = (n.neg(residual) if additive else n.sub(n.const(1 << F, F + 3, True), residual, F + 3)) if logarithm else residual
                shifted = n.shlv(magnitude, amount, magnitude.w + (N + 1) * rb)
                rounded = n.shr(n.add(shifted, n.const(1 << (F - 1), shifted.w, True)), F)
                clipped = n.mux(n.gt(rounded, n.const(dmax, rounded.w, True)), n.const(dmax, rounded.w, True), rounded)
                if digits == "signed_redundant":
                    clipped = n.mux(n.lt(clipped, n.const(-dmax, clipped.w, True)), n.const(-dmax, clipped.w, True), clipped)
                    dw = max(2, dmax.bit_length() + 1)
                    dsel = n.mux(active, n.trunc(clipped, dw), n.const(0, dw, True))
                    table = [0] * (1 << dw) + [constants.get((j, _wrap(raw, dw, True)), 0)
                            for j in range(1, N + 1) for raw in range(1 << dw)]
                    factor = n.rom(table, n.cat(index, n.uns(dsel)), F + 3, True)
                    digit_refs.append(dsel)
                    return dsel, factor, amount
                clipped = n.mux(n.lt(clipped, n.const(0, clipped.w, True)), n.const(0, clipped.w, True), clipped)
                dsel = n.uns(n.trunc(clipped, rb))
                factor_table = [0] * radix + [constants[j, digit] for j in range(1, N + 1) for digit in dset]
                def factor_of(digit):
                    return n.rom(factor_table, n.cat(index, digit), F + 3, True)
                if logarithm:
                    wide = residual.w + (N + 1) * rb
                    trial = n.add(n.shlv(residual, amount, wide), n.mul(residual, dsel))
                    if additive:
                        trial = n.add(trial, n.shl(n.sgn(dsel), F))
                        limit = n.const(0, trial.w, True)
                    else:
                        limit = n.shlv(n.const(1 << F, F + 3, True), amount, wide)
                    repair = n.gt(trial, limit)
                else:
                    repair = n.gt(factor_of(dsel), residual)
                repair = n.land(n.ne(dsel, n.const(0, rb)), repair)
                dsel = n.mux(repair, n.sub(dsel, n.const(1, rb), rb), dsel)
                dsel = n.mux(active, dsel, n.const(0, rb))
                digit_refs.append(dsel)
                return dsel, factor_of(dsel), amount
            if digits == "signed_redundant":
                dw = max(2, dmax.bit_length() + 1)
                if logarithm:
                    dsel = n.const(dmax, dw, True)
                    for digit in reversed(dset[:-1]):
                        table = [0] + [-(-((1 << F) * 2 * radix ** j) // (2 * radix ** j + 2 * digit + 1)) - ((1 << F) if additive else 0)
                                       for j in range(1, N + 1)]
                        threshold = n.rom(table, index, F + 3, True)
                        dsel = n.mux(n.ge(residual, threshold), n.const(digit, dw, True), dsel)
                else:
                    dsel = n.const(-dmax, dw, True)
                    for digit in dset[1:]:
                        # ceil midpoint is required even when both factor
                        # constants are negative, or one rounds to zero.
                        table = [0] + [(constants[j, digit - 1] + constants[j, digit] + 1) // 2
                                       for j in range(1, N + 1)]
                        threshold = n.rom(table, index, F + 3, True)
                        dsel = n.mux(n.ge(residual, threshold), n.const(digit, dw, True), dsel)
                dsel = n.mux(active, dsel, n.const(0, dw, True))
                table = [0] * (1 << dw) + [constants.get((j, _wrap(raw, dw, True)), 0)
                        for j in range(1, N + 1) for raw in range(1 << dw)]
                factor = n.rom(table, n.cat(index, n.uns(dsel)), F + 3, True)
                digit_refs.append(dsel)
                return dsel, factor, amount
            # Every candidate digit has a dynamic index ROM port. The
            # result and factor are selected together from the full digit
            # domain; a zero-valued log constant is still a live choice.
            dsel = n.const(0, rb)
            selected_factor = n.const(0, F + 3, True)
            for digit in dset[1:]:
                factors = n.rom([0] + [constants[j, digit] for j in range(1, N + 1)], index, F + 3, True)
                if logarithm:
                    table = [0] + [((1 << F) * radix ** j) // (radix ** j + digit) - ((1 << F) if additive else 0)
                                   for j in range(1, N + 1)]
                    threshold = n.rom(table, index, F + 3, True)
                    hit = n.land(active, n.le(residual, threshold))
                else:
                    hit = n.land(active, n.ge(residual, factors))
                dsel = n.mux(hit, n.const(digit, rb), dsel)
                selected_factor = n.mux(hit, factors, selected_factor)
            digit_refs.append(dsel)
            return dsel, selected_factor, amount
        def skip_digit(index, active, residual, constants, logarithm=False):
            digit, factor, amount = raw_skip_digit(index, active, residual, constants, logarithm)
            if selection == "rounding_of_scaled_residual":
                digit_refs.pop(); shift_refs.pop()
                startup_digit, startup_factor, _ = raw_skip_digit(index, active, residual, constants, logarithm=logarithm, selector="table_lookup")
                digit_refs.pop(); shift_refs.pop()
                startup = n.le(index, n.const(2, index.w))
                digit = n.mux(startup, startup_digit, digit)
                factor = n.mux(startup, startup_factor, factor)
                digit_refs.append(digit); shift_refs.append(amount)
            return digit, factor, amount
        if core.name == "exp2c":
            if digits == "signed_redundant":
                upper = n.ge(u, n.const(1 << (Fu - 1), max(u.w, Fu)))
                signed_u = n.sgn(u)
                folded = n.mux(upper, n.sub(signed_u, n.const(1 << Fu, max(signed_u.w, Fu + 2), True)), signed_u)
                r = n.shr(n.mul(folded, n.const(ln2, ln2.bit_length() + 1, True)), Fu + 2)
                r = n.trunc(r, F + 3) if r.w > F + 3 else n.ext(r, F + 3)
                y = n.mux(upper, n.const((1 if additive else 2) << F, F + 4, True),
                          n.const(0 if additive else 1 << F, F + 4, True))
                manifest.update(initial_upper_signal=upper.name, initial_upper_width=upper.w)
            else:
                r = n.sgn(n.shr(n.mul(u, n.const(ln2, ln2.bit_length())), Fu + 2))
                r = n.ext(r, F + 3)
                y = n.const(0 if additive else 1 << F, F + 4, True)
            state_refs.append(y)
            residual_refs.append(r)
            schedule = ([(1, True)] if bootstrap else []) + [(i, False) for i in range(1, N + 1)]
            for i, startup_stage in schedule:
                stage_selection = "table_lookup" if i <= 2 else selection
                if startup_stage and advance == "leading_bit_skip":
                    index_refs.append(n.const(1, iw))
                    shift_refs.append(n.const(rb, iw + rb.bit_length() - 1))
                if advance == "leading_bit_skip" and not startup_stage:
                    if digits == "signed_redundant":
                        index, take, next_index = signed_skip_index(r, next_index, lnT)
                    else:
                        thresholds = [max(1, lnT[j, 1]) if selection == "rounding_of_scaled_residual" and j > 2 else lnT[j, 1]
                                      for j in range(1, N + 1)]
                        index, take, next_index = skip_index(r, next_index, thresholds)
                    digit, factor, amount = skip_digit(index, take, r, lnT)
                    r = n.mux(take, n.sub(r, factor, F + 3), r)
                    if additive:
                        y = n.mux(take, additive_update(y, digit, amount), y)
                    else:
                        product = y if radix == 2 and digits == "nonredundant" else n.mul(y, digit)
                        y = n.mux(take, n.add(y, n.shrv(product, amount), F + 4), y)
                    state_refs.append(y)
                    residual_refs.append(r)
                    continue
                # the digit: by comparison against the table (nonredundant) or by rounding the scaled residual
                if digits == "nonredundant" and stage_selection == "table_lookup" and radix == 2:
                    L1 = n.const(lnT[(i, 1)], F + 3, True)
                    take = n.ge(r, L1)
                    digit_refs.append(take)
                    r = n.mux(take, n.sub(r, L1), r)
                    y = n.mux(take, additive_update(y, n.const(1, 1), i), y) if additive else \
                        n.mux(take, n.add(y, n.shr(y, i)), n.ext(y, y.w + 1))
                else:
                    lo, hi = min(dset), max(dset)
                    dw = max(2, max(abs(lo), abs(hi)).bit_length() + 1)
                    if stage_selection == "table_lookup":
                        # Decode the stored log-factor thresholds. The
                        # nonredundant set takes the largest safe factor;
                        # signed digits use boundaries between neighbours.
                        dsel = n.const(lo, dw, True)
                        for digit in dset[1:]:
                            threshold = lnT[(i, digit)] if digits == "nonredundant" else \
                                (lnT[(i, digit - 1)] + lnT[(i, digit)] + 1) // 2
                            hit = n.ge(r, n.const(threshold, r.w, True))
                            dsel = n.mux(hit, n.const(digit, dw, True), dsel)
                    else:
                        # d = round(r radix^i) clamped to the digit set.
                        sc = round_scaled(r, i * rb)
                        dsel = n.mux(n.gt(sc, n.const(hi, sc.w, True)), n.const(hi, sc.w, True), n.mux(n.lt(sc, n.const(lo, sc.w, True)), n.const(lo, sc.w, True), sc))
                        dsel = n.trunc(dsel, dw) if dsel.w > dw else n.ext(dsel, dw)
                        if digits == "nonredundant":
                            candidate_table = [lnT.get((i, a), 0) for a in range(1 << dw)]
                            candidate = n.rom(candidate_table, n.uns(dsel), F + 3, True)
                            dsel = n.mux(n.gt(candidate, r), n.sub(dsel, n.const(1, dw, True), dw), dsel)
                    digit_refs.append(dsel)
                    tab = [lnT[(i, _wrap(a, dw, True))] if _wrap(a, dw, True) in dset else 0 for a in range(1 << dw)]
                    Lt = n.rom(tab, n.uns(dsel), F + 3, True)
                    r = n.sub(r, Lt)
                    if additive:
                        y = additive_update(y, dsel, i * rb)
                    else:
                        prod = n.shr(n.mul(y, dsel), i * rb)
                        y = n.add(y, prod)
                r = n.trunc(r, F + 3) if r.w > F + 3 else r
                y = n.trunc(y, F + 4) if y.w > F + 4 else y
                state_refs.append(y)
                residual_refs.append(r)
            if term == "linear_extrapolation":
                y = n.add(y, n.add(r, n.shr(n.mul(y, r), F))) if additive else n.add(y, n.shr(n.mul(y, r), F))
                notes.append("termination linear_extrapolation: delta + r + delta*r" if additive else
                             "termination linear_extrapolation: y (1 + r) after half the iterations")
            state_refs.append(y)
            residual_refs.append(r)
            if additive:
                y = n.add(y, n.const(1 << F, max(y.w, F + 4), True))
            notes.append(f"exp: {normalization} normalization, radix {radix}, {digits} digits, {physical_stages} physical stages")
            if digits == "signed_redundant":
                notes.append("signed upper-half fold with exact initial product two" + (", explicit radix16 index-one bootstrap" if bootstrap else ""))
            return finish(_clamp_result(n, n.shr(y, F - Fo), Fo + 1), lnT)
        # log2c direct: r = m' -> 1 by the factors (1 + d radix^-i), L -= log2(1 + d radix^-i)
        d0 = n.sub(n.sgn(u), n.const(1 << (Fu - 2), Fu + 1, True))
        r = n.ext(n.shl(d0, F - Fu) if F > Fu else n.shr(d0, Fu - F), F + 3)
        if not additive:
            r = n.add(n.const(1 << F, F + 3, True), r, F + 3)
        if digits == "nonredundant":
            # Unsigned digits only increase r. Fold m'>1 into m'/2 so
            # every legal operand starts at r in [1/2,1], and compensate
            # its logarithm by one. Signed digits keep the centred input.
            halve = n.gt(r, n.const(0 if additive else 1 << F, r.w, True))
            half_state = n.sub(n.shr(r, 1), n.const(1 << (F - 1), r.w, True), r.w) if additive else n.ext(n.shr(r, 1), r.w)
            r = n.mux(halve, half_state, r)
            manifest.update(initial_halve_signal=halve.name, initial_halve_width=halve.w)
            L = n.mux(halve, n.const(1 << F, F + 3, True), n.const(0, F + 3, True))
        else:
            L = n.const(0, 2, True)
        state_refs.append(r)
        residual_refs.append(r if additive else n.sub(r, n.const(1 << F, r.w, True), F + 3))
        accumulator_refs.append(L)
        dset2 = dset
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            lgT = {(i, d): int(mpmath.floor(mpmath.log(1 + mpmath.mpf(d) * mpmath.mpf(radix) ** -i, 2) * (1 << F) + mpmath.mpf("0.5"))) if 1 + d * radix ** -i > 0 else 0
                   for i in range(1, N + 1) for d in dset2}
        schedule = ([(1, True)] if bootstrap else []) + [(i, False) for i in range(1, N + 1)]
        if term == "linear_extrapolation" and N == Ntot:
            # F<=12 here. Enumerate every reachable integer significand,
            # including sparse Fu<F inputs, rather than sampling operands.
            stop = manifest["domain_hi_exclusive"]
            if Fu >= F:
                initial = [(k << (Fu - F), (3 << (F - 2)) + k) for k in range(((stop - 1) >> (Fu - F)) + 1)]
            else:
                initial = [(k, (3 << (F - 2)) + (k << (F - Fu))) for k in range(stop)]
            witness = None
            for argument, value in initial:
                if digits == "nonredundant" and value > 1 << F:
                    value //= 2
                for index, _ in schedule:
                    scale = radix ** index
                    if selection == "table_lookup" or index <= 2:
                        if digits == "nonredundant":
                            digit = max(d for d in dset if value * (scale + d) <= (1 << F) * scale)
                        else:
                            digit = dset[-1]
                            for d in reversed(dset[:-1]):
                                if value * (2 * scale + 2 * d + 1) >= (2 << F) * scale:
                                    digit = d
                    else:
                        digit = max(dset[0], min(dset[-1], (2 * ((1 << F) - value) * scale + (1 << F)) // (2 << F)))
                        if digits == "nonredundant" and value * (scale + digit) > (1 << F) * scale:
                            digit -= 1
                    value += value * digit // scale
                if value != 1 << F:
                    witness = {"input": argument, "terminal_centered_state": value - (1 << F)}
                    break
            if witness is None:
                raise ValueError(f"log linear_extrapolation has an identically zero tail and no shorter schedule at Fo={Fo}; "
                                 f"use at least {max(0, 3 * rb - 5)} output fraction bits for a shorter schedule")
            manifest["termination_activity_witness"] = witness
        for i, startup_stage in schedule:
            stage_selection = "table_lookup" if i <= 2 else selection
            if startup_stage and advance == "leading_bit_skip":
                index_refs.append(n.const(1, iw))
                shift_refs.append(n.const(rb, iw + rb.bit_length() - 1))
            if advance == "leading_bit_skip" and not startup_stage:
                gap = n.neg(r) if additive else n.sub(n.const(1 << F, F + 3, True), r, F + 3)
                if digits == "signed_redundant":
                    index, take, next_index = signed_skip_index(gap, next_index, lgT, logarithm=True)
                else:
                    boundaries = [-(-(1 << F) // (radix ** j + 1)) for j in range(1, N + 1)]
                    index, take, next_index = skip_index(gap, next_index, boundaries)
                digit, factor, amount = skip_digit(index, take, r, lgT, logarithm=True)
                if additive:
                    r = n.mux(take, additive_update(r, digit, amount), r)
                else:
                    product = r if radix == 2 and digits == "nonredundant" else n.mul(r, digit)
                    r = n.mux(take, n.add(r, n.shrv(product, amount), F + 3), r)
                L = n.sub(L, n.mux(take, factor, n.const(0, F + 3, True)))
                state_refs.append(r)
                residual_refs.append(r if additive else n.sub(r, n.const(1 << F, r.w, True), F + 3))
                accumulator_refs.append(L)
                continue
            e = r if additive else n.sub(r, n.const(1 << F, F + 3, True))
            lo, hi = min(dset2), max(dset2)
            dw = max(1, hi.bit_length()) if digits == "nonredundant" else max(2, max(abs(lo), abs(hi)).bit_length() + 1)
            if stage_selection == "table_lookup":
                if digits == "nonredundant":
                    dsel = n.const(0, dw)
                    for digit in dset2[1:]:
                        boundary = ((1 << F) * radix ** i) // (radix ** i + digit) - ((1 << F) if additive else 0)
                        hit = n.le(r, n.const(boundary, r.w, True))
                        dsel = n.mux(hit, n.const(digit, dw), dsel)
                else:
                    dsel = n.const(hi, dw, True)
                    for digit in reversed(dset2[:-1]):
                        factor_sum = Fraction(2) + Fraction(2 * digit + 1, radix ** i)
                        threshold = (2 / factor_sum) * (1 << F)
                        boundary = -(-threshold.numerator // threshold.denominator)
                        if additive:
                            boundary -= 1 << F
                        hit = n.ge(r, n.const(boundary, max(r.w, boundary.bit_length() + 1), True))
                        dsel = n.mux(hit, n.const(digit, dw, True), dsel)
            else:
                sc = round_scaled(n.neg(e), i * rb)
                dsel = n.mux(n.gt(sc, n.const(hi, sc.w, True)), n.const(hi, sc.w, True), n.mux(n.lt(sc, n.const(lo, sc.w, True)), n.const(lo, sc.w, True), sc))
                dsel = n.trunc(dsel, dw) if dsel.w > dw else n.ext(dsel, dw)
                if digits == "nonredundant":
                    dsel = n.uns(dsel)
                    # Rounding the residual can exceed the largest safe
                    # unsigned digit by one; repair it before updating r.
                    trial = n.add(n.shl(r, i * rb), n.mul(r, dsel))
                    if additive:
                        trial = n.add(trial, n.shl(n.sgn(dsel), F))
                        limit = n.const(0, trial.w, True)
                    else:
                        limit = n.const(1 << (F + i * rb), max(trial.w, F + i * rb + 2), True)
                    repair = n.gt(trial, limit)
                    dsel = n.mux(repair, n.sub(dsel, n.const(1, dw), dw), dsel)
            digit_refs.append(dsel)
            value_of = (lambda a: a) if digits == "nonredundant" else (lambda a: _wrap(a, dw, True))
            tab = [lgT[(i, value_of(a))] if value_of(a) in dset2 else 0 for a in range(1 << dw)]
            Lt = n.rom(tab, n.uns(dsel), F + 3, True)
            r = additive_update(r, dsel, i * rb) if additive else n.add(r, n.shr(n.mul(r, dsel), i * rb))
            L = n.sub(L, Lt)
            r = n.trunc(r, F + 3) if r.w > F + 3 else r
            state_refs.append(r)
            residual_refs.append(r if additive else n.sub(r, n.const(1 << F, r.w, True), F + 3))
            accumulator_refs.append(L)
        state_refs.append(r)
        e = r if additive else n.sub(r, n.const(1 << F, F + 3, True))
        if term == "linear_extrapolation":
            L = n.add(L, n.shr(n.mul(e, n.const(inv_ln2, inv_ln2.bit_length())), F + 2))
        residual_refs.append(e)
        accumulator_refs.append(L)
        notes.append(f"log: {normalization} normalization, radix {radix}, {digits} digits, {physical_stages} physical stages; table startup through index two" + (", fixed index-one bootstrap" if bootstrap else ""))
        return finish(n.shr(L, F - Fo), lgT)


# ---- Newton-Raphson and Goldschmidt over a seed table ---------------------------------------------
class NewtonEngine(_Engine):
    covers = {"recipc", "rsqrtc", "sqrtc"}

    def build(self, n: Net, core: Core, u: Ref, Fu: int, Fo: int) -> tuple:
        notes = []
        steps = int(self.P("steps", 1))
        if not 1 <= steps <= 3:
            raise ValueError(f"{self.family} steps must be in 1..3, got {steps}")
        gold = self.family == "goldschmidt"
        monotone = str(self.P("termination", "fixed_steps")) == "monotone_non_decrease"
        ub = u.w
        # m at F bits and the seed bits from the steps (each step doubles)
        k = max(4, -(-(Fo + 3) // (1 << steps)) + 1)
        k = min(k, ub)
        # Keep the squared seed error represented through every requested
        # refinement, rather than adding statically converged NOP stages.
        F = max(Fo + 4, (k + 3) * (1 << steps) + 4)
        from chialu.targets.rtl.families.fidelity import effective
        effective(self.pins, "steps", steps, "refinements retain the seed-error precision through the last stage",
                  {"fraction_bits": F, "seed_index_bits": k})
        if core.L > 1:
            hi_bit = n.bit(u, ub - 1)
            frac = n.bits(u, ub - 2, 0)
            m = n.mux(hi_bit, n.cat(n.const(1, 1), frac, n.const(0, 1)), n.cat(n.const(0, 1), n.const(1, 1), frac))
            Fm = Fu
        else:
            m = n.cat(n.const(1, 1), u)
            Fm = Fu
        m = n.shl(m, F - Fm) if F > Fm else n.shr(m, Fm - F)
        idx = n.bits(u, ub - 1, ub - k)
        tab = []
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            for a in range(1 << k):
                uu = (a << (ub - k)) + (1 << (ub - k - 1))
                g = core.f(mpmath.mpf(uu) / (1 << Fu)) if core.name != "sqrtc" else 1 / mpmath.sqrt(_mval(uu, Fu, core.L))
                tab.append(int(mpmath.floor(g * (1 << (k + 1)) + mpmath.mpf("0.5"))))
        y = n.shl(n.rom(tab, idx, k + 2), F - (k + 1))
        rsq = core.name in ("rsqrtc", "sqrtc")
        if not gold:
            stopped = n.const(0, 1) if monotone else None
            for s in range(steps):
                previous = y
                if rsq:
                    y2 = n.shr(n.mul(y, y), F)
                    my2 = n.shr(n.mul(m, y2), F)
                    t = n.sub(n.const(3 << F, F + 3, True), n.sgn(my2))
                    y = n.shr(n.mul(y, t), F + 1)
                else:
                    my = n.shr(n.mul(m, y), F)
                    t = n.sub(n.const(2 << F, F + 3, True), n.sgn(my))
                    y = n.shr(n.mul(y, t), F)
                y = n.uns(n.trunc(y, F + 2)) if y.w > F + 2 else n.uns(y)
                if monotone:
                    def residual(candidate):
                        product = n.shr(n.mul(candidate, candidate), F) if rsq else candidate
                        product = n.shr(n.mul(m, product), F)
                        error = n.sub(n.sgn(product), n.const(1 << F, F + 3, True))
                        return n.uns(n.mux(n.lt(error, n.const(0, error.w, True)), n.neg(error), error))
                    stopped = n.lor(stopped, n.ge(residual(y), residual(previous)))
                    y = n.mux(stopped, previous, y)
                n.refinement_stages.append((s, previous, y))
            if monotone:
                notes.append("termination monotone_non_decrease: compare the absolute residual with the preceding stage and bypass when it stops decreasing")
            notes.append(f"newton_raphson: a {k}-bit seed table, {steps} step(s)")
        else:
            if rsq:
                # B = m y0^2, Y = y0; F = (3 - B)/2, Y <- Y F, B <- B F^2
                Y = y
                B = n.shr(n.mul(m, n.shr(n.mul(y, y), F)), F)
                for s in range(steps):
                    previous = Y
                    Fh = n.shr(n.sub(n.const(3 << F, F + 3, True), n.sgn(B)), 1)
                    Y = n.shr(n.mul(n.sgn(Y), Fh), F)
                    B = n.shr(n.mul(n.sgn(B), n.shr(n.mul(Fh, Fh), F)), F)
                    Y = n.uns(n.trunc(Y, F + 2)) if Y.w > F + 2 else n.uns(Y)
                    B = n.uns(n.trunc(B, F + 2)) if B.w > F + 2 else n.uns(B)
                    n.refinement_stages.append((s, previous, Y))
                y = Y
            else:
                Nn = n.shr(n.mul(y, n.const(1 << F, F + 1)), F)
                D = n.shr(n.mul(m, y), F)
                Nn = n.uns(n.trunc(Nn, F + 2)) if Nn.w > F + 2 else n.uns(Nn)
                D = n.uns(n.trunc(D, F + 2)) if D.w > F + 2 else n.uns(D)
                for s in range(steps):
                    previous = Nn
                    Fh = n.sub(n.const(2 << F, F + 3, True), n.sgn(D))
                    Nn = n.shr(n.mul(n.sgn(Nn), Fh), F)
                    D = n.shr(n.mul(n.sgn(D), Fh), F)
                    Nn = n.uns(n.trunc(Nn, F + 2)) if Nn.w > F + 2 else n.uns(Nn)
                    D = n.uns(n.trunc(D, F + 2)) if D.w > F + 2 else n.uns(D)
                    n.refinement_stages.append((s, previous, Nn))
                y = Nn
            notes.append(f"goldschmidt: a {k}-bit seed table, {steps} step(s)")
        if core.name == "sqrtc":
            y = n.shr(n.mul(y, m), F)
        return _clamp_result(n, n.shr(y, F - Fo), Fo + core.ibits()), notes



# ---- the vector functions: softmax and layernorm over the lanes of one mode ------------------------
class SoftmaxEngine(_Engine):
    """The exponential core of the softmax_layernorm family by its
    exp_evaluation choice; the other cores (the reciprocal, the log,
    the reciprocal square root) fall back to a segmented polynomial."""
    covers = {"exp2c", "recipc", "log2c", "rsqrtc"}

    def __init__(self, family, pins):
        super().__init__(family, pins)
        ev = str(self.P("exp_evaluation", "lut_pwl"))
        if ev == "lut_pwl":
            self.inner = poly_engine("pwl", {"segments": 16, "coeff_frac_bits": 20, "x_frac_bits": 16})
            self.what = "a 16-segment piecewise-linear table"
        elif ev == "base2_shift_add":
            self.inner = LnsEngine("logarithmic_converters", {"correction": "rom_free_shift_add"})
            self.what = "Mitchell's 1 + f with the shift-add correction"
        elif ev == "approximate_substitute":
            self.inner = LnsEngine("logarithmic_converters", {"correction": "none"})
            self.what = "the substitute 2^f ~ 1 + f"
        elif ev == "integer_polynomial":
            self.inner = poly_engine("single_poly", {"degree": 2, "basis": "minimax_remez"})
            self.what = "one quadratic (the integer-polynomial line)"
        else:
            self.inner = table_engine("bipartite", {"symmetric": True})
            self.what = "a bipartite table" + (" (input_proximity gating has no combinational form)" if str(self.P("lut_group_gating", "fixed")) != "fixed" else "")

    def build(self, n, core, u, Fu, Fo):
        if core.name != "exp2c":
            # These are fixed constituent normalization cores of this family;
            # exp_evaluation selects only the exponential datapath.
            helper = poly_engine("piecewise_poly", {"segments": 16, "degree": 2,
                                                    "basis": "chebyshev", "guard_bits": 2})
            return helper(n, core, u, Fu, Fo, core.name), [f"normalization core {core.name}: fixed quadratic"]
        if str(self.P("exp_evaluation", "lut_pwl")) == "lut_pwl":
            inner = poly_engine("pwl", {"segments": 16, "coeff_frac_bits": 20, "x_frac_bits": min(16, u.w)})
            R = inner(n, core, u, Fu, Fo, core.name)
        else:
            R = self.inner(n, core, u, Fu, Fo, core.name)
        return R, [f"exp_evaluation: {self.what}"]


class VectorLane:
    """softmax / layernorm over `count` lanes: every lane's X in (x<i>),
    every lane's X out (y<i>, the seed packs them) and inv (a special
    operand). softmax: the lanes as fixed-point values, the maximum
    subtracted (max_subtraction), d_i log2 e split into an integer and a
    fraction, 2^f through the exponential core, the sum over a reduction
    tree, the normalization by a true divider (the library's restoring
    divider), a reciprocal multiply (the reciprocal core over the
    normalized sum) or the log-domain subtraction (log2 of the sum off
    the exponents, then the antilog core). layernorm: the exact mean
    and variance in fixed point, the reciprocal square root core over
    the normalized variance, one multiply per lane."""

    def __init__(self, net: Net, g: Geom, fmt, fn: str, count: int, engine, pins: dict, guard: int = 3):
        self.n, self.g, self.fmt, self.fn, self.count, self.engine, self.pins, self.G = net, g, fmt, fn, count, engine, pins, guard
        self.facts = fmt_facts(fmt)
        self.SW = self.facts["SW"]
        self.XW, self.EW, self.XT = g.XW, g.EW, g.XT
        self.notes: list = []
        self.lanes = [Lane(net, g, fmt, fn, engine, guard=guard, pins=pins) for _ in range(count)]

    def build(self):
        n = self.n
        for i, ln in enumerate(self.lanes):
            ln.unpack(f"x{i}")
        specials = n.lor(*[n.ne(ln.sp, n.const(0, 2)) for ln in self.lanes])
        outs = self.p_softmax() if self.fn == "softmax" else self.p_layernorm()
        for i, (s, e, sig, st) in enumerate(outs):
            y = self.lanes[i].x_out(n.mux(specials, n.const(1, 2), n.const(0, 2)), s, e, sig, n.land(st, n.nz(sig)))
            n.port_out(f"y{i}", y)
        n.port_out("inv", specials)

    # -- the lanes as signed fixed-point values
    def fixed_lanes(self, I: int, F: int) -> list:
        n = self.n
        vals = []
        for ln in self.lanes:
            mag, lost, ovf = ln.to_fixed(ln.sign, ln.E, I, F)
            mag = n.mux(ln.zero, n.const(0, mag.w), mag)
            mag = n.mux(n.land(ovf, n.lnot(ln.zero)), n.const((1 << (I + F)) - 1, I + F), mag)   # a value beyond 2^I saturates
            vals.append(ln.fixed_signed(mag, n.land(lost, n.lnot(ln.zero)), ln.s))
        return vals

    def _tree(self, terms: list, w: int) -> Ref:
        n = self.n
        while len(terms) > 1:
            terms = [n.add(terms[i], terms[i + 1], w) if i + 1 < len(terms) else terms[i] for i in range(0, len(terms), 2)]
        return terms[0]

    def p_softmax(self) -> list:
        n, SW, G, EW, XW = self.n, self.SW, self.G, self.EW, self.XW
        cnt = self.count
        P = lambda k, d: _pin(self.pins, k, d)  # noqa: E731
        maxsub = bool(P("max_subtraction", True))
        norm = str(P("normalization_division", "true_divider"))
        passes = int(P("passes_over_vector", 1))
        if passes > 1:
            self.notes.append(f"passes_over_vector {passes}: the unrolled datapath is one pass over the lanes")
        I = min(32, self.facts["emax"] + 2)
        F = SW + G + 2
        Fo = SW + G + 1
        v = self.fixed_lanes(I, F)                                     # I + F + 1 bits, signed
        W = v[0].w
        # the maximum, or a zero reference without the subtraction
        if maxsub:
            m = v[0]
            for x in v[1:]:
                m = n.mux(n.gt(x, m), x, m)
        # the exponent argument: the maximum subtracted (d_i = max - x_i >= 0), or -x_i itself when the lanes'
        # exponentials go in floating form and the accumulation aligns to the largest exponent
        d = [n.sub(m, x, W + 1) if maxsub else n.neg(x) for x in v]
        if not maxsub:
            self.notes.append("max_subtraction false: e^x of the lanes themselves in floating form; the accumulation aligns "
                              "the lanes to the largest exponent (no subtraction pass over the vector)")
        # y_i = -d_i log2 e: the integer and the fraction of the exponent
        log2e = self._log2e()
        Fk = F + 6
        cq = int(round(log2e * (1 << Fk)))
        nn, ff = [], []
        for x in d:
            yy = n.shr(n.mul(n.neg(x), n.const(cq, cq.bit_length())), Fk)     # F fraction bits, signed
            ni = n.shr(yy, F)                                          # the lane's binary exponent (its own width)
            nn.append(n.ext(ni, max(ni.w, EW)))
            ff.append(n.bits(yy, F - 1, 0))
        core = core_of("exp2c")
        cs = [self.lanes[i].fitw(self.engine(n, core, ff[i], F, Fo, f"exp2c[{i}]"), Fo + 1) for i in range(cnt)]
        # the reference exponent of the accumulation: 0 under the subtraction, else the lanes' largest
        if maxsub:
            ref_n = n.const(0, 2, True)
        else:
            ref_n = nn[0]
            for x in nn[1:]:
                ref_n = n.mux(n.gt(x, ref_n), x, ref_n)
        # every lane's exponent relative to the reference (<= 0, floored at the exponent frame: a lane that far
        # below vanishes); the sum: a fixed accumulator of FS fraction bits and IS integer bits, every lane
        # shifted down by its distance from the reference
        rel = []
        for i in range(cnt):
            wr = max(nn[i].w, ref_n.w) + 2
            r_ = n.sub(n.ext(nn[i], wr), n.ext(ref_n, wr), wr)
            floor_ = n.const(-(1 << (EW - 2)), wr, True)
            rel.append(n.mux(n.lt(r_, floor_), floor_, r_))
        FS = Fo + 4
        IS = 1 + cnt.bit_length()
        WS = IS + FS + 1
        terms = []
        for i in range(cnt):
            c = n.shl(cs[i], FS - Fo)                                  # FS fraction bits
            dist = n.neg(rel[i])                                       # >= 0
            shr_amt = n.uns(n.trunc(n.mux(n.gt(dist, n.const(FS + 1, dist.w, True)), n.const(FS + 1, dist.w, True), dist),
                                    max(1, (FS + 1).bit_length() + 1)))
            terms.append(n.shrv(n.ext(c, WS), shr_amt))
        S = self._tree(terms, WS)
        # S = 2^k (1 + u) relative to the reference exponent: the leading one and the fraction below it
        lz = n.lzc(S)
        Sn = n.shlv(S, lz, WS)
        k = n.sub(n.const(WS - 1 - FS, lz.w + 2, True), n.ext(n.sgn(lz), lz.w + 2), lz.w + 2)
        u = n.bits(Sn, WS - 2, WS - 1 - F)
        kx = n.ext(k, EW + 4) if k.w <= EW + 4 else n.trunc(k, EW + 4)          # k in the exponent frame
        self.dbg = {"v": v, "d": d, "nn": nn, "ff": ff, "cs": cs, "S": S, "k": k, "u": u, "F": F, "Fo": Fo, "FS": FS}
        outs = []
        if norm == "reciprocal_multiply":
            r = self.lanes[0].fitw(self.engine(n, core_of("recipc"), u, F, Fo + 1, "recipc"), Fo + 2)
            for i in range(cnt):
                Pm = n.mul(cs[i], r)
                sig, st, adj = self.lanes[i].fit(Pm)
                e = n.sub(self.lanes[i].eadj(rel[i], -Fo - (Fo + 1), adj), kx, EW + 4)
                outs.append((n.const(0, 1), e, sig, n.const(1, 1)))
            self.notes.append("normalization: the reciprocal of the normalized sum by the reciprocal core, one multiply per lane")
        elif norm == "log_domain_subtraction":
            # log2 S = kk + log2(1 + d) with S centred into the log core's domain (d in [-1/4, 1/2)); the lane's
            # log2 y = -d_i log2 e - log2 S; the antilog through the exponential core
            half = n.bit(u, F - 1)
            dd = n.mux(half, n.sub(n.sgn(n.shr(u, 1)), n.const(1 << (F - 1), F + 1, True)), n.sgn(u))     # (u - 1) / 2 or u
            kk = n.add(n.ext(k, k.w + 1), n.ext(half, k.w + 1), k.w + 1)
            ul = n.uns(n.trunc(n.add(dd, n.const(1 << (F - 2), F + 2, True)), F))                      # d + 1/4
            gR = self.engine(n, core_of("log2c"), ul, F, Fo, "log2c")
            if getattr(self.engine, "direct", None) and "log2c" in self.engine.direct:
                Lf = gR if gR.s else n.sgn(gR)                         # log2(1 + d) at Fo bits
            else:
                Lf = n.shr(n.mul(dd, gR), F)                           # d g(d) = log2(1 + d) at Fo bits
            Lf = n.shl(Lf, F - Fo) if F > Fo else n.shr(Lf, Fo - F)   # F fraction bits
            k = kk
            for i in range(cnt):
                yi = n.sub(n.sub(n.shl(n.ext(rel[i], rel[i].w + 2), F), n.shl(n.ext(k, k.w + 2), F)), n.ext(Lf, Lf.w + 2))
                yi = n.add(yi, n.ext(n.sgn(ff[i]), yi.w))              # -d log2 e = nn + ff
                n2 = n.shr(yi, F)
                f2 = n.bits(yi, F - 1, 0)
                c2 = self.lanes[i].fitw(self.engine(n, core, f2, F, Fo, f"exp2c[{i}]'"), Fo + 1)
                sig, st, adj = self.lanes[i].fit(c2)
                e = self.lanes[i].eadj(n2, -Fo, adj)
                outs.append((n.const(0, 1), e, sig, n.const(1, 1)))
            self.notes.append("normalization: log2 of the sum subtracted in the exponent domain, then the antilog core per lane")
        else:
            # a true divider: the library's restoring array per lane on the normalized sum's top bits
            from chialu.targets.rtl import families as FAM
            D = F + 1
            Q = Fo + 2
            dv = n.bits(Sn, WS - 1, WS - D)
            fam = str(P("divider.family", "restoring_nonrestoring"))
            for i in range(cnt):
                a = n.shl(cs[i], Q)
                m = FAM.div_module(fam, {}, a.w, D, a.w)
                if m is not None:
                    q = n.declare(a.w, False, lambda env, a=a, dv=dv, m_=(1 << a.w) - 1: (env[a.name] // max(1, env[dv.name])) & m_)
                    rr = n.declare(D, False, lambda env, a=a, dv=dv: env[a.name] % max(1, env[dv.name]))
                    n.inst(m, {"a": a.name, "b": dv.name, "q": q.name, "r": rr.name}, f"the true divider of lane {i}: the library module {m.name}")
                else:
                    raise ValueError(f"softmax true divider {fam!r} cannot generate {a.w}/{D} bits")
                sig, st, adj = self.lanes[i].fit(q)
                # q = c 2^(Fo+Q) / ((1+u) 2^(D-1)); y = c 2^nn / (2^k (1+u)) => e = nn - k - Fo - Q + D - 1 + adj
                e = n.sub(self.lanes[i].eadj(rel[i], -Q - Fo + D - 1, adj), kx, EW + 4)
                outs.append((n.const(0, 1), e, sig, n.const(1, 1)))
            self.notes.append(f"normalization: a true divider per lane ({fam}) over the normalized sum")
        return outs

    def _u_log(self, u: Ref, F: int) -> Ref:
        """The log core's argument u' = d + 1/4 for d = u (the sum's fraction, in [0, 1))."""
        n = self.n
        return n.uns(n.trunc(n.add(n.sgn(u), n.const(1 << (F - 2), F + 2, True)), F))

    def _log2e(self):
        with mpmath.workprec(max(PROFILE_BITS, _fit_precision.get())):
            return Fraction(str(mpmath.nstr(1 / mpmath.log(2), 40)))

    def p_layernorm(self) -> list:
        n, SW, G, EW, XW = self.n, self.SW, self.G, self.EW, self.XW
        cnt = self.count
        emin, emax = self.facts["emin"], self.facts["emax"]
        I = min(32, emax + 2)
        F = min(40, max(0, -emin))                                     # every lane value exact
        v = self.fixed_lanes(I, F)
        W = v[0].w
        lb = max(1, (cnt - 1).bit_length())
        Ws = W + lb
        S = self._tree([n.ext(x, Ws) for x in v], Ws)
        # the mean: exact with lb more fraction bits when the count is a power of two, else a small divider
        if cnt & (cnt - 1) == 0:
            mu = S                                                     # S / cnt at F + lb fraction bits
            Fm = F + lb
        else:
            Fm = F + lb + 4
            mu = n.wire(Ws + 4, True, f"$signed(({S.name} <<< {lb + 4}) / {cnt})",
                        lambda env, S=S, w=Ws + 4: _wrap((env[S.name] << (lb + 4)) // cnt if env[S.name] >= 0 else -((-env[S.name] << (lb + 4)) // cnt), w, True), "mu")
        d = [n.sub(n.shl(n.ext(x, Ws + 1), Fm - F), n.ext(mu, Ws + 1 + Fm - F)) for x in v]   # Fm fraction bits
        sq = [n.mul(x, x) for x in d]                                  # 2 Fm fraction bits
        Wq = sq[0].w + lb + 1
        var_n = self._tree([n.ext(x, Wq) for x in sq], Wq)             # n var at 2 Fm bits
        Fv = 2 * Fm + (lb if cnt & (cnt - 1) == 0 else 0)
        if cnt & (cnt - 1):
            var_n = n.wire(Wq, True, f"$signed({var_n.name} / {cnt})", lambda env, a=var_n, w=Wq: _wrap(env[a.name] // cnt, w, True), "var")
        var = n.uns(var_n)
        # var = 2^kv (1 + w) with kv even: the reciprocal square root core over w
        lz = n.lzc(var)
        top = n.sub(n.const(Wq - 1 - Fv, lz.w + 2, True), n.ext(n.sgn(lz), lz.w + 2), lz.w + 2)   # the leading one's exponent
        odd = n.bit(n.uns(top), 0)
        Fw = SW + G + 2
        vn = n.shlv(var, lz, Wq)                                       # leading one at Wq-1
        fr = n.bits(vn, Wq - 2, Wq - 1 - Fw)
        w = n.mux(odd, n.cat(n.const(1, 1), fr), n.cat(n.const(0, 1), fr))   # [0, 2): 1 + fr for an odd exponent
        Fo = SW + G + 1
        r = self.lanes[0].fitw(self.engine(n, core_of("rsqrtc"), w, Fw, Fo, "rsqrtc"), Fo + 2)   # 1/sqrt(1 + w) or 1/sqrt(2 w)
        half = n.shr(n.sub(top, n.ext(odd, top.w)), 1)                 # floor(top / 2)
        zero_var = n.eqc(var, 0)
        outs = []
        for i in range(cnt):
            neg = n.lt(d[i], n.const(0, d[i].w, True))
            mag = n.uns(n.mux(neg, n.neg(d[i]), d[i]))
            lzd = n.lzc(mag)
            dn = n.shlv(mag, lzd, mag.w)
            dt = n.bits(dn, mag.w - 1, max(0, mag.w - (XW + 2)))
            Pm = n.mul(dt, n.mux(zero_var, n.const(1 << Fo, Fo + 2), r))
            sig, st, adj = self.lanes[i].fit(Pm)
            # d = dt 2^(mag.w - 1 - lzd - Fm - (dt.w - 1)); r = 1/sqrt(var) 2^-half... y = d r 2^(-half)
            e = n.sub(self.lanes[i].eadj(n.neg(n.ext(lzd, EW + 3)), (mag.w - 1) - (dt.w - 1) - Fm - Fo, adj), n.mux(zero_var, n.const(0, EW + 4, True), n.ext(half, EW + 4)), EW + 4)
            outs.append((neg, e, sig, n.const(1, 1)))
        self.notes.append(f"layernorm: exact mean and variance over {cnt} lanes at {F} fraction bits, the reciprocal square root core, one multiply per lane")
        return outs


def vector_sv(fn: str, fmt, g: Geom, count: int, family: str, pins: dict | None = None, name: str | None = None) -> tuple:
    """(name, text, net) of the softmax_layernorm family's module for a
    vector function over `count` lanes of a format."""
    pins = pins or {}
    validate_sfu_pins(family, pins, fmt)
    if family != "softmax_layernorm":
        raise ValueError("the vector functions are the softmax_layernorm family's")
    if fn == "layernorm" and not bool(_pin(pins, "layernorm_support", False)):
        raise ValueError("layernorm needs layernorm_support")
    name = name or sfu_module_name(fn, fmt, "softmax_layernorm", pins).replace(f"_{fn}_", f"_{fn}_n{count}_", 1)
    bind = bind_of(pins)
    net = Net(name, f"{fn} over {count} lanes of {fmt.name} by the softmax_layernorm family (X in, X out per lane; the seed packs)"
              + ("; " + ", ".join(f"the {k} slot {v[0]}" for k, v in bind.items()) if bind else ""), bind=bind)
    primary = SoftmaxEngine(family, pins)
    eng = StagedEngine(primary)
    vl = VectorLane(net, g, fmt, fn, count, eng, pins)
    vl.build()
    net.notes += vl.notes
    net.lane = vl
    text = net.render()
    from chialu.targets.rtl.families.selection import register_origin
    register_origin(getattr(pins, "owner", None), family, pins, name, text)
    return name, text, net


def measure_vector(fn: str, fmt, g: Geom, count: int, net: Net, rounding: str = "RNE", limit: int = 300, seed: int = 1) -> dict:
    """The vector module's error against the verify layer's vector reference over random lane vectors."""
    import random
    from chialu.verify import sfu_ref as S
    from chialu.verify.formats import Special
    from chialu.verify.rounding import Rounder
    rng = random.Random(seed)
    r = Rounder(rounding, 8)
    posit = isinstance(_fmt_core(fmt), PositFormat)
    mx, n_, wrong, worst = 0, 0, 0, []
    for _ in range(limit):
        pats = []
        while len(pats) < count:
            b = rng.getrandbits(fmt.width)
            if fmt.valid(b) and not isinstance(fmt.decode(b), Special):
                pats.append(b)
        if rng.random() < 0.3:                                          # clustered vectors: close values
            base = pats[0]
            pats = [b if rng.random() < 0.5 else (base ^ rng.getrandbits(2)) for b in pats]
            pats = [b for b in pats if fmt.valid(b) and not isinstance(fmt.decode(b), Special)] or pats
            while len(pats) < count:
                pats.append(pats[0])
        vals = [fmt.decode(b) for b in pats]
        outs, _fls = S.vector_fn(fn, fmt, vals, r, [0] * count)
        env = net.run({f"x{i}": x_of_bits(fmt, b, g) for i, b in enumerate(pats)})
        for i in range(count):
            got, _fl = bits_of_x(fmt, env[f"y{i}"], g, rounding)
            d = abs(fmt.index(got) - fmt.index(outs[i]))
            n_ += 1
            if d:
                wrong += 1
            if d > mx:
                mx = d
                worst = [(tuple(hex(b) for b in pats), hex(outs[i]), hex(got))]
    return {"max_ulp": mx, "n": n_, "wrong": wrong, "worst": worst}


# ---- the value tables over the pattern: direct_lut, compressed_lut ------------------------------
def pattern_sv(fn: str, fmt, family: str, pins: dict, name: str) -> tuple:
    """Build a direct or compressed table from independently evaluated function values."""
    w = fmt.width
    if w > PATTERN_MAX_BITS:
        raise ValueError(f"a value table needs a format of at most {PATTERN_MAX_BITS} bits")
    net = Net(name, f"{fn} on {fmt.name} by the {family} family (a value table over the pattern)")
    net.stage = "evaluator0"
    x = net.port_in("x", w)
    from chialu.targets.rtl.families.sfu_table import table_values, working_precision
    precision = pins.get("_table_precision")
    precision = working_precision(fmt) if precision is None else int(precision)
    vals = table_values(fn, fmt, precision)
    net.notes.append(f"Entries use {precision} bits of working precision and one output rounding.")
    if family == "direct_lut":
        y = net.rom(vals, x, w)
        net.notes.append(f"direct_lut: {1 << w} entries of {w} bits")
    else:
        k = min(3, w - 1)
        hi = net.bits(x, w - 1, k)
        base = [vals[a << k] for a in range(1 << (w - k))]
        deltas = [vals[b] - base[b >> k] for b in range(1 << w)]
        dw = max(2, max(abs(d) for d in deltas).bit_length() + 1)
        B = net.rom(base, hi, w)
        D = net.rom(deltas, x, dw, True)
        s = net.add(net.sgn(B), net.ext(D, w + 1))
        y = net.bits(net.uns(s), w - 1, 0)
        net.notes.append(f"compressed_lut: a base table of {1 << (w - k)} x {w} bits and a delta table of {1 << w} x {dw} bits "
                         f"({(1 << (w - k)) * w + (1 << w) * dw} against {(1 << w) * w} bits)")
    net.port_out("y", y)
    return name, net.render(), net


# ---- the engines of the families ---------------------------------------------------------------
POLY_FAMILIES = ("piecewise_poly", "pwl", "single_poly", "lut_plus_poly", "mixed_degree", "region_dependent",
                 "pwl_residual_lut", "gpu_multifunction_interpolator")


def _poly_kw(family: str, pins: dict) -> dict:
    """The PolyEngine settings of a segmented-polynomial family from its pins."""
    P = lambda k, d: _pin(pins, k, d)  # noqa: E731
    seg = str(P("segmenter.family", "uniform_high_bit_decode"))
    ev = str(P("evaluator.family", "horner"))
    kw = dict(segmenter=seg, evaluator=ev, addressing=str(P("segmenter.addressing", "direct_address_bits")),
              boundary_search=str(P("segmenter.boundary_search", "greedy_error_driven")),
              basis=str(P("basis", "taylor")), encoding=str(P("coeff_encoding", "plain")))
    if family == "piecewise_poly":
        kw.update(K=int(P("segments", 4)), degree=int(P("degree", 1)),
                  joint_search=str(P("coefficient_optimization", "rounded_remez")) == "joint_wordlength_search")
    elif family == "pwl":
        segm = str(P("segmentation", "uniform"))
        selected = {"uniform": "uniform_high_bit_decode", "nonuniform": "nonuniform", "power_of_two": "power_of_two"}[segm]
        if "segmenter.family" in pins and pins["segmenter.family"] != selected:
            raise ValueError(f"pwl segmentation={segm} requires segmenter.family={selected}; "
                             f"got {pins['segmenter.family']}")
        kw.update(K=int(P("segments", 8)), degree=1, coeff_frac=int(P("coeff_frac_bits", 12)), x_frac=int(P("x_frac_bits", 12)),
                  segmenter=selected,
                  encoding={"plain": "plain", "power_of_two": "power_of_two", "signed_po2_pair": "po2_pair", "csd": "csd"}[str(P("slope_encoding", "plain"))])
    elif family == "single_poly":
        kw.update(K=1, degree=int(P("degree", 2)), segmenter="uniform_high_bit_decode")
    elif family == "lut_plus_poly":
        kw.update(K=1 << int(P("index_bits", 5)), degree=int(P("degree", 1)), mult_shape=str(P("multiplier_shape", "full_square")))
    elif family == "mixed_degree":
        kw.update(K=16, degree=int(P("max_degree", 2)), mixed_max_degree=int(P("max_degree", 2)))
    elif family == "region_dependent":
        kw.update(K=4 * int(P("regions", 2)), degree=2, mixed_max_degree=2)
    elif family == "pwl_residual_lut":
        kw.update(K=8, degree=1, residual_bits=int(P("residual_bits", 2)))
    elif family == "gpu_multifunction_interpolator":
        kw.update(K=64, degree=int(P("interpolation_degree", 1)), evaluator=str(P("quadratic_core.family", "horner")),
                  joint_search=str(P("coefficient_precision_grading", "shared")) == "per_function")
    return kw


def polynomial_manifest(pe, family, source, result):
    """Serializable algorithm inputs, separate from the generated dataflow."""
    return {"kind": "segmented_polynomial", "family": family,
            "core": pe.core.name, "input": source.name, "output": result.name,
            "source_width": pe.source_width, "source_fraction_bits": pe.source_fraction_bits,
            "smooth_root": pe.smooth_root, "input_shift": pe.input_shift,
            "input_width": pe.evaluation_input_width, "fraction_bits": pe.Fu,
            "local_fraction_bits": pe.local_fraction_bits, "working_fraction_bits": pe.Fint,
            "output_fraction_bits": pe.Fo, "output_width": result.w,
            "starts": pe.seg.starts, "ends": pe.seg.ends, "shifts": pe.seg.shifts,
            "coefficients": pe.tables, "coefficient_fraction_bits": pe.fq,
            "evaluator": pe.evaluator, "encoding": pe.encoding,
            "basis": pe.basis, "residual": pe.residual_table,
            "coefficient_work_precision": pe.coefficient_work_precision,
            "bound_arithmetic": {kind: {"family": binding[0], "pins": dict(binding[1])}
                                 for kind, binding in pe.net.bind.items()},
            "primitive_assumption": "exact integer add, multiply, shift and leading-zero count; approximate children require a composed contract",
            "coefficient_source": f"families.sfu._fit_poly/{pe.basis}; supplied coefficient and segmentation contract"}


def poly_engine(family: str, pins: dict):
    kw = _poly_kw(family, pins)

    def eng(net: Net, core: Core, u: Ref, Fu: int, Fo: int, label: str) -> Ref:
        pe = PolyEngine(net, core, Fu, Fo, label=label, **kw)
        R = pe.build(u)
        from chialu.targets.rtl.families.fidelity import effective
        if "degree" in pins and pe.degree > 0 and not any(row[pe.degree] for row in pe.tables):
            raise ValueError(f"degree={pe.degree} has a zero leading coefficient in every segment at this geometry; "
                             "increase coefficient or target precision to exercise the requested degree")
        effective(pins, "segments", pe.seg.K, "every segment has a distinct argument interval", {"fraction_bits": pe.Fu})
        effective(pins, "x_frac_bits", min(u.w, pe.x_frac) if pe.x_frac is not None else u.w,
                  "argument bits entering segmentation", {"argument_bits": u.w})
        effective(pins, "coeff_frac_bits", pe.coeff_frac, "coefficient quantization fraction bits")
        effective(pins, "degree", pe.degree, "polynomial coefficient count and evaluator depth")
        effective(pins, "max_degree", max(pe.degs), "highest active regional polynomial degree")
        effective(pins, "segmenter.family", pe.segmenter, "segment boundaries and address circuit")
        effective(pins, "evaluator.family", pe.evaluator, "polynomial evaluation circuit")
        effective(pins, "quadratic_core.family", pe.evaluator, "interpolation evaluation circuit")
        effective(pins, "basis", pe.basis, "coefficient construction")
        effective(pins, "coeff_encoding", pe.encoding, "coefficient representation")
        net.algorithm_contracts.append(polynomial_manifest(pe, family, u, R))
        net.notes += [f"{label}: {family} K={pe.seg.K} degree {max(pe.degs)} {kw['basis']} {kw['encoding']} "
                      f"{kw['segmenter']}/{kw['evaluator']}, {pe.table_bits} table bits"] + [f"{label}: {x}" for x in pe.notes]
        return R
    return eng


def guard_of(family: str, pins: dict) -> int:
    g = int(_pin(pins, "guard_bits", 0)) if family in ("piecewise_poly", "single_poly", "lut_plus_poly") else 0
    if family == "piecewise_poly" and str(_pin(pins, "rounding_contract", "faithful")) == "exact":
        g += 3
    return g + 2


class ActivationEngine(_Engine):
    """The activation-function families: a direct segmented approximation
    of the function over a bounded, folded argument (sigmoid_tanh_pwl)
    or the integer polynomial / learned table of the transformer line."""
    covers = {"sigd", "sigd2", "tanhd", "tanhd2h", "erfd", "gelud", "spd"}
    direct = covers
    CLIP = {"erf": 2, "gelu": 4, "tanh": 2, "sigmoid": 4, "silu": 4, "softplus": 4}

    def clip_T(self, fn: str, T: int) -> int:
        """The integer polynomial's clipped domain (I-BERT clips erf at 1.769 and saturates beyond)."""
        if self.family == "transformer_activation_lut" and str(self.P("method", "integer_polynomial")) == "integer_polynomial":
            return min(T, self.CLIP.get(fn, T))
        return T

    def build(self, n: Net, core: Core, u: Ref, Fu: int, Fo: int) -> tuple:
        notes = []
        source, source_fraction = u, Fu
        fam = self.family
        if fam == "sigmoid_tanh_pwl":
            if core.name not in ("sigd", "sigd2", "tanhd", "tanhd2h"):
                raise ValueError("sigmoid_tanh_pwl serves the sigmoid and tanh")
            approx = str(self.P("approximation", "pwl_segments"))
            K = int(self.P("segments", 3))
            kw = dict(K=K, degree=1, basis="chebyshev", segmenter="uniform_high_bit_decode")
            if approx == "piecewise_quadratic":
                kw.update(degree=2)
            elif approx == "bit_level_mapping":
                kw.update(K=1 << min(Fu, Fo + 1), degree=0)
                notes.append("bit_level_mapping: the output bits as a table over the argument's leading bits")
            elif approx == "shift_add_powers_of_two":
                kw.update(encoding="power_of_two")
            elif approx == "probability_weighted_pwl":
                kw.update(segmenter="nonuniform", boundary_search="quantile", addressing="priority_encoder")
            elif approx == "step_sum":
                kw.update(K=4 * K, degree=0)
                notes.append("step_sum: a staircase of steps (degree 0)")
            if bool(self.P("training_absorbs_error", False)):
                notes.append("training_absorbs_error: no structural effect; the error is reported as measured")
            pe = PolyEngine(n, core, Fu, Fo, label=core.name, **kw)
            R = pe.build(u)
            n.algorithm_contracts.append(polynomial_manifest(pe, fam, source, R))
            notes.append(f"{approx}: K={pe.seg.K} degree {max(pe.degs)}, {pe.table_bits} table bits")
            return R, notes
        # transformer_activation_lut
        method = str(self.P("method", "integer_polynomial"))
        self.notes_extra = []
        operand_format = str(self.P("operand_format", "int8"))
        if operand_format in ("int8", "int16"):
            magnitude_bits = int(operand_format[3:]) - 1
            if u.w < magnitude_bits:
                raise ValueError(f"operand_format={operand_format} needs {magnitude_bits} varying normalized-argument "
                                 f"bits; this target supplies {u.w}")
            removed = u.w - magnitude_bits
            u = n.bits(u, u.w - 1, removed) if removed else u
            Fu -= removed
            notes.append(f"operand_format {operand_format}: signed normalized fixed-point input, "
                         f"{magnitude_bits} magnitude bits over the clipped activation domain")
            from chialu.targets.rtl.families.fidelity import effective
            effective(self.pins, "operand_format", operand_format, "normalized integer input conversion",
                      {"integer_word_bits": magnitude_bits + 1, "fraction_bits": Fu})
        cal = str(self.P("calibration", "analytic_minimax"))
        if method == "integer_polynomial":
            kw = dict(K=1, degree=2, basis="minimax_remez" if cal == "analytic_minimax" else "chebyshev", segmenter="uniform_high_bit_decode")
        else:
            kw = dict(K=8, degree=1, basis="chebyshev", segmenter="nonuniform", addressing="priority_encoder",
                      boundary_search="quantile" if cal == "learned_from_data" else "greedy_error_driven")
        pe = PolyEngine(n, core, Fu, Fo, label=core.name, **kw)
        R = pe.build(u)
        manifest = polynomial_manifest(pe, fam, source, R)
        manifest["source_width"] = source.w
        manifest["source_fraction_bits"] = source_fraction
        manifest["input_shift"] += source.w - u.w
        n.algorithm_contracts.append(manifest)
        notes.append(f"{method} ({cal}): K={pe.seg.K} degree {max(pe.degs)}, {pe.table_bits} table bits")
        return R, notes


class CompositeEngine:
    """A selected engine: unsupported constituent cores are generation errors."""

    def __init__(self, primary: _Engine):
        self.primary = primary
        self.covers = set(primary.covers)
        self.direct = set(primary.direct) & set(primary.covers)
        self.paired_sincos = getattr(primary, "paired_sincos", False)

    def __call__(self, net: Net, core: Core, u: Ref, Fu: int, Fo: int, label: str) -> Ref | tuple[Ref, Ref]:
        if core.name in self.primary.covers:
            return self.primary(net, core, u, Fu, Fo, label)
        raise ValueError(f"{label}: the selected {self.primary.family} family has no {core.name} core")


class StagedEngine:
    """Record each evaluator invocation separately from its surrounding datapath."""

    def __init__(self, engine):
        self.engine = engine

    def __getattr__(self, name):
        return getattr(self.engine, name)

    def __call__(self, net, core, u, Fu, Fo, label):
        net.stage = f"evaluator{net.core_index}"
        net.core_index += 1
        precision = max(_fit_precision.get(), 2 * Fo + Fu + 32)
        token = _fit_precision.set(precision)
        try:
            with mpmath.workprec(precision):
                return self.engine(net, core, u, Fu, Fo, label)
        finally:
            _fit_precision.reset(token)
            net.stage = f"reconstruction{net.core_index}"


ENGINE_CLASSES = {"rational_approximation": RationalEngine, "table_factor_refinement": WongGotoEngine,
                  "logarithmic_converters": LnsEngine, "cordic": CordicEngine, "redundant_high_radix_cordic": CordicEngine,
                  "digit_recurrence_exp_log": DigitRecEngine, "newton_raphson": NewtonEngine, "goldschmidt": NewtonEngine,
                  "sigmoid_tanh_pwl": ActivationEngine, "transformer_activation_lut": ActivationEngine}


def engine_of(family: str, pins: dict, fn: str, fmt):
    """The core evaluator of a family (a callable over the netlist) and its guard bits."""
    if family in POLY_FAMILIES:
        return StagedEngine(poly_engine(family, pins)), guard_of(family, pins)
    if family in TABLE_FAMILIES:
        return StagedEngine(table_engine(family, pins)), 2
    if family in ENGINE_CLASSES:
        primary = ENGINE_CLASSES[family](family, pins)
        if family == "sigmoid_tanh_pwl" and fn not in ("sigmoid", "silu", "tanh"):
            raise ValueError("sigmoid_tanh_pwl serves the sigmoid, silu and tanh")
        return StagedEngine(CompositeEngine(primary)), 3
    raise ValueError(f"sfu family {family!r}: no engine")


ARITH_SLOTS = ("multiplier", "adder", "shifter", "lzc")


def bind_of(pins: dict | None) -> dict:
    """The Net binding of a family's arithmetic slots: kind -> (family, sub-pins) for each slot the pins declare."""
    pins = pins or {}
    out = {}
    for k in ARITH_SLOTS:
        fam = pins.get(f"{k}.family")
        if fam:
            sub = {kk[len(k) + 1:]: v for kk, v in pins.items()
                   if kk.startswith(k + ".") and kk != f"{k}.family"}
            if hasattr(pins, "owner"):
                from chialu.targets.rtl.families.selection import SelectedPins
                sub = SelectedPins(f"{pins.owner}.{k}", sub)
            out[k] = (str(fam), sub)
    return out


def sfu_active_parameters(family: str, pins: dict, functions=()) -> dict:
    """Inactive keys of the selected conditional configuration, with reasons.

    This describes applicability, not generator completeness. Unsupported
    active choices stay in the public space and are reported separately.
    """
    inactive = {}
    def mark(prefix, reason):
        for key in pins:
            if key == prefix or key.startswith(prefix + "."):
                inactive[key] = reason
    segmenter = pins.get("segmenter.family", "uniform_high_bit_decode")
    if segmenter != "nonuniform":
        mark("segmenter.addressing", "addressing selects the nonuniform segmenter's circuit")
        mark("segmenter.boundary_search", "boundary search belongs to the nonuniform segmenter")
    elif pins.get("segmenter.addressing") == "power_of_two_cascade":
        mark("segmenter.boundary_search", "power-of-two boundaries are fixed by the cascade")
    if "range_reducer.family" in pins:
        if functions and not set(functions) & {"sin", "cos"}:
            mark("range_reducer", "the current scalar contract uses this argument reducer for sine/cosine")
        elif pins.get("range_reducer.method", "cody_waite") != "cody_waite":
            mark("range_reducer.split_constant_terms", "split constants are a Cody-Waite construction")
    if family == "sigmoid_tanh_pwl" and pins.get("approximation") == "bit_level_mapping":
        mark("segments", "bit-level mapping uses one entry per retained argument code")
    if family == "softmax_layernorm":
        if pins.get("exp_evaluation", "lut_pwl") != "group_lookup_table":
            mark("lut_group_gating", "group gating applies to group lookup tables")
        if functions and set(functions) == {"layernorm"}:
            for key in ("exp_evaluation", "max_subtraction", "normalization_division"):
                mark(key, "layer normalization uses mean, variance and reciprocal square root")
    if family == "logarithmic_converters" and pins.get("correction", "none") in ("none", "rom_free_shift_add"):
        mark("regions", "this correction circuit has no table regions")
    if family == "nonuniform" and pins.get("addressing") == "power_of_two_cascade":
        mark("boundary_search", "power-of-two boundaries are fixed by the cascade")
    if family == "range_reduction" and pins.get("method", "cody_waite") != "cody_waite":
        mark("split_constant_terms", "split constants are a Cody-Waite construction")
    return inactive


def sfu_incompatible_parameters(family, pins, functions=()):
    """Conflicting choices and unmet target conditions; these cannot be projected away."""
    issues = {}
    if family == "digit_recurrence_exp_log" and pins.get("state_domain") == "complex_bkm" \
            and pins.get("digit_set", "nonredundant") == "nonredundant" and set(functions) & {"sin", "cos"}:
        issues["digit_set"] = "the scale-free unit-circle BKM E-mode requires signed real correction digits"
    if family == "rational_approximation" and pins.get("expression_form") == "decomposed":
        if int(pins.get("numerator_degree", 1)) < int(pins.get("denominator_degree", 1)):
            issues["expression_form"] = "decomposed form requires a nonzero polynomial quotient"
    if family == "redundant_high_radix_cordic" and functions and not set(functions) & {"sin", "cos"}:
        if pins.get("coarse_fine_hybrid"):
            issues["coarse_fine_hybrid"] = "the coarse rotation table needs a sine/cosine target"
    if family == "table_factor_refinement" and pins.get("terminal_correction") == "table_square":
        if int(pins.get("tail_degree", 1)) < 2:
            issues["tail_degree"] = "table-square correction needs a quadratic or higher tail"
    if family == "cordic" and pins.get("coordinate_set") == "unified":
        if pins.get("sharing", "datapath_per_fn") not in ("shared_evaluator", "fully_shared_rom_evaluator"):
            issues["coordinate_set"] = "unified coordinates require a physical evaluator shared across coordinate domains"
        elif functions and len(sfu_coordinate_domains(functions)) < 2:
            issues["coordinate_set"] = "the target must exercise at least two coordinate domains"
    if family == "cordic" and pins.get("mode") == "both" and functions:
        directions = set()
        for function in functions:
            if function in ("sin", "cos", "exp", "exp2", "tanh"):
                directions.add("rotation")
            if function in ("log", "log2", "recip", "sqrt", "rsqrt", "tanh"):
                directions.add("vectoring")
        if len(directions) < 2:
            issues["mode"] = "the target must exercise both rotation and vectoring"
    return issues


def sfu_coordinate_domains(functions):
    domains = {"sin": {"circular"}, "cos": {"circular"}, "exp": {"hyperbolic"},
               "exp2": {"hyperbolic"}, "log": {"hyperbolic"}, "log2": {"hyperbolic"},
               "sqrt": {"hyperbolic"}, "recip": {"linear"},
               "rsqrt": {"hyperbolic", "linear"}, "tanh": {"hyperbolic", "linear"}}
    return set().union(*(domains.get(function, set()) for function in functions))


def sfu_unsupported_parameters(family: str, pins: dict, fmt=None) -> dict:
    """Active declared choices whose named construction is still missing.

    Keeping these in the space makes the support gap visible. Generation
    rejects them rather than substituting an unrelated implementation.
    """
    out = {}
    def choice(key, values, reason):
        if key in pins and pins[key] in values:
            out[key] = reason
    choice("range_reducer.reduction_type", ("multiplicative",), "multiplicative argument reduction is not implemented")
    choice("range_reducer.argument_scaling", ("pi_scaled",), "the pi-scaled reduction path is not implemented")
    choice("range_reducer.worst_case_bound_proven", (True,), "no checked worst-case reduction certificate is attached")
    if family == "rational_approximation":
        choice("evaluation_format", ("floating_point",), "rational evaluation currently uses fixed-point arithmetic")
    if family == "lut_plus_poly":
        choice("breakpoint_placement", ("gal_accurate_points",), "Gal accurate-point breakpoint search is not implemented")
        choice("multiplier_shape", ("rectangular",), "the separate rectangular coefficient multiplier is not implemented")
    if family == "table_factor_refinement":
        choice("multiplier_shape", ("full_square",), "factor products currently use rectangular operands")
        choice("rectangular_multiplier_count", (2,), "two parallel factor multipliers are not implemented")
        choice("function_set", ("atan2", "sine_cosine"), "this refinement engine does not implement this function group")
        choice("unified_hardware", (True,), "use of a unified refinement core has not been implemented")
        choice("tail_evaluator.family", tuple(x for x in _EVALUATORS if x != "horner"), "this tail evaluator is not implemented")
    if family == "gpu_multifunction_interpolator":
        choice("attribute_interpolation_reuse", (True,), "VecSFU has no attribute-interpolation operation interface")
    if family == "cordic":
        choice("angle_recoding", (True,), "recoded angle selection is not implemented")
    if family == "redundant_high_radix_cordic":
        choice("radix", (4,), "the radix-4 redundant recurrence is not implemented")
        choice("scale_handling", ("online_scale_computation", "virtually_scaling_free", "differential_constant_scale"),
               "this scale-repair circuit is not implemented")
    if family == "digit_recurrence_exp_log" and pins.get("state_domain") == "complex_bkm":
        choice("radix", (16,), "radix-16 complex BKM selection/convergence contract is not implemented")
        choice("selection", ("rounding_of_scaled_residual",), "complex BKM rounded selection is not implemented")
    if family == "sigmoid_tanh_pwl":
        choice("training_absorbs_error", (True,), "no trained approximation coefficients are supplied by this contract")
    if family == "transformer_activation_lut":
        choice("calibration", ("learned_from_data",), "learned coefficient data is not supplied by this contract")
        if fmt is not None and pins.get("operand_format") in ("fp16", "bf16") and pins["operand_format"] != fmt.name:
            out["operand_format"] = f"the requested operand format does not match mode format {fmt.name}"
    if family == "softmax_layernorm":
        choice("lut_group_gating", ("input_proximity",), "input-proximity table-bank gating is not implemented")
        choice("passes_over_vector", (2, 3), "the current vector datapath is a single combinational pass")
    return out


def validate_sfu_pins(family, pins, fmt=None, functions=()):
    from chialu.targets.rtl.families.fidelity import inactive, unsupported, require
    from chialu.spaces.sfu_spaces import UNSUPPORTED_SFU_CHOICES
    for key, excluded in UNSUPPORTED_SFU_CHOICES.get(family, {}).items():
        if key in pins and pins[key] in excluded:
            unsupported(pins, key, excluded[pins[key]])
    products = _sfu_schema_products()
    if family not in products:
        raise ValueError(f"unknown SFU family {family!r}")
    # complete() validates a partial selection against every active child
    # family, including each discrete Range member. Defaults are used for
    # validation only; they are not counted as exercised structural choices.
    products[family].complete({key: value for key, value in pins.items() if key != "_table_precision"})
    for key, reason in sfu_active_parameters(family, pins, functions).items():
        inactive(pins, key, reason)
    for key, reason in sfu_unsupported_parameters(family, pins, fmt).items():
        unsupported(pins, key, reason)
    for key, reason in sfu_incompatible_parameters(family, pins, functions).items():
        require(False, key, reason)
    if functions and "function_set" in pins:
        functions = set(functions)
        if family == "gpu_multifunction_interpolator" and pins["function_set"] == "recip_rsqrt_only":
            allowed = {"recip", "rsqrt"}
        elif family == "table_factor_refinement":
            allowed = {"division": {"recip"}, "logarithm": {"log", "log2"},
                       "reciprocal_square_root": {"rsqrt", "sqrt"}, "exponential": {"exp", "exp2"},
                       "atan2": set(), "sine_cosine": {"sin", "cos"}}[pins["function_set"]]
        else:
            allowed = functions
        if not functions <= allowed:
            raise ValueError(f"function_set={pins['function_set']} does not include {sorted(functions - allowed)}")


@lru_cache(maxsize=1)
def _sfu_schema_products():
    from chialu.spaces.sfu_spaces import sfu_approx_space
    from chialu.variants import compile_family
    cache = {}
    return {family.name: compile_family(family, cache) for family in sfu_approx_space(multi_fn=True).families}


def sfu_requirements(family: str, pins: dict | None = None) -> dict:
    """Conservative geometry that keeps declared size parameters observable.

    These requirements deliberately do not count a clipped size as covered.
    A witness still needs generation and simulation; satisfying this function
    alone is not a support or accuracy certificate.
    """
    pins = pins or {}
    precision = max(4, int(pins.get("x_frac_bits", 0)), int(pins.get("index_bits", 0)) + 3,
                    int(pins.get("input_chunk_bits", 0)) + 4)
    segments = int(pins.get("segments", 1))
    degree = max(int(pins.get("degree", 1)), int(pins.get("max_degree", 1)),
                 int(pins.get("numerator_degree", 1)), int(pins.get("denominator_degree", 1)))
    # Local coefficients shrink with segment width and factorial degree.
    # This conservative start avoids declaring a degree covered when its
    # entire leading coefficient table rounds to zero.
    effective_segments = (1 << int(pins.get("index_bits", 0))) if "index_bits" in pins else segments
    precision = max(precision, degree * (max(1, effective_segments) - 1).bit_length()
                    + math.factorial(degree).bit_length() + degree + 2)
    if pins.get("segmentation") == "power_of_two" or pins.get("segmenter.family") == "power_of_two" or pins.get("segmenter.addressing") == "power_of_two_cascade":
        precision = max(precision, segments)
    else:
        precision = max(precision, (segments - 1).bit_length() + int(pins.get("residual_bits", 0)) + 2)
    if family in ("stam", "multipartite"):
        precision = max(precision, 3 * int(pins.get("tables", 2)) + 6)
    if family == "table_factor_refinement":
        precision = max(precision, int(pins.get("factor_bits", 8)) * (int(pins.get("residual_stages", 1)) + 1) + 2)
    if family == "transformer_activation_lut" and pins.get("operand_format", "int8") in ("int8", "int16"):
        precision = max(precision, int(str(pins.get("operand_format", "int8"))[3:]) - 1)
    functions = {"direct_lut": ("exp2", "log2"), "compressed_lut": ("exp2", "log2"),
                 "newton_raphson": ("recip", "rsqrt"), "goldschmidt": ("recip", "rsqrt"),
                 "sigmoid_tanh_pwl": ("sigmoid", "tanh"), "transformer_activation_lut": ("gelu", "silu"),
                 "softmax_layernorm": ("softmax", "layernorm") if pins.get("layernorm_support") else ("softmax",),
                 "cordic": ("sin", "cos"), "redundant_high_radix_cordic": ("sin", "cos"),
                 "digit_recurrence_exp_log": ("exp2", "log2"),
                 "logarithmic_converters": ("exp2", "log2"),
                 "table_factor_refinement": ("recip", "rsqrt")}.get(family, ("exp2", "exp"))
    if family == "gpu_multifunction_interpolator" and pins.get("function_set") == "recip_rsqrt_only":
        functions = ("recip", "rsqrt")
    if family == "table_factor_refinement" and "function_set" in pins:
        functions = {"division": ("recip",), "logarithm": ("log2", "log"),
                     "reciprocal_square_root": ("rsqrt", "sqrt"), "exponential": ("exp2", "exp"),
                     "atan2": (), "sine_cosine": ("sin", "cos")}[pins["function_set"]]
    if family == "rational_approximation" and pins.get("symmetry_form") == "odd":
        functions = ("sin", "cos")
    target_requirements = []
    if family == "digit_recurrence_exp_log" and pins.get("state_domain", "real") == "real":
        radix = int(pins.get("radix", 2))
        minimum_fo = max(3 if radix == 16 and pins.get("selection") == "rounding_of_scaled_residual" else 0,
                         max(0, 3 * (radix.bit_length() - 1) - 5) if pins.get("termination") == "linear_extrapolation" else 0)
        # engine_of supplies three guard bits and p_exp uses Fo=SW+G.
        precision = max(precision, minimum_fo - 3)
        target_requirements.append(f"real exp core output fraction bits >= {minimum_fo}; rounded selector and linear tail require live internal activity")
    if family == "digit_recurrence_exp_log" and pins.get("state_domain") == "complex_bkm":
        functions = ("sin", "cos")
        target_requirements.append("exercise nonzero imaginary states, negative real correction digits, and both quadrant-selected pair outputs")
        if pins.get("index_advance") == "leading_bit_skip":
            target_requirements.append("exercise all nonzero active complex digit pairs (8 at radix2, 24 at radix4), actual zero-pair omissions, and both component index paths")
    if family == "cordic":
        coordinate = pins.get("coordinate_set", "circular")
        mode = pins.get("mode", "rotation")
        functions = {
            ("circular", "rotation"): ("sin", "cos"),
            ("circular", "both"): ("sin", "cos"),
            ("circular", "vectoring"): (),
            ("linear", "rotation"): (),
            ("linear", "vectoring"): ("recip",),
            ("linear", "both"): ("recip",),
            ("hyperbolic", "rotation"): ("exp2", "exp"),
            ("hyperbolic", "vectoring"): ("log2", "sqrt"),
            ("hyperbolic", "both"): ("exp2", "log2"),
            ("unified", "rotation"): ("sin", "exp2"),
            ("unified", "vectoring"): ("log2", "recip"),
            ("unified", "both"): ("sin", "tanh"),
        }[(coordinate, mode)]
        if not functions:
            target_requirements.append(f"the current VecSFU named operations do not exercise {coordinate} {mode}")
        if mode == "both" and coordinate in ("circular", "linear"):
            target_requirements.append(f"the current VecSFU operation contract cannot exercise both directions in {coordinate} coordinates")
        if coordinate == "unified":
            target_requirements.append("a shared physical rotation unit must serve the selected coordinate domains through fn_sel")
    if family == "logarithmic_converters" and pins.get("lns_full_alu"):
        functions = ("recip", "sqrt", "rsqrt")
    if "range_reducer.family" in pins and not set(functions) & {"sin", "cos"}:
        if family in POLY_FAMILIES + TABLE_FAMILIES + ("rational_approximation",):
            functions += ("sin", "cos")
    sharing = pins.get("sharing", "datapath_per_fn")
    internal_fraction = None
    if family == "cordic":
        internal_fraction = int(pins.get("iterations", 16)) + 8
    if family in ("newton_raphson", "goldschmidt"):
        steps = int(pins.get("steps", 1))
        seed_index = max(4, -(-(precision + 7) // (1 << steps)) + 1)
        internal_fraction = (seed_index + 3) * (1 << steps) + 4
    return {"minimum_significand_bits": precision, "minimum_lanes": 2 if family == "softmax_layernorm" else 1,
            "minimum_functions": 2 if sharing != "datapath_per_fn" else 1,
            "functions": functions, "maximum_pattern_bits": PATTERN_MAX_BITS if family in PATTERN_FAMILIES else None,
            "inactive": sfu_active_parameters(family, pins, functions),
            "incompatible": sfu_incompatible_parameters(family, pins, functions),
            "unsupported": sfu_unsupported_parameters(family, pins),
            "target_requirements": target_requirements,
            "minimum_internal_fraction_bits": internal_fraction,
            "criterion": "parameters must remain untruncated in the generated circuit"}


def sfu_module_name(fn: str, fmt, family: str, pins: dict | None = None) -> str:
    """The module name of a family for a function on a format; a tag of the pins when any are declared
    (two pin sets render two texts)."""
    base = f"fam_sfu_{family}_{fn}_{fmt.name.replace('.', '_')}"
    if not pins:
        return base
    import hashlib
    return f"{base}_{hashlib.blake2b(repr(sorted((str(k), str(v)) for k, v in pins.items())).encode(), digest_size=6).hexdigest()}"


def sfu_sv(fn: str, fmt, g: Geom, family: str, pins: dict | None = None, name: str | None = None) -> tuple:
    """(name, text, net) of the family's module for one function on one
    format at the engine geometry."""
    pins = pins or {}
    validate_sfu_pins(family, pins, fmt)
    name = name or sfu_module_name(fn, fmt, family, pins)
    if family in PATTERN_FAMILIES:
        name, text, net = pattern_sv(fn, fmt, family, pins, name)
    else:
        eng, guard = engine_of(family, pins, fn, fmt)
        bind = bind_of(pins)
        net = Net(name, f"{fn} on {fmt.name} by the {family} family (X in, X out; the seed packs and handles the specials)"
                  + ("; " + ", ".join(f"the {k} slot {v[0]}" for k, v in bind.items()) if bind else ""), bind=bind)
        lane = Lane(net, g, fmt, fn, eng, guard=guard, pins=pins)
        lane.build()
        net.notes += lane.notes
        net.lane = lane
        text = net.render()
    from chialu.targets.rtl.families.selection import register_origin
    register_origin(getattr(pins, "owner", None), family, pins, name, text)
    return name, text, net


# ---- the model: patterns in, patterns out, against the verify layer's reference ------------------
def x_of_bits(fmt, bits: int, g: Geom) -> int:
    """The X word of a pattern as the seed's unpacker produces it (the
    stored significand at the low bits, the exponent of bit 0)."""
    from chialu.verify.formats import NAN, NAR, NINF, PINF, Special
    c = _fmt_core(fmt)
    XW, EW, XT = g.XW, g.EW, g.XT
    sp = s = e = sig = 0
    if isinstance(c, PositFormat):
        v = c.decode(bits)
        if v is NAR:
            sp = 1
        elif v != 0:
            s = 1 if v < 0 else 0
            a = abs(v)
            from chialu.verify.formats import _floor_log2
            e = _floor_log2(a) - (c.width - 1)
            sig = int(a / Fraction(2) ** e)
    else:
        M, E, bias = c.man_bits, c.exp_bits, c.bias
        m = bits & _mask(M)
        ef = (bits >> M) & _mask(E)
        s = (bits >> (M + E)) & 1 if c.signed else 0
        v = c.decode(bits)
        if v is NAN:
            sp = 1
        elif v in (PINF, NINF):
            sp = 2
        elif ef == 0:
            sig, e = m, 1 - bias - M
        else:
            sig, e = m | (1 << M), ef - bias - M
    return (sp << (XT - 2)) | (s << (XT - 3)) | ((e & _mask(EW)) << (XW + 1)) | (sig << 1)


def bits_of_x(fmt, y: int, g: Geom, rounding: str = "RNE", inv: int = 0, dz: int = 0) -> tuple:
    """(pattern, flags) of an output X under a rounding mode, the way the
    engine's pack rounds it (a set sticky stands for a value half an X
    lsb above)."""
    from chialu.verify.formats import NAN, NINF, PINF, NAR
    from chialu.verify.rounding import Rounder
    XW, EW, XT = g.XW, g.EW, g.XT
    sp = (y >> (XT - 2)) & 3
    s = (y >> (XT - 3)) & 1
    e = _wrap((y >> (XW + 1)) & _mask(EW), EW, True)
    sig = (y >> 1) & _mask(XW)
    st = y & 1
    c = _fmt_core(fmt)
    posit = isinstance(c, PositFormat)
    r = Rounder(rounding, 8)
    fl = set()
    if inv:
        fl.add("invalid")
    if dz:
        fl.add("div_zero")
    if sp == 1:
        b, f = (c._nar, {"nan"}) if posit else r.float(c, NAN, 0, 0)
        return b, fl | f
    if sp == 2:
        if posit:
            return c._nar, fl | {"nan"}
        b, f = r.float(c, NINF if s else PINF, 0, 0)
        return b, fl | f
    v = Fraction(2 * sig + st) * Fraction(2) ** (e - 1)
    if s:
        v = -v
    if posit:
        b, f = r.posit(c, v)
    else:
        b, f = r.float(c, v, 0, s)
    return b, fl | f


_REF_CACHE: dict = {}


def reference_bits(fn: str, fmt, bits: int, rounding: str = "RNE") -> int:
    """The verify layer's correctly rounded result of fn at a pattern."""
    from chialu.verify import sfu_ref as S
    from chialu.verify.rounding import Rounder
    key = (fn, fmt.name, rounding)
    cache = _REF_CACHE.setdefault(key, {})
    if bits in cache:
        return cache[bits]
    r = Rounder(rounding, 8)
    posit = isinstance(_fmt_core(fmt), PositFormat)
    if posit:
        v, s = fmt.decode(bits), 0
    else:
        v, s, _den = S._read(fmt, bits, False)
    val, _fl = S.fn_value(fn, fmt, v, s)
    if fn == "softplus" and isinstance(val, tuple) and isinstance(v, Fraction) and v > 4:
        # the verify layer's tail surrogate returns +huge for softplus above (log2 max + 2) ln 2, which is
        # exp's asymptote; softplus(x) tends to x there, so the library measures against the exact value
        from chialu.verify.ops import _mp
        with mpmath.workprec(fmt.width * 3 + 60):
            exact = _mp("softplus", v, fmt.width * 3 + 60)
        b, _f2 = S._round_out(fmt, exact, r, 0)
    else:
        b, _f2 = S.resolve(fmt, val, r, 0, s if fn in ("sin", "tanh", "erf", "gelu", "silu", "sqrt") else 0)
    cache[bits] = b
    return b


def measure(fn: str, fmt, g: Geom, net: Net, rounding: str = "RNE", limit: int | None = None, seed: int = 1) -> dict:
    """The model's error against the reference over every pattern of a
    format up to 16 bits (a random sample of `limit` otherwise): max ulp
    (the format-ordered index distance), the count of inexact results and
    the worst cases."""
    import random
    from chialu.verify.formats import Special
    c = _fmt_core(fmt)
    rng = random.Random(seed)
    if fmt.width <= 16 and (limit is None or limit >= (1 << fmt.width)):
        pats = range(1 << fmt.width)
    else:
        pats = [rng.getrandbits(fmt.width) for _ in range(limit or 4096)]
    worst = []
    mx, n, wrong = 0, 0, 0
    for b in pats:
        if not fmt.valid(b):
            continue
        v = fmt.decode(b)
        if isinstance(v, Special):
            continue
        if net.ports[0][1].w == fmt.width:            # a value table over the pattern
            got = net.run({"x": b})["y"]
        else:
            env = net.run({"x": x_of_bits(fmt, b, g)})
            got, _fl = bits_of_x(fmt, env["y"], g, rounding, env.get("inv", 0), env.get("dz", 0))
        exp = reference_bits(fn, fmt, b, rounding)
        d = abs(fmt.index(got) - fmt.index(exp))
        n += 1
        if d:
            wrong += 1
        if d > mx or (d == mx and d and len(worst) < 3):
            if d > mx:
                worst = []
            mx = d
            worst.append((b, exp, got))
    return {"max_ulp": mx, "n": n, "wrong": wrong, "worst": worst[:3]}


def main(argv=None) -> int:
    import argparse
    from chialu.targets.rtl.engine import Conventions, Engine
    from chialu.verify.formats import parse_format
    ap = argparse.ArgumentParser(description="emit a special-function family's module and its modeled error")
    ap.add_argument("--function", required=True)
    ap.add_argument("--format", default="fp16")
    ap.add_argument("--family", default="piecewise_poly")
    ap.add_argument("--pins", default="", help="k=v,... (the family's choices; component families as slot.family=...)")
    ap.add_argument("--count", type=int, default=4, help="lanes of a vector function")
    ap.add_argument("--limit", type=int, default=2000, help="sampled patterns above 16 bits")
    ap.add_argument("--no-measure", action="store_true")
    ap.add_argument("--sv", default=None, help="write the module here instead of stdout")
    args = ap.parse_args(argv)
    pins = {}
    for kv in args.pins.split(","):
        if "=" in kv:
            k, v = kv.split("=", 1)
            pins[k.strip()] = v.strip()
    fmt = parse_format(args.format)
    e = Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions())
    g = Geom.of_engine(e)
    if args.function in ("softmax", "layernorm"):
        name, text, net = vector_sv(args.function, fmt, g, args.count, args.family, pins)
        r = None if args.no_measure else measure_vector(args.function, fmt, g, args.count, net, limit=min(args.limit, 400))
    else:
        name, text, net = sfu_sv(args.function, fmt, g, args.family, pins)
        r = None if args.no_measure else measure(args.function, fmt, g, net, limit=args.limit)
    if r is not None:
        text = f"// modeled error against the reference: max {r['max_ulp']} ulp, {r['wrong']} of {r['n']} results inexact\n" + text
    if args.sv:
        from pathlib import Path
        Path(args.sv).write_text(text)
    else:
        print(text)
    if r is not None:
        print(f"// {name}: max_ulp {r['max_ulp']} wrong {r['wrong']}/{r['n']} worst {r['worst']}", file=__import__("sys").stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
