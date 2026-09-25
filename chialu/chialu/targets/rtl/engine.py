"""SystemVerilog generator for the behavioral reference datapath of a
chialu.ALU spec: the seed (`alu_core`) and the duplicate the checker
compares against are the same generated logic.

One engine per mode. A value is (special, sign, exp, sig): value =
(-1)^sign x sig x 2^exp, sig an unsigned SW-bit integer (V type); an
intermediate result adds guard bits and a sticky bit (X type). The
functions per engine:

  unpack_*   pattern -> V (floats, posits, integers, block elements)
  add/mul/div/sqrt   X x X -> X (exact up to the sticky bit)
  pack_*     X -> {flags, pattern} under the rounding mode, the SR word,
             ftz; float, posit, integer/fixed and block targets
  quant_*    X[size] -> one block (the section 2.6 rule)

Rounding mode codes: 0 RNE, 1 RTZ, 2 RDN, 3 RUP, 4 SR, 5 away from zero
(the checker's one-ulp window). Flag bits: FLAG_ORDER below.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from chialu.verify.formats import (BCDFormat, BlockFormat, FixedFormat,
                                    FloatFormat, IntFormat, PositFormat,
                                    ScaledIntFormat, X87Format, _floor_log2)

FLAG_ORDER = ("invalid", "div_zero", "overflow", "underflow", "inexact",
              "nan", "denormal", "carry", "int_overflow", "unordered")
FW = len(FLAG_ORDER)
RND = {"RNE": 0, "RTZ": 1, "RDN": 2, "RUP": 3, "SR": 4}
# forced rounding of a reference copy: none (the rnd input), toward zero
# (code 1) or away from zero (code 5): the two ends of the one-ulp window
# the checker accepts for an unchecked stochastic rounding
FORCE_NONE, FORCE_RTZ, FORCE_RAZ = 0, 1, 2
FORCE_RND_EXPR = {FORCE_NONE: "rnd_sel", FORCE_RTZ: "3'd1", FORCE_RAZ: "3'd5"}


def fmt_tag(fmt) -> str:
    """A format name as an SV identifier fragment."""
    return "".join(ch if ch.isalnum() else "_" for ch in fmt.name)


@dataclass(frozen=True)
class Conventions:
    """The convention options (spec section 3.9) an engine renders into
    its functions: each becomes one template token, bound once at
    construction."""
    nan_payload: str = "canonical"
    invalid_result: str = "saturate"
    nan_to_int: str = "zero"
    minmax_nan: str = "propagate"
    tininess: str = "after"
    int_div_zero: str = "riscv"
    zero_sign: str = "positive"
    block_scale_rounding: str = "nearest"
    block_element_overflow: str = "saturate"
    sr_compare: str = "gt"

    @classmethod
    def from_spec(cls, spec: dict) -> "Conventions":
        names = cls.__dataclass_fields__
        return cls(**{k: spec[k] for k in names if k in spec and spec[k] is not None})

    def tokens(self) -> dict:
        return {"ZERO_POSITIVE": "1" if self.zero_sign == "positive" else "0",
                "SRGE": "1" if self.sr_compare == "ge" else "0",
                "TININESS_BEFORE": "1" if self.tininess == "before" else "0",
                "NANTOINT": {"zero": "0", "max": "1", "min": "2"}[self.nan_to_int],
                "SCALE_RUP": "1" if self.block_scale_rounding == "up" else "0",
                "ELEM_INF": "1" if self.block_element_overflow == "inf" else "0",
                "INVZERO": "1" if self.invalid_result == "zero" else "0"}


def flag_bit(name):
    return FLAG_ORDER.index(name)


def _core(fmt):
    return fmt.core if isinstance(fmt, X87Format) else fmt


def _sub(text: str, **kw) -> str:
    for k, v in kw.items():
        text = text.replace(f"@{k}@", str(v))
    return text


class Engine:
    """The SV function library of one mode (prefix `p`)."""

    def __init__(self, p: str, fmt, sr_bits: int, sr: bool, targets=(),
                 conv: Conventions | None = None, tight: bool = False):
        self.p = p
        self.fmt = fmt
        self.sr_bits = sr_bits
        self.sr = sr
        # tight: the guard-round-sticky X of a float mode (the unit option x_form): SW + 3 significand
        # bits and the sticky rather than the exact product's 2 SW + 4, and an exponent of exp_bits + 3 rather
        # than + 8; a producer folds what lies below into the sticky, which the IEEE modes round exactly from
        self.tight = bool(tight)
        self.conv = conv or Conventions()
        self.tokens = self.conv.tokens()
        base = fmt.elem if isinstance(fmt, BlockFormat) else fmt
        # significand and exponent widths of the mode's values
        if isinstance(fmt, BlockFormat):
            sc = fmt.scale
            if isinstance(fmt.elem, FloatFormat):
                sw = fmt.elem.man_bits + 1 + sc.man_bits + 1
                ew = max(fmt.elem.exp_bits, sc.exp_bits) + 8
            else:
                sw = fmt.elem.width + sc.man_bits + 1
                ew = sc.exp_bits + 8
        elif isinstance(base, (FloatFormat, X87Format)):
            c = _core(base)
            sw = c.man_bits + 1
            ew = c.exp_bits + (3 if self.tight else 8)
        elif isinstance(base, PositFormat):
            sw = base.width
            ew = base.es + (base.width - 1).bit_length() + 6
        else:                                   # integer, fixed
            sw = base.width + 1
            ew = 8 + (getattr(base, "frac_bits", 0)).bit_length()
        mt = 0
        for t in targets:
            tc = t.elem if isinstance(t, BlockFormat) else t
            tc = _core(tc)
            mt = max(mt, getattr(tc, "man_bits", 0) + 2, getattr(tc, "width", 0) + 2)
            if isinstance(t, BlockFormat):
                # the quantizer into a block target unpacks and packs the target's
                # scale, so the significand width carries the target's element and
                # its scale together, by the rule the source-block branch applies
                if isinstance(t.elem, FloatFormat):
                    sw = max(sw, t.elem.man_bits + 1 + t.scale.man_bits + 1)
                else:
                    sw = max(sw, t.elem.width + t.scale.man_bits + 1)
            if isinstance(t, BlockFormat) and isinstance(t.scale, FloatFormat):
                ew = max(ew, t.scale.exp_bits + 8)
            if isinstance(tc, (FloatFormat,)):
                ew = max(ew, tc.exp_bits + (3 if self.tight else 8))
        self.SW = sw
        self.EW = ew
        self.XW = max(self.x_sig(sw), mt + 4) + (sr_bits + 2 if sr else 0)
        self.VW = 3 + ew + sw
        self.XT = 3 + ew + self.XW + 1

    def x_sig(self, sw: int) -> int:
        """The X significand bits a stored significand of `sw` bits needs: the
        exact product and its guard under the exact form, the kept bits with
        guard and round under the tight one (the sticky is the X's own bit)."""
        return sw + 3 if self.tight else 2 * sw + 4

    def widen(self, sw: int):
        """Grow the significand width (a second operand format)."""
        if sw > self.SW:
            self.SW = sw
            self.XW = max(self.XW, self.x_sig(sw) + (self.sr_bits + 2 if self.sr else 0))
            self.VW = 3 + self.EW + self.SW
            self.XT = 3 + self.EW + self.XW + 1

    def widen_exp(self, ew: int):
        if ew > self.EW:
            self.EW = ew
            self.VW = 3 + self.EW + self.SW
            self.XT = 3 + self.EW + self.XW + 1

    def sub(self, text: str, **kw) -> str:
        """Render a template: the convention tokens, then the call's own."""
        return _sub(text, **{**self.tokens, **kw})

    # -- layout helpers ---------------------------------------------------
    def vdecl(self):
        p = self.p
        return self.sub('''
  // ---- @P@: V = {special[1:0], sign, exp[@EW@] (signed), sig[@SW@]}
  //           X = {special[1:0], sign, exp[@EW@] (signed), sig[@XW@], sticky}
  localparam int @P@_SW = @SW@, @P@_EW = @EW@, @P@_XW = @XW@;
  localparam int @P@_VW = @VW@, @P@_XT = @XT@;
  function automatic [@VWm@:0] @P@_mkv(input [1:0] sp, input s, input signed [@EWm@:0] e, input [@SWm@:0] sig);
    @P@_mkv = {sp, s, e, sig};
  endfunction
  function automatic [@XTm@:0] @P@_mkx(input [1:0] sp, input s, input signed [@EWm@:0] e, input [@XWm@:0] sig, input st);
    @P@_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [@XTm@:0] @P@_x(input [@VWm@:0] v);   // widen V to X
    @P@_x = {v[@VWm@:@VWm@-1], v[@VWm@-2], v[@VWm@-3 -: @EW@], {{(@XW@-@SW@){1'b0}}, v[@SWm@:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [@XTm@:0] @P@_norm(input [@XTm@:0] x);
    logic [@XWm@:0] s; logic signed [@EWm@:0] e; integer k;
    s = x[@XW@:1]; e = x[@XW@+@EW@:@XW@+1];
    if (s != 0) begin
      for (k = @NORM_START@; k >= 1; k = k / 2) begin
        if (k < @XW@) begin
          if (s[@XWm@ -: 1] == 1'b0 && (s >> (@XW@ - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    @P@_norm = {x[@XTm@:@XTm@-1], x[@XTm@-2], e, s, x[0]};
  endfunction
''', P=p, EW=self.EW, EWm=self.EW - 1, SW=self.SW, SWm=self.SW - 1,
                    XW=self.XW, XWm=self.XW - 1, VW=self.VW, VWm=self.VW - 1,
                    XT=self.XT, XTm=self.XT - 1, NORM_START=1 << ((self.XW - 1).bit_length() - 1))

    def x_fields(self, x):
        """SV slices of an X expression: (special, sign, exp, sig, sticky)."""
        XT, XW, EW = self.XT, self.XW, self.EW
        return (f"{x}[{XT-1}:{XT-2}]", f"{x}[{XT-3}]",
                f"{x}[{XW+EW}:{XW+1}]", f"{x}[{XW}:1]", f"{x}[0]")

    # -- arithmetic ------------------------------------------------------
    def arith(self):
        p = self.p
        XW, EW, XT = self.XW, self.EW, self.XT
        return self.sub('''
  // a +/- b on X (normalized inputs); specials: nan wins, inf-inf = nan
  function automatic [@XTm@:0] @P@_add(input [@XTm@:0] a, input [@XTm@:0] b, input sub);
    logic [@XTm@:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [@EWm@:0] ea, eb, d; logic [@XW@:0] ms, mb, r; logic st, stb; integer sh;
    na = @P@_norm(a); nb = @P@_norm(b);
    spa = na[@XTm@:@XTm@-1]; spb = nb[@XTm@:@XTm@-1];
    sa = na[@XTm@-2]; sb = nb[@XTm@-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) @P@_add = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) @P@_add = (sa == sb) ? @P@_mkx(2'd2, sa, 0, 0, 1'b0) : @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) @P@_add = @P@_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) @P@_add = @P@_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[@XW@:1] == 0 && !na[0]) @P@_add = {nb[@XTm@:@XTm@-1], sb, nb[@XTm@-3:0]};
    else if (nb[@XW@:1] == 0 && !nb[0]) @P@_add = na;
    else begin
      ea = na[@XW@+@EW@:@XW@+1]; eb = nb[@XW@+@EW@:@XW@+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[@XW@:1] >= nb[@XW@:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[@XW@+@EW@:@XW@+1] - sml[@XW@+@EW@:@XW@+1];
      ms = {1'b0, sml[@XW@:1]}; stb = sml[0];
      if (d > @XW@ + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < @XW@ + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[@XW@:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[@XW@]) begin st = st | r[0]; r = r >> 1; @P@_add = @P@_mkx(2'd0, sr, big[@XW@+@EW@:@XW@+1] + 1, r[@XWm@:0], st); end
      else @P@_add = @P@_mkx(2'd0, sr, big[@XW@+@EW@:@XW@+1], r[@XWm@:0], st);
    end
  endfunction
  function automatic [@XTm@:0] @P@_mul(input [@XTm@:0] a, input [@XTm@:0] b);
    logic [@XTm@:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*@XW@-1:0] pr; logic st; integer k;
    na = @P@_norm(a); nb = @P@_norm(b);
    spa = na[@XTm@:@XTm@-1]; spb = nb[@XTm@:@XTm@-1]; s = na[@XTm@-2] ^ nb[@XTm@-2];
    if (spa == 2'd1 || spb == 2'd1) @P@_mul = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[@XW@:1] == 0 && !na[0]) || (spb == 2'd0 && nb[@XW@:1] == 0 && !nb[0]))
        @P@_mul = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else @P@_mul = @P@_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[@XW@:1] * nb[@XW@:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[@XWm@:0] != 0);
      @P@_mul = @P@_mkx(2'd0, s, na[@XW@+@EW@:@XW@+1] + nb[@XW@+@EW@:@XW@+1] + @XW@, pr[2*@XW@-1:@XW@], st);
    end
  endfunction
  // restoring division (a << XW) / dv of two XW-bit significands with dv
  // normalized (dv >= 2^(XW-1)): {q[XW:0], r[XW:0]}, XW+1 quotient bits.
  // The first step compares a itself (the partial remainder after the
  // dividend's top XW bits: with dv normalized no earlier step can
  // subtract, so those steps are omitted), then one step per zero bit
  // shifted in. Every step assigns r and q unconditionally (a ternary on
  // the compare): the loop unrolls into straight-line logic rather than
  // a chain of if/else switches in one process, which yosys's latch
  // analysis (proc_dlatch) never finishes on
  function automatic [2*@XW@+1:0] @P@_udiv(input [@XWm@:0] a, input [@XWm@:0] dv);
    logic [@XW@+1:0] r; logic [@XW@:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = @XW@; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[@XWm@:0], ge};
      if (i > 0) r = {r[@XW@:0], 1'b0};
    end
    @P@_udiv = {q, r[@XW@:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*@XW@+@EW@+2:0] @P@_mulx(input [@XTm@:0] a, input [@XTm@:0] b);
    logic [@XTm@:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*@XW@-1:0] pr;
    na = @P@_norm(a); nb = @P@_norm(b);
    pr = na[@XW@:1] * nb[@XW@:1];
    spa = na[@XTm@:@XTm@-1]; spb = nb[@XTm@:@XTm@-1]; s = na[@XTm@-2] ^ nb[@XTm@-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[@XW@:1] == 0) || (spb == 2'd0 && nb[@XW@:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    @P@_mulx = {sp, s, na[@XW@+@EW@:@XW@+1] + nb[@XW@+@EW@:@XW@+1], pr};
  endfunction
  function automatic [@XTm@:0] @P@_div(input [@XTm@:0] a, input [@XTm@:0] b);
    logic [@XTm@:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*@XW@+1:0] qr; logic [@XW@:0] q, r;
    na = @P@_norm(a); nb = @P@_norm(b);
    spa = na[@XTm@:@XTm@-1]; spb = nb[@XTm@:@XTm@-1]; s = na[@XTm@-2] ^ nb[@XTm@-2];
    if (spa == 2'd1 || spb == 2'd1) @P@_div = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) @P@_div = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) @P@_div = @P@_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) @P@_div = @P@_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[@XW@:1] == 0 && !nb[0]) begin
      if (na[@XW@:1] == 0 && !na[0]) @P@_div = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else @P@_div = @P@_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[@XW@:1] == 0 && !na[0]) @P@_div = @P@_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = @P@_udiv(na[@XW@:1], nb[@XW@:1]);     // both normalized: nonzero finite
      q = qr[2*@XW@+1:@XW@+1]; r = qr[@XW@:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[@XW@]) @P@_div = @P@_mkx(2'd0, s, na[@XW@+@EW@:@XW@+1] - nb[@XW@+@EW@:@XW@+1] - @XW@ + 1, q[@XW@:1], (r != 0) | q[0] | na[0] | nb[0]);
      else @P@_div = @P@_mkx(2'd0, s, na[@XW@+@EW@:@XW@+1] - nb[@XW@+@EW@:@XW@+1] - @XW@, q[@XWm@:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [@XTm@:0] @P@_sqrt(input [@XTm@:0] a);
    logic [@XTm@:0] na; logic [1:0] spa; logic signed [@EWm@:0] e; logic [@XW@:0] m; logic [2*@XW@+3:0] rad;
    logic [@XW@+2:0] rem, trial; logic [@XW@:0] root; logic ge; integer i;
    na = @P@_norm(a); spa = na[@XTm@:@XTm@-1];
    if (spa == 2'd1) @P@_sqrt = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) @P@_sqrt = na[@XTm@-2] ? @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[@XW@:1] == 0 && !na[0]) @P@_sqrt = na;
    else if (na[@XTm@-2]) @P@_sqrt = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[@XW@+@EW@:@XW@+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[@XW@:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[@XW@:1]};
      rad = {{(@XW@+3){1'b0}}, m} << @SQK2@;
      rem = 0; root = 0;
      for (i = @XW@; i >= 0; i = i - 1) begin
        rem = {rem[@XW@:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[@XWm@:0], ge};
      end
      @P@_sqrt = @P@_mkx(2'd0, 1'b0, (e >>> 1) - @SQK@ + 1, root[@XW@:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic @P@_lt(input [@XTm@:0] a, input [@XTm@:0] b);
    logic [@XTm@:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [@EWm@:0] ea, eb;
    na = @P@_norm(a); nb = @P@_norm(b);
    za = (na[@XW@:1] == 0) && !na[0]; zb = (nb[@XW@:1] == 0) && !nb[0];
    sa = na[@XTm@-2] && !za; sb = nb[@XTm@-2] && !zb;
    if (na[@XTm@:@XTm@-1] == 2'd1 || nb[@XTm@:@XTm@-1] == 2'd1) @P@_lt = 1'b0;
    else if (na[@XTm@:@XTm@-1] == 2'd2 || nb[@XTm@:@XTm@-1] == 2'd2) begin
      if (na[@XTm@:@XTm@-1] == 2'd2 && nb[@XTm@:@XTm@-1] == 2'd2) @P@_lt = na[@XTm@-2] && !nb[@XTm@-2];
      else if (na[@XTm@:@XTm@-1] == 2'd2) @P@_lt = na[@XTm@-2];
      else @P@_lt = !nb[@XTm@-2];
    end else if (za && zb) @P@_lt = 1'b0;
    else if (sa != sb) @P@_lt = sa;
    else begin
      ea = na[@XW@+@EW@:@XW@+1]; eb = nb[@XW@+@EW@:@XW@+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[@XW@:1] < nb[@XW@:1] || (na[@XW@:1] == nb[@XW@:1] && !na[0] && nb[0])));
      @P@_lt = sa ? !mag_lt && !(za && zb) && !@P@_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic @P@_eq(input [@XTm@:0] a, input [@XTm@:0] b);
    logic [@XTm@:0] na, nb; logic za, zb;
    na = @P@_norm(a); nb = @P@_norm(b);
    za = (na[@XW@:1] == 0) && !na[0]; zb = (nb[@XW@:1] == 0) && !nb[0];
    if (na[@XTm@:@XTm@-1] == 2'd1 || nb[@XTm@:@XTm@-1] == 2'd1) @P@_eq = 1'b0;
    else if (na[@XTm@:@XTm@-1] == 2'd2 || nb[@XTm@:@XTm@-1] == 2'd2)
      @P@_eq = (na[@XTm@:@XTm@-1] == nb[@XTm@:@XTm@-1]) && (na[@XTm@-2] == nb[@XTm@-2]);
    else if (za || zb) @P@_eq = za && zb;
    else @P@_eq = (na[@XTm@-2] == nb[@XTm@-2]) && (na[@XW@+@EW@:@XW@+1] == nb[@XW@+@EW@:@XW@+1]) && (na[@XW@:1] == nb[@XW@:1]) && (na[0] == nb[0]);
  endfunction
''', P=p, XW=XW, XWm=XW - 1, EW=EW, EWm=EW - 1, XT=XT, XTm=XT - 1,
                    SQK=(XW + 1) // 2, SQK2=2 * ((XW + 1) // 2))

    def fma_fn(self):
        """fma(a, b, c, np, nc) on X: the fused multiply-add of a float
        mode with a fused op, which the behavioral realization and the
        checker's reference copy compute with (a mode without one does not
        declare it)."""
        return self.sub('''
  // the fused multiply-add (-1)^np * a * b + (-1)^nc * c, rounded once: the
  // exact 2 XW-bit product and c (its significand at the product's scale)
  // meet in a 2 XW + 2-bit frame, the smaller aligned right with a sticky,
  // and the sum or difference normalizes to the X (the top XW bits, the
  // rest sticky). The specials as IEEE 754 orders them: a NaN operand, an
  // invalid product (inf * 0), an infinite product against the opposite
  // infinite addend, an infinite product, an infinite addend. An exact zero
  // leaves with sign 0 (the caller applies the zero-sign rule); the
  // operands' own stickies fold into the result's (the ALU's unpacked
  // operands carry none).
  function automatic [@XTm@:0] @P@_fma(input [@XTm@:0] a, input [@XTm@:0] b, input [@XTm@:0] c, input np, input nc);
    logic [@XTm@:0] na, nb, ncc; logic [1:0] spa, spb, spc; logic sp, sc, sr, sbig, ssml, a_zero, b_zero, c_zero, neg;
    logic signed [@EWm@:0] ea, eb, ec, ep, ecw, ebase; logic signed [@EW@+1:0] d;
    logic [2*@XW@-1:0] pr; logic [2*@XW@+1:0] mp, mc, big, sml, r; logic stp, stc, stb, sts, st; integer sh, k;
    na = @P@_norm(a); nb = @P@_norm(b); ncc = @P@_norm(c);
    spa = na[@XTm@:@XTm@-1]; spb = nb[@XTm@:@XTm@-1]; spc = ncc[@XTm@:@XTm@-1];
    sp = na[@XTm@-2] ^ nb[@XTm@-2] ^ np; sc = ncc[@XTm@-2] ^ nc;
    a_zero = (spa == 2'd0) && na[@XW@:1] == 0 && !na[0]; b_zero = (spb == 2'd0) && nb[@XW@:1] == 0 && !nb[0];
    c_zero = (spc == 2'd0) && ncc[@XW@:1] == 0 && !ncc[0];
    if (spa == 2'd1 || spb == 2'd1 || spc == 2'd1) @P@_fma = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 && b_zero) || (spb == 2'd2 && a_zero)) @P@_fma = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 || spb == 2'd2) && spc == 2'd2 && sp != sc) @P@_fma = @P@_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) @P@_fma = @P@_mkx(2'd2, sp, 0, 0, 1'b0);
    else if (spc == 2'd2) @P@_fma = @P@_mkx(2'd2, sc, 0, 0, 1'b0);
    // an exact zero product (a zero operand's exponent means nothing): the addend, with its negation
    else if (a_zero || b_zero) @P@_fma = c_zero ? @P@_mkx(2'd0, 1'b0, 0, 0, 1'b0) : {ncc[@XTm@:@XTm@-1], sc, ncc[@XTm@-3:0]};
    else begin
      ea = na[@XW@+@EW@:@XW@+1]; eb = nb[@XW@+@EW@:@XW@+1]; ec = ncc[@XW@+@EW@:@XW@+1];
      pr = na[@XW@:1] * nb[@XW@:1]; mp = {2'b00, pr}; stp = na[0] | nb[0]; ep = ea + eb;
      mc = {2'b00, ncc[@XW@:1], {@XW@{1'b0}}}; stc = ncc[0]; ecw = ec - @XW@;
      d = $signed({{2{ep[@EWm@]}}, ep}) - $signed({{2{ecw[@EWm@]}}, ecw});
      // a zero addend (its exponent means nothing): the product stays in place
      if (c_zero) begin big = mp; sml = 0; sbig = sp; ssml = sp; stb = stp; sts = 1'b0; ebase = ep; d = 0; end
      else if (d >= 0) begin big = mp; sml = mc; sbig = sp; ssml = sc; stb = stp; sts = stc; ebase = ep; end
      else begin big = mc; sml = mp; sbig = sc; ssml = sp; stb = stc; sts = stp; ebase = ecw; d = -d; end
      if (d > 2*@XW@ + 2) begin sts = sts | (sml != 0); sml = 0; end
      else begin
        for (sh = 0; sh < 2*@XW@ + 3; sh = sh + 1) begin
          if (sh < d) begin sts = sts | sml[0]; sml = sml >> 1; end
        end
      end
      st = stb | sts;
      if (sbig == ssml) begin r = big + sml; sr = sbig; end
      else begin
        // the difference: the aligned smaller value's sticky borrows one lsb; the sign follows the larger magnitude
        neg = (big < sml) || (big == sml && sts);
        if (neg) begin r = sml - big; sr = ssml; end
        else begin r = big - sml - (sts ? 1'b1 : 1'b0); sr = sbig; end
      end
      if (r == 0) @P@_fma = @P@_mkx(2'd0, st ? sr : 1'b0, ebase, 0, st);
      else begin
        sh = 0;
        for (k = 0; k < 2*@XW@ + 2; k = k + 1) begin
          if (!r[2*@XW@+1]) begin r = r << 1; sh = sh + 1; end
        end
        st = st | (r[@XW@+1:0] != 0);
        @P@_fma = @P@_mkx(2'd0, sr, ebase + @XW@ + 2 - sh, r[2*@XW@+1:@XW@+2], st);
      end
    end
  endfunction
''', P=self.p, XW=self.XW, XWm=self.XW - 1, EW=self.EW, EWm=self.EW - 1,
                        XT=self.XT, XTm=self.XT - 1)

    # -- rounding of an X into a float pattern --------------------------------
    def pack_float(self, tgt, tag: str):
        """pack_<tag>(x, rnd, word, ftz) -> {flags[FW], bits}."""
        c = _core(tgt)
        p = self.p
        M, E, bias = c.man_bits, c.exp_bits, c.bias
        top = c._top()
        maxf = c._max_finite_bits()
        W = c.width
        XW, EW, XT = self.XW, self.EW, self.XT
        sb = self.sr_bits
        emax_code = c.emax_code
        nan_bits = c.encode_special(NAN_) if c.has_nan else 0
        inf_bits = (emax_code << M) if c.has_inf else maxf
        signed = 1 if c.signed else 0
        MW = W - signed
        if c.exp_only:
            return self._pack_exp_only(c, tag)
        hole_declarations = hole_correction = ""
        if c.has_inf and not c.has_nan:
            hole = c.emax_code << M
            fraction_bits = XW - M - 1
            low_numerator = ((1 << (M + 1)) - 1) << fraction_bits
            fraction_expr = (f"hole_delta >> {fraction_bits - sb}" if fraction_bits >= sb
                             else f"hole_delta << {sb - fraction_bits}")
            chosen = f"{{s, (hole_up ? {MW}'d{hole+1} : {MW}'d{hole-1})}}" if signed \
                else f"(hole_up ? {MW}'d{hole+1} : {MW}'d{hole-1})"
            hole_declarations = f"\n    logic [{XW+1}:0] hole_delta; logic [{XW+sb+1}:0] hole_fraction; logic hole_up;"
            hole_correction = f"""
        if (code == {W+EW+1}'d{hole}) begin
          hole_delta = ((eu == {EW}'sd{emax_code-bias}) ? ({{2'b0,sig}} << 1) : {{2'b0,sig}}) - {XW+2}'d{low_numerator};
          hole_fraction = ({fraction_expr}) / 3;
          case (rnd)
            3'd0: hole_up = (hole_delta << 1) >= {XW+2}'d{3 << fraction_bits};
            3'd1: hole_up = 1'b0;
            3'd2: hole_up = s;
            3'd3: hole_up = !s;
            3'd4: hole_up = @SRGE@ ? (hole_fraction >= word) : (hole_fraction > word);
            default: hole_up = 1'b1;
          endcase
          outb = {chosen}; fl[@F_INEX@] = 1'b1;
        end
"""
            hole_correction = self.sub(hole_correction, F_INEX=flag_bit("inexact"))
        text = self.sub('''
  // X -> @TAG@ (@NAME@): sign(@S@) exp @E@ man @M@, top field @TOP@, max finite @MAXF@
  function automatic [@FW@+@W@-1:0] @P@_pack_@TAG@(input [@XTm@:0] x0, input [2:0] rnd, input [@SBm@:0] word, input ftz);
    logic [@XTm@:0] x; logic [1:0] sp; logic s; logic signed [@EWm@:0] e, eu, biased; logic [@XWm@:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [@XW@:0] keep, rest, keepn, restn, halfv, halfn; logic [@XW@+@SB@:0] fint, fintn; logic [@FW@-1:0] fl;
    logic [@W@+@EW@:0] code; logic [@W@:0] mag; logic [@W@-1:0] outb;@HOLE_DECLARATIONS@
    x = @P@_norm(x0); sp = x[@XTm@:@XTm@-1]; s = x[@XTm@-2] & @S@; sig = x[@XW@:1]; st = x[0]; e = x[@XW@+@EW@:@XW@+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[@F_NAN@] = 1'b1; outb = @NANB@; end
    else if (sp == 2'd2) begin
      outb = @OUT_INF@; if (!@HASINF@) begin fl[@F_INEX@] = 1'b1; fl[@F_OVF@] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = @ZERO_POSITIVE@ ? 0 : @OUT_ZERO@; end
    else begin
      if (sig == 0) begin sig = 1 << @XWm@; e = e - (2*@XW@-1); end // normalize the lone sticky's tiny value
      eu = e + @XWm@;                 // exponent of the leading one
      biased = eu + @BIAS@;
      shn = @XW@ - 1 - @M@;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > @XW@ + 1) sh = @XW@ + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > @XW@) ? {(@XW@+1){1'b1}} : ({1'b0, {@XW@{1'b1}}} >> (@XW@ - sh)));
      halfv = (sh == 0) ? 0 : ({{@XW@{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {@XW@{1'b1}}} >> (@XW@ - shn));
      halfn = (shn == 0) ? 0 : ({{@XW@{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - @SB@ > @XW@) ? 0 : (sht >= @SB@) ? (rest >> (sht - @SB@)) : (rest << (@SB@ - sht));
      fintn = (shn >= @SB@) ? (restn >> (shn - @SB@)) : (restn << (@SB@ - shn));
      up = @P@_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = @P@_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{@XW@{1'b0}}, 1'b1} << (@M@ + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << @M@) + mag - ({{(@W@+@EW@){1'b0}}, 1'b1} << @M@));
      tiny = @TININESS_BEFORE@ ? (eu < @EMIN@) : ((eu < @EMIN@) && !(eu == @EMIN@ - 1 && carry_n) && !(eu + @BIAS@ == 0 && carry_n));
      ovf = (code > @MAXF@);
      if (ovf) begin
        to_inf = @HASINF@ && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (eu > @EMAX@ || up)));
        outb = to_inf ? @OUT_INF@ : @OUT_MAX@;
        fl[@F_OVF@] = 1'b1; fl[@F_INEX@] = 1'b1;
      end else begin
        outb = @OUT_CODE@;
        if (inexact) fl[@F_INEX@] = 1'b1;
        if (tiny && inexact) fl[@F_UNF@] = 1'b1;
        if (ftz && code[@MW@-1:@M@] == 0 && @SUBNZ@) begin
          outb = @OUT_ZERO@; fl[@F_INEX@] = 1'b1; fl[@F_UNF@] = 1'b1;
        end
@HOLE_CORRECTION@
      end
    end
    @P@_pack_@TAG@ = {fl, outb};
  endfunction
''', P=p, TAG=tag, NAME=c.name, S=signed, E=E, M=M, TOP=top, MAXF=f"{MW}'d{maxf}",
                    W=W, XW=XW, XWm=XW - 1, EW=EW, EWm=EW - 1, XT=XT, XTm=XT - 1,
                    FW=FW, SB=sb, SBm=sb - 1, F_NAN=flag_bit("nan"), F_INEX=flag_bit("inexact"),
                    F_OVF=flag_bit("overflow"), F_UNF=flag_bit("underflow"),
                    NANB=f"{W}'d{nan_bits}", INFB=f"{W-1}'d{inf_bits & ((1 << (W-1)) - 1)}",
                    HASINF=1 if c.has_inf else 0, BIAS=bias, EMIN=1 - bias, EMAX=top - bias, SUBNZ=(f"code[{M-1}:0] != 0" if M > 0 else "1'b0"),
                    MW=MW, OUT_INF=(f"{{s, {MW}'d{inf_bits}}}" if signed else f"{MW}'d{inf_bits}"),
                    OUT_MAX=(f"{{s, {MW}'d{maxf}}}" if signed else f"{MW}'d{maxf}"),
                    OUT_ZERO=(f"{{s, {{{MW}{{1'b0}}}}}}" if signed else f"{MW}'d0"),
                    OUT_CODE=(f"{{s, code[{MW-1}:0]}}" if signed else f"code[{MW-1}:0]"),
                    HOLE_DECLARATIONS=hole_declarations, HOLE_CORRECTION=hole_correction)
        return text

    def _pack_exp_only(self, c, tag):
        """X -> an exponent-only format (E8M0): the power of two nearest
        by value (ties to the even exponent field), or the directed one;
        SR from the fraction of the ulp 2^k."""
        p = self.p
        E, bias, W = c.exp_bits, c.bias, c.width
        top = c._top()
        XW, EW, XT = self.XW, self.EW, self.XT
        sb = self.sr_bits
        nan_bits = c.encode_special(NAN_) if c.has_nan else 0
        inf_bits = c.emax_code if c.has_inf else top
        return self.sub('''
  // X -> @TAG@ (@NAME@): exponent-only, top field @TOP@
  function automatic [@FW@+@W@-1:0] @P@_pack_@TAG@(input [@XTm@:0] x0, input [2:0] rnd, input [@SBm@:0] word, input ftz);
    logic [@XTm@:0] x; logic [1:0] sp; logic signed [@EWm@:0] e, eu, code; logic [@XWm@:0] sig, frac; logic s, st, inexact, up, gt_half, half_eq;
    logic [@XW@+@SB@:0] fint; logic [@FW@-1:0] fl; logic [@W@-1:0] outb;
    x = @P@_norm(x0); sp = x[@XTm@:@XTm@-1]; s = x[@XTm@-2] & @SIGNED@; sig = x[@XW@:1]; st = x[0]; e = x[@XW@+@EW@:@XW@+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[@F_NAN@] = 1'b1; outb = @NANB@; end
    else if (sp == 2'd2) begin outb = @SIGNED_INF@; if (!@HASINF@) begin fl[@F_INEX@] = 1'b1; fl[@F_OVF@] = 1'b1; end end
    else if (sig == 0 && !st) begin outb = 0; fl[@F_INEX@] = 1'b1; end
    else begin
      if (sig == 0) begin sig = 1 << @XWm@; e = e - (2*@XW@-1); end
      eu = e + @XWm@;
      frac = sig & {1'b0, {(@XW@-1){1'b1}}};
      inexact = (frac != 0) | st;
      gt_half = frac > ({{(@XW@-1){1'b0}}, 1'b1} << (@XW@ - 2)) || (frac == ({{(@XW@-1){1'b0}}, 1'b1} << (@XW@ - 2)) && st);
      half_eq = (frac == ({{(@XW@-1){1'b0}}, 1'b1} << (@XW@ - 2))) && !st;
      fint = (@XW@ - 1 >= @SB@) ? ({{(@SB@+1){1'b0}}, frac} >> (@XW@ - 1 - @SB@)) : ({{(@SB@+1){1'b0}}, frac} << (@SB@ - @XW@ + 1));
      case (rnd)
        3'd0: up = gt_half || (half_eq && ((eu + @BIAS@) & 1));
        3'd1: up = 1'b0;
        3'd2: up = s && inexact;
        3'd3: up = !s && inexact;
        3'd4: up = inexact && (@SRGE@ ? (fint >= word) : (fint > word));
        default: up = inexact;
      endcase
      code = eu + @BIAS@ + up;
      if (code < 0) begin outb = @SIGNED_MIN@; fl[@F_INEX@] = 1'b1; end
      else if (code > @TOP@) begin
        outb = (@HASINF@ && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || rnd == 3'd4)) ? @SIGNED_INF@ : @SIGNED_MAX@;
        fl[@F_INEX@] = 1'b1; fl[@F_OVF@] = 1'b1;
      end else begin
        outb = @SIGNED_CODE@;
        if (inexact) fl[@F_INEX@] = 1'b1;
        if (inexact && code == @TOP@) fl[@F_OVF@] = 1'b1;
      end
    end
    @P@_pack_@TAG@ = {fl, outb};
  endfunction
''', P=p, TAG=tag, NAME=c.name, TOP=top, W=W, XW=XW, XWm=XW - 1, EW=EW, EWm=EW - 1, XT=XT,
                    XTm=XT - 1, FW=FW, SB=sb, SBm=sb - 1, F_NAN=flag_bit("nan"), F_INEX=flag_bit("inexact"),
                    F_OVF=flag_bit("overflow"), NANB=f"{W}'d{nan_bits}", INFB=f"{W}'d{inf_bits}",
                    HASINF=1 if c.has_inf else 0, BIAS=bias, SIGNED=int(c.signed),
                    SIGNED_INF=f"{{s, {E}'d{inf_bits}}}" if c.signed else f"{E}'d{inf_bits}",
                    SIGNED_MAX=f"{{s, {E}'d{top}}}" if c.signed else f"{E}'d{top}",
                    SIGNED_MIN=f"{{s, {E}'d0}}" if c.signed else f"{E}'d0",
                    SIGNED_CODE=f"{{s, code[{E-1}:0]}}" if c.signed else f"code[{E-1}:0]")

    def rup_fn(self):
        """The rounding decision shared by every pack: rnd, sign, inexact,
        the dropped bits against half, sticky, lsb, the SR fraction word."""
        return self.sub('''
  function automatic @P@_rup(input [2:0] rnd, input s, input inexact, input [@XW@:0] rest, input [@XW@:0] halfv,
                             input st, input lsb, input [@XW@+@SB@:0] fint, input [@SBm@:0] word);
    logic gt_half, half_eq;
    gt_half = rest > halfv; half_eq = (rest == halfv) && (halfv != 0);
    case (rnd)
      3'd0: @P@_rup = gt_half || (half_eq && (st || lsb));
      3'd1: @P@_rup = 1'b0;
      3'd2: @P@_rup = inexact && s;
      3'd3: @P@_rup = inexact && !s;
      3'd4: @P@_rup = inexact && (@SRGE@ ? (fint >= word) : (fint > word));
      default: @P@_rup = inexact;   // 5: away from zero
    endcase
  endfunction
''', P=self.p, XW=self.XW, SB=self.sr_bits, SBm=self.sr_bits - 1)

    # -- unpack ---------------------------------------------------------------
    def unpack_float(self, fmt, tag):
        c = _core(fmt)
        p = self.p
        M, E, bias, W = c.man_bits, c.exp_bits, c.bias, c.width
        emax = c.emax_code
        signed = c.signed
        cond_inf = "1'b0"
        cond_nan = "1'b0"
        if c.exp_only:
            if c.has_nan or c.has_inf:
                cond_nan = f"(e == {E}'d{emax})" if c.has_nan else "1'b0"
                cond_inf = f"(e == {E}'d{emax})" if c.has_inf and not c.has_nan else "1'b0"
        else:
            if c.has_inf and c.has_nan:
                cond_inf = f"(e == {E}'d{emax} && m == 0)"
                cond_nan = f"(e == {E}'d{emax} && m != 0)"
            elif c.has_inf:
                cond_inf = f"(e == {E}'d{emax} && m == 0)"
            elif c.has_nan:
                cond_nan = f"(e == {E}'d{emax} && m == {{{M}{{1'b1}}}})"
        if M > 0:
            body = f'''    if (e == 0) begin sig = {{{{({self.SW}-{M}){{1'b0}}}}, m}}; ex = {1 - bias - M}; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{{{({self.SW}-{M}-1){{1'b0}}}}, 1'b1, m}}; ex = e - {bias + M}; end'''
        else:
            body = f'''    sig = 1; ex = e - {bias};'''
        s_expr = f"b[{W-1}]" if signed else "1'b0"
        return self.sub(f'''
  // {c.name} pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [@VW@:0] @P@_unpack_{tag}(input [{W-1}:0] b, input daz);
    logic [{E-1}:0] e; logic [{max(M,1)-1}:0] m; logic [@SWm@:0] sig; logic signed [@EWm@:0] ex; logic den, s;
    e = b[{M+E-1}:{M}]; m = {"b[" + str(M-1) + ":0]" if M > 0 else "1'b0"}; s = {s_expr}; den = 1'b0; sig = 0; ex = 0;
    if ({cond_nan}) @P@_unpack_{tag} = {{1'b0, @P@_mkv(2'd1, 1'b0, 0, 0)}};
    else if ({cond_inf}) @P@_unpack_{tag} = {{1'b0, @P@_mkv(2'd2, s, 0, 0)}};
    else begin
{body}
      @P@_unpack_{tag} = {{den, @P@_mkv(2'd0, s, ex, sig)}};
    end
  endfunction
''', P=p, VW=self.VW, SWm=self.SW - 1, EWm=self.EW - 1)

    def unpack_posit(self, fmt: PositFormat, tag):
        n, es = fmt.width, fmt.es
        p = self.p
        return self.sub(f'''
  // posit{n}_{es} pattern -> V
  function automatic [@VW@:0] @P@_unpack_{tag}(input [{n-1}:0] b, input daz);
    logic s; logic [{n-1}:0] mag; logic [{n-2}:0] body; logic first, done; integer run, i, rest_bits, e_bits, f_bits;
    logic signed [@EWm@:0] k, ex; logic [{max(es,1)-1}:0] e; logic [{n-1}:0] f; logic [@SWm@:0] sig;
    s = b[{n-1}];
    if (b == 0) @P@_unpack_{tag} = {{1'b0, @P@_mkv(2'd0, 1'b0, 0, 0)}};
    else if (b == {{1'b1, {{{n-1}{{1'b0}}}}}}) @P@_unpack_{tag} = {{1'b0, @P@_mkv(2'd1, 1'b0, 0, 0)}};
    else begin
      mag = s ? (~b + 1'b1) : b;
      body = mag[{n-2}:0];
      first = body[{n-2}]; run = 0; done = 1'b0;
      for (i = {n-2}; i >= 0; i = i - 1) begin
        if (!done) begin
          if (body[i] == first) run = run + 1; else done = 1'b1;
        end
      end
      k = first ? run - 1 : -run;
      rest_bits = {n-1} - run - 1;
      if (rest_bits < 0) rest_bits = 0;
      e_bits = (rest_bits < {es}) ? rest_bits : {es};
      f_bits = rest_bits - {es}; if (f_bits < 0) f_bits = 0;
      e = 0;
      if (e_bits > 0) e = (body >> (rest_bits - e_bits)) & ((1 << e_bits) - 1);
      e = e << ({es} - e_bits);
      f = (f_bits > 0) ? (body & ((1 << f_bits) - 1)) : 0;
      // value = 2^(k*2^es + e) * (1 + f / 2^f_bits): sig has the hidden one at bit n-1
      sig = ({{{{(@SW@-{n}){{1'b0}}}}, 1'b1, {{{n-1}{{1'b0}}}}}}) | (f << ({n-1} - f_bits));
      ex = (k <<< {es}) + e - {n-1};
      @P@_unpack_{tag} = {{1'b0, @P@_mkv(2'd0, s, ex, sig)}};
    end
  endfunction
''', P=p, VW=self.VW, SW=self.SW, SWm=self.SW - 1, EWm=self.EW - 1)

    def pack_posit(self, fmt: PositFormat, tag):
        n, es = fmt.width, fmt.es
        p = self.p
        XW, EW, XT = self.XW, self.EW, self.XT
        RW = n + es + XW + 2
        return self.sub(f'''
  // X -> posit{n}_{es}: frozen pattern rounding modes, clamped to maxpos/minpos
  function automatic [@FW@+{n}-1:0] @P@_pack_{tag}(input [@XTm@:0] x0, input [2:0] rnd, input [@SBm@:0] word, input ftz);
    logic [@XTm@:0] x; logic [1:0] sp; logic s; logic signed [@EWm@:0] e, eu, k; logic [@XWm@:0] sig; logic st;
    logic [{RW-1}:0] r; logic [{n-2}:0] topb; logic [{RW-1}:0] dropped, halfv; integer rl, pos, i;
    logic [{max(es,1)-1}:0] elow; logic [{n-1}:0] mag; logic clamp_hi, clamp_lo, up, inexact; logic [@FW@-1:0] fl;
    x = @P@_norm(x0); sp = x[@XTm@:@XTm@-1]; s = x[@XTm@-2]; sig = x[@XW@:1]; st = x[0]; e = x[@XW@+@EW@:@XW@+1];
    fl = 0; mag = 0; clamp_hi = 1'b0; clamp_lo = 1'b0; inexact = 1'b0;
    if (sp != 2'd0) begin fl[@F_NAN@] = 1'b1; @P@_pack_{tag} = {{fl, {{1'b1, {{{n-1}{{1'b0}}}}}}}}; end
    else if (sig == 0 && !st) @P@_pack_{tag} = {{fl, {{{n}{{1'b0}}}}}};
    else begin
      if (sig == 0) begin sig = 1; e = e - @XW@; end
      eu = e + @XWm@;
      k = eu >>> {es};
      elow = eu & ((1 << {es}) - 1);
      if (k > {n-2}) clamp_hi = 1'b1;
      else if (k < -({n-2})) clamp_lo = 1'b1;
      if (clamp_hi) begin mag = {{1'b0, {{{n-1}{{1'b1}}}}}}; inexact = 1'b1; fl[@F_OVF@] = 1'b1; end
      else if (clamp_lo) begin mag = 1; inexact = 1'b1; fl[@F_UNF@] = 1'b1; end
      else begin
        // regime, then es bits, then the fraction (sig below its leading one), then sticky
        r = 0; pos = {RW};
        if (k >= 0) begin rl = k + 2; for (i = 0; i < {n}; i = i + 1) if (i < k + 1) begin pos = pos - 1; r[pos] = 1'b1; end
                    pos = pos - 1; r[pos] = 1'b0; end
        else begin rl = -k + 1; for (i = 0; i < {n}; i = i + 1) if (i < -k) begin pos = pos - 1; r[pos] = 1'b0; end
                    pos = pos - 1; r[pos] = 1'b1; end
        for (i = {es} - 1; i >= 0; i = i - 1) begin pos = pos - 1; r[pos] = elow[i]; end
        for (i = @XW@ - 2; i >= 0; i = i - 1) begin pos = pos - 1; r[pos] = sig[i]; end
        r[0] = st;
        topb = r[{RW-1} -: {n-1}];
        dropped = r & ((1 << ({RW} - {n-1})) - 1);
        halfv = 1 << ({RW} - {n-1} - 1);
        inexact = (dropped != 0);
        case (rnd)
          3'd1, 3'd2: up = inexact && s;
          3'd3: up = inexact && !s;
          default: up = (dropped > halfv) || (dropped == halfv && topb[0]);
        endcase
        mag = {{1'b0, topb}} + up;
        if (mag[{n-1}]) begin mag = {{1'b0, {{{n-1}{{1'b1}}}}}}; fl[@F_OVF@] = 1'b1; end
        if (k == {n-2} && inexact) fl[@F_OVF@] = 1'b1;
        if (mag == 0) begin mag = 1; fl[@F_UNF@] = 1'b1; end
      end
      if (inexact) fl[@F_INEX@] = 1'b1;
      @P@_pack_{tag} = {{fl, s ? (~mag + 1'b1) : mag}};
    end
  endfunction
''', P=p, XW=XW, XWm=XW - 1, EW=EW, EWm=EW - 1, XT=XT, XTm=XT - 1, FW=FW,
                    SBm=self.sr_bits - 1, F_NAN=flag_bit("nan"), F_INEX=flag_bit("inexact"),
                    F_OVF=flag_bit("overflow"), F_UNF=flag_bit("underflow"))

    def unpack_int(self, fmt, tag):
        """Integer or fixed pattern -> V (sig = magnitude, exp = -F)."""
        p = self.p
        W = fmt.width
        F = getattr(fmt, "frac_bits", 0)
        enc = fmt.encoding
        if enc == "unsigned":
            body = f"s = 1'b0; mag = b;"
        elif enc == "twos_complement":
            body = f"s = b[{W-1}]; mag = s ? (~b + 1'b1) : b;"
        elif enc == "ones_complement":
            body = f"s = b[{W-1}]; mag = s ? ~b : b;"
        elif enc == "sign_magnitude":
            body = f"s = b[{W-1}]; mag = b & {{1'b0, {{{W-1}{{1'b1}}}}}};"
        else:                                    # bcd
            D = fmt.digits
            body = f"s = 1'b0; mag = 0; for (i = {D-1}; i >= 0; i = i - 1) mag = mag * 10 + b[4*i +: 4];"
        return self.sub(f'''
  function automatic [@VW@:0] @P@_unpack_{tag}(input [{W-1}:0] b, input daz);
    logic s; logic [{W-1}:0] mag; integer i;
    {body}
    @P@_unpack_{tag} = {{1'b0, @P@_mkv(2'd0, s && (mag != 0), -{F}, {{{{(@SW@-{W}){{1'b0}}}}, mag}})}};
  endfunction
''', P=p, VW=self.VW, SW=self.SW)

    def pack_int(self, tgt, tag):
        """X -> integer or fixed target (round under rnd/SR, saturate);
        specials per nan_to_int (@NANTOINT@ code: 0 zero, 1 max, 2 min)."""
        p = self.p
        W = tgt.width
        F = getattr(tgt, "frac_bits", 0)
        enc = tgt.encoding
        XW, EW, XT = self.XW, self.EW, self.XT
        IW = W + 2
        mx, mn = tgt.max_int, tgt.min_int
        if enc == "bcd":
            D = tgt.digits
            encode = f"for (i = 0; i < {D}; i = i + 1) begin outb[4*i +: 4] = t % 10; t = t / 10; end"
        elif enc == "unsigned":
            encode = f"outb = t[{W-1}:0];"
        elif enc == "twos_complement":
            encode = f"outb = neg ? (~t[{W-1}:0] + 1'b1) : t[{W-1}:0];"
        elif enc == "ones_complement":
            encode = f"outb = neg ? ~t[{W-1}:0] : t[{W-1}:0];"
        else:
            encode = f"outb = {{neg, t[{W-2}:0]}};"
        # the saturation bounds as literals sized to t: an unsized 2^31
        # (int32's |min|) is a 32-bit signed literal to the converter, which then
        # sign-extends it in the compare against t and the saturation
        # never fires (the seed of alu_mixed32 failed its gates on the
        # cluster this way while the unconverted source passed the simulator)
        TW = XW + IW + 1
        MX, MNA = f"{TW}'d{mx}", f"{TW}'d{abs(mn)}"
        MN_NEG = "1'b1" if mn < 0 else "1'b0"
        MN_ZERO = "1'b1" if mn == 0 else "1'b0"
        return self.sub(f'''
  // X -> {tgt.name} (width {W}, {F} fraction bits): rounded and saturated
  function automatic [@FW@+{W}-1:0] @P@_pack_{tag}(input [@XTm@:0] x0, input [2:0] rnd, input [@SBm@:0] word, input ftz);
    logic [@XTm@:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [@EWm@:0] e, pe; logic [@XWm@:0] sig;
    logic [@XW@:0] keep, rest, halfv; logic [@XW@+@SB@:0] fint; integer sh, sht, i; logic [@XW@+{IW}:0] wide, t; logic [@FW@-1:0] fl; logic [{W-1}:0] outb;
    x = @P@_norm(x0); sp = x[@XTm@:@XTm@-1]; s = x[@XTm@-2]; sig = x[@XW@:1]; st = x[0]; e = x[@XW@+@EW@:@XW@+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[@F_INV@] = 1'b1; t = (@NANTOINT@ == 1) ? {MX} : (@NANTOINT@ == 2) ? {MNA} : 0; neg = (@NANTOINT@ == 2) && {MN_NEG}; end
    else if (sp == 2'd2) begin fl[@F_INV@] = 1'b1; neg = s; t = s ? {MNA} : {MX}; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - @XW@; end
      pe = e + {F};                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > {IW}) big = 1'b1;
        else begin wide = {{{{({IW}+1){{1'b0}}}}, sig}} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = @P@_rup(rnd, s, st, {{(@XW@+1){{1'b0}}}}, {{(@XW@+1){{1'b0}}}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > @XW@ + 1) sh = @XW@ + 1;
        keep = {{1'b0, sig}} >> sh; rest = {{1'b0, sig}} & ((sh > @XW@) ? {{(@XW@+1){{1'b1}}}} : ({{1'b0, {{@XW@{{1'b1}}}}}} >> (@XW@ - sh)));
        halfv = ({{{{@XW@{{1'b0}}}}, 1'b1}} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - @SB@ > @XW@) ? 0 : (sht >= @SB@) ? (rest >> (sht - @SB@)) : (rest << (@SB@ - sht));
        up = @P@_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[@F_INEX@] = 1'b1;
      if (big || (neg && t > {MNA}) || (!neg && t > {MX})) begin
        fl[@F_OVF@] = 1'b1; fl[@F_INEX@] = 1'b1; fl[@F_INV@] = 1'b1;
        t = neg ? {MNA} : {MX};
      end
      if ({MN_ZERO} && neg) begin t = 0; neg = 1'b0; end
    end
    {encode}
    @P@_pack_{tag} = {{fl, outb}};
  endfunction
''', P=p, XW=XW, XWm=XW - 1, EW=EW, EWm=EW - 1, XT=XT, XTm=XT - 1, FW=FW, SB=self.sr_bits,
                    SBm=self.sr_bits - 1, F_INV=flag_bit("invalid"), F_INEX=flag_bit("inexact"),
                    F_OVF=flag_bit("overflow"))

    # -- blocks ---------------------------------------------------------------
    def unpack_block(self, fmt: BlockFormat, tag):
        """Block pattern -> size V values (packed, element i at [i*VW1 +: VW1])
        where VW1 = VW + 1 carries the denormal-read flag."""
        p = self.p
        el, sc = fmt.elem, fmt.scale
        we, ws = el.width, sc.width
        size = fmt.size
        VW1 = self.VW + 1
        parts = []
        if isinstance(el, FloatFormat):
            parts.append(self.unpack_float(el, f"{tag}_e"))
        else:
            parts.append(self.unpack_int(el, f"{tag}_e"))
        parts.append(self.unpack_float(sc, f"{tag}_s"))
        SW, EW, VW = self.SW, self.EW, self.VW
        parts.append(self.sub(f'''
  function automatic [{size * VW1 - 1}:0] @P@_unpack_{tag}(input [{fmt.width - 1}:0] b, input daz);
    logic [@VW@:0] ve, vs; logic [@VW@:0] vo; integer i; logic [@SWm@:0] se, ss; logic signed [@EWm@:0] ee, es;
    vs = @P@_unpack_{tag}_s(b[{size * we} +: {ws}], 1'b0);
    ss = vs[@SWm@:0]; es = vs[@VWm@-3 -: @EW@];
    for (i = 0; i < {size}; i = i + 1) begin
      ve = @P@_unpack_{tag}_e(b[i*{we} +: {we}], daz);
      se = ve[@SWm@:0]; ee = ve[@VWm@-3 -: @EW@];
      if (ve[@VWm@:@VWm@-1] != 2'd0) vo = ve;
      else vo = {{ve[@VW@], @P@_mkv(2'd0, ve[@VWm@-2], ee + es, se * ss)}};
      @P@_unpack_{tag}[i*{VW1} +: {VW1}] = vo;
    end
  endfunction
''', P=p, VW=VW, VWm=VW - 1, SWm=SW - 1, EW=EW, EWm=EW - 1))
        return "".join(parts)

    def quant_block(self, fmt: BlockFormat, tag, rnd_scale="0"):
        """size X values -> one block: quant_<tag>(xs, rnd, words, ftz) ->
        {flags[size*FW], block}. Conventions: @SCALE_RUP@ (block_scale_
        rounding up), @ELEM_INF@ (block_element_overflow inf),
        @INVZERO@ (invalid_result zero)."""
        p = self.p
        el, sc = fmt.elem, fmt.scale
        size = fmt.size
        XW, EW, XT, SW = self.XW, self.EW, self.XT, self.SW
        fl_el = isinstance(el, FloatFormat)
        emax = el.max_finite() if fl_el else Fraction(el.max_int)
        e_emax = _floor_log2(emax)
        # emax as an X constant: sig = emax normalized to XW bits
        num, den = emax.numerator, emax.denominator
        assert den & (den - 1) == 0
        # emax = num / 2^k -> sig = num << (XW - bitlen), exp = -k - (XW - bitlen)
        k = den.bit_length() - 1
        bl = num.bit_length()
        emax_sig = num << (XW - bl)
        emax_exp = -k - (XW - bl)
        parts = []
        parts.append(self.pack_float(el, f"{tag}_e") if fl_el else self.pack_int(el, f"{tag}_e"))
        parts.append(self.pack_float(sc, f"{tag}_s"))
        parts.append(self.unpack_float(sc, f"{tag}_sd"))
        top_s = sc._top()
        min_pos_bits = sc.encode(sc.min_positive())
        el_nan = el.encode_special(NAN_) if (fl_el and el.has_nan) else 0
        el_inf = (el.emax_code << el.man_bits) if (fl_el and el.has_inf) else 0
        el_max = el._max_finite_bits() if fl_el else el.encode(el.max_int)
        el_negative_saturation = (el_max | ((1 << (el.width - 1)) if el.signed else 0)) if fl_el else el.encode(el.min_int)
        el_signed = 1 if (fl_el and el.signed) else 0
        parts.append(self.sub(f'''
  // section 2.6 quantizer into {fmt.name}
  function automatic [{size * FW + fmt.width - 1}:0] @P@_quant_{tag}(input [{size * XT - 1}:0] xs, input [2:0] rnd, input [{size * self.sr_bits - 1}:0] words, input ftz);
    logic [@XTm@:0] x, nx, amax, xe, sq; logic have; logic signed [@EWm@:0] eu, emx, es; logic [@XWm@:0] sm; integer i;
    logic [{sc.width - 1}:0] sb; logic [@VW@:0] vs; logic [@FW@+{sc.width}-1:0] ps; logic [@FW@+{el.width}-1:0] pe;
    logic [{fmt.width - 1}:0] blk; logic [{size * FW - 1}:0] fls; logic [@FW@-1:0] f; logic sat, nz;
    have = 1'b0; emx = 0; sm = 0; amax = 0; blk = 0; fls = 0;
    for (i = 0; i < {size}; i = i + 1) begin
      nx = @P@_norm(xs[i*@XT@ +: @XT@]);
      if (nx[@XTm@:@XTm@-1] == 2'd0 && (nx[@XW@:1] != 0) && !({int(fl_el and not el.signed)} && nx[@XTm@-2])) begin
        eu = nx[@XW@+@EW@:@XW@+1] + @XWm@;
        if (!have || eu > emx || (eu == emx && nx[@XW@:1] > sm)) begin have = 1'b1; emx = eu; sm = nx[@XW@:1]; amax = {{2'd0, 1'b0, nx[@XW@+@EW@:0]}}; end
      end
    end
    if ({1 if sc.exp_only else 0}) begin
      if (!have) sb = 0;
      else begin
        es = emx - {e_emax} + {sc.bias};
        sb = (es < 0) ? 0 : (es > {top_s}) ? {top_s} : es;
      end
    end else begin
      if (!have) sb = {sc.width}'d{min_pos_bits};
      else begin
        ps = @P@_pack_{tag}_s(@P@_div(amax, @P@_mkx(2'd0, 1'b0, {emax_exp}, {XW}'d{emax_sig}, 1'b0)), @SCALE_RUP@ ? 3'd3 : 3'd0, 0, 1'b0);
        sb = ps[{sc.width - 1}:0];
        if (sb == 0) sb = {sc.width}'d{min_pos_bits};
        else if (sb > {sc.width}'d{sc._max_finite_bits()}) sb = {sc.width}'d{sc._max_finite_bits()};
      end
    end
    vs = @P@_unpack_{tag}_sd(sb, 1'b0);
    for (i = 0; i < {size}; i = i + 1) begin
      x = xs[i*@XT@ +: @XT@]; f = 0;
      if ({int(fl_el and not el.signed)} && x[@XTm@-2] &&
          (x[@XTm@:@XTm@-1] == 2'd2 || (x[@XTm@:@XTm@-1] == 2'd0 && (x[@XW@:1] != 0 || x[0])))) begin
        f[@F_INV@] = 1'b1;
        if ({int(fl_el and el.has_nan)}) begin blk[i*{el.width} +: {el.width}] = {el.width}'d{el_nan}; f[@F_NAN@] = 1'b1; end
        else begin blk[i*{el.width} +: {el.width}] = @INVZERO@ ? 0 : {el.width}'d{el_max}; f[@F_INEX@] = 1'b1; end
      end else if (x[@XTm@:@XTm@-1] == 2'd1) begin
        f[@F_INV@] = 1'b1;
        if ({1 if (fl_el and el.has_nan) else 0}) begin blk[i*{el.width} +: {el.width}] = {el.width}'d{el_nan}; f[@F_NAN@] = 1'b1; end
        else begin blk[i*{el.width} +: {el.width}] = @INVZERO@ ? 0 : {el.width}'d{el_max}; f[@F_INEX@] = 1'b1; end
      end else if (x[@XTm@:@XTm@-1] == 2'd2) begin
        f[@F_OVF@] = 1'b1;
        if ({1 if (fl_el and el.has_nan) else 0} && !({1 if (fl_el and el.has_inf) else 0} && @ELEM_INF@)) begin blk[i*{el.width} +: {el.width}] = {el.width}'d{el_nan}; f[@F_NAN@] = 1'b1; end
        else if ({1 if (fl_el and el.has_inf) else 0} && @ELEM_INF@) blk[i*{el.width} +: {el.width}] = {el.width}'d{el_inf} | ((x[@XTm@-2] && {el_signed}) ? ({el.width}'d1 << {el.width - 1}) : 0);
        else if (@INVZERO@) begin blk[i*{el.width} +: {el.width}] = 0; f[@F_INEX@] = 1'b1; end
        else begin blk[i*{el.width} +: {el.width}] = x[@XTm@-2] ? {el.width}'d{el_negative_saturation} : {el.width}'d{el_max}; f[@F_INEX@] = 1'b1; end
      end else begin
        // x / scale
        if ({1 if sc.exp_only else 0}) xe = {{x[@XTm@:@XTm@-2], x[@XW@+@EW@:@XW@+1] - vs[@VWm@-3 -: @EW@], x[@XW@:0]}};
        else xe = @P@_div(x, @P@_x(vs[@VWm@:0]));
        sat = 1'b0;
        if ({1 if fl_el else 0} && !@ELEM_INF@) begin
          // saturate at the element's largest finite magnitude
          if (@P@_lt(@P@_mkx(2'd0, 1'b0, {emax_exp}, {XW}'d{emax_sig}, 1'b0), {{2'd0, 1'b0, xe[@XW@+@EW@:0]}})) sat = 1'b1;
        end
        if (sat) begin
          blk[i*{el.width} +: {el.width}] = {el.width}'d{el_max} | ((xe[@XTm@-2] && {el_signed}) ? ({el.width}'d1 << {el.width - 1}) : 0);
          f[@F_OVF@] = 1'b1; f[@F_INEX@] = 1'b1;
        end else begin
          pe = @P@_pack_{tag}_e(xe, rnd, words[i*{self.sr_bits} +: {self.sr_bits}], ftz);
          blk[i*{el.width} +: {el.width}] = pe[{el.width - 1}:0];
          f = f | pe[@FW@+{el.width}-1:{el.width}];
          if ({int(not fl_el)}) f[@F_INV@] = 1'b0;
        end
      end
      fls[i*@FW@ +: @FW@] = f;
    end
    blk[{size * el.width} +: {sc.width}] = sb;
    @P@_quant_{tag} = {{fls, blk}};
  endfunction
''', P=p, XW=XW, XWm=XW - 1, EW=EW, EWm=EW - 1, XT=XT, XTm=XT - 1, VW=self.VW, VWm=self.VW - 1,
                     FW=FW, F_INV=flag_bit("invalid"), F_NAN=flag_bit("nan"),
                     F_INEX=flag_bit("inexact"), F_OVF=flag_bit("overflow")))
        return "".join(parts)


class _NanTok:
    pass


NAN_ = None


def _init():
    global NAN_
    from chialu.verify.formats import NAN
    NAN_ = NAN


_init()
