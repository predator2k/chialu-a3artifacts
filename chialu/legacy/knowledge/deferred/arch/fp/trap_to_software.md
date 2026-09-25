# trap_to_software

Subnormal handling by exception: when a denormal operand or an underflowed result is detected and the hardware dataflow cannot produce the required form, the operation traps to software or to internal millicode, which recomputes the result and returns it. It was the common 1990s design point and is the alternative the hardware-denormal line replaced.

The cost is latency, thousands of cycles for an external trap, which makes denormal support impractical for programmers and turns a numerically benign event into a performance cliff; vector interfaces that forbid data-dependent stalls and traps cannot use it at all. Its surviving form is the narrow internal case: the z990 handles most denormal inputs and results in the normal flow and confines millicode to one enabled-underflow FMA case, where a denormal addend exceeds the product and significant product bits must enter the rebiased result, a case that already requires the architected underflow trap. Some enabled-underflow and cancellation arrangements otherwise require a wider shifter, bounded-result manipulation or prenormalization, so the trap is the fallback that bounds the hardware for those corners.

Choose it only for corner cases that coincide with an architectural exception; full_hardware is the pick for compliant near-normal speed, and flush_to_zero_mode for datapaths that may discard the values.

## references

schwarz_2005 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "FPU Implementations with Denormalized Numbers", IEEE Transactions on Computers, 2005
kessler_1999 -> R. E. Kessler, "The Alpha 21264 Microprocessor", IEEE Micro, 1999
gerwig_2004 -> G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
schwarz_2003 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
eisen_2007 -> Eisen, Ward, Tast, Mading, Leenstra, Mueller, Granito, Prasad, Whitcomb, Mansfield, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
