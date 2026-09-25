# streaming_accurate_accumulator

Accumulation with only a fixed-point add on the loop-carried path:
each floating-point summand is shifted once into an application-sized
window from bit LSBA to bit MSBA, converted to two's complement
without carry propagation, and added to a wA = MSBA - LSBA + 1 bit
accumulator; the input shifter is bounded by MaxMSBX and sticky bits
record input and accumulator overflow. Normalization leaves the
recurrence and runs once at the end. The compensated form keeps
normalization in the loop and carries a correction S2 = (S - T) + S2
that captures each step's rounding error; the tree form reduces
rounded sums plus exact residues over further passes until the
rounded result cannot change.

The approach fixes what sits in the loop. A window accumulator accepts
one summand per cycle with only the adder in the feedback path; an
80-bit two's-complement window in TSMC 28 nm reaches II = 1 while the
multiply and alignment pipeline freely, and a sign-magnitude feedback
encoding would put more work on that path. A floating-point adder in
the loop costs 6 to 12 cycles of latency on an FPGA and cannot be
interleaved, and the compensated two-sum adds four operations per term
and needs arithmetic that normalizes before it rounds. The refinement
tree returns the correctly rounded sum, usually in two passes, at
about three operations per summand and a modest area overhead over
the plain tree, but its iteration count is data-dependent.

The window bits are application bounds rather than a format: LSBA sets
accuracy against area, MSBA is chosen with a safety margin against
overflow, and MaxMSBX equal to MSBA is the safe setting when the
summand bound is unknown. Inputs whose last bit lies at or above LSBA
are accumulated exactly and lower inputs contribute at most
2^(LSBA-1) each, so the result is exact or bounded rather than rounded
per step and differs from an FMA chain. The 63-bit case-study window
sums twenty million binary32 terms to 2.0e-16 relative error at 182
Virtex-4 slices, against 1.2e-3 at 482 slices for a binary32 adder
and 2.8e-15 at 839 slices for binary64.

The family wins when a running sum is needed every cycle or the
summand magnitudes can be profiled, and it is the bounded cousin of
the Kulisch register, which drops the profiling by paying for the
whole exponent range. Post-normalization can be omitted, shared among
accumulators, or run at reduced rate, so the family is fixed-iteration
with a single epilogue.

A second construction anchors the window on the incoming summand
rather than on the application's bounds. The summand's mantissa shifts
left by its five least significant exponent bits, which converts it to
base 32 and extends 24 bits to 55, and the loop carries the remaining
three exponent bits, so every alignment inside the loop is a constant
32-bit shift and no variable shifter sits on the loop-carried path.
Normalization leaves the loop and runs in the last three pipeline
stages under a software-set enable. That loop costs 31 bits of extra
mantissa width against a base-2 loop, in a wider adder and more
accumulator flip-flops, and reaches 6.2 GFlops at 3.1 GHz and 1.2 W in
90 nm, with a sustained 330 ps per multiply-accumulate. The deferred
normalization pipeline holds 28 percent of the devices, and gating it
by clock and by an nMOS sleep transistor cuts its own power by 94
percent and the unit's active power by 24.6 percent, for 4.5 percent
of frequency and 7.4 percent of area. Double precision would need base
64 and a mantissa extended by 63 bits. This form implements none of
the four IEEE rounding modes and raises an exception on a denormalized
operand, and its anticipator can be off by one or two positions on the
final result, which a compensatory shift corrects after the conversion
to sign-magnitude.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the one-operation form of the window: `shifted_fixed_point_window` anchors a window of `window_bits` (raised to the exact width under the correctly-rounded contract) at the largest exponent and shifts the terms into it, `tree_reduce_with_refinement` reduces them in a tree whose dropped bits refine the sticky, `in_loop_normalization` normalizes the products first). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## references

kahan_1965 -> W. Kahan, "Pracniques: Further Remarks on Reducing Truncation Errors", Communications of the ACM, vol. 8, no. 1, p. 40, 1965
dedinechin_2008 -> F. de Dinechin, B. Pasca, O. Cret, R. Tudoran, "An FPGA-Specific Approach to Floating-Point Accumulation and Sum-of-Products", IEEE FPT, pp. 33-40, 2008
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
brunie_2017 -> N. Brunie, "Modified Fused Multiply and Add for Exact Low Precision Product Accumulation", ARITH-24, pp. 106-113, 2017
vangal_2006 -> S. Vangal, Y. Hoskote, N. Borkar, A. Alvandpour, "A 6.2-GFlops Floating-Point Multiply-Accumulator With Conditional Normalization", IEEE Journal of Solid-State Circuits, vol. 41, no. 10, 2006
