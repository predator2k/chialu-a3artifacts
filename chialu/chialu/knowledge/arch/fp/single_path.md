# single_path

Floating-point addition on one serial datapath for every operand case: compare exponents, align the smaller-exponent significand by a right shift of at most p + 1 digits, perform the exact effective addition or subtraction over p digits, normalize after a carry-out or a cancellation with a leading-zero count and a left shift, and round from the round, guard, and sticky bits, plus a one-digit renormalization if rounding carries out. Close cases (effective subtraction at exponent difference 0 or 1) need the full normalization shift; far cases need the large alignment shift and one normalization digit at most; the single path carries both in series. Feed-forward, in 1 to 5 pipeline stages.

The pipeline depth, a sequential property outside the single-cycle unit, trades latency against cycle time. The 360/91 merged the work into three hardware areas over two stages, so an add takes 2 cycles at one issue per cycle against 3 cycles for the conventional unit it replaced; a fabricated fp64 adder in 0.5-µm CMOS takes 3 cycles in 1.8 mm² with 33,000 transistors; the G5 and later designs use 4 or 5 stages when the combined add and round exceeds one stage. The z13's decimal and quad execution pipeline runs 8 stages and starts a new operation every cycle for every arithmetic operation but multiply, divide and the binary/decimal converts, which puts a quad-precision add or subtract at 11 cycles of latency and 1.5 CPI in IBM 22 nm against 35 cycles and 28 CPI on the machine it replaced. The significand carry-propagate adder sets the minimum cycle time, which is why pipeline_after_significand_add places a boundary right after it. The renormalization after a rounding carry-out belongs to the rounder's family: an increment adder after normalization needs the extra renormalization step, while fuse_round_with_add uses a flagged prefix adder that produces the sum, sum+1, and sum+2 alternatives inside the significand addition, so all four rounding modes and the absolute difference after a negative subtraction fall out of one adder. replace_lzc_with_lza runs leading-one prediction concurrently with the subtraction; with concurrent position correction the compensation shifter and exponent incrementer disappear and a 5-stage adder becomes a 4-stage one with the same critical path.

The other slots follow the machine's contract. align is full in nearly every design; the bounded form of Stretch shifted at most 4 right or 6 left per pass and looped for the rest, which covered 80% of numbers within six shifting cycles. norm is a single barrel or a coarse/fine pair; subnormal_representation keeps a subnormal operand as stored (the exponent of bit 0 orders it with the normals) or normalizes it into the wide exponent first; flush-to-zero, an optional mode in later machines, and a trap are mode and system properties outside the unit. sig_adder went from group-4 carry-lookahead to the compound flagged prefix adder. The family is chosen for area and simplicity over the faster leading-one-predictor or two-path organizations, and one datapath can serve add, subtract, compare, complement, and conversions because they share alignment, normalization, and rounding. It loses on latency to split_into_two_paths, which separates the close and far cases so each carries only one large shift.

A denormal operand costs an exponent-difference correction. The exponent difference that drives the aligner is off by one when an operand is denormal, so the usual implementation computes D, D-1 and D+1 in parallel and a late detection of an operand equal to a denormal selects among the three. An aligner stage that performs a late correction shift, chosen by which operand is denormal, is the alternative. The implied ones stay off the critical path under as_stored, because the aligner shifts one significand while the other is not needed until the carry-propagate addition, so that significand is corrected for its implied bit at the adder input. The z13's serial pipeline binds full_align as a two-stage shifter of up to 36 digits left or right followed by 0 to 3 bits right, lz as an anticipator whose one-too-large count is corrected from the most significant bit of the normalizer output, end_around_carry for the effective subtraction, and as_stored for a denormal operand. That pipeline places the normalizer circuit and the rounding-selection circuit side by side in the post-adder stage and selects one of them, because an add or a subtract in homogeneous precision needs a wide normalization or a rounding rather than both.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: one aligner (or one per operand under operand_order shift_each_operand), one significand adder, one normalizer).
The choices (subnormal_representation, operand_order) and the component families (align, exp, sig_adder, lz, norm) select its sub-structures
from the library.

## design choices

### operand_order

| member | what it selects |
| --- | --- |
| `swap_before_shift` | the operands are ordered by exponent first, so one shifter and one adder serve. |
| `shift_each_operand` | neither operand is swapped: each has its own shifter and the difference is formed both ways. |

### subnormal_representation

| member | what it selects |
| --- | --- |
| `as_stored` | a subnormal significand enters the datapath unnormalized. |
| `pseudo_normalized_wide_exponent` | a subnormal is normalized at entry and its exponent is carried in a wider field. |

### negation_handling

The magnitude of an unswapped datapath's difference (operand_order `shift_each_operand`; the swapped datapath's difference is non-negative and takes none). A subtraction borrows the shifted operand's sticky, so the integer part of the exact difference is X - Y - stb when non-negative and Y - X - sta when negative.

| member | what it selects |
| --- | --- |
| `end_around_carry` | one ones' complement adder (X + ~Y without the one) and an incrementer: a carry out adds the one back, no carry gives the ones' complement of the sum. |
| `dual_adder` | two adders, X + Y (or X - Y) and Y - X in parallel, the first adder's carry selecting; no comparator, one adder more. |
| `complement_recode` | one two's complement adder; a negative difference is complemented after the fact through an incrementer, the one withheld when a sticky borrowed. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
anderson1967 -> S. F. Anderson, J. G. Earle, R. E. Goldschmidt, D. M. Powers, "The IBM System/360 Model 91: Floating-Point Execution Unit", IBM Journal of Research and Development, vol. 11, no. 1, pp. 34-53, 1967
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
beaumont_smith1999 -> A. Beaumont-Smith, N. Burgess, S. Lefrere, C.-C. Lim, "Reduced Latency IEEE Floating-Point Standard Adder Architectures", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999.
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
lichtenau_2016 -> C. Lichtenau, S. Carlough, S. M. Mueller, "Quad Precision Floating Point on the IBM z13", ARITH-23, 2016
schwarz_2003 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
