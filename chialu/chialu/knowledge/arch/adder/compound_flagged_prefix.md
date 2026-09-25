# compound_flagged_prefix

One parallel-prefix carry tree yields both A+B and A+B+1, and in its
flagged form also the late complement, with linear extra hardware and
constant extra delay. The flag row turns the tree's output grey cells
into black cells so that each position returns the group generate and
the group not-kill, the late carry into bit i is G or (not-K and inc),
and a per-bit output cell under two late inc/cmp controls selectively
inverts sum bits to deliver sum, sum+1, the negated sum and the
absolute difference from one addition. The dual-carry-tree form instead
duplicates the carry-lookahead network rather than the whole adder, so
the unincremented and incremented values arrive in parallel.

The implementation choice trades a second carry network against
per-bit output logic. The flag row adds one 2-input AND per bit inside
the tree and one AND-OR complex gate plus one XOR per bit at the
output, costs one XOR delay and one buffer delay over a plain prefix
adder of the same topology, and needs 63% to 72% of the transistors of
two adders at 16 and 64 bits on Ladner-Fischer and Kogge-Stone trees;
a dedicated late-increment-only cell brings that to 57% to 62%, and a
dedicated absolute-difference cell simplifies the controls the same
way. The dual carry tree keeps the output row plain and pays for the
duplicated lookahead network; FP multiplier rounding uses it and
derives R+2 from R and R+1 by selection and LSB control without
further carry propagation. A quad-precision instance builds the dual
tree per digit: 4-bit adders produce a digit generate and a digit
propagate, two binary carry trees take those signals with carry-in 0 and
carry-in 1, and the two carry vectors select the digits of the sum, of
the sum+1 and of the inverted sum over 37 decimal digits or 119 binary
mantissa bits.

The outputs choice fixes what the row must deliver: sum and sum+1
alone serve floating-point rounding, because the rounded significand
is either the sum or its successor, while adding sum-1 buys negation
and absolute difference for a second invert enable and slightly more
logic. Late carry-in matters because inc and cmp arrive after the
operands and drive every output cell, so they need buffering; the
flagged adder still matches a dual adder in speed, since the dual
adder buffers its multiplexer controls too. Deriving the select signals
from the adder's carry-out is the critical path of any fraction adder, so
one design precomputes both sets of selects, one for carry-out 0 and one
for carry-out 1, and another places a carry-only network beside the main
tree to produce that carry-out early. The selection is then absorbed into
the first normalizer stage in five- or six-port multiplexer latches, which
hides the multiplexer delay in the latch insertion delay. Any logarithmic-depth
prefix tree carries the flags; the reported designs use
Ladner-Fischer and Kogge-Stone, including a 63-bit Kogge-Stone tree in
a Decimal64 significand adder. A single-precision fused
multiply-add picks Kogge-Stone for both its main adder and its carry-only
adder to avoid fanout problems.

The family wins wherever a datapath needs a sum and its increment in
the same cycle. IEEE adders form the incremented sum from OR(Gen_C,
Prop_C) on the same prefix strings and can split the computation
across a pipeline boundary so that only one XOR line for the
incremented result remains in the second stage; FP multipliers and
three-term adders round by selecting among the compound results; an
FPGA DSP block adds flagged sum, sum+1 and sum+2 outputs to a split
Kogge-Stone network for about 3% extra logic on a 20 nm Arria 10.
Reported extensions are a half-adder row before the tree that turns
kill/generate patterns into propagate strings, and modified
least-significant cells that supply plus 2 for rounding after
significand overflow at about 70% of the logic of a compound adder. The
exponent path uses the same structure: a 10-bit three-way compound adder
precomputes e, e+1 and e+2 early enough that no adder or checker in the
exponent rounder needs a carry-in, which saved 15 FO4 on that rounder and
4 FO4 on the incrementer and adder in IBM 90nm SOI-low-k.

## the library's module

The seed instantiates the library's prefix module for the declared
`topology` (see the parallel_prefix card: `chialu.targets.rtl.families.prefix`
emits any graph; `--flagged` adds the s1 = s + 1 output from the tree's group propagates, the flag row of Burgess, valid with cin = 0); a rewrite pastes an edited graph's module in
its place.

## design choices

### outputs

| member | what it selects |
| --- | --- |
| `sum_sum1` | the sum and the sum plus one leave the adder. |
| `sum_sum1_summinus1` | the sum less one leaves it as well, which a rounding stage selecting three ways needs. |

### topology

| member | what it selects |
| --- | --- |
| `sklansky` | the minimum-depth prefix graph with doubling fanout. |
| `kogge_stone` | the minimum-depth graph at unit fanout and maximal wiring. |
| `brent_kung` | a regular constant-track graph that spends an extra log depth. |
| `ladner_fischer` | the depth and wiring point between Sklansky and Kogge-Stone. |
| `han_carlson` | a Brent-Kung skeleton over a Kogge-Stone core. |
| `knowles_mixed` | the Knowles continuum, whose fanout vector names the point. |
| `harris` | the taxonomy's (l, f) point, which fixes the extra levels and the fanout cap. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
burgess2002 -> N. Burgess, "The Flagged Prefix Adder and its Applications in Integer Arithmetic", Journal of VLSI Signal Processing, vol. 31, no. 3, pp. 263-271, 2002.
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
seidel_2001 -> P.-M. Seidel and G. Even, "On the Design of Fast IEEE Floating-Point Adders", 15th IEEE Symposium on Computer Arithmetic, 2001
quach_2004 -> N. T. Quach, N. Takagi, M. J. Flynn, "Systematic IEEE Rounding Method for High-Speed Floating-Point Multipliers", IEEE Transactions on VLSI Systems, 2004
beaumont_smith1999 -> A. Beaumont-Smith, N. Burgess, S. Lefrere, C.-C. Lim, "Reduced Latency IEEE Floating-Point Standard Adder Architectures", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999.
langhammer_2015b -> M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
vazquez_2009 -> Vazquez, Antelo, "A High-Performance Significand BCD Adder with IEEE 754-2008 Decimal Rounding", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
lichtenau_2016 -> C. Lichtenau, S. Carlough, S. M. Mueller, "Quad Precision Floating Point on the IBM z13", ARITH-23, 2016
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
