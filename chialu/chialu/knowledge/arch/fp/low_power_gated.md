# low_power_gated

Floating-point addition partitioned by operand case, one partition
active per cycle: an exponent comparator routes each operation to a
near path (effective subtraction at exponent difference 0 or 1: 0/1-bit
pre-alignment, one's-complement adder, pseudo LZA, full normalization
shifter), a far path (every other computed case: full pre-alignment
shifter, two's-complement adder, one-level normalization shift), or a
bypass whose result is known before significand arithmetic (exponent
distance beyond p, zero operand, infinity, NaN). Gated clocks hold
inactive paths at their prior state; rounding is precomputed as sum and
sum+1 and selected once the rounding condition is known.

The datapath_partitions choice buys transition activity with area: each
added partition owns shifters bounded to its own case (bounded
alignment on the near path, bounded normalization on the far path), so
no operation pays for a full-length shifter it does not need, while the
front-end comparator and the duplicated significand adder are the
price. Clock gating of the inactive partitions, a sequential property (the
single-cycle unit isolates the inactive partition's operands at their
inputs instead), is what converts that partitioning into power: with uniformly distributed exponents the gated
design draws around 50% of the power of other schemes when exponent
differences stay below p, and it reports about a 16x
power-delay-product reduction against a conventional high-speed adder
with leading-zero anticipation in single precision. Without gating the
partitions only shorten the delay.

The rounder's compound selection removes the rounding increment from
the critical path at the cost of the second sum; the anticipator (the lz
slot) serves the close partition alone, where normalization can be
long, and the far partitions carry none. Against its neighbours
the family sits at equal area to an LZA adder and about one tenth of
its power, while an adder without LZA is smaller but more than 2x
slower and more than 5x hungrier. The contract is IEEE single and
double addition with no numerical error and no fault coverage;
execution is feed-forward, with per-operation latency fixed by the
pipeline rather than by the path taken.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: one, two or three partitions (datapath_partitions: one path; a close and a far path; the far path split into its add and subtract cases) with their inputs isolated when inactive).
The choices (datapath_partitions, subnormal_representation, operand_order) and the component families (align, exp, sig_adder, lz, norm) select its sub-structures
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

pillai_1997 -> R. V. K. Pillai, D. Al-Khalili, A. J. Al-Khalili, "A Low Power Approach to Floating Point Adder Design", IEEE International Conference on Computer Design (ICCD), 1997
