---
family: integer_mac
pin: {array_style: simd_packed_dot}
---
# simd_packed_dot

Packed dot product inside a SIMD lane: byte or halfword elements of
two vector registers are multiplied at full precision, the products
of each 32-bit lane are summed with an addend from a third vector,
and the partial sums saturate, so one instruction performs several
multiplies and a short reduction per lane; a sum-across step reduces
the lane sums to one scalar. The organization scales to an eight-way
int4 pipeline with int16 results and to 40-lane dot-product engines
with a binary tree.

The packed form wins on integration: it lives in a vector register
file, fits an existing SIMD issue slot, and the subword multiplier
can be a twin-precision Booth array whose result subwords feed one
multioperand adder shared across the 8-, 16- and 32-bit modes; a
decoupled int4 engine built this way costs about 16 percent area
over an integer-extended training FPU at 7 nm and doubles its power
efficiency. Its reductions are short, so long accumulations return to
the register file or a scratchpad each instruction, and utilization
depends on batching operands across lanes. A systolic array instead
keeps weights stationary and streams partial sums through hundreds of
MACs per cycle, which is the pick when the operand reuse of dense
matrix multiply is available and a fixed accumulator memory is
acceptable.

The library realizes this choice as a pin of the generated integer_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
agrawal_2021 -> A. Agrawal, S. K. Lee, J. Silberman, et al., "A 7nm 4-Core AI Chip with 25.6TFLOPS Hybrid FP8 Training, 102.4TOPS INT4 Inference and Workload-Aware Throttling", IEEE ISSCC, 2021
krithivasan2003 -> S. Krithivasan, M. J. Schulte, "Multiplier Architectures for Media Processing", 37th Asilomar Conference on Signals, Systems and Computers, pp. 2193-2197, 2003
boutros_2020 -> A. Boutros, E. Nurvitadhi, R. Ma, S. Gribok, Z. Zhao, J. C. Hoe, et al., "Beyond Peak Performance: Comparing the Real Performance of AI-Optimized FPGAs and GPUs", International Conference on Field-Programmable Technology (ICFPT), 2020
jouppi_2017 -> N. P. Jouppi, C. Young, N. Patil, D. Patterson, et al., "In-Datacenter Performance Analysis of a Tensor Processing Unit", ISCA, 2017
