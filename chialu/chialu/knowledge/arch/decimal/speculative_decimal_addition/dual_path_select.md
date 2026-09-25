---
family: speculative_decimal_addition
pin: {recovery: dual_path_select}
---
# dual_path_select

Recovery by selection: every speculated alternative runs to the end of
the datapath as a full candidate, and the resolved carry, carry-out or
cancellation condition selects one, so no correction stage follows.
z900 lets the carries pick among four candidate sums per digit;
Vazquez's adder selects S^H, SI^H or the complement of S^H by cmp =
eop Cout and the rounding increment; z196 runs a carry-select AREN and
selects the injection digit p or p+1 after the leading digit resolves.

The cost is the duplicated candidate logic plus the selection
multiplexers, which in the Vazquez decimal64 estimate are 570 NAND2
and 6.6 FO4 of a 3580 NAND2, 26.1 FO4 total; the sparse-prefix version
selects two conditional digit sums through a 7-level tree at 21.8 FO4
stage delay. The win is a fixed latency with no serial pass after the
sum. The late_correction_stage sibling applies a second injection
correction through flagged-prefix masks after the sum instead, so it
avoids the duplicate candidates but adds a dependent stage.
dual_path_select is the pick when the candidates are cheap, one or two
per digit, and a carry_select or compound_flagged_prefix carry network
is already in place; the late stage is the pick when the prefix
network can absorb flag generation more cheaply than duplicating the
datapath.

## references

schwarz_2002 -> E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
vazquez_2009 -> Vazquez, Antelo, "A High-Performance Significand BCD Adder with IEEE 754-2008 Decimal Rounding", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
