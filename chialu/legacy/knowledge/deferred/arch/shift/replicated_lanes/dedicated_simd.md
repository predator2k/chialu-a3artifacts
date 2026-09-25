---
family: replicated_lanes
pin: {register_file: dedicated_simd}
---
# dedicated_simd

The SIMD lanes read and write a register file of their own, separate
from the integer and floating-point files: AltiVec holds 32 fixed
128-bit vector registers of four, eight or 16 elements beside a
first-class permute unit; the TPUv2 vector unit gives each of its 128
lanes and eight sublanes a dual-issue 32-bit ALU with a 32-deep
register file; each ILLIAC IV processing element owns five 64-bit data
registers next to its local arithmetic and shift logic.

A dedicated file lets vector width and register count be set for the
workload rather than inherited: AltiVec's 32 registers and 162
instructions issue one ALU-class and one permute-class instruction per
cycle for average kernel speedups of 6.5 on integer and 5.1 on
floating-point kernels over the same PowerPC core (diefendorff_2000);
the TPUv2 sublanes raise the vector-to-matrix compute ratio and the
result FIFO shortens register lifetimes (norrie_2021); ILLIAC IV's 256
PEs run in lock step, so the slowest PE sets the operation time
(davis_1969). The AMD-K6-2 kept per-pipeline MMX ALUs on dedicated
state, while the K7 moved 3DNow! into the shared floating-point
coprocessor (oberman_favor_1999). The dedicated file is the pick when
new architectural state and operating-system context support are
acceptable; fp_shared wins when the extension must add no state.

## references

diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
norrie_2021 -> T. Norrie, N. Patil, D. H. Yoon, G. Kurian, S. Li, J. Laudon, C. Young, N. Jouppi, D. Patterson, "The Design Process for Google's Training Chips: TPUv2 and TPUv3", IEEE Micro, vol. 41, no. 2, pp. 56-63, 2021.
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
oberman_favor_1999 -> S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
