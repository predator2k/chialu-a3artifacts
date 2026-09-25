"""Ordered-prefix estimates with an exact low-key correction."""


def corrected_keys(m, coarse_a, coarse_b, coarse_bits, fine_a, fine_b, fine_bits, *, model, error_units):
    """Emit a coarse decision and resolve ties with the retained low key.

    Lexicographic order of (coarse,fine) equals order of their concatenation.
    The coarse value is an order estimate; the correction recovers exactness.
    Both operands of both comparisons are real key fields, without padding.
    """
    if min(coarse_bits, fine_bits) < 1:
        raise ValueError('corrected RNS comparison needs both a coarse and a fine key')
    name = f'fam_rns_order_correction_c{coarse_bits}_f{fine_bits}'
    m.extra.append(f'''module {name} (
  input wire [{coarse_bits-1}:0] coarse_a, coarse_b,
  input wire [{fine_bits-1}:0] fine_a, fine_b,
  output wire lt
);
  localparam integer COARSE_BITS = {coarse_bits}, FINE_BITS = {fine_bits};
  wire coarse_lt = coarse_a < coarse_b;
  wire coarse_equal = coarse_a == coarse_b;
  wire fine_lt = fine_a < fine_b;
  assign lt = coarse_lt | (coarse_equal & fine_lt);
endmodule
''')
    m.raw(f'  // coarse estimate: {model}; discarded interval width is {error_units} key units')
    m.raw(f'  {name} u_order_correction (.coarse_a({coarse_a}), .coarse_b({coarse_b}), '
          f'.fine_a({fine_a}), .fine_b({fine_b}), .lt(lt));')
    return {'coarse_bits': coarse_bits, 'fine_bits': fine_bits, 'model': model,
            'discarded_interval_width': error_units, 'correction_instance': 'u_order_correction'}
