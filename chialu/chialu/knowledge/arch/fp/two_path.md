# two_path

Floating-point addition split into two parallel significand paths by
the exponent difference: the far path takes differences above the
threshold, performs the full alignment shift, adds or subtracts, and
needs at most a one- or two-bit normalization; the close path takes the
cancellation cases, effective subtraction with exponent difference at
most one, aligns by at most one bit, and performs the large
normalization with a leading-zero anticipator running beside the
subtraction. Each operation therefore meets one full-length shifter
rather than the serial alignment-then-normalization of a single path,
and a multiplexer selects the path result before or after a shared
rounding stage.

The close-path trigger decides what the close path handles. Sending
every equal-or-adjacent exponent pair there, addition included, keeps
the far path free of cancellation and lets the close path skip
rounding, since its operands are misaligned by at most one bit; sending
only effective subtraction there leaves the far path without a
leading-zero anticipator, and the close path can start separate
anticipators for the difference-0 and difference-1 cases alongside
operand swapping. The threshold moves that boundary by a bit; a
directional interval suits operands arriving on different schedules.
The select point is the speculation decision: an early exponent compare
steers operands to one path and lets the other be gated for power; a
late result mux runs both paths and predicts the difference-1 case from
exponent LSBs and significand MSBs, which takes an fp64 adder from
three cycles to two for one extra flagged prefix adder. The unit's rounder
rounds once after the path mux; per-path rounding, which exploits the
exact close-path result, is a sharing choice of the unit.

The slots carry the remaining latency. A compound adder that
precomputes sum and sum+1 turns rounding into selection and removes a
pipeline stage, with sum+2 from a half-adder row for the directed
modes, and a flagged prefix adder folds the increment into the add. A
leading-zero anticipator errs by at most one bit, which a concurrent
correction removes to equalize the path delays; a post-add count saves
around 2x the anticipation logic's area and power when bounded
pre-alignment delivers the close-path result early enough. Subnormals
get full hardware, with the close-path shift limited to ex - emin, or
flush to zero, as in the DSP-block adder that fits around a multiplier
at about 0.9 of an 18x18 multiplier's area in 20 nm.

The family is the default for latency-critical adders, two to four
cycles at binary64 and one cycle for a restricted add built from seven
adders; comparisons, min/max and conversions reuse the paths at no
cost. Its price is a second significand adder and the final mux, so a
single path is the alternative where area dominates. The datapath is
feed-forward at one operation per cycle.

Product units pin the partition. The SPARC64 adder runs two concurrent
pipelines, each shifting in one direction only. Path 1 takes effective
subtraction at exponent difference 0, and difference 1 when the larger
operand's mantissa is below 1.5, so the result falls in (0, 1) and
always needs a one-bit left shift, which lands the guard bit on the LSB
and removes Path 1's rounding stage. Path 2 takes effective addition
and every other subtraction. Both exponent subtractions A - B and B - A
run, their low-order bits pre-shift both mantissas right by 0, 1, 2 or
3 places before the precedence is known, and the second stage completes
the alignment once the smaller operand is swapped into the subtrahend
position. That unit binds far_align to full_align, near_lz to an
anticipator whose vector has at most one too few leading zeros, and
close_norm to a coarse/fine pair of 0/4/8/12 and 0/16/32/48 mux stages.
It runs at 3 cycles of latency and one operation per cycle in 0.15 um
six-layer-metal CMOS, and supports normalized results only, so a
denormal operand or a denormal result traps.

The delay accounting behind the split is that the critical path is the
alignment right shift followed by the significand add and its rounding,
or the significand add followed by the normalizing left shift, rather
than both: at a difference of at most one the alignment shift reduces
to a muxing step, and above one the result needs at most a one-bit left
shift. A 53-bit leading-one prediction costs 1.1 of a 53-bit add delay,
about ten percent more than an adder of the same length, and the
arrangement needs one compound adder per path, which puts a binary64
add at 3.4 add delays plus wire delay. Clocking only the path a given
operation uses is where a cascade multiply-add unit takes the family's
energy saving, which is the gate_inactive_path_for_power mutation.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: a far path with the full aligner and a close path with the anticipator and the normalizer, selected by the exponent difference).
The choices (path_threshold, close_path_trigger, path_select_point, subnormal_representation, operand_order) and the component families (far_align, exp, sig_adder, near_lz, close_norm) select its sub-structures
from the library.

## design choices

### operand_order

| member | what it selects |
| --- | --- |
| `swap_before_shift` | the operands are ordered by exponent first, so one shifter and one adder serve. |
| `shift_each_operand` | neither operand is swapped: each has its own shifter and the difference is formed both ways. |

### path_select_point

| member | what it selects |
| --- | --- |
| `early_exponent_compare` | the path is chosen from the exponent comparison, before the datapaths run. |
| `late_result_mux` | both paths run and the result is selected at the end. |

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

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the datapath carries two paths, so the align and the normalize never run in series at full width | - | `\(two_path\): \d+ paths` |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
oberman_1996 -> S. F. Oberman and M. J. Flynn, "A Variable Latency Pipelined Floating-Point Adder", Euro-Par'96 Parallel Processing (LNCS 1124), Springer, 1996
nielsen_2000 -> A. M. Nielsen, D. W. Matula, C. N. Lyu, G. Even, "An IEEE Compliant Floating-Point Adder that Conforms with the Pipelined Packet-Forwarding Paradigm", IEEE Transactions on Computers, 2000
schmookler_2001 -> M. S. Schmookler, K. J. Nowka, "Leading Zero Anticipation and Detection — A Comparison of Methods", Proc. ARITH-15, pp. 7-12, 2001
beaumont_smith1999 -> A. Beaumont-Smith, N. Burgess, S. Lefrere, C.-C. Lim, "Reduced Latency IEEE Floating-Point Standard Adder Architectures", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999.
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
pillai_1997 -> R. V. K. Pillai, D. Al-Khalili, A. J. Al-Khalili, "A Low Power Approach to Floating Point Adder Design", IEEE International Conference on Computer Design (ICCD), 1997
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
