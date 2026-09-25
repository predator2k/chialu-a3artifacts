"""Structural carry-save reductions for the redundant/RNS column slot.

Every word has the same weight and width.  The returned two words sum to
the input sum modulo 2**width; callers choose a wide enough frame when
overflow must be preserved and provide the selected final CPA.

A 4:2 cell has a horizontal carry chain, with cout independent of cin.
A 7:3 cell counts seven bits into weights 1, 2, and 4.  Partial groups use
3:2 cells and are recorded as tails, never as full selected compressors.

The 4:2 bit identity is a+b+c+d+cin = s+2*carry+2*cout.
In a word cin[j+1]=cout[j], so the horizontal terms cancel between
columns (the final cout is outside the modulo frame). The 7:3 bit
identity is sum(a..g) = s+2*carry+4*carry2. Each word replacement
therefore preserves the sum modulo 2**width, as does each whole layer.
"""


MODULES = r"""
module fam_redundant_csa_bit_3_2 (
  input wire a, b, c, output wire s, carry
);
  assign s = a ^ b ^ c;
  assign carry = (a & b) | (a & c) | (b & c);
endmodule

module fam_redundant_csa_bit_4_2 (
  input wire a, b, c, d, cin, output wire s, carry, cout
);
  wire partial = a ^ b ^ c;
  assign cout = (a & b) | (a & c) | (b & c);
  assign s = partial ^ d ^ cin;
  assign carry = (partial & d) | (partial & cin) | (d & cin);
endmodule

module fam_redundant_csa_bit_7_3 (
  input wire a, b, c, d, e, f, g, output wire s, carry, carry2
);
  wire s0, c0, s1, c1, c2;
  fam_redundant_csa_bit_3_2 fa0(a, b, c, s0, c0);
  fam_redundant_csa_bit_3_2 fa1(d, e, f, s1, c1);
  fam_redundant_csa_bit_3_2 fa2(s0, s1, g, s, c2);
  fam_redundant_csa_bit_3_2 fa3(c0, c1, c2, carry, carry2);
endmodule

module fam_redundant_csa_3_2 #(parameter W=1) (
  input wire [W-1:0] a, b, c, output wire [W-1:0] s, carry
);
  wire [W-1:0] unshifted;
  for (genvar j=0; j<W; j=j+1) begin: bits
    fam_redundant_csa_bit_3_2 cell32(a[j], b[j], c[j], s[j], unshifted[j]);
  end
  assign carry = unshifted << 1;
endmodule

module fam_redundant_csa_4_2 #(parameter W=1) (
  input wire [W-1:0] a, b, c, d, output wire [W-1:0] s, carry
);
  wire [W:0] chain;
  wire [W-1:0] unshifted;
  assign chain[0] = 1'b0;
  for (genvar j=0; j<W; j=j+1) begin: bits
    fam_redundant_csa_bit_4_2 cell42(a[j], b[j], c[j], d[j], chain[j],
                                   s[j], unshifted[j], chain[j+1]);
  end
  assign carry = unshifted << 1;
endmodule

module fam_redundant_csa_7_3 #(parameter W=1) (
  input wire [W-1:0] a, b, c, d, e, f, g,
  output wire [W-1:0] s, carry, carry2
);
  wire [W-1:0] unshifted, unshifted2;
  for (genvar j=0; j<W; j=j+1) begin: bits
    fam_redundant_csa_bit_7_3 cell73(a[j], b[j], c[j], d[j], e[j], f[j], g[j],
                                   s[j], unshifted[j], unshifted2[j]);
  end
  assign carry = unshifted << 1;
  assign carry2 = unshifted2 << 2;
endmodule
"""


def csa_rows(m, terms, width, tag, compressor, *, require_full=False):
    """Emit the requested cells and return two same-width row expressions.

    ``m.reduction_stats`` records full word/bit cells separately from 3:2
    tails.  A parent containing multiple reductions may aggregate these
    records to require at least one full use of its selected column slot.
    ``require_full`` supplies the same check for a standalone reduction.
    Row count alone is structural coverage: callers must additionally
    establish activity when rows contain constants or sparse bit masks.
    """
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError('carry-save reduction width must be a positive integer')
    if compressor not in ('3:2', '4:2', '7:3'):
        raise ValueError(f'unknown carry-save compressor {compressor!r}')
    arity = int(compressor.split(':')[0])
    cur = list(terms)
    if require_full and len(cur) < arity:
        raise ValueError(f'compressor={compressor} needs at least {arity} actual input rows; got {len(cur)}')
    stats = {'tag': tag, 'compressor': compressor, 'width': width,
             'input_rows': len(cur), 'full_word_cells': 0, 'full_bit_cells': 0,
             'tail_3_2_word_cells': 0, 'tail_3_2_bit_cells': 0, 'stages': 0}
    if not hasattr(m, 'reduction_stats'):
        m.reduction_stats = []
    m.reduction_stats.append(stats)
    if len(cur) > 2:
        m.extra.append(MODULES)

    def emit(group, kind, tail=False):
        m.n += 1
        prefix = f'{tag}_csa{m.n}'
        count = 3 if kind == '7:3' else 2
        outputs = [m.wire(f'{prefix}_r{i}', width) for i in range(count)]
        connections = [f'.{p}({x})' for p, x in zip('abcdefg', group)]
        connections += [f'.{p}({x})' for p, x in zip(('s', 'carry', 'carry2'), outputs)]
        m.raw(f'  fam_redundant_csa_{kind.replace(":", "_")} #(.W({width})) '
              f'{prefix} ({", ".join(connections)});')
        which = 'tail_3_2' if tail else 'full'
        stats[f'{which}_word_cells'] += 1
        stats[f'{which}_bit_cells'] += width
        return outputs

    while len(cur) > 2:
        stats['stages'] += 1
        nxt = []
        complete = len(cur) // arity * arity
        for i in range(0, complete, arity):
            nxt.extend(emit(cur[i:i + arity], compressor))
        tail = cur[complete:]
        for i in range(0, len(tail) // 3 * 3, 3):
            nxt.extend(emit(tail[i:i + 3], '3:2', tail=True))
        nxt.extend(tail[len(tail) // 3 * 3:])
        cur = nxt
    m.raw('  // carry-save structure: ' + ', '.join(f'{k}={v}' for k, v in stats.items()))
    return tuple((cur + [f"{width}'d0", f"{width}'d0"])[:2])
