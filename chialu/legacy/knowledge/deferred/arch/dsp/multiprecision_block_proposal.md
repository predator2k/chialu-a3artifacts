# multiprecision_block_proposal

Academic DSP-block proposals that fracture an Intel-like or
Xilinx-like multiplier into native low-precision multiply and MAC
lanes while keeping the routing interfaces and every legacy mode.
Mode-controlled partial-product logic and blocked carry paths cut
the Baugh-Wooley arrays, standalone small multipliers may be added,
and modified 4:2 compressors separate or combine the packed products
behind the same 72 output ports: one 27x27, two 18x18, four 9x9 or
eight 4x4 products per block. The PIR-DSP line chops 27x18 into 9-bit
parts, recursively decomposes each 9x9 into 4x4 and 2x2 multipliers,
and adds ALU partitions, forwarding to the next two blocks and a FIFO for data reuse.

The fracture depth trades lane count against area and clock. Adding
four int9 lanes costs about 4 to 5 percent block area and eight int4
lanes about 9 to 12 percent in 28 nm at the 600 MHz target, or 0.6
percent of die area, for 1.3x and 1.6x accelerator performance at
8-bit and 4-bit with 15 and 30 percent fewer utilized resources; full
fracturing of every array fails timing after place and route, so the
chosen design fractures selected arrays and adds standalone 4x4
multipliers. Deeper recursive decomposition to twelve 4-bit and
twenty-four 2-bit lanes raises the multiplier area ratio to about
1.7 and lowers the clock from 763 to 538 MHz in SMIC 65 nm, while
energy per MAC falls from 28.4 pJ to 2.0 pJ at 2 bits.

Runtime composition, with per-operand signedness, chain forwarding
distance and embedded reuse storage, is what separates the PIR-DSP
line from the mode-only proposals: the complete block is 1.28x the
area of a DSP48E2 at 357 rather than 463 MHz, adds one latency cycle
and keeps an unused pre-adder on the critical path, and it beats the
mode-only design at 8x8 and below while losing on area, power and
delay at 16x16 and above. The multiplier slot decides the lane
arithmetic: an exact Baugh-Wooley array with a Dadda tree, a
twin-precision subword array, or approximate 9x9 tiles that cut
block area by about a fifth for error-tolerant DNN and filter
workloads. The proposals win only where the DSP supports the low
precision natively, since decomposition in soft logic gives none of
the gain.

No unit template opens `dsp_block_space`: the family describes the internal organization of an FPGA DSP slice, a fixed-function unit class of its own, so no seed declares it and the library has no module for it; the ALU, dot and SFU templates cover the slice's parts (multipliers, wide adders, SIMD lanes, dot arrays) through their own slots.

## references

boutros_2021 -> A. Boutros, V. Betz, "FPGA Architecture: Principles and Progression", IEEE Circuits and Systems Magazine, 2021
boutros_2018 -> A. Boutros, S. Yazdanshenas, V. Betz, "Embracing Diversity: Enhanced DSP Blocks for Low-Precision Deep Learning on FPGAs", International Conference on Field Programmable Logic and Applications (FPL), 2018
rasoulinezhad_2019 -> S. Rasoulinezhad, H. Zhou, L. Wang, P. H. W. Leong, "PIR-DSP: An FPGA DSP Block Architecture for Multi-Precision Deep Neural Networks", IEEE Symposium on Field-Programmable Custom Computing Machines (FCCM), 2019
