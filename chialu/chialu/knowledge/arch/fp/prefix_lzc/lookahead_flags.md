---
family: prefix_lzc
pin: {count_form: lookahead_flags}
---
# lookahead_flags

Dimitrakopoulos's formulation: a binary OR tree forms progressively
reduced input strings and the all-zero flag, and independent
single-output carry-lookahead trees apply a Z operator to those
strings so that each weighted count bit is computed as a prefix flag
rather than selected through the levels. The straightforward
organization holds gate fanout to 2; the shared-carry-propagate
organization reuses intermediate OR-tree signals for fewer gates.

The flag formulation is the pick when the leading-zero count sits on
a floating-point critical path in a fast static or dynamic process: a
64-bit static CMOS unit in 130 nm reaches 6.6 FO4, 4 percent under
Oklobdzija's tree and well under the about 11 FO4 of encoder-based
and Bruguera-Lang counters, with 10 to 49 percent less energy per
operation at equal delay; the dynamic single-rail version is 12 to 40
percent faster and 55 to over 80 percent lower in energy than
Lee-Nowka and encoder-based designs, and the hybrid single/dual-rail
form saves more than 45 percent over full dual rail. The shared
organization is the energy pick above 8.5 FO4 static or 5 FO4
dynamic. Count bits are don't-care for an all-zero input. The
valid/position tree (lzd_cell_tree) remains the regular-layout and
generator choice with pair or nibble cells. In the ADIR grammar it is
`family: prefix_lzc` with `pin: {count_form: lookahead_flags}`.

## references

dimitrakopoulos_2008 -> G. Dimitrakopoulos et al., "Low-Power Leading-Zero Counting and Anticipation Logic for High-Speed Floating Point Units", IEEE Transactions on VLSI Systems, vol. 16, no. 7, 2008
oklobdzija_1994 -> V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, vol. 2, no. 1, pp. 124-128, 1994
schmookler_2001 -> M. S. Schmookler, K. J. Nowka, "Leading Zero Anticipation and Detection — A Comparison of Methods", Proc. ARITH-15, pp. 7-12, 2001
