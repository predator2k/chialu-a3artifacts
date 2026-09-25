# dsp48_style_slice

The hardened FPGA DSP block of the Xilinx DSP48 lineage taken as one
unit: a pre-adder feeds an asymmetric two's-complement multiplier
(18x18 in DSP48, 25x18 in DSP48E/E1, 27x18 in DSP48E2) whose product
enters a 48-bit three-operand adder/subtracter/accumulator that also
runs bitwise logic and a pattern detector, so the block computes
P = B x (A + D) + C + Pin. Dedicated PCIN/PCOUT and BCIN/BCOUT cascades,
with a fixed 17-bit right shift on the result cascade, chain
neighbouring blocks so FIR taps and the subproduct reductions of wide
multipliers stay inside the DSP column, and up to four internal
register levels pipeline the path.

The mult_shape choice is what tilers see: the 25x18 block serves a
16x24 unsigned tile so the tile widths share a gcd of 8, and the signed
17x25 Karatsuba pre-subtraction fits the same multiplier because the
extra bit lands on the sign input, with one embedded pre-adder per
subproduct. The pre_adder pays for itself in symmetric FIRs and those
pre-subtractions; the cascade paths turn a column into a systolic
filter, where a 51-tap FIR occupies 0.49 mm2 against 1.46 mm2 in soft
logic and runs at 510 MHz against 217 MHz in a 40 nm device. The cost
is portability, since the advanced modes need manual block
instantiation.

The alu_width, alu_op_set and simd_partition choices size the
post-adder. Native SIMD splits the 48-bit ALU into independent lanes;
the PIR-DSP variant goes to 4/8/18/48-bit partitions with a
decomposable Baugh-Wooley multiplier, a wide XOR and semi-2D
forwarding to two downstream blocks at a 3.85 ns critical path in
65 nm against 3.94 ns for a DSP48E1 model. Virtual packing is the
other route to multi-lane use: two n-bit products that share one
unsigned operand are packed into the 25x18 multiplier with n
separating bits and a guard bit, carry-out and sign corrections are
accumulated outside the block and subtracted once, and the result is
0.5 DSP per 8-bit MAC at 11 LUTs and 12 FFs of correction logic; the
same ports pack five 9-bit additions per block. Both packed forms stay
exact, with accuracy loss only from operand quantization.

The family wins where a design needs many exact MACs at high
utilization (97-99% on MobileNet layers, above a tensor block whose
size restricts legal unrolling) or a wide multiplier built from few
hard tiles, and it loses per-block throughput to dedicated tensor
blocks on dense layers. The pattern detector carries no stated fault
model. Execution is feed-forward at one packed multiplication per
clock.

No unit template opens `dsp_block_space`: the family describes the internal organization of an FPGA DSP slice, a fixed-function unit class of its own, so no seed declares it and the library has no module for it; the ALU, dot and SFU templates cover the slice's parts (multipliers, wide adders, SIMD lanes, dot arrays) through their own slots.

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
boutros_2021 -> A. Boutros, V. Betz, "FPGA Architecture: Principles and Progression", IEEE Circuits and Systems Magazine, 2021
kumm2018 -> M. Kumm, O. Gustafsson, F. de Dinechin, J. Kappauf, P. Zipf, "Karatsuba with Rectangular Multipliers for FPGAs", 25th IEEE Symposium on Computer Arithmetic (ARITH), 2018
nguyen_2017 -> D. Nguyen, D. Kim, J. Lee, "Double MAC: Doubling the Performance of Convolutional Neural Networks on Modern FPGAs", Design, Automation and Test in Europe (DATE), 2017
lee_2019 -> S. Lee, D. Kim, D. Nguyen, J. Lee, "Double MAC on a DSP: Boosting the Performance of Convolutional Neural Networks on FPGAs", IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, 2019
rasoulinezhad_2019 -> S. Rasoulinezhad, H. Zhou, L. Wang, P. H. W. Leong, "PIR-DSP: An FPGA DSP Block Architecture for Multi-Precision Deep Neural Networks", IEEE Symposium on Field-Programmable Custom Computing Machines (FCCM), 2019
roorda_2022 -> E. Roorda, S. Rasoulinezhad, P. H. W. Leong, S. J. E. Wilton, "FPGA Architecture Exploration for DNN Acceleration", ACM Transactions on Reconfigurable Technology and Systems, 2022
sommer_2022 -> J. Sommer, M. A. Özkan, O. Keszocze, J. Teich, "DSP-Packing: Squeezing Low-Precision Arithmetic into FPGA DSP Blocks", International Conference on Field-Programmable Logic and Applications (FPL), 2022
