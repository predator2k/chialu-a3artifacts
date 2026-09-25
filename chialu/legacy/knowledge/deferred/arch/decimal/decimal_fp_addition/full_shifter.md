---
family: decimal_fp_addition
pin: {alignment: full_shifter}
---
# full_shifter

Single-path alignment through a full-width decimal shifter: operands
are DPD-decoded to BCD, the exponent difference is computed, and one
or both significands pass through a barrel shifter or rotator spanning
the whole significand ahead of one significand addition, so every
exponent-difference case shares one adder and rounding stage. POWER6
and z10 split execution into equal-exponent, align-to-smaller-exponent
and shift-both cases, since a 2p-digit adder is prohibitive at 34
digits.

Equal exponents are the common accounting case, and the z10 early-end
path takes it when the most-significant digit sum is below 9 and the
inputs are not subnormal; POWER6 takes 9 to 17 cycles for decimal64
and z10 12 to 28 cycles for double-word operands. Wang's adder shifts
both significands at once through separate left and right barrel
shifters driven by LSA/RSA to fix the rounding position, cutting the
alignment critical path by roughly 41 percent for about 4.8 percent
more area than the earlier OACSU. z196 pre-aligns through a two-stage
rotator with an operation-dependent assumption (carry-out for
addition, cancellation for subtraction), which limits rounding
hardware to two decimal locations and removes the exponent
decrementor. The limited_shift_two_path sibling is pinned by no block
in the notes. It is the pick when non-normalized cohorts make any
exponent difference legal and one datapath must serve all of them.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
