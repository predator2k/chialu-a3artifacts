# coarse_fine

Normalization left-shift split into a coarse stage of coarse_granularity positions and a fine stage below it, driven by the lz slot: with an LZA the fine stage absorbs the one-bit over-anticipation (the shift count arrives as a hexadecimal group index plus a small remainder, and a final small shift plus exponent increment repairs the error and the rounding shift); with a post-add LZC the split is only a mux-depth choice.

The lz slot's correction_scheme repairs the anticipator's one-bit error: post_norm_fine_shift adds an explicit one-bit stage after the fine shift, compensation_in_rounding leaves the value one position short and lets the rounder's own normalization absorb it, which eliminates the later compensation shifter and exponent incrementer, lets the last two pipeline stages merge, and makes close and far path delays equal. Encoding the LZA string straight into the coarse and fine shifter controls skips the binary-count round trip. The coarse stage is where a wide FMA normalizer spends its wires, so under a 13 FO4 cycle the partition follows the stage boundary. Normalization overlaps rounding: the shift runs concurrently with the round decision, and the post-shift correction folds the rounding overflow in.

Pick coarse_fine over single_barrel when the shifter is wide enough to split across a stage boundary or when an LZA drives it and the correction must be cheap; single_barrel is the pick for a narrow close path fed by a one-hot LZA string or by an exact count.

## references

hokenek_1990 -> E. Hokenek and R. K. Montoye, "Leading-Zero Anticipator (LZA) in the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
suzuki_1996 -> H. Suzuki, H. Morinaka, H. Makino, Y. Nakase, K. Mashiko, T. Sumi, "Leading-Zero Anticipatory Logic for High-Speed Floating Point Addition", IEEE Journal of Solid-State Circuits, 1996
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
schmookler_2001 -> M. S. Schmookler and K. J. Nowka, "Leading Zero Anticipation and Detection - A Comparison of Methods", 15th IEEE Symposium on Computer Arithmetic, 2001
trong_2007 -> S. D. Trong, M. Schmookler, E. M. Schwarz, M. Kroener, "P6 Binary Floating-Point Unit", 18th IEEE Symposium on Computer Arithmetic, 2007
seidel_2004 -> P.-M. Seidel and G. Even, "Delay-Optimized Implementation of IEEE Floating-Point Addition", IEEE Transactions on Computers, 2004
