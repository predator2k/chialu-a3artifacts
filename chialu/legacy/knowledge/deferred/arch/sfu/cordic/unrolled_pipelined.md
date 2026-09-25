---
family: cordic
pin: {topology: unrolled_pipelined}
---
# unrolled_pipelined

One hardware stage per iteration: the variable shifter of a folded
core becomes fixed wiring, the angle table becomes hardwired constants
in each stage, and registers between stages let a new operand enter
every cycle. A DDS phase-amplitude converter of this shape is 18
stages with the shift sequence 0, 0, 0, 1, 2 ... 15, two zero
iterations widening convergence from 99.88 to 180 degrees;
Maharatna's rotator is a 12-stage core in a 14-stage pipeline with
latency 14 and one result set per clock.

Unrolling is the pick when throughput rather than latency is bought
and the shifts map poorly to logic: bit-parallel iterative variable
shifters suffer high fan-in on FPGAs, while a 14-bit 5-iteration
parallel pipeline on an XC4013E gives a 52 MHz data rate at half the
device, and a complete DDS with the 18-stage converter fits 916 LEs
above 110 MHz on a Cyclone II. Latency stays tied to stage count and
addition time, wider pipelines lose to carry propagation and need
heavy x/y cross-routing, and an unpipelined unrolled chain has
substantial combinational delay. The unrolled form also hosts the
latency schemes: Timmermann's parallel direction prediction with
generalized termination reaches 60 percent speedup over the fastest
carry-save array, and Ercegovac and Lang's on-line rotation uses
delays instead of shifters at two cycles per iteration. The folded
core is the area pick when one result per n cycles suffices.

The library's module for cordic realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

andraka_1998 -> R. Andraka, "A Survey of CORDIC Algorithms for FPGA Based Computers", ACM/SIGDA International Symposium on FPGAs, pp. 191-200, 1998
maharatna_2005 -> K. Maharatna, S. Banerjee, E. Grass, M. Krstic, A. Troya, "Modified Virtually Scaling-Free Adaptive CORDIC Rotator Algorithm and Architecture", IEEE Transactions on Circuits and Systems for Video Technology, vol. 15, pp. 1463-1474, 2005
timmermann_1992 -> D. Timmermann, H. Hahn, B. J. Hosticka, "Low Latency Time CORDIC Algorithms", IEEE Transactions on Computers, vol. 41, no. 8, pp. 1010-1015, 1992
ercegovac_lang_1990 -> Ercegovac, Lang, "Redundant and On-Line CORDIC: Application to Matrix Triangularization and SVD", IEEE Transactions on Computers, 1990
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
