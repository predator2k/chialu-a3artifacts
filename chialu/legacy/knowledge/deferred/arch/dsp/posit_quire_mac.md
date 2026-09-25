# posit_quire_mac

Exact accumulation of posit products in a Kulisch-style fixed-point
register, the quire: each posit is decoded into sign, regime, exponent
and fraction, the exact fraction product is shifted by its combined
scale factor into a two's-complement fixed-point word wide enough for
every product from minpos squared to maxpos squared (16n bits, 128
for posit16 and 512 for posit32), products are added or subtracted
without intermediate rounding, and one leading-digit count, shift and
round-to-nearest-even conversion at the end yields the posit result.
Fused multiply-add, sums and dot products are subsets of the fused dot
product this supports.

organization trades frequency against read latency. A monolithic
register with one wide adder holds the resolved sum at all times, but
its carry propagation is long, 8.85 ns for an unsegmented 512-bit
posit32 quire on a Kintex-7 against a 3 ns target; segmenting the
quire into 32- or 64-bit pieces with delayed carries reaches about
2.9 ns at one product per cycle with fewer LUTs, at the price of a
final carry propagation before conversion, and a segmented pipelined
accumulator with increment FIFOs doubles the clock of the monolithic
unit while lengthening the fused multiply-add to 19 cycles for posit32
and making a quire read wait for queued accumulations.
quire_width_bits follows 16n, so posit32 already costs 512 bits and
posit64 would need 2048; a fixed 128-bit quire with an external scale
factor keeps the critical path of the small format but is exact only
for posit8, and the accumulators the origin proposal sizes for n of 32
and above need cache-sized scratch space rather than a register.
op_set ranges from accumulate-only through the QMADD/QMSUB/QROUND dot
product of PERCIVAL to general fused operations including
divide-accumulate.

The cost is the width. A posit unit with quire needs 11,879 LUTs
against 4,046 for an fp32 FPU on the same FPGA, about half of it
quire, and the sum of two posit32 products through a hardware quire
takes more than 4 times the area and 8 times the latency of a posit
adder plus multiplier. The conversion, a leading-digit count across
half the quire plus a comparably wide XOR for correct rounding, is
irreducible, so the family wins on long dot products and matrix
kernels, where GEMM error falls far below fused fp32 and 8-bit
inference recovers 32-bit float accuracy, and loses on short sums,
range reduction and polynomial evaluation. A single non-loadable
quire also forbids interleaved independent accumulations and a safe
context switch, since saving it through posit conversion loses
accuracy.

The contract is an exact sum of exact products with one final
round-to-nearest-even; a sticky flag carries Not-a-Real through the
computation, and no fault detection is reported.

The family's defining structure is an accumulator register across operations (the quire) and the ALU has no accumulate op, so the library has no combinational module for it; a seed that declares it stays behavioral and the family is listed as an exception (`posit.EXCEPTIONS`).

## references

gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
dedinechin_2019b -> F. de Dinechin, L. Forget, J.-M. Muller, Y. Uguen, "Posits: The Good, the Bad and the Ugly", Conference for Next Generation Arithmetic (CoNGA), 2019
uguen_2019 -> Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
carmichael_2019 -> Z. Carmichael, H. F. Langroudi, C. Khazanov, J. Lillie, J. L. Gustafson, D. Kudithipudi, "Deep Positron: A Deep Neural Network Using the Posit Number System", Design, Automation and Test in Europe (DATE), 2019
crespo_2022 -> L. Crespo, P. Tomás, N. Roma, N. Neves, "Unified Posit/IEEE-754 Vector MAC Unit for Transprecision Computing", IEEE Transactions on Circuits and Systems II: Express Briefs, 2022
