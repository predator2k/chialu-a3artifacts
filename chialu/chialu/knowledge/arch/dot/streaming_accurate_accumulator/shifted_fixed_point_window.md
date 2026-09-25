---
family: streaming_accurate_accumulator
pin: {approach: shifted_fixed_point_window}
---
# shifted_fixed_point_window

Each floating-point summand is shifted into an application-sized
fixed-point window and converted to two's complement, and the
loop-carried operation is a fixed-point addition with no alignment,
normalization or rounding. Three bounds size the window: MSBA prevents accumulator overflow, LSBA sets accuracy and
area, and MaxMSBX limits the input shifter; a separate LongAcc2FP
block does carry propagation, leading-zero count, shift, sign
conversion and rounding when a float result is wanted.

The window is the pick when a running sum is needed every cycle or
the floating-point adder's 6 to 12 FPGA cycles cannot be interleaved,
and when the application's magnitude bounds can be profiled: the coil-inductance case study fits MSBA = 24,
LSBA = -38, MaxMSBX = 8 in a 63-bit accumulator that sums 20 million
binary32 terms to 2.0 x 10^-16 relative error, where a binary32 adder
gives 1.2 x 10^-3, in fewer slices. Inputs whose LSB lies at or above
LSBA add exactly and lower ones cost at most 2^(LSBA - 1) each, with
sticky overflow and underflow flags for an a posteriori check. A
two's-complement feedback keeps only the 80-bit add in the loop at
initiation interval 1 in 28 nm. Compensated summation keeps
normalization in the loop and only estimates the lost part, and the
refinement tree suits parallel reductions rather than a stream.

The window can also be anchored on the incoming summand instead of on
profiled bounds. Shifting the mantissa left by its five least
significant exponent bits converts it to base 32 and extends 24 bits
to 55, leaving three exponent bits in the loop, so every in-loop
alignment is a constant 32-bit shift and the deferred normalization
runs in the last three pipeline stages under a software-set enable.
That form costs 31 bits of extra mantissa width against a base-2 loop
and reaches 6.2 GFlops at 3.1 GHz in 90 nm, and double precision would
need base 64 with the mantissa extended by 63 bits.

The library realizes this choice as a pin of the generated streaming_accurate_accumulator module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
dedinechin_2008 -> F. de Dinechin, B. Pasca, O. Cret, R. Tudoran, "An FPGA-Specific Approach to Floating-Point Accumulation and Sum-of-Products", IEEE FPT, pp. 33-40, 2008
brunie_2017 -> N. Brunie, "Modified Fused Multiply and Add for Exact Low Precision Product Accumulation", ARITH-24, pp. 106-113, 2017
kahan_1965 -> W. Kahan, "Pracniques: Further Remarks on Reducing Truncation Errors", Communications of the ACM, vol. 8, no. 1, p. 40, 1965
vangal_2006 -> S. Vangal, Y. Hoskote, N. Borkar, A. Alvandpour, "A 6.2-GFlops Floating-Point Multiply-Accumulator With Conditional Normalization", IEEE Journal of Solid-State Circuits, vol. 41, no. 10, 2006
