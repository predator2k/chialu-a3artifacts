# classic_fma

The RS/6000 fused multiply-add: a Booth-recoded tree forms the 2p-bit
product in carry-save form while the addend is aligned, and
complemented if needed, against the fixed product across a 3p+5-bit
range; a 3:2 CSA merges the aligned addend into the last reduction
row; one wide adder (a 2p-bit adder plus a p-bit incrementer selected
by the lower carry, with end-around carry for the one's-complement
subtraction) resolves the sum while a leading-zero anticipator derives
the normalization shift; the normalized result is rounded once. A
single path covers the product-anchored, addend-anchored and
cancellation cases, and addition and multiplication are the degenerate
forms B + A*1 and 0 + A*C.

Subsuming the adder and multiplier into one unit removes an
adder/normalizer pair and gives add, multiply and FMA the same 4-cycle
latency in a current 64-bit pipeline, but all three operands are
needed at issue, an in-order sum of n products costs 4n cycles, and
standalone adds cannot run concurrently with multiplies; the bridge
variant fixes the standalone latency at higher FMA power. Negation
handling trades adder width against duplication: the end-around-carry
one's-complement sum widens the adder by half and adds a gate delay, a
dual adder computes A-B and B-A and selects by sign, and inversion
with an increment shared with the rounding incrementer shortens the
mantissa path by 9% in a 32 nm fp32 unit, where pre-shifting the
addend in parallel with the multiplier saves another 14%.

Pipeline depth runs from two stages, which needs a fast shifter and an
LZA that overlaps normalization with the addition, to seven stages at
13 FO4 per cycle, where forwarding the unrounded, partially normalized
stage-6 result with a multiplier correction term makes the dependent
latency six. The 161-bit aligner and adder form a wire-dominated
critical path (81 logic levels in 65 nm), so the alignment slot is
where bounded-window variants save. The LZA carries a possible one-bit
error that the normalization shifter corrects; counting zeros after
the add is simpler but serial. The carry-propagate slot is a prefix or
conditional-sum adder with the end-around recirculation folded in, and
the rounding slot is an incrementer, a compound-adder select, or an
injection returned through the addend or multiplicand pipeline.

The contract is one rounding of the full-precision product and sum,
which yields exact residuals for division, square root and argument
reduction; two extra exponent bits absorb overflow before rounding.
Denormals need two aligner positions beyond the product LSB and late
Booth-term and aligner corrections to avoid stalls. Repeated
accumulation still loses information at every FMA output.

Two organization axes sit outside the family's choices. The number of
passes the multiplier operand makes through the array per
double-precision product is one in the PowerPC 604e and two in the
PowerPC 603e. The second pass halves the array, which cuts the FPU
from 19.5 mm2 to 11.7 mm2 in the same 0.5 um CMOS and costs two cycles
per double-precision multiply rather than one. The dual-pass form
splits the 161-bit aligned addend into a low 26 bits in the first pass
and an upper 135 bits in the second, so the one 161-bit adder becomes
a 26-bit incrementer, an 81-bit carry-lookahead block and a 54-bit
incrementer, and the 3:2 CSA group that injects the aligned addend
sits in either the multiply stage or the add stage. The second axis is
the fused organization against separate multiply and add pipelines. At
the same 3.2 GFlops single-precision point in 90 nm the two reach the
same area efficiency of 0.036 mm2/GFlops and the same power efficiency
of 0.046 W/GFlops, and the fused unit gets there at 10 cycles against
the cascade's 12. A 45 nm generator study puts the fused unit ahead on
the throughput criterion, because the cascade trades additional logic
for latency savings, with Pareto pipeline depths of three to eight
stages for single precision and four to eight for double, almost all
of them radix-8 Booth, since that radix minimizes area at a large
operand width. The reduction tree's topology decides delay rather than
area or energy, and the multiplier holds 31 percent of the area and
power of a single-precision unit and 45 percent of a double-precision
one. A conventional three-stage double-precision MAF of this shape,
with a 161-bit aligner, a 106-bit 3:2 CSA and a 161-bit adder,
measures 119,668 um2 at 444.24 MHz post-layout in 65 nm.

POWER7 binds the tail for two target precisions at once. It aligns
fully, runs a leading-zero anticipator over the trailing 110 bits of a
160-bit sum, and rebiases its 13-bit internal exponent with the target
precision's minimum exponent rather than with a constant bias, so
underflow is the exponent's sign bit and the 13-bit comparators
disappear. The fully rounded result is forwarded after 5.5 cycles,
where POWER6 forwarded an unrounded result and corrected it inside the
multiplier. One 64-bit instance takes 0.26 mm2 in 45 nm SOI against
0.46 mm2 for the POWER6 unit scaled into the same node. The CELL SPE
pair binds alignment, negation and the leading-zero path alike. Both
units align sum-addressed in parallel with the multiplier, form the
sum or the absolute difference by end-around carry, and correct the
anticipator's one-position error in the result multiplexer. The single-precision unit merges a 97-bit aligned addend
through a 3:2 counter, resolves the sum in a compound adder producing
sum and sum + 1, and truncates in a 4-port result multiplexer instead
of rounding, which saves the 24-bit fraction incrementer and fits 11
FO4 per stage inside a 60 FO4 logic budget, against about 100 FO4 for
a conventional single-precision FPU. Its double-precision companion
folds a 106-bit carry-save product into two rows and a 160-bit aligned
addend into three, which reshapes the adder, the anticipator's edge
vector and the normalization shifter, and runs nine cycles.

Denormals carry a measured cost inside the fused datapath. A Power4
multiply-add adds 3 cycles for each additional denormal operand,
because prenormalization stalls the front of the pipeline, and an
unusual result costs a 2-cycle back-end stall in which a denormal
result returns to the normalizer aligned 65 bit positions to the
right. Avoiding that back-end stall costs a 108-bit LZA and normalizer
instead, as in Power3, while the Power4 stall lets both be much
smaller. The disjoint case, which is a denormalized addend with a
product below the addend's least significant bit, cannot carry 53 bits
of significance through a dataflow that concatenates the addend to the
product across a couple of guard bits, so it is prenormalized or
trapped. The PowerPC 603e prenormalizes denormalized source operands
through its write-back normalization shifter, at 3, 4 or 5 extra
cycles before execution starts for one, two or three of them. Leaving
denormals to software costs tens of thousands of cycles. Supporting
all four rounding modes and denormals together costs 5 to 10 percent
over a unit that truncates and flushes. The CELL SPE pair splits on
exactly that line. Its single-precision unit forces denormal operands
and results to zero and supports round-toward-zero alone, while its
double-precision unit treats denormal operands as zero and computes
denormal results in all four modes.

A second rounding contract appears in the literature. A MAF is called
IEEE compatible there when it delivers the result of a sequential
FMPY followed by an FADD, which one rounding of the full-precision
product and sum does not, and the higher internal precision that buys
the single rounding is what requires 159-bit shifters, a 159-bit adder
and a 159-bit leading-one predictor rather than 106-bit ones. Rounding
cannot be folded into that addition, because the carry point and the
normalization shifter's input both depend on the alignment shift
distance, so an explicit rounding step follows the normalization.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: for a one-element mode, the addend aligned in parallel with the significand multiplier over the 2S + Sc + 3 window with a sticky lsb, the window adder from the `cpa` component, the negation by `negation_handling` (end-around carry, dual adder or complement), the leading zeros by the `lza` component (the anticipator on the adder's operands with its one-position correction, or a count after the add), one normalize; a mode of several elements keeps the behavioral path, since an FMA sums one product). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## in the ALU's fp_fma slot

The ALU class offers the family on its `fp_fma` slot (fp_spaces.fp_fma_space), one structure per float mode and lane whose alternative is `separate_multiplier_and_adder`: the fused datapath serves the mode's fadd and fsub as 1 * a + b, its fmul as a * b + 0 (the addend a zero of the product's sign) and its fused multiply-add ops fmadd, fmsub, fnmsub and fnmadd as a * b + c with the negations folded into the signs of a and c (an op code `fop` selects; families/fp.py `FMA_OP_CODES`), and the mode's fp_adder and fp_multiplier slots are then closed (their variables are active under the separate organization alone), so nothing is declared twice. The family's slots are the significand `multiplier` and the tail (`align`, `lza`, `cpa`, `norm_shifter`); `negation_handling` is the window sum's; the exponent path is behavioral. The specials follow the engine's order for each op: a NaN operand, an invalid product, infinities of opposite sign, an infinite product, an infinite addend, a zero product (the addend passes), a zero addend. Every finite result leaves normalized (the leading one at the top of the X, an exact zero, or a lone sticky), so the mode's rounder takes `normalized_input` and builds no normalizer of its own; the one exception is the anticipator under `lza.correction_scheme: compensation_in_rounding`, which leaves its one-position error to the rounder's own normalization, as the fp adder families do under that member (families/fp.py `fma_normalizes`).

### subnormal_representation (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `as_stored` | a subnormal operand enters with its leading zeros; the exponent alignment places it in the window and the one normalize after the sum absorbs the zeros (FPnew's `is_subnormal` exponent adjustment, no normalizer at entry); the IEEE modes. |
| `pseudo_normalized_wide_exponent` | each operand normalized at entry by a leading-zero count and a shift, its exponent lowered (the dot class's contract, which the stochastic mode's exact comparison of the dropped bits needs). |

### sharing

| member | what it selects |
| --- | --- |
| `dedicated_per_mode` | one fused datapath per float mode and lane, at the mode's geometry. |
| `shared_across_formats` | one physical datapath per lane at the widest geometry serves every float mode that selects it; the seed muxes the operands by the mode (FPnew's MERGED slice: one `fpnew_fma_multi` lane for fp16, bf16 and fp8 beside an fp8-only lane). The modes must agree on the family and its pins. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
montoye_1990 -> R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
lang_2004 -> T. Lang, J. D. Bruguera, "Floating-Point Multiply-Add-Fused with Reduced Latency", IEEE Transactions on Computers, vol. 53, pp. 988-1003, 2004
trong_2007 -> S. D. Trong, M. Schmookler, E. M. Schwarz, M. Kroener, "P6 Binary Floating-Point Unit", 18th IEEE Symposium on Computer Arithmetic, 2007
schwarz_2005 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "FPU Implementations with Denormalized Numbers", IEEE Transactions on Computers, 2005
quinnell_2008 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Bridge Floating-Point Fused Multiply-Add Design", IEEE Transactions on VLSI Systems, vol. 16, no. 12, pp. 1726-1730, 2008
kaul_2012 -> H. Kaul, M. Anders, S. Mathew, S. Hsu, A. Agarwal, F. Sheikh, R. Krishnamurthy, S. Borkar, "A 1.45GHz 52-to-162GFLOPS/W Variable-Precision Floating-Point Fused Multiply-Add Unit with Certainty Tracking in 32nm CMOS", ISSCC Digest of Technical Papers, pp. 182-184, 2012.
lutz_2019 -> D. R. Lutz, "ARM Floating Point 2019: Latency, Area, Power", 26th IEEE Symposium on Computer Arithmetic, 2019
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011
jessani_1998 -> R. M. Jessani, M. Putrino, "Comparison of Single- and Dual-Pass Multiply-Add Fused Floating-Point Units", IEEE Transactions on Computers, vol. 47, no. 9, 1998
jessani_1996 -> R. M. Jessani, C. H. Olson, "The Floating-Point Unit of the PowerPC 603e Microprocessor", IBM Journal of Research and Development, vol. 40, no. 5, 1996
galal_2011 -> S. Galal, M. Horowitz, "Energy-Efficient Floating-Point Unit Design", IEEE Transactions on Computers, vol. 60, no. 7, 2011
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
boersma_2011 -> M. Boersma, M. Kroener, C. Layer, P. Leber, S. M. Mueller, K. Schelm, "The POWER7 Binary Floating-Point Unit", ARITH-20, 2011
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
schwarz_2003 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
manolopoulos_2016 -> K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
