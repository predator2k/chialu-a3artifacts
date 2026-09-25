# full_hardware

Gradual underflow handled in the datapath: denormal operands are detected by register tags or late exponent/fraction detection and either prenormalized (with a stall) or corrected inline by adjusting exponent differences and implied bits, and an underflowed result is denormalized by a dedicated right shifter, pipeline feedback, iterative small shifts, or a normalizer whose left shift is bounded at the denormal radix point. With the internal significand pseudo-normalized under a wider exponent, denormals run near normalized speed.

internal_representation decides whether the special cases collapse into the normal flow (pseudo_normalized_wide_exponent, two extra exponent bits on Power4) or the stored form is kept and corrected late. denorm_result_shift trades a large dedicated right shifter and instruction reordering against reuse of the normalizer with a clamp, which needs no separate pass. extra_latency_cycles is the stall budget: Power4 pays a two-cycle back-end stall for unusual results and three more cycles per additional denormal operand in a pipelined multiply-add, while the S/390 G5 fed results back through a 1-to-4-bit shifter for up to 13 cycles on fp64. In multipliers a denormal multiplicand is repaired by a late partial-product row entering a free tree input, which adds no delay when the tree does not gain a stage; the z990 kept most denormal cases in the normal flow and left one enabled-underflow FMA case to millicode. Register tags remove arithmetic from the critical path but complicate mixed-format execution and verification.

This is the IEEE-compliant pick once the normalizer is exponent-clamped; flush_to_zero_mode is the cheaper noncompliant sibling and the software trap (deferred in this version) the 1990s alternative it replaced.

## references

schwarz_2005 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "FPU Implementations with Denormalized Numbers", IEEE Transactions on Computers, 2005
schwarz_2003 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
gerwig_2004 -> G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
trong_2007 -> S. D. Trong, M. Schmookler, E. M. Schwarz, M. Kroener, "P6 Binary Floating-Point Unit", 18th IEEE Symposium on Computer Arithmetic, 2007
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
eisen_2007 -> Eisen, Ward, Tast, Mading, Leenstra, Mueller, Granito, Prasad, Whitcomb, Mansfield, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
kessler_1999 -> R. E. Kessler, "The Alpha 21264 Microprocessor", IEEE Micro, 1999
