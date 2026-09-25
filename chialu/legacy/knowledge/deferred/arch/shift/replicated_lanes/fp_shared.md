---
family: replicated_lanes
pin: {register_file: fp_shared}
---
# fp_shared

The packed lanes live in the floating-point register file: MMX aliases
its eight 64-bit registers onto the IA floating-point stack and marks
the stack empty with EMMS after an MMX section; VIS stores packed
operands in the SPARC floating-point registers with partitioned
operations on 8-, 16- or 32-bit components; POWER8's two symmetric VSU
pipelines each carry a vector register file serving VMX, VSX and FPU
instructions and reuse the floating-point multiplier for packed
integer multiplies.

Reusing the floating-point registers adds no architectural state and
needs no operating-system context support, which is why 3DNow! packs
two fp32 values into an MMX register and ignores the high half for
scalar work (oberman_favor_1999); the price is that MMX and
floating-point code cannot use the shared registers at once, so
transitions need the EMMS discipline (peleg1996). The first VIS
implementation took 3% of the UltraSPARC I die (tremblay_1996), and
POWER8's multiplier reuse gives 8 word, 16 halfword or 32 byte
multiplies per cycle per core at little added area, with the two
vector files synchronized in single-thread mode and split between
thread sets under SMT (sinharoy_2015). The shared file is the pick for
an extension to an existing ISA; dedicated_simd wins when the vector
width should exceed the floating-point register width or a permute
unit is planned.

## references

oberman_favor_1999 -> S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
peleg1996 -> A. Peleg, U. Weiser, "MMX Technology Extension to the Intel Architecture", IEEE Micro, vol. 16, no. 4, pp. 42-50, 1996
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
sinharoy_2015 -> B. Sinharoy, et al., "IBM POWER8 Processor Core Microarchitecture", IBM Journal of Research and Development, vol. 59, no. 1, pp. 2:1-2:21, 2015.
