---
family: low_power_gated
pin: {lz_logic_style: pseudo_lza}
---
# pseudo_lza

Pseudo leading-zero anticipation serves only the path that can cancel
massively. The left path handles effective subtraction with exponent
difference zero or one behind a 0/1-bit pre-alignment shifter and a
1's-complement adder, and its pseudo-LZA drives a full normalization
barrel switch; the right path handles every other case with a full
pre-alignment barrel switch, a 2's-complement adder and a single-level
normalization shifter, and needs no anticipation.

An analytical comparison at IEEE single precision puts a conventional
FADD with LZA at about 10 times the power and more than 1.5 times the
delay of the gated design at equal area, and a FADD without LZA at
more than 5 times the power and more than 2 times the delay at smaller
area, for about a 16X power-delay-product reduction against the LZA
design; the savings are attributed to transition scaling, the
simplified paths and zero-overhead rounding, under uniformly
distributed exponents (pillai_1997). Pseudo-LZA is the pick when the
partition confines cancellation to one path, so the full_lza of a
conventional unpartitioned adder, whose power the comparison reports,
is not needed.

## references

pillai_1997 -> R. V. K. Pillai, D. Al-Khalili, A. J. Al-Khalili, "A Low Power Approach to Floating Point Adder Design", IEEE International Conference on Computer Design (ICCD), 1997
