# flush_to_zero_mode

Subnormal handling by suppression: denormal inputs are read as signed zeros and results that would underflow are flushed to zero, so the datapath never shifts below the normal range and exponent underflow becomes a clear of the result. The mode is noncompliant with IEEE 754 gradual underflow and is offered either as the only behavior or as an optional mode beside a compliant path.

Its value is what it removes: the denormal normalizer, the exponent-clamped shifter and the stall or trap machinery of full_hardware. An FPGA DSP-block adder without subnormal support was 0.9 of the area of the version with it at latency 3 (20 nm), and a fixed-location injection multiplier supports the flush mode without the bidirectional prenormalization stage that IEEE subnormals need. Vector units have shipped it as the default (the POWER6 VMX non-Java mode, the Apple G4/G5 vector unit, 3DNow!) and CPUs as a switchable mode beside a compliant datapath (PA7100). Its cost is semantic: results near the underflow threshold lose gradual precision, and a flushed unit reports no flags for the discarded values, so the mode interacts with the ftz/daz parameters of the module contract rather than with the architecture alone.

Choose it for throughput datapaths whose numerics tolerate abrupt underflow; choose full_hardware for IEEE compliance at near-normal speed and a software trap (deferred in this version) only where the hardware cannot form the result at all.

## references

schwarz_2005 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "FPU Implementations with Denormalized Numbers", IEEE Transactions on Computers, 2005
asprey_1993 -> T. Asprey, G. S. Averill, E. DeLano, R. Mason, B. Weiner, J. Yetter, "Performance Features of the PA7100 Microprocessor", IEEE Micro, vol. 13, no. 3, pp. 22-35, 1993.
eisen_2007 -> Eisen, Ward, Tast, Mading, Leenstra, Mueller, Granito, Prasad, Whitcomb, Mansfield, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
langhammer_2015b -> M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
oberman_favor_1999 -> S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
