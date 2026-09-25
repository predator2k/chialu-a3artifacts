# increment_adder

Rounding as a serial increment after normalization: the carry-propagate result is normalized, the guard, round and sticky bits decide, and a separate incrementer adds one ulp (with an overflow-dependent constant, and a one-bit right shift with exponent bump when the increment carries out). It is the textbook realization: one extra carry chain in series with the significand adder and the shifter.

The two serial carry propagations are its limit: adequate for software models and moderate-performance hardware, they are what compound_adder_select and injection remove from the critical path. Where the increment is kept, it is hidden or shared: the normalization shift runs concurrently with the rounding decision and a final small shift plus exponent increment absorbs both the LZA error and the rounding overflow; an FMA splits its wide carry propagation into a 106-bit adder and a 53-bit incrementer selected by the lower carry, a 24-bit incrementer shares its carry chain with the two's-complement negation, and a lane-partitioned unit accepts four independent increment signals. Round-to-nearest-even needs the L/R/sticky tie correction after the increment. modes and position follow the rounding slot; unified_add_sub_cases is rarely exploited here, since the incrementer does not see the operation. Production FMAs that round across two cycles forward the unrounded, partially normalized value early and repair its later use with correction terms.

Choose increment_adder for area and simplicity when a stage of latency is affordable, when only RNE is needed, or when the rounder is off the critical path; replace it by compound selection when the round stage sets the pipeline depth.

## references

santoro_1989 -> M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
suzuki_1996 -> H. Suzuki, H. Morinaka, H. Makino, Y. Nakase, K. Mashiko, T. Sumi, "Leading-Zero Anticipatory Logic for High-Speed Floating Point Addition", IEEE Journal of Solid-State Circuits, 1996
darley_1990 -> M. Darley, B. Kronlage, D. Bural, B. Churchill, D. Pulling, P. Wang, et al., "The TMS390C602A Floating-Point Coprocessor for Sparc Systems", IEEE Micro, vol. 10, no. 3, pp. 36-47, 1990.
trong_2007 -> S. D. Trong, M. Schmookler, E. M. Schwarz, M. Kroener, "P6 Binary Floating-Point Unit", 18th IEEE Symposium on Computer Arithmetic, 2007
kaul_2012 -> H. Kaul, M. Anders, S. Mathew, S. Hsu, A. Agarwal, F. Sheikh, R. Krishnamurthy, S. Borkar, "A 1.45GHz 52-to-162GFLOPS/W Variable-Precision Floating-Point Fused Multiply-Add Unit with Certainty Tracking in 32nm CMOS", ISSCC Digest of Technical Papers, pp. 182-184, 2012.
lang_2004 -> T. Lang, J. D. Bruguera, "Floating-Point Multiply-Add-Fused with Reduced Latency", IEEE Transactions on Computers, vol. 53, pp. 988-1003, 2004
chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
