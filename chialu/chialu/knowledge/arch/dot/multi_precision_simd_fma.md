# multi_precision_simd_fma

One FMA datapath that splits at run time into independent narrower
lanes: precision-mode multiplexers segment the alignment and
normalization shifters, the leading-zero anticipator, and the adder
at lane boundaries, the partial-product array masks the cross-lane
(off-diagonal) products so one 53x53 multiplier becomes two 24x24
ones, boundary carries are reset in the final adder, and
the exponent and rounding hardware is either duplicated per lane or
built as one incrementer that accepts an increment signal per lane.
Unused lanes and format slices are clock-gated, so one wide unit
returns one fp64, two fp32, four fp16, or eight fp8 results per
cycle, each rounded once to its own format.

Lane split trades throughput at narrow precision against overhead at
the wide one. Splitting a double-precision unit into two
single-precision lanes costs roughly 18 percent area and 9 percent
delay over the fixed unit (0.18 um), and a three-way 24/12/6-bit
mantissa split costs about 12 percent area and 11 percent mantissa
power (32 nm) while replacing several fixed single-precision units at
equal throughput for a fraction of their area; a unified posit/IEEE
unit is about half the area of the separate fixed-precision units it
subsumes. The alignment shifter is cheap to segment; the multiplier
is where the choice bites, since Booth recoding needs cross-subword
carry detection and suppression, so an unsigned array with masked
partial products or a Booth tree with disabled off-diagonal products
are the two workable forms. The shared rounder saves the duplicated
exponent and rounding paths at the cost of a variable-precision
incrementer; the hybrid keeps sharing for the wide modules and
duplicates the timing-sensitive ones. Two's-complement mantissas
avoid end-around-carry correction in the lanes, and normalization
becomes a precision-dependent constant shift followed by a lane-wide
variable shift.

Against dedicated per-format slices, the merged datapath is smaller
but imposes one pipeline depth on every format and runs narrow
formats through an over-dimensioned unit, so parallel slices with
clock gating give stronger energy proportionality; a vector fp8 FMA
still runs at about 0.80 pJ per flop against 13.36 for scalar fp64 in
the same 22 nm unit. The processor-level alternatives are peeling the
second single-precision operand off to a supplemental narrow FMAC
rather than fracturing the main one, or selecting one fp64 or two
fp32 per FPU per instruction and replicating that FPU across a wide
vector register. A variable-precision lane can also carry a small
certainty field and recompute at higher precision when a narrow
result is uncertain, with energy gains that depend on how often the
narrow mode succeeds. Execution is feed-forward and fully pipelined
at initiation interval one, and the mixed-format (multiply in the
source format, add in the destination format) case belongs to the
merged slice as well.

A quadruple-precision datapath that also serves two double or four
single precision instructions settles the same trades concretely. Its
113x113 array multiplier forms 2 x 53-bit or 4 x 24-bit products by
forcing the off-diagonal partial-product regions to zero, and Booth
encoding is rejected there for its control complexity and its subword
carry suppression. The exponent processing is replicated as one
quadruple, one double and two single precision units rather than
segmented. The full-width shifters are built from sub-shifters that
combine in the wider modes, so the 115-bit aligner is two shifters of
60 and 55 bits, the second alignment path is two of 65 and 56 bits,
and the 118-bit normalization shifter is two 30-bit and two 29-bit
shifters. Assimilating the multiplier's two carry-save vectors at the
start of the add stage, before alignment, shrinks the alignment
shifters and every module after the addition, and one far-path shifter
aligns either the product or the addend according to the sign of the
exponent difference. The unit costs 23 percent area and 14 percent
latency over a fixed quadruple-precision MAF, and post-layout in 65 nm
it measures 672,046 um2 at 293.5 MHz against 812,952 um2 for a
multi-block baseline of equal functionality and throughput, which it
beats on area and loses to on energy per operation, 1295.4 pJ per
operation against 979.2.

SIMD width can also come from instances rather than from lanes inside
one datapath. POWER7 gives each core four 64-bit FPU
instances. One instance serves scalar code, two serve 2-way
double-precision vectors, and all four serve 4-way single-precision
vectors, so no datapath is split internally. Scalar single-precision arithmetic there reads 64-bit
double-precision register data, rounds the intermediate once to single
precision, and converts back to the 64-bit format, and the normalizer
and the leading-zero anticipator precompute sticky bits and carry-out
for each target precision so one rounder per instance serves both.
Merging what had been separate vector and scalar FPUs reduces area by
a factor of 1.35 in 45 nm SOI. The cost is that a program mixing
scalar and vector single-precision data needs explicit conversions,
because scalar floating-point data sit in the register file in the
64-bit format whatever their precision.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the products as the lanes of one gated partial-product matrix (the twin-precision matrix of `families/subword.py`, the `lane_split` naming the split), aligned into the frame and summed by a chain of the `cpa` component; the shared rounder is the seed's single rounding). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## design choices

### lane_split

| member | what it selects |
| --- | --- |
| `1x64` | one 64-bit lane. |
| `2x32` | two 32-bit lanes. |
| `4x16` | four 16-bit lanes. |
| `8x8` | eight 8-bit lanes; the lanes are the gated regions of one partial-product matrix. |

## references

huang_2007 -> L. Huang, L. Shen, K. Dai, Z. Wang, "A New Architecture For Multiple-Precision Floating-Point Multiply-Add Fused Unit Design", ARITH-18, pp. 69-76, 2007
kaul_2012 -> H. Kaul, M. Anders, S. Mathew, S. Hsu, A. Agarwal, F. Sheikh, R. Krishnamurthy, S. Borkar, "A 1.45GHz 52-to-162GFLOPS/W Variable-Precision Floating-Point Fused Multiply-Add Unit with Certainty Tracking in 32nm CMOS", ISSCC Digest of Technical Papers, pp. 182-184, 2012.
mach_2020 -> S. Mach, F. Schuiki, F. Zaruba, L. Benini, "FPnew: An Open-Source Multi-Format Floating-Point Unit Architecture for Energy-Proportional Transprecision Computing", arXiv:2007.01530, 2020
crespo_2022 -> L. Crespo, P. Tomás, N. Roma, N. Neves, "Unified Posit/IEEE-754 Vector MAC Unit for Transprecision Computing", IEEE Transactions on Circuits and Systems II: Express Briefs, 2022
sharangpani_2000 -> H. Sharangpani, K. Arora, "Itanium Processor Microarchitecture", IEEE Micro, vol. 20, no. 5, pp. 24-43, 2000.
sinharoy_2015 -> B. Sinharoy, et al., "IBM POWER8 Processor Core Microarchitecture", IBM Journal of Research and Development, vol. 59, no. 1, pp. 2:1-2:21, 2015.
manolopoulos_2016 -> K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
boersma_2011 -> M. Boersma, M. Kroener, C. Layer, P. Leber, S. M. Mueller, K. Schelm, "The POWER7 Binary Floating-Point Unit", ARITH-20, 2011
