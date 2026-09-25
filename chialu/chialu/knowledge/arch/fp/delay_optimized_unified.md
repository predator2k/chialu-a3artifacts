# delay_optimized_unified

Floating-point addition with the two-path split redrawn so that only
one path rounds: the R-path takes effective additions, exponent
differences of magnitude at least 2, and effective subtractions whose
pre-shifted significand result is at least 2, and performs alignment,
one's-complement subtraction with unconditional pre-shifts, and
injection rounding in a compound prefix adder that returns sum and
sum+1 over the two result binades [1,4). The N-path takes the
remaining subtractions with at most a one-bit alignment, needs no
rounding, approximates the leading zeros from a borrow-save
difference, and normalizes the exact difference. Both paths span two
balanced stages.

Path separation trades the standard close/far split against a split
co-designed with rounding: moving every rounding case onto the R-path
and pre-shifting unconditionally balances the two stages, so the fp64
adder needs 24 logic levels against 26 for an adapted AMD design and 28
for an adapted SUN design, and 30.6 FO4 latency at a 15.3 FO4 cycle by
Logical Effort, which is 13% less latency and 22% less cycle time than
the adopted AMD design; a 23-level option duplicates the alignment
shifters. The unified single-path form computes two leading-zero
anticipations two cycles before the addition and left-shifts the
cancellation case before the add, so the last stage adds and injects
rounding with no post-add normalization cycle, in four cycles, with
equivalent timing and less area than a near/far adder, and it accepts
a double-length unrounded product for a fused multiply-add.

Subtraction style trades the two's complement subtraction against the
one's complement one whose end-around carry passes through the
eac_incrementer slot after the significand adder. The library
anticipates the leading zeros from the operands (the near_lz slot); the
approximation on the redundant borrow-save difference, which keeps the
N-path off the critical path at 21 levels, is a circuit-level form of
the same count. The rounding slot is injection into the compound
adder; the far alignment is full; normalization is coarse then fine.
The contract is correctly normalized IEEE rounding in all four modes,
reduced internally to RZ, RNU and RI, for normalized inputs; subnormal
support costs one or two logic levels through cited extensions in the
two-path form and stays in the normal datapath in the unified form.
Multiple precisions need prealignment of the rounding positions and
postalignment of results. Execution is feed-forward.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the two paths, the subtraction two's complement or ones' complement with the end-around carry through the eac_incrementer slot, the anticipator on the operands).
The choices (path_separation, subtraction_style, subnormal_representation, operand_order) and the component families (far_align, exp, sig_adder, near_lz, norm, eac_incrementer) select its sub-structures
from the library.

## design choices

### operand_order

| member | what it selects |
| --- | --- |
| `swap_before_shift` | the operands are ordered by exponent first, so one shifter and one adder serve; the difference is then non-negative. |
| `shift_each_operand` | neither operand is swapped: each has its own shifter and the difference is formed both ways and selected by the magnitude order. |

### path_separation

| member | what it selects |
| --- | --- |
| `standard_close_far` | the close and far paths split at an exponent difference of one, as the two-path adder does. |
| `nonstandard_unified_rounding` | the split moves to a difference of two, which is the point the unified rounding of the Seidel-Even line needs. |

### subnormal_representation

| member | what it selects |
| --- | --- |
| `as_stored` | a subnormal significand enters the datapath unnormalized. |
| `pseudo_normalized_wide_exponent` | a subnormal is normalized at entry and its exponent is carried in a wider field. |

### subtraction_style

| member | what it selects |
| --- | --- |
| `twos_complement` | the difference is a two's complement subtraction whose carry-in is the sticky's borrow. |
| `ones_complement_end_around` | the difference is a ones' complement subtraction whose end-around carry runs through the end-around-carry incrementer slot. |

### negation_handling

The magnitude of an unswapped datapath's difference (operand_order `shift_each_operand`; the swapped datapath's difference is non-negative and takes none). A subtraction borrows the shifted operand's sticky, so the integer part of the exact difference is X - Y - stb when non-negative and Y - X - sta when negative.

| member | what it selects |
| --- | --- |
| `end_around_carry` | one ones' complement adder (X + ~Y without the one) and an incrementer: a carry out adds the one back, no carry gives the ones' complement of the sum. |
| `dual_adder` | two adders, X + Y (or X - Y) and Y - X in parallel, the first adder's carry selecting; no comparator, one adder more. |
| `complement_recode` | one two's complement adder; a negative difference is complemented after the fact through an incrementer, the one withheld when a sticky borrowed. |

## references

seidel_2001 -> P.-M. Seidel and G. Even, "On the Design of Fast IEEE Floating-Point Adders", 15th IEEE Symposium on Computer Arithmetic, 2001
seidel_2004 -> P.-M. Seidel and G. Even, "Delay-Optimized Implementation of IEEE Floating-Point Addition", IEEE Transactions on Computers, 2004
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
