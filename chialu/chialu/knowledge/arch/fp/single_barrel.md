# single_barrel

Normalization by one barrel shifter driven directly by the lz slot: the leading-zero (or leading-one) position, as a binary count or as one-hot stage controls, selects the left shift in a single mux tree, and the shifted significand goes to rounding. With an exact post-add count the shift is final; with an LZA the lz slot's correction_scheme repairs the over-anticipation (a one-bit stage after the barrel, or compensation in the rounding).

The barrel is the close-path and small-adder normalizer: a near path that pre-aligns by at most one bit normalizes through a full barrel switch while the far path gets a single-level shifter, a conventional serial adder chosen for area keeps one barrel after an exact count, and a seven-stage accumulate adder detects the leading one and normalizes in one block. Driving the stages one-hot from the LZA string removes the encode and decode between count and shift. Under gradual underflow the close-path shift must be limited to the exponent margin above emin, so the count is clamped before it drives the barrel. Against coarse_fine it is one structure rather than two and needs no fine stage, but a wide FMA normalizer under a short cycle splits anyway, and the one-bit correction stage lands in series after the barrel unless it merges into the round mux.

Pick single_barrel for the close path of a two-path adder and for area-first serial adders; pick coarse_fine for wide normalizers under a short cycle or where the LZA correction must fold into the fine-shifter controls.

## references

beaumont_smith1999 -> A. Beaumont-Smith, N. Burgess, S. Lefrere, C.-C. Lim, "Reduced Latency IEEE Floating-Point Standard Adder Architectures", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999.
pillai_1997 -> R. V. K. Pillai, D. Al-Khalili, A. J. Al-Khalili, "A Low Power Approach to Floating Point Adder Design", IEEE International Conference on Computer Design (ICCD), 1997
quinnell_2008 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Bridge Floating-Point Fused Multiply-Add Design", IEEE Transactions on VLSI Systems, vol. 16, no. 12, pp. 1726-1730, 2008
kadric_2016 -> E. Kadric, P. Gurniak, A. DeHon, "Accurate Parallel Floating-Point Accumulation", IEEE Transactions on Computers, vol. 65, no. 11, pp. 3224-3238, 2016
schmookler_2001 -> M. S. Schmookler and K. J. Nowka, "Leading Zero Anticipation and Detection - A Comparison of Methods", 15th IEEE Symposium on Computer Arithmetic, 2001
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
